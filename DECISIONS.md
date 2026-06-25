# Design Decisions

## Storage

**Choice:** SQLite with four tables — `subscriptions`, `events`, `deliveries`, and `delivery_attempts`.

**Alternatives considered:** In-memory storage (rejected — events must survive restart); PostgreSQL (rejected — extra infra for a single-process take-home).

**Why:** SQLite needs no separate service, persists to a file on disk, and is sufficient for one worker polling due deliveries. Events and delivery rows are written before any HTTP call, so ingest is durable even if the process crashes before delivery.

## Concurrency / worker model

**Choice:** Single FastAPI process with an asyncio background worker started in the app lifespan. The worker polls every 2 seconds, fetches due deliveries, claims them (`status → delivering`), and POSTs via `httpx.AsyncClient`.

**Alternatives considered:** Separate worker process; thread pool; message queue (Redis, SQS).

**Why:** The assignment expects one runnable process with clear module boundaries. Async I/O handles outbound HTTP without extra services. `claim_delivery` prevents double-sends within a single process. `recover_stale_deliveries` resets rows stuck in `delivering` for longer than 120 seconds after a crash mid-request.

## Retry policy

**Choice:** Exponential backoff (base 1s, cap 60s), max 5 auto attempts per cycle. Retry on 5xx, network errors, 408, and 429. Other 4xx responses are marked `dead` with no retry. Manual retry re-queues `failed`/`dead` deliveries with a fresh auto budget (`attempt_count → 0`) but keeps an append-only attempt log — numbering continues (#1–#5, then #6 after manual retry).

**Alternatives considered:** Fixed delay between retries; jitter; infinite retries; wiping attempt history on manual retry.

**Why:** Matches common webhook guidance: 2xx is success, most 4xx is permanent, 5xx and transient errors deserve backoff. Append-only attempts preserve an audit trail; resetting only the cycle counter lets operators trigger another batch of auto retries without losing history.

## Payload signing

**Choice:** HMAC-SHA256 over the raw JSON body, sent as `X-Webhook-Signature: sha256=<hex>`. Signing is optional per subscription (only when a `secret` is provided).

**Alternatives considered:** No signing; JWT; asymmetric keys (RSA).

**Why:** Same pattern as Stripe and GitHub webhooks — a shared secret both sides know, subscriber verifies authenticity and integrity. Skipping the signature when no secret is set keeps local testing simple.

## Dashboard scope

**Choice:** Minimal Jinja2 UI — admin key login (cookie), home page listing subscriptions and recent events, event detail page showing deliveries and attempt history with a manual retry button. Subscription creation is API-only.

**Alternatives considered:** React SPA; full CRUD in the UI; real authentication.

**Why:** The assignment says a table view and detail view is enough. Cookie auth reuses the same admin key as the API. Keeping the UI read-heavy plus retry avoids scope creep; subscription management via curl or `/docs` is acceptable for the time box.
