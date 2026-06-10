// libastra_nexus/src/kepler.cpp
// Extracted from proto/astra_nexus.cpp lines 368-398. Semantics IDENTICAL.

#include "astra_nexus/kepler.h"
#include "astra_nexus/constants.h"  // for M_PI
#include <cmath>

namespace astra {

double solve_kepler_E(double M, double e) {
    double E = M;  // initial guess for low-eccentricity orbits
    for (int i = 0; i < 30; i++) {
        double f  = E - e * std::sin(E) - M;
        double fp = 1.0 - e * std::cos(E);
        double dE = f / fp;
        E -= dE;
        if (std::abs(dE) < 1e-13) break;
    }
    return E;
}

double orbit_phase(const Orbit& orb, double t) {
    double M = 2.0 * M_PI * (t - orb.t0) / orb.period;
    double E = solve_kepler_E(M, orb.e);
    return 2.0 * std::atan2(
        std::sqrt(1.0 + orb.e) * std::sin(E / 2.0),
        std::sqrt(1.0 - orb.e) * std::cos(E / 2.0)
    );
}

}  // namespace astra
