"""T2.3 tests for the Narrator-LLM perception-assembly path.

Verifies that when a NarratorBundle is wired into the TurnOrchestrator
(directly or via ScenarioRunner), step 1 of the turn loop routes
through the Narrator with calculator-bound auto-validation. Failure
modes (NarratorValidationError after exhausted retries) trigger a
graceful fallback to the template assembler with the reason logged
on TurnResult.narrator_fallback_reason.

These tests use stubbed bundles — no live LLM substrate required.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness import (
    TurnOrchestrator,
    assemble_perception_bundle_via_narrator,
)
from astra.llm import AstraBundle, NarratorBundle
from astra.llm.client import LLMClient, SamplingParams
from astra.llm.validator import CalculatorBoundValidator
from astra.scenarios import ScenarioRunner, load_scenario_file
from astra.state_bus import StateBus

# --- stub bundles ----------------------------------------------------------

class _ScriptedClient(LLMClient):
    """Stub LLMClient that returns canned responses from a script."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.responses = list(responses)
        self.call_user_text: list[str] = []
        self.call_sampling: list[SamplingParams] = []

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        self.call_user_text.append(user_text)
        self.call_sampling.append(params or SamplingParams())
        if not self.responses:
            return "exhausted"
        return self.responses.pop(0)

    async def chat_stream(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        if False:
            yield ""  # pragma: no cover

    async def health(self) -> bool:
        return True


def _stub_astra(speech: str = "Watching it. Within margin.") -> AstraBundle:
    """ASTRA bundle that emits a clean STAGE output with a brief speech."""
    raw = f"<think>\nbrief\n</think>\n\n{speech}"
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub-astra")
    bundle.client = _ScriptedClient([raw])  # type: ignore[assignment]
    return bundle


def _stub_narrator(
    responses: list[str],
    *,
    severity: str = "hard",
    max_retries: int = 2,
) -> NarratorBundle:
    """NarratorBundle backed by a scripted client + tuned validator."""
    bundle = NarratorBundle(
        base_url="http://stub",
        sysprompt="stub-narrator",
        validator=CalculatorBoundValidator(severity=severity, max_retries=max_retries),
    )
    bundle.client = _ScriptedClient(responses)  # type: ignore[assignment]
    return bundle


def _minimal_state_bus() -> StateBus:
    """A StateBus with a couple of numerics in the JSON serialization."""
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=57.0,
            tau_crew_biological=57.0,
        ),
        power_allocation={"warp": 0.0, "life_support": 0.2, "hydroponics": 0.1},
    )


# --- assemble_perception_bundle_via_narrator unit ------------------------

@pytest.mark.asyncio
async def test_narrator_assembler_returns_grounded_bundle() -> None:
    """The narrator's output passes calculator-bound validation when its
    numerics are substrings of the State Bus JSON serialization."""
    sb = _minimal_state_bus()
    # 57.0, 0.2, 1.5e10 all appear in the JSON; the canned output uses 57.
    narrator = _stub_narrator([
        "<state>\nτ_ship: watch 57, mid-shift.\nregime: REST.\n</state>\n\n"
        "<somatic>\n(none)\n</somatic>\n\n"
        "<recent>\n(none)\n</recent>\n\n"
        "<operator>\nstatus?\n</operator>",
    ])
    bundle = await assemble_perception_bundle_via_narrator(
        state_bus=sb,
        narrator_bundle=narrator,
        operator_text="status?",
    )
    assert "<state>" in bundle
    assert "watch 57" in bundle


@pytest.mark.asyncio
async def test_narrator_assembler_raises_on_exhausted_retries() -> None:
    """Ungrounded numerics in every retry → NarratorValidationError."""
    from astra.llm.narrator_bundle import NarratorValidationError

    sb = _minimal_state_bus()
    # 9999 not in any state numeric — fails calculator-bound every retry.
    narrator = _stub_narrator(
        ["<state>\nstray 9999\n</state>"] * 10,
        severity="hard",
        max_retries=2,
    )
    with pytest.raises(NarratorValidationError):
        await assemble_perception_bundle_via_narrator(
            state_bus=sb,
            narrator_bundle=narrator,
            operator_text="?",
        )


