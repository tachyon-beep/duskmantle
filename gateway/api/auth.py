from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gateway.config.settings import get_settings

_security = HTTPBearer(auto_error=False)


def require_scope(scope: str) -> Callable[[HTTPAuthorizationCredentials | None], Awaitable[None]]:
    """Return a dependency enforcing the given scope."""

    async def dependency(
        credentials: HTTPAuthorizationCredentials = Depends(_security),  # noqa: B008
    ) -> None:
        settings = get_settings()
        if not settings.auth_enabled:
            return
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

        token = credentials.credentials
        allowed_tokens: list[str] = []

        maintainer_token = settings.maintainer_token or ""
        reader_token = settings.reader_token or ""

        if scope == "maintainer":
            if maintainer_token:
                allowed_tokens.append(maintainer_token)
        else:  # reader scope accepts maintainer as superset
            if reader_token:
                allowed_tokens.append(reader_token)
            if maintainer_token:
                allowed_tokens.append(maintainer_token)

        if not allowed_tokens:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auth not configured for scope")

        if token not in allowed_tokens:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    return dependency


require_reader = require_scope("reader")
require_maintainer = require_scope("maintainer")
