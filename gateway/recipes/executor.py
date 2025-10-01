"""Recipe execution layer for automating MCP-driven workflows."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType

import yaml

from gateway.mcp.backup import trigger_backup
from gateway.mcp.client import GatewayClient
from gateway.mcp.config import MCPSettings
from gateway.mcp.exceptions import GatewayRequestError
from gateway.mcp.ingest import latest_ingest_status, trigger_ingest

from .models import Capture, Condition, Recipe, WaitConfig

logger = logging.getLogger(__name__)


class RecipeExecutionError(RuntimeError):
    """Raised when a recipe step fails."""


@dataclass
class StepResult:
    """Lightweight representation of a single recipe step outcome."""

    step_id: str
    status: str
    duration_seconds: float
    result: object | None = None
    message: str | None = None


@dataclass
class RecipeRunResult:
    """Aggregate outcome for a recipe execution, including captured outputs."""

    recipe: Recipe
    started_at: float
    finished_at: float
    success: bool
    steps: list[StepResult] = field(default_factory=list)
    outputs: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise the run result to a JSON-friendly mapping."""
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

    async def call(self, tool: str, params: dict[str, object]) -> object:  # pragma: no cover - interface
        """Invoke a named tool with the given parameters."""
        raise NotImplementedError

    async def __aenter__(self) -> ToolExecutor:  # pragma: no cover - interface
        """Allow derived executors to perform async setup."""
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:  # pragma: no cover - interface
        """Allow derived executors to perform async teardown."""
        return None


class GatewayToolExecutor(ToolExecutor):
    """Execute tools by reusing gateway HTTP/MCP helpers."""

    def __init__(self, settings: MCPSettings) -> None:
        self.settings = settings
        self._client_manager: GatewayClient | None = None
        self._client: GatewayClient | None = None

    async def __aenter__(self) -> GatewayToolExecutor:
        """Open the shared gateway client for tool execution."""
        self._client_manager = GatewayClient(self.settings)
        self._client = await self._client_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        """Close the shared gateway client when execution completes."""
        if self._client_manager is not None:
            await self._client_manager.__aexit__(exc_type, exc, tb)
        self._client = None
        self._client_manager = None

    async def call(self, tool: str, params: dict[str, object]) -> object:
        """Route tool invocations to the appropriate gateway operation."""
        if self._client is None:
            raise RuntimeError("Gateway client not initialised")
        client = self._client

        if tool == "km-search":
            return await client.search(params)
        if tool == "km-graph-subsystem":
            name = _require_str(params, "name")
            depth = _coerce_positive_int(params.get("depth"), default=1)
            include_artifacts = _coerce_bool(params.get("include_artifacts"), default=True)
            if include_artifacts is None:
                include_artifacts = True
            cursor = _coerce_optional_str(params.get("cursor"))
            limit = _coerce_positive_int(params.get("limit"), default=25)
            return await client.graph_subsystem(
                name,
                depth=depth,
                include_artifacts=include_artifacts,
                cursor=cursor,
                limit=limit,
            )
        if tool == "km-graph-node":
            node_id = _require_str(params, "node_id")
            relationships = _coerce_optional_str(params.get("relationships")) or "outgoing"
            limit = _coerce_positive_int(params.get("limit"), default=50)
            return await client.graph_node(
                node_id,
                relationships=relationships,
                limit=limit,
            )
        if tool == "km-graph-search":
            term = _coerce_optional_str(params.get("term")) or ""
            limit = _coerce_positive_int(params.get("limit"), default=20)
            return await client.graph_search(term, limit=limit)
        if tool == "km-coverage-summary":
            return await client.coverage_summary()
        if tool == "km-lifecycle-report":
            return await client.lifecycle_report()
        if tool == "km-ingest-status":
            limit = _coerce_positive_int(params.get("limit"), default=10)
            history = await client.audit_history(limit=limit)
            profile = _coerce_optional_str(params.get("profile"))
            record = await latest_ingest_status(history=history, profile=profile)
            if record is None:
                return {"status": "not_found", "profile": profile}
            return {"status": "ok", "run": record}
        if tool == "km-ingest-trigger":
            profile = _coerce_optional_str(params.get("profile")) or self.settings.ingest_profile_default
            dry_run = _coerce_bool(params.get("dry_run"), default=False)
            if dry_run is None:
                dry_run = False
            use_dummy = _coerce_bool(params.get("use_dummy_embeddings"))
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
            limit = _coerce_positive_int(params.get("limit"), default=20)
            return await client.audit_history(limit=limit)

        raise RecipeExecutionError(f"Unsupported tool '{tool}' in recipe")


