"""
Context Builder for HTL Pipeline.
Gathers all necessary context via API calls to build pipeline input.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from llm.schemas import (
    PipelineInput, MessageContext, TimingContext, NudgeContext
)
from server.enums import (
    ConversationStage, ConversationMode, IntentLevel, UserSentiment
)
from whatsapp_worker.processors.api_client import api_client

logger = logging.getLogger(__name__)

def get_last_messages(
    conversation_id: UUID,
    limit: int = 3
) -> List[MessageContext]:
    """
    Get last N messages for context via API.
    """
    messages = api_client.get_conversation_messages(conversation_id, limit)
    
    return [
        MessageContext(
            sender=msg["sender"],
            text=msg["text"],
            timestamp=msg["timestamp"],
        )
        for msg in messages
    ]


def calculate_whatsapp_window(last_user_message_at: Optional[str]) -> bool:
    """
    Check if WhatsApp 24-hour messaging window is open.
    
    WhatsApp Business API allows sending messages without templates
    only within 24 hours of the last user message.
    """
    if not last_user_message_at:
        return False  # No user message = no window
    
    # Parse ISO timestamp
    try:
        last_msg_time = datetime.fromisoformat(last_user_message_at.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False
    
    # Ensure timezone-aware comparison
    now = datetime.now(timezone.utc)
    if last_msg_time.tzinfo is None:
        last_msg_time = last_msg_time.replace(tzinfo=timezone.utc)
    
    window_end = last_msg_time + timedelta(hours=24)
    
    return now < window_end


def build_pipeline_context(
    organization_name: str,
    conversation: Dict,
    lead: Dict,
) -> PipelineInput:
    """
    Build complete pipeline context from API data.
    """
    conversation_id = UUID(conversation["id"])
    
    # Get last messages
    last_messages = get_last_messages(conversation_id, limit=3)
    
    # Get current time in ISO format
    now = datetime.now(timezone.utc)
    now_local = now.isoformat()
    
    # Calculate WhatsApp window
    whatsapp_window = calculate_whatsapp_window(conversation.get("last_user_message_at"))
    
    # Build timing context
    timing = TimingContext(
        now_local=now_local,
        last_user_message_at=conversation.get("last_user_message_at"),
        last_bot_message_at=conversation.get("last_bot_message_at"),
        whatsapp_window_open=whatsapp_window,
    )
    
    # Build nudge context
    nudges = NudgeContext(
        followup_count_24h=conversation.get("followup_count_24h", 0),
        total_nudges=conversation.get("total_nudges", 0),
    )
    
    # Parse enums from string values
    stage = ConversationStage(conversation.get("stage", ConversationStage.GREETING.value))
    intent_level = IntentLevel(conversation.get("intent_level", IntentLevel.UNKNOWN.value)) if conversation.get("intent_level") else IntentLevel.UNKNOWN
    user_sentiment = UserSentiment(conversation.get("user_sentiment", UserSentiment.NEUTRAL.value)) if conversation.get("user_sentiment") else UserSentiment.NEUTRAL
    mode = conversation.get("mode", ConversationMode.BOT.value)
    
    # Build pipeline input
    context = PipelineInput(
        # Business context
        business_name="Global TaxMaster",
        business_description="Global Tax Masters is a distinguished advisory firm with 15+ years of experience. We have assisted 400+ clients across 20 states, saving over ₹1500 Crores in duties. Our services are cost-effective, with reasonable professional fees tailored to specific client requirements. Core Service (MOOWR Scheme): Allows manufacturing entities (Pvt Ltd, LLP, Partnership, Proprietorship) to import capital goods and raw materials without paying upfront duties. Duty Relief: You do not pay Basic Customs Duty (BCD), IGST, Social Welfare Surcharge, or Anti-Dumping Duty. Payment Terms: Duty is effectively exempted if goods are used for manufacturing indefinitely. Duty is payable only if goods are sold/removed to the domestic market (no interest charged). Future Scope: The license has lifetime validity. Once registered, all future machine imports for that factory are automatically duty-free. Registration & Documents: Timeline & Scope: Approval takes 4–6 weeks. Registration is premises-based (factory-specific); moving locations or adding units requires separate registrations. Verification: Customs Superintendent visits specifically to verify storage safety (CCTV, fire safety, burglary protection). Required Documents: Site Plan, Bank Solvency Certificate, Fire Safety Audit, All-Risk Insurance Policy, Incorporation/Financial documents, and KYC of key personnel. Contact: Email: rohit@saveduty.com | Phone: +91 8797 01 02 03 Address: HD-305, WeWork Futura, Magarpatta, Pune.",  # Mocked for testing
        
        # Conversation context  
        rolling_summary=conversation.get("rolling_summary", ""),
        last_3_messages=last_messages,
        
        # Current state
        conversation_stage=stage,
        conversation_mode=mode,
        intent_level=intent_level,
        user_sentiment=user_sentiment,
        active_cta=None,  # TODO: Get active CTA if any
        
        # Timing
        timing=timing,
        nudges=nudges,
        
        # Constraints (defaults for now)
        max_words=80,
        questions_per_message=1,
        language_pref="en",
    )
    
    return context