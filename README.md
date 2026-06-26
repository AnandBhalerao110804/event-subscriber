# Webhook Delivery Service

A single-process webhook delivery service built with FastAPI and SQLite.

## Quick start (Docker)

```bash
cp .env.example .env   # skip if you already have a .env
docker compose up --build
```

Verify the service is running:

```bash
curl http://localhost:8000/health
```

SQLite data is stored in `./data/webhooks.db` on your machine. Docker bind-mounts that folder, so **Docker and local uvicorn share the same database**.

> If you previously used the old `webhook-data` Docker volume, that data is separate. Copy it out or re-ingest; you can remove the unused volume with `docker volume rm assignment_webhook-data` (name may vary — check `docker volume ls`).

### Local development with hot reload

Docker Compose uses two files:

| File | Role |
|------|------|
| `docker-compose.yml` | Base setup: build image, port 8000, `.env`, shared `./data` volume |
| `docker-compose.dev.yml` | Dev overrides: Uvicorn `--reload` + bind-mount `app/` for live code edits |

Compose merges them when you pass both `-f` flags — you get the base service plus dev-only changes without duplicating the whole file.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This bind-mounts `app/` (code hot reload) and `data/` (same DB as local uvicorn).

## Quick start (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # skip if you already have a .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## What works

- [x] Phase 1: Project skeleton, SQLite schema, health check
- [x] Phase 2: Subscriptions + event ingest
- [x] Phase 3: Delivery worker + retries
- [x] Phase 4: Restart recovery (stale `delivering` → `pending` on worker loop)
- [x] Phase 5: Dashboard (web UI + manual retry)
- [x] Phase 6: Tests, DECISIONS.md, AI_LOG.md

**Features:**
- Subscriptions with target URL, optional shared secret, and event type filters (`*`, exact match, `prefix.*`)
- Event ingest with fan-out to matching subscriptions
- Async delivery worker with exponential backoff retries
- HMAC-SHA256 payload signing (`X-Webhook-Signature`) when a secret is set
- Append-only delivery attempt history; manual retry continues numbering (#6 after five auto failures)
- Dashboard to browse events, view attempt history, and manually retry failed deliveries

## Configuration

Copy `.env.example` to `.env`. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_API_KEY` | `dev-admin-key` | Bearer token for admin API routes and dashboard login |
| `DATABASE_PATH` | `data/webhooks.db` | SQLite database file |
| `WORKER_POLL_INTERVAL_SEC` | `2.0` | How often the worker checks for due deliveries |
| `DELIVERY_TIMEOUT_SEC` | `10.0` | HTTP timeout per delivery attempt |
| `MAX_DELIVERY_ATTEMPTS` | `5` | Max auto attempts per retry cycle |
| `RETRY_BASE_DELAY_SEC` | `1.0` | Base delay for exponential backoff |
| `RETRY_MAX_DELAY_SEC` | `60.0` | Cap on retry delay |
| `STALE_DELIVERING_SEC` | `120` | Reset stuck `delivering` rows after this many seconds |

## API examples

All admin routes require: `Authorization: Bearer <ADMIN_API_KEY>`

```bash
# Create a subscription
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Authorization: Bearer dev-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://httpbin.org/post","event_filter":"order.*","secret":"my-secret"}'

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

Deliveries are processed by a background worker (polls every 2s). A `200` response from the subscriber marks the delivery as `delivered`. `5xx` and network errors retry with exponential backoff (max 5 attempts per cycle). `4xx` (except `408`/`429`) are marked `dead` without retry.

```bash
# Manually retry a failed/dead delivery
curl -X POST http://localhost:8000/api/deliveries/<delivery_id>/retry \
  -H "Authorization: Bearer dev-admin-key"
```

Manual retry resets the auto-retry cycle (`attempt_count → 0`) but preserves attempt history. Attempt numbers continue from where they left off (e.g. #1–#5, then #6 after manual retry).

### Testing retries

```bash
# Always returns 500 — triggers auto retries, eventually dead
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Authorization: Bearer dev-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://httpbin.org/status/500","event_filter":"*"}'

# Always returns 404 — one attempt, then dead (no retry)
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Authorization: Bearer dev-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://httpbin.org/status/404","event_filter":"*"}'
```

## Dashboard

Open http://localhost:8000 and sign in with your `ADMIN_API_KEY` (default: `dev-admin-key`).

The dashboard lets you:
- List subscriptions and recent events
- Drill into an event to see deliveries and attempt history
- Manually retry failed or dead deliveries

Interactive API docs: http://localhost:8000/docs

In Swagger UI, click **Authorize**, enter your `ADMIN_API_KEY` (e.g. `dev-admin-key`), then try endpoints. Postman and curl still use `Authorization: Bearer <ADMIN_API_KEY>` unchanged.

## Running tests

With the virtualenv activated (local):

```bash
pytest
```

Or inside Docker (requires a rebuild after pulling test files into the image):

```bash
docker compose run --rm webhook-service pytest
```

## What's incomplete

- No rate limiting per subscription (a down endpoint can be retried indefinitely via manual retry)
- No cap on manual retries (operators can re-queue `dead` deliveries without limit)
- Subscription management is API-only (no create form in the dashboard)
- Single shared admin key (by design per assignment — not real auth)

## What I'd improve with more time

- Cap manual retries with cooldown to prevent retry storms
- `trigger` column on delivery attempts (`auto` vs `manual`) for ops visibility
- Rate limiting per subscription
- Structured logging and metrics (delivery latency, success rate)
- OpenAPI examples for all endpoints
