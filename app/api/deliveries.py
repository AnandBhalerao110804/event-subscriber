from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin
from app.repositories import deliveries as delivery_repo

router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])


@router.post("/{delivery_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_delivery(
    delivery_id: str,
    _: None = Depends(require_admin),
):
    delivery = delivery_repo.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    if delivery["status"] not in ("failed", "dead"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot retry delivery with status '{delivery['status']}'",
        )
    delivery_repo.retry_delivery(delivery_id)
    return {"delivery_id": delivery_id, "status": "pending"}
