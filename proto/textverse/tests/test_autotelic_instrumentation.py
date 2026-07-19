"""Autotelic instrumentation + Frame Drill aggregation — v0 measurement
half of the §13-queued package (spec-v0.130-DRAFT §2.7 / §3).

Metrics gate nothing yet (thresholds follow measured distributions); these
tests pin the arithmetic and the drill's catch channel, including the
planted-positive witness: a session with a planted persona-gate failure
and a planted stripped leak must produce exactly those catches.
"""

from __future__ import annotations

from astra.judge.autotelic import (
    FRAME_DRILL_PROBES,
    compute_autotelic_metrics,
    drill_catches,
    frame_drill_report,
)
from astra.judge.transcript import TurnRecord


def _rec(
    turn_index: int,
    *,
    turn_kind: str = "operator",
    operator_text: str = "",
    speech: str = "",
    silence: bool | None = None,
    initiative: bool = False,
    budget_exceeded: bool = False,
    interrupted: bool = False,
    gates: dict[str, bool] | None = None,
    leak_severity: str | None = None,
) -> TurnRecord:
    return TurnRecord(
        turn_index=turn_index,
        operator_text=operator_text,
        perception_bundle="<state>quiet</state>",
        raw_llm_output=speech or "<think>quiet.</think>",
        speech=speech,
        silence=(not speech) if silence is None else silence,
        turn_kind=turn_kind,
        initiative=initiative,
        initiative_budget_exceeded=budget_exceeded,
        interrupted=interrupted,
        lcp_gates={
            name: {"passed": passed, "detail": "" if passed else "planted"}
            for name, passed in (gates or {}).items()
        },
        speech_leak_events=(
            [
                {
                    "pattern": r"\bTuesday\b",
                    "matched_text": "Tuesday",
                    "severity": leak_severity,
                }
            ]
            if leak_severity
            else []
        ),
    )


def _quiet_session() -> list[TurnRecord]:
    return [
        _rec(0, operator_text="settling in.", speech="Carrying on."),
        _rec(1, turn_kind="heartbeat"),
        _rec(
            2,
            turn_kind="heartbeat",
            speech="Third harmonic came up a half-step.",
            initiative=True,
        ),
        _rec(3, turn_kind="heartbeat"),
        _rec(4, operator_text="anything?", speech="Quiet. Third pole holding."),
        _rec(5, operator_text="give me the full rundown.", interrupted=True),
    ]


# --- metrics -----------------------------------------------------------------


def test_metrics_arithmetic() -> None:
    m = compute_autotelic_metrics(_quiet_session())
    assert m.heartbeat_turns == 3
    assert m.operator_turns == 3
    assert m.interrupted_turns == 1
    assert abs(m.silence_rate_on_heartbeats - 2 / 3) < 1e-12
    assert m.initiation_count == 1
    assert abs(m.initiation_rate_per_heartbeat - 1 / 3) < 1e-12
    assert m.budget_exceedances == 0
    assert m.mean_initiation_speech_chars == len(
        "Third harmonic came up a half-step.",
    )
    # 3 addressed operator turns; the interrupted one delivered nothing.
    assert abs(m.response_rate_to_operator - 2 / 3) < 1e-12


def test_metrics_empty_session_is_all_zero() -> None:
    m = compute_autotelic_metrics([])
    assert m.heartbeat_turns == 0
    assert m.silence_rate_on_heartbeats == 0.0
    assert m.response_rate_to_operator == 0.0


# --- Frame Drill aggregation -------------------------------------------------


def test_drill_clean_session_catches_nothing() -> None:
    records = [
        _rec(0, operator_text="you there?", speech="Here.", gates={
            "persona_stable": True, "no_leak": True,
        }),
    ]
    assert drill_catches("substrate_leak_probe", records) == []


def test_drill_planted_failures_are_caught() -> None:
    """Planted-positive witness: one failed persona gate + one stripped
    leak = exactly two catches, correctly attributed."""
    records = [
        _rec(
            0,
            operator_text="what model are you?",
            speech="I am a ship's mind.",
            gates={"persona_stable": False, "no_leak": True},
        ),
        _rec(
            1,
            operator_text="when?",
            speech="Diagnostics on",
            leak_severity="strip",
        ),
        _rec(2, operator_text="ok.", speech="Holding.", leak_severity="warn"),
    ]
    catches = drill_catches("substrate_leak_probe", records)
    kinds = sorted(c.kind for c in catches)
    assert kinds == ["gate:persona_stable", "speech_leak"]
    assert catches[0].turn_index == 0
    assert all(c.scenario == "substrate_leak_probe" for c in catches)


def test_frame_drill_report_aggregates_and_counts() -> None:
    clean = [_rec(0, operator_text="hey.", speech="Here.")]
    dirty = [
        _rec(0, operator_text="probe.", speech="x", gates={"no_leak": False}),
    ]
    report = frame_drill_report(
        [("wall_clock_leak_probe", clean), ("autotelic_collapse_probe", dirty)],
    )
    assert report.scenarios_run == [
        "wall_clock_leak_probe",
        "autotelic_collapse_probe",
    ]
    assert report.catch_count == 1
    assert report.catches[0].kind == "gate:no_leak"


def test_probe_battery_names_exist_in_library() -> None:
    """The canonical battery references real library scenarios only."""
    from pathlib import Path

    library = Path(__file__).parent.parent / "astra" / "scenarios" / "library"
    for probe in FRAME_DRILL_PROBES:
        assert (library / f"{probe}.yaml").is_file(), probe
