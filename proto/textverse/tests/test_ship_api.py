"""Day 5 tests for ship.spec + ship.api + ship.dispatcher.

Verifies the locked v0 tool surface accepts valid args, rejects malformed
args with descriptive errors, and emits the expected state_diff shape
per op.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from astra.core import Regime
from astra.core.astra_coord import AstraCoord
from astra.ship import (
    DECK_1,
    DECK_4,
    DECKS,
    HULL_HEIGHT_M,
    HULL_LENGTH_M,
    HULL_WIDTH_M,
    NUM_DECKS,
    TOOL_API,
    PowerAllocateArgs,
    SensorsScanArgs,
    WarpEngageArgs,
    all_camera_free_zones,
    all_zones,
    dispatch,
    regime_label,
    subsystem_in_locked_list,
    tool_schema_hint,
    zone_to_deck,
)

# --- Spec constants ----------------------------------------------------------

def test_hull_dimensions_match_memory() -> None:
    """Per memory/hull_design_v0.md: 280 m × 78 m × 22 m, 4 decks."""
    assert HULL_LENGTH_M == 280.0
    assert HULL_WIDTH_M == 78.0
    assert HULL_HEIGHT_M == 22.0
    assert NUM_DECKS == 4
    assert len(DECKS) == 4


def test_deck_indices_are_1_to_4_top_to_bottom() -> None:
    assert DECK_1.index == 1
    assert DECK_4.index == 4
    assert DECK_1.function == "bridge_and_observation"
    assert DECK_4.function == "engineering"


def test_camera_free_zones_match_canon() -> None:
    """Per book/CANON.md + spec §4.8: quarters, hygiene, observation, hydroponics greenhouse."""
    czs = all_camera_free_zones()
    assert "observation_lounge" in czs
    assert "quarters" in czs
    assert "hygiene" in czs
    assert "hydroponics_greenhouse" in czs


def test_zone_to_deck_inverse_mapping() -> None:
    z2d = zone_to_deck()
    assert z2d["bridge"] == 1
    assert z2d["quarters"] == 2
    assert z2d["medical"] == 3
    assert z2d["reactor"] == 4


def test_all_zones_unique() -> None:
    """No duplicate zone names across decks."""
    zones = all_zones()
    assert len(zones) == len(set(zones))


# --- TOOL_API locked names ---------------------------------------------------

def test_tool_api_has_seven_v0_ops() -> None:
    """Six effector/log ops + status.query, the surface's only read op
    (ruling R-A, v0.130 adoption 2026-07-19)."""
    expected = {
        "warp.engage", "warp.disengage", "nav.heading_set",
        "sensors.scan", "power.allocate", "log.write",
        "status.query",
    }
    assert set(TOOL_API) == expected


def test_subsystem_in_locked_list() -> None:
    assert subsystem_in_locked_list("warp") is True
    assert subsystem_in_locked_list("cognitive_cores") is True
    assert subsystem_in_locked_list("shields") is False     # not in v0 list
    assert subsystem_in_locked_list("hyperdrive") is False  # not in v0 list


def test_tool_schema_hint_contains_field_names() -> None:
    hint = tool_schema_hint("power.allocate")
    assert "subsystem" in hint
    assert "fraction" in hint
    assert "power.allocate" in hint


def test_tool_schema_hint_unknown_op() -> None:
    assert "unknown op" in tool_schema_hint("not.a.real.op")


# --- Arg schemas (validation) ------------------------------------------------

def test_warp_engage_factor_bounded() -> None:
    WarpEngageArgs(target_factor=0.0)        # ok at floor
    WarpEngageArgs(target_factor=1.0)        # ok at ceiling
    with pytest.raises(ValidationError):
        WarpEngageArgs(target_factor=-0.1)
    with pytest.raises(ValidationError):
        WarpEngageArgs(target_factor=1.1)


def test_power_allocate_fraction_bounded() -> None:
    PowerAllocateArgs(subsystem="warp", fraction=0.5)
    with pytest.raises(ValidationError):
        PowerAllocateArgs(subsystem="warp", fraction=1.5)
    with pytest.raises(ValidationError):
        PowerAllocateArgs(subsystem="warp", fraction=-0.1)


def test_power_allocate_subsystem_must_be_locked() -> None:
    with pytest.raises(ValidationError):
        PowerAllocateArgs(subsystem="shields", fraction=0.5)


def test_sensors_scan_defaults() -> None:
    args = SensorsScanArgs()
    assert args.region == "forward"
    assert args.sensitivity == 0.5


# --- Dispatcher: validate + describe -----------------------------------------

def test_dispatch_unknown_op() -> None:
    result = dispatch("not.a.real.op", {})
    assert result.ok is False
    assert "unknown op" in result.error


def test_dispatch_power_allocate_emits_diff() -> None:
    result = dispatch("power.allocate", {"subsystem": "warp", "fraction": 0.7})
    assert result.ok is True
    assert result.args == {"subsystem": "warp", "fraction": 0.7}
    assert result.state_diff == {"power_allocation": {"warp": 0.7}}


def test_dispatch_log_write_emits_diff() -> None:
    result = dispatch("log.write", {"channel": "watch", "text": "harmonic 4.2% noted"})
    assert result.ok is True
    assert result.state_diff["log_appended"]["channel"] == "watch"


def test_dispatch_warp_engage_without_coords() -> None:
    result = dispatch("warp.engage", {"target_factor": 0.3})
    assert result.ok is True
    assert result.state_diff == {"warp_target_factor": 0.3}


def test_dispatch_warp_engage_with_coords() -> None:
    coords = AstraCoord(sx=10, sy=0, sz=0)
    result = dispatch("warp.engage", {"target_factor": 0.5, "target_coords": coords.model_dump()})
    assert result.ok is True
    assert "warp_target_coords" in result.state_diff


def test_dispatch_invalid_args_rejected() -> None:
    result = dispatch("power.allocate", {"subsystem": "warp", "fraction": 99.0})
    assert result.ok is False
    assert "schema validation failed" in result.error


def test_dispatch_nav_heading_set_named_body() -> None:
    result = dispatch("nav.heading_set", {"target": "earth"})
    assert result.ok is True
    assert result.state_diff == {"nav_target_body": "earth"}


def test_dispatch_sensors_scan_default_region() -> None:
    result = dispatch("sensors.scan", {})
    assert result.ok is True
    assert result.state_diff["sensor_scan_pending"]["region"] == "forward"


# --- regime_label ------------------------------------------------------------

def test_regime_label_rest() -> None:
    assert regime_label(Regime.REST) == "REST"


def test_regime_label_stl_rel() -> None:
    assert regime_label(Regime.STL_REL) == "STL_REL"


def test_regime_label_composed() -> None:
    composed = Regime.STL_REL | Regime.GRAVITY_WELL
    assert "STL_REL" in regime_label(composed)
    assert "GRAVITY_WELL" in regime_label(composed)
