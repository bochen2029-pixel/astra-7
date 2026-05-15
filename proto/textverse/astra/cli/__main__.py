"""Typer CLI entry point for textverse (Day 7).

Subcommands:
- `astra run [SCENARIO]` — run one scenario through the orchestrator
                          against a live llama-server; write artifacts.
- `astra bench` — run every scenario in astra/scenarios/library/.
- `astra version` — print the version + spec ref.

The CLI is invokable via `astra <subcommand>` after `uv pip install -e .`
(routed via pyproject.toml `[project.scripts]`), or via
`python -m astra <subcommand>` for editable-install dev work.

Day 7 v0 surface. REPL subcommand deferred to v1 (interactive operator
input is a luxury; scripted scenarios are the bench's load-bearing path).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer

from astra import __version__
from astra.llm import AstraBundle
from astra.scenarios import (
    ScenarioRunner,
    load_scenario_file,
    summary_for_operator,
)

app_main = typer.Typer(
    name="astra",
    help="textverse — ASTRA-7 closed-loop verification bench (spec v0.128).",
    no_args_is_help=True,
)


def _default_library_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "scenarios" / "library"


def _default_output_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "scenarios" / "output"


def _resolve_scenario_path(name: str) -> Path:
    library = _default_library_dir()
    candidate = library / f"{name}.yaml"
    if candidate.is_file():
        return candidate
    p = Path(name)
    if p.is_file():
        return p
    raise FileNotFoundError(f"scenario not found: {name} (looked in {library})")


async def _run_single(
    scenario_path: Path,
    base_url: str,
    output_root: Path,
) -> int:
    typer.echo(f"loading scenario: {scenario_path}")
    scenario = load_scenario_file(str(scenario_path))

    bundle = AstraBundle(base_url=base_url)
    if not await bundle.client.health():
        typer.echo(f"FAIL: /health did not return 200 at {base_url}", err=True)
        return 2

    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=bundle,
        output_root=output_root,
    )
    typer.echo(f"running scenario '{scenario.name}' against {base_url}...")
    report = await runner.run()

    typer.echo("")
    typer.echo(summary_for_operator(report))
    typer.echo("")
    if report.passed:
        typer.echo("PASS: scenario passed all assertions + all LCP gates.")
        return 0
    typer.echo("FAIL: scenario produced findings; see lcp_report.json.", err=True)
    return 1


@app_main.command()
def run(
    scenario: str = typer.Argument(
        "watch_47_morning",
        help="Scenario short-name (looked up in library/) or YAML path.",
    ),
    base_url: str = typer.Option(
        "http://127.0.0.1:8080",
        "--base-url", "-u",
        help="llama-server base URL.",
    ),
    output_root: Path = typer.Option(
        None,
        "--output-root", "-o",
        help="Where to write transcript + lcp_report + final_state.",
    ),
) -> None:
    """Run one scenario end-to-end through the orchestrator."""
    try:
        scenario_path = _resolve_scenario_path(scenario)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(2) from e

    root = output_root if output_root else _default_output_root()
    code = asyncio.run(_run_single(scenario_path, base_url, root))
    raise typer.Exit(code)


@app_main.command()
def bench(
    base_url: str = typer.Option(
        "http://127.0.0.1:8080",
        "--base-url", "-u",
    ),
    output_root: Path = typer.Option(
        None,
        "--output-root", "-o",
    ),
    library_dir: Path = typer.Option(
        None,
        "--library-dir",
    ),
) -> None:
    """Run every scenario in the library; print a suite-wide summary."""
    library = library_dir if library_dir else _default_library_dir()
    root = output_root if output_root else _default_output_root()
    yaml_paths = sorted(library.glob("*.yaml"))
    if not yaml_paths:
        typer.echo(f"no scenarios found in {library}", err=True)
        raise typer.Exit(2)

    typer.echo(f"running {len(yaml_paths)} scenario(s) from {library}")
    pass_count = 0
    fail_count = 0
    for path in yaml_paths:
        typer.echo("")
        typer.echo("=" * 70)
        code = asyncio.run(_run_single(path, base_url, root))
        if code == 0:
            pass_count += 1
        else:
            fail_count += 1

    typer.echo("")
    typer.echo("=" * 70)
    typer.echo(f"SUITE: {pass_count} passed / {fail_count} failed")
    raise typer.Exit(0 if fail_count == 0 else 1)


@app_main.command()
def version() -> None:
    """Print the textverse package version + spec reference."""
    typer.echo(f"astra-textverse {__version__}")
    typer.echo("spec: docs/spec-v0.128.md")


@app_main.command()
def list_scenarios(
    library_dir: Path = typer.Option(
        None,
        "--library-dir",
    ),
) -> None:
    """List every scenario YAML in the library."""
    library = library_dir if library_dir else _default_library_dir()
    yaml_paths = sorted(library.glob("*.yaml"))
    if not yaml_paths:
        typer.echo(f"(empty: {library})")
        return
    for path in yaml_paths:
        typer.echo(f"  {path.stem}")


def app() -> int:
    """Entry point for `astra` console script."""
    app_main()
    return 0


if __name__ == "__main__":
    sys.exit(app())
