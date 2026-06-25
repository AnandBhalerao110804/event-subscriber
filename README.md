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
- [x] Phase 2: Subscriptions + event ingest
- [x] Phase 3: Delivery worker + retries
- [x] Phase 4: Restart recovery (stale `delivering` → `pending` on worker loop)
- [x] Phase 5: Dashboard (web UI + manual retry)
- [ ] Phase 6: Tests, DECISIONS.md, AI_LOG.md

## Configuration

Copy `.env.example` to `.env`. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_API_KEY` | `dev-admin-key` | Bearer token for admin API routes |
| `DATABASE_PATH` | `data/webhooks.db` | SQLite database file |

## API examples

All admin routes require: `Authorization: Bearer <ADMIN_API_KEY>`

```bash
# Create a subscription
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Authorization: Bearer dev-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://httpbin.org/post","event_filter":"order.*"}'

# List subscriptions
curl http://localhost:8000/api/subscriptions \
  -H "Authorization: Bearer dev-admin-key"

# Ingest an event (creates pending delivery rows for matching subscriptions)
curl -X POST http://localhost:8000/api/events \
  -H "Authorization: Bearer dev-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"type":"order.created","payload":{"id":123}}'

# View event with delivery status (should become "delivered" after a few seconds)
curl http://localhost:8000/api/events/<event_id> \
  -H "Authorization: Bearer dev-admin-key"
```

Deliveries are processed by a background worker (polls every 2s). A `200` response from the subscriber marks the delivery as `delivered`. `5xx` and network errors retry with exponential backoff (max 5 attempts). `4xx` (except `408`/`429`) are marked `dead` without retry.

```bash
# Manually retry a failed/dead delivery
curl -X POST http://localhost:8000/api/deliveries/<delivery_id>/retry \
  -H "Authorization: Bearer dev-admin-key"
```

## Dashboard

Open http://localhost:8000 and sign in with your `ADMIN_API_KEY` (default: `dev-admin-key`).

The dashboard lets you:
- List subscriptions and recent events
- Drill into an event to see deliveries and attempt history
- Manually retry failed or dead deliveries

Interactive API docs: http://localhost:8000/docs

## Running tests

```bash
pytest
```

Or inside Docker:

```bash
docker compose run --rm webhook-service pytest
```

## What's incomplete

See checkboxes above. More detail will be added as phases are completed.

## What I'd improve with more time

- Rate limiting per subscription
- Structured logging and metrics
- OpenAPI examples for all endpoints
# event-subscriber
