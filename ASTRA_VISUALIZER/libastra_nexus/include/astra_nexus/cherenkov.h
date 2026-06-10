// libastra_nexus/include/astra_nexus/cherenkov.h
//
// NEW: closes the AUDIT 5D-F4 gap. The Cherenkov half-angle formula was
// locked at 4 spec sites (§6 step 10, §6 Appendix B, §10 validation, §15.6)
// with ZERO code-side implementation. This module closes that gap.
//
// Formula (spec §6 step 10):
//   cos(theta_c) = 1 / (n * beta)
//
// where n is the warp-field refractive index (default n(W) = 1 + n_coeff * W)
// and beta is the EFFECTIVE velocity / c (v_app/c in WARP, raw tanh(omega) in
// STL). The cone is physically meaningful only when n * beta > 1.

#pragma once

#include "constants.h"

namespace astra {

// Default refractive-index model for the warp field.
// Provisional per DESIGN_SPEC §6.6: n(W) = 1 + n_coefficient * W,
// with n_coefficient = 1.0 as the default tuning value.
inline double n_refractive_default(double W, double n_coefficient = 1.0) {
    return 1.0 + n_coefficient * W;
}

// Compute Cherenkov half-angle.
//   W:             warp field magnitude at evaluation point, expected in [0, 1].
//   beta:          effective velocity / c (use v_app/c for warp; tanh(omega) for STL).
//   n_coefficient: tuning parameter for the n(W) model (default 1.0).
// Returns the angle in RADIANS when n*beta > 1; returns -1.0 when the
// cone is inactive / undefined (n*beta <= 1).
double compute_cherenkov_angle(double W, double beta, double n_coefficient = 1.0);

}  // namespace astra
