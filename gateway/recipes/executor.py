from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict

import yaml
from gateway.mcp.backup import trigger_backup
from gateway.mcp.config import MCPSettings
from gateway.mcp.ingest import latest_ingest_status, trigger_ingest
from gateway.mcp.client import GatewayClient

from .models import Capture, Condition, Recipe, RecipeStep, WaitConfig

logger = logging.getLogger(__name__)


class RecipeExecutionError(RuntimeError):
    """Raised when a recipe step fails."""


@dataclass
class StepResult:
    step_id: str
    status: str
    duration_seconds: float
    result: Any | None = None
    message: str | None = None


@dataclass
class RecipeRunResult:
    recipe: Recipe
    started_at: float
    finished_at: float
    success: bool
    steps: list[StepResult] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe": self.recipe.name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.finished_at - self.started_at,
            "success": self.success,
            "steps": [
                {
                    "id": step.step_id,
                    "status": step.status,
                    "duration_seconds": step.duration_seconds,
                    "message": step.message,
                    "result": step.result,
                }
                for step in self.steps
            ],
            "outputs": self.outputs,
        }


class ToolExecutor:
    """Abstract tool executor interface."""

    async def call(self, tool: str, params: dict[str, Any]) -> Any:  # pragma: no cover - interface
        raise NotImplementedError

    async def __aenter__(self) -> "ToolExecutor":  # pragma: no cover - interface
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - interface
        return None


class GatewayToolExecutor(ToolExecutor):
    """Execute tools by reusing gateway HTTP/MCP helpers."""

    def __init__(self, settings: MCPSettings):
        self.settings = settings
        self._client_manager: GatewayClient | None = None
        self._client: GatewayClient | None = None

    async def __aenter__(self) -> "GatewayToolExecutor":
        self._client_manager = GatewayClient(self.settings)
        self._client = await self._client_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client_manager is not None:
            await self._client_manager.__aexit__(exc_type, exc, tb)
        self._client = None
        self._client_manager = None

    async def call(self, tool: str, params: dict[str, Any]) -> Any:
        if self._client is None:
            raise RuntimeError("Gateway client not initialised")
        client = self._client

        if tool == "km-search":
            return await client.search(params)
        if tool == "km-graph-subsystem":
            return await client.graph_subsystem(
                params["name"],
                depth=params.get("depth", 1),
                include_artifacts=params.get("include_artifacts", True),
                cursor=params.get("cursor"),
                limit=params.get("limit", 25),
            )
        if tool == "km-graph-node":
            return await client.graph_node(
                params["node_id"],
                relationships=params.get("relationships", "outgoing"),
                limit=params.get("limit", 50),
            )
        if tool == "km-graph-search":
            return await client.graph_search(params.get("term", ""), limit=params.get("limit", 20))
        if tool == "km-coverage-summary":
            return await client.coverage_summary()
        if tool == "km-lifecycle-report":
            return await client.lifecycle_report()
        if tool == "km-ingest-status":
            limit = int(params.get("limit", 10))
            history = await client.audit_history(limit=limit)
            profile = params.get("profile")
            record = await latest_ingest_status(history=history, profile=profile)
            if record is None:
                return {"status": "not_found", "profile": profile}
            return {"status": "ok", "run": record}
        if tool == "km-ingest-trigger":
            profile = params.get("profile") or self.settings.ingest_profile_default
            dry_run = bool(params.get("dry_run", False))
            use_dummy = params.get("use_dummy_embeddings")
            result = await trigger_ingest(
                settings=self.settings,
                profile=profile,
                dry_run=dry_run,
                use_dummy_embeddings=use_dummy,
            )
            return {"status": "success" if result.get("success") else "failure", "run": result}
        if tool == "km-backup-trigger":
            return await trigger_backup(self.settings)
        if tool == "km-audit-history":
            limit = int(params.get("limit", 20))
            return await client.audit_history(limit=limit)

        raise RecipeExecutionError(f"Unsupported tool '{tool}' in recipe")


