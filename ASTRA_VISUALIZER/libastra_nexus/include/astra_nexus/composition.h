// libastra_nexus/include/astra_nexus/composition.h
//
// Gravitational composition (§3.2 v0.126 — Schwarzschild-everywhere-dominant)
// + warp dilation canon (§3.5) + full composition rule (§3.2).
// Extracted from proto/astra_nexus.cpp lines 170-234 (READ-ONLY source).
// Semantics IDENTICAL.

#pragma once

#include "constants.h"
#include <vector>

namespace astra {

struct BHEntry {
    double M;
    Vec3   pos;
};

// Schwarzschild radius for a body of mass M (kg).
double schwarzschild_r(double M);

// Composite gravitational dilation factor: dominant BH gets full Schwarzschild,
// non-dominant bodies contribute via summed weak-field potential.
double compute_grav_factor(const std::vector<BHEntry>& bh_list, Vec3 ship_pos);

// Warp dilation — ASTRA-7 canon default (§3.5).
// f_warp(W) = max(0.5, 1 - 0.5*W^2)
double f_warp_canon(double W);

// Composition rule (§3.2): dtau_ship / dt_cosmic.
// = f_warp(W) * grav_factor / gamma_kinematic
double dtau_dt_cosmic(double W_warp, double grav_factor, double gamma_kin,
                      bool warp_active);

}  // namespace astra
