from app.repositories import deliveries as delivery_repo
from app.repositories import events as event_repo
from app.repositories import subscriptions as subscription_repo


def test_attempt_numbers_are_monotonic(temp_db):
    subscription_repo.create_subscription(
        url="https://example.com/hook",
        event_filter="*",
    )
    event, _ = event_repo.create_event("order.created", {"id": 1})
    delivery_id = event_repo.get_event_with_deliveries(event["id"])["deliveries"][0]["id"]

    for i in range(3):
        delivery_repo.record_delivery_result(
            delivery_id=delivery_id,
            status_code=500,
            error=None,
            duration_ms=10,
            new_status="failed",
            new_attempt_count=i + 1,
            next_attempt_at="2099-01-01T00:00:00Z",
        )

    attempts = delivery_repo.get_delivery_attempts(delivery_id)
    assert [a["attempt_number"] for a in attempts] == [1, 2, 3]