def _resolve_template(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        if value.startswith("${") and value.endswith("}") and value.count("${") == 1:
            expr = value[2:-1].strip()
            return _lookup_expression(expr, context)

        def replace(match):
            expr_inner = match.group(1)
            resolved = _lookup_expression(expr_inner.strip(), context)
            return str(resolved)

        if "${" in value:
            import re

            return re.sub(r"\$\{([^}]+)\}", replace, value)
    if isinstance(value, list):
        return [_resolve_template(item, context) for item in value]
    if isinstance(value, dict):
        return {k: _resolve_template(v, context) for k, v in value.items()}
    return value


def _lookup_expression(expr: str, context: dict[str, Any]) -> Any:
    parts = expr.split(".")
    root = context
    current: Any = None
    for index, part in enumerate(parts):
        if index == 0:
            if part == "vars":
                current = root.get("vars", {})
                continue
            if part == "steps":
                current = root.get("steps", {})
                continue
            current = root.get(part)
            continue
        if isinstance(current, dict):
            key = part
            idx = None
            if "[" in key:
                base, rest = key.split("[", 1)
                if base:
                    current = current.get(base)
                else:
                    rest = "[" + rest
                segments = [seg[:-1] for seg in rest.split("[") if seg]
                for segment in segments:
                    if isinstance(current, (list, tuple)):
                        current = current[int(segment)]
                    elif isinstance(current, dict):
                        current = current.get(segment)
                    else:
                        current = None
                        break
                continue
            current = current.get(key)
        elif isinstance(current, (list, tuple)):
            if part.isdigit():
                current = current[int(part)]
            else:
                raise RecipeExecutionError(f"Cannot access key '{part}' on list")
        else:
            raise RecipeExecutionError(f"Cannot access '{part}' on {type(current).__name__}")
    return current


def _evaluate_condition(result: Any, condition: Condition) -> None:
    value = _lookup_expression(condition.path, {"result": result}) if condition.path else result
    if condition.exists is not None:
        exists = value is not None
        if condition.exists != exists:
            raise RecipeExecutionError(
                f"Expected existence {condition.exists} for path '{condition.path}', got {exists}"
            )
    if condition.equals is not None and value != condition.equals:
        raise RecipeExecutionError(
            f"Expected {condition.path} == {condition.equals!r}, got {value!r}"
        )
    if condition.not_equals is not None and value == condition.not_equals:
        raise RecipeExecutionError(
            f"Expected {condition.path} != {condition.not_equals!r}, got {value!r}"
        )


def _compute_capture(result: Any, capture: Capture) -> Any:
    if capture.path is None:
        return result
    return _lookup_expression(capture.path, {"result": result})


class RecipeRunner:
    """Run recipes using the configured MCP settings."""

    def __init__(
        self,
        settings: MCPSettings,
        executor_factory: Callable[[], ToolExecutor | AsyncIterator[ToolExecutor]] | None = None,
        audit_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.executor_factory = executor_factory or (lambda: GatewayToolExecutor(settings))
        self.audit_path = audit_path or settings.state_path / "audit" / "recipes.log"

    async def run(
        self,
        recipe: Recipe,
        *,
        variables: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> RecipeRunResult:
        variables = variables or {}
        context = {
            "vars": {**recipe.variables, **variables},
            "steps": {},
            "captures": {},
        }
        started = time.time()
        step_results: list[StepResult] = []
        success = True

        if dry_run:
            logger.info("[recipe] dry-run mode enabled; steps will be skipped")
            for step in recipe.steps:
                params = _resolve_template(step.params, context)
                logger.info("[recipe] step %s -> %s params=%s", step.id, step.tool or "wait", params)
                step_results.append(
                    StepResult(step_id=step.id, status="skipped", duration_seconds=0.0, message="dry-run")
                )
            finished = time.time()
            result = RecipeRunResult(
                recipe=recipe,
                started_at=started,
                finished_at=finished,
                success=True,
                steps=step_results,
                outputs={},
            )
            self._append_audit(result, context)
            return result

        async with _executor_cm(self.executor_factory) as executor:
            for step in recipe.steps:
                logger.info("[recipe] executing step %s", step.id)
                step_start = time.time()
                try:
                    result_payload: Any
                    if step.tool:
                        params = _resolve_template(step.params, context)
                        result_payload = await executor.call(step.tool, params)
                        logger.debug("[recipe:%s] result=%s", step.id, result_payload)
                        if step.expect:
                            for path, expected in step.expect.items():
                                actual = _lookup_expression(path, {"result": result_payload})
                                expected_value = _resolve_template(expected, context)
                                if actual != expected_value:
                                    raise RecipeExecutionError(
                                        f"Expectation failed for {path}: got {actual!r}, expected {expected_value!r}"
                                    )
                        if step.asserts:
                            for cond in step.asserts:
                                _evaluate_condition({"result": result_payload}, cond)
                    elif step.wait:
                        result_payload = await self._execute_wait(executor, context, step.wait)
                    else:  # pragma: no cover - validator forbids this path
                        raise RecipeExecutionError("Invalid step configuration")

                    context["steps"][step.id] = result_payload
                    if step.capture:
                        for capture in step.capture:
                            context["captures"][capture.name] = _compute_capture(result_payload, capture)
                    duration = time.time() - step_start
                    step_results.append(
                        StepResult(step_id=step.id, status="success", duration_seconds=duration, result=result_payload)
                    )
                except Exception as exc:  # pragma: no cover - failure path
                    duration = time.time() - step_start
                    logger.error("[recipe] step %s failed: %s", step.id, exc)
                    step_results.append(
                        StepResult(
                            step_id=step.id,
                            status="error",
                            duration_seconds=duration,
                            message=str(exc),
                        )
                    )
                    success = False
                    break

        finished = time.time()
        outputs: dict[str, Any] = {}
        if success:
            for key, expr in recipe.outputs.items():
                outputs[key] = _resolve_template(expr, {
                    **context,
                    "outputs": outputs,
                })

        result = RecipeRunResult(
            recipe=recipe,
            started_at=started,
            finished_at=finished,
            success=success,
            steps=step_results,
            outputs=outputs,
        )
        self._append_audit(result, context)
        if not success:
            raise RecipeExecutionError("Recipe execution failed")
        return result

    async def _execute_wait(
        self,
        executor: ToolExecutor,
        context: dict[str, Any],
        wait: WaitConfig,
    ) -> Any:
        deadline = time.time() + wait.timeout_seconds
        attempt = 0
        params = _resolve_template(wait.params, context)
        while True:
            attempt += 1
            payload = await executor.call(wait.tool, params)
            try:
                _evaluate_condition({"result": payload}, wait.until)
                logger.info("[recipe] wait condition satisfied after %s attempts", attempt)
                return payload
            except RecipeExecutionError:
                if time.time() >= deadline:
                    raise RecipeExecutionError(
                        f"Wait condition for tool '{wait.tool}' timed out after {attempt} attempts"
                    )
                await asyncio.sleep(wait.interval_seconds)

    def _append_audit(self, result: RecipeRunResult, context: dict[str, Any]) -> None:
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "recipe": result.recipe.name,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
                "success": result.success,
                "outputs": result.outputs,
                "steps": [
                    {
                        "id": step.step_id,
                        "status": step.status,
                        "duration_seconds": step.duration_seconds,
                    }
                    for step in result.steps
                ],
                "captures": context.get("captures", {}),
            }
            with self.audit_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(record) + "\n")
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.warning("Failed to append recipe audit log: %s", exc)


@asynccontextmanager
def _executor_cm(factory: Callable[[], ToolExecutor | AsyncIterator[ToolExecutor]]) -> AsyncIterator[ToolExecutor]:
    obj = factory()
    if hasattr(obj, "__aenter__"):
        async with obj as executor:
            yield executor
    else:  # pragma: no cover - for factories returning async generators
        async with obj:  # type: ignore[misc]
            yield obj


def load_recipe(path: Path) -> Recipe:
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"Recipe file {path} does not contain a mapping")
    return Recipe.model_validate(data)


def list_recipes(recipes_dir: Path) -> list[Path]:
    return sorted(recipes_dir.glob("*.yml")) + sorted(recipes_dir.glob("*.yaml"))


__all__ = [
    "RecipeRunner",
    "RecipeRunResult",
    "RecipeExecutionError",
    "GatewayToolExecutor",
    "load_recipe",
    "list_recipes",
]
