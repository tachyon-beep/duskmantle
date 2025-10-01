from __future__ import annotations

import json
import os
import shutil
import signal
from datetime import UTC, datetime, timedelta
from pathlib import Path

import uvicorn

from gateway.api.app import create_app


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _prepare_state(state_path: Path) -> None:
    reports_dir = state_path / "reports"
    history_dir = reports_dir / "lifecycle_history"
    history_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=UTC)
    earlier = now - timedelta(days=7)
    midpoint = now - timedelta(days=3)
    later = now - timedelta(days=1)

    # Lifecycle report payload used by /lifecycle
    lifecycle_payload = {
        "generated_at": later.timestamp(),
        "generated_at_iso": later.isoformat(),
        "run": {
            "run_id": "playwright-run",
            "profile": "playwright",
            "repo_head": "deadbeef",
        },
        "thresholds": {
            "stale_days": 30,
        },
        "isolated": {
            "DesignDoc": [
                {
                    "id": "DesignDoc:docs/orphan.md",
                    "path": "docs/orphan.md",
                    "name": "Orphan DesignDoc",
                }
            ]
        },
        "stale_docs": [
            {
                "path": "docs/design/playbook.md",
                "subsystem": "ReleaseTooling",
                "git_timestamp": (later - timedelta(days=90)).timestamp(),
            },
            {
                "path": "docs/api/overview.md",
                "subsystem": "GatewayCore",
                "git_timestamp": (later - timedelta(days=60)).timestamp(),
            },
        ],
        "missing_tests": [
            {
                "subsystem": "GatewayCore",
                "note": "Add integration smoke tests",
            }
        ],
        "removed_artifacts": [
            {
                "path": "docs/legacy.md",
                "removed_at": now.isoformat(),
            }
        ],
        "summary": {
            "stale_docs": 2,
            "isolated_nodes": 1,
            "subsystems_missing_tests": 1,
            "removed_artifacts": 1,
        },
    }

    _write_json(reports_dir / "lifecycle_report.json", lifecycle_payload)

    history_entries = [
        (
            earlier,
            {
                **lifecycle_payload,
                "generated_at": earlier.timestamp(),
                "generated_at_iso": earlier.isoformat(),
                "summary": {
                    "stale_docs": 0,
                    "isolated_nodes": 0,
                    "subsystems_missing_tests": 0,
                    "removed_artifacts": 0,
                },
                "counts": {
                    "stale_docs": 0,
                    "isolated_nodes": 0,
                    "subsystems_missing_tests": 0,
                    "removed_artifacts": 0,
                },
                "stale_docs": [],
                "isolated": {},
                "missing_tests": [],
                "removed_artifacts": [],
            },
        ),
        (
            midpoint,
            {
                **lifecycle_payload,
                "generated_at": midpoint.timestamp(),
                "generated_at_iso": midpoint.isoformat(),
                "summary": {
                    "stale_docs": 1,
                    "isolated_nodes": 1,
                    "subsystems_missing_tests": 0,
                    "removed_artifacts": 0,
                },
                "counts": {
                    "stale_docs": 1,
                    "isolated_nodes": 1,
                    "subsystems_missing_tests": 0,
                    "removed_artifacts": 0,
                },
                "stale_docs": lifecycle_payload["stale_docs"][:1],
                "isolated": lifecycle_payload["isolated"],
                "missing_tests": [],
                "removed_artifacts": [],
            },
        ),
        (
            later,
            {
                **lifecycle_payload,
                "counts": lifecycle_payload["summary"],
            },
        ),
    ]

    for _index, (point_time, payload) in enumerate(history_entries, start=1):
        timestamp = point_time.strftime("%Y%m%dT%H%M%S000000")
        _write_json(history_dir / f"lifecycle_{timestamp}.json", payload)


def _configure_environment(state_path: Path) -> None:
    os.environ.setdefault("KM_STATE_PATH", str(state_path))
    os.environ.setdefault("KM_AUTH_ENABLED", "false")
    os.environ.setdefault("KM_SCHEDULER_ENABLED", "false")
    os.environ.setdefault("KM_WATCH_ENABLED", "false")
    os.environ.setdefault("KM_LIFECYCLE_HISTORY_LIMIT", "30")
    os.environ.setdefault("KM_LOG_LEVEL", "WARNING")


def main() -> None:
    root = Path(os.environ.get("PLAYWRIGHT_STATE_PATH", ".playwright-state")).resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    _configure_environment(root)
    _prepare_state(root)

    app = create_app()

    port = int(os.environ.get("PLAYWRIGHT_PORT", "8765"))
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    def _handle_stop(*_args: object) -> None:
        server.should_exit = True

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    server.run()


if __name__ == "__main__":
    main()
