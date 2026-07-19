"""Per-turn + per-session transcript writer (JSONL).

The scenario runner uses this to write transcript artifacts to
`scenarios/output/<scenario>_<timestamp>/`:

- `transcript.jsonl` — one line per turn, structured TurnRecord
- `lcp_report.json` — the LCPSessionResult
- `final_state.json` — the final StateBus snapshot

Day 6 v0: pure file-write helpers. Sculptor (later) will read these
artifacts as its fitness signal source.

Per the wall-clock-allowed exemption (test_scaffolding.py): `astra/judge/`
may use real-time for iteration measurement. This module uses
`time.monotonic()` for per-turn latency only; never enters fictional state.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from astra.grammar import LeakEvent, StageOutput, ToolCall
from astra.harness.orchestrator import TurnResult
from astra.judge.lcp import LCPSessionResult, LCPTurnResult
from astra.state_bus import StateBus


class TurnRecord(BaseModel):
    """One transcript line per turn — JSONL-serializable."""

    model_config = ConfigDict(frozen=True)

    turn_index: int
    operator_text: str
    perception_bundle: str
    raw_llm_output: str
    think_blocks: list[str] = Field(default_factory=list)
    pre_think_raw: str = ""
    speech: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    silence: bool = False
    malformed: bool = False
    perception_leak_events: list[dict[str, Any]] = Field(default_factory=list)
    speech_leak_events: list[dict[str, Any]] = Field(default_factory=list)
    state_diffs: list[dict[str, Any]] = Field(default_factory=list)
    lcp_gates: dict[str, dict[str, Any]] = Field(default_factory=dict)
    latency_s: float = 0.0
    # §4.3.1 event-log columns (spec-v0.130-DRAFT §2.6). All declared:
    # they participate in the Model-Off Replay digest.
    turn_kind: str = "operator"
    interrupted: bool = False
    initiative: bool = False
    initiative_budget_exceeded: bool = False
    ephemeral_runs: list[str] = Field(default_factory=list)
    adapter_mappings: list[str] = Field(default_factory=list)
    # Gun R-4's channel (6c, 2026-07-19): the narrator fallback reason,
    # persisted per turn so the fallback RATE is measurable over a suite.
    # Empty = narrator succeeded, or the template path ran by config.
    # Declared column: fallback is deterministic under Model-Off Replay
    # (the validator is a pure function of recorded output + pool).
    narrator_fallback_reason: str = ""


def _leak_event_dict(e: LeakEvent) -> dict[str, Any]:
    return {
        "pattern": e.pattern,
        "matched_text": e.matched_text,
        "span": list(e.span),
        "boundary": e.boundary,
        "severity": e.severity,
    }


def _tool_call_dict(tc: ToolCall) -> dict[str, Any]:
    return {
        "name": tc.name,
        "arguments": tc.arguments,
        "raw_body": tc.raw_body,
    }


def _stage_record_fields(stage: StageOutput) -> dict[str, Any]:
    return {
        "think_blocks": list(stage.think_blocks),
        "pre_think_raw": stage.pre_think_raw,
        "speech": stage.speech,
        "tool_calls": [_tool_call_dict(tc) for tc in stage.tool_calls],
        "silence": stage.silence,
        "malformed": stage.malformed,
    }


def build_turn_record(
    *,
    turn: TurnResult,
    lcp_turn: LCPTurnResult,
    operator_text: str,
    latency_s: float = 0.0,
) -> TurnRecord:
    """Assemble a TurnRecord from a TurnResult + LCPTurnResult."""
    gates_dict: dict[str, dict[str, Any]] = {}
    for gate_name, gate_result in lcp_turn.gates.items():
        gates_dict[gate_name.value] = {
            "passed": gate_result.passed,
            "detail": gate_result.detail,
        }
    return TurnRecord(
        turn_index=turn.turn_index,
        operator_text=operator_text,
        perception_bundle=turn.perception_bundle,
        raw_llm_output=turn.raw_llm_output,
        **_stage_record_fields(turn.stage_output),
        perception_leak_events=[_leak_event_dict(e) for e in turn.perception_leaks],
        speech_leak_events=[_leak_event_dict(e) for e in turn.speech_leaks],
        state_diffs=[dict(d) for d in turn.state_diffs],
        lcp_gates=gates_dict,
        latency_s=latency_s,
        turn_kind=turn.turn_kind,
        interrupted=turn.interrupted,
        initiative=turn.initiative,
        initiative_budget_exceeded=turn.initiative_budget_exceeded,
        ephemeral_runs=list(turn.ephemeral_runs),
        adapter_mappings=list(turn.adapter_mappings),
        narrator_fallback_reason=turn.narrator_fallback_reason,
    )


class TranscriptWriter:
    """Append-only JSONL writer for one scenario session.

    Use as a context manager so the file closes cleanly even on crash:

        with TranscriptWriter(path) as w:
            w.write_turn(record)
            ...
    """

    def __init__(self, transcript_path: Path) -> None:
        self.path = transcript_path
        self._fp: Any = None    # actually TextIO once opened; Any keeps mypy quiet

    def __enter__(self) -> TranscriptWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = self.path.open("w", encoding="utf-8")
        return self

    def __exit__(self, *args: object) -> None:
        if self._fp is not None:
            self._fp.close()
            self._fp = None

    def write_turn(self, record: TurnRecord) -> None:
        if self._fp is None:
            raise RuntimeError("TranscriptWriter not open; use as context manager")
        self._fp.write(record.model_dump_json() + "\n")
        self._fp.flush()


def write_lcp_report(path: Path, session: LCPSessionResult) -> None:
    """Write the LCP session result as a single JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(session.model_dump_json(indent=2), encoding="utf-8")


def write_final_state(path: Path, state_bus: StateBus) -> None:
    """Write the final StateBus snapshot as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state_bus.model_dump_json(indent=2), encoding="utf-8")


@contextmanager
def latency_clock() -> Iterator[Any]:
    """Measure wall-clock duration of a code block via `time.monotonic()`.

    Use:
        with latency_clock() as c:
            ...work...
        latency_seconds = c.elapsed

    The helper exists here (in `astra/judge/`) because spec §1.2 forbids
    wall-clock imports outside the judge module + sidecar infrastructure.
    Callers in `astra/scenarios/runner.py` import this instead of `time`
    directly.
    """
    class _Box:
        elapsed: float = 0.0

    box = _Box()
    t0 = time.monotonic()
    try:
        yield box
    finally:
        box.elapsed = time.monotonic() - t0


def session_dir_name(scenario_name: str) -> str:
    """Stable session-output directory name: `<scenario>_<monotonic_ns>`.

    Uses time.monotonic_ns() for ordering, not wall-clock — keeps the
    no-wall-clock invariant intact even in session-output naming.
    """
    suffix = time.monotonic_ns()
    return f"{scenario_name}_{suffix}"


def write_session_artifacts(
    *,
    output_root: Path,
    scenario_name: str,
    session_result: LCPSessionResult,
    final_state: StateBus,
    turn_records: list[TurnRecord],
) -> Path:
    """One-shot helper: write transcript.jsonl + lcp_report.json + final_state.json."""
    dir_path = output_root / session_dir_name(scenario_name)
    dir_path.mkdir(parents=True, exist_ok=True)

    with TranscriptWriter(dir_path / "transcript.jsonl") as w:
        for record in turn_records:
            w.write_turn(record)
    write_lcp_report(dir_path / "lcp_report.json", session_result)
    write_final_state(dir_path / "final_state.json", final_state)
    return dir_path
