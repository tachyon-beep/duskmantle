"""FastMCP server exposing the knowledge gateway."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from textwrap import dedent
from time import perf_counter
from typing import Any

from fastmcp import Context, FastMCP

from gateway import get_version
from gateway.observability.metrics import MCP_FAILURES_TOTAL, MCP_REQUEST_SECONDS, MCP_REQUESTS_TOTAL, MCP_STORETEXT_TOTAL, MCP_UPLOAD_TOTAL

from .backup import trigger_backup
from .client import GatewayClient
from .config import MCPSettings
from .exceptions import GatewayRequestError
from .feedback import record_feedback
from .ingest import latest_ingest_status, trigger_ingest
from .storetext import handle_storetext
from .upload import handle_upload

TOOL_USAGE = {
    "km-search": {
        "description": "Hybrid search across the knowledge base with optional filters and graph context",
        "details": dedent(
            """
            Required: `query` text. Optional: `limit` (default 10, max 25), `include_graph`, structured `filters`, `sort_by_vector`.
            Example: `/sys mcp run duskmantle km-search --query "ingest pipeline" --limit 5`.
            Returns scored chunks with metadata and optional graph enrichments.
            """
        ).strip(),
    },
    "km-graph-node": {
        "description": "Fetch a graph node by ID and inspect incoming/outgoing relationships",
        "details": dedent(
            """
            Required: `node_id` such as `DesignDoc:docs/archive/WP6/WP6_RELEASE_TOOLING_PLAN.md`.
            Optional: `relationships` (`outgoing`, `incoming`, `all`, `none`) and `limit` (default 50, max 200).
            Example: `/sys mcp run duskmantle km-graph-node --node-id "Code:gateway/mcp/server.py"`.
            """
        ).strip(),
    },
    "km-graph-subsystem": {
        "description": "Review a subsystem, related artifacts, and connected subsystems",
        "details": dedent(
            """
            Required: `name` of the subsystem.
            Optional: `depth` (default 1, max 5), `include_artifacts`, pagination `cursor`, `limit` (default 25, max 100).
            Example: `/sys mcp run duskmantle km-graph-subsystem --name Kasmina --depth 2`.
            """
        ).strip(),
    },
    "km-graph-search": {
        "description": "Search graph entities (artifacts, subsystems, teams) by term",
        "details": dedent(
            """
            Required: `term` to match against graph nodes.
            Optional: `limit` (default 20, max 50).
            Example: `/sys mcp run duskmantle km-graph-search --term coverage`.
            """
        ).strip(),
    },
    "km-coverage-summary": {
        "description": "Summarise ingestion coverage (artifact and chunk counts, freshness)",
        "details": dedent(
            """
            No parameters. Returns the same payload as `/coverage` including summary counts and stale thresholds.
            Example: `/sys mcp run duskmantle km-coverage-summary`.
            """
        ).strip(),
    },
    "km-lifecycle-report": {
        "description": "Summarise isolated nodes, stale docs, and missing tests",
        "details": dedent(
            """
            No parameters. Mirrors the `/lifecycle` endpoint and highlights isolated graph nodes, stale design docs, and subsystems missing tests.
            Example: `/sys mcp run duskmantle km-lifecycle-report`.
            """
        ).strip(),
    },
    "km-ingest-status": {
        "description": "Show the most recent ingest run (profile, status, timestamps)",
        "details": dedent(
            """
            Optional: `profile` to scope results to a specific ingest profile.
            Example: `/sys mcp run duskmantle km-ingest-status --profile demo`.
            Returns `status: ok` with run metadata or `status: not_found` when history is empty.
            """
        ).strip(),
    },
    "km-ingest-trigger": {
        "description": "Kick off a manual ingest run (full rebuild via gateway-ingest)",
        "details": dedent(
            """
            Optional: `profile` (defaults to MCP settings), `dry_run`, `use_dummy_embeddings`.
            Example: `/sys mcp run duskmantle km-ingest-trigger --profile local --dry-run true`.
            Requires maintainer token (`KM_ADMIN_TOKEN`).
            """
        ).strip(),
    },
    "km-backup-trigger": {
        "description": "Create a compressed backup of gateway state (Neo4j/Qdrant data)",
        "details": dedent(
            """
            No parameters. Returns archive path and metadata.
            Example: `/sys mcp run duskmantle km-backup-trigger`.
            Requires maintainer token; mirrors the `bin/km-backup` helper.
            """
        ).strip(),
    },
    "km-feedback-submit": {
        "description": "Vote on a search result and attach optional notes for training data",
        "details": dedent(
            """
            Required: `request_id` (search request) and `chunk_id` (result identifier).
            Optional: numeric `vote` (-1.0 to 1.0) and freeform `note`.
            Example: `/sys mcp run duskmantle km-feedback-submit --request-id req123 --chunk-id chunk456 --vote 1`.
            Maintainer token required when auth is enforced.
            """
        ).strip(),
    },
    "km-upload": {
        "description": "Copy an existing file into the knowledge workspace and optionally trigger ingest",
        "details": dedent(
            """
            Required: `source_path` (file visible to the MCP host). Optional: `destination` (relative path inside the
            content root), `overwrite`, `ingest`. Default behaviour stores the file under the configured docs directory.
            Example: `/sys mcp run duskmantle km-upload --source-path ./notes/design.md --destination docs/uploads/`.
            Maintainer scope recommended because this writes to the repository volume and may trigger ingestion.
            """
        ).strip(),
    },
    "km-storetext": {
        "description": "Persist raw text as a document within the knowledge workspace",
        "details": dedent(
            """
            Required: `content` (text body). Optional: `title`, `destination`, `subsystem`, `tags`, `metadata` map,
            `overwrite`, `ingest`. Defaults write markdown into the configured docs directory with YAML front matter
            derived from the provided metadata.
            Example: `/sys mcp run duskmantle km-storetext --title "Release Notes" --content "## Summary"`.
            Maintainer scope recommended because this writes to the repository volume.
            """
        ).strip(),
    },
}

HELP_DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "MCP_INTERFACE_SPEC.md"


class MCPServerState:
    """Holds shared state for the MCP server lifespan."""

    def __init__(self, settings: MCPSettings) -> None:
        self.settings = settings
        self.client: GatewayClient | None = None

    def require_client(self) -> GatewayClient:
        if self.client is None:
            raise RuntimeError("Gateway client is not initialised")
        return self.client

    def lifespan(self) -> AsyncIterator[MCPServerState]:
        @asynccontextmanager
        async def _lifespan(_server: FastMCP) -> AsyncIterator[MCPServerState]:
            async with GatewayClient(self.settings) as client:
                self.client = client
                try:
                    yield self
                finally:
                    self.client = None

        return _lifespan


def build_server(settings: MCPSettings | None = None) -> FastMCP:
    """Create a FastMCP server wired to the gateway API."""

    settings = settings or MCPSettings()
    state = MCPServerState(settings)
    instructions = (
        "Use these tools to interact with the Duskmantle knowledge gateway: perform hybrid search, "
        "inspect graph relationships, review coverage, trigger ingestion, capture feedback, and "
        "produce state backups. Reader operations require KM_READER_TOKEN; maintainer operations "
        "require KM_ADMIN_TOKEN. Call 'km-help' for detailed usage guidance."
    )
    server = FastMCP(
        name="duskmantle-km",
        version=get_version(),
        instructions=instructions,
        lifespan=state.lifespan(),
    )
    server._duskmantle_state = state
    _initialise_metric_labels()

    @server.tool(name="km-help", description="Return usage notes for Duskmantle MCP tools")
    async def km_help(
        tool: str | None = None,
        include_spec: bool = False,
        context: Context | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        try:
            usage_payload = _resolve_usage(tool)
            if include_spec:
                usage_payload["spec"] = _load_help_document()
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-help", exc, start)
            raise
        _record_success("km-help", start)
        await _report_info(context, "Returned MCP usage help")
        return usage_payload

    @server.tool(name="km-search", description=TOOL_USAGE["km-search"]["description"])
    async def km_search(
        query: str,
        limit: int = 10,
        include_graph: bool = True,
        filters: dict[str, Any] | None = None,
        sort_by_vector: bool | None = None,
        context: Context | None = None,
    ) -> dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        limit = _clamp(limit, minimum=1, maximum=25)

        payload: dict[str, Any] = {
            "query": query.strip(),
            "limit": limit,
            "include_graph": include_graph,
        }
        if filters:
            payload["filters"] = _normalise_filters(filters)
        if sort_by_vector is not None:
            payload["sort_by_vector"] = bool(sort_by_vector)

        start = perf_counter()
        try:
            response = await state.require_client().search(payload)
        except GatewayRequestError as exc:  # pragma: no cover - network errors exercised in integration tests
            await _report_error(context, f"Search failed: {exc.detail}")
            _record_failure("km-search", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-search", exc, start)
            raise
        _record_success("km-search", start)
        await _report_info(context, f"Search returned {len(response.get('results', []))} result(s)")
        return response

    @server.tool(name="km-graph-node", description=TOOL_USAGE["km-graph-node"]["description"])
    async def km_graph_node(
        node_id: str,
        relationships: str = "outgoing",
        limit: int = 50,
        context: Context | None = None,
    ) -> dict[str, Any]:
        if not node_id or not node_id.strip():
            raise ValueError("node_id must be a non-empty string")
        relationships_normalised = relationships.lower()
        if relationships_normalised not in {"outgoing", "incoming", "all", "none"}:
            raise ValueError("relationships must be one of outgoing, incoming, all, none")
        limit = _clamp(limit, minimum=1, maximum=200)
        start = perf_counter()
        try:
            result = await state.require_client().graph_node(
                node_id.strip(),
                relationships=relationships_normalised,
                limit=limit,
            )
        except GatewayRequestError as exc:
            await _report_error(context, f"Graph node lookup failed: {exc.detail}")
            _record_failure("km-graph-node", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-graph-node", exc, start)
            raise
        _record_success("km-graph-node", start)
        return result

    @server.tool(name="km-graph-subsystem", description=TOOL_USAGE["km-graph-subsystem"]["description"])
    async def km_graph_subsystem(
        name: str,
        depth: int = 1,
        include_artifacts: bool = True,
        cursor: str | None = None,
        limit: int = 25,
        context: Context | None = None,
    ) -> dict[str, Any]:
        if not name or not name.strip():
            raise ValueError("name must be a non-empty string")
        limit = _clamp(limit, minimum=1, maximum=100)
        depth = _clamp(depth, minimum=0, maximum=5)
        start = perf_counter()
        try:
            result = await state.require_client().graph_subsystem(
                name.strip(),
                depth=depth,
                include_artifacts=include_artifacts,
                cursor=cursor,
                limit=limit,
            )
        except GatewayRequestError as exc:
            await _report_error(context, f"Subsystem lookup failed: {exc.detail}")
            _record_failure("km-graph-subsystem", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-graph-subsystem", exc, start)
            raise
        _record_success("km-graph-subsystem", start)
        return result

    @server.tool(name="km-graph-search", description=TOOL_USAGE["km-graph-search"]["description"])
    async def km_graph_search(
        term: str,
        limit: int = 20,
        context: Context | None = None,
    ) -> dict[str, Any]:
        if not term or not term.strip():
            raise ValueError("term must be a non-empty string")
        limit = _clamp(limit, minimum=1, maximum=50)
        start = perf_counter()
        try:
            result = await state.require_client().graph_search(term.strip(), limit=limit)
        except GatewayRequestError as exc:
            await _report_error(context, f"Graph search failed: {exc.detail}")
            _record_failure("km-graph-search", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-graph-search", exc, start)
            raise
        _record_success("km-graph-search", start)
        return result

    @server.tool(name="km-coverage-summary", description=TOOL_USAGE["km-coverage-summary"]["description"])
    async def km_coverage_summary(context: Context | None = None) -> dict[str, Any]:
        start = perf_counter()
        try:
            summary = await state.require_client().coverage_summary()
        except GatewayRequestError as exc:
            await _report_error(context, f"Coverage query failed: {exc.detail}")
            _record_failure("km-coverage-summary", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-coverage-summary", exc, start)
            raise
        _record_success("km-coverage-summary", start)
        return summary

    @server.tool(name="km-lifecycle-report", description=TOOL_USAGE["km-lifecycle-report"]["description"])
    async def km_lifecycle_report(context: Context | None = None) -> dict[str, Any]:
        start = perf_counter()
        try:
            report = await state.require_client().lifecycle_report()
        except GatewayRequestError as exc:
            await _report_error(context, f"Lifecycle query failed: {exc.detail}")
            _record_failure("km-lifecycle-report", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-lifecycle-report", exc, start)
            raise
        _record_success("km-lifecycle-report", start)
        return report

    @server.tool(name="km-ingest-status", description=TOOL_USAGE["km-ingest-status"]["description"])
    async def km_ingest_status(
        profile: str | None = None,
        context: Context | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        try:
            history = await state.require_client().audit_history(limit=10)
        except GatewayRequestError as exc:
            await _report_error(context, f"Failed to load ingest history: {exc.detail}")
            _record_failure("km-ingest-status", exc, start)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-ingest-status", exc, start)
            raise
        _record_success("km-ingest-status", start)
        record = await latest_ingest_status(history=history, profile=profile)
        if record is None:
            message = "No ingest runs found" if profile is None else f"No ingest runs found for profile '{profile}'"
            await _report_info(context, message)
            return {"status": "not_found", "profile": profile}
        await _report_info(
            context,
            f"Most recent ingest run {record.get('run_id')} succeeded" if record.get("success") else "Most recent ingest run failed",
        )
        return {"status": "ok", "run": record}

    @server.tool(name="km-ingest-trigger", description=TOOL_USAGE["km-ingest-trigger"]["description"])
    async def km_ingest_trigger(
        profile: str | None = None,
        paths: list[str] | None = None,
        dry_run: bool = False,
        use_dummy_embeddings: bool | None = None,
        context: Context | None = None,
    ) -> dict[str, Any]:
        if paths:
            raise ValueError("Targeted path ingest is not supported yet; omit 'paths' for a full rebuild")
        run_profile = profile or settings.ingest_profile_default
        await _report_info(context, f"Starting ingest run with profile '{run_profile}'")
        start = perf_counter()
        try:
            result = await trigger_ingest(
                settings=settings,
                profile=run_profile,
                dry_run=dry_run,
                use_dummy_embeddings=use_dummy_embeddings,
            )
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-ingest-trigger", exc, start)
            raise
        status = "success" if result.get("success") else "failure"
        if status == "success":
            _record_success("km-ingest-trigger", start)
            await _report_info(context, f"Ingest run completed with status {status}")
        else:
            _record_failure("km-ingest-trigger", RuntimeError("ingest run failed"), start)
            await _report_error(context, "Ingest run completed with status failure")
        return {"status": status, "run": result}

    @server.tool(name="km-backup-trigger", description=TOOL_USAGE["km-backup-trigger"]["description"])
    async def km_backup_trigger(context: Context | None = None) -> dict[str, Any]:
        await _report_info(context, "Launching backup helper")
        start = perf_counter()
        try:
            archive = await trigger_backup(settings)
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-backup-trigger", exc, start)
            raise
        _record_success("km-backup-trigger", start)
        await _report_info(context, f"Backup created at {archive['archive']}")
        return archive

    @server.tool(name="km-feedback-submit", description=TOOL_USAGE["km-feedback-submit"]["description"])
    async def km_feedback_submit(
        request_id: str,
        chunk_id: str,
        vote: float | None = None,
        note: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not request_id or not chunk_id:
            raise ValueError("request_id and chunk_id are required")
        start = perf_counter()
        try:
            payload = await record_feedback(
                settings=settings,
                request_id=request_id,
                chunk_id=chunk_id,
                vote=vote,
                note=note,
                context=context,
            )
        except Exception as exc:  # pragma: no cover - defensive
            _record_failure("km-feedback-submit", exc, start)
            raise
        _record_success("km-feedback-submit", start)
        return payload

    @server.tool(name="km-upload", description=TOOL_USAGE["km-upload"]["description"])
    async def km_upload(
        source_path: str,
        destination: str | None = None,
        overwrite: bool | None = None,
        ingest: bool | None = None,
        context: Context | None = None,
    ) -> dict[str, Any]:
        _ensure_maintainer_scope(settings)
        overwrite_flag = settings.upload_default_overwrite if overwrite is None else bool(overwrite)
        ingest_flag = settings.upload_default_ingest if ingest is None else bool(ingest)
        start = perf_counter()
        try:
            response = await handle_upload(
                settings=settings,
                source_path=source_path,
                destination=destination,
                overwrite=overwrite_flag,
                ingest=ingest_flag,
            )
        except Exception as exc:  # pragma: no cover - defensive
            MCP_UPLOAD_TOTAL.labels(result="error").inc()
            _record_failure("km-upload", exc, start)
            await _report_error(context, f"Upload failed: {exc}")
            raise
        MCP_UPLOAD_TOTAL.labels(result="success").inc()
        _record_success("km-upload", start)
        await _report_info(context, f"Stored file at {response['relative_path']}")
        _append_audit_entry(
            state.settings,
            tool="km-upload",
            payload={
                "source_path": source_path,
                "destination": destination,
                "relative_path": response["relative_path"],
                "overwritten": response["overwritten"],
                "ingest_triggered": response["ingest_triggered"],
            },
        )
        return response

    @server.tool(name="km-storetext", description=TOOL_USAGE["km-storetext"]["description"])
    async def km_storetext(
        content: str,
        title: str | None = None,
        destination: str | None = None,
        subsystem: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        overwrite: bool | None = None,
        ingest: bool | None = None,
        context: Context | None = None,
    ) -> dict[str, Any]:
        _ensure_maintainer_scope(settings)
        overwrite_flag = settings.upload_default_overwrite if overwrite is None else bool(overwrite)
        ingest_flag = settings.upload_default_ingest if ingest is None else bool(ingest)
        start = perf_counter()
        try:
            response = await handle_storetext(
                settings=settings,
                content=content,
                title=title,
                destination=destination,
                subsystem=subsystem,
                tags=tags,
                metadata=metadata,
                overwrite=overwrite_flag,
                ingest=ingest_flag,
            )
        except Exception as exc:  # pragma: no cover - defensive
            MCP_STORETEXT_TOTAL.labels(result="error").inc()
            _record_failure("km-storetext", exc, start)
            await _report_error(context, f"Storetext failed: {exc}")
            raise
        MCP_STORETEXT_TOTAL.labels(result="success").inc()
        _record_success("km-storetext", start)
        await _report_info(context, f"Stored text at {response['relative_path']}")
        _append_audit_entry(
            state.settings,
            tool="km-storetext",
            payload={
                "relative_path": response["relative_path"],
                "title": title,
                "destination": destination,
                "ingest_triggered": response["ingest_triggered"],
            },
        )
        return response

    return server


async def _report_info(context: Context | None, message: str) -> None:
    if context is not None:
        await context.info(message)


async def _report_error(context: Context | None, message: str) -> None:
    if context is not None:
        await context.error(message)


def _record_success(tool: str, start: float) -> None:
    duration = perf_counter() - start
    MCP_REQUESTS_TOTAL.labels(tool, "success").inc()
    MCP_REQUEST_SECONDS.labels(tool).observe(duration)


def _record_failure(tool: str, exc: Exception, start: float) -> None:
    duration = perf_counter() - start
    MCP_REQUESTS_TOTAL.labels(tool, "error").inc()
    MCP_FAILURES_TOTAL.labels(tool, exc.__class__.__name__).inc()
    MCP_REQUEST_SECONDS.labels(tool).observe(duration)


def _clamp(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _normalise_filters(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "subsystems",
        "artifact_types",
        "namespaces",
        "tags",
        "updated_after",
        "max_age_days",
    }
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in allowed:
            continue
        if value is None:
            continue
        result[key] = value
    return result


def _resolve_usage(tool: str | None) -> dict[str, Any]:
    if tool:
        key = tool.strip()
        if not key:
            raise ValueError("tool must be a non-empty string when provided")
        usage = TOOL_USAGE.get(key)
        if usage is None:
            available = ", ".join(sorted(TOOL_USAGE))
            raise ValueError(f"Unknown tool '{key}'. Available tools: {available}")
        return {"tool": key, "usage": dict(usage)}
    return {"tools": {name: dict(data) for name, data in TOOL_USAGE.items()}}


def _ensure_maintainer_scope(settings: MCPSettings) -> None:
    if settings.admin_token:
        return
    raise PermissionError("Maintainer token (KM_ADMIN_TOKEN) must be configured to use this tool")


def _append_audit_entry(settings: MCPSettings, *, tool: str, payload: dict[str, Any]) -> None:
    try:
        audit_dir = settings.state_path / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "tool": tool,
            "timestamp": datetime.now(UTC).isoformat(),
            **payload,
        }
        audit_file = audit_dir / "mcp_actions.log"
        with audit_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # pragma: no cover - audit best-effort
        # Audit logging should not block primary operations.
        return


@lru_cache(maxsize=1)
def _load_help_document() -> str:
    try:
        return HELP_DOC_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "MCP interface specification not found; expected at docs/MCP_INTERFACE_SPEC.md. "
            "Ensure documentation is included with the deployment."
        )


__all__ = ["build_server"]


def _initialise_metric_labels() -> None:
    tools = list(TOOL_USAGE.keys()) + ["km-help"]
    for tool in tools:
        MCP_REQUESTS_TOTAL.labels(tool, "success").inc(0)
        MCP_REQUESTS_TOTAL.labels(tool, "error").inc(0)
        MCP_REQUEST_SECONDS.labels(tool)
    MCP_UPLOAD_TOTAL.labels(result="success").inc(0)
    MCP_UPLOAD_TOTAL.labels(result="error").inc(0)
    MCP_STORETEXT_TOTAL.labels(result="success").inc(0)
    MCP_STORETEXT_TOTAL.labels(result="error").inc(0)
