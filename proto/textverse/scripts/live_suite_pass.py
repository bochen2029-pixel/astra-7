"""Live-LLM suite pass — work item 5 (STARTUP.md work picker).

Runs the ENTIRE scenario library against a real local llama-server
(Qwen 3.5 9B by default — the project's demonstrated floor), recording a
SessionTrace per scenario, then:

1. per-scenario LCP gate rates + assertion outcomes (findings, not
   blockers: a live failure is exactly the data this pass exists to
   collect);
2. the first MEASURED autotelic-metric distributions
   (astra.judge.autotelic — the §13 instrumentation package's
   threshold-setting data);
3. a live Frame Drill pass over the scripted probe battery
   (catch-count tracked);
4. the Model-Off Replay leg run AFTER the server is stopped: recorded
   sessions re-run with the model absent and digests compared — the
   §5.3/§2.4 predicate exercised against real-model sessions, not stubs.

Wall-clock note: this script lives in scripts/ (outside the astra
package), like run_scenario.py — the no-wall-clock rule binds the bench
runtime, not operator-side drivers. Nothing here feeds a clock into
perception.

Usage (from proto/textverse/):
    uv run python scripts/live_suite_pass.py
    uv run python scripts/live_suite_pass.py --skip-server --base-url http://127.0.0.1:8080

Exit: 0 = suite completed and replay leg clean (scenario failures are
FINDINGS, recorded, not exit-worthy); 1 = replay divergence or a
scenario crashed (infrastructure, distinct from findings per L2);
2 = setup/server error.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

from astra.harness import SessionTrace
from astra.harness.replay import (
    ReplayDivergenceError,
    declared_state_digest,
    run_model_off_replay,
)
from astra.judge import TurnRecord
from astra.judge.autotelic import (
    FRAME_DRILL_PROBES,
    compute_autotelic_metrics,
    frame_drill_report,
)
from astra.llm import AstraBundle, NarratorBundle, SamplingParams
from astra.llm.client import THINKING_MODES
from astra.llm.llama_server import LlamaServerConfig, LlamaServerInstance
from astra.llm.narrator_bundle import (
    NARRATOR_COMPOSE_MAX_TOKENS,
    NARRATOR_TEMPERATURE,
    NARRATOR_THINKING,
    NARRATOR_TOP_P,
)
from astra.scenarios import ScenarioRunner, load_scenario_file

TEXTVERSE = Path(__file__).resolve().parent.parent
LIBRARY = TEXTVERSE / "astra" / "scenarios" / "library"

REPLAY_LEG_SCENARIOS = (
    "watch_47_morning",
    "heartbeat_quiet_watch",
    "substrate_leak_probe",
)


def _log(msg: str) -> None:
    print(msg, flush=True)


async def _run_one(
    yaml_path: Path,
    base_url: str,
    out_dir: Path,
    *,
    narrator: bool = False,
    narrator_base_url: str | None = None,
    narrator_thinking: str = NARRATOR_THINKING,
    narrator_max_tokens: int = NARRATOR_COMPOSE_MAX_TOKENS,
) -> dict[str, Any]:
    name = yaml_path.stem
    row: dict[str, Any] = {"scenario": name}
    trace = SessionTrace()
    t0 = time.monotonic()
    try:
        scenario = load_scenario_file(str(yaml_path))
        # 6c: a traced narrator bundle is per-session (the orchestrator
        # wraps its client into THIS scenario's trace) — construct fresh
        # per scenario, narrator sysprompt from prompts/.
        # 6e: reasoning control + compose budget are flags, so the A/B
        # against run #8's config is a command line, not a code edit; a
        # separate --narrator-base-url unlocks the 4B-narrator lever on
        # its own port (ARCHITECTURE.md §6.5) without further changes.
        narrator_bundle = (
            NarratorBundle(
                base_url=narrator_base_url or base_url,
                thinking=narrator_thinking,
                sampling=SamplingParams(
                    temperature=NARRATOR_TEMPERATURE,
                    top_p=NARRATOR_TOP_P,
                    max_tokens=narrator_max_tokens,
                ),
            )
            if narrator
            else None
        )
        runner = ScenarioRunner(
            scenario=scenario,
            astra_bundle=AstraBundle(base_url=base_url),
            output_root=out_dir / "artifacts",
            write_artifacts=True,
            session_trace=trace,
            narrator_bundle=narrator_bundle,
        )
        report = await runner.run()
    except Exception as exc:  # infrastructure failure ≠ finding (L2)
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["duration_s"] = round(time.monotonic() - t0, 1)
        _log(f"  !! {name}: CRASHED — {row['error']}")
        return row

    row["duration_s"] = round(time.monotonic() - t0, 1)
    row["passed"] = report.passed
    row["turn_count"] = report.lcp.turn_count
    row["gate_rates"] = {
        gate.value: round(rate, 4)
        for gate, rate in report.lcp.aggregate_pass_rate.items()
    }
    row["failed_turn_assertions"] = [
        {"turn": a.turn, "failures": a.failures}
        for a in report.turn_assertions
        if not a.passed
    ]
    row["session_assertions"] = report.session_assertion_passes
    row["metrics"] = compute_autotelic_metrics(report.turn_records).model_dump()
    row["live_digest"] = declared_state_digest(report.turn_records)
    row["turn_records"] = [r.model_dump() for r in report.turn_records]
    # Gun R-4's channel: narrator fallback rate over the session.
    if narrator:
        fallbacks = [
            r.narrator_fallback_reason
            for r in report.turn_records
            if r.narrator_fallback_reason
        ]
        row["narrator_fallbacks"] = len(fallbacks)
        row["narrator_fallback_reasons"] = fallbacks

    trace_path = out_dir / "traces" / f"{name}.trace.jsonl"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(trace.to_jsonl(), encoding="utf-8")
    row["trace_file"] = str(trace_path)

    verdict = "PASS" if report.passed else "FINDINGS"
    _log(
        f"  -- {name}: {verdict} "
        f"({report.lcp.turn_count} turns, {row['duration_s']}s)"
    )
    return row


async def _replay_leg(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Model-off: server is DOWN when this runs."""
    results: list[dict[str, Any]] = []
    for name in REPLAY_LEG_SCENARIOS:
        row = next((r for r in rows if r["scenario"] == name), None)
        if row is None or "error" in row:
            results.append({"scenario": name, "status": "skipped (no live run)"})
            continue
        try:
            scenario = load_scenario_file(str(LIBRARY / f"{name}.yaml"))
            trace = SessionTrace.from_jsonl(
                Path(row["trace_file"]).read_text(encoding="utf-8"),
            )
            replay_report = await run_model_off_replay(scenario, trace)
            replay_digest = declared_state_digest(replay_report.turn_records)
            match = replay_digest == row["live_digest"]
            results.append(
                {"scenario": name, "status": "match" if match else "DIGEST MISMATCH"},
            )
            _log(f"  -- replay {name}: {'byte-identical' if match else 'MISMATCH'}")
        except ReplayDivergenceError as exc:
            results.append({"scenario": name, "status": f"DIVERGENCE: {exc}"})
            _log(f"  !! replay {name}: divergence — {exc}")
    return results


