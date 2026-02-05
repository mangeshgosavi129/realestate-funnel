# WhatsApp Funnel AI: Eyes → Brain → Mouth → Memory Architecture

## 1. Project Overview
This project is an **AI-Driven Sales Agent** for WhatsApp using a **4-Stage Pipeline** that mimics human cognitive processing.

### Core Philosophy
- **Intentionality**: The AI never "just talks". It observes, strategizes, then communicates.
- **Separation of Concerns**: Each stage has ONE job — Eyes observe, Brain decides, Mouth speaks, Memory remembers.
- **Micro-State Management**: Conversations tracked via explicit stages (`GREETING`, `QUALIFICATION`, `PRICING`, etc.).
- **Self-Healing**: Background workers handle follow-ups if users go silent.

---

## 2. The 4-Stage Pipeline

```
┌─────────────┐    observation    ┌─────────────┐    implementation_plan    ┌─────────────┐
│    EYES     │ ───────────────► │    BRAIN    │ ─────────────────────────►│    MOUTH    │
│  (Observer) │                   │ (Strategist)│                           │(Communicator)│
└─────────────┘                   └─────────────┘                           └─────────────┘
       │                                 │                                         │
       │ intent, sentiment               │ action, stage                           │ message_text
       │ risk_flags                      │ needs_human_attention                   │
       ▼                                 ▼                                         ▼
                                                                            ┌─────────────┐
                                        ◄───────────────────────────────────│   MEMORY    │
                                                                            │ (Archivist) │
                                                                            └─────────────┘
```

### Stage Responsibilities

| Stage | Role | Input | Output |
|-------|------|-------|--------|
| **Eyes** | Observe & Analyze | `PipelineInput` | `observation`, intent, sentiment, risks |
| **Brain** | Decide & Strategize | Eyes observation | `implementation_plan`, action, stage, CTA |
| **Mouth** | Communicate | Brain's plan | `message_text` |
| **Memory** | Compress & Retain | Mouth's output | `updated_rolling_summary` |

### Key Handoff: `implementation_plan`
Brain passes a natural language instruction to Mouth:
```
"Send a friendly follow-up asking about their timeline. Mention the free consultation CTA."
```

---

## 3. Architecture & Components

### A. The Server (`/server`)
- **Framework**: FastAPI (Python)
- **Role**: Source of Truth — DB, API endpoints, WebSockets, Auth
- **Database**: PostgreSQL

### B. The Worker (`/whatsapp_worker`)
- **Technique**: Celery + Redis
- **Flow**: Webhook → Fetch Context → Run Pipeline → Send Response → Persist State

### C. The LLM Pipeline (`/llm`)
| File | Purpose |
|------|---------|
| `pipeline.py` | Orchestrates Eyes → Brain → Mouth |
| `prompts.py` | 8 prompts (4 SYSTEM + 4 USER_TEMPLATE) |
| `schemas.py` | `EyesOutput`, `BrainOutput`, `MouthOutput`, `MemoryOutput`, `PipelineResult` |
| `steps/eyes.py` | Observer — analyzes conversation |
| `steps/brain.py` | Strategist — decides action |
| `steps/mouth.py` | Communicator — generates message |
| `steps/memory.py` | Archivist — updates rolling summary |
| `utils.py` | Enum normalization, formatting |

### D. The Frontend (`/frontend`)
- **Framework**: Next.js + React
- **Role**: Dashboard for monitoring and intervention

---

## 4. Pipeline Flow Example

**Scenario**: User asks about price during qualification.

### Step 1: EYES (Observer)
```json
{
  "observation": "User asking about pricing. Shows buying intent. Ready for price discussion.",
  "intent_level": "high",
  "user_sentiment": "curious",
  "confidence": 0.85
}
```

### Step 2: BRAIN (Strategist)
```json
{
  "implementation_plan": "Provide pricing range based on 100 units. Ask about budget fit.",
  "action": "send_now",
  "new_stage": "pricing",
  "should_respond": true
}
```

### Step 3: MOUTH (Communicator)
```json
{
  "message_text": "For 100 units, pricing starts at $500/mo. Does that fit your budget?"
}
```

### Step 4: MEMORY (Archivist)
Updates rolling summary with the exchange.

---

## 5. Key Files

### `/llm` (Intelligence Core)
| File | Purpose |
|------|---------|
| `pipeline.py` | Entry point (`run_pipeline`) |
| `prompts.py` | All 8 prompts (SYSTEM + USER_TEMPLATE) |
| `schemas.py` | Pydantic schemas for all stages |
| `steps/eyes.py` | Observer implementation |
| `steps/brain.py` | Strategist implementation |
| `steps/mouth.py` | Communicator implementation |
| `steps/memory.py` | Archivist implementation |

### `/server` (Backend)
| File | Purpose |
|------|---------|
| `main.py` | FastAPI entry point |
| `routes/internals.py` | Internal API for Worker |
| `enums.py` | `ConversationStage`, `IntentLevel`, `DecisionAction`, etc. |

### `/whatsapp_worker` (Hands)
| File | Purpose |
|------|---------|
| `main.py` | Webhook receiver |
| `processors/context.py` | Builds `PipelineInput` |
| `processors/actions.py` | Handles post-pipeline actions |

---

## 6. Development Setup

### Prerequisites
- Python 3.10+, Node.js 18+, PostgreSQL, Redis

### Installation
```bash
# Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with API keys, DATABASE_URL, etc.
```

### Run Services
```bash
# Server
uvicorn server.main:app --reload

# Worker
celery -A whatsapp_worker.celery_app worker --loglevel=info -P solo

# Frontend
cd frontend && npm install && npm run dev
```

### Testing the Pipeline
```bash
# Interactive mode
python tests/simulate_htl.py

# Automated tests
python tests/simulate_htl.py --test
```

---

## 7. Important Context for AI Agents

1. **Stage Separation**:
   - Eyes: Only observes (no decisions)
   - Brain: Only decides (no message generation)
   - Mouth: Only generates (follows Brain's `implementation_plan`)
   - Memory: Only summarizes (runs after Mouth)

2. **Prompt Structure**:
   - 4 `*_SYSTEM_PROMPT` constants (static persona/rules)
   - 4 `*_USER_TEMPLATE` constants (dynamic context injection)
   - All in `llm/prompts.py`

3. **Enum Synchronization**:
   - If you change `server/enums.py`, update the inline schemas in step files.

4. **Internal API Pattern**:
   - Worker doesn't touch DB directly — uses `server/routes/internals.py`.
