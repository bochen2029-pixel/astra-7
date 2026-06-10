// libastra_nexus/include/astra_nexus/rapidity.h
//
// Rapidity (§3.7 v0.126) — 3-vector with cosh-only discipline.
// Extracted from proto/astra_nexus.cpp lines 144-168 (READ-ONLY source).
// Semantics IDENTICAL.

#pragma once

#include "constants.h"

namespace astra {

struct Rapidity {
    Vec3 zeta;  // zeta-vector

    double omega() const;
    // LOCKED: gamma = cosh(omega). Never compute as 1/sqrt(1-beta^2) per
    // §3.7 v0.126 catastrophic-cancellation discipline.
    double gamma() const;
    double beta()  const;
    Vec3   velocity() const;
};

// dzeta/dtau_ship = a_proper / c, with magnitude clamping at OMEGA_MAX.
Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship);

}  // namespace astra
