"""Day 5 tests for the template-based perception assembler."""

from __future__ import annotations

from astra.core import AstraCoord, TimeState
from astra.harness import ReelEntry, assemble_perception_bundle
from astra.state_bus import BodyState, KeplerianElements, StateBus


def _minimal_state_bus(
    *,
    tau_ship: float = 47.0,
) -> StateBus:
    """Build a minimal StateBus for assembler tests (REST regime by default)."""
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=tau_ship,
            tau_crew_biological=tau_ship,
        ),
        procedural_body_states={
            "earth": BodyState(
                name="earth",
                kind="planet",
                mass_kg=5.972e24,
                kepler=KeplerianElements(a=1.5e11, e=0.0167, period_s=3.156e7, parent="sun"),
            ),
        },
    )


def test_bundle_has_four_xml_sections() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="hey",
    )
    assert "<state>" in bundle
    assert "</state>" in bundle
    assert "<somatic>" in bundle
    assert "<recent>" in bundle
    assert "<operator>" in bundle
    assert "</operator>" in bundle


def test_state_section_includes_tau_ship_and_regime() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(tau_ship=47.5),
        operator_text="",
    )
    assert "watch 47" in bundle
    assert "REST" in bundle


def test_state_section_mentions_bodies() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="",
    )
    assert "earth" in bundle


def test_operator_text_passthrough() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="hey, you still watching that reactor thing?",
    )
    assert "hey, you still watching that reactor thing?" in bundle


def test_silence_operator_input_keeps_empty_tag() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="",
    )
    assert "<operator>" in bundle
    assert "</operator>" in bundle
    # Empty operator body means the tag is present but body is whitespace
    op_start = bundle.index("<operator>") + len("<operator>")
    op_end = bundle.index("</operator>")
    assert bundle[op_start:op_end].strip() == ""


def test_somatic_note_included() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="",
        somatic_note="third harmonic doing that thing again. watched.",
    )
    assert "third harmonic" in bundle


def test_reel_retrievals_in_recent_section() -> None:
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="",
        reel_retrievals=[
            ReelEntry(tau_ship=46.0, t_cosmic_at_write=0.0, body="third-harmonic drift noted cycle 46"),
        ],
    )
    assert "third-harmonic drift noted cycle 46" in bundle
    assert "watch 46" in bundle


def test_no_em_dash_in_bundle() -> None:
    """Per voice rules: no em-dashes anywhere in operator-facing prose."""
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="",
    )
    assert "\u2014" not in bundle


def test_no_wall_clock_in_bundle() -> None:
    """Per spec §1.2: bundle must not leak real-world dates/times."""
    bundle = assemble_perception_bundle(
        state_bus=_minimal_state_bus(),
        operator_text="",
    )
    # The bundle uses τ_ship watch numbers, not wall-clock
    assert "2026" not in bundle
    assert "AM" not in bundle
    assert "PM" not in bundle
    assert "Monday" not in bundle
