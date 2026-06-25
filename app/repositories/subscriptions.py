from app.db import get_connection
from app.utils import new_id, utc_now_iso


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "url": row["url"],
        "secret": row["secret"],
        "event_filter": row["event_filter"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
    }


def create_subscription(url: str, event_filter: str, secret: str | None = None) -> dict:
    subscription_id = new_id()
    created_at = utc_now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO subscriptions (id, url, secret, event_filter, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (subscription_id, url, secret, event_filter, created_at),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE id = ?", (subscription_id,)
        ).fetchone()
    return _row_to_dict(row)


def list_subscriptions(include_inactive: bool = False) -> list[dict]:
    with get_connection() as conn:
        if include_inactive:
            rows = conn.execute(
                "SELECT * FROM subscriptions ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM subscriptions WHERE active = 1 ORDER BY created_at DESC"
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_subscription(subscription_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE id = ?", (subscription_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_subscription(subscription_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET active = 0 WHERE id = ? AND active = 1",
            (subscription_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_active_subscriptions() -> list[dict]:
    return list_subscriptions(include_inactive=False)
