#include "physics/physics_core.h"

#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/composition.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/rapidity.h"
#include "astra_nexus/vec3.h"

#include <cmath>

namespace astra_viz {

PhysicsCalcOutput physics_calc(const PhysicsCalcInput& in) {
    PhysicsCalcOutput out{};

    // Reconstruct rapidity from v_radial via inverse tanh. For STL we want
    // gamma = cosh(atanh(beta)), the canon's locked formulation (NEVER 1/sqrt).
    // For WARP the bubble crew is inertial (gamma_kin = 1) per spec §3.3, but
    // we still report omega/beta so the operator can see the v/c ratio.
    double beta = in.v_radial_si / astra::C_LIGHT;
    double beta_c = beta;
    if (beta_c >=  0.9999999) beta_c =  0.9999999;
    if (beta_c <= -0.9999999) beta_c = -0.9999999;
    out.omega = std::atanh(beta_c);
    out.gamma = std::cosh(out.omega);
    out.beta  = beta;

    out.f_warp = astra::f_warp_canon(in.W_warp);

    // For WARP_CRUISE composition uses gamma_kin = 1 per spec §3.3.
    double gamma_for_composition = in.warp_active ? 1.0 : out.gamma;
    out.dtau_dt_cosmic = astra::dtau_dt_cosmic(in.W_warp, in.grav_factor,
                                               gamma_for_composition, in.warp_active);

    out.apparent_rate_raw = astra::compute_apparent_rate(in.v_radial_si, in.regime);

    // Set up the geometry for observe(): place the body on +z, ship at origin
    // moving in +z at the requested radial speed so r_hat dot ship_vel reproduces
    // the supplied v_radial.
    astra::Vec3 ship_pos{0.0, 0.0, 0.0};
    astra::Vec3 body_pos{0.0, 0.0, in.d_to_body_si};
    astra::Vec3 ship_vel{0.0, 0.0, -in.v_radial_si};
    out.obs = astra::observe(ship_pos, ship_vel, in.t_cosmic_s,
                             body_pos, in.body_metric_shift, in.regime,
                             in.body_t_source_start);
    return out;
}

} // namespace astra_viz
