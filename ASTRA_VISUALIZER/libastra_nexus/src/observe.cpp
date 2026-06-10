// libastra_nexus/src/observe.cpp
// Extracted from proto/astra_nexus.cpp lines 236-366. Semantics IDENTICAL.

#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include <algorithm>
#include <cmath>

namespace astra {

double compute_apparent_rate(double v_radial, uint32_t regime) {
    double beta = v_radial / C_LIGHT;

    if (regime & R_WARP_CRUISE) {
        // Bubble crew is locally inertial (gamma_kinematic == 1, §3.3).
        // Recession is geometric (sectors iterating), not kinematic.
        // Classical retarded-time formula: dt_emit/dt_recv = 1 - beta.
        // Can go arbitrarily negative for v_app > c. THIS IS THE EFFECT.
        return 1.0 - beta;
    }

    if (regime & R_STL_REL) {
        // Inertial motion in flat spacetime: SR longitudinal Doppler.
        // T_obs/T_emit = sqrt((1+beta)/(1-beta)); apparent rate = sqrt((1-beta)/(1+beta)).
        // For |beta| < 1 always; never reverses (asymptotes to 0 or inf).
        double bc = beta;
        if (bc >=  0.9999) bc =  0.9999;
        if (bc <= -0.9999) bc = -0.9999;
        return std::sqrt((1.0 - bc) / (1.0 + bc));
    }

    // REST / STL_NONREL — linear approx fine for small beta.
    return 1.0 - beta;
}

double compute_z_kin(double v_radial) {
    double beta = v_radial / C_LIGHT;
    // Cap beta for visual purposes; temporal reversal is carried by
    // apparent_rate, not by z_kin (which is colour).
    if (beta >=  0.9999) beta =  0.9999;
    if (beta <= -0.9999) beta = -0.9999;
    return std::sqrt((1.0 + beta) / (1.0 - beta)) - 1.0;
}

double compute_z_cosmo(double d_proper) {
    return H0_SI * d_proper / C_LIGHT;
}

double compute_lookback(double d_proper, double z_cosmo) {
    double lb = d_proper / C_LIGHT;
    if (z_cosmo > 0.01) {
        // t_lookback ~= (d/c) * (1 - 3z/4) for z < 2 (provisional)
        lb *= (1.0 - 0.75 * std::min(z_cosmo, 2.0));
    }
    return lb;
}

ObservableState observe(Vec3   ship_pos,
                        Vec3   ship_velocity,
                        double t_cosmic,
                        Vec3   body_pos,
                        double body_metric_shift,
                        uint32_t regime,
                        double body_t_source_start)
{
    ObservableState obs = {};
    Vec3 to_body = body_pos - ship_pos;
    obs.d_proper = std::max(to_body.mag(), 1.0);
    Vec3 r_hat = to_body / obs.d_proper;

    // v_radial positive when ship moves AWAY from body.
    // ship_velocity points in ship motion; r_hat points from ship to body.
    // If ship_velocity antiparallel to r_hat, ship recedes from body.
    obs.v_radial = -ship_velocity.dot(r_hat);

    obs.z_cosmo  = compute_z_cosmo(obs.d_proper);
    obs.z_kin    = compute_z_kin(obs.v_radial);
    obs.z_metric = body_metric_shift;

    // Multiplicative composition: (1+z_total) = (1+z_cosmo)(1+z_kin)(1+z_metric)
    obs.z_total = (1.0 + obs.z_cosmo) * (1.0 + obs.z_kin)
                * (1.0 + obs.z_metric) - 1.0;

    double lookback = compute_lookback(obs.d_proper, obs.z_cosmo);
    obs.t_emit = t_cosmic - lookback;

    obs.apparent_rate = compute_apparent_rate(obs.v_radial, regime)
                      / (1.0 + obs.z_cosmo);
    obs.time_reversed = obs.apparent_rate < 0.0;

    // §3.11: source-history bound.
    obs.beyond_photon_history = obs.t_emit < body_t_source_start;

    // §3.12: Hubble horizon.
    obs.beyond_hubble_horizon = obs.d_proper > D_HUBBLE_SI;

    return obs;
}

}  // namespace astra
