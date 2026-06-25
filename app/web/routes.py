from pathlib import Path
import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.repositories import deliveries as delivery_repo
from app.repositories import events as event_repo
from app.repositories import subscriptions as subscription_repo
from app.web.deps import check_dashboard_auth

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.filters["tojson"] = lambda value, indent=None: json.dumps(
    value, indent=indent, default=str
)

router = APIRouter(tags=["dashboard"])


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": None},
    )


@router.post("/login")
def login(request: Request, admin_key: str = Form(...)):
    if admin_key != settings.admin_api_key:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid admin key"},
            status_code=401,
        )
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="admin_key", value=admin_key, httponly=True, samesite="lax")
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("admin_key")
    return response


@router.get("/")
def dashboard_home(
    request: Request,
    auth_redirect: RedirectResponse | None = Depends(check_dashboard_auth),
):
    if auth_redirect:
        return auth_redirect
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "subscriptions": subscription_repo.list_subscriptions(include_inactive=True),
            "events": event_repo.list_events(limit=50),
        },
    )


@router.get("/events/{event_id}")
def event_detail(
    request: Request,
    event_id: str,
    auth_redirect: RedirectResponse | None = Depends(check_dashboard_auth),
):
    if auth_redirect:
        return auth_redirect
    event = event_repo.get_event_with_deliveries(event_id)
    if not event:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"message": "Event not found"},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "event_detail.html",
        {"event": event},
    )


@router.post("/deliveries/{delivery_id}/retry")
def retry_delivery_from_dashboard(
    delivery_id: str,
    auth_redirect: RedirectResponse | None = Depends(check_dashboard_auth),
):
    if auth_redirect:
        return auth_redirect
    delivery = delivery_repo.get_delivery(delivery_id)
    if not delivery:
        return RedirectResponse(url="/", status_code=303)
    if delivery["status"] in ("failed", "dead"):
        delivery_repo.retry_delivery(delivery_id)
    return RedirectResponse(url=f"/events/{delivery['event_id']}", status_code=303)
