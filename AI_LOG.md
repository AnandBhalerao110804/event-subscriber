# AI Log

Brief log of meaningful AI-assisted decisions. Not full transcripts.

---

### 1. Assignment alignment and E2E test flow

**Asked:** Summarize the assignment requirements, check alignment with what was built, and outline an end-to-end test flow.

**Got back:** Feature checklist mapped to existing code, curl examples for subscriptions/events/deliveries, and a step-by-step happy path using httpbin.

**Kept:** The E2E flow and httpbin URLs (`/post` for success, `/status/500` for retries, `/status/404` for no-retry). Used this as my manual test script.

**Rejected:** Nothing — used purely for orientation.

---

### 2. Understanding the data model

**Asked:** What tables exist, how to view them, and what rows appear at each stage of delivery.

**Got back:** Schema breakdown, sqlite3 CLI commands, and expected DB state after ingest, delivery, failures, and manual retry.

**Kept:** SQLite one-liners for inspecting `deliveries` and `delivery_attempts` during testing. Referenced DB Browser for SQLite as a GUI option.

**Rejected:** N/A — factual guidance, no code changes.

---

### 3. Manual retry attempt counting

**Asked:** Should manual retries continue the attempt count or reset it? What do production systems do?

**Got back:** Production systems typically use append-only attempt logs with separate auto-retry budgets. Current code wiped history and restarted numbering at #1.

**Kept:** Append-only approach — preserve `delivery_attempts` rows, continue `attempt_number` from `MAX + 1` (#6 after five failures), reset only `attempt_count` for the auto-retry cycle.

**Rejected:** The original "delete all attempts on manual retry" behavior. Also deferred adding a `manual_retry_count` column and `trigger` field — documented as future improvements instead.

---

### 4. Event types and subscription secrets

**Asked:** What event types can be ingested? What does the subscription `secret` field mean?

**Got back:** Event types are free-form strings (no fixed enum); `secret` is an optional shared key for HMAC-SHA256 signing via `X-Webhook-Signature`.

**Kept:** Used in README API examples and the DECISIONS signing section.

**Rejected:** N/A — factual answers.

---

### 5. Retry testing scenarios

**Asked:** How to test automatic retries and what the DB should look like after five failures plus a manual retry.

**Got back:** Test matrix with httpbin status endpoints, expected delivery statuses over time, and SQL queries to verify state.

**Kept:** The 500 vs 404 test cases. Updated expected attempt numbers after switching to append-only manual retry.

**Modified:** Dashboard labels changed to show "Total attempts" and "Auto retries this cycle" to avoid confusion between cycle counter and lifetime log.

---

### 6. Production retry design (research)

**Asked:** Recommended production approach for tracking manual vs auto retries.

**Got back:** Track lifetime attempts as primary metric; add separate manual retry caps and optional `trigger` column on attempts.

**Kept:** Documented in README "improve with more time" and DECISIONS retry section.

**Rejected:** Implementing manual retry caps in this pass — out of scope for the time box; append-only history was the priority.

---

### 7. Documentation deliverables

**Asked:** What MD files are needed and what should they contain?

**Got back:** Outlines for DECISIONS.md (five topics), AI_LOG.md (5–10 entries with kept/modified/rejected), and README updates.

**Kept:** Structure and content as starting points; personalized AI_LOG entries to reflect actual decisions made during the project.

**Modified:** Trimmed DECISIONS to fit one page; expanded README config table and manual retry behavior note.
