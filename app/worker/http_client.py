import json
import time

import httpx

from app.config import settings
from app.signing import sign_payload


def build_webhook_body(event_id: str, event_type: str, payload: dict) -> bytes:
    body_dict = {"id": event_id, "type": event_type, "payload": payload}
    return json.dumps(body_dict, separators=(",", ":")).encode()


async def deliver_webhook(
    client: httpx.AsyncClient,
    delivery: dict,
) -> tuple[int | None, str | None, int]:
    body = build_webhook_body(
        delivery["event_id"],
        delivery["event_type"],
        delivery["event_payload"],
    )
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event-Id": delivery["event_id"],
        "X-Webhook-Event-Type": delivery["event_type"],
        "X-Webhook-Delivery-Id": delivery["id"],
    }
    if delivery["subscription_secret"]:
        headers["X-Webhook-Signature"] = sign_payload(delivery["subscription_secret"], body)

    start = time.perf_counter()
    status_code = None
    error = None
    try:
        response = await client.post(
            delivery["subscription_url"],
            content=body,
            headers=headers,
            timeout=settings.delivery_timeout_sec,
        )
        status_code = response.status_code
    except httpx.HTTPError as exc:
        error = str(exc)

    duration_ms = int((time.perf_counter() - start) * 1000)
    return status_code, error, duration_ms
