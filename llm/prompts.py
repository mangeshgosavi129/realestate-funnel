"""
LLM Prompts for Eyes → Brain → Mouth → Memory Pipeline.
Each stage has SYSTEM (static) and USER_TEMPLATE (dynamic) prompts.
"""

# ============================================================
# EYES - Observer
# ============================================================

EYES_SYSTEM_PROMPT = """
You are the Eyes of a sales assistant. Your role is to observe and analyze.
TODO: Full prompt implementation
"""

EYES_USER_TEMPLATE = """
## Context
Rolling Summary: {rolling_summary}
Current Stage: {conversation_stage}
Intent Level: {intent_level}
User Sentiment: {user_sentiment}

## Timing
Now: {now_local}
WhatsApp Window Open: {whatsapp_window_open}

## Recent Messages
{last_messages}

Analyze this conversation and provide your observation.
"""


# ============================================================
# BRAIN - Strategist
# ============================================================

BRAIN_SYSTEM_PROMPT = """
You are the Brain of a sales assistant. Your role is to decide and strategize.
TODO: Full prompt implementation
"""

BRAIN_USER_TEMPLATE = """
## Observation from Eyes
{observation}

## Available CTAs
{available_ctas}

## Nudge Context
Followups in 24h: {followup_count_24h}
Total Nudges: {total_nudges}

## Timing
Now: {now_local}
WhatsApp Window Open: {whatsapp_window_open}

Decide the next action and create an implementation plan for the Mouth.
"""


# ============================================================
# MOUTH - Communicator
# ============================================================

MOUTH_SYSTEM_PROMPT = """
You are the Mouth of a sales assistant for {business_name}. Your role is to communicate.
{business_description}

Constraints:
- Max {max_words} words
- Max {questions_per_message} questions per message

TODO: Full prompt implementation
"""

MOUTH_USER_TEMPLATE = """
## Implementation Plan from Brain
{implementation_plan}

## Business Context
Business: {business_name}

## Available CTAs
{available_ctas}

## Recent Messages (for context)
{last_messages}

Write the message following the implementation plan.
"""


# ============================================================
# MEMORY - Archivist
# ============================================================

MEMORY_SYSTEM_PROMPT = """
You are the Memory of a sales assistant. Your role is to compress and retain context.
TODO: Full prompt implementation
"""

MEMORY_USER_TEMPLATE = """
## Current Rolling Summary
{rolling_summary}

## New Exchange
User: {user_message}
Bot: {bot_message}

## Action Taken
{action_taken}

Update the rolling summary to include this exchange.
"""