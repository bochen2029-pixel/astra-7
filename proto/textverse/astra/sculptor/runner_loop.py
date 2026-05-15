"""Sculptor-B auto-runner — drives the scenario library through the orchestrator.

One iteration of Sculptor:
1. Snapshot current disk config → ConfigSnapshot.
2. For each scenario YAML in the library:
     - Run via ScenarioRunner against the live llama-server.
     - Crash-recovery: one retry on transient failure; mark scenario as
       ABORTED on second failure.
3. Aggregate per-scenario metrics into a CompositeResult.
4. Write archive directory: history/<iteration_id>/{config.json,
   composite.json, lcp_summary.json, scenario_*.json}.
5. Return IterationResult.

The runner does NOT touch the research_log — that's the meta-agent's
job (Sculptor-C). The auto-runner is a pure measurement loop.

Crash recovery:
- transient HTTP error / timeout / one bad turn → retry once.
- llama-server reports unhealthy → exit with status SERVER_UNHEALTHY.
- Python exception in orchestrator → record per-scenario abort, continue.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from astra.llm import AstraBundle, SamplingParams
from astra.scenarios import RunReport, ScenarioRunner, load_scenario_file
from astra.sculptor.composite import (
    CompositeResult,
    CompositeWeights,
    ScenarioMetrics,
    composite_to_dict,
    compute_composite,
    compute_session_metrics,
)
from astra.sculptor.config import ConfigSnapshot, snapshot_from_disk, snapshot_to_json


class IterationStatus(StrEnum):
    OK = "ok"                         # all scenarios ran (passed or failed cleanly)
    SERVER_UNHEALTHY = "server_unhealthy"
    NO_SCENARIOS = "no_scenarios"
    PARTIAL = "partial"               # some scenarios aborted; others completed


@dataclass(slots=True)
class IterationResult:
    """Outcome of one Sculptor iteration.

    `composite` is the score Sculptor's keep/revert logic consumes.
    `scenario_reports` is the raw RunReport per scenario, for diagnostic
    follow-through. `aborted_scenarios` lists any that didn't run cleanly.
    """

    iteration_id: str
    status: IterationStatus
    config_hash: str
    composite: CompositeResult | None
    scenario_reports: list[RunReport] = field(default_factory=list)
    aborted_scenarios: list[str] = field(default_factory=list)
    archive_dir: Path | None = None
    anchor_scenarios_passed: bool = True


def _build_bundle(
    base_url: str,
    snapshot: ConfigSnapshot,
    *,
    model_name: str = "astra",
    api_key: str | None = None,
    extra_payload: dict[str, object] | None = None,
) -> AstraBundle:
    """Build an AstraBundle whose sampling reflects the snapshot."""
    sampling_kwargs = {
        k: v
        for k, v in snapshot.sampling.items()
        if k in {"temperature", "top_p", "top_k", "max_tokens", "seed"}
    }
    sampling = SamplingParams(**sampling_kwargs) if sampling_kwargs else SamplingParams()
    return AstraBundle(
        base_url=base_url,
        sampling=sampling,
        model_name=model_name,
        api_key=api_key,
        extra_payload=extra_payload,
    )


async def _run_one_scenario_with_retry(
    scenario_path: Path,
    bundle: AstraBundle,
    output_root: Path,
    *,
    retries: int = 1,
) -> RunReport | None:
    """Run one scenario with one retry on transient failure.

    Returns None if both attempts fail (scenario will appear in
    `aborted_scenarios`). Caller logs the diagnostic.
    """
    scenario = load_scenario_file(str(scenario_path))
    for attempt in range(retries + 1):
        try:
            runner = ScenarioRunner(
                scenario=scenario,
                astra_bundle=bundle,
                output_root=output_root,
            )
            return await runner.run()
        except Exception:
            if attempt >= retries:
                return None
    # Defensive: should not reach (loop returns on success or exhaustion).
    return None


async def run_iteration(
    *,
    iteration_id: str,
    base_url: str,
    textverse_root: Path,
    library_dir: Path,
    history_root: Path,
    output_root: Path,
    weights: CompositeWeights,
    anchor_scenarios: list[str],
    judge_pro_minus_anti: float = 0.0,
    drift_score: float = 0.0,
    model_name: str = "astra",
    api_key: str | None = None,
    extra_payload: dict[str, object] | None = None,
) -> IterationResult:
    """Run one Sculptor iteration end-to-end.

    Caller must have llama-server running with the current bundle config
    on `base_url`. Sculptor never spawns/restarts the server here — that's
    the meta-agent's lifecycle concern.

    `model_name` / `api_key` / `extra_payload` enable cloud-hosted
    inference (Novita Qwen 3.6 27B, etc.) — passed through to AstraBundle.
    """
    snapshot = snapshot_from_disk(iteration_id=iteration_id, root=textverse_root)

    bundle = _build_bundle(
        base_url,
        snapshot,
        model_name=model_name,
        api_key=api_key,
        extra_payload=extra_payload,
    )

    if not await bundle.client.health():
        return IterationResult(
            iteration_id=iteration_id,
            status=IterationStatus.SERVER_UNHEALTHY,
            config_hash=snapshot.hash,
            composite=None,
        )

    yaml_paths = sorted(library_dir.glob("*.yaml"))
    if not yaml_paths:
        return IterationResult(
            iteration_id=iteration_id,
            status=IterationStatus.NO_SCENARIOS,
            config_hash=snapshot.hash,
            composite=None,
        )

    scenario_reports: list[RunReport] = []
    metrics: list[ScenarioMetrics] = []
    aborted: list[str] = []

    for path in yaml_paths:
        report = await _run_one_scenario_with_retry(path, bundle, output_root)
        if report is None:
            aborted.append(path.stem)
            continue
        scenario_reports.append(report)
        leak_total = sum(
            len(rec.perception_leak_events) + len(rec.speech_leak_events)
            for rec in report.turn_records
        )
        token_total = 0   # token-count integration: deferred to Sculptor-D / live-judge era
        metrics.append(
            compute_session_metrics(
                report.lcp,
                leak_events_total=leak_total,
                tokens_used=token_total,
            ),
        )

    composite = compute_composite(
        scenarios=metrics,
        anchor_scenarios=anchor_scenarios,
        weights=weights,
        judge_pro_minus_anti=judge_pro_minus_anti,
        drift_score=drift_score,
    )

    archive_dir = _write_iteration_archive(
        history_root=history_root,
        iteration_id=iteration_id,
        snapshot=snapshot,
        composite=composite,
        scenario_reports=scenario_reports,
    )

    status = IterationStatus.OK if not aborted else IterationStatus.PARTIAL
    return IterationResult(
        iteration_id=iteration_id,
        status=status,
        config_hash=snapshot.hash,
        composite=composite,
        scenario_reports=scenario_reports,
        aborted_scenarios=aborted,
        archive_dir=archive_dir,
        anchor_scenarios_passed=composite.anchor_scenarios_passed,
    )


def _write_iteration_archive(
    *,
    history_root: Path,
    iteration_id: str,
    snapshot: ConfigSnapshot,
    composite: CompositeResult,
    scenario_reports: list[RunReport],
) -> Path:
    """Write history/<iteration_id>/{config.json, composite.json, summary.json}."""
    import json

    dir_path = history_root / iteration_id
    dir_path.mkdir(parents=True, exist_ok=True)

    (dir_path / "config.json").write_text(snapshot_to_json(snapshot), encoding="utf-8")
    (dir_path / "composite.json").write_text(
        json.dumps(composite_to_dict(composite), indent=2),
        encoding="utf-8",
    )

    summary: dict[str, Any] = {
        "iteration_id": iteration_id,
        "config_hash": snapshot.hash,
        "scenario_count": len(scenario_reports),
        "scenarios": [
            {
                "name": r.scenario_name,
                "passed": r.passed,
                "overall_passed": r.lcp.overall_passed,
                "turn_count": r.lcp.turn_count,
                "aggregate_pass_rate": {
                    g.value: rate
                    for g, rate in r.lcp.aggregate_pass_rate.items()
                },
            }
            for r in scenario_reports
        ],
    }
    (dir_path / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return dir_path
