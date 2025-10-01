from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gateway.config.settings import AppSettings, get_settings

_security = HTTPBearer(auto_error=False)


def require_scope(scope: str) -> Callable[[HTTPAuthorizationCredentials | None], None]:
    """Return a dependency enforcing the given scope."""

    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(_security),  # noqa: B008
    ) -> None:
        settings = get_settings()
        if not settings.auth_enabled:
            return
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

        token = credentials.credentials
        allowed_tokens = _allowed_tokens_for_scope(settings, scope)

        if not allowed_tokens:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auth not configured for scope")

        if token not in allowed_tokens:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    return dependency


require_reader = require_scope("reader")
require_maintainer = require_scope("maintainer")


def _allowed_tokens_for_scope(settings: AppSettings, scope: str) -> list[str]:
    maintainer_token = settings.maintainer_token or ""
    reader_token = settings.reader_token or ""

    if scope == "maintainer":
        return [maintainer_token] if maintainer_token else []

    tokens: list[str] = []
    if reader_token:
        tokens.append(reader_token)
    if maintainer_token:
        tokens.append(maintainer_token)
    return tokens
