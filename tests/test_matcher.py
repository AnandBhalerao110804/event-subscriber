import pytest

from app.matcher import matches_filter


@pytest.mark.parametrize(
    ("event_filter", "event_type", "expected"),
    [
        ("*", "order.created", True),
        ("*", "user.deleted", True),
        ("order.created", "order.created", True),
        ("order.created", "order.updated", False),
        ("order.*", "order.created", True),
        ("order.*", "order.updated", True),
        ("order.*", "user.created", False),
        ("user.*", "order.created", False),
    ],
)
def test_matches_filter(event_filter, event_type, expected):
    assert matches_filter(event_filter, event_type) is expected
