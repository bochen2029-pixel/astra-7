#include "astra_nexus/rapidity.h"
#include "astra_nexus/constants.h"

#include <cmath>

namespace astra {

double Rapidity::omega() const { return zeta.mag(); }

double Rapidity::gamma() const { return std::cosh(omega()); }

double Rapidity::beta()  const { return std::tanh(omega()); }

Vec3 Rapidity::velocity() const {
    double w = omega();
    if (w < 1e-30) return {0, 0, 0};
    return zeta * (C_LIGHT * std::tanh(w) / w);
}

Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship) {
    Vec3 new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT);
    double mag = new_zeta.mag();
    if (mag > OMEGA_MAX) new_zeta = new_zeta * (OMEGA_MAX / mag);
    return Rapidity{new_zeta};
}

} // namespace astra
