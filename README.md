# Webhook Delivery Service

A single-process webhook delivery service built with FastAPI and SQLite.

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Verify the service is running:

```bash
curl http://localhost:8000/health
```

SQLite data is stored in a Docker volume (`webhook-data`) so it survives container restarts.

### Local development with hot reload

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This bind-mounts `app/` and runs Uvicorn with `--reload`.

## Quick start (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## What works

- [x] Phase 1: Project skeleton, SQLite schema, health check
- [ ] Phase 2: Subscriptions + event ingest
- [ ] Phase 3: Delivery worker + retries
- [ ] Phase 4: Restart recovery
- [ ] Phase 5: Dashboard
- [ ] Phase 6: Tests, DECISIONS.md, AI_LOG.md

## Configuration

Copy `.env.example` to `.env`. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_API_KEY` | `dev-admin-key` | Bearer token for admin API routes |
| `DATABASE_PATH` | `data/webhooks.db` | SQLite database file |

## What's incomplete

See checkboxes above. More detail will be added as phases are completed.

## What I'd improve with more time

- Rate limiting per subscription
- Structured logging and metrics
- OpenAPI examples for all endpoints
# event-subscriber
