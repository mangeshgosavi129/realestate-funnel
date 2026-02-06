# TODO

This document captures potential risks, current gaps, and forward-looking tasks to help evolve the project safely and sustainably.

## Potential issues / risks

1. **Environment variable drift across services**
   - Multiple services load env vars from different locations and names (e.g., `.env.dev` vs Lambda env, and different AWS/SQS variable names). This can lead to misconfigurations between local and production.

2. **Missing runtime health checks for worker and queueing**
   - The worker uses long-polling SQS, but there is no explicit health endpoint or metric emission to detect stuck processing, queue backlog, or message retry churn.

3. **Lack of explicit retry/backoff strategy**
   - On transient failures (e.g., internal API outage, WhatsApp API errors), the worker logs and relies on SQS retries but does not implement targeted backoff or dead-letter queue handling guidance in code.

4. **Limited observability for LLM usage**
   - LLM steps record timing and token usage but the values are not persisted to the database or centralized monitoring, which makes cost tracking and performance tuning difficult.

5. **Database migrations and schema management**
   - The API auto-creates tables at runtime; there is no documented or enforced migration workflow for schema changes, which can lead to production drift.

6. **Websocket lifecycle management**
   - WebSocket routes exist, but there is no explicit mention of connection cleanup, reconnection strategy, or scaling approach for multiple instances.

7. **Inconsistent error handling across services**
   - Some modules return generic error responses without structured error codes or consistent error schema, which makes debugging and client handling harder.

8. **Security posture for secrets and internal APIs**
   - The internal API secret is used for critical lookups and signature verification. Rotations, TTLs, and least-privilege access are not documented.

9. **Production readiness of logging**
   - File-based rotating logs are configured locally; centralized logging integrations for production deployments are not documented.

10. **No explicit rate limiting / abuse controls**
   - The system accepts inbound webhook traffic and API requests, but there is no clear rate limiting or abuse mitigation configured.

## Recommended tasks for project progression

### Configuration & deployment
- [ ] Define a single source of truth for environment configuration (e.g., a shared schema or `.env` template per service) and document it.
- [ ] Add deployment-specific configuration docs (Lambda + worker + API).
- [ ] Add a production checklist that covers secrets, logging, monitoring, and scaling.

### Reliability & observability
- [ ] Add health endpoints and metrics for `whatsapp_worker` (queue depth, processing time, error rate).
- [ ] Add a dead-letter queue (DLQ) strategy and explicit retry/backoff handling for failed messages.
- [ ] Persist LLM usage metrics (tokens/latency) for cost analysis and debugging.
- [ ] Add structured logging (JSON logs) for production observability.

### Data & migrations
- [ ] Adopt Alembic migrations for schema evolution and document the workflow.
- [ ] Add seed scripts for baseline entities and reference data (templates, CTAs, etc.).

### Security & access
- [ ] Document secret rotation strategy and minimum required permissions for each service.
- [ ] Add API rate limiting and webhook abuse detection.
- [ ] Ensure internal API endpoints are explicitly scoped and audited.

### Product & UX
- [ ] Define standard event payloads for WebSocket updates (new message, lead updates, stage changes).
- [ ] Add frontend-friendly error codes and user-facing error messages.

### Testing
- [ ] Add automated tests for core webhook parsing and signature validation.
- [ ] Add integration tests for the full message flow (webhook → queue → worker → API).
- [ ] Add LLM prompt regression tests to reduce response drift.
