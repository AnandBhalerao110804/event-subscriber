import pytest

from app.delivery_summary import summarize_delivery_statuses


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([], "no_deliveries"),
        (["delivered"], "delivered"),
        (["delivered", "delivered"], "delivered"),
        (["dead"], "dead"),
        (["dead", "dead"], "dead"),
        (["pending"], "pending"),
        (["pending", "pending"], "pending"),
        (["failed"], "in_progress"),
        (["delivering"], "in_progress"),
        (["delivered", "pending"], "in_progress"),
        (["delivered", "failed"], "in_progress"),
        (["delivered", "dead"], "partial"),
        (["delivered", "dead", "dead"], "partial"),
    ],
)
def test_summarize_delivery_statuses(statuses, expected):
    assert summarize_delivery_statuses(statuses) == expected
