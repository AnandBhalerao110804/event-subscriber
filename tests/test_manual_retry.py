from app.repositories import deliveries as delivery_repo
from app.repositories import events as event_repo
from app.repositories import subscriptions as subscription_repo


def test_manual_retry_preserves_attempt_history(temp_db):
    subscription_repo.create_subscription(
        url="https://example.com/hook",
        event_filter="*",
    )
    event, _ = event_repo.create_event("order.created", {"id": 1})
    detail = event_repo.get_event_with_deliveries(event["id"])
    delivery_id = detail["deliveries"][0]["id"]

    delivery_repo.record_delivery_result(
        delivery_id=delivery_id,
        status_code=500,
        error=None,
        duration_ms=100,
        new_status="dead",
        new_attempt_count=3,
        next_attempt_at=None,
    )

    assert len(delivery_repo.get_delivery_attempts(delivery_id)) == 1

    assert delivery_repo.retry_delivery(delivery_id) is True
    delivery = delivery_repo.get_delivery(delivery_id)
    assert delivery["status"] == "pending"
    assert delivery["attempt_count"] == 0
    assert delivery["last_error"] is None
    assert len(delivery_repo.get_delivery_attempts(delivery_id)) == 1


def test_manual_retry_continues_attempt_numbering(temp_db):
    subscription_repo.create_subscription(
        url="https://example.com/hook",
        event_filter="*",
    )
    event, _ = event_repo.create_event("order.created", {"id": 1})
    delivery_id = event_repo.get_event_with_deliveries(event["id"])["deliveries"][0]["id"]

    for i in range(5):
        delivery_repo.record_delivery_result(
            delivery_id=delivery_id,
            status_code=500,
            error=None,
            duration_ms=100,
            new_status="dead" if i == 4 else "failed",
            new_attempt_count=i + 1,
            next_attempt_at="2099-01-01T00:00:00Z" if i < 4 else None,
        )

    attempts = delivery_repo.get_delivery_attempts(delivery_id)
    assert [a["attempt_number"] for a in attempts] == [1, 2, 3, 4, 5]

    assert delivery_repo.retry_delivery(delivery_id) is True

    delivery_repo.record_delivery_result(
        delivery_id=delivery_id,
        status_code=500,
        error=None,
        duration_ms=100,
        new_status="failed",
        new_attempt_count=1,
        next_attempt_at="2099-01-01T00:00:00Z",
    )

    attempts = delivery_repo.get_delivery_attempts(delivery_id)
    assert [a["attempt_number"] for a in attempts] == [1, 2, 3, 4, 5, 6]


def test_manual_retry_ignores_delivered(temp_db):
    subscription_repo.create_subscription(
        url="https://example.com/hook",
        event_filter="*",
    )
    event, _ = event_repo.create_event("order.created", {"id": 1})
    delivery_id = event_repo.get_event_with_deliveries(event["id"])["deliveries"][0]["id"]

    delivery_repo.record_delivery_result(
        delivery_id=delivery_id,
        status_code=200,
        error=None,
        duration_ms=50,
        new_status="delivered",
        new_attempt_count=1,
        next_attempt_at=None,
    )

    assert delivery_repo.retry_delivery(delivery_id) is False
