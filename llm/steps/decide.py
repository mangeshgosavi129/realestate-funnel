"""
Step 2: DECIDE - Determine what action to take.
"""
import json
import logging
import time
from typing import Tuple

from openai import OpenAI

from llm.config import llm_config
from llm.schemas import PipelineInput, AnalyzeOutput, DecisionOutput
from llm.prompts import DECISION_SYSTEM_PROMPT, DECISION_USER_TEMPLATE
from llm.utils import normalize_enum
from llm.api_helpers import llm_call_with_retry
from server.enums import ConversationStage, DecisionAction, CTAType

logger = logging.getLogger(__name__)


def _build_user_prompt(context: PipelineInput, analysis: AnalyzeOutput) -> str:
    """Build the user prompt with analysis results."""
    # Compact analysis JSON for token efficiency
    analysis_compact = {
        "summary": analysis.situation_summary,
        "goal": analysis.lead_goal_guess,
        "missing": analysis.missing_info,
        "objections": analysis.detected_objections,
        "stage_rec": analysis.stage_recommendation.value,
        "risks": {
            "spam": analysis.risk_flags.spam_risk.value,
            "policy": analysis.risk_flags.policy_risk.value,
        },
        "kb_needed": analysis.need_kb.required,
        "confidence": analysis.confidence,
    }
    
    return DECISION_USER_TEMPLATE.format(
        analysis_json=json.dumps(analysis_compact, separators=(",", ":")),
        conversation_stage=context.conversation_stage.value,
        conversation_mode=context.conversation_mode,
        intent_level=context.intent_level.value,
        user_sentiment=context.user_sentiment.value,
        now_local=context.timing.now_local,
        last_user_at=context.timing.last_user_message_at or "unknown",
        whatsapp_window_open=context.timing.whatsapp_window_open,
        followup_count_24h=context.nudges.followup_count_24h,
        total_nudges=context.nudges.total_nudges,
    )


def _parse_response(content: str) -> dict:
    """Parse JSON from LLM response."""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(content)


def _validate_and_build_output(data: dict, context: PipelineInput, analysis: AnalyzeOutput) -> DecisionOutput:
    """Validate and build typed output from raw JSON."""
    # Map action string to enum with fuzzy matching
    action = normalize_enum(
        data.get("action"),
        DecisionAction,
        DecisionAction.WAIT_SCHEDULE
    )
    
    # Map stage string to enum with fuzzy matching
    next_stage = normalize_enum(
        data.get("next_stage"),
        ConversationStage,
        context.conversation_stage
    )
    
    # Map CTA type with fuzzy matching
    recommended_cta = normalize_enum(
        data.get("recommended_cta"),
        CTAType,
        None
    )
    
    # Parse CTA scheduling fields
    cta_scheduled_time = data.get("cta_scheduled_time")
    if cta_scheduled_time == "null" or cta_scheduled_time == "":
        cta_scheduled_time = None
    
    cta_name = data.get("cta_name")
    if cta_name == "null" or cta_name == "":
        cta_name = None
    
    # Ensure followup_in_minutes is reasonable
    followup = data.get("followup_in_minutes", 0)
    if action == DecisionAction.SEND_NOW:
        followup = 0  # No wait for immediate send
    elif action == DecisionAction.WAIT_SCHEDULE and followup <= 0:
        followup = 120  # Default 2 hours if not specified
    
    # If action is INITIATE_CTA but no recommended_cta, default to book_call
    if action == DecisionAction.INITIATE_CTA and recommended_cta is None:
        recommended_cta = CTAType.BOOK_CALL
    
    return DecisionOutput(
        action=action,
        why=data.get("why", "Decision made")[:150],
        next_stage=_apply_stage_override(
            llm_stage=next_stage, 
            current_stage=context.conversation_stage, 
            analyze_stage=analysis.stage_recommendation, 
            analyze_confidence=analysis.confidence
        ),
        recommended_cta=recommended_cta,
        cta_scheduled_time=cta_scheduled_time,
        cta_name=cta_name,
        followup_in_minutes=max(0, followup),
        followup_reason=data.get("followup_reason", "")[:100],
        kb_used=data.get("kb_used", False),
        template_required=data.get("template_required", False),
    )


