// composition.h — gravitational composition + warp dilation + dtau/dt_cosmic.
// Per spec §3.2 (v0.126 Schwarzschild-everywhere-dominant) and §3.5 (warp canon).
// Mirrors canon proto/astra_nexus.cpp:172-234.
#pragma once

#include <vector>
#include "astra_nexus/vec3.h"

namespace astra {

struct BHEntry {
    double M;
    Vec3   pos;
};

double schwarzschild_r(double M);
double compute_grav_factor(const std::vector<BHEntry>& bh_list, Vec3 ship_pos);

// Warp dilation - ASTRA-7 canon default (§3.5). f_warp(0)=1, f_warp(1)=0.5.
double f_warp_canon(double W);

// Composition rule (§3.2): f_warp * grav_factor / gamma_kin.
// warp_active toggles f_warp; pass false to enforce f_warp == 1.
double dtau_dt_cosmic(double W_warp, double grav_factor, double gamma_kin,
                      bool warp_active);

} // namespace astra
