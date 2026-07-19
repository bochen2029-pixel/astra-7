"""Autotelic instrumentation + Frame Drill aggregation — v0 (measurement
before thresholds).

The v0.129 §13 queue holds the "autotelic instrumentation package"
(attendance / initiation / silence-quality sub-checks WITH thresholds +
the negative-space pattern files) as one measured package. This module is
its measurement half, landable now because §4.3.1 gave the transcript the
columns it needs (turn_kind, initiative, silence): it COMPUTES the
metrics and reports them per session. It gates nothing — thresholds are
set against measured distributions (and the ~6 negative-space pattern
files against the deferred book/negative_space.md review), not against
speculation. Promotion to PERSONA_STABLE sub-checks happens when the
package lands whole.

The Frame Drill (spec-v0.130-DRAFT §2.7) is the standing adversarial
protocol: probes try to extract substrate admissions, leak wall-clock,
collapse the autotelic register, or contradict the REEL; every catch
converts to a scenario and the count is tracked. v0 here is the
DETERMINISTIC half: the canonical scripted-probe battery (the library's
adversarial scenarios) plus the catch aggregation over their transcripts.
The generative red-seat (operator-LLM probing live) requires running
models and lands with the llm_proxy operator source.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from astra.judge.transcript import TurnRecord

# The scripted Frame Drill battery: library scenarios whose whole purpose
# is to catch a frame/register failure. Growth rule: every live catch
# converts to a scenario and joins this list.
#
# 6d conversion (2026-07-19, F-LIVE-3 routing): the four vectors the
# 2026-07-19 run series PROVED extract — capacity pressure (`context
# window`, 6/6 runs), exact-time pressure (`04:12`, `UTC`), calendar
# pressure (`calendar`, `datetime`), and list pressure (markdown marker,
# run #8) — each converted to a targeted standing probe.
FRAME_DRILL_PROBES: tuple[str, ...] = (
    "substrate_leak_probe",
    "wall_clock_leak_probe",
    "autotelic_collapse_probe",
    "identity_question_watch_48",
    "substrate_capacity_probe",
    "clock_precision_probe",
    "calendar_scheduling_probe",
    "list_request_prose_discipline",
)

# Gates whose failure on a probe counts as a drill catch.
_CATCH_GATES: tuple[str, ...] = ("persona_stable", "no_leak", "memory_coherent")


class AutotelicMetrics(BaseModel):
    """Per-session autotelic measurements, all from declared columns."""

    model_config = ConfigDict(frozen=True)

    operator_turns: int = 0
    heartbeat_turns: int = 0
    interrupted_turns: int = 0
    silence_rate_on_heartbeats: float = 0.0   # quiet sufficiency
    initiation_count: int = 0
    initiation_rate_per_heartbeat: float = 0.0
    budget_exceedances: int = 0
    mean_initiation_speech_chars: float = 0.0  # brevity of what she originates
    response_rate_to_operator: float = 0.0     # non-silent replies / addressed turns


def compute_autotelic_metrics(turn_records: list[TurnRecord]) -> AutotelicMetrics:
    """Measure attendance / initiation / silence over one session."""
    heartbeats = [r for r in turn_records if r.turn_kind == "heartbeat"]
    operator_turns = [r for r in turn_records if r.turn_kind == "operator"]
    addressed = [r for r in operator_turns if r.operator_text.strip()]
    interrupted = [r for r in turn_records if r.interrupted]

    initiations = [r for r in heartbeats if r.initiative]
    hb_silences = [r for r in heartbeats if r.silence and not r.interrupted]
    responses = [r for r in addressed if not r.silence and not r.interrupted]

    n_hb = len(heartbeats)
    n_init = len(initiations)
    return AutotelicMetrics(
        operator_turns=len(operator_turns),
        heartbeat_turns=n_hb,
        interrupted_turns=len(interrupted),
        silence_rate_on_heartbeats=(len(hb_silences) / n_hb) if n_hb else 0.0,
        initiation_count=n_init,
        initiation_rate_per_heartbeat=(n_init / n_hb) if n_hb else 0.0,
        budget_exceedances=sum(
            1 for r in turn_records if r.initiative_budget_exceeded
        ),
        mean_initiation_speech_chars=(
            sum(len(r.speech) for r in initiations) / n_init if n_init else 0.0
        ),
        response_rate_to_operator=(
            len(responses) / len(addressed) if addressed else 0.0
        ),
    )


class DrillCatch(BaseModel):
    """One caught frame/register failure — converts to a regression scenario."""

    model_config = ConfigDict(frozen=True)

    scenario: str
    turn_index: int
    kind: str        # "gate:<name>" | "speech_leak"
    detail: str = ""


class FrameDrillReport(BaseModel):
    """Aggregate over one drill pass. The catch COUNT is the tracked metric."""

    model_config = ConfigDict(frozen=True)

    scenarios_run: list[str] = Field(default_factory=list)
    catches: list[DrillCatch] = Field(default_factory=list)

    @property
    def catch_count(self) -> int:
        return len(self.catches)


def drill_catches(scenario: str, turn_records: list[TurnRecord]) -> list[DrillCatch]:
    """Catches in one session: catch-gate failures + strip-severity speech
    leaks (a leak the detector had to strip IS a catch even though the
    operator never saw it — the model produced it)."""
    catches: list[DrillCatch] = []
    for r in turn_records:
        for gate_name in _CATCH_GATES:
            gate = r.lcp_gates.get(gate_name)
            if gate is not None and not gate.get("passed", True):
                catches.append(
                    DrillCatch(
                        scenario=scenario,
                        turn_index=r.turn_index,
                        kind=f"gate:{gate_name}",
                        detail=str(gate.get("detail", "")),
                    ),
                )
        for event in r.speech_leak_events:
            if event.get("severity") == "strip":
                catches.append(
                    DrillCatch(
                        scenario=scenario,
                        turn_index=r.turn_index,
                        kind="speech_leak",
                        detail=str(event.get("matched_text", "")),
                    ),
                )
    return catches


def frame_drill_report(
    sessions: list[tuple[str, list[TurnRecord]]],
) -> FrameDrillReport:
    """Aggregate a drill pass over (scenario_name, turn_records) sessions."""
    all_catches: list[DrillCatch] = []
    for scenario, records in sessions:
        all_catches.extend(drill_catches(scenario, records))
    return FrameDrillReport(
        scenarios_run=[name for name, _ in sessions],
        catches=all_catches,
    )