def _resolve_template(value: object, context: Mapping[str, object]) -> object:
    if isinstance(value, str):
        if value.startswith("${") and value.endswith("}") and value.count("${") == 1:
            expr = value[2:-1].strip()
            return _lookup_expression(expr, context)

        def replace(match: re.Match[str]) -> str:
            expr_inner = match.group(1)
            resolved = _lookup_expression(expr_inner.strip(), context)
            return str(resolved)

        if "${" in value:
            return re.sub(r"\$\{([^}]+)\}", replace, value)
    if isinstance(value, list):
        return [_resolve_template(item, context) for item in value]
    if isinstance(value, dict):
        return {k: _resolve_template(v, context) for k, v in value.items()}
    return value


def _lookup_expression(expr: str, context: Mapping[str, object]) -> object:
    vars_section = context.get("vars")
    if isinstance(vars_section, Mapping) and expr in vars_section:
        return vars_section[expr]
    direct = context.get(expr)
    if direct is not None:
        return direct

    parts = expr.split(".")
    current: object | None = context
    for part in parts:
        if current is None:
            break
        if part == "vars" and isinstance(current, Mapping):
            current = current.get("vars")
            continue
        if part == "steps" and isinstance(current, Mapping):
            current = current.get("steps")
            continue
        if part == "captures" and isinstance(current, Mapping):
            current = current.get("captures")
            continue
        current = _descend(current, part)

    if current is None and isinstance(context.get("result"), Mapping):
        result_section = context.get("result")
        if isinstance(result_section, Mapping):
            current = result_section.get(expr)
    if current is None:
        raise RecipeExecutionError(f"Unable to resolve expression '{expr}'")
    return current


def _descend(current: object, part: str) -> object:
    if isinstance(current, Mapping):
        key = part
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
                elif isinstance(current, Mapping):
                    current = current.get(segment)
                else:
                    current = None
                    break
            return current
        return current.get(key)
    if isinstance(current, (list, tuple)):
        if part.isdigit():
            return current[int(part)]
        raise RecipeExecutionError(f"Cannot access key '{part}' on list")
    return None


def _evaluate_condition(result: object, condition: Condition) -> None:
    value = _lookup_expression(condition.path, {"result": result}) if condition.path else result
    if condition.exists is not None:
        exists = value is not None
        if condition.exists != exists:
            raise RecipeExecutionError(f"Expected existence {condition.exists} for path '{condition.path}', got {exists}")
    if condition.equals is not None and value != condition.equals:
        raise RecipeExecutionError(f"Expected {condition.path} == {condition.equals!r}, got {value!r}")
    if condition.not_equals is not None and value == condition.not_equals:
        raise RecipeExecutionError(f"Expected {condition.path} != {condition.not_equals!r}, got {value!r}")


def _compute_capture(result: object, capture: Capture) -> object:
    if capture.path is None:
        return result
    return _lookup_expression(capture.path, {"result": result})


