import pytest

from app.repositories import events as event_repo
from app.repositories import subscriptions as subscription_repo


def test_ingest_creates_matching_deliveries(temp_db):
    subscription_repo.create_subscription(
        url="https://example.com/hooks/order",
        event_filter="order.*",
    )
    subscription_repo.create_subscription(
        url="https://example.com/hooks/user",
        event_filter="user.*",
    )
    subscription_repo.create_subscription(
        url="https://example.com/hooks/all",
        event_filter="*",
    )

    event, delivery_count = event_repo.create_event(
        "order.created",
        {"id": 123},
    )

    assert delivery_count == 2
    detail = event_repo.get_event_with_deliveries(event["id"])
    assert len(detail["deliveries"]) == 2
    assert all(delivery["status"] == "pending" for delivery in detail["deliveries"])


def test_ingest_with_no_matching_subscriptions(temp_db):
    subscription_repo.create_subscription(
        url="https://example.com/hooks/user",
        event_filter="user.*",
    )

    _, delivery_count = event_repo.create_event("order.created", {"id": 1})

    assert delivery_count == 0
