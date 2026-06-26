from pathlib import Path
import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import settings
from app.models import SubscriptionCreate
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

DEFAULT_FORM_VALUES = {"url": "", "event_filter": "*", "secret": ""}


def _dashboard_context(
    form_error: str | None = None,
    form_values: dict | None = None,
) -> dict:
    return {
        "subscriptions": subscription_repo.list_subscriptions(include_inactive=True),
        "events": event_repo.list_events_with_summary(limit=50),
        "form_error": form_error,
        "form_values": form_values or DEFAULT_FORM_VALUES,
    }


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
        _dashboard_context(),
    )


@router.post("/subscriptions")
def create_subscription_from_dashboard(
    request: Request,
    url: str = Form(...),
    event_filter: str = Form(...),
    secret: str = Form(""),
    auth_redirect: RedirectResponse | None = Depends(check_dashboard_auth),
):
    if auth_redirect:
        return auth_redirect

    form_values = {"url": url, "event_filter": event_filter, "secret": secret}
    try:
        body = SubscriptionCreate(
            url=url,
            event_filter=event_filter,
            secret=secret or None,
        )
    except ValidationError:
        return templates.TemplateResponse(
            request,
            "index.html",
            _dashboard_context(
                form_error="Invalid URL or event filter. URL must be http(s); filter cannot be empty.",
                form_values=form_values,
            ),
            status_code=400,
        )

    subscription_repo.create_subscription(
        url=str(body.url),
        event_filter=body.event_filter,
        secret=body.secret,
    )
    return RedirectResponse(url="/", status_code=303)


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
