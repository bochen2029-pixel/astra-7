// observe.h — ObservableState struct + observe() per spec §6.3 (v0.128).
//
// ObservableState carries all per-body retarded-time + redshift output.
// observe() composes 12 steps: distance, v_radial, three redshifts, multiplicative
// total, lookback, t_emit, regime-dispatched apparent_rate, two history-bound flags.
// Mirrors canon proto/astra_nexus.cpp:250-366.
#pragma once

#include <cstdint>
#include <limits>
#include "astra_nexus/vec3.h"

namespace astra {

struct ObservableState {
    double d_proper;             // proper distance (m)
    double v_radial;             // positive = receding
    double z_cosmo;
    double z_kin;
    double z_metric;
    double z_total;
    double t_emit;               // retarded time (cosmic seconds)
    double apparent_rate;        // dt_emit/dt_cosmic; can be < 0 in WARP
    bool   time_reversed;
    bool   beyond_photon_history; // §3.11: t_emit < t_source_start
    bool   beyond_hubble_horizon; // §3.12: d_proper > c/H_0
};

double compute_z_kin(double v_radial);
double compute_z_cosmo(double d_proper);
double compute_lookback(double d_proper, double z_cosmo);

ObservableState observe(Vec3   ship_pos,
                        Vec3   ship_velocity,
                        double t_cosmic,
                        Vec3   body_pos,
                        double body_metric_shift,
                        uint32_t regime,
                        double body_t_source_start = -std::numeric_limits<double>::infinity());

} // namespace astra
