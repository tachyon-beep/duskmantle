from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class Condition(BaseModel):
    """Assertion condition evaluated against a step result."""

    path: str = Field(description="Dot path into the result payload")
    equals: Any | None = None
    not_equals: Any | None = None
    exists: bool | None = None


class Capture(BaseModel):
    """Capture part of a step result into the execution context."""

    name: str
    path: str | None = None


class WaitConfig(BaseModel):
    """Poll a tool until a condition is satisfied."""

    tool: str = Field(description="Tool to invoke while waiting")
    params: Dict[str, Any] = Field(default_factory=dict)
    until: Condition = Field(description="Condition that terminates the wait")
    interval_seconds: float = Field(default=5.0, ge=0.5, description="Polling interval")
    timeout_seconds: float = Field(default=300.0, ge=1.0, description="Timeout before failing")


class RecipeStep(BaseModel):
    """Single step inside a recipe."""

    id: str
    description: str | None = None
    tool: str | None = None
    params: Dict[str, Any] = Field(default_factory=dict)
    expect: Dict[str, Any] | None = None
    asserts: List[Condition] | None = Field(default=None, alias="assert")
    capture: List[Capture] | None = None
    wait: WaitConfig | None = None
    prompt: str | None = None

    @model_validator(mode="after")
    def validate_mode(self) -> "RecipeStep":
        if self.tool is None and self.wait is None:
            raise ValueError("Step must define either 'tool' or 'wait'")
        if self.tool is not None and self.wait is not None:
            raise ValueError("Step cannot define both 'tool' and 'wait'")
        return self


class Recipe(BaseModel):
    """Top level recipe definition."""

    version: int = Field(1, description="Schema version")
    name: str
    summary: str | None = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    steps: List[RecipeStep]
    outputs: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ensure_unique_step_ids(self) -> "Recipe":
        seen: set[str] = set()
        for step in self.steps:
            if step.id in seen:
                raise ValueError(f"Duplicate step id '{step.id}' in recipe '{self.name}'")
            seen.add(step.id)
        return self


RecipeDict = Dict[str, Any]
