"""Day 5 tests for the mini-universe catalog + body queries."""

from __future__ import annotations

from astra.universe import (
    AU_M,
    EARTH,
    EARTH_PERIOD_S,
    HOT_EARTH,
    SUN,
    V0_CATALOG,
    all_names,
    is_keplerian,
    lookup_body,
    parent_name,
    static_position,
)


def test_catalog_has_three_bodies() -> None:
    assert set(V0_CATALOG) == {"sun", "earth", "hot_earth"}
    assert set(all_names()) == {"sun", "earth", "hot_earth"}


def test_sun_static_position() -> None:
    assert static_position(SUN) is not None
    assert is_keplerian(SUN) is False
    assert SUN.kind == "star"
    assert SUN.mass_kg == 1.989e30


def test_earth_keplerian() -> None:
    assert is_keplerian(EARTH) is True
    assert static_position(EARTH) is None
    assert parent_name(EARTH) == "sun"
    assert EARTH.kepler is not None
    assert abs(EARTH.kepler.a - AU_M) < 1.0
    assert abs(EARTH.kepler.period_s - EARTH_PERIOD_S) < 1.0


def test_hot_earth_1_day_orbit() -> None:
    """Hot-Earth's 1-day period is what makes retarded-time effects visible."""
    assert is_keplerian(HOT_EARTH) is True
    assert HOT_EARTH.kepler is not None
    assert HOT_EARTH.kepler.period_s == 86400.0    # 1 day in seconds


def test_lookup_known_body() -> None:
    assert lookup_body("sun") == SUN
    assert lookup_body("earth") == EARTH


def test_lookup_unknown_returns_none() -> None:
    assert lookup_body("jupiter") is None
    assert lookup_body("") is None


def test_parent_name_for_static_body() -> None:
    """Static-position bodies have no orbital parent."""
    assert parent_name(SUN) is None


def test_au_value_match_si() -> None:
    """1 AU per IAU 2012: 149_597_870_700 m exactly (we use 149_597_870_700.0)."""
    assert abs(AU_M - 1.495_978_707e11) < 1e2
