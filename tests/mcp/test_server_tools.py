from pathlib import Path

import pytest

from gateway.mcp.config import MCPSettings
from gateway.mcp.exceptions import GatewayRequestError
from gateway.mcp.server import build_server
from gateway.observability.metrics import (
    MCP_FAILURES_TOTAL,
    MCP_REQUEST_SECONDS,
    MCP_REQUESTS_TOTAL,
    MCP_STORETEXT_TOTAL,
    MCP_UPLOAD_TOTAL,
)
from prometheus_client import generate_latest


@pytest.fixture(autouse=True)
def _reset_mcp_metrics():
    MCP_REQUESTS_TOTAL.clear()
    MCP_FAILURES_TOTAL.clear()
    MCP_REQUEST_SECONDS.clear()
    MCP_UPLOAD_TOTAL.clear()
    MCP_STORETEXT_TOTAL.clear()
    yield
    MCP_REQUESTS_TOTAL.clear()
    MCP_FAILURES_TOTAL.clear()
    MCP_REQUEST_SECONDS.clear()
    MCP_UPLOAD_TOTAL.clear()
    MCP_STORETEXT_TOTAL.clear()


@pytest.fixture
def mcp_server():
    server = build_server(settings=MCPSettings())
    state = server._duskmantle_state
    yield server, state
    state.client = None


def _counter_value(counter, *labels: str) -> float:
    return counter.labels(*labels)._value.get()


def _histogram_sum(histogram, *labels: str) -> float:
    return histogram.labels(*labels)._sum.get()


def _upload_counter(result: str) -> float:
    return MCP_UPLOAD_TOTAL.labels(result)._value.get()


def _storetext_counter(result: str) -> float:
    return MCP_STORETEXT_TOTAL.labels(result)._value.get()


@pytest.mark.asyncio
async def test_km_help_lists_tools_and_provides_details(monkeypatch, mcp_server):
    server, _state = mcp_server

    from gateway.mcp import server as mcp_server_module

    mcp_server_module._load_help_document.cache_clear()

    def stub_spec():
        return "stub spec"

    monkeypatch.setattr(mcp_server_module, "_load_help_document", stub_spec)

    tool = await server.get_tool("km-help")

    listing = await tool.fn(tool=None, include_spec=False, context=None)
    assert "km-search" in listing["tools"]
    assert listing["tools"]["km-search"]["description"].startswith("Hybrid search")

    detail = await tool.fn(tool="km-search", include_spec=True, context=None)
    assert detail["tool"] == "km-search"
    assert "Required: `query`" in detail["usage"]["details"]
    assert detail["spec"] == "stub spec"


@pytest.mark.asyncio
async def test_metrics_export_includes_tool_labels(monkeypatch, mcp_server):
    server, _state = mcp_server

    tool = await server.get_tool("km-help")
    await tool.fn(context=None)

    metrics_data = generate_latest().decode()
    assert 'km_mcp_requests_total{result="success",tool="km-help"} 1.0' in metrics_data


@pytest.mark.asyncio
async def test_km_search_success_records_metrics(mcp_server):
    server, state = mcp_server

    class StubClient:
        async def search(self, payload):
            assert payload["query"] == "design docs"
            return {"results": [], "metadata": {}}

    state.client = StubClient()

    tool = await server.get_tool("km-search")
    result = await tool.fn(query="design docs", limit=5, include_graph=False, context=None)

    assert result == {"results": [], "metadata": {}}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-search", "success") == 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-search", "error") == 0
    assert _counter_value(MCP_FAILURES_TOTAL, "km-search", "GatewayRequestError") == 0
    assert _histogram_sum(MCP_REQUEST_SECONDS, "km-search") > 0.0


