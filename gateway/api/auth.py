from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gateway.config.settings import get_settings

_security = HTTPBearer(auto_error=False)


def require_scope(scope: str):
    """Return a dependency enforcing the given scope."""

    async def dependency(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> None:
        settings = get_settings()
        if not settings.auth_enabled:
            return
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
        token = credentials.credentials
        expected = settings.maintainer_token if scope == "maintainer" else settings.reader_token
        if expected is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auth not configured for scope")
        if token != expected:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    return dependency


require_reader = require_scope("reader")
require_maintainer = require_scope("maintainer")
