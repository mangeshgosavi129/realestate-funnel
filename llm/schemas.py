"""
Pydantic schemas for HTL Pipeline I/O.
Strict JSON schemas ensure LLM outputs are validated and typed.
"""
from typing import Optional, List, Literal, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from server.enums import (
    ConversationStage,
    IntentLevel,
    UserSentiment,
    DecisionAction,
    RiskLevel,
)


# ============================================================
# Pipeline Input Context
# ============================================================

class MessageContext(BaseModel):
    """A single message in conversation history."""
    sender: Literal["lead", "bot", "human"]
    text: str
    timestamp: str  # ISO format


class TimingContext(BaseModel):
    """Timing information for decisions."""
    now_local: str
    last_user_message_at: Optional[str] = None
    last_bot_message_at: Optional[str] = None
    whatsapp_window_open: bool = True


class NudgeContext(BaseModel):
    """Anti-spam tracking."""
    followup_count_24h: int = 0
    total_nudges: int = 0


class PipelineInput(BaseModel):
    """
    Complete input context for the HTL pipeline.
    Kept minimal for token efficiency.
    """
    # Business context
    business_name: str
    business_description: str = ""
    flow_prompt: str = ""  # Conversation flow/sales script instructions
    
    # CTAs
    available_ctas: List[Dict[str, str]] = [] # [{id: UUID, name: str}]
    
    # Conversation context
    rolling_summary: str = ""
    last_messages: List[MessageContext] = []
    
    # Current state
    conversation_stage: ConversationStage
    conversation_mode: Literal["bot", "human"]
    intent_level: IntentLevel
    user_sentiment: UserSentiment
    active_cta_id: Optional[UUID] = None
    
    # Timing
    timing: TimingContext
    nudges: NudgeContext
    
    # Constraints (from business config)
    max_words: int = 80
    questions_per_message: int = 1
    language_pref: str = "en"


# ============================================================
# Step 1: Classify Output ( The Brain )
# ============================================================

class RiskFlags(BaseModel):
    """Risk assessment for the conversation."""
    spam_risk: RiskLevel = RiskLevel.LOW
    policy_risk: RiskLevel = RiskLevel.LOW
    hallucination_risk: RiskLevel = RiskLevel.LOW


class ClassifyOutput(BaseModel):
    """
    Output from Step 1: Classify (The Brain).
    Consolidates Analysis and Decision making into one step.
    """
    # Analysis
    thought_process: str = Field(..., max_length=2000)
    situation_summary: str = Field(..., max_length=1000)
    intent_level: IntentLevel
    user_sentiment: UserSentiment
    risk_flags: RiskFlags
    
    # Decision
    action: DecisionAction
    new_stage: ConversationStage  # The determined next stage
    should_respond: bool = False
    
    # Action Payload
    selected_cta_id: Optional[UUID] = None
    cta_scheduled_at: Optional[str] = None # ISO format if LLM picks a time
    followup_in_minutes: int = 0
    followup_reason: str = ""
    
    # Metadata
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_human_attention: bool = False  # Flag independently of action


# ============================================================
# Step 2: Generate Output ( The Mouth )
# ============================================================

class GenerateOutput(BaseModel):
    """
    Output from Step 2: Generate.
    The actual message to send.
    """
    message_text: str = ""  # The generated response
    message_language: str = "en"
    selected_cta_id: Optional[UUID] = None
    next_followup_in_minutes: int = 0  # Optional override from generator
    
    self_check_passed: bool = True
    violations: List[str] = Field(default_factory=list)


# ============================================================
# Step 3: Summary Output ( The Memory )
# ============================================================

class SummaryOutput(BaseModel):
    """
    Output from Step 3: Summarize (Async).
    Updated rolling summary.
    """
    updated_rolling_summary: str = Field(..., max_length=2000)
    needs_recursive_summary: bool = False  # If true, this summary is partial/queued


# ============================================================
# Complete Pipeline Result
# ============================================================

class PipelineResult(BaseModel):
    """
    Complete result from running the Router-Agent pipeline.
    """
    # Step outputs
    classification: ClassifyOutput
    response: Optional[GenerateOutput] = None
    summary: Optional[SummaryOutput] = None
    
    # Metadata
    pipeline_latency_ms: int = 0
    total_tokens_used: int = 0
    
    # Async Flags
    needs_background_summary: bool = True
    
    # Computed actions helpers
    @property
    def should_send_message(self) -> bool:
        return self.classification.should_respond and self.response is not None and bool(self.response.message_text)
    
    @property
    def should_schedule_followup(self) -> bool:
        return self.classification.action == DecisionAction.WAIT_SCHEDULE
    
    @property
    def should_escalate(self) -> bool:
        return self.classification.needs_human_attention
        
    @property
    def should_initiate_cta(self) -> bool:
        return self.classification.action == DecisionAction.INITIATE_CTA