@pytest.mark.asyncio
async def test_km_search_gateway_error_records_failure(mcp_server):
    server, state = mcp_server

    class StubClient:
        async def search(self, payload):  # pragma: no cover - exercised in test
            raise GatewayRequestError(status_code=500, detail="upstream boom")

    state.client = StubClient()

    tool = await server.get_tool("km-search")
    with pytest.raises(GatewayRequestError):
        await tool.fn(query="design docs", limit=3, include_graph=True, context=None)

    assert _counter_value(MCP_REQUESTS_TOTAL, "km-search", "success") == 0
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-search", "error") == 1
    assert _counter_value(MCP_FAILURES_TOTAL, "km-search", "GatewayRequestError") == 1
    assert _histogram_sum(MCP_REQUEST_SECONDS, "km-search") > 0.0


@pytest.mark.asyncio
async def test_graph_tools_delegate_to_client_and_record_metrics(mcp_server):
    server, state = mcp_server

    class StubClient:
        async def graph_node(self, node_id, *, relationships, limit):
            assert node_id == "DesignDoc:docs/README.md"
            assert relationships == "outgoing"
            assert limit == 25
            return {"id": node_id}

        async def graph_subsystem(self, name, *, depth, include_artifacts, cursor, limit):
            assert name == "Kasmina"
            assert depth == 1
            assert include_artifacts is True
            assert cursor is None
            assert limit == 10
            return {"name": name}

        async def graph_search(self, term, *, limit):
            assert term == "ingest"
            assert limit == 7
            return {"results": ["node"]}

    state.client = StubClient()

    node_tool = await server.get_tool("km-graph-node")
    node = await node_tool.fn(
        node_id="DesignDoc:docs/README.md",
        relationships="outgoing",
        limit=25,
        context=None,
    )
    subsystem_tool = await server.get_tool("km-graph-subsystem")
    subsystem = await subsystem_tool.fn(
        name="Kasmina",
        depth=1,
        include_artifacts=True,
        cursor=None,
        limit=10,
        context=None,
    )
    search_tool = await server.get_tool("km-graph-search")
    graph_search = await search_tool.fn(term="ingest", limit=7, context=None)

    assert node == {"id": "DesignDoc:docs/README.md"}
    assert subsystem == {"name": "Kasmina"}
    assert graph_search == {"results": ["node"]}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-graph-node", "success") == 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-graph-subsystem", "success") == 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-graph-search", "success") == 1


@pytest.mark.asyncio
async def test_lifecycle_report_records_metrics(mcp_server):
    server, state = mcp_server

    class StubClient:
        async def lifecycle_report(self):
            return {"missing_tests": []}

    state.client = StubClient()

    tool = await server.get_tool("km-lifecycle-report")
    report = await tool.fn(context=None)

    assert report == {"missing_tests": []}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-lifecycle-report", "success") == 1


@pytest.mark.asyncio
async def test_coverage_summary_records_metrics(mcp_server):
    server, state = mcp_server

    class StubClient:
        async def coverage_summary(self):
            return {"artifacts": 10}

    state.client = StubClient()

    tool = await server.get_tool("km-coverage-summary")
    summary = await tool.fn(context=None)

    assert summary == {"artifacts": 10}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-coverage-summary", "success") == 1


@pytest.mark.asyncio
async def test_ingest_status_handles_missing_history(mcp_server):
    server, state = mcp_server

    class StubClient:
        async def audit_history(self, *, limit):
            assert limit == 10
            return []

    state.client = StubClient()

    tool = await server.get_tool("km-ingest-status")
    status = await tool.fn(profile=None, context=None)

    assert status == {"status": "not_found", "profile": None}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-ingest-status", "success") == 1


@pytest.mark.asyncio
async def test_ingest_trigger_succeeds(monkeypatch, mcp_server):
    server, state = mcp_server

    called: dict[str, tuple] = {}

    async def stub_trigger_ingest(*, settings, profile, dry_run, use_dummy_embeddings):
        called["args"] = (profile, dry_run, use_dummy_embeddings)
        return {"success": True, "run_id": "xyz"}

    monkeypatch.setattr("gateway.mcp.server.trigger_ingest", stub_trigger_ingest)

    tool = await server.get_tool("km-ingest-trigger")
    result = await tool.fn(
        profile="manual",
        paths=None,
        dry_run=False,
        use_dummy_embeddings=None,
        context=None,
    )

    assert result == {"status": "success", "run": {"success": True, "run_id": "xyz"}}
    assert called["args"] == ("manual", False, None)
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-ingest-trigger", "success") == 1


