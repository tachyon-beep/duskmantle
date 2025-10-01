"""HTTP client for interacting with the gateway API."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from types import TracebackType
from typing import Any
from urllib.parse import quote as _quote

import httpx

from .config import MCPSettings
from .exceptions import GatewayRequestError, MissingTokenError

logger = logging.getLogger(__name__)


class GatewayClient:
    """Thin async wrapper over the gateway REST API."""

    def __init__(self, settings: MCPSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> GatewayClient:
        if self._client is not None:
            raise RuntimeError("GatewayClient already started")
        timeout = httpx.Timeout(self._settings.request_timeout_seconds)
        self._client = httpx.AsyncClient(
            base_url=str(self._settings.gateway_url),
            timeout=timeout,
            verify=self._settings.verify_ssl,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # noqa: D401 - required signature
        if self._client is not None:
            await self._client.aclose()
        self._client = None

    @property
    def settings(self) -> MCPSettings:
        return self._settings

    async def search(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request(
            "POST",
            "/search",
            json_payload=payload,
            require_reader=True,
        )
        return _expect_dict(data, "search")

    async def graph_node(self, node_id: str, *, relationships: str, limit: int) -> dict[str, Any]:
        data = await self._request(
            "GET",
            f"/graph/nodes/{_quote_segment(node_id)}",
            params={"relationships": relationships, "limit": limit},
            require_reader=True,
        )
        return _expect_dict(data, "graph-node")

    async def graph_subsystem(
        self,
        name: str,
        *,
        depth: int,
        include_artifacts: bool,
        cursor: str | None,
        limit: int,
    ) -> dict[str, Any]:
        params: dict[str, _ParamValue] = {
            "depth": depth,
            "include_artifacts": include_artifacts,
            "limit": limit,
        }
        if cursor is not None:
            params["cursor"] = cursor
        data = await self._request(
            "GET",
            f"/graph/subsystems/{_quote_segment(name)}",
            params=params,
            require_reader=True,
        )
        return _expect_dict(data, "graph-subsystem")

    async def graph_search(self, term: str, *, limit: int) -> dict[str, Any]:
        data = await self._request(
            "GET",
            "/graph/search",
            params={"q": term, "limit": limit},
            require_reader=True,
        )
        return _expect_dict(data, "graph-search")

    async def coverage_summary(self) -> dict[str, Any]:
        data = await self._request(
            "GET",
            "/coverage",
            require_admin=True,
        )
        return _expect_dict(data, "coverage")

    async def lifecycle_report(self) -> dict[str, Any]:
        data = await self._request(
            "GET",
            "/lifecycle",
            require_admin=True,
        )
        return _expect_dict(data, "lifecycle")

    async def audit_history(self, *, limit: int = 10) -> list[dict[str, Any]]:
        data = await self._request(
            "GET",
            "/audit/history",
            params={"limit": limit},
            require_admin=True,
        )
        if not isinstance(data, list):
            raise GatewayRequestError(status_code=500, detail="Unexpected audit payload", payload=data)
        return data

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_payload: Mapping[str, object] | list[object] | None = None,
        params: Mapping[str, _ParamValue] | None = None,
        require_admin: bool = False,
        require_reader: bool = False,
    ) -> object:
        if self._client is None:
            raise RuntimeError("GatewayClient is not running")

        headers: dict[str, str] = {}
        token: str | None = None
        if require_admin:
            token = self._settings.admin_token
            if token is None:
                raise MissingTokenError("Maintainer")
        elif require_reader:
            token = self._settings.reader_token or self._settings.admin_token
            if token is None:
                logger.debug("No reader token configured; issuing unauthenticated request")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        if self._settings.log_requests:
            logger.debug("MCP -> Gateway %s %s", method, path)

        request_params = dict(params) if params is not None else None

        response = await self._client.request(
            method,
            path,
            json=json_payload,
            params=request_params,
            headers=headers or None,
        )

        if response.status_code >= 400:
            detail = _extract_error_detail(response)
            raise GatewayRequestError(
                status_code=response.status_code,
                detail=detail,
                payload=_safe_json(response),
            )

        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return response.text or "Unknown error"
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
    return response.text or "Unknown error"


def _safe_json(response: httpx.Response) -> Mapping[str, object] | list[object] | None:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return payload
    return None


def _quote_segment(value: str) -> str:
    return _quote(value, safe="")


_ParamValue = str | int | float | bool | None


def _expect_dict(data: object, operation: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise GatewayRequestError(status_code=500, detail=f"Unexpected response for {operation}", payload=data)
    return data


__all__ = ["GatewayClient"]
