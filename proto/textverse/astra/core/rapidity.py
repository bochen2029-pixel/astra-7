"""Rapidity ζ⃗ constants and helpers per spec v0.129 §3.7.

The 3-vector rapidity ζ⃗ is the primary kinematic state variable. Its scalar
magnitude ω = |ζ⃗| is clamped at ω_max ≈ 16.811, giving γ_max = cosh(ω_max)
≈ 10⁷ and β_max ≈ 1 − 5·10⁻¹⁵.

Derived kinematics (computed by proto/astra_nexus, queried via nexus_bridge):
    ω = |ζ⃗|
    v⃗ = c · tanh(ω) · (ζ⃗ / ω)
    γ = cosh(ω)
    β = tanh(ω)

Compute γ from ω directly; never round-trip through β (catastrophic
cancellation at high ω destroys precision — v0.126 N6 finding).

This module exposes constants and pure helpers used by TimeState validation.
Day 2 extends it with nexus_bridge calls for integration.
"""

from __future__ import annotations

from math import sqrt

OMEGA_MAX: float = 16.811  # spec v0.129 §3.7 locked clamp (γ_max ≈ 10⁷)


def rapidity_magnitude(zeta: tuple[float, float, float]) -> float:
    """ω = |ζ⃗|, the scalar rapidity magnitude.

    Pure math, no I/O. Used by TimeState's clamp validator.
    """
    zx, zy, zz = zeta
    return sqrt(zx * zx + zy * zy + zz * zz)