@pytest.mark.asyncio
async def test_ingest_trigger_failure_records_metrics(monkeypatch, mcp_server):
    server, _state = mcp_server

    async def stub_trigger_ingest(**_kwargs):  # pragma: no cover - exercised in test
        return {"success": False}

    monkeypatch.setattr("gateway.mcp.server.trigger_ingest", stub_trigger_ingest)

    tool = await server.get_tool("km-ingest-trigger")
    result = await tool.fn(profile=None, paths=None, dry_run=False, use_dummy_embeddings=None, context=None)

    assert result == {"status": "failure", "run": {"success": False}}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-ingest-trigger", "error") == 1
    assert _counter_value(MCP_FAILURES_TOTAL, "km-ingest-trigger", "RuntimeError") == 1


@pytest.mark.asyncio
async def test_backup_trigger(monkeypatch, mcp_server):
    server, _state = mcp_server

    async def stub_trigger_backup(_settings):
        return {"archive": "backups/km-backup.tgz"}

    monkeypatch.setattr("gateway.mcp.server.trigger_backup", stub_trigger_backup)

    tool = await server.get_tool("km-backup-trigger")
    archive = await tool.fn(context=None)

    assert archive == {"archive": "backups/km-backup.tgz"}
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-backup-trigger", "success") == 1


@pytest.mark.asyncio
async def test_feedback_submit(monkeypatch, mcp_server):
    server, _state = mcp_server

    async def stub_record_feedback(**kwargs):
        return {"echo": kwargs}

    monkeypatch.setattr("gateway.mcp.server.record_feedback", stub_record_feedback)

    tool = await server.get_tool("km-feedback-submit")
    payload = await tool.fn(
        request_id="req-1",
        chunk_id="chunk-1",
        vote=1.0,
        note="useful",
        context={"task": "demo"},
    )

    assert payload["echo"]["request_id"] == "req-1"
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-feedback-submit", "success") == 1


@pytest.mark.asyncio
async def test_km_upload_copies_file_and_records_metrics(tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="secret",
        KM_UPLOAD_DEFAULT_INGEST="false",
        KM_UPLOAD_DEFAULT_OVERWRITE="false",
    )
    server = build_server(settings=settings)

    source = tmp_path / "notes.md"
    source.write_text("notes")

    tool = await server.get_tool("km-upload")
    result = await tool.fn(
        source_path=str(source),
        destination=None,
        overwrite=None,
        ingest=None,
        context=None,
    )

    target = content_root / "docs" / "notes.md"
    assert target.exists()
    assert result["relative_path"] == "docs/notes.md"
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-upload", "success") == 1
    assert _upload_counter("success") == 1
    audit_file = state_path / "audit" / "mcp_actions.log"
    assert audit_file.exists()
    assert '"tool": "km-upload"' in audit_file.read_text()


@pytest.mark.asyncio
async def test_km_upload_missing_source_raises(tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="secret",
    )
    server = build_server(settings=settings)

    tool = await server.get_tool("km-upload")
    with pytest.raises(ValueError):
        await tool.fn(
            source_path=str(tmp_path / "missing.md"),
            destination=None,
            overwrite=None,
            ingest=None,
            context=None,
        )

    assert _counter_value(MCP_REQUESTS_TOTAL, "km-upload", "error") == 1
    assert _upload_counter("error") == 1


@pytest.mark.asyncio
async def test_km_upload_requires_admin_token(tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="",
    )
    server = build_server(settings=settings)

    source = tmp_path / "note.md"
    source.write_text("note")

    tool = await server.get_tool("km-upload")
    with pytest.raises(PermissionError):
        await tool.fn(
            source_path=str(source),
            destination=None,
            overwrite=None,
            ingest=None,
            context=None,
        )


