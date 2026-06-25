from fastapi import Header, HTTPException, status

from app.config import settings


def require_admin(authorization: str = Header(...)) -> None:
    expected = f"Bearer {settings.admin_api_key}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )
