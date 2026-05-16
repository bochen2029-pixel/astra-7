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
from astra.sculptor import (
    HypothesisGenerator,
    LLMHypothesisGenerator,
    MetaAgent,
    StubHypothesisGenerator,
    build_default_dual_judge,
    read_entries,
    seed_day0_baseline,
)
from astra.sculptor.convergence import convergence_one_line

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


def _build_extra_payload(thinking: str) -> dict[str, object] | None:
    """Translate --thinking flag to chat_template_kwargs payload.

    - "auto": do not send chat_template_kwargs (let the server decide).
    - "on" / "off": send {"chat_template_kwargs": {"enable_thinking": bool}}
      at the JSON top level (Novita + llama-server both accept this shape).
    """
    if thinking == "auto":
        return None
    if thinking == "on":
        return {"chat_template_kwargs": {"enable_thinking": True}}
    if thinking == "off":
        return {"chat_template_kwargs": {"enable_thinking": False}}
    raise typer.BadParameter(
        f"--thinking must be one of: auto / on / off (got: {thinking!r})",
    )


async def _run_single(
    scenario_path: Path,
    base_url: str,
    output_root: Path,
    *,
    model_name: str = "astra",
    api_key: str | None = None,
    extra_payload: dict[str, object] | None = None,
) -> int:
    typer.echo(f"loading scenario: {scenario_path}")
    scenario = load_scenario_file(str(scenario_path))

    bundle = AstraBundle(
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        extra_payload=extra_payload,
    )
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
        help="OpenAI-compat endpoint base URL (llama-server local or cloud).",
    ),
    model_name: str = typer.Option(
        "astra",
        "--model-name", "-m",
        help="Model name in the chat completions payload (e.g. qwen/qwen3.6-27b for Novita).",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="NOVITA_API_KEY",
        help="API key for cloud endpoints. Default reads env NOVITA_API_KEY; absent = no auth header.",
    ),
    thinking: str = typer.Option(
        "auto",
        "--thinking",
        help="enable_thinking chat-template flag: 'auto' (don't send) / 'on' / 'off'.",
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

    extra_payload = _build_extra_payload(thinking)
    root = output_root if output_root else _default_output_root()
    code = asyncio.run(
        _run_single(
            scenario_path,
            base_url,
            root,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        ),
    )
    raise typer.Exit(code)


@app_main.command()
def bench(
    base_url: str = typer.Option(
        "http://127.0.0.1:8080",
        "--base-url", "-u",
    ),
    model_name: str = typer.Option(
        "astra",
        "--model-name", "-m",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="NOVITA_API_KEY",
    ),
    thinking: str = typer.Option(
        "auto",
        "--thinking",
        help="enable_thinking chat-template flag: 'auto' (don't send) / 'on' / 'off'.",
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

    extra_payload = _build_extra_payload(thinking)
    typer.echo(f"running {len(yaml_paths)} scenario(s) from {library}")
    pass_count = 0
    fail_count = 0
    for path in yaml_paths:
        typer.echo("")
        typer.echo("=" * 70)
        code = asyncio.run(
            _run_single(
                path,
                base_url,
                root,
                model_name=model_name,
                api_key=api_key,
                extra_payload=extra_payload,
            ),
        )
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


@app_main.command()
def sculptor_run(
    base_url: str = typer.Option(
        "http://127.0.0.1:8080",
        "--base-url", "-u",
    ),
    model_name: str = typer.Option(
        "astra",
        "--model-name", "-m",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="NOVITA_API_KEY",
    ),
    thinking: str = typer.Option(
        "auto",
        "--thinking",
        help="enable_thinking chat-template flag: 'auto' (don't send) / 'on' / 'off'.",
    ),
    max_iterations: int = typer.Option(
        200,
        "--max-iterations", "-N",
        help="Stop after N iterations regardless of convergence.",
    ),
    n_runs: int = typer.Option(
        3,
        "--n-runs",
        help="Sub-runs per iteration for composite averaging (N=3 default).",
    ),
    with_judge: bool = typer.Option(
        False,
        "--with-judge/--no-judge",
        help="Wire the dual-judge into the composite. Requires running llama-server.",
    ),
    seed_day0: bool = typer.Option(
        True,
        "--seed-day0/--no-seed-day0",
        help="Seed Day-0 baseline findings to research_log before iterating.",
    ),
    hypothesizer: str = typer.Option(
        "stub",
        "--hypothesizer",
        help="Hypothesis source: 'stub' (deterministic 30-entry bank) or 'llm' (LLMHypothesisGenerator).",
    ),
    hypothesizer_base_url: str | None = typer.Option(
        None,
        "--hypothesizer-base-url",
        help="When --hypothesizer=llm, OpenAI-compat endpoint for the hypothesizer LLM (default: same as --base-url).",
    ),
    hypothesizer_model_name: str | None = typer.Option(
        None,
        "--hypothesizer-model-name",
        help="When --hypothesizer=llm, model name (default: same as --model-name).",
    ),
    hypothesizer_api_key: str | None = typer.Option(
        None,
        "--hypothesizer-api-key",
        envvar="HYPOTHESIZER_API_KEY",
        help="When --hypothesizer=llm, API key (default: same as --api-key; env HYPOTHESIZER_API_KEY).",
    ),
    hypothesizer_thinking: str | None = typer.Option(
        None,
        "--hypothesizer-thinking",
        help="When --hypothesizer=llm, enable_thinking flag for the hypothesizer (default: same as --thinking).",
    ),
) -> None:
    """Run the Sculptor meta-agent loop until convergence / halt / budget."""
    textverse_root = Path(__file__).resolve().parent.parent.parent
    extra_payload = _build_extra_payload(thinking)

    if seed_day0:
        wrote = seed_day0_baseline(textverse_root)
        if wrote:
            typer.echo(f"seeded {wrote} Day-0 baseline findings to research_log")

    dual_judge = None
    if with_judge:
        dual_judge = build_default_dual_judge(
            judge_prompt_path=textverse_root / "tuning" / "judge_prompt.md",
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        typer.echo("dual-judge wired (pro + anti, both on same endpoint)")

    hypothesis_generator: HypothesisGenerator
    if hypothesizer == "llm":
        h_base_url = hypothesizer_base_url or base_url
        h_model_name = hypothesizer_model_name or model_name
        h_api_key = hypothesizer_api_key if hypothesizer_api_key is not None else api_key
        h_thinking = hypothesizer_thinking if hypothesizer_thinking is not None else thinking
        h_extra_payload = _build_extra_payload(h_thinking)
        hypothesis_generator = LLMHypothesisGenerator.from_local_qwen(
            base_url=h_base_url,
            model_name=h_model_name,
            api_key=h_api_key,
            extra_payload=h_extra_payload,
        )
        typer.echo(
            f"LLM hypothesizer wired (base_url={h_base_url}, model={h_model_name}, "
            f"thinking={h_thinking})",
        )
    elif hypothesizer == "stub":
        hypothesis_generator = StubHypothesisGenerator()
    else:
        raise typer.BadParameter(
            f"--hypothesizer must be 'stub' or 'llm' (got: {hypothesizer!r})",
        )

    agent = MetaAgent(
        textverse_root=textverse_root,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        extra_payload=extra_payload,
        n_runs_per_iteration=n_runs,
        dual_judge=dual_judge,
        hypothesis_generator=hypothesis_generator,
    )

    typer.echo(f"Sculptor starting; max_iterations={max_iterations}, n_runs={n_runs}")

    async def _run() -> None:
        final = await agent.run_until_done(max_iterations=max_iterations)
        typer.echo("")
        typer.echo(f"Sculptor stopped. Final entry: {final.decision} @ iter {final.iteration}")
        report = agent.convergence_status()
        typer.echo(convergence_one_line(report))

    asyncio.run(_run())


@app_main.command()
def sculptor_status() -> None:
    """Print the latest research-log entry + a convergence one-liner."""
    textverse_root = Path(__file__).resolve().parent.parent.parent
    log_path = textverse_root / "tuning" / "research_log.jsonl"
    entries = read_entries(log_path)
    if not entries:
        typer.echo("(no Sculptor activity yet)")
        return
    latest = entries[-1]
    typer.echo(f"latest: iter {latest.iteration} | {latest.decision}")
    if latest.hypothesis:
        typer.echo(f"hypothesis: {latest.hypothesis[:200]}")
    if latest.composite_score is not None:
        typer.echo(f"composite: {latest.composite_score:.4f}")
    if latest.rationale:
        typer.echo(f"rationale: {latest.rationale[:200]}")

    from astra.sculptor.composite import load_weights
    from astra.sculptor.convergence import check_convergence
    weights = load_weights(textverse_root / "tuning" / "weights.json")
    report = check_convergence(
        entries=entries,
        library_dir=textverse_root / "astra" / "scenarios" / "library",
        weights=weights,
    )
    typer.echo("")
    typer.echo(convergence_one_line(report))


@app_main.command()
def sculptor_halt() -> None:
    """Touch tuning/halt.flag. Sculptor will stop at next iteration boundary."""
    textverse_root = Path(__file__).resolve().parent.parent.parent
    halt = textverse_root / "tuning" / "halt.flag"
    halt.parent.mkdir(parents=True, exist_ok=True)
    halt.write_text("halt\n", encoding="utf-8")
    typer.echo(f"wrote {halt}")


@app_main.command()
def sculptor_pause() -> None:
    """Touch tuning/pause.flag. Sculptor will pause at next iteration boundary."""
    textverse_root = Path(__file__).resolve().parent.parent.parent
    pause = textverse_root / "tuning" / "pause.flag"
    pause.parent.mkdir(parents=True, exist_ok=True)
    pause.write_text("pause\n", encoding="utf-8")
    typer.echo(f"wrote {pause}")


@app_main.command()
def sculptor_resume() -> None:
    """Remove tuning/pause.flag if present."""
    textverse_root = Path(__file__).resolve().parent.parent.parent
    pause = textverse_root / "tuning" / "pause.flag"
    if pause.is_file():
        pause.unlink()
        typer.echo(f"removed {pause}")
    else:
        typer.echo("(no pause.flag present)")


def app() -> int:
    """Entry point for `astra` console script."""
    app_main()
    return 0


if __name__ == "__main__":
    sys.exit(app())
