from __future__ import annotations

import json
from pathlib import Path

import pytest

RECIPES = Path("docs/MCP_RECIPES.md").read_text().splitlines()


def _recipe_params() -> list[pytest.ParameterSet]:
    params: list[pytest.ParameterSet] = []
    for idx, recipe_line in enumerate(RECIPES):
        if recipe_line.strip().startswith("km-"):
            params.append(pytest.param(recipe_line, id=f"recipe-{idx}"))
    return params


@pytest.mark.mcp_smoke
@pytest.mark.parametrize("line", _recipe_params())
def test_recipe_lines_are_valid_json(line: str) -> None:
    stripped = line.strip()
    if "{" not in stripped:
        pytest.skip("No JSON payload on this line")
    command, payload = stripped.split(None, 1)
    try:
        json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON payload in MCP recipe: {payload}") from exc
