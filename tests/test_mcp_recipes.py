from __future__ import annotations

import json
from pathlib import Path

import pytest

RECIPES = Path("docs/MCP_RECIPES.md").read_text()


@pytest.mark.parametrize(
    "snippet",
    [
        'km-search {"query": "ingest pipeline", "limit": 2}',
        'km-graph-node {"node_id": "DesignDoc:docs/QUICK_START.md"}',
        "km-coverage-summary {}",
    ],
)
def test_snippets_are_valid_json(snippet: str) -> None:
    commands = [line.strip(" >") for line in snippet.splitlines() if line.strip().startswith("km-")]
    for cmd in commands:
        if "{" in cmd:
            payload = cmd.split(None, 1)[1]
            json.loads(payload)
