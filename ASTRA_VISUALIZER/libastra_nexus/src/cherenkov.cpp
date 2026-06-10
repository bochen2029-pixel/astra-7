// libastra_nexus/src/cherenkov.cpp
//
// NEW — closes the AUDIT 5D-F4 gap: Cherenkov formula was locked at 4 spec
// sites (§6 step 10, §6 Appendix B, §10 validation, §15.6) with zero code
// implementation. This module is the code-side closure. Empirical evidence
// gathered here feeds back into the spec via DESIGN_SPEC §15.4.

#include "astra_nexus/cherenkov.h"
#include <cmath>

namespace astra {

double compute_cherenkov_angle(double W, double beta, double n_coefficient) {
    double n = n_refractive_default(W, n_coefficient);
    double n_beta = n * beta;
    if (n_beta <= 1.0) return -1.0;  // cone inactive
    return std::acos(1.0 / n_beta);
}

}  // namespace astra
