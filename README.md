# Real Estate WhatsApp Funnel

A multi-service backend that powers a WhatsApp-first real estate lead funnel. The system ingests Meta/WhatsApp webhooks, queues inbound messages, processes them through an LLM-driven conversation pipeline, and persists/updates lead and conversation data via an internal API. It also schedules follow-ups with Celery for proactive outreach.

## Architecture overview

**Core flow**
1. **Webhook receiver (whatsapp_receive)** accepts Meta webhook verification and inbound messages.
2. **SQS queue** buffers messages for asynchronous processing.
3. **Worker (whatsapp_worker)** pulls from SQS, validates signatures, enriches context with internal API data, runs the LLM pipeline, sends responses via WhatsApp, and updates the database.
4. **Internal API (server)** provides persistence, authentication, analytics, and business configuration.
5. **LLM pipeline (llm)** performs the Eyes → Brain → Mouth → Memory flow for intent detection, strategy, message generation, and conversation summarization.

**Follow-ups**
- **Celery beat** triggers periodic follow-up checks and sends scheduled messages when needed.

```
┌───────────────────┐     ┌────────────┐     ┌──────────────────────┐
│ WhatsApp Webhook  │ --> │ SQS Queue  │ --> │ WhatsApp Worker       │
│ (whatsapp_receive)│     └────────────┘     │  - Signature verify   │
└───────────────────┘                        │  - LLM pipeline       │
                                             │  - Send WA message    │
                                             │  - Update API/DB       │
                                             └─────────┬────────────┘
                                                       │
                                                       v
                                             ┌──────────────────────┐
                                             │ Internal API (server)│
                                             │  - DB + auth         │
                                             └──────────────────────┘
```

## Repository layout

```
.
├── llm/                  # LLM pipeline and prompt orchestration
├── server/               # FastAPI internal API + database models
├── whatsapp_receive/     # Webhook receiver (Lambda-friendly)
├── whatsapp_worker/      # SQS consumer + Celery tasks
├── scripts/              # Maintenance / migration helpers
├── logging_config.py     # Shared logging setup
├── requirements.txt      # Base Python dependencies
└── .env.example           # Sample environment variables
```

## Services

### 1) Internal API (`server/`)
FastAPI app that owns data persistence and business logic. It auto-creates tables on startup and exposes endpoints for authentication, leads, conversations, templates, analytics, and more. The API also powers the frontend UI for live conversation and lead details, with WebSockets providing real-time updates.

**Entry point**: `server/main.py`

**Key modules**:
- `server/database.py` — SQLAlchemy engine and base model setup.
- `server/routes/` — FastAPI routers (auth, leads, conversations, messages, analytics, templates, dashboards, etc.).
- `server/security.py` — JWT auth helpers and hashing.

### 2) Webhook receiver (`whatsapp_receive/`)
A lightweight FastAPI app designed for AWS Lambda (via Mangum). It handles:
- **GET /webhook** — Meta webhook verification.
- **POST /webhook** — Receives inbound messages and pushes them to SQS.

**Entry point**: `whatsapp_receive/main.py`

### 3) Worker (`whatsapp_worker/`)
Consumes SQS messages, validates Meta signatures, loads org + conversation context from the internal API, runs the LLM pipeline, and sends replies via WhatsApp.

**Entry point**: `whatsapp_worker/main.py`

**Key behaviors**:
- Signature validation uses a dynamic `app_secret` fetched from the internal API.
- Debounces quick successive messages for the same user.
- Stores inbound messages before generating a response.

### 4) LLM pipeline (`llm/`)
Implements the **Eyes → Brain → Mouth → Memory** workflow:
- **Eyes**: Observe the conversation and detect intent, sentiment, and risks.
- **Brain**: Decide action (respond, schedule, CTA, or wait) and update stage.
- **Mouth**: Generate the outbound message when needed.
- **Memory**: Summarize conversation into a rolling summary.

**Entry point**: `llm/pipeline.py`

## Environment configuration

Create a `.env.dev` file (loaded by most services) or use environment variables directly. A sample is available in `.env.example`.

### Required variables (core)
- `DATABASE_URL` — SQLAlchemy connection string.
- `SECRET_KEY` — JWT secret.
- `ALGORITHM` — JWT algorithm (e.g., HS256).
- `INTERNAL_API_BASE_URL` — Base URL of the internal API.
- `INTERNAL_API_SECRET` — Shared secret for internal API auth.

### WhatsApp/SQS
- `QUEUE_URL`
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Webhook receiver (Lambda configuration)
- `QUEUE_URL`
- `AWS_REGION_SQS`
- `AWS_ACCESS_KEY_ID_SQS`
- `AWS_SECRET_ACCESS_KEY_SQS`
- `VERIFY_TOKEN`

### LLM
- `GROQ_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`

### Celery (follow-ups)
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## Local development

### Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the internal API
```bash
uvicorn server.main:app --reload
```

### Run the webhook receiver
```bash
uvicorn whatsapp_receive.main:app --reload
```

### Run the worker
```bash
python -m whatsapp_worker.main
```

### Run Celery (scheduled follow-ups)
```bash
celery -A whatsapp_worker.tasks.celery_app worker --loglevel=info
celery -A whatsapp_worker.tasks.celery_app beat --loglevel=info
```

## Operational notes

- **Logging**: `logging_config.py` sets up colored console logs and rotating file logs for `server`, `whatsapp_worker`, `llm`, and `celery`.
- **Database auto-create**: The internal API creates missing tables at startup.
- **Debouncing**: The worker batches rapid successive messages to avoid spamming users with multiple replies.

## Scripts

The `scripts/` folder contains helpers for database migrations, template updates, and debugging. Examples include:
- `scripts/seed_db.py` — seed baseline data
- `scripts/migrate_templates.py` — migrate template data
- `scripts/debug_db_state.py` — inspect database state

Run scripts directly with `python` when needed.

## High-level request flow

1. User sends a WhatsApp message.
2. Meta calls **POST /webhook** (whatsapp_receive).
3. Payload is queued in SQS.
4. Worker pulls the message, verifies signature, and loads context from the internal API.
5. LLM pipeline generates a response (if required).
6. Worker sends the reply and persists updates (conversation stage, summaries, follow-ups).

## Troubleshooting

- **Webhook verification fails**: confirm `VERIFY_TOKEN` matches Meta settings.
- **Signature validation fails**: ensure `INTERNAL_API_BASE_URL` and `INTERNAL_API_SECRET` allow fetching app secrets, and verify Meta headers are forwarded to the worker.
- **No responses sent**: check LLM env variables and outbound WhatsApp configuration.
- **Follow-ups not firing**: verify Celery worker + beat are running and Redis is available.

## License

No license file is currently present. Add one if you plan to open-source the project.
