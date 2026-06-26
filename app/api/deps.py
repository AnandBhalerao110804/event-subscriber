from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

security = HTTPBearer()


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
    if credentials.credentials != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )
