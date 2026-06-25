from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin
from app.models import SubscriptionCreate, SubscriptionResponse
from app.repositories import subscriptions as subscription_repo

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    body: SubscriptionCreate,
    _: None = Depends(require_admin),
):
    return subscription_repo.create_subscription(
        url=str(body.url),
        event_filter=body.event_filter,
        secret=body.secret,
    )


@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    include_inactive: bool = False,
    _: None = Depends(require_admin),
):
    return subscription_repo.list_subscriptions(include_inactive=include_inactive)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: str,
    _: None = Depends(require_admin),
):
    subscription = subscription_repo.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: str,
    _: None = Depends(require_admin),
):
    deleted = subscription_repo.delete_subscription(subscription_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