@pytest.mark.asyncio
async def test_km_upload_triggers_ingest_when_requested(monkeypatch, tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    settings = MCPSettings(
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="secret",
        KM_MCP_DEFAULT_INGEST_PROFILE="demo",
    )
    server = build_server(settings=settings)

    source = tmp_path / "demo.txt"
    source.write_text("demo")

    async def fake_trigger_ingest(*, settings, profile, dry_run, use_dummy_embeddings):
        assert profile == "demo"
        return {"success": True, "profile": profile, "run_id": "123"}

    monkeypatch.setattr("gateway.mcp.upload.trigger_ingest", fake_trigger_ingest)

    tool = await server.get_tool("km-upload")
    result = await tool.fn(
        source_path=str(source),
        destination="docs/uploads",
        overwrite=True,
        ingest=True,
        context=None,
    )

    target = content_root / "docs" / "uploads" / "demo.txt"
    assert target.exists()
    assert result["ingest_triggered"] is True
    assert result["ingest_run"]["success"] is True
    assert _upload_counter("success") == 1


@pytest.mark.asyncio
async def test_km_storetext_creates_document_with_front_matter(tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="secret",
    )
    server = build_server(settings=settings)

    tool = await server.get_tool("km-storetext")
    result = await tool.fn(
        content="## Body\nDetails",
        title="Release Notes",
        destination=None,
        subsystem="Deployment",
        tags=["release", "notes"],
        metadata={"author": "agent"},
        overwrite=None,
        ingest=None,
        context=None,
    )

    stored = content_root / result["relative_path"]
    assert stored.exists()
    contents = stored.read_text()
    assert "title: Release Notes" in contents
    assert "subsystem: Deployment" in contents
    assert "tags: [release, notes]" in contents
    assert "author: agent" in contents
    assert contents.strip().endswith("Details")
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-storetext", "success") == 1
    assert _storetext_counter("success") == 1
    audit_file = state_path / "audit" / "mcp_actions.log"
    assert audit_file.exists()
    assert '"tool": "km-storetext"' in audit_file.read_text()


@pytest.mark.asyncio
async def test_km_storetext_requires_content(tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="secret",
    )
    server = build_server(settings=settings)

    tool = await server.get_tool("km-storetext")
    with pytest.raises(ValueError):
        await tool.fn(
            content=" ",
            title=None,
            destination=None,
            subsystem=None,
            tags=None,
            metadata=None,
            overwrite=None,
            ingest=None,
            context=None,
        )

    assert _counter_value(MCP_REQUESTS_TOTAL, "km-storetext", "error") == 1
    assert _storetext_counter("error") == 1


@pytest.mark.asyncio
async def test_km_storetext_triggers_ingest_when_requested(monkeypatch, tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="secret",
        KM_MCP_DEFAULT_INGEST_PROFILE="demo",
    )
    server = build_server(settings=settings)

    async def fake_trigger_ingest(*, settings, profile, dry_run, use_dummy_embeddings):
        assert profile == "demo"
        return {"success": True, "profile": profile, "run_id": "abc"}

    monkeypatch.setattr("gateway.mcp.storetext.trigger_ingest", fake_trigger_ingest)

    tool = await server.get_tool("km-storetext")
    result = await tool.fn(
        content="Hello world",
        title="demo",
        destination="docs/uploads",
        subsystem=None,
        tags=None,
        metadata=None,
        overwrite=True,
        ingest=True,
        context=None,
    )

    stored = content_root / result["relative_path"]
    assert stored.exists()
    assert result["ingest_triggered"] is True
    assert result["ingest_run"]["success"] is True
    assert _storetext_counter("success") == 1


@pytest.mark.asyncio
async def test_km_storetext_requires_admin_token(tmp_path: Path):
    content_root = tmp_path / "repo"
    (content_root / "docs").mkdir(parents=True)
    state_path = tmp_path / "state"
    settings = MCPSettings(
        KM_STATE_PATH=str(state_path),
        KM_CONTENT_ROOT=str(content_root),
        KM_CONTENT_DOCS_SUBDIR="docs",
        KM_ADMIN_TOKEN="",
    )
    server = build_server(settings=settings)

    tool = await server.get_tool("km-storetext")
    with pytest.raises(PermissionError):
        await tool.fn(
            content="Hello",
            title=None,
            destination=None,
            subsystem=None,
            tags=None,
            metadata=None,
            overwrite=None,
            ingest=None,
            context=None,
        )


@pytest.mark.asyncio
@pytest.mark.mcp_smoke
async def test_mcp_smoke_run(monkeypatch, mcp_server):
    server, state = mcp_server

    class StubClient:
        async def search(self, payload):
            return {"results": ["hit"], "metadata": {}}

        async def coverage_summary(self):
            return {"artifacts": 1}

        async def graph_node(self, node_id, *, relationships, limit):
            return {
                "node": {"id": node_id, "labels": ["DesignDoc"], "properties": {"path": "docs/demo.md"}},
                "relationships": [
                    {
                        "type": "HAS_CHUNK",
                        "direction": "OUT",
                        "target": {
                            "id": "Chunk:docs/demo.md::0",
                            "labels": ["Chunk"],
                            "properties": {"chunk_id": "docs/demo.md::0"},
                        },
                    }
                ],
            }

        async def graph_subsystem(self, name, *, depth, include_artifacts, cursor, limit):
            return {
                "subsystem": {"id": f"Subsystem:{name}", "labels": ["Subsystem"], "properties": {"name": name}},
                "related": {"nodes": [], "cursor": None},
                "artifacts": [],
            }

        async def graph_search(self, term, *, limit):
            return {"results": [{"id": "Subsystem:demo", "label": "Subsystem", "score": 0.5, "snippet": term}]}

    state.client = StubClient()

    async def stub_trigger_backup(settings):
        return {"archive": "demo.tgz"}

    monkeypatch.setattr("gateway.mcp.server.trigger_backup", stub_trigger_backup)

    search_tool = await server.get_tool("km-search")
    search_result = await search_tool.run({"query": "demo", "context": None})
    coverage_tool = await server.get_tool("km-coverage-summary")
    coverage_result = await coverage_tool.run({"context": None})
    backup_tool = await server.get_tool("km-backup-trigger")
    backup_result = await backup_tool.run({"context": None})
    node_tool = await server.get_tool("km-graph-node")
    node_result = await node_tool.run({"node_id": "DesignDoc:docs/demo.md", "relationships": "outgoing", "limit": 5, "context": None})
    subsystem_tool = await server.get_tool("km-graph-subsystem")
    subsystem_result = await subsystem_tool.run({"name": "Demo", "depth": 1, "context": None})
    graph_search_tool = await server.get_tool("km-graph-search")
    graph_search_result = await graph_search_tool.run({"term": "demo", "limit": 5, "context": None})

    assert search_result.content is not None
    assert coverage_result.content is not None
    assert backup_result.content is not None
    assert node_result.content is not None
    assert subsystem_result.content is not None
    assert graph_search_result.content is not None
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-search", "success") >= 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-coverage-summary", "success") >= 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-backup-trigger", "success") >= 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-graph-node", "success") >= 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-graph-subsystem", "success") >= 1
    assert _counter_value(MCP_REQUESTS_TOTAL, "km-graph-search", "success") >= 1

    metrics_blob = generate_latest().decode()
    assert 'km_mcp_requests_total{result="success",tool="km-search"}' in metrics_blob
    assert 'km_mcp_requests_total{result="success",tool="km-graph-node"}' in metrics_blob
    assert 'km_mcp_requests_total{result="success",tool="km-graph-subsystem"}' in metrics_blob
