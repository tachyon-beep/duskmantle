from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from gateway.config.settings import get_settings
from gateway.observability import UI_REQUESTS_TOTAL

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/ui", tags=["ui"])


def get_static_path() -> Path:
    """Return the absolute path to UI static assets."""

    return STATIC_DIR


@router.get("/", response_class=HTMLResponse)
async def ui_index(request: Request) -> HTMLResponse:
    """Render the landing page for the embedded UI."""

    UI_REQUESTS_TOTAL.labels(view="landing").inc()
    return _templates.TemplateResponse(
        request,
        "index.html",
        {},
    )


@router.get("/search", response_class=HTMLResponse)
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
    return _templates.TemplateResponse(
        request,
        "search.html",
        context,
    )
