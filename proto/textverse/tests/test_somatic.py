"""Somatic Aggregator tests — v0.129 TENTATIVE §6.3.1 implemented as residue.

Covers:
1. SomaticSignal validation (magnitude bounds).
2. aggregate(): determinism, salience filtering, magnitude ordering, top-3
   cap, ≤2 lines, sentence termination, empty/quiet → empty banner.
3. Emitters: power pressure, warp phases, cryosleep, hull stress, chaos
   field, quiet baseline — each from a real StateBus snapshot.
4. Sensor-grounded discipline: no phenomenal vocabulary in any emitted label
   across a grid of ship states ("sensor-grounded, not phenomenal claim").
5. Perception assembler integration: somatic_signals takes precedence over
   somatic_note; explicit empty list renders an empty somatic section; the
   legacy note path is unchanged.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from astra.core.astra_coord import AstraCoord
from astra.core.time_state import TimeState
from astra.harness.perception_assembler import assemble_perception_bundle
from astra.harness.somatic import (
    MAX_BANNER_SIGNALS,
    SomaticSignal,
    aggregate,
    emit_somatic_signals,
)
from astra.state_bus import ChaosFieldSummary, StateBus, WarpState


def make_bus(
    *,
    warp: WarpState | None = None,
    cryosleep: bool = False,
    power: dict[str, float] | None = None,
    hull: dict[str, float] | None = None,
    chaos_max: float = 0.0,
) -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(t_cosmic=100.0, tau_ship=90.0, tau_crew_biological=88.0),
        warp=warp,
        cryosleep_active=cryosleep,
        power_allocation=power or {},
        hull_damage=hull or {},
        chaos_field_summary=ChaosFieldSummary(
            mean_amplitude=chaos_max * 0.5,
            max_amplitude=chaos_max,
            energy_density=chaos_max * 0.2,
        ),
    )


def sig(label: str, mag: float, *, salient: bool = True, source: str = "power") -> SomaticSignal:
    return SomaticSignal(source=source, label=label, magnitude=mag, salient=salient)


# --- SomaticSignal validation ----------------------------------------------------


def test_magnitude_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        SomaticSignal(source="power", label="x", magnitude=1.2)
    with pytest.raises(ValidationError):
        SomaticSignal(source="power", label="x", magnitude=-0.1)


# --- aggregate() -------------------------------------------------------------------


def test_empty_input_empty_banner() -> None:
    assert aggregate([]) == ""


def test_non_salient_signals_stay_silent() -> None:
    assert aggregate([sig("power steady", 0.4, salient=False)]) == ""


def test_single_salient_signal_one_line() -> None:
    banner = aggregate([sig("power margin thin", 0.95)])
    assert banner == "Power margin thin." or banner == "power margin thin."
    assert "\n" not in banner


def test_strongest_signal_takes_first_line() -> None:
    banner = aggregate(
        [
            sig("coils taking charge", 0.6, source="warp"),
            sig("power margin thin", 0.95, source="power"),
        ]
    )
    lines = banner.split("\n")
    assert len(lines) == 2
    assert "power margin thin" in lines[0]
    assert "coils taking charge" in lines[1]


def test_cap_at_three_signals_two_lines() -> None:
    signals = [sig(f"signal {i}", 0.1 * (i + 1)) for i in range(6)]
    banner = aggregate(signals)
    assert banner.count("\n") == 1                 # exactly two lines
    assert banner.count(".") == MAX_BANNER_SIGNALS  # one sentence per signal
    assert "signal 5" in banner                     # strongest survived
    assert "signal 0" not in banner                 # weakest dropped


def test_aggregate_deterministic() -> None:
    signals = [
        sig("b-signal", 0.5, source="hull"),
        sig("a-signal", 0.5, source="chaos"),
        sig("top", 0.9, source="warp"),
    ]
    assert aggregate(signals) == aggregate(list(signals))


def test_labels_get_sentence_termination() -> None:
    banner = aggregate([sig("hull stress at dorsal-7", 0.8)])
    assert banner.endswith(".")


# --- Emitters -----------------------------------------------------------------------


def test_power_pressure_salient() -> None:
    bus = make_bus(power={"warp": 0.5, "life_support": 0.3, "cognitive_cores": 0.15})
    signals = emit_somatic_signals(bus)
    power = [s for s in signals if s.source == "power"]
    assert len(power) == 1
    assert power[0].salient is True
    assert "thin" in power[0].label


def test_power_steady_not_salient() -> None:
    bus = make_bus(power={"life_support": 0.3})
    power = [s for s in emit_somatic_signals(bus) if s.source == "power"]
    assert power[0].salient is False


def test_warp_charging_signal() -> None:
    bus = make_bus(warp=WarpState(W=0.2, phase="charging", charge_progress=0.6))
    warp = [s for s in emit_somatic_signals(bus) if s.source == "warp"]
    assert warp[0].salient is True
    assert warp[0].magnitude == 0.6
    assert "charge" in warp[0].label


def test_warp_cruise_high_w_salient() -> None:
    bus = make_bus(warp=WarpState(W=0.9, phase="cruising"))
    warp = [s for s in emit_somatic_signals(bus) if s.source == "warp"]
    assert warp[0].salient is True
    assert "harmonic" in warp[0].label


def test_warp_cruise_low_w_not_salient() -> None:
    bus = make_bus(warp=WarpState(W=0.3, phase="cruising"))
    warp = [s for s in emit_somatic_signals(bus) if s.source == "warp"]
    assert warp[0].salient is False


def test_cryosleep_signal() -> None:
    bus = make_bus(cryosleep=True)
    cryo = [s for s in emit_somatic_signals(bus) if s.source == "cryosleep"]
    assert cryo[0].salient is True
    assert "pod sealed" in cryo[0].label


def test_hull_stress_reports_worst_section() -> None:
    bus = make_bus(hull={"dorsal-7": 0.6, "ventral-2": 0.1})
    hull = [s for s in emit_somatic_signals(bus) if s.source == "hull"]
    assert hull[0].salient is True
    assert "dorsal-7" in hull[0].label


def test_chaos_unquiet_when_high() -> None:
    bus = make_bus(chaos_max=0.8)
    chaos = [s for s in emit_somatic_signals(bus) if s.source == "chaos"]
    assert chaos[0].salient is True
    assert "unquiet" in chaos[0].label


def test_quiet_baseline_when_nothing_to_report() -> None:
    bus = make_bus()
    signals = emit_somatic_signals(bus)
    assert len(signals) == 1
    assert signals[0].source == "hardware"
    assert signals[0].salient is False
    assert aggregate(signals) == ""   # quiet body, empty banner


# --- Sensor-grounded discipline -----------------------------------------------------


PHENOMENAL_TERMS = ("i feel", "feels", "pain", "hurt", "afraid", "scared", "happy")


def test_no_phenomenal_claims_in_any_label() -> None:
    grid = [
        make_bus(),
        make_bus(warp=WarpState(W=0.95, phase="cruising"), power={"warp": 0.99}),
        make_bus(warp=WarpState(W=0.4, phase="charging", charge_progress=0.9)),
        make_bus(warp=WarpState(W=0.5, phase="dropping")),
        make_bus(cryosleep=True, chaos_max=0.9),
        make_bus(hull={"bow-1": 0.95}, chaos_max=0.2),
    ]
    for bus in grid:
        for signal in emit_somatic_signals(bus):
            lowered = signal.label.lower()
            for term in PHENOMENAL_TERMS:
                assert term not in lowered, (signal.label, term)


# --- Assembler integration ------------------------------------------------------------


def test_signals_take_precedence_over_note() -> None:
    bus = make_bus()
    bundle = assemble_perception_bundle(
        bus,
        somatic_note="legacy note text",
        somatic_signals=[sig("power margin thin", 0.95)],
    )
    assert "power margin thin" in bundle
    assert "legacy note text" not in bundle


def test_explicit_empty_signals_render_empty_somatic() -> None:
    bus = make_bus()
    bundle = assemble_perception_bundle(bus, somatic_signals=[])
    somatic_section = bundle.split("<somatic>")[1].split("</somatic>")[0]
    assert somatic_section.strip() == ""


def test_legacy_note_path_unchanged() -> None:
    bus = make_bus()
    bundle = assemble_perception_bundle(bus, somatic_note="third harmonic warm. watched.")
    assert "third harmonic warm. watched." in bundle


def test_emitter_to_assembler_end_to_end() -> None:
    bus = make_bus(warp=WarpState(W=0.9, phase="cruising"), power={"warp": 0.95})
    bundle = assemble_perception_bundle(bus, somatic_signals=emit_somatic_signals(bus))
    somatic_section = bundle.split("<somatic>")[1].split("</somatic>")[0]
    assert "power margin thin" in somatic_section
    assert "harmonic" in somatic_section
