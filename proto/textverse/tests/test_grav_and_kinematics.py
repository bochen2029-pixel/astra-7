"""Grav-factor mirror + ShipKinematicState derivation — spec-v0.130-DRAFT
§1 QCR-5 (GRAVITY_WELL leg plumbed to the StateBus computed regime) and
QCR-6 (the §4.2 derived kinematic view wired).

Anchor values mirror the C++ suite in proto/astra_nexus.cpp: grav factor at
r = 100·r_s, smooth approach to 1 at large r, the §10 composition-rule
identity cases, and the f_warp canon-default curve. Cross-substrate parity
via a stdio `compute_grav_factor` op is queued additive Track C work (the
C++ JSON parser has no array support yet); until then these anchors pin
both implementations to the same closed forms.
"""

from __future__ import annotations

from math import cosh, sqrt, tanh

from astra.core.astra_coord import AstraCoord, astra_distance
from astra.core.grav import (
    C_LIGHT_M_S,
    compute_grav_factor,
    schwarzschild_radius_m,
)
from astra.core.regime import Regime
from astra.core.ship_kinematic import (
    derive_ship_kinematics,
    dtau_dt_cosmic,
    f_warp_canon,
)
from astra.core.time_state import TimeState
from astra.state_bus.schema import BHRecord, StateBus, WarpState

M_SUN_KG = 1.98892e30  # matches the nexus constant

_ORIGIN = AstraCoord(sx=0, sy=0, sz=0)


