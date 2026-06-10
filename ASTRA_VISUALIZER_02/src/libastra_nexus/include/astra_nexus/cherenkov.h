// cherenkov.h — NEW in libastra_nexus mirror; closes AUDIT 5D-F4.
//
// Cherenkov cone half-angle for a body inside the warp bubble moving at
// speed beta*c through a medium of refractive index n. Formula:
//
//     cos(theta_c) = 1 / (n * beta)
//
// When n*beta <= 1, no real Cherenkov angle exists (the body is sub-luminal
// in the medium). compute_cherenkov_angle returns -1.0 as the inactive sentinel.
//
// Provisional refractive-index model per DESIGN_SPEC §4.5 v2 plan:
//     n_refractive_default(W) = 1 + W
// where W is the warp metric value at the sample point (0 at infinity, ramps
// to ~1 inside the bubble). Scene S06 exposes the model coefficient via UI
// slider so the operator can sweep alternative shapes.
//
// Per spec §6 step 10 (Cherenkov formula) + §7 truth table + Appendix B.
// Not present in proto/astra_nexus.cpp; added here to bring assertion count
// from 66 (canon) -> 69+ (mirror) per CLAUDE.md §4 verification step.
#pragma once

namespace astra {

double n_refractive_default(double W);

// Optional n_model lets callers inject alternative refractive-index shapes
// (e.g. n = 1 + alpha*W^2). Pass nullptr to use n_refractive_default.
// Returns -1.0 when n*beta <= 1 (cone inactive).
using NRefractiveModel = double (*)(double);

double compute_cherenkov_angle(double W, double beta, NRefractiveModel n_model = nullptr);

} // namespace astra
