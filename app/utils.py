from datetime import UTC, datetime
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
