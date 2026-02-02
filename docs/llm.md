# LLM Module Documentation (Human Thinking Layer)

This document provides an in-depth analysis of the `llm` directory, which implements the **Human Thinking Layer (HTL)** pipeline for the WhatsApp Token Sales Bot.

## 1. Overview

The `llm` module is designed to give the bot "human-like" reasoning capabilities by decoupling **decision-making** (The Brain) from **response generation** (The Mouth). It uses a **Router-Agent Architecture** to ensuring high control, safety, and sales effectiveness.

**Key Goals:**
- **State Awareness:** Tracks where usage is in the sales funnel (Greeting, Qualification, Closing, etc.).
- **Separation of Concerns:** Decisions are made before any text is written.
- **Strict Typing:** All LLM inputs and outputs are validated against Pydantic schemas.
- **Reliability:** Robust error handling, retries, and fallbacks.

## 2. Architecture: Router-Agent Pipeline

The core logic is orchestrated by `pipeline.py`. The flow consists of three distinct steps:

```mermaid
flowchart LR
    Input[PipelineInput] --> Classify[Step 1: CLASSIFY\n(The Brain)]
    Classify --> Decision{Should Respond?}
    Decision -- Yes --> Generate[Step 2: GENERATE\n(The Mouth)]
    Decision -- No --> Result[PipelineResult]
    Generate --> Result
    Result -.-> Summarize[Step 3: SUMMARIZE\n(The Memory)]
```

### The Three Steps:

1.  **Step 1: CLASSIFY (The Brain)**
    *   **Goal:** Analyze context, assess risk, determine intent, and decide the *next best action*.
    *   **Output:** Action (Send/Wait), New Stage, Thought Process.
    *   **File:** `steps/classify.py`

2.  **Step 2: GENERATE (The Mouth)**
    *   **Goal:** Write the actual response text based on the Brain's instructions.
    *   **Input:** Context + Brain's Decision.
    *   **Output:** Message Text, CTA, Updated State.
    *   **File:** `steps/generate.py`

3.  **Step 3: SUMMARIZE (The Memory)**
    *   **Goal:** Update the rolling summary to maintain long-term context within token limits.
    *   **Execution:** Designed to run asynchronously/background to reduce user latency.
    *   **File:** `steps/summarize.py`

## 3. Component Deep Dive

### 3.1 Entry Points
- **`main.py`**: Exports the main `run_pipeline` function and all necessary schemas. This is the public API of the module.
- **`pipeline.py`**: The orchestrator that calls the steps in order and aggregates performance metrics (latency, tokens).

### 3.2 Data Structures (`schemas.py`)
Safety is enforced via strict Pydantic models.
- **`PipelineInput`**: The "God Object" containing everything the LLM needs to know (Business info, History, Current State, Timing).
- **`ClassifyOutput`**: Structured decision data (e.g., `risk_flags`, `intent_level`, `should_respond`).
- **`GenerateOutput`**: The final message and any self-checks.
- **`PipelineResult`**: The final return object containing the outputs of all steps.

### 3.3 Prompt Management (`prompts_registry.py`)
This module solves the "Context Pollution" problem where a bot gets confused about its goal.
- **Dynamic System Prompts:** Instead of one giant system prompt, it generates a targeted prompt based on the **Current Conversation Stage**.
- **Stages:**
    - `GREETING`: Focus on acknowledging user.
    - `QUALIFICATION`: Focus on gathering requirements.
    - `PRICING`: Focus on value and quotes.
    - `CTA`: Focus on closing.
    - ...and more.

### 3.4 Utilities
- **`api_helpers.py`**:
    - `llm_call_with_retry`: Handles API errors and retries.
    - `extract_json_from_text`: Robustly parses JSON even if the model "thinks" out loud before outputting JSON.
- **`utils.py`**:
    - `normalize_enum`: Fuzzy matching for enums (e.g., maps "send" -> `DecisionAction.SEND_NOW`).
    - **JSON Schemas**: Generates strict JSON schemas for the LLM configuration to ensure the model outputs exactly what we expect.
- **`config.py`**:
    - Loads environment variables (API keys, Model IDs).
    - Defaults to Groq for high-speed inference.

## 4. Usage Example

```python
from llm.main import run_pipeline
from llm.schemas import PipelineInput, MessageContext, ConversationStage

# 1. Build Context
context = PipelineInput(
    business_name="Acme Corp",
    conversation_stage=ConversationStage.GREETING,
    last_3_messages=[
        MessageContext(sender="human", text="Hi, tell me about your pricing", timestamp="...")
    ],
    # ... other fields
)

# 2. Run Pipeline
result = run_pipeline(context, user_message="Hi, tell me about your pricing")

# 3. Use Result
if result.should_send_message:
    print(f"Bot says: {result.response.message_text}")
    print(f"New Stage: {result.classification.new_stage}")
```

## 5. Directory Structure

```text
llm/
├── main.py                 # Public API entry point
├── pipeline.py             # Orchestrates steps
├── schemas.py              # Pydantic models (Input/Output)
├── prompts_registry.py     # Dynamic system prompts per stage
├── prompts.py              # Static template strings
├── config.py               # Env var loading
├── utils.py                # Schema generation & enum helpers
├── api_helpers.py          # Groq API client & retry logic
└── steps/                  # Implementation of pipeline steps
    ├── classify.py         # Step 1: Decision Logic
    ├── generate.py         # Step 2: Response Generation
    └── summarize.py        # Step 3: Context Summarization
```