class RecipeRunner:
    """Run recipes using the configured MCP settings."""

    def __init__(
        self,
        settings: MCPSettings,
        executor_factory: Callable[[], ToolExecutor] | None = None,
        audit_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.executor_factory = executor_factory or (lambda: GatewayToolExecutor(settings))
        self.audit_path = audit_path or settings.state_path / "audit" / "recipes.log"

    def make_executor(self) -> ToolExecutor:
        """Instantiate a tool executor using the configured factory."""
        return self.executor_factory()

    async def run(
        self,
        recipe: Recipe,
        *,
        variables: dict[str, object] | None = None,
        dry_run: bool = False,
    ) -> RecipeRunResult:
        """Execute a recipe end-to-end and return the collected results."""
        variables = variables or {}
        vars_store: dict[str, object] = {**recipe.variables, **variables}
        steps_store: dict[str, object] = {}
        captures_store: dict[str, object] = {}
        context: dict[str, object] = {
            "vars": vars_store,
            "steps": steps_store,
            "captures": captures_store,
        }
        started = time.time()
        step_results: list[StepResult] = []
        success = True

        if dry_run:
            logger.info("[recipe] dry-run mode enabled; steps will be skipped")
            for step in recipe.steps:
                params = _resolve_template(step.params, context)
                logger.info("[recipe] step %s -> %s params=%s", step.id, step.tool or "wait", params)
                step_results.append(StepResult(step_id=step.id, status="skipped", duration_seconds=0.0, message="dry-run"))
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
                    result_payload: object
                    if step.tool:
                        params_obj = _resolve_template(step.params, context)
                        params = _ensure_object_map(params_obj, step.id)
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
                                _evaluate_condition(result_payload, cond)
                    elif step.wait:
                        result_payload = await self._execute_wait(executor, context, step.wait)
                    else:  # pragma: no cover - validator forbids this path
                        raise RecipeExecutionError("Invalid step configuration")

                    steps_store[step.id] = result_payload
                    if step.capture:
                        for capture in step.capture:
                            captures_store[capture.name] = _compute_capture(result_payload, capture)
                    duration = time.time() - step_start
                    step_results.append(StepResult(step_id=step.id, status="success", duration_seconds=duration, result=result_payload))
                except RecipeExecutionError as exc:  # pragma: no cover - failure path
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
                except (
                    GatewayRequestError,
                    ValueError,
                    KeyError,
                    RuntimeError,
                    asyncio.TimeoutError,
                ) as exc:  # pragma: no cover - failure path
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
        outputs: dict[str, object] = {}
        if success:
            for key, expr in recipe.outputs.items():
                outputs[key] = _resolve_template(
                    expr,
                    {
                        **context,
                        "outputs": outputs,
                    },
                )

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
        context: dict[str, object],
        wait: WaitConfig,
    ) -> object:
        """Repeatedly invoke a wait tool until the condition passes or times out."""
        deadline = time.time() + wait.timeout_seconds
        attempt = 0
        params_obj = _resolve_template(wait.params, context)
        params = _ensure_object_map(params_obj, wait.tool)
        while True:
            attempt += 1
            payload = await executor.call(wait.tool, params)
            try:
                _evaluate_condition(payload, wait.until)
                logger.info("[recipe] wait condition satisfied after %s attempts", attempt)
                return payload
            except RecipeExecutionError:
                if time.time() >= deadline:
                    raise RecipeExecutionError(f"Wait condition for tool '{wait.tool}' timed out after {attempt} attempts") from None
                await asyncio.sleep(wait.interval_seconds)

    def _append_audit(self, result: RecipeRunResult, context: dict[str, object]) -> None:
        """Append the recipe outcome to the on-disk audit log."""
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
        except (OSError, RuntimeError, TypeError, ValueError) as exc:  # pragma: no cover - best effort logging
            logger.warning("Failed to append recipe audit log: %s", exc)


@asynccontextmanager
async def _executor_cm(factory: Callable[[], ToolExecutor]) -> AsyncIterator[ToolExecutor]:
    """Context manager that yields a tool executor from the provided factory."""
    executor = factory()
    async with executor as exec_instance:
        yield exec_instance


def load_recipe(path: Path) -> Recipe:
    """Load a recipe file from disk and validate the schema."""
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"Recipe file {path} does not contain a mapping")
    return Recipe.model_validate(data)


def _ensure_object_map(value: object, label: str) -> dict[str, object]:
    """Ensure template resolution returned a mapping, raising otherwise."""
    if isinstance(value, dict):
        return {str(key): val for key, val in value.items()}
    raise RecipeExecutionError(f"Resolved parameters for '{label}' must be a mapping; got {type(value).__name__}")


def _require_str(params: Mapping[str, object], key: str) -> str:
    """Fetch a required string parameter from a mapping of arguments."""
    candidate = params.get(key)
    result = _coerce_optional_str(candidate)
    if result is None or not result:
        raise RecipeExecutionError(f"Parameter '{key}' is required and must be a string")
    return result


def _coerce_optional_str(value: object | None) -> str | None:
    """Convert optional string-like values to trimmed strings."""
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return None


def _coerce_positive_int(value: object | None, *, default: int) -> int:
    """Convert inputs to a positive integer, falling back to the default."""
    numeric = _coerce_int(value)
    if numeric is None:
        return max(1, default)
    return max(1, numeric)


def _coerce_int(value: object | None) -> int | None:
    """Coerce common primitive values to an integer when possible."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _coerce_bool(value: object | None, *, default: bool | None = None) -> bool | None:
    """Interpret truthy/falsey string values and return a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return default


def list_recipes(recipes_dir: Path) -> list[Path]:
    """Return all recipe definition files within the directory."""
    return sorted(recipes_dir.glob("*.yml")) + sorted(recipes_dir.glob("*.yaml"))


__all__ = [
    "RecipeRunner",
    "RecipeRunResult",
    "RecipeExecutionError",
    "GatewayToolExecutor",
    "load_recipe",
    "list_recipes",
]
