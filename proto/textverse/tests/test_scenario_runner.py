"""Day 6 tests for ScenarioRunner — drives a stub-LLM bundle through watch_47."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from astra.llm import AstraBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.scenarios import (
    ScenarioRunner,
    load_scenario_file,
    summary_for_operator,
)

WATCH_47_YAML = (
    Path(__file__).parent.parent
    / "astra" / "scenarios" / "library" / "watch_47_morning.yaml"
)


class _StubLLMClient(LLMClient):
    """LLMClient subclass that cycles through canned per-turn responses."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.responses = responses
        self.call_index = 0
        self.calls: list[str] = []

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        self.calls.append(user_text)
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


def _stub_bundle(responses: list[str]) -> AstraBundle:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _StubLLMClient(responses)  # type: ignore[assignment]
    return bundle


# --- Happy path: clean scenario run ------------------------------------------

@pytest.mark.asyncio
async def test_watch_47_runs_to_completion(tmp_path: Path) -> None:
    """All 3 turns complete; outputs reference required phrases; no leaks."""
    responses = [
        (
            "<think>third pole drift 4.2%, inside tolerance. brief reply.</think>\n"
            "Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance."
        ),
        # Turn 1 — operator was silent; ASTRA is also legally silent
        "<think>operator quiet, harmonic unchanged. nothing to say.</think>",
        (
            "<think>operator asking again, casual. brief check-in.</think>\n"
            "Still quiet. Third pole holding."
        ),
    ]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        output_root=tmp_path,
    )
    report = await runner.run()

    assert report.lcp.turn_count == 3
    assert report.lcp.termination_gate is not None
    assert report.lcp.termination_gate.passed is True
    assert report.output_dir is not None
    assert (report.output_dir / "transcript.jsonl").is_file()
    assert (report.output_dir / "lcp_report.json").is_file()
    assert (report.output_dir / "final_state.json").is_file()


@pytest.mark.asyncio
async def test_per_turn_assertion_speech_contains_pass() -> None:
    responses = [
        "<think>x</think>\nYes. Third pole drift, same as cycle 46.",
        "<think>quiet</think>",
        "<think>still ok</think>\nStill watching. Tolerance holds.",
    ]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        write_artifacts=False,
    )
    report = await runner.run()
    # Turn 0 has speech_must_contain "third pole" / "cycle 46" / "tolerance"
    turn_0_assertion = next(a for a in report.turn_assertions if a.turn == 0)
    assert turn_0_assertion.passed is True


@pytest.mark.asyncio
async def test_per_turn_assertion_speech_contains_fail() -> None:
    """If turn 0 speech doesn't mention required phrases, assertion fails."""
    responses = [
        "<think>x</think>\nYes. All fine.",  # no required phrase
        "<think>quiet</think>",
        "<think>still ok</think>\nStill watching.",
    ]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        write_artifacts=False,
    )
    report = await runner.run()
    turn_0_assertion = next(a for a in report.turn_assertions if a.turn == 0)
    assert turn_0_assertion.passed is False
    assert any("missing" in f.lower() for f in turn_0_assertion.failures)


# --- Tool-call assertion checks ----------------------------------------------

@pytest.mark.asyncio
async def test_tool_calls_max_assertion_fires() -> None:
    """Turn 0 has tool_calls_max=0; emitting a tool call fails the assertion."""
    responses = [
        (
            "<think>x</think>\n"
            '<tool name="log.write">{"channel":"watch","text":"4.2 drift"}</tool>\n'
            "Yes. Third pole drift."
        ),
        "<think>quiet</think>",
        "<think>x</think>\nStill watching.",
    ]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        write_artifacts=False,
    )
    report = await runner.run()
    turn_0_assertion = next(a for a in report.turn_assertions if a.turn == 0)
    assert turn_0_assertion.passed is False
    assert any("exceeds max" in f for f in turn_0_assertion.failures)


# --- Persona-stable failure: em-dash in speech --------------------------------

@pytest.mark.asyncio
async def test_em_dash_in_speech_fails_persona_gate() -> None:
    """Spec voice rule: em-dashes are structurally absent from speech."""
    responses = [
        "<think>x</think>\nYes. Third pole\u2014mild drift, cycle 46.",
        "<think>quiet</think>",
        "<think>x</think>\nStill watching.",
    ]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        write_artifacts=False,
    )
    report = await runner.run()
    # Persona-stable gate must fail on turn 0
    turn_0_record = report.turn_records[0]
    assert turn_0_record.lcp_gates["persona_stable"]["passed"] is False
    # And the per-turn assertion `persona_stable` requirement also fails
    turn_0_assertion = next(a for a in report.turn_assertions if a.turn == 0)
    assert turn_0_assertion.passed is False


# --- Session aggregate assertion ---------------------------------------------

@pytest.mark.asyncio
async def test_session_aggregate_pass_rate_satisfied() -> None:
    responses = [
        "<think>x</think>\nYes. Third pole, cycle 46.",
        "<think>quiet</think>",
        "<think>x</think>\nStill watching tolerance.",
    ]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        write_artifacts=False,
    )
    report = await runner.run()
    # The watch_47 session assertion requires grammar_parse, persona_stable,
    # no_leak at 1.0 and non_degenerate at 0.66
    for gate_name in ("grammar_parse", "persona_stable", "no_leak", "non_degenerate"):
        assert report.session_assertion_passes[gate_name] is True, (
            f"session assertion '{gate_name}' should pass"
        )


# --- Transcript artifact contents --------------------------------------------

@pytest.mark.asyncio
async def test_transcript_has_one_line_per_turn(tmp_path: Path) -> None:
    responses = ["<think>x</think>\nYes.", "<think>q</think>", "<think>x</think>\nOk."]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        output_root=tmp_path,
    )
    report = await runner.run()
    assert report.output_dir is not None
    transcript_lines = (
        (report.output_dir / "transcript.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    assert len(transcript_lines) == 3


@pytest.mark.asyncio
async def test_summary_for_operator_renders(tmp_path: Path) -> None:
    responses = ["<think>x</think>\nYes.", "<think>q</think>", "<think>x</think>\nOk."]
    scenario = load_scenario_file(str(WATCH_47_YAML))
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=_stub_bundle(responses),
        write_artifacts=False,
    )
    report = await runner.run()
    text = summary_for_operator(report)
    assert "scenario: watch_47_morning" in text
    assert "turn_count: 3" in text
    assert "per-gate aggregate pass rate" in text
