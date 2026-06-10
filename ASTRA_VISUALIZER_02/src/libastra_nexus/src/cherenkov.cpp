#include "astra_nexus/cherenkov.h"

#include <cmath>

namespace astra {

double n_refractive_default(double W) {
    // Provisional shape: n = 1 + W. At rest (W=0) the medium is vacuum (n=1);
    // at the bubble core (W ~= 1) the medium has n ~= 2. Tunable via UI slider
    // in Scene S06; future revisions may introduce n = 1 + alpha * W^k or
    // similar after empirical residue accumulates.
    return 1.0 + W;
}

double compute_cherenkov_angle(double W, double beta, NRefractiveModel n_model) {
    double n = n_model ? n_model(W) : n_refractive_default(W);
    double nb = n * beta;
    if (nb <= 1.0) return -1.0;  // inactive: no real angle
    return std::acos(1.0 / nb);
}

} // namespace astra
