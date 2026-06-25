from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import require_admin
from app.models import EventCreate, EventDetailResponse, EventIngestResponse, EventResponse
from app.repositories import events as event_repo

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_event(
    body: EventCreate,
    _: None = Depends(require_admin),
):
    event, delivery_count = event_repo.create_event(body.type, body.payload)
    return EventIngestResponse(event_id=event["id"], delivery_count=delivery_count)


@router.get("", response_model=list[EventResponse])
def list_events(
    limit: int = Query(default=50, ge=1, le=200),
    _: None = Depends(require_admin),
):
    return event_repo.list_events(limit=limit)


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(
    event_id: str,
    _: None = Depends(require_admin),
):
    event = event_repo.get_event_with_deliveries(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