def _time(zeta: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> TimeState:
    return TimeState(
        t_cosmic=1.5e10,
        tau_ship=47.5,
        tau_crew_biological=47.5,
        rapidity_zeta=zeta,
    )


# --- astra_distance (mirrors C++ §1.1 tests) ---------------------------------


def test_astra_distance_local_km() -> None:
    b = AstraCoord(sx=0, sy=0, sz=0, lx=1000.0)
    assert abs(astra_distance(_ORIGIN, b) - 1000.0) < 1e-9


def test_astra_distance_one_sector() -> None:
    c = AstraCoord(sx=1, sy=0, sz=0)
    assert abs(astra_distance(_ORIGIN, c) - 1_000_000.0) < 1e-6


# --- grav factor anchors (mirror C++ §3.2 tests) -----------------------------


def test_schwarzschild_radius_solar() -> None:
    rs = schwarzschild_radius_m(M_SUN_KG)
    assert abs(rs - 2954.0) < 1.0  # ~2.954 km for 1 M_sun


def test_grav_factor_empty_is_flat() -> None:
    assert compute_grav_factor([], _ORIGIN) == 1.0


def test_grav_factor_at_100_rs() -> None:
    """C++ anchor: grav factor at r = 100·r_s equals √(1 − 1/100)."""
    rs = schwarzschild_radius_m(10.0 * M_SUN_KG)
    r_target = 100.0 * rs  # ≈ 2.954e6 m → sector 3 minus a local offset
    sx = round(r_target / 1_000_000.0)
    lx = r_target - sx * 1_000_000.0
    bh = BHRecord(
        mass_kg=10.0 * M_SUN_KG,
        position=AstraCoord(sx=sx, sy=0, sz=0, lx=lx),
    )
    factor = compute_grav_factor([bh], _ORIGIN)
    assert abs(factor - sqrt(0.99)) < 1e-9


def test_grav_factor_far_approaches_unity() -> None:
    """C++ anchor: at ~1e15 m the factor approaches 1 smoothly."""
    bh = BHRecord(
        mass_kg=10.0 * M_SUN_KG,
        position=AstraCoord(sx=1_000_000_000, sy=0, sz=0),
    )
    factor = compute_grav_factor([bh], _ORIGIN)
    assert 0.999999 < factor <= 1.0


# --- composition-rule mirrors (C++ §10 identity anchors) ---------------------


def test_f_warp_canon_anchors() -> None:
    assert f_warp_canon(0.0) == 1.0
    assert f_warp_canon(1.0) == 0.5
    assert abs(f_warp_canon(0.5) - 0.875) < 1e-12


def test_dtau_dt_cosmic_anchors() -> None:
    assert dtau_dt_cosmic(0.0, 1.0, 1.0, warp_active=False) == 1.0
    assert dtau_dt_cosmic(0.0, 1.0, 2.0, warp_active=False) == 0.5
    assert dtau_dt_cosmic(1.0, 1.0, 1.0, warp_active=True) == 0.5
    assert abs(dtau_dt_cosmic(0.0, 0.7, 1.5, warp_active=False) - 0.7 / 1.5) < 1e-12
    full = dtau_dt_cosmic(0.8, 0.9, 2.0, warp_active=True)
    assert abs(full - f_warp_canon(0.8) * 0.9 / 2.0) < 1e-12


# --- derive_ship_kinematics --------------------------------------------------


def test_derive_rest_identity() -> None:
    sk = derive_ship_kinematics(rapidity_zeta=(0.0, 0.0, 0.0))
    assert sk.gamma == 1.0
    assert sk.beta == 0.0
    assert sk.dilation_ratio == 1.0
    assert sk.v_local_cmb == (0.0, 0.0, 0.0)


def test_derive_stl_omega_one() -> None:
    """ω = 1: γ = cosh(1), β = tanh(1), v_z = c·tanh(1); cosh-only path."""
    sk = derive_ship_kinematics(rapidity_zeta=(0.0, 0.0, 1.0))
    assert abs(sk.gamma - cosh(1.0)) < 1e-12
    assert abs(sk.beta - tanh(1.0)) < 1e-12
    assert abs(sk.dilation_ratio - 1.0 / cosh(1.0)) < 1e-12
    assert abs(sk.v_local_cmb[2] - C_LIGHT_M_S * tanh(1.0)) < 1e-3
    assert sk.v_local_cmb[0] == 0.0


def test_derive_warp_gamma_is_one_for_dilation() -> None:
    """§3.3: γ_kinematic ≡ 1 during warp; dilation = f_warp(W)·grav."""
    sk = derive_ship_kinematics(
        rapidity_zeta=(0.0, 0.0, 0.0),
        warp_active=True,
        warp_w=1.0,
    )
    assert sk.dilation_ratio == 0.5
    sk2 = derive_ship_kinematics(
        rapidity_zeta=(0.0, 0.0, 0.0),
        grav_factor=0.9,
        warp_active=True,
        warp_w=0.8,
    )
    assert abs(sk2.dilation_ratio - f_warp_canon(0.8) * 0.9) < 1e-12


# --- StateBus wiring (the QCR-5 / QCR-6 closures, end to end) ----------------


def test_state_bus_grav_factor_computed_field() -> None:
    sb = StateBus(astra_coord=_ORIGIN, time=_time())
    assert "grav_factor" in StateBus.model_computed_fields
    assert sb.grav_factor == 1.0


def test_state_bus_gravity_well_composes_into_regime() -> None:
    """A BH at r = 10·r_s drops the factor to √0.9 ≈ 0.949 < 0.99 →
    the GRAVITY_WELL bit composes at the StateBus root. This is the
    QCR-5 finding closed: before the plumb, this bit could never fire."""
    rs = schwarzschild_radius_m(10.0 * M_SUN_KG)
    bh = BHRecord(
        mass_kg=10.0 * M_SUN_KG,
        position=AstraCoord(sx=0, sy=0, sz=0, lx=10.0 * rs),
    )
    sb = StateBus(astra_coord=_ORIGIN, time=_time(), bh_list=[bh])
    assert abs(sb.grav_factor - sqrt(0.9)) < 1e-9
    assert sb.regime & Regime.GRAVITY_WELL
    assert sb.regime & ~Regime.GRAVITY_WELL == Regime.REST


def test_state_bus_far_bh_no_gravity_well() -> None:
    bh = BHRecord(
        mass_kg=M_SUN_KG,
        position=AstraCoord(sx=10, sy=0, sz=0),
    )
    sb = StateBus(astra_coord=_ORIGIN, time=_time(), bh_list=[bh])
    assert not (sb.regime & Regime.GRAVITY_WELL)


def test_state_bus_ship_kinematics_view() -> None:
    sb = StateBus(astra_coord=_ORIGIN, time=_time(zeta=(0.0, 0.0, 1.0)))
    assert "ship_kinematics" in StateBus.model_computed_fields
    sk = sb.ship_kinematics
    assert abs(sk.gamma - cosh(1.0)) < 1e-12
    assert abs(sk.dilation_ratio - 1.0 / cosh(1.0)) < 1e-12


def test_state_bus_ship_kinematics_under_warp() -> None:
    sb = StateBus(
        astra_coord=_ORIGIN,
        time=_time(),
        warp=WarpState(W=1.0, phase="cruising"),
    )
    assert sb.ship_kinematics.dilation_ratio == 0.5
    assert sb.regime & Regime.WARP_CRUISE


def test_state_bus_dump_roundtrip_ignores_echoes() -> None:
    """Computed fields serialize as echoes; validation ignores them and
    re-derives (the §4.6 coherence-gate pattern at snapshot scale)."""
    sb = StateBus(astra_coord=_ORIGIN, time=_time())
    dumped = sb.model_dump()
    assert "regime" in dumped
    assert "grav_factor" in dumped
    assert "ship_kinematics" in dumped
    rebuilt = StateBus.model_validate(dumped)
    assert rebuilt.regime == sb.regime
    assert rebuilt.grav_factor == sb.grav_factor
