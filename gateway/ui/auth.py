"""Authentication helpers for the embedded UI."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gateway.api.auth import require_reader
from gateway.config.settings import get_settings

UI_SESSION_KEY = "ui_authenticated"
_ui_bearer = HTTPBearer(auto_error=False)


def require_ui_access(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_ui_bearer),
) -> None:
    """Guard UI routes based on either UI login or API tokens."""

    settings = get_settings()
    if settings.ui_login_enabled:
        if request.session.get(UI_SESSION_KEY):
            request.state.ui_authenticated = True
            return
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="UI login required",
            headers={"Location": "/ui/login"},
        )

    # Fallback to token-based auth when UI login is disabled.
    require_reader(credentials)


def mark_ui_session(request: Request) -> None:
    """Record the authenticated state for templates."""

    if "session" in request.scope:
        request.state.ui_authenticated = bool(request.session.get(UI_SESSION_KEY))
    else:
        request.state.ui_authenticated = False


__all__ = [
    "UI_SESSION_KEY",
    "require_ui_access",
    "mark_ui_session",
]
