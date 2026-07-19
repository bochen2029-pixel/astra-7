"""Model-Off Replay — spec-v0.130-DRAFT §2.4/§2.5 CI leg.

The suite-level predicate: a recorded session replays byte-identically on
declared state from (scenario, trace, turn count) with every LLM absent.
The ReplayClient answers from the trace and verifies the context hash on
every call, so upstream nondeterminism surfaces at the exact turn it
appears. Includes the planted-positive witnesses (§10 positive-control
row): a tampered context hash and an exhausted trace must both raise.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from astra.harness import SessionTrace
from astra.harness.replay import (
    ReplayClient,
    ReplayDivergenceError,
    declared_state_digest,
    run_model_off_replay,
)
from astra.llm import AstraBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.scenarios import ScenarioRunner, load_scenario_file

WATCH_47_YAML = (
    Path(__file__).parent.parent
    / "astra" / "scenarios" / "library" / "watch_47_morning.yaml"
)

RESPONSES = [
    (
        "<think>third pole drift 4.2%, inside tolerance. brief reply.</think>\n"
        "Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance."
    ),
    "<think>operator quiet, harmonic unchanged. nothing to say.</think>",
    (
        "<think>operator asking again, casual. brief check-in.</think>\n"
        "Still quiet. Third pole holding."
    ),
]


class _StubLLMClient(LLMClient):
    """Deterministic stand-in for the live model during the recording run."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.responses = responses
        self.call_index = 0

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        idx = min(self.call_index, len(self.responses) - 1)
        self.call_index += 1
        return self.responses[idx]

    async def chat_stream(
        self, user_text: str, params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        if False:
            yield ""  # pragma: no cover

    async def health(self) -> bool:
        return True


def _stub_bundle() -> AstraBundle:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _StubLLMClient(RESPONSES)  # type: ignore[assignment]
    return bundle


async def _record_session() -> tuple[SessionTrace, str]:
    """Run the scenario once (recording), return (trace, declared digest)."""
    scenario = load_scenario_file(str(WATCH_47_YAML))
    trace = SessionTrace()
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(),
        write_artifacts=False,
        session_trace=trace,
    )
    report = await runner.run()
    assert report.lcp.turn_count == 3
    return trace, declared_state_digest(report.turn_records)


# --- The predicate -----------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_is_byte_identical_on_declared_state() -> None:
    scenario = load_scenario_file(str(WATCH_47_YAML))
    trace, live_digest = await _record_session()

    replay_report = await run_model_off_replay(scenario, trace)
    replay_digest = declared_state_digest(replay_report.turn_records)

    assert replay_digest == live_digest
    assert replay_report.lcp.turn_count == 3


@pytest.mark.asyncio
async def test_replay_survives_jsonl_persistence() -> None:
    """The on-disk trace alone suffices: serialize, deserialize, replay."""
    scenario = load_scenario_file(str(WATCH_47_YAML))
    trace, live_digest = await _record_session()

    rehydrated = SessionTrace.from_jsonl(trace.to_jsonl())
    assert [r.model_dump() for r in rehydrated.records] == [
        r.model_dump() for r in trace.records
    ]

    replay_report = await run_model_off_replay(scenario, rehydrated)
    assert declared_state_digest(replay_report.turn_records) == live_digest


@pytest.mark.asyncio
async def test_trace_columns_are_receipted() -> None:
    """Operator inputs and utterances land in the trace with receipts."""
    trace, _ = await _record_session()

    ops = trace.operator_inputs()
    utts = trace.utterances("astra")
    assert len(ops) == 3
    assert len(utts) == 3
    assert ops[0].payload == "hey. you still watching that reactor thing?"
    for u in utts:
        assert u.payload  # verbatim raw output
        assert len(u.context_sha256) == 64
        assert u.model_id  # client model_name receipted
        assert len(u.params_fingerprint) == 64


# --- Planted-positive witnesses (§10 positive-control row) -------------------


@pytest.mark.asyncio
async def test_replay_detects_tampered_context() -> None:
    """A single flipped context hash must raise at the exact utterance."""
    scenario = load_scenario_file(str(WATCH_47_YAML))
    trace, _ = await _record_session()

    tampered_records = []
    for r in trace.records:
        if r.kind == "llm_utterance" and r.turn_index == 1:
            r = r.model_copy(update={"context_sha256": "0" * 64})
        tampered_records.append(r)
    tampered = SessionTrace(tampered_records)

    with pytest.raises(ReplayDivergenceError, match="context divergence"):
        await run_model_off_replay(scenario, tampered)


@pytest.mark.asyncio
async def test_replay_detects_exhausted_trace() -> None:
    scenario = load_scenario_file(str(WATCH_47_YAML))
    trace, _ = await _record_session()

    truncated = SessionTrace(
        [r for r in trace.records if not (r.kind == "llm_utterance" and r.turn_index == 2)],
    )
    with pytest.raises(ReplayDivergenceError, match="trace exhausted"):
        await run_model_off_replay(scenario, truncated)


def test_replay_client_is_model_off() -> None:
    """The replay client's transport surface is a sentinel; no network path."""
    client = ReplayClient([])
    assert client.base_url.startswith("replay://")
