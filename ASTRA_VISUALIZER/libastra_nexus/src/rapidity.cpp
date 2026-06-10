// libastra_nexus/src/rapidity.cpp
// Extracted from proto/astra_nexus.cpp lines 144-168. Semantics IDENTICAL.

#include "astra_nexus/rapidity.h"
#include <cmath>

namespace astra {

double Rapidity::omega() const { return zeta.mag(); }

// LOCKED: gamma = cosh(omega). NEVER compute as 1/sqrt(1-beta^2) —
// catastrophic cancellation at high omega (v0.126 §3.7 discipline).
double Rapidity::gamma() const { return std::cosh(omega()); }

double Rapidity::beta()  const { return std::tanh(omega()); }

Vec3 Rapidity::velocity() const {
    double w = omega();
    if (w < 1e-30) return {0, 0, 0};
    return zeta * (C_LIGHT * std::tanh(w) / w);
}

// dzeta/dtau_ship = a_proper / c, with clamp at OMEGA_MAX.
Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship) {
    Vec3 new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT);
    double mag = new_zeta.mag();
    if (mag > OMEGA_MAX) new_zeta = new_zeta * (OMEGA_MAX / mag);
    return Rapidity{new_zeta};
}

}  // namespace astra
