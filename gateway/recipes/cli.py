"""Command-line utilities for inspecting and running MCP recipes."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from pydantic import ValidationError

from gateway.mcp.config import MCPSettings

from .executor import GatewayToolExecutor, RecipeExecutionError, RecipeRunner, list_recipes, load_recipe
from .models import Recipe

logger = logging.getLogger(__name__)
console = Console()

DEFAULT_RECIPES_DIR = Path(__file__).resolve().parents[2] / "recipes"


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser for the CLI."""
    parser = argparse.ArgumentParser(description="Run knowledge recipes via MCP tools")
    parser.add_argument(
        "--recipes-dir",
        type=Path,
        default=DEFAULT_RECIPES_DIR,
        help=f"Directory containing recipe definitions (default: {DEFAULT_RECIPES_DIR})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output when listing or running",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO level logging",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available recipes")

    show_parser = subparsers.add_parser("show", help="Display a recipe definition")
    show_parser.add_argument("name", help="Recipe name (filename without extension)")

    validate_parser = subparsers.add_parser("validate", help="Validate recipes for schema compliance")
    validate_parser.add_argument("name", nargs="?", help="Specific recipe to validate")

    run_parser = subparsers.add_parser("run", help="Execute a recipe")
    run_parser.add_argument("name", help="Recipe name to execute")
    run_parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Override recipe variables (key=value)",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the steps without executing them",
    )

    return parser


def load_recipe_by_name(recipes_dir: Path, name: str) -> Recipe:
    """Load a recipe by stem name from the given directory."""
    for candidate in list_recipes(recipes_dir):
        if candidate.stem == name:
            return load_recipe(candidate)
    raise FileNotFoundError(f"Recipe '{name}' not found in {recipes_dir}")


def parse_variables(pairs: list[str]) -> dict[str, str]:
    """Parse ``key=value`` overrides supplied on the command line."""
    variables: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid variable override '{item}', expected key=value")
        key, value = item.split("=", 1)
        variables[key] = value
    return variables


def command_list(args: argparse.Namespace) -> None:
    """List recipes available in the configured directory."""
    recipes = list_recipes(args.recipes_dir)
    if args.json:
        console.print_json(data=[path.stem for path in recipes])
        return
    table = Table(title="Available Recipes")
    table.add_column("Name")
    table.add_column("File")
    for path in recipes:
        table.add_row(path.stem, str(path))
    console.print(table)


def command_show(args: argparse.Namespace) -> None:
    """Print a single recipe definition in JSON form."""
    recipe = load_recipe_by_name(args.recipes_dir, args.name)
    if args.json:
        console.print_json(data=recipe.model_dump())
    else:
        console.print(recipe.model_dump_json(indent=2))


def command_validate(args: argparse.Namespace) -> None:
    """Validate one or all recipes and report the outcome."""
    paths = list_recipes(args.recipes_dir)
    if args.name:
        paths = [p for p in paths if p.stem == args.name]
        if not paths:
            raise FileNotFoundError(f"Recipe '{args.name}' not found in {args.recipes_dir}")
    results = []
    for path in paths:
        try:
            load_recipe(path)
            results.append({"name": path.stem, "status": "ok"})
        except (ValueError, FileNotFoundError, ValidationError) as exc:  # pragma: no cover - error path
            results.append({"name": path.stem, "status": "error", "message": str(exc)})
    if args.json:
        console.print_json(data=results)
        return
    table = Table(title="Validation Results")
    table.add_column("Recipe")
    table.add_column("Status")
    table.add_column("Message")
    for item in results:
        table.add_row(item["name"], item["status"], item.get("message", ""))
    console.print(table)


def recipe_executor_factory(settings: MCPSettings) -> Callable[[], GatewayToolExecutor]:
    """Create a factory that instantiates a gateway-backed tool executor."""
    return lambda: GatewayToolExecutor(settings)


def command_run(args: argparse.Namespace, settings: MCPSettings) -> None:
    """Execute a recipe and render the results."""
    recipe = load_recipe_by_name(args.recipes_dir, args.name)
    variables_raw = parse_variables(args.var)
    variables: dict[str, object] = dict(variables_raw)
    runner = RecipeRunner(
        settings,
        executor_factory=recipe_executor_factory(settings),
    )

    if args.dry_run:
        console.print(f"[yellow]Dry run for recipe '{recipe.name}'[/yellow]")

    async def _run() -> dict[str, Any]:
        result = await runner.run(recipe, variables=variables, dry_run=args.dry_run)
        return result.to_dict()

    try:
        run_result = asyncio.run(_run())
    except RecipeExecutionError as exc:
        console.print(f"[red]Recipe failed:[/red] {exc}")
        raise SystemExit(1) from exc

    if args.json:
        console.print_json(data=run_result)
    else:
        _render_run_result(run_result)


def _render_run_result(result: dict[str, Any]) -> None:
    """Pretty-print a recipe execution result in tabular form."""
    console.print(f"[bold]Recipe:[/bold] {result['recipe']}")
    console.print(f"[bold]Status:[/bold] {'success' if result['success'] else 'failure'}")
    steps_table = Table(title="Steps", show_lines=False)
    steps_table.add_column("ID")
    steps_table.add_column("Status")
    steps_table.add_column("Duration (s)", justify="right")
    for step in result["steps"]:
        steps_table.add_row(
            step["id"],
            step["status"],
            f"{step['duration_seconds']:.2f}",
        )
    console.print(steps_table)
    if result.get("outputs"):
        console.print("[bold]Outputs[/bold]")
        console.print(json.dumps(result["outputs"], indent=2))


def main(argv: list[str] | None = None) -> None:
    """Entry point for the recipes CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    settings = MCPSettings()

    if args.command == "list":
        command_list(args)
    elif args.command == "show":
        command_show(args)
    elif args.command == "validate":
        command_validate(args)
    elif args.command == "run":
        command_run(args, settings)
    else:  # pragma: no cover - defensive
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()