def _apply_stage_override(
    llm_stage: ConversationStage,
    current_stage: ConversationStage,
    analyze_stage: ConversationStage = None,
    analyze_confidence: float = 0.0
) -> ConversationStage:
    """
    Apply deterministic stage transition rules.
    
    Priority:
    1. If analyze has high confidence recommendation, trust it
    2. Never regress to earlier stage (greeting < qualification < pricing < cta)
    3. LLM suggestion only for forward progression
    """
    STAGE_ORDER = {
        ConversationStage.GREETING: 0,
        ConversationStage.QUALIFICATION: 1,
        ConversationStage.PRICING: 2,
        ConversationStage.CTA: 3,
        ConversationStage.FOLLOWUP: 3,
        ConversationStage.CLOSED: 4,
        ConversationStage.LOST: 4,
        ConversationStage.GHOSTED: 4,
    }
    
    # If analyze_stage not passed (backward compat), treat as current
    if analyze_stage is None:
        analyze_stage = current_stage

    current_order = STAGE_ORDER.get(current_stage, 1)
    analyze_order = STAGE_ORDER.get(analyze_stage, 1)
    llm_order = STAGE_ORDER.get(llm_stage, 1)
    
    # Rule 1: High-confidence analyzer recommendation overrides LLM if it progresses forward
    if analyze_confidence >= 0.7 and analyze_order > current_order:
        logger.info(f"Stage Override: Trusting Analyze ({analyze_stage.value}) over LLM ({llm_stage.value}) due to high confidence")
        return analyze_stage
    
    # Rule 2: Prevent backward regression
    if llm_order < current_order:
        # Exceptions logic could go here (e.g. if user says "Wait actually I have a question about X")
        # For now, strict no-regression
        logger.warning(f"Stage Regression Blocked: {current_stage.value} -> {llm_stage.value}. Keeping {current_stage.value}")
        return current_stage
    
    return llm_stage


def run_decision(context: PipelineInput, analysis: AnalyzeOutput) -> Tuple[DecisionOutput, int, int]:
    """
    Run the Decision step.
    
    Returns:
        Tuple of (DecisionOutput, latency_ms, tokens_used)
    """
    client = OpenAI(
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
    )
    
    # Check if mode is human - must escalate
    if context.conversation_mode == "human":
        return DecisionOutput(
            action=DecisionAction.HANDOFF_HUMAN,
            why="Mode is already human, maintaining handoff",
            next_stage=context.conversation_stage,
            recommended_cta=None,
            followup_in_minutes=0,
            followup_reason="",
            kb_used=False,
            template_required=False,
        ), 0, 0
    
    user_prompt = _build_user_prompt(context, analysis)
    
    start_time = time.time()
    tokens_used = 0
    
    def make_api_call():
        return client.chat.completions.create(
            model=llm_config.model,
            messages=[
                {"role": "system", "content": DECISION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},  # More reliable than strict schema
        )
    
    try:
        data = llm_call_with_retry(
            api_call=make_api_call,
            max_retries=2,
            step_name="Decision"
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        output = _validate_and_build_output(data, context, analysis)
        
        logger.info(f"Decision step completed: action={output.action.value}, stage={output.next_stage.value}")
        
        return output, latency_ms, tokens_used
        
    except Exception as e:
        logger.error(f"Decision step failed: {e}", exc_info=True)
        return _get_fallback_output(context, analysis), int((time.time() - start_time) * 1000), 0


def _get_fallback_output(context: PipelineInput, analysis: AnalyzeOutput) -> DecisionOutput:
    """Return safe fallback output on error."""
    # If high risk, escalate to human
    if (analysis.risk_flags.spam_risk.value == "high" or 
        analysis.risk_flags.policy_risk.value == "high" or
        analysis.confidence < 0.3):
        return DecisionOutput(
            action=DecisionAction.HANDOFF_HUMAN,
            why="Escalating due to uncertainty or high risk",
            next_stage=context.conversation_stage,
            recommended_cta=None,
            followup_in_minutes=0,
            followup_reason="",
            kb_used=False,
            template_required=False,
        )
    
    # Default: wait and schedule followup
    return DecisionOutput(
        action=DecisionAction.WAIT_SCHEDULE,
        why="Defaulting to wait due to processing error",
        next_stage=context.conversation_stage,
        recommended_cta=None,
        followup_in_minutes=120,
        followup_reason="System fallback",
        kb_used=False,
        template_required=False,
    )
