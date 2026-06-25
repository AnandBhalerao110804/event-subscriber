from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SubscriptionCreate(BaseModel):
    url: HttpUrl
    secret: str | None = None
    event_filter: str = Field(..., min_length=1, examples=["order.*", "*"])


class SubscriptionResponse(BaseModel):
    id: str
    url: str
    secret: str | None
    event_filter: str
    active: bool
    created_at: str


class EventCreate(BaseModel):
    type: str = Field(..., min_length=1, examples=["order.created"])
    payload: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: str
    type: str
    payload: dict[str, Any]
    created_at: str


class EventIngestResponse(BaseModel):
    event_id: str
    delivery_count: int


class DeliveryAttemptSummary(BaseModel):
    id: str
    delivery_id: str
    attempt_number: int
    status_code: int | None
    error: str | None
    duration_ms: int | None
    created_at: str


class DeliverySummary(BaseModel):
    id: str
    subscription_id: str
    subscription_url: str
    status: str
    attempt_count: int
    next_attempt_at: str
    last_status_code: int | None
    last_error: str | None
    updated_at: str
    attempts: list[DeliveryAttemptSummary] = []


class EventDetailResponse(EventResponse):
    deliveries: list[DeliverySummary]
