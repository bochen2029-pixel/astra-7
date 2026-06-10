#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/regime.h"

#include <cmath>

namespace astra {

double compute_apparent_rate(double v_radial, uint32_t regime) {
    double beta = v_radial / C_LIGHT;

    if (regime & R_WARP_CRUISE) {
        // Bubble crew is locally inertial (gamma_kin == 1, §3.3).
        // Recession is geometric (sectors iterating), not kinematic.
        // Classical retarded-time: dt_emit/dt_recv = 1 - beta.
        // Goes arbitrarily negative for v_app > c. THIS IS THE EFFECT.
        return 1.0 - beta;
    }

    if (regime & R_STL_REL) {
        // Inertial motion in flat spacetime: SR longitudinal Doppler.
        // T_obs/T_emit = sqrt((1+beta)/(1-beta)); apparent rate = sqrt((1-beta)/(1+beta)).
        // For |beta| < 1 always; never reverses.
        double bc = beta;
        if (bc >=  0.9999) bc =  0.9999;
        if (bc <= -0.9999) bc = -0.9999;
        return std::sqrt((1.0 - bc) / (1.0 + bc));
    }

    // REST / STL_NONREL: linear approx is fine for small beta.
    return 1.0 - beta;
}

} // namespace astra
