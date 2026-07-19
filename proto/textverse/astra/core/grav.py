"""Gravitational composition — Python mirror of the §3.2 Schwarzschild-
dominant factor (proto/astra_nexus.cpp `compute_grav_factor`).

Pure closed-form kinematic derivation in the detect_regime / rapidity
mirror family: small, anchor-tested against the same values the C++ suite
asserts, used where a synchronous derivation is required (StateBus
computed fields — a frozen snapshot cannot await the stdio bridge).
Cross-substrate parity: the C++ binary exposes the identical algorithm
as the `compute_grav_factor` stdio op (QCR-5 additive Track C turn,
2026-07-19; the wire's first array-bearing op), and the two substrates
are held in agreement across a mass/distance grid by
tests/test_nexus_bridge.py::test_compute_grav_factor_python_matches_cpp.

Formula (spec v0.129 §3.2, locked): the dominant BH (smallest r/r_s with
r > r_s) contributes full Schwarzschild `√(1 − r_s/r)`; non-dominant
bodies contribute the summed weak-field correction `√(1 + 2·Φ_other/c²)`.
Factors multiply; the result is ≡ 1 in flat space and continuous in r
(reduces to weak-field at large r by Taylor expansion — no piecewise
discontinuities in dτ/dt).
"""

from __future__ import annotations

from collections.abc import Sequence
from math import inf, sqrt
from typing import Protocol

from astra.core.astra_coord import AstraCoord, astra_distance

C_LIGHT_M_S: float = 299_792_458.0  # m/s, exact by SI definition
G_GRAV: float = 6.67430e-11         # m^3 kg^-1 s^-2 (CODATA; matches nexus)


class BHLike(Protocol):
    """Structural type for black-hole records.

    Keeps the dependency direction clean (core never imports state_bus);
    `astra.state_bus.schema.BHRecord` satisfies this structurally.
    Read-only properties so frozen pydantic models type-check as members.
    """

    @property
    def mass_kg(self) -> float: ...

    @property
    def position(self) -> AstraCoord: ...


def schwarzschild_radius_m(mass_kg: float) -> float:
    """r_s = 2GM/c² (mirrors C++ `schwarzschild_r`)."""
    return 2.0 * G_GRAV * mass_kg / (C_LIGHT_M_S * C_LIGHT_M_S)


def compute_grav_factor(bh_list: Sequence[BHLike], ship_pos: AstraCoord) -> float:
    """Composite gravitational time-dilation factor at `ship_pos` (§3.2).

    Empty list → 1.0 (flat space). Bodies at or inside their own r_s are
    excluded from dominance selection (the r > r_s guard, as in C++); the
    sub-10·r_s domain is out of v0.1 scope per §7.4 (navigation refusal
    fires long before the formula's breakdown).
    """
    if not bh_list:
        return 1.0

    dom_i = -1
    min_ratio = inf
    for i, bh in enumerate(bh_list):
        r = astra_distance(bh.position, ship_pos)
        rs = schwarzschild_radius_m(bh.mass_kg)
        if r > rs and (r / rs) < min_ratio:
            min_ratio = r / rs
            dom_i = i

    factor = 1.0
    if dom_i >= 0:
        r = astra_distance(bh_list[dom_i].position, ship_pos)
        rs = schwarzschild_radius_m(bh_list[dom_i].mass_kg)
        factor *= sqrt(1.0 - rs / r)

    phi_other = 0.0
    for i, bh in enumerate(bh_list):
        if i == dom_i:
            continue
        r = astra_distance(bh.position, ship_pos)
        if r > 0.0:
            phi_other += -G_GRAV * bh.mass_kg / r
    if abs(phi_other) > 1e-30:
        arg = 1.0 + 2.0 * phi_other / (C_LIGHT_M_S * C_LIGHT_M_S)
        if arg > 0.0:
            factor *= sqrt(arg)

    return factor
