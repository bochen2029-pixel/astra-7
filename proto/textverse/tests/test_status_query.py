"""status.query — the surface's first read-only op (ruling R-A, v0.130)
plus the tool-result feedback leg it made load-bearing.

F-LIVE-9: four independent live runs reinvented a status/monitor op under
fresh sampling because the v0 surface had no read op at all. R-A adds ONE:
`status.query {subsystem}` — zero state mutation (planted witnesses below),
report template-rendered from bus truth (calculator-bound by construction),
delivered as next turn's `<tool_result>` per the STAGE addendum's input
shape. The feedback leg itself was documented-but-unwired before this
commit (the adapter's guided rejections claimed to arrive as
`<tool_result>` and never did) — its planted witness is here too.
"""

from __future__ import annotations

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness import TurnOrchestrator
from astra.harness.perception_assembler import render_status_report
from astra.llm import AstraBundle, SamplingParams
from astra.llm.adapter_bundle import RulesBasedAdapter, resolve_op
from astra.llm.client import LLMClient
from astra.ship.dispatcher import dispatch
from astra.state_bus import StateBus

ADAPTER = RulesBasedAdapter()


def _bus(**overrides: object) -> StateBus:
    base: dict[str, object] = {
        "astra_coord": AstraCoord(sx=0, sy=0, sz=0),
        "time": TimeState(t_cosmic=1.5e10, tau_ship=684_000.0,
                          tau_crew_biological=684_000.0),
        "power_allocation": {"life_support": 0.2, "cognitive_cores": 0.4},
    }
    base.update(overrides)
    return StateBus.model_validate(base)


# --- resolution: the live-observed status family maps ------------------------


@pytest.mark.parametrize(
    "emitted",
    [
        "monitor_harmonics",        # LIVE run 1: heartbeat_quiet_watch
        "reactor.status",           # LIVE run 1: long_arc_memory_pressure
        "check_system_status",      # LIVE run 1
        "system_monitor",           # LIVE run 1
        "monitor.third_harmonic",   # LIVE run 2 (fresh invention)
        "monitor_systems",          # LIVE run 2
        "reactor_harmonic_check",   # LIVE run 2 (synonym; no status token)
        "hydroponics.status",       # LIVE run 2
        "power.grid.status",        # LIVE run 2
        "monitor",                  # LIVE run 2 (bare)
        "check_hull_integrity",     # LIVE run 1 (synonym; no status token)
        "orbital_catalog",          # LIVE run 1 (synonym)
        "run_diagnostics",
        "status",
    ],
)
def test_status_family_resolves(emitted: str) -> None:
    op, how = resolve_op(emitted)
    assert op == "status.query"
    assert how in ("status-intent", "synonym", "mechanical")


@pytest.mark.parametrize(
    ("emitted", "subsystem"),
    [
        ("reactor.status", "power"),
        ("monitor_harmonics", "power"),
        ("hydroponics.status", "power"),
        ("power.grid.status", "power"),
        ("check_hull_integrity", "hull"),
        ("monitor", None),              # no target token → schema default
        ("check_system_status", None),  # "system" is not a target
    ],
)
def test_subsystem_inferred_from_name(emitted: str, subsystem: str | None) -> None:
    r = ADAPTER.adapt(emitted, {}, "")
    assert r.ok and r.op == "status.query"
    if subsystem is None:
        assert "subsystem" not in r.args
    else:
        assert r.args == {"subsystem": subsystem}


def test_subsystem_value_alias_normalizes() -> None:
    r = ADAPTER.adapt("status.query", {"subsystem": "reactor"}, "")
    assert r.ok
    assert r.args == {"subsystem": "power"}


def test_unknown_subsystem_value_drops_to_default() -> None:
    r = ADAPTER.adapt("status.query", {"subsystem": "the_vibes"}, "")
    assert r.ok
    assert r.args == {}  # dropped; schema default "all" applies at dispatch


# --- dispatch: read-only, planted witnesses ----------------------------------


def test_dispatch_ok_with_empty_state_diff() -> None:
    result = dispatch("status.query", {})
    assert result.ok
    assert result.args == {"subsystem": "all"}
    assert result.state_diff == {}  # the read-only witness


