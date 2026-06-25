from contextlib import asynccontextmanager, suppress
import asyncio
import logging

from fastapi import FastAPI

from app.api.deliveries import router as deliveries_router
from app.api.events import router as events_router
from app.api.subscriptions import router as subscriptions_router
from app.db import init_db
from app.web.routes import router as dashboard_router
from app.worker.delivery_worker import run_delivery_worker

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    worker_task = asyncio.create_task(run_delivery_worker())
    yield
    worker_task.cancel()
    with suppress(asyncio.CancelledError):
        await worker_task


app = FastAPI(
    title="Webhook Delivery Service",
    description="Reliable webhook delivery with retries and persistence.",
    lifespan=lifespan,
)

app.include_router(subscriptions_router)
app.include_router(events_router)
app.include_router(deliveries_router)
app.include_router(dashboard_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
