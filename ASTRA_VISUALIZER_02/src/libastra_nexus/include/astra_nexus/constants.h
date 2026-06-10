// constants.h — physical constants shared with canon (proto/astra_nexus.cpp:55-69).
// Mirrors canon spec §1.2, §4.2 (State Bus), Appendix B.
// Any divergence from canon values is a bug.
#pragma once

namespace astra {

constexpr double C_LIGHT     = 299792458.0;                  // m/s (exact)
constexpr double G_GRAV      = 6.67430e-11;                  // m^3 kg^-1 s^-2
constexpr double M_SUN       = 1.98892e30;                   // kg
constexpr double PARSEC      = 3.0856775814913673e16;        // m
constexpr double LIGHT_YEAR  = 9.4607304725808e15;           // m
constexpr double MPC         = 1.0e6 * PARSEC;
constexpr double H0_KMS_MPC  = 70.0;                         // km/s/Mpc (provisional)
constexpr double H0_SI       = H0_KMS_MPC * 1000.0 / MPC;    // s^-1
constexpr double OMEGA_M     = 0.3;                          // matter density (provisional)
constexpr double OMEGA_LAM   = 0.7;                          // dark energy density (provisional)
constexpr double D_HUBBLE_SI = C_LIGHT / H0_SI;              // m, Hubble horizon (~13.7 Gly @ H0=70)

// v0.126 N1 lock: clamp for 3-vector rapidity magnitude
// gives gamma_max = cosh(16.811) approx 1e7. NEVER raise without operator approval.
constexpr double OMEGA_MAX = 16.811;

// Time conventions used by the visualizer scenes' sim-speed sliders.
// (Not in canon proto/astra_nexus.cpp; visualizer-side convenience.)
constexpr double SECONDS_PER_DAY  = 86400.0;
constexpr double SECONDS_PER_YEAR = 365.25 * SECONDS_PER_DAY;

} // namespace astra
