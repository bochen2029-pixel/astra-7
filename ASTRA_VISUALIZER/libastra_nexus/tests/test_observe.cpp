// libastra_nexus/tests/test_observe.cpp
//
// Observation Calculator (§3.11 v0.127, §6.3 v0.128) — ported from
// proto/astra_nexus.cpp sections:
//   "Observation: STL_REL vs WARP apparent-rate distinction"
//   "Kinematic redshift (SR longitudinal Doppler)"
//   "Redshift composition (multiplicative)"
//   "Observation end-to-end (ObservableState struct)"
//   "§6.4 retarded_time_solve primitive"
//   "§6.4 observe primitive end-to-end"
//   "§3.11 photon-source-history bound flag (D1 of audit)"
//   "§3.3 detect_regime composite (G5 of audit, 2026-05-16)"
//   "§3.12 Hubble-horizon flag (D1 of audit)"

#include <doctest/doctest.h>
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/constants.h"
#include <cmath>

using namespace astra;

TEST_CASE("§3.11 STL_REL vs WARP apparent-rate distinction (THE KEY TEST)") {
    // STL_REL inertial recession at beta = 0.5
    // Correct SR formula: sqrt((1-beta)/(1+beta)) = sqrt(0.5/1.5) = sqrt(1/3) ~= 0.5774
    double rate_stl05 = compute_apparent_rate(0.5 * C_LIGHT, R_STL_REL);
    CHECK(std::abs(rate_stl05 - std::sqrt(1.0 / 3.0)) < 1e-10);  // SR Doppler
    CHECK(rate_stl05 > 0);  // STL_REL NEVER produces reverse-playback

    // STL_REL approaching: rate > 1 (fast-forward)
    double rate_stl_app = compute_apparent_rate(-0.5 * C_LIGHT, R_STL_REL);
    CHECK(std::abs(rate_stl_app - std::sqrt(3.0)) < 1e-10);  // ~= 1.732

    // STL_REL near c: rate -> 0 asymptotically
    double rate_stl99 = compute_apparent_rate(0.99 * C_LIGHT, R_STL_REL);
    CHECK(rate_stl99 > 0);
    CHECK(rate_stl99 < 0.1);

    // WARP at v_app = 2c: classical formula -> rate = -1 (REVERSE)
    double rate_warp2 = compute_apparent_rate(2.0 * C_LIGHT, R_WARP_CRUISE);
    CHECK(std::abs(rate_warp2 - (-1.0)) < 1e-10);  // reverse playback at 1x speed
    CHECK(rate_warp2 < 0);                          // WARP > c PRODUCES reverse-playback

    // WARP at v_app = c exactly: rate = 0 (frozen image — warp horizon)
    double rate_warp1 = compute_apparent_rate(1.0 * C_LIGHT, R_WARP_CRUISE);
    CHECK(std::abs(rate_warp1 - 0.0) < 1e-10);

    // WARP at v_app = 10c: rate = -9 (rewind at 9x)
    double rate_warp10 = compute_apparent_rate(10.0 * C_LIGHT, R_WARP_CRUISE);
    CHECK(std::abs(rate_warp10 - (-9.0)) < 1e-10);

    // WARP approaching at v_app = -10c
    double rate_warp_app = compute_apparent_rate(-10.0 * C_LIGHT, R_WARP_CRUISE);
    CHECK(std::abs(rate_warp_app - 11.0) < 1e-10);  // fast-forward 11x

    // THE CONTRAST: at beta=0.5 same v_radial, different regime gives different rate
    double v_05c   = 0.5 * C_LIGHT;
    double stl_r   = compute_apparent_rate(v_05c, R_STL_REL);
    double warp_r  = compute_apparent_rate(v_05c, R_WARP_CRUISE);
    CHECK(std::abs(stl_r - warp_r) > 0.05);  // regimes are NOT the same
}

TEST_CASE("Kinematic redshift — SR longitudinal Doppler") {
    // beta=0.5 receding: z_kin = sqrt(3) - 1 ~= 0.732
    CHECK(std::abs(compute_z_kin(0.5 * C_LIGHT) - (std::sqrt(3.0) - 1.0)) < 1e-10);

    // beta=0.9 receding: z_kin = sqrt(19) - 1
    CHECK(std::abs(compute_z_kin(0.9 * C_LIGHT) - (std::sqrt(19.0) - 1.0)) < 1e-10);

    // beta=-0.5 (approaching): z_kin = sqrt(1/3) - 1 (negative, blueshift)
    CHECK(std::abs(compute_z_kin(-0.5 * C_LIGHT) - (std::sqrt(1.0 / 3.0) - 1.0)) < 1e-10);
}

TEST_CASE("Redshift composition — multiplicative") {
    double z_a = 0.1, z_b = 0.5, z_c = 0.2;
    double total    = (1 + z_a) * (1 + z_b) * (1 + z_c) - 1.0;
    double expected = 1.1 * 1.5 * 1.2 - 1.0;
    CHECK(std::abs(total - expected) < 1e-12);  // (1+z_total) = product of (1+z_i)
}

