// libastra_nexus/src/composition.cpp
// Extracted from proto/astra_nexus.cpp lines 170-234. Semantics IDENTICAL.

#include "astra_nexus/composition.h"
#include <algorithm>
#include <cmath>

namespace astra {

double schwarzschild_r(double M) {
    return 2.0 * G_GRAV * M / (C_LIGHT * C_LIGHT);
}

double compute_grav_factor(const std::vector<BHEntry>& bh_list, Vec3 ship_pos) {
    if (bh_list.empty()) return 1.0;

    // Find dominant BH (smallest r/r_s — strongest gravitational influence).
    int dom_i = -1;
    double min_ratio = 1e300;
    for (size_t i = 0; i < bh_list.size(); i++) {
        double r  = (bh_list[i].pos - ship_pos).mag();
        double rs = schwarzschild_r(bh_list[i].M);
        if (r > rs && (r / rs) < min_ratio) {
            min_ratio = r / rs;
            dom_i = (int)i;
        }
    }

    double factor = 1.0;

    // Dominant BH gets full Schwarzschild (continuous in r; reduces to weak-field at large r).
    if (dom_i >= 0) {
        double r  = (bh_list[dom_i].pos - ship_pos).mag();
        double rs = schwarzschild_r(bh_list[dom_i].M);
        factor *= std::sqrt(1.0 - rs / r);
    }

    // Non-dominant bodies contribute via summed weak-field potential.
    double phi_other = 0.0;
    for (size_t i = 0; i < bh_list.size(); i++) {
        if ((int)i == dom_i) continue;
        double r = (bh_list[i].pos - ship_pos).mag();
        if (r > 0) phi_other += -G_GRAV * bh_list[i].M / r;
    }
    if (std::abs(phi_other) > 1e-30) {
        double arg = 1.0 + 2.0 * phi_other / (C_LIGHT * C_LIGHT);
        if (arg > 0) factor *= std::sqrt(arg);
    }

    return factor;
}

double f_warp_canon(double W) {
    return std::max(0.5, 1.0 - 0.5 * W * W);
}

double dtau_dt_cosmic(double W_warp, double grav_factor, double gamma_kin,
                      bool warp_active)
{
    double f_w = warp_active ? f_warp_canon(W_warp) : 1.0;
    return f_w * grav_factor / gamma_kin;
}

}  // namespace astra
