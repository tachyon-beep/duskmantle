from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Any

import pytest

from gateway.mcp.config import MCPSettings
from gateway.recipes.executor import RecipeExecutionError, RecipeRunner
from gateway.recipes.models import Recipe


class FakeToolExecutor:
    def __init__(self, responses: dict[str, list[Any] | Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def __aenter__(self) -> FakeToolExecutor:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        return None

    async def call(self, tool: str, params: dict[str, object]) -> object:
        self.calls.append((tool, params))
        value = self.responses[tool]
        if isinstance(value, list):
            if not value:
                raise RuntimeError(f"No responses left for tool {tool}")
            item = value.pop(0)
            return item
        if callable(value):
            return value(params)  # type: ignore[call-arg]
        return value


@pytest.mark.asyncio
async def test_recipe_runner_success(tmp_path: Path) -> None:
    recipe = Recipe.model_validate(
        {
            "version": 1,
            "name": "simple",
            "steps": [
                {
                    "id": "coverage",
                    "tool": "km-coverage-summary",
                    "expect": {"result.status": "ok"},
                    "capture": [{"name": "coverage"}],
                }
            ],
            "outputs": {"status": "${captures.coverage.status}"},
        }
    )
    fake = FakeToolExecutor({"km-coverage-summary": {"status": "ok"}})
    settings = MCPSettings()
    runner = RecipeRunner(settings, executor_factory=lambda: fake, audit_path=tmp_path / "recipes.log")

    result = await runner.run(recipe)
    assert result.success is True
    assert result.outputs["status"] == "ok"
    assert fake.calls == [("km-coverage-summary", {})]


@pytest.mark.asyncio
async def test_recipe_runner_wait(tmp_path: Path) -> None:
    recipe = Recipe.model_validate(
        {
            "version": 1,
            "name": "waiter",
            "steps": [
                {
                    "id": "wait-ingest",
                    "wait": {
                        "tool": "km-ingest-status",
                        "params": {"profile": "manual"},
                        "until": {"path": "status", "equals": "ok"},
                        "interval_seconds": 0.5,
                        "timeout_seconds": 1.5,
                    },
                }
            ],
        }
    )
    counter = {"count": 0}

    def status_fn(_params: dict[str, object]) -> dict[str, object]:
        counter["count"] += 1
        if counter["count"] < 2:
            return {"status": "running"}
        return {"status": "ok", "run": {"success": True}}

    fake = FakeToolExecutor({"km-ingest-status": status_fn})
    settings = MCPSettings()
    runner = RecipeRunner(settings, executor_factory=lambda: fake, audit_path=tmp_path / "recipes.log")

    result = await runner.run(recipe)
    assert result.success is True
    assert counter["count"] >= 2


@pytest.mark.asyncio
async def test_recipe_runner_expect_failure(tmp_path: Path) -> None:
    recipe = Recipe.model_validate(
        {
            "version": 1,
            "name": "failure",
            "steps": [
                {
                    "id": "coverage",
                    "tool": "km-coverage-summary",
                    "expect": {"result.status": "ok"},
                }
            ],
        }
    )
    fake = FakeToolExecutor({"km-coverage-summary": {"status": "error"}})
    settings = MCPSettings()
    runner = RecipeRunner(settings, executor_factory=lambda: fake, audit_path=tmp_path / "recipes.log")

    with pytest.raises(RecipeExecutionError):
        await runner.run(recipe)


@pytest.mark.asyncio
async def test_recipe_runner_dry_run(tmp_path: Path) -> None:
    recipe = Recipe.model_validate(
        {
            "version": 1,
            "name": "dry",
            "steps": [
                {"id": "coverage", "tool": "km-coverage-summary"},
            ],
        }
    )
    fake = FakeToolExecutor({"km-coverage-summary": {"status": "ok"}})
    settings = MCPSettings()
    runner = RecipeRunner(settings, executor_factory=lambda: fake, audit_path=tmp_path / "recipes.log")

    result = await runner.run(recipe, dry_run=True)
    assert result.success is True
    assert fake.calls == []
