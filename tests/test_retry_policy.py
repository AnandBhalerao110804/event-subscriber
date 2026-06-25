import pytest

from app.worker.retry import (
    next_retry_delay,
    resolve_delivery_status,
    should_retry,
)


@pytest.mark.parametrize(
    ("status_code", "error", "expected"),
    [
        (200, None, False),
        (201, None, False),
        (404, None, False),
        (400, None, False),
        (408, None, True),
        (429, None, True),
        (500, None, True),
        (502, None, True),
        (None, "connection failed", True),
    ],
)
def test_should_retry(status_code, error, expected):
    assert should_retry(status_code, error) is expected


def test_next_retry_delay_exponential_with_cap(monkeypatch):
    monkeypatch.setattr("app.worker.retry.settings.retry_base_delay_sec", 1.0)
    monkeypatch.setattr("app.worker.retry.settings.retry_max_delay_sec", 10.0)

    assert next_retry_delay(0) == 1.0
    assert next_retry_delay(1) == 2.0
    assert next_retry_delay(2) == 4.0
    assert next_retry_delay(3) == 8.0
    assert next_retry_delay(4) == 10.0


def test_resolve_delivery_status_success():
    status, attempts, next_at = resolve_delivery_status(0, 200, None)
    assert status == "delivered"
    assert attempts == 1
    assert next_at is None


def test_resolve_delivery_status_client_error_is_dead():
    status, attempts, next_at = resolve_delivery_status(0, 404, None)
    assert status == "dead"
    assert attempts == 1
    assert next_at is None


def test_resolve_delivery_status_server_error_retries(monkeypatch):
    monkeypatch.setattr("app.worker.retry.settings.max_delivery_attempts", 5)
    status, attempts, next_at = resolve_delivery_status(0, 500, None)
    assert status == "failed"
    assert attempts == 1
    assert next_at is not None


def test_resolve_delivery_status_max_attempts_reached(monkeypatch):
    monkeypatch.setattr("app.worker.retry.settings.max_delivery_attempts", 3)
    status, attempts, next_at = resolve_delivery_status(2, 500, None)
    assert status == "dead"
    assert attempts == 3
    assert next_at is None
