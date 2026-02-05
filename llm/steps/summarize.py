"""
Step 3: SUMMARIZE (The Memory) - Background Process.
Updates the rolling summary. Now robust against failures via recursive queuing.
"""

import logging
import time
from typing import Tuple, Optional
from llm.schemas import PipelineInput, SummaryOutput, ClassifyOutput
from llm.prompts import SUMMARIZE_SYSTEM_PROMPT, SUMMARIZE_USER_TEMPLATE
from llm.api_helpers import make_api_call

logger = logging.getLogger(__name__)


def run_background_summary(
    context: PipelineInput,
    user_message: str,
    bot_message: str,
    classification: ClassifyOutput
) -> Optional[str]:
    """
    Run the Summarize step in "background".
    Returns the new summary string so the worker can save it.
    """
    try:
        # 1. Run LLM
        output, latency, tokens = _run_summary_llm(context, user_message, bot_message, classification)
        return output.updated_rolling_summary
        
    except Exception as e:
        logger.error(f"Background Summary failed: {e}")
        # QUEUE FALLBACK
        # Since we can't save to DB here easily without ID, we return the "dirty" append string
        # and let the worker save that as the "summary".
        return _queue_for_next_summary(context, user_message, bot_message)


def _run_summary_llm(
    context: PipelineInput,
    user_message: str,
    bot_message: str,
    classification: ClassifyOutput
) -> Tuple[SummaryOutput, int, int]:
    """Core LLM Logic"""
    user_prompt = SUMMARIZE_USER_TEMPLATE.format(
        rolling_summary=context.rolling_summary or "No prior summary",
        user_message=user_message,
        bot_message=bot_message or "(No response sent)",
    )
    
    start_time = time.time()

    data = make_api_call(
        messages=[
            {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
        step_name="Summarize"
    )
    
    summary_text = data.get("updated_rolling_summary", "")[:500]
    
    # Save to Schema
    output = SummaryOutput(
        updated_rolling_summary=summary_text,
        needs_recursive_summary=False
    )
    
    return output, int((time.time() - start_time) * 1000), 0


def _queue_for_next_summary(context: PipelineInput, user_msg: str, bot_msg: str):
    """
    Fallback: Don't lose data. Append to summary so next run sees it.
    """
    # In a perfect world, we push to a `pending_messages` table.
    # "Dumb Append" strategy as requested in Plan:
    
    current = context.rolling_summary or ""
    append = f"\n[PENDING] User: {user_msg} | Bot: {bot_msg}"
    
    # We need to save this "dirty" summary back to DB.
    # But we don't have ID. 
    # See note in `run_background_summary`.
    logger.warning("Queuing logic triggered - Implementation limitation: Caller must handle ID.")
    return current + append
