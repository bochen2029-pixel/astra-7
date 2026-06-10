// physics_core.h - thin facade over libastra_nexus that bundles the typical
// per-frame calculation pattern (rapidity -> composition -> observe) into one
// call. The UI's PhysicsCalc panel + Scene state displays go through here so
// every numeric the operator sees traces to a single code path.
//
// V2 deliberately keeps this lean: just the calculator + verify-math output.
// V3+ will extend with CUDA pre/post hooks where it matters.
#pragma once

#include <cstdint>

#include "astra_nexus/observe.h"

namespace astra_viz {

// Input bundle. All SI units. Defaults give the REST baseline (S01).
struct PhysicsCalcInput {
    uint32_t regime              = 0;       // R_REST
    double   v_radial_si         = 0.0;     // ship recession speed toward body; m/s
    double   W_warp              = 0.0;     // warp metric value [0, 1]
    bool     warp_active         = false;
    double   grav_factor         = 1.0;     // schwarzschild composition (1 = no grav)
    double   d_to_body_si        = 1.0e16;  // proper distance to body; m (~1 ly default)
    double   body_metric_shift   = 0.0;     // additional metric shift at the body
    double   t_cosmic_s          = 0.0;     // cosmic time of the observation
    double   body_t_source_start = -1.0e300; // -infinity = "always emitting"
};

// Output bundle. Every field is exactly what libastra_nexus returns.
struct PhysicsCalcOutput {
    // Rapidity reconstruction from v_radial (pure axial motion assumption).
    double omega;
    double gamma;
    double beta;

    // Composition rule (§3.2).
    double f_warp;
    double dtau_dt_cosmic;

    // Apparent-rate raw value WITHOUT the cosmological-redshift suppression.
    // Useful for the UI to show the dispatch decision explicitly.
    double apparent_rate_raw;

    // Full §6.3 ObservableState (raw libastra::observe output).
    astra::ObservableState obs;
};

PhysicsCalcOutput physics_calc(const PhysicsCalcInput& in);

} // namespace astra_viz
