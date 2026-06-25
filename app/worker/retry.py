from datetime import UTC, datetime, timedelta

from app.config import settings


def should_retry(status_code: int | None, error: str | None) -> bool:
    if error is not None:
        return True
    if status_code is None:
        return True
    if 200 <= status_code < 300:
        return False
    if status_code in (408, 429):
        return True
    if 400 <= status_code < 500:
        return False
    if 500 <= status_code < 600:
        return True
    return True


def next_retry_delay(attempt_count: int) -> float:
    delay = settings.retry_base_delay_sec * (2**attempt_count)
    return min(delay, settings.retry_max_delay_sec)


def future_iso(delay_sec: float) -> str:
    future = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=delay_sec)
    return future.isoformat().replace("+00:00", "Z")


def resolve_delivery_status(
    current_attempt_count: int,
    status_code: int | None,
    error: str | None,
) -> tuple[str, int, str | None]:
    new_attempt_count = current_attempt_count + 1

    if status_code is not None and 200 <= status_code < 300:
        return "delivered", new_attempt_count, None

    if not should_retry(status_code, error):
        return "dead", new_attempt_count, None

    if new_attempt_count >= settings.max_delivery_attempts:
        return "dead", new_attempt_count, None

    delay = next_retry_delay(current_attempt_count)
    return "failed", new_attempt_count, future_iso(delay)