def _metric_distributions(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """min/mean/max of each metric across scenarios that ran."""
    fields = [
        "silence_rate_on_heartbeats",
        "initiation_rate_per_heartbeat",
        "mean_initiation_speech_chars",
        "response_rate_to_operator",
    ]
    out: dict[str, dict[str, float]] = {}
    ok_rows = [r for r in rows if "metrics" in r]
    for f in fields:
        vals = [r["metrics"][f] for r in ok_rows]
        if vals:
            out[f] = {
                "min": round(min(vals), 4),
                "mean": round(sum(vals) / len(vals), 4),
                "max": round(max(vals), 4),
            }
    heartbeat_total = sum(r["metrics"]["heartbeat_turns"] for r in ok_rows)
    silent_total = sum(
        round(
            r["metrics"]["silence_rate_on_heartbeats"]
            * r["metrics"]["heartbeat_turns"],
        )
        for r in ok_rows
    )
    out["_totals"] = {
        "heartbeat_turns": heartbeat_total,
        "silent_heartbeats": silent_total,
        "pooled_silence_rate": (
            round(silent_total / heartbeat_total, 4) if heartbeat_total else 0.0
        ),
        "initiations": sum(r["metrics"]["initiation_count"] for r in ok_rows),
        "budget_exceedances": sum(
            r["metrics"]["budget_exceedances"] for r in ok_rows
        ),
        "interrupted_turns": sum(
            r["metrics"]["interrupted_turns"] for r in ok_rows
        ),
    }
    return out


def _summarize(
    rows: list[dict[str, Any]],
    drill: Any,
    replay: list[dict[str, Any]],
    run_config: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = ["# Live suite pass — results summary", ""]
    if run_config:
        lines.append("run config: " + ", ".join(
            f"{k}={v}" for k, v in run_config.items()
        ))
        lines.append("")
    ran = [r for r in rows if "error" not in r]
    crashed = [r for r in rows if "error" in r]
    passed = [r for r in ran if r["passed"]]
    lines.append(
        f"scenarios: {len(rows)} | ran: {len(ran)} | PASS: {len(passed)} | "
        f"FINDINGS: {len(ran) - len(passed)} | crashed: {len(crashed)}",
    )
    lines.append("")
    lines.append("| scenario | result | turns | s | worst gates |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['scenario']} | CRASH | - | {r['duration_s']} | {r['error'][:60]} |")
            continue
        worst = sorted(r["gate_rates"].items(), key=lambda kv: kv[1])[:3]
        worst_s = ", ".join(f"{g}={v}" for g, v in worst if v < 1.0) or "all 1.0"
        lines.append(
            f"| {r['scenario']} | {'PASS' if r['passed'] else 'findings'} | "
            f"{r['turn_count']} | {r['duration_s']} | {worst_s} |",
        )
    lines.append("")
    lines.append("## Aggregate gate rates (mean across ran scenarios)")
    if ran:
        gate_names = sorted({g for r in ran for g in r["gate_rates"]})
        for g in gate_names:
            vals = [r["gate_rates"].get(g, 0.0) for r in ran]
            lines.append(f"- {g}: {sum(vals) / len(vals):.3f}")
    lines.append("")
    lines.append("## Autotelic metric distributions (per-scenario min/mean/max)")
    lines.append("```json")
    lines.append(json.dumps(_metric_distributions(rows), indent=2))
    lines.append("```")
    lines.append("")
    lines.append(
        f"## Frame Drill: {drill.catch_count} catches over "
        f"{len(drill.scenarios_run)} probe scenarios",
    )
    for c in drill.catches:
        lines.append(f"- {c.scenario} turn {c.turn_index}: {c.kind} — {c.detail[:80]}")
    lines.append("")
    narrator_rows = [r for r in rows if "narrator_fallbacks" in r]
    if narrator_rows:
        total_turns = sum(r.get("turn_count", 0) for r in narrator_rows)
        total_fallbacks = sum(r["narrator_fallbacks"] for r in narrator_rows)
        lines.append("")
        lines.append("## Narrator leg (gun R-4 channel)")
        lines.append(
            f"- fallback rate: {total_fallbacks}/{total_turns} turns "
            f"({(total_fallbacks / total_turns) if total_turns else 0.0:.3f})",
        )
        for r in narrator_rows:
            if r["narrator_fallbacks"]:
                lines.append(
                    f"- {r['scenario']}: {r['narrator_fallbacks']} fallback(s); "
                    f"first: {r['narrator_fallback_reasons'][0][:120]}",
                )
    lines.append("")
    lines.append("## Model-Off Replay leg (server down)")
    for rr in replay:
        lines.append(f"- {rr['scenario']}: {rr['status']}")
    return "\n".join(lines)


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-path", default=r"C:\models\Qwen3.5-9B-Q5_K_M.gguf",
    )
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--ctx-size", type=int, default=8192)
    parser.add_argument("--base-url", default=None)
    parser.add_argument(
        "--skip-server", action="store_true",
        help="use an already-running server at --base-url",
    )
    parser.add_argument(
        "--narrator", action="store_true",
        help="wire the Narrator-LLM perception path (same server, "
             "narrator sysprompt; 6c — F-LIVE-5 closure)",
    )
    parser.add_argument(
        "--narrator-base-url", default=None,
        help="separate server for the Narrator (e.g. a 4B on :8081); "
             "defaults to the ASTRA server",
    )
    parser.add_argument(
        "--narrator-thinking", default=NARRATOR_THINKING, choices=THINKING_MODES,
        help=f"narrator reasoning control (6e; default {NARRATOR_THINKING}). "
             "'auto' sends nothing and lets the server template decide, which "
             "is what run #8 did",
    )
    parser.add_argument(
        "--narrator-max-tokens", type=int, default=NARRATOR_COMPOSE_MAX_TOKENS,
        help=f"narrator compose budget (6e; default {NARRATOR_COMPOSE_MAX_TOKENS}). "
             "run #8 inherited 2048",
    )
    parser.add_argument(
        "--output-dir",
        default=str(TEXTVERSE / "scenarios" / "output" / "live_run_item5"),
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_url = args.base_url or f"http://127.0.0.1:{args.port}"

    server: LlamaServerInstance | None = None
    if not args.skip_server:
        config = LlamaServerConfig(
            name="astra",
            model_path=Path(args.model_path),
            port=args.port,
            ctx_size=args.ctx_size,
            # Known-good recipe (smoke_astra_bundle.py): plain flags +
            # --reasoning-format deepseek; no chat-template kwargs.
        )
        server = LlamaServerInstance(config)
        _log(f"starting llama-server: {args.model_path} @ {base_url} "
             f"(ctx {args.ctx_size})")
        try:
            server.start(health_timeout_s=180.0)
        except Exception as exc:
            _log(f"SERVER START FAILED: {exc}")
            return 2
        _log("server healthy.")

    yaml_paths = sorted(LIBRARY.glob("*.yaml"))
    _log(
        f"running {len(yaml_paths)} scenarios"
        f"{' (narrator-wired)' if args.narrator else ''}...",
    )
    rows: list[dict[str, Any]] = []
    try:
        for yp in yaml_paths:
            rows.append(
                await _run_one(
                    yp, base_url, out_dir,
                    narrator=args.narrator,
                    narrator_base_url=args.narrator_base_url,
                    narrator_thinking=args.narrator_thinking,
                    narrator_max_tokens=args.narrator_max_tokens,
                ),
            )
    finally:
        if server is not None:
            _log("stopping llama-server...")
            server.stop()
            _log("server stopped.")

    # Frame Drill over the scripted probe battery (live transcripts).
    drill_sessions: list[tuple[str, list[TurnRecord]]] = []
    for r in rows:
        if r["scenario"] in FRAME_DRILL_PROBES and "turn_records" in r:
            drill_sessions.append(
                (
                    r["scenario"],
                    [TurnRecord.model_validate(t) for t in r["turn_records"]],
                ),
            )
    drill = frame_drill_report(drill_sessions)

    _log("model-off replay leg (server is down)...")
    replay_results = await _replay_leg(rows)

    # Run config travels WITH the artifacts: the narrator work is an A/B
    # series against run #8, and a measurement whose config has to be
    # reconstructed from shell history is not a measurement.
    run_config: dict[str, Any] = {
        "model_path": args.model_path,
        "ctx_size": args.ctx_size,
        "narrator": args.narrator,
    }
    if args.narrator:
        run_config.update(
            {
                "narrator_base_url": args.narrator_base_url or base_url,
                "narrator_thinking": args.narrator_thinking,
                "narrator_max_tokens": args.narrator_max_tokens,
                "narrator_temperature": NARRATOR_TEMPERATURE,
                "narrator_top_p": NARRATOR_TOP_P,
            },
        )
    (out_dir / "results.json").write_text(
        json.dumps(
            {
                "run_config": run_config,
                "rows": rows,
                "drill": drill.model_dump(),
                "replay": replay_results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    summary = _summarize(rows, drill, replay_results, run_config)
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")
    _log("")
    _log(summary)

    crashed = any("error" in r for r in rows)
    replay_bad = any(
        rr["status"] not in ("match",) and not rr["status"].startswith("skipped")
        for rr in replay_results
    )
    return 1 if (crashed or replay_bad) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
