import json
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.db import get_connection
from app.utils import new_id, utc_now_iso


def _delivery_context_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "subscription_id": row["subscription_id"],
        "status": row["status"],
        "attempt_count": row["attempt_count"],
        "next_attempt_at": row["next_attempt_at"],
        "last_status_code": row["last_status_code"],
        "last_error": row["last_error"],
        "updated_at": row["updated_at"],
        "event_type": row["event_type"],
        "event_payload": json.loads(row["event_payload"]),
        "subscription_url": row["subscription_url"],
        "subscription_secret": row["subscription_secret"],
    }


def recover_stale_deliveries() -> int:
    cutoff = (
        datetime.now(UTC).replace(microsecond=0) - timedelta(seconds=settings.stale_delivering_sec)
    ).isoformat().replace("+00:00", "Z")
    now = utc_now_iso()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE deliveries
            SET status = 'pending', updated_at = ?
            WHERE status = 'delivering' AND updated_at < ?
            """,
            (now, cutoff),
        )
        conn.commit()
        return cursor.rowcount


def fetch_due_deliveries(limit: int = 20) -> list[dict]:
    now = utc_now_iso()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                d.id,
                d.event_id,
                d.subscription_id,
                d.status,
                d.attempt_count,
                d.next_attempt_at,
                d.last_status_code,
                d.last_error,
                d.updated_at,
                e.type AS event_type,
                e.payload AS event_payload,
                s.url AS subscription_url,
                s.secret AS subscription_secret
            FROM deliveries d
            JOIN events e ON e.id = d.event_id
            JOIN subscriptions s ON s.id = d.subscription_id
            WHERE d.status IN ('pending', 'failed')
              AND d.next_attempt_at <= ?
              AND d.attempt_count < ?
            ORDER BY d.next_attempt_at ASC, d.id ASC
            LIMIT ?
            """,
            (now, settings.max_delivery_attempts, limit),
        ).fetchall()
    return [_delivery_context_row_to_dict(row) for row in rows]


def claim_delivery(delivery_id: str) -> bool:
    now = utc_now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE deliveries
            SET status = 'delivering', updated_at = ?
            WHERE id = ? AND status IN ('pending', 'failed')
            """,
            (now, delivery_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def record_delivery_result(
    delivery_id: str,
    status_code: int | None,
    error: str | None,
    duration_ms: int,
    new_status: str,
    new_attempt_count: int,
    next_attempt_at: str | None,
) -> None:
    now = utc_now_iso()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(MAX(attempt_number), 0) AS max_attempt
            FROM delivery_attempts
            WHERE delivery_id = ?
            """,
            (delivery_id,),
        ).fetchone()
        attempt_number = row["max_attempt"] + 1

        conn.execute(
            """
            INSERT INTO delivery_attempts (
                id, delivery_id, attempt_number, status_code, error, duration_ms, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id(), delivery_id, attempt_number, status_code, error, duration_ms, now),
        )
        conn.execute(
            """
            UPDATE deliveries
            SET status = ?,
                attempt_count = ?,
                next_attempt_at = COALESCE(?, next_attempt_at),
                last_status_code = ?,
                last_error = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                new_status,
                new_attempt_count,
                next_attempt_at,
                status_code,
                error,
                now,
                delivery_id,
            ),
        )
        conn.commit()


def get_delivery_attempts(delivery_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, delivery_id, attempt_number, status_code, error, duration_ms, created_at
            FROM delivery_attempts
            WHERE delivery_id = ?
            ORDER BY created_at ASC, attempt_number ASC
            """,
            (delivery_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "delivery_id": row["delivery_id"],
            "attempt_number": row["attempt_number"],
            "status_code": row["status_code"],
            "error": row["error"],
            "duration_ms": row["duration_ms"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def retry_delivery(delivery_id: str) -> bool:
    now = utc_now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE deliveries
            SET status = 'pending',
                attempt_count = 0,
                next_attempt_at = ?,
                last_status_code = NULL,
                last_error = NULL,
                updated_at = ?
            WHERE id = ? AND status IN ('failed', 'dead')
            """,
            (now, now, delivery_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_delivery(delivery_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT d.*, s.url AS subscription_url
            FROM deliveries d
            JOIN subscriptions s ON s.id = d.subscription_id
            WHERE d.id = ?
            """,
            (delivery_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "subscription_id": row["subscription_id"],
        "subscription_url": row["subscription_url"],
        "status": row["status"],
        "attempt_count": row["attempt_count"],
        "next_attempt_at": row["next_attempt_at"],
        "last_status_code": row["last_status_code"],
        "last_error": row["last_error"],
        "updated_at": row["updated_at"],
    }
