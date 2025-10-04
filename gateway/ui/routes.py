"""UI router exposing static assets and HTML entry points."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from gateway.api.auth import require_maintainer
from gateway.config.settings import get_settings
from gateway.observability import UI_EVENTS_TOTAL, UI_REQUESTS_TOTAL
from gateway.ui.auth import UI_SESSION_KEY, mark_ui_session, require_ui_access

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/ui", tags=["ui"])

logger = logging.getLogger(__name__)


def get_static_path() -> Path:
    """Return the absolute path to UI static assets."""

    return STATIC_DIR


@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_ui_access)],
)
async def ui_index(request: Request) -> HTMLResponse:
    """Render the landing page for the embedded UI."""

    UI_REQUESTS_TOTAL.labels(view="landing").inc()
    mark_ui_session(request)
    return _templates.TemplateResponse(
        request,
        "index.html",
        {},
    )


@router.get(
    "/search",
    response_class=HTMLResponse,
    dependencies=[Depends(require_ui_access)],
)
async def ui_search(request: Request) -> HTMLResponse:
    """Render the search console view."""

    UI_REQUESTS_TOTAL.labels(view="search").inc()
    settings = get_settings()
    profile_name, resolved = settings.resolved_search_weights()
    context = {
        "weight_profile": profile_name,
        "weights": {
            "vector_weight": settings.search_vector_weight,
            "lexical_weight": settings.search_lexical_weight,
            "subsystem": resolved["weight_subsystem"],
            "relationship": resolved["weight_relationship"],
            "support": resolved["weight_support"],
            "coverage_penalty": resolved["weight_coverage_penalty"],
            "criticality": resolved["weight_criticality"],
        },
    }
    mark_ui_session(request)
    return _templates.TemplateResponse(
        request,
        "search.html",
        context,
    )


@router.get(
    "/subsystems",
    response_class=HTMLResponse,
    dependencies=[Depends(require_ui_access)],
)
async def ui_subsystems(request: Request) -> HTMLResponse:
    """Render the subsystem explorer view."""

    UI_REQUESTS_TOTAL.labels(view="subsystems").inc()
    context = {
        "default_depth": 2,
        "default_limit": 15,
    }
    mark_ui_session(request)
    return _templates.TemplateResponse(
        request,
        "subsystems.html",
        context,
    )


@router.get(
    "/lifecycle",
    response_class=HTMLResponse,
    dependencies=[Depends(require_ui_access)],
)
async def ui_lifecycle(request: Request) -> HTMLResponse:
    """Render the lifecycle dashboard view."""

    UI_REQUESTS_TOTAL.labels(view="lifecycle").inc()
    settings = get_settings()
    context = {
        "report_enabled": settings.lifecycle_report_enabled,
    }
    mark_ui_session(request)
    return _templates.TemplateResponse(
        request,
        "lifecycle.html",
        context,
    )


@router.get(
    "/lifecycle/report",
    dependencies=[Depends(require_ui_access)],
)
async def ui_lifecycle_report(request: Request) -> JSONResponse:
    """Serve the lifecycle report JSON while recording UI metrics."""

    del request
    UI_EVENTS_TOTAL.labels(event="lifecycle_download").inc()
    settings = get_settings()
    if not settings.lifecycle_report_enabled:
        return JSONResponse(status_code=404, content={"detail": "Lifecycle report disabled"})
    report_path = settings.state_path / "reports" / "lifecycle_report.json"
    if not report_path.exists():
        return JSONResponse(status_code=404, content={"detail": "Lifecycle report not found"})
    try:
        raw = report_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except OSError as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    except json.JSONDecodeError as exc:
        return JSONResponse(status_code=500, content={"detail": f"Lifecycle report invalid JSON: {exc}"})
    return JSONResponse(content=payload)


@router.post(
    "/events",
    dependencies=[Depends(require_maintainer)],
)
async def ui_event(request: Request, payload: dict[str, object]) -> JSONResponse:
    """Record a UI event for observability purposes."""

    event_name = str(payload.get("event") or "").strip().lower()
    if not event_name:
        raise HTTPException(status_code=422, detail="Field 'event' is required")
    UI_EVENTS_TOTAL.labels(event=event_name).inc()
    logger.info("UI event", extra={"ui_event": event_name, "remote": request.client.host if request.client else None})
    return JSONResponse({"status": "ok"})


@router.get("/login", response_class=HTMLResponse)
async def ui_login_form(request: Request) -> HTMLResponse:
    """Render the login form when UI passwords are enabled."""

    settings = get_settings()
    if not settings.ui_login_enabled:
        raise HTTPException(status_code=404, detail="UI login is disabled")
    if "session" in request.scope and request.session.get(UI_SESSION_KEY):
        return RedirectResponse(url="/ui/", status_code=303)

    next_requested = request.query_params.get("next", "/ui/")
    next_url = next_requested if isinstance(next_requested, str) and next_requested.startswith("/") else "/ui/"
    context = {
        "next": next_url,
        "username": settings.ui_username,
        "error": request.query_params.get("error"),
    }
    return _templates.TemplateResponse(request, "login.html", context)


@router.post("/login")
async def ui_login_submit(
    request: Request,
    password: str = Form(...),
    next: str = Form("/ui/"),  # noqa: A003 - shadow builtins intentionally for form handling
) -> RedirectResponse:
    """Handle login submissions and set the session cookie."""

    settings = get_settings()
    if not settings.ui_login_enabled:
        raise HTTPException(status_code=404, detail="UI login is disabled")

    target = next if next.startswith("/") else "/ui/"
    if password != settings.ui_password:
        params = f"?next={target}&error=invalid"
        return RedirectResponse(url=f"/ui/login{params}", status_code=303)

    if "session" not in request.scope:
        raise HTTPException(status_code=500, detail="Session support unavailable")

    request.session[UI_SESSION_KEY] = True
    mark_ui_session(request)
    return RedirectResponse(url=target, status_code=303)


@router.post("/logout")
async def ui_logout(request: Request) -> RedirectResponse:
    """Clear the UI login session."""

    if "session" in request.scope:
        request.session.pop(UI_SESSION_KEY, None)
    mark_ui_session(request)
    return RedirectResponse(url="/ui/login", status_code=303)
