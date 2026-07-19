"""ShipKinematicState — derived kinematic view per spec v0.129 §4.2.

The view is (v_local_cmb, γ, β, grav_factor, dτ/dt): computed from ζ⃗ +
warp + gravitational context, never stored independently of them. The
v0.128-era `regime` slot is gone — regime lives solely as the StateBus
computed field, so a second copy cannot drift (spec-v0.130-DRAFT QCR-6).

`derive_ship_kinematics` is the synchronous derivation behind the
StateBus `ship_kinematics` computed field. Its math mirrors
proto/astra_nexus.cpp (`f_warp_canon`, `dtau_dt_cosmic`,
`Rapidity::velocity`) and is anchor-tested against the same §10 canonical
values the C++ suite asserts (tests/test_grav_and_kinematics.py).
Cosh-only discipline per §3.7: γ = cosh(ω), never 1/√(1−β²).
"""

from __future__ import annotations

from math import cosh, tanh

from pydantic import BaseModel, ConfigDict, Field

from astra.core.grav import C_LIGHT_M_S
from astra.core.rapidity import rapidity_magnitude


class ShipKinematicState(BaseModel):
    """Derived kinematic view (§4.2). Fields are computed, never stored
    independently of ζ⃗ and the grav/warp context; serialization is an
    echo, re-derived on load."""

    model_config = ConfigDict(frozen=True)

    v_local_cmb: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gamma: float = Field(ge=1.0, default=1.0)                 # γ = cosh(|ζ⃗|)
    beta: float = Field(ge=0.0, lt=1.0, default=0.0)          # β = tanh(|ζ⃗|)
    grav_factor: float = Field(ge=0.0, le=1.0, default=1.0)   # §3.2 composite
    dilation_ratio: float = Field(gt=0.0, le=1.0, default=1.0)  # dτ_ship/dt_cosmic


def f_warp_canon(w: float) -> float:
    """ASTRA-7 canon-default warp dilation `f_warp(W) = max(0.5, 1 − 0.5·W²)`
    (§3.5; mirrors C++ `f_warp_canon`). Contract-level default is ≡ 1; this
    is the operator's canon dial."""
    return max(0.5, 1.0 - 0.5 * w * w)


def dtau_dt_cosmic(
    w_warp: float,
    grav_factor: float,
    gamma_kin: float,
    warp_active: bool,
) -> float:
    """Composition rule §3.2 (mirrors C++ `dtau_dt_cosmic`):
    dτ_ship/dt_cosmic = f_warp(W) · grav_factor / γ_kinematic,
    with f_warp ≡ 1 when the warp drive is inactive."""
    f_w = f_warp_canon(w_warp) if warp_active else 1.0
    return f_w * grav_factor / gamma_kin


def derive_ship_kinematics(
    *,
    rapidity_zeta: tuple[float, float, float],
    grav_factor: float = 1.0,
    warp_active: bool = False,
    warp_w: float = 0.0,
) -> ShipKinematicState:
    """Derive the §4.2 kinematic view from the underlying truth fields.

    γ_kinematic ≡ 1 during warp for the dilation leg (§3.3: the bubble
    suspends kinematic velocity in its own frame); the ζ⃗-derived γ/β/v⃗
    are still reported as kinematic facts of the stored rapidity.
    """
    omega = rapidity_magnitude(rapidity_zeta)
    gamma = cosh(omega)
    beta = tanh(omega)
    if omega < 1e-30:
        v_local_cmb = (0.0, 0.0, 0.0)
    else:
        scale = C_LIGHT_M_S * beta / omega
        zx, zy, zz = rapidity_zeta
        v_local_cmb = (zx * scale, zy * scale, zz * scale)

    gamma_for_dilation = 1.0 if warp_active else gamma
    dilation = dtau_dt_cosmic(warp_w, grav_factor, gamma_for_dilation, warp_active)

    return ShipKinematicState(
        v_local_cmb=v_local_cmb,
        gamma=gamma,
        beta=beta,
        grav_factor=grav_factor,
        dilation_ratio=dilation,
    )
