import json

from app.db import get_connection
from app.delivery_summary import summarize_delivery_statuses
from app.matcher import matches_filter
from app.repositories import deliveries as delivery_repo
from app.repositories import subscriptions as subscription_repo
from app.utils import new_id, utc_now_iso


def _event_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "payload": json.loads(row["payload"]),
        "created_at": row["created_at"],
    }


def _delivery_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "subscription_id": row["subscription_id"],
        "subscription_url": row["subscription_url"],
        "status": row["status"],
        "attempt_count": row["attempt_count"],
        "next_attempt_at": row["next_attempt_at"],
        "last_status_code": row["last_status_code"],
        "last_error": row["last_error"],
        "updated_at": row["updated_at"],
    }


def create_event(event_type: str, payload: dict) -> tuple[dict, int]:
    event_id = new_id()
    created_at = utc_now_iso()
    payload_json = json.dumps(payload)

    active_subscriptions = subscription_repo.list_active_subscriptions()
    matching = [
        sub for sub in active_subscriptions if matches_filter(sub["event_filter"], event_type)
    ]

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO events (id, type, payload, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, event_type, payload_json, created_at),
        )

        now = utc_now_iso()
        for sub in matching:
            conn.execute(
                """
                INSERT INTO deliveries (
                    id, event_id, subscription_id, status,
                    attempt_count, next_attempt_at, updated_at
                )
                VALUES (?, ?, ?, 'pending', 0, ?, ?)
                """,
                (new_id(), event_id, sub["id"], now, now),
            )

        conn.commit()
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    return _event_row_to_dict(row), len(matching)


def list_events(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_event_row_to_dict(row) for row in rows]


def list_events_with_summary(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        event_rows = conn.execute(
            """
            SELECT * FROM events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        if not event_rows:
            return []

        event_ids = [row["id"] for row in event_rows]
        placeholders = ",".join("?" for _ in event_ids)
        delivery_rows = conn.execute(
            f"""
            SELECT event_id, status
            FROM deliveries
            WHERE event_id IN ({placeholders})
            """,
            event_ids,
        ).fetchall()

    statuses_by_event: dict[str, list[str]] = {event_id: [] for event_id in event_ids}
    for row in delivery_rows:
        statuses_by_event[row["event_id"]].append(row["status"])

    events = []
    for row in event_rows:
        event = _event_row_to_dict(row)
        delivery_statuses = statuses_by_event[event["id"]]
        event["delivery_count"] = len(delivery_statuses)
        event["delivery_summary"] = summarize_delivery_statuses(delivery_statuses)
        events.append(event)
    return events


def get_event_with_deliveries(event_id: str) -> dict | None:
    with get_connection() as conn:
        event_row = conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        if not event_row:
            return None

        delivery_rows = conn.execute(
            """
            SELECT d.*, s.url AS subscription_url
            FROM deliveries d
            JOIN subscriptions s ON s.id = d.subscription_id
            WHERE d.event_id = ?
            ORDER BY d.updated_at ASC, d.id ASC
            """,
            (event_id,),
        ).fetchall()

    event = _event_row_to_dict(event_row)
    deliveries = []
    for row in delivery_rows:
        delivery = _delivery_row_to_dict(row)
        delivery["attempts"] = delivery_repo.get_delivery_attempts(delivery["id"])
        deliveries.append(delivery)
    event["deliveries"] = deliveries
    return event
