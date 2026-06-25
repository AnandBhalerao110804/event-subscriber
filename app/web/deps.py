from fastapi import Cookie
from fastapi.responses import RedirectResponse

from app.config import settings


def check_dashboard_auth(admin_key: str | None = Cookie(default=None)) -> RedirectResponse | None:
    if admin_key != settings.admin_api_key:
        return RedirectResponse(url="/login", status_code=303)
    return None