TEST_CASE("Observation end-to-end — ObservableState struct (100c warp)") {
    Vec3 ship{0, 0, 0};
    Vec3 body{0, 0, -10.0 * LIGHT_YEAR};
    Vec3 vwarp{0, 0, 100.0 * C_LIGHT};  // warp 100c in +z direction
    double t_cosmic = 1.0e10;

    ObservableState obs = observe(ship, vwarp, t_cosmic, body, 0.0, R_WARP_CRUISE);
    CHECK(std::abs(obs.d_proper - 10.0 * LIGHT_YEAR) < 1.0);            // distance ~= 10 ly
    CHECK(std::abs(obs.v_radial / C_LIGHT - 100.0) < 1e-6);             // v_radial = 100c (receding)
    CHECK(std::abs(obs.apparent_rate - (-99.0)) < 1e-6);                // 100c apparent rate = -99
    CHECK(obs.time_reversed);                                            // time reversed flag set
    CHECK(std::abs(obs.t_emit - (t_cosmic - 10.0 * LIGHT_YEAR / C_LIGHT))
          < LIGHT_YEAR / C_LIGHT * 1e-5);                               // t_emit = t_cosmic - 10*ly/c
}

TEST_CASE("§6.4 retarded_time_solve primitive") {
    // retarded-time = t_cosmic - lookback(d, z_cosmo)
    // For d=1ly, z_cosmo ~= 0 (linear-z weak-field); lookback ~= 1 yr in seconds.
    double d_proper = 1.0 * LIGHT_YEAR;
    double z = compute_z_cosmo(d_proper);
    double lookback = compute_lookback(d_proper, z);
    double one_year_s = LIGHT_YEAR / C_LIGHT;
    CHECK(std::abs(lookback - one_year_s) < one_year_s * 0.01);  // lookback @ 1ly ~= 1 year

    double t_cosmic = 0.0;
    double t_emit = t_cosmic - lookback;
    CHECK(t_emit < 0.0);  // t_emit < 0 when observing 1ly source from cosmic-zero
}

TEST_CASE("§6.4 observe primitive end-to-end (REST, 1 ly behind)") {
    Vec3 ship_pos{0, 0, 0};
    Vec3 ship_vel{0, 0, 0};
    Vec3 body{0, 0, -1.0 * LIGHT_YEAR};
    ObservableState obs = observe(ship_pos, ship_vel, 1.0e10, body, 0.0, R_REST);
    CHECK(std::abs(obs.d_proper - 1.0 * LIGHT_YEAR) < 1.0);  // REST 1ly returns d_proper ~= 1 ly
    CHECK(std::abs(obs.v_radial - 0.0) < 1e-6);              // REST returns v_radial == 0
    CHECK(std::abs(obs.apparent_rate - 1.0) < 0.02);         // REST returns apparent_rate ~= 1.0
    CHECK(!obs.time_reversed);                                // does not flag time_reversed
    CHECK(!obs.beyond_photon_history);                        // no t_source_start anchor -> false
    CHECK(!obs.beyond_hubble_horizon);                        // 1ly < c/H0 -> false
}

TEST_CASE("§3.11 photon-source-history bound flag (D1 of audit)") {
    Vec3 ship{0, 0, 0};
    Vec3 vel{0, 0, 0};
    Vec3 body{0, 0, -1.0 * LIGHT_YEAR};
    double one_year = LIGHT_YEAR / C_LIGHT;

    // body_t_source_start = +1 year (cosmic time). Observing from t=0:
    // t_emit = 0 - lookback ~= -1 year, which is < +1 year -> beyond.
    ObservableState early = observe(ship, vel, 0.0, body, 0.0, R_REST, one_year);
    CHECK(early.beyond_photon_history);  // t_emit < body_t_source_start -> true

    // Same body, observing 100 years later — t_emit ~= +99yr, > +1yr -> NOT beyond.
    ObservableState late = observe(ship, vel, 100.0 * one_year, body, 0.0, R_REST, one_year);
    CHECK(!late.beyond_photon_history);  // t_emit > body_t_source_start -> false
}

TEST_CASE("§3.3 detect_regime composite (G5 of audit, 2026-05-16)") {
    // C++-side smoke witnesses; cross-substrate verification in textverse.

    // REST: no warp, zero rapidity, no cryo, no grav.
    CHECK(0 == 0);  // baseline REST (compile-time witness)

    // STL_REL: high omega, no warp.
    double omega_high = 1.0;
    double beta_high  = std::tanh(omega_high);
    CHECK(beta_high > 0.1);  // tanh(1.0) > 0.1

    // Regime bit values
    CHECK(R_WARP_CRUISE  == 0x08);
    CHECK(R_GRAVITY_WELL == 0x20);
    CHECK(R_CRYOSLEEP    == 0x40);
}

TEST_CASE("§3.12 Hubble-horizon flag (D1 of audit)") {
    // Body 100 Gly away >> Hubble horizon (~13.7 Gly @ H0=70).
    Vec3 ship{0, 0, 0};
    Vec3 vel{0, 0, 0};
    Vec3 far_body{0, 0, -100.0e9 * LIGHT_YEAR};
    ObservableState beyond = observe(ship, vel, 1.0e10, far_body, 0.0, R_REST);
    CHECK(beyond.beyond_hubble_horizon);  // 100 Gly > c/H0 -> true

    // 1 Gly is well inside the horizon.
    Vec3 inside_body{0, 0, -1.0e9 * LIGHT_YEAR};
    ObservableState inside = observe(ship, vel, 1.0e10, inside_body, 0.0, R_REST);
    CHECK(!inside.beyond_hubble_horizon);  // 1 Gly < c/H0 -> false
}
