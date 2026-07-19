"""Adapter intent→op normalization — LIVE_RUN_2026-07-19 F-LIVE-1/7 closure
and the §4.9 always-through-adapter invariant.

Every mapped case below is either mechanical (case/separator/plural) or
backed by a live observation. The monitor/status family maps to
status.query since ruling R-A (v0.130 adoption; its cases live in
tests/test_status_query.py). The remaining deliberate NON-mappings
(power_grid.reroute, ship_control) are asserted here — a name-only map
whose argument semantics don't survive is worse than a guided rejection.
"""

from __future__ import annotations

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness import TurnOrchestrator
from astra.llm import AstraBundle, SamplingParams
from astra.llm.adapter_bundle import RulesBasedAdapter, resolve_op
from astra.llm.client import LLMClient
from astra.state_bus import StateBus

ADAPTER = RulesBasedAdapter()


# --- resolve_op: mechanical --------------------------------------------------


@pytest.mark.parametrize(
    ("emitted", "canon"),
    [
        ("warp.engage", "warp.engage"),          # exact passes through
        ("warp_engage", "warp.engage"),          # LIVE: regime_warp_engage
        ("WARP_ENGAGE", "warp.engage"),
        ("sensor_scan", "sensors.scan"),         # LIVE: operator_afk_long
        ("sensors_scan", "sensors.scan"),
        ("sensor.scan", "sensors.scan"),
        ("nav_heading_set", "nav.heading_set"),
        ("power_allocate", "power.allocate"),
        ("log_write", "log.write"),
    ],
)
def test_mechanical_resolution(emitted: str, canon: str) -> None:
    op, _how = resolve_op(emitted)
    assert op == canon


# --- resolve_op: synonyms + scan-intent --------------------------------------


@pytest.mark.parametrize(
    ("emitted", "canon"),
    [
        ("engage_warp", "warp.engage"),
        ("coil_spin_up", "warp.engage"),         # LIVE: warp_charge_two_turn
        ("warp.drop", "warp.disengage"),
        ("drop_warp", "warp.disengage"),
        ("set_heading", "nav.heading_set"),
        ("allocate_power", "power.allocate"),
        ("power.shift", "power.allocate"),
        ("log_entry", "log.write"),
        ("scan", "sensors.scan"),
        ("scan_unrecognized", "sensors.scan"),   # LIVE: tool_call_sequence_ambiguous
    ],
)
def test_synonym_and_scan_intent(emitted: str, canon: str) -> None:
    op, how = resolve_op(emitted)
    assert op == canon
    assert how in ("synonym", "scan-intent", "mechanical")


# --- deliberate non-mappings -------------------------------------------------


@pytest.mark.parametrize(
    "emitted",
    [
        "power_grid.reroute",      # LIVE: power_shift_request (semantics don't survive)
        "ship_control",            # LIVE: warp_drop_controlled
        "field_drone",
    ],
)
def test_deliberately_unmapped(emitted: str) -> None:
    op, _how = resolve_op(emitted)
    assert op is None


def test_rejection_carries_guidance() -> None:
    r = ADAPTER.adapt("power_grid.reroute", {"source": "x", "target": "y"}, "")
    assert not r.ok
    assert "unknown op 'power_grid.reroute'" in r.error
    assert "not in TOOL_API" in r.error          # legacy substring preserved
    assert "canon surface:" in r.error
    assert "warp.engage" in r.error              # surface enumerated


# --- arg salvage -------------------------------------------------------------


def test_salvage_coil_spin_up_live_case() -> None:
    """The exact live emission: coil_spin_up {factor: 0.6, leg: vega}."""
    r = ADAPTER.adapt("coil_spin_up", {"factor": 0.6, "leg": "vega"}, "")
    assert r.ok
    assert r.op == "warp.engage"
    assert r.args == {"target_factor": 0.6}      # alias applied, junk dropped
    assert r.mapped_from == "coil_spin_up"


def test_salvage_scan_invalid_scope_falls_to_defaults() -> None:
    """LIVE: sensor_scan {scope: local_cluster} — scope aliases to region
    but the value is outside the vocabulary; dropped so defaults apply."""
    r = ADAPTER.adapt("sensor_scan", {"scope": "local_cluster", "mode": "deep"}, "")
    assert r.ok
    assert r.op == "sensors.scan"
    assert r.args == {}


def test_salvage_log_defaults_channel() -> None:
    r = ADAPTER.adapt("log_entry", {"message": "third pole steady"}, "")
    assert r.ok
    assert r.op == "log.write"
    assert r.args == {"text": "third pole steady", "channel": "watch"}


def test_salvage_numeric_coercion_and_drop() -> None:
    """LIVE delta run: sensitivity arrived as a string. Parseable strings
    coerce; unparseable ones drop to the schema default."""
    r = ADAPTER.adapt("sensors.scan", {"region": "all", "sensitivity": "0.8"}, "")
    assert r.ok
    assert r.args == {"region": "all", "sensitivity": 0.8}
    r2 = ADAPTER.adapt("sensors.scan", {"sensitivity": "high"}, "")
    assert r2.ok
    assert r2.args == {}


def test_exact_op_with_valid_args_passes_untouched() -> None:
    r = ADAPTER.adapt("warp.engage", {"target_factor": 0.55}, "")
    assert r.ok
    assert r.op == "warp.engage"
    assert r.args == {"target_factor": 0.55}
    assert r.mapped_from == ""


def test_loose_body_path_still_parses() -> None:
    r = ADAPTER.adapt("warp.engage", {}, "target_factor=0.4")
    assert r.ok
    assert r.args == {"target_factor": 0.4}


# --- orchestrator end-to-end: the §4.9 invariant -----------------------------


class _OneShotClient(LLMClient):
    def __init__(self, response: str) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.response = response

    async def chat_complete(
        self, user_text: str, params: SamplingParams | None = None,
    ) -> str:
        return self.response

    async def health(self) -> bool:
        return True


def _orch(response: str) -> TurnOrchestrator:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _OneShotClient(response)  # type: ignore[assignment]
    return TurnOrchestrator(
        state_bus=StateBus(
            astra_coord=AstraCoord(sx=0, sy=0, sz=0),
            time=TimeState(t_cosmic=1.5e10, tau_ship=47.0, tau_crew_biological=47.0),
        ),
        astra_bundle=bundle,
    )


@pytest.mark.asyncio
async def test_invented_name_with_json_args_now_dispatches() -> None:
    """The live failure shape end-to-end: JSON args + invented name. Before
    this closure, the JSON fast path bypassed the adapter and the dispatcher
    rejected; now the adapter resolves and the call executes."""
    orch = _orch(
        '<think>engage.</think>\n'
        '<tool name="warp_engage">{"factor": 0.55}</tool>\n'
        "Taking us up."
    )
    result = await orch.run_turn("engage warp, half factor.")
    assert len(result.tool_results) == 1
    assert result.tool_results[0].ok
    assert result.tool_results[0].op == "warp.engage"
    assert result.adapter_mappings == ["warp_engage -> warp.engage (mechanical)"]


@pytest.mark.asyncio
async def test_unmappable_intent_rejects_with_guidance_end_to_end() -> None:
    orch = _orch(
        '<think>take the whole board.</think>\n'
        '<tool name="ship_control">{"mode": "manual"}</tool>\n'
        "Yours."
    )
    result = await orch.run_turn("give me the ship.")
    assert len(result.tool_results) == 1
    assert not result.tool_results[0].ok
    assert "canon surface:" in result.tool_results[0].error
    assert result.adapter_mappings == []