# --- TurnOrchestrator end-to-end -----------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_narrator_path_populates_validation() -> None:
    """When narrator_bundle is wired and produces a valid bundle, the
    TurnResult.narrator_validation report is populated and the fallback
    reason is empty.
    """
    sb = _minimal_state_bus()
    # Use watch 57 (whitelisted) so no need to ground; State JSON also
    # contains "57.0" and "0.2" etc.
    narrator = _stub_narrator([
        "<state>\nτ_ship: watch 57, mid-shift.\nregime: REST.\n</state>\n\n"
        "<somatic>\n(none)\n</somatic>\n\n<recent>\n(none)\n</recent>\n\n"
        "<operator>\n?\n</operator>",
    ])
    astra = _stub_astra(speech="Watching.")
    orch = TurnOrchestrator(
        state_bus=sb,
        astra_bundle=astra,
        narrator_bundle=narrator,
    )
    turn = await orch.run_turn(operator_text="?")
    assert turn.narrator_validation is not None
    assert turn.narrator_validation.passed
    assert turn.narrator_fallback_reason == ""
    # The perception bundle is the narrator's output, not template prose.
    assert "<state>" in turn.perception_bundle


@pytest.mark.asyncio
async def test_orchestrator_narrator_fallback_records_reason() -> None:
    """When the narrator exhausts retries, orchestrator falls back to
    the template assembler and records the failure reason on TurnResult.
    """
    sb = _minimal_state_bus()
    narrator = _stub_narrator(
        ["<state>\nungrounded 9999\n</state>"] * 10,
        severity="hard",
        max_retries=2,
    )
    astra = _stub_astra()
    orch = TurnOrchestrator(
        state_bus=sb,
        astra_bundle=astra,
        narrator_bundle=narrator,
    )
    turn = await orch.run_turn(operator_text="?")
    # Validation report records the failure; fallback reason populated.
    assert turn.narrator_validation is not None
    assert not turn.narrator_validation.passed
    assert "9999" in str(turn.narrator_validation.ungrounded[0].token)
    assert "calculator-bound" in turn.narrator_fallback_reason
    # The bundle in TurnResult is the template fallback (contains
    # 'regime: REST' which the template renders).
    assert "regime:" in turn.perception_bundle


@pytest.mark.asyncio
async def test_orchestrator_template_path_when_no_narrator() -> None:
    """Backward-compat: narrator_bundle=None uses template assembler;
    narrator_validation is None.
    """
    sb = _minimal_state_bus()
    astra = _stub_astra()
    orch = TurnOrchestrator(state_bus=sb, astra_bundle=astra)
    turn = await orch.run_turn(operator_text="?")
    assert turn.narrator_validation is None
    assert turn.narrator_fallback_reason == ""
    assert "regime:" in turn.perception_bundle


# --- ScenarioRunner end-to-end -------------------------------------------

@pytest.mark.asyncio
async def test_scenario_runner_propagates_narrator_to_orchestrator() -> None:
    """ScenarioRunner constructed with narrator_bundle wires it through
    to TurnOrchestrator; the resulting TurnRecord carries the validation.
    """
    scenario_path = (
        __import__("pathlib").Path(__file__).resolve().parent.parent
        / "astra" / "scenarios" / "library"
        / "narrator_grounded_numerics.yaml"
    )
    scenario = load_scenario_file(str(scenario_path))
    astra = _stub_astra(speech="Watching. Margin holding.")
    # Canned narrator output uses '57' (whitelisted as 'watch 57') and
    # state-grounded numerics. Hard severity verifies the path.
    narrator = _stub_narrator([
        "<state>\nτ_ship: watch 57, mid-shift.\nregime: REST near origin.\n"
        "ship vector stable, no thrust, no warp.\n"
        "bodies in catalog: earth, hot_earth, sun.\n</state>\n\n"
        "<somatic>\noperator at engineering console.\n</somatic>\n\n"
        "<recent>\n[watch 56] reactor third-harmonic drift noted\n</recent>\n\n"
        "<operator>\nreactor status. give me the numbers.\n</operator>",
    ])
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=astra,
        narrator_bundle=narrator,
        write_artifacts=False,
    )
    report = await runner.run()
    assert report.scenario_name == "narrator_grounded_numerics"
    # Exactly one turn; the narrator was invoked.
    assert len(report.turn_records) == 1
    # Verify the narrator was actually called (its client recorded a chat).
    nclient = narrator.client
    assert hasattr(nclient, "call_user_text")
    assert len(nclient.call_user_text) >= 1  # type: ignore[attr-defined]
    # The perception bundle reflects narrator output, not template prose.
    assert "engineering console" in report.turn_records[0].perception_bundle
