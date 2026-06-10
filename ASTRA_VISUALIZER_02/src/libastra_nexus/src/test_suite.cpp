// test_suite.cpp - mirrors proto/astra_nexus.cpp namespace astra::test (lines 404-887)
// faithfully, then appends the 4 new Cherenkov assertions per DESIGN_SPEC §4.5.
//
// Canon strings preserved verbatim (including unicode) so a failing assertion in
// the mirror has a label-for-label match against canon, which makes cross-check
// against proto/astra_nexus.cpp trivial.
#include "astra_nexus/test_suite.h"
#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/cherenkov.h"
#include "astra_nexus/composition.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/coord.h"
#include "astra_nexus/kepler.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/rapidity.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/vec3.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace astra {
namespace test {

int passed = 0;
int failed = 0;

static void check(bool cond, const char* name) {
    if (cond) { passed++; std::printf("  [PASS] %s\n", name); }
    else      { failed++; std::printf("  [FAIL] %s\n", name); }
}

static void check_close(double actual, double expected, double tol, const char* name) {
    double diff = std::abs(actual - expected);
    bool ok = diff <= tol;
    if (ok) {
        passed++;
        std::printf("  [PASS] %s  (got %.6g, exp %.6g, diff %.3g)\n",
                    name, actual, expected, diff);
    } else {
        failed++;
        std::printf("  [FAIL] %s  (got %.6g, exp %.6g, diff %.3g, tol %.3g)\n",
                    name, actual, expected, diff, tol);
    }
}

static void section(const char* name) {
    std::printf("\n--- %s ---\n", name);
}

void run_all() {
    std::printf("\n========================= TEST SUITE =========================\n");

    // -------- AstraCoord --------
    section("AstraCoord (\xC2\xA7" "1.1)");
    {
        AstraCoord a{0, 0, 0, 0, 0, 0};
        AstraCoord b{0, 0, 0, 1000.0, 0, 0};
        check_close(astra_distance(a, b), 1000.0, 1e-9, "1km local distance");

        AstraCoord c{1, 0, 0, 0, 0, 0};
        check_close(astra_distance(a, c), SECTOR_SIZE, 1e-6, "1-sector distance");

        AstraCoord d{0, 0, 0, 600000.0, 0, 0};
        d.renormalize();
        check(d.sx == 1, "Renormalize rolls sx to 1");
        check_close(d.lx, -400000.0, 1e-9, "Renormalize lx after roll");

        d.lx += 1.5e6;
        d.renormalize();
        check_close(d.lx + (double)d.sx * SECTOR_SIZE, 2.1e6, 1e-9,
                    "Round-trip preserves total position");
    }

    // -------- Rapidity & v0.126 N1 lock --------
    section("Rapidity (\xC2\xA7" "3.7) - v0.126 N1 verification");
    {
        Rapidity rest{{0, 0, 0}};
        check_close(rest.gamma(), 1.0, 1e-12, "gamma at rest = 1");
        check_close(rest.beta(),  0.0, 1e-12, "beta at rest = 0");

        Rapidity r1{{0, 0, 1.0}};
        check_close(r1.gamma(), std::cosh(1.0), 1e-12, "gamma(omega=1) = cosh(1)");
        check_close(r1.beta(),  std::tanh(1.0), 1e-12, "beta(omega=1) = tanh(1)");

        Rapidity rmax{{0, 0, OMEGA_MAX}};
        double gamma_max = rmax.gamma();
        check(gamma_max > 9.0e6 && gamma_max < 1.1e7,
              "v0.126 LOCK: omega_max=16.811 -> gamma ~ 1e7");
        std::printf("         gamma at omega=16.811 = %.4e\n", gamma_max);

        double omega_v125 = std::atanh(0.99999999);
        double gamma_v125 = std::cosh(omega_v125);
        check(gamma_v125 > 7000.0 && gamma_v125 < 7200.0,
              "v0.125 BUG: arctanh(0.99999999) -> gamma ~ 7071 (NOT 1e7)");
        std::printf("         v0.125 N1: arctanh(.99999999) = omega=%.4f -> gamma=%.1f\n",
                    omega_v125, gamma_v125);
        std::printf("         shortfall factor: %.1fx less than claimed gamma_max\n",
                    1.0e7 / gamma_v125);

        double beta_at_max = std::tanh(OMEGA_MAX);
        double gamma_cosh  = std::cosh(OMEGA_MAX);
        double gamma_naive = 1.0 / std::sqrt(1.0 - beta_at_max * beta_at_max);
        double rel_err     = std::abs(gamma_cosh - gamma_naive) / gamma_cosh;
        std::printf("         gamma via cosh(omega):     %.6e (LOCKED PATH)\n", gamma_cosh);
        std::printf("         gamma via 1/sqrt(1-b^2):   %.6e (FORBIDDEN PATH)\n", gamma_naive);
        std::printf("         relative error:            %.3e\n", rel_err);
        check(rel_err > 1e-4,
              "Naive 1/sqrt(1-b^2) loses precision at omega=omega_max (justifies cosh discipline)");

        double g = 9.81;
        double year = 3.15576e7;
        Rapidity rs{{0, 0, 0}};
        Vec3 a_fwd{0, 0, g};
        rs = integrate_rapidity_step(rs, a_fwd, year);
        check_close(rs.omega(), g * year / C_LIGHT, 1e-10, "1g*tau -> omega = g*tau/c exact");

        Rapidity r_fast{{0, 0, 5.0}};
        Vec3 a_perp{0, g * 100.0, 0};
        Rapidity r_after = integrate_rapidity_step(r_fast, a_perp, year);
        check(r_after.beta() < 1.0,
              "Perpendicular thrust at high gamma: |v| < c by tanh-bound");
        check(r_after.zeta.y > 0,
              "Perpendicular thrust rotates zeta direction");

        Rapidity r_init{{0, 0, OMEGA_MAX - 0.1}};
        Vec3 a_strong{0, 0, 1.0e10};
        Rapidity r_clamped = integrate_rapidity_step(r_init, a_strong, 1.0);
        check_close(r_clamped.omega(), OMEGA_MAX, 1e-9, "Rapidity clamps at OMEGA_MAX");
    }

    // -------- Composition rule --------
    section("Composition rule (\xC2\xA7" "3.2 v0.126)");
    {
        check_close(dtau_dt_cosmic(0, 1.0, 1.0, false), 1.0, 1e-12,
                    "REST + no warp + no gravity: dtau/dt = 1");

        check_close(dtau_dt_cosmic(0, 1.0, 2.0, false), 0.5, 1e-12,
                    "STL gamma=2: dtau/dt = 0.5");

        std::vector<BHEntry> bhs;
        double rs = schwarzschild_r(10.0 * M_SUN);
        bhs.push_back({10.0 * M_SUN, {100.0 * rs, 0, 0}});
        double grav = compute_grav_factor(bhs, {0, 0, 0});
        double expected = std::sqrt(1.0 - rs / (100.0 * rs));
        check_close(grav, expected, 1e-12, "Grav factor at r = 100*r_s");

        bhs[0].pos = {1.0e15, 0, 0};
        double grav_far = compute_grav_factor(bhs, {0, 0, 0});
        check(grav_far > 0.999999 && grav_far <= 1.0,
              "Grav factor at very large r approaches 1 smoothly");

        check_close(f_warp_canon(0.0), 1.0, 1e-12, "f_warp(0) = 1");
        check_close(f_warp_canon(1.0), 0.5, 1e-12, "f_warp(1) = 0.5");
        check_close(f_warp_canon(0.5), 1.0 - 0.5 * 0.25, 1e-12,
                    "f_warp(0.5) = 1 - 0.5*0.25");

        double full = dtau_dt_cosmic(0.8, 0.9, 2.0, true);
        double expected_full = f_warp_canon(0.8) * 0.9 / 2.0;
        check_close(full, expected_full, 1e-12, "Full composition (W=0.8, grav=0.9, gamma=2)");
    }

    // -------- THE KEY TEST: STL_REL vs WARP regime distinction --------
    section("Observation: STL_REL vs WARP apparent-rate distinction");
    {
        double rate_stl05 = compute_apparent_rate(0.5 * C_LIGHT, R_STL_REL);
        check_close(rate_stl05, std::sqrt(1.0/3.0), 1e-10,
                    "STL_REL b=0.5 recede: rate = sqrt(1/3) ~ 0.5774 (SR Doppler)");
        check(rate_stl05 > 0,
              "STL_REL NEVER produces reverse-playback (rate > 0 always)");

        double rate_stl_app = compute_apparent_rate(-0.5 * C_LIGHT, R_STL_REL);
        check_close(rate_stl_app, std::sqrt(3.0), 1e-10,
                    "STL_REL b=-0.5 approach: rate = sqrt(3) ~ 1.732");

        double rate_stl99 = compute_apparent_rate(0.99 * C_LIGHT, R_STL_REL);
        check(rate_stl99 > 0 && rate_stl99 < 0.1,
              "STL_REL b=0.99: rate near 0 but still positive");

        double rate_warp2 = compute_apparent_rate(2.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp2, -1.0, 1e-10,
                    "WARP v_app=2c: rate = -1 (reverse playback @ 1x speed)");
        check(rate_warp2 < 0, "WARP > c PRODUCES reverse-playback");

        double rate_warp1 = compute_apparent_rate(1.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp1, 0.0, 1e-10,
                    "WARP v_app=c: rate = 0 (frozen image)");

        double rate_warp10 = compute_apparent_rate(10.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp10, -9.0, 1e-10,
                    "WARP v_app=10c: rate = -9 (rewind 9x)");

        double rate_warp_app = compute_apparent_rate(-10.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp_app, 11.0, 1e-10,
                    "WARP approach v_app=-10c: rate = +11 (fast-forward 11x)");

        double v_05c = 0.5 * C_LIGHT;
        double stl_rate = compute_apparent_rate(v_05c, R_STL_REL);
        double warp_rate = compute_apparent_rate(v_05c, R_WARP_CRUISE);
        std::printf("         CONTRAST at v_radial = 0.5c:\n");
        std::printf("           STL_REL  rate = %.6f (SR formula)\n", stl_rate);
        std::printf("           WARP     rate = %.6f (classical formula)\n", warp_rate);
        std::printf("           Spec must dispatch by regime - these are NOT the same.\n");
        check(std::abs(stl_rate - warp_rate) > 0.05,
              "STL_REL and WARP give meaningfully different rates at same v");
    }

    // -------- z_kin --------
    section("Kinematic redshift (SR longitudinal Doppler)");
    {
        check_close(compute_z_kin(0.5 * C_LIGHT),
                    std::sqrt(3.0) - 1.0, 1e-10,
                    "z_kin(b=0.5) = sqrt(3) - 1");
        check_close(compute_z_kin(0.9 * C_LIGHT),
                    std::sqrt(19.0) - 1.0, 1e-10,
                    "z_kin(b=0.9) = sqrt(19) - 1");
        check_close(compute_z_kin(-0.5 * C_LIGHT),
                    std::sqrt(1.0/3.0) - 1.0, 1e-10,
                    "z_kin(b=-0.5) = sqrt(1/3) - 1 (blueshift)");
    }

    // -------- Multiplicative z composition --------
    section("Redshift composition (multiplicative)");
    {
        double z_a = 0.1, z_b = 0.5, z_c = 0.2;
        double total = (1+z_a) * (1+z_b) * (1+z_c) - 1.0;
        double expected = 1.1 * 1.5 * 1.2 - 1.0;
        check_close(total, expected, 1e-12,
                    "(1+z_total) = (1+z_cosmo)(1+z_kin)(1+z_metric)");
    }

    // -------- End-to-end observation --------
    section("Observation end-to-end (ObservableState struct)");
    {
        Vec3 ship{0, 0, 0};
        Vec3 body{0, 0, -10.0 * LIGHT_YEAR};
        Vec3 vwarp{0, 0, 100.0 * C_LIGHT};
        double t_cosmic = 1.0e10;

        ObservableState obs = observe(ship, vwarp, t_cosmic, body, 0.0, R_WARP_CRUISE);
        check_close(obs.d_proper, 10.0 * LIGHT_YEAR, 1.0,
                    "Distance to body = 10 ly");
        check_close(obs.v_radial / C_LIGHT, 100.0, 1e-6,
                    "v_radial = 100c (receding at warp)");
        check_close(obs.apparent_rate, -99.0, 1e-6,
                    "WARP 100c apparent rate = -99");
        check(obs.time_reversed, "Time reversed flag set at WARP > c");
        check_close(obs.t_emit, t_cosmic - 10.0 * LIGHT_YEAR / C_LIGHT,
                    LIGHT_YEAR / C_LIGHT * 1e-5,
                    "t_emit = t_cosmic - 10*ly/c");
    }

    // -------- THE PAYOFF: Kepler-at-t_emit --------
    section("Kepler-at-t_emit: orbit reversal during warp egress");
    {
        Orbit earth_like{1.496e11, 0.0, 365.25 * 86400.0, 0.0};
        Vec3 body_pos{0, 0, -1.0 * LIGHT_YEAR};
        Vec3 vwarp{0, 0, 2.0 * C_LIGHT};

        double t0 = 1.0e10;
        ObservableState o0 = observe({0,0,0}, vwarp, t0, body_pos, 0.0, R_WARP_CRUISE);

        double dt = 30.0 * 86400.0;
        Vec3 ship_t1{0, 0, vwarp.z * dt};
        double t1 = t0 + dt;
        ObservableState o1 = observe(ship_t1, vwarp, t1, body_pos, 0.0, R_WARP_CRUISE);

        std::printf("         t0: ship at z=0,  t_emit=%.6e s\n", o0.t_emit);
        std::printf("         t1: ship at z=%.3g ly, t_emit=%.6e s\n",
                    ship_t1.z / LIGHT_YEAR, o1.t_emit);
        std::printf("         dt_cosmic=%+.4g d, dt_emit=%+.4g d\n",
                    (t1 - t0) / 86400.0, (o1.t_emit - o0.t_emit) / 86400.0);

        check(o1.t_emit < o0.t_emit,
              "t_emit DECREASES as ship warps superluminally away");
        check_close((o1.t_emit - o0.t_emit) / 86400.0, -30.0, 0.5,
                    "dt_emit ~ -dt_cosmic at v_app=2c (1x reverse)");

        double phase_0 = orbit_phase(earth_like, o0.t_emit);
        double phase_1 = orbit_phase(earth_like, o1.t_emit);
        double dphase = phase_1 - phase_0;
        while (dphase >  M_PI) dphase -= 2.0 * M_PI;
        while (dphase < -M_PI) dphase += 2.0 * M_PI;
        std::printf("         orbital phase at t_emit: %+.4f -> %+.4f rad (d=%+.4f)\n",
                    phase_0, phase_1, dphase);
        check(dphase < 0,
              "Orbital phase RUNS BACKWARD when sampled at t_emit (the effect)");
    }

    // -------- AstraCoord at billion-light-year scale --------
    section("AstraCoord at billion-light-year scale");
    {
        double d_target = 100.0e6 * LIGHT_YEAR;
        int64_t sectors = (int64_t)(d_target / SECTOR_SIZE);
        AstraCoord ship{0, 0, 0, 0, 0, 0};
        AstraCoord far_obj{sectors, 0, 0, 0, 0, 0};
        double d = astra_distance(ship, far_obj);
        check_close(d, (double)sectors * SECTOR_SIZE, 1.0,
                    "Distance at 100 Mly scale, m-precision");

        double max_reach_ly = ((double)INT64_MAX * SECTOR_SIZE) / LIGHT_YEAR;
        std::printf("         Maximum reach: %.3e ly = %.3f billion ly\n",
                    max_reach_ly, max_reach_ly / 1e9);
        check(max_reach_ly > 9.0e8,
              "AstraCoord reaches > 900M ly with sub-mm precision");
    }

    section("\xC2\xA7" "6.4 Narrator-LLM tool surface - kepler_at primitive");
    {
        Orbit orb{1.5e11, 0.0167, 3.156e7, 0.0};
        double phase_t0   = orbit_phase(orb, 0.0);
        double phase_full = orbit_phase(orb, orb.period);
        double diff = std::fmod(phase_full - phase_t0 + 4.0 * M_PI, 2.0 * M_PI);
        if (diff > M_PI) diff -= 2.0 * M_PI;
        check_close(diff, 0.0, 1e-6,
                    "kepler_at(t0+P) == kepler_at(t0) within 2pi");

        Orbit ecc{1.0e11, 0.5, 1.0e7, 0.0};
        double last = orbit_phase(ecc, 0.0);
        bool monotonic_or_unwrap = true;
        for (int i = 1; i <= 50; i++) {
            double t = (double)i * (ecc.period / 50.0);
            double cur = orbit_phase(ecc, t);
            if (cur < last && (last - cur) < M_PI) {
                monotonic_or_unwrap = false;
                break;
            }
            last = cur;
        }
        check(monotonic_or_unwrap,
              "kepler_at advances monotonically (mod 2pi) across one period");
    }

    section("\xC2\xA7" "6.4 Narrator-LLM tool surface - composition_rule_evaluate primitive");
    {
        double r1 = dtau_dt_cosmic(0.0, 1.0, 1.0, /*warp_active=*/false);
        check_close(r1, 1.0, 1e-12,
                    "composition_rule_evaluate(rest, no-grav, gamma=1) == 1.0");

        double r2 = dtau_dt_cosmic(0.0, 1.0, 2.0, false);
        check_close(r2, 0.5, 1e-12,
                    "composition_rule_evaluate(STL gamma=2) == 0.5");

        double r3 = dtau_dt_cosmic(1.0, 1.0, 1.0, /*warp_active=*/true);
        check_close(r3, 0.5, 1e-12,
                    "composition_rule_evaluate(W=1.0 cruise) == 0.5");

        double r4 = dtau_dt_cosmic(0.0, 0.7, 1.5, false);
        check_close(r4, 0.7 / 1.5, 1e-12,
                    "composition_rule_evaluate(STL+grav) composes multiplicatively");
    }

    section("\xC2\xA7" "6.4 Narrator-LLM tool surface - retarded_time_solve primitive");
    {
        double d_proper = 1.0 * LIGHT_YEAR;
        double z = compute_z_cosmo(d_proper);
        double lookback = compute_lookback(d_proper, z);
        double one_year_s = LIGHT_YEAR / C_LIGHT;
        check_close(lookback, one_year_s, one_year_s * 0.01,
                    "retarded_time lookback @ 1ly ~ 1 year (within 1%)");

        double t_cosmic = 0.0;
        double t_emit = t_cosmic - lookback;
        check(t_emit < 0.0,
              "retarded_time t_emit < 0 when observing 1ly source from cosmic-zero");
    }

    section("\xC2\xA7" "6.4 Narrator-LLM tool surface - observe primitive end-to-end");
    {
        Vec3 ship_pos{0, 0, 0};
        Vec3 ship_vel{0, 0, 0};
        Vec3 body{0, 0, -1.0 * LIGHT_YEAR};
        ObservableState obs = observe(ship_pos, ship_vel, 1.0e10, body, 0.0, R_REST);
        check_close(obs.d_proper, 1.0 * LIGHT_YEAR, 1.0,
                    "observe: REST 1ly returns d_proper ~ 1 ly");
        check_close(obs.v_radial, 0.0, 1e-6,
                    "observe: REST returns v_radial == 0");
        check_close(obs.apparent_rate, 1.0, 0.02,
                    "observe: REST returns apparent_rate ~ 1.0 (real-time)");
        check(!obs.time_reversed,
              "observe: REST does not flag time_reversed");
        check(!obs.beyond_photon_history,
              "observe: 1ly source with no t_source_start anchor -> beyond_photon_history=false");
        check(!obs.beyond_hubble_horizon,
              "observe: 1ly source within Hubble horizon -> beyond_hubble_horizon=false");
    }

    section("\xC2\xA7" "3.11 photon-source-history bound flag (D1 of audit)");
    {
        Vec3 ship{0, 0, 0};
        Vec3 vel{0, 0, 0};
        Vec3 body{0, 0, -1.0 * LIGHT_YEAR};
        double one_year = LIGHT_YEAR / C_LIGHT;
        ObservableState early = observe(ship, vel, 0.0, body, 0.0, R_REST, one_year);
        check(early.beyond_photon_history,
              "observe: t_emit < body_t_source_start -> beyond_photon_history=true");
        ObservableState late = observe(ship, vel, 100.0 * one_year, body, 0.0, R_REST, one_year);
        check(!late.beyond_photon_history,
              "observe: t_emit > body_t_source_start -> beyond_photon_history=false");
    }

    section("\xC2\xA7" "3.3 detect_regime composite (G5 of audit, 2026-05-16)");
    {
        check(0 == 0, "detect_regime baseline REST (compile-time witness)");

        double omega_high = 1.0;
        double beta_high  = std::tanh(omega_high);
        check(beta_high > 0.1,
              "detect_regime STL_REL threshold: tanh(1.0) > 0.1");

        check(R_WARP_CRUISE == 0x08,
              "detect_regime base regime bit value WARP_CRUISE == 0x08");
        check(R_GRAVITY_WELL == 0x20,
              "detect_regime base regime bit value GRAVITY_WELL == 0x20");
        check(R_CRYOSLEEP == 0x40,
              "detect_regime base regime bit value CRYOSLEEP == 0x40");
    }

    section("\xC2\xA7" "3.12 Hubble-horizon flag (D1 of audit)");
    {
        Vec3 ship{0, 0, 0};
        Vec3 vel{0, 0, 0};
        Vec3 far_body{0, 0, -100.0e9 * LIGHT_YEAR};
        ObservableState beyond = observe(ship, vel, 1.0e10, far_body, 0.0, R_REST);
        check(beyond.beyond_hubble_horizon,
              "observe: 100 Gly > c/H0 -> beyond_hubble_horizon=true");
        Vec3 inside_body{0, 0, -1.0e9 * LIGHT_YEAR};
        ObservableState inside = observe(ship, vel, 1.0e10, inside_body, 0.0, R_REST);
        check(!inside.beyond_hubble_horizon,
              "observe: 1 Gly < c/H0 -> beyond_hubble_horizon=false");
    }

    // -------- NEW IN MIRROR: Cherenkov angle (closes AUDIT 5D-F4) --------
    // Per DESIGN_SPEC §4.5; these 4 assertions are the V0 closure of the
    // canon gap. compute_cherenkov_angle does not exist in proto/astra_nexus.cpp.
    section("\xC2\xA7" "6 step 10 Cherenkov angle (NEW; AUDIT 5D-F4 closure)");
    {
        // Inactive case: n=1.5 (W=0.5), beta=0.3 -> n*beta=0.45 < 1 -> -1 sentinel.
        check_close(compute_cherenkov_angle(0.5, 0.3), -1.0, 1e-12,
                    "cherenkov inactive when n*beta <= 1 (W=0.5, beta=0.3)");

        // Degenerate exactly at threshold: n=2 (W=1), beta=0.5 -> n*beta=1 -> angle=acos(1)=0.
        double a_deg = compute_cherenkov_angle(1.0, 0.50001);
        check_close(a_deg, 0.0, 0.01,
                    "cherenkov angle ~ 0 at the n*beta -> 1+ threshold");

        // Canonical numerical case: n=2 (W=1), beta=0.9 -> n*beta=1.8 -> acos(1/1.8) ~ 0.9818 rad.
        double a_09 = compute_cherenkov_angle(1.0, 0.9);
        check_close(a_09, std::acos(1.0/1.8), 1e-9,
                    "cherenkov angle at W=1, beta=0.9 matches acos(1/(n*beta))");

        // Monotonicity: at fixed beta, higher W => higher n => higher n*beta
        // => smaller cos(theta_c) => LARGER theta_c. Cherenkov cone WIDENS
        // monotonically with W. (DESIGN_SPEC §4.5 originally asserted the
        // opposite; that text was a physics error caught during V0 build.)
        double a_W05 = compute_cherenkov_angle(0.5, 0.99);
        double a_W10 = compute_cherenkov_angle(1.0, 0.99);
        check(a_W10 > a_W05,
              "cherenkov cone widens monotonically as W increases at fixed beta");
    }

    std::printf("\n============== SUMMARY: %d passed, %d failed ==============\n",
                passed, failed);
}

} // namespace test
} // namespace astra
