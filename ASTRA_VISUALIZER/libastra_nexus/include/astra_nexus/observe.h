// libastra_nexus/include/astra_nexus/observe.h
//
// Observation Calculator (§3.11 v0.127 / §6.3 v0.128) — retarded-time
// observation with regime-dispatched apparent rate.
//
// CRITICAL: regime-dispatched apparent-rate formula.
//   STL_REL  (inertial v<c, SR):     sqrt((1-beta)/(1+beta)). Never reverses.
//   WARP_CRUISE (bubble gamma=1):    1 - v_app/c. Can reverse.
//   REST / STL_NONREL: linear approx (~1).
//
// Extracted from proto/astra_nexus.cpp lines 236-366 (READ-ONLY source).
// Semantics IDENTICAL.

#pragma once

#include "constants.h"
#include <cstdint>
#include <limits>

namespace astra {

// §6.3 v0.128: ObservableState — per-body retarded-time + redshift composition.
// `beyond_photon_history`: §3.11; `beyond_hubble_horizon`: §3.12.
struct ObservableState {
    double d_proper;              // proper distance (m)
    double v_radial;              // positive = receding
    double z_cosmo;
    double z_kin;
    double z_metric;
    double z_total;
    double t_emit;                // retarded time (cosmic seconds)
    double apparent_rate;         // dt_emit/dt_cosmic — can be < 0 in WARP
    bool   time_reversed;
    bool   beyond_photon_history; // §3.11: t_emit < body t_source_start
    bool   beyond_hubble_horizon; // §3.12: d_proper > c/H0
};

// Regime-dispatched apparent-rate (§3.11 v0.127, §10 validation row).
double compute_apparent_rate(double v_radial, uint32_t regime);

// SR longitudinal Doppler redshift, receding-positive convention.
double compute_z_kin(double v_radial);

// Cosmological redshift, linear-z weak-field approx for z < 0.1.
double compute_z_cosmo(double d_proper);

// Look-back time with flat-LambdaCDM correction (provisional).
double compute_lookback(double d_proper, double z_cosmo);

// §6.3 observe() — full 12-step retarded-time + redshift workflow.
ObservableState observe(Vec3   ship_pos,
                        Vec3   ship_velocity,
                        double t_cosmic,
                        Vec3   body_pos,
                        double body_metric_shift,
                        uint32_t regime,
                        double body_t_source_start = -std::numeric_limits<double>::infinity());

}  // namespace astra
