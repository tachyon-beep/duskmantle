from __future__ import annotations

import json
from pathlib import Path

import pytest

RECIPES = Path("docs/MCP_RECIPES.md").read_text().splitlines()


@pytest.mark.mcp_smoke
@pytest.mark.parametrize("line", [recipe_line for recipe_line in RECIPES if recipe_line.strip().startswith("km-")])
def test_recipe_lines_are_valid_json(line: str) -> None:
    stripped = line.strip()
    if "{" not in stripped:
        pytest.skip("No JSON payload on this line")
    command, payload = stripped.split(None, 1)
    try:
        json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON payload in MCP recipe: {payload}") from exc
