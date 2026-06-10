// rapidity.h — 3-vector Rapidity zeta per spec §3.7 (v0.126).
// Discipline: gamma = cosh(omega). NEVER 1/sqrt(1-beta^2) (catastrophic cancellation
// at high omega). Mirrors canon proto/astra_nexus.cpp:147-168.
#pragma once

#include "astra_nexus/vec3.h"

namespace astra {

struct Rapidity {
    Vec3 zeta;

    double omega() const;
    double gamma() const;     // LOCKED: cosh(omega) path only
    double beta()  const;
    Vec3   velocity() const;
};

// d(zeta)/d(tau_ship) = a_proper / c, clamped at OMEGA_MAX.
Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship);

} // namespace astra