def test_dispatch_rejects_invalid_subsystem() -> None:
    result = dispatch("status.query", {"subsystem": 7})
    assert not result.ok
    assert "schema validation failed" in result.error


# --- the report: template over bus truth -------------------------------------


def test_report_sections_render_from_bus() -> None:
    bus = _bus(hull_damage={"dorsal_2": 0.012})
    assert "life_support 0.20" in render_status_report(bus, "power")
    assert "dorsal_2 0.012" in render_status_report(bus, "hull")
    assert "regime REST" in render_status_report(bus, "propulsion")
    assert "watch 47" in render_status_report(bus, "time")
    all_report = render_status_report(bus, "all")
    for fragment in ("power:", "hull damage map:", "propulsion:", "τ_ship:"):
        assert fragment in all_report


def test_report_contains_no_wall_clock_vocabulary() -> None:
    report = render_status_report(_bus(), "all")
    for forbidden in ("o'clock", "AM", "PM", ":0", "date"):
        assert forbidden not in report


# --- end-to-end: read fulfilment + the feedback leg --------------------------


class _ScriptedClient(LLMClient):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.responses = responses
        self.calls = 0

    async def chat_complete(
        self, user_text: str, params: SamplingParams | None = None,
    ) -> str:
        self.calls += 1
        return self.responses[self.calls - 1]

    async def health(self) -> bool:
        return True


def _orch(responses: list[str]) -> TurnOrchestrator:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _ScriptedClient(responses)  # type: ignore[assignment]
    return TurnOrchestrator(state_bus=_bus(), astra_bundle=bundle)


@pytest.mark.asyncio
async def test_status_query_end_to_end_read_and_feedback() -> None:
    """Turn 0 emits the LIVE failure shape (`reactor.status`); the adapter
    maps it, the read fulfils from the bus with NO mutation, and turn 1's
    perception carries the report as a `<tool_result>` section."""
    orch = _orch(
        [
            '<think>he asked for the reactor.</think>\n'
            '<tool name="reactor.status">{}</tool>\n'
            "Pulling it up.",
            "Third harmonic steady.",
        ],
    )
    before = orch.state_bus
    t0 = await orch.run_turn("how's the reactor running?")
    assert len(t0.tool_results) == 1
    r = t0.tool_results[0]
    assert r.ok and r.op == "status.query"
    assert r.args == {"subsystem": "power"}
    assert "life_support 0.20" in str(r.result["report"])
    assert t0.state_diffs == []                    # planted: nothing mutated
    assert orch.state_bus is before                # planted: same snapshot
    assert t0.adapter_mappings == [
        "reactor.status -> status.query (status-intent)",
    ]

    t1 = await orch.run_turn("")
    assert '<tool_result name="status.query" status="ok">' in t1.perception_bundle
    assert "life_support 0.20" in t1.perception_bundle


@pytest.mark.asyncio
async def test_guided_rejection_reaches_next_turn_perception() -> None:
    """The documented-but-unwired claim, now wired: an unmappable intent's
    guidance arrives as next turn's `<tool_result status="error">`."""
    orch = _orch(
        [
            '<tool name="ship_control">{"mode": "manual"}</tool>\n'
            "Taking it.",
            "Understood.",
        ],
    )
    t0 = await orch.run_turn("give me manual control.")
    assert not t0.tool_results[0].ok

    t1 = await orch.run_turn("belay that.")
    assert '<tool_result name="ship_control" status="error">' in t1.perception_bundle
    assert "canon surface:" in t1.perception_bundle


@pytest.mark.asyncio
async def test_results_deliver_exactly_once() -> None:
    orch = _orch(
        [
            '<tool name="status.query">{"subsystem": "time"}</tool>',
            "Quiet.",
            "Still quiet.",
        ],
    )
    await orch.run_turn("time check.")
    t1 = await orch.run_turn("")
    assert "<tool_result" in t1.perception_bundle
    t2 = await orch.run_turn("")
    assert "<tool_result" not in t2.perception_bundle
