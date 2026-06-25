import asyncio
import logging
from contextlib import suppress

import httpx

from app.config import settings
from app.repositories import deliveries as delivery_repo
from app.worker.http_client import deliver_webhook
from app.worker.retry import resolve_delivery_status

logger = logging.getLogger(__name__)


async def process_delivery(client: httpx.AsyncClient, delivery: dict) -> None:
    if not delivery_repo.claim_delivery(delivery["id"]):
        return

    status_code, error, duration_ms = await deliver_webhook(client, delivery)
    new_status, new_attempt_count, next_attempt_at = resolve_delivery_status(
        delivery["attempt_count"],
        status_code,
        error,
    )
    delivery_repo.record_delivery_result(
        delivery_id=delivery["id"],
        status_code=status_code,
        error=error,
        duration_ms=duration_ms,
        new_status=new_status,
        new_attempt_count=new_attempt_count,
        next_attempt_at=next_attempt_at,
    )


async def run_delivery_worker() -> None:
    async with httpx.AsyncClient() as client:
        while True:
            try:
                recovered = delivery_repo.recover_stale_deliveries()
                if recovered:
                    logger.info("Recovered %s stale deliveries", recovered)

                due_deliveries = delivery_repo.fetch_due_deliveries()
                for delivery in due_deliveries:
                    await process_delivery(client, delivery)
            except Exception:
                logger.exception("Delivery worker iteration failed")

            await asyncio.sleep(settings.worker_poll_interval_sec)
