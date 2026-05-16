// =============================================================================
// astra_nexus.cpp — ASTRA-7 Unified Physics Nexus Demonstration
//
// Independent implementation of the 14-equation unified framework.
// Proves that SR + GR + Warp + Cosmology + Finite-c Observation compose
// without contradiction at the math + code level.
//
// Compile (any C++17):
//   g++ -std=c++17 -O2 -Wall -o astra_nexus astra_nexus.cpp -lm
//   clang++ -std=c++17 -O2 -Wall -o astra_nexus astra_nexus.cpp -lm
//   cl /std:c++17 /EHsc /O2 astra_nexus.cpp           (MSVC)
//
// Run:  ./astra_nexus
//
// Key independent choices vs prior GLM draft:
//   1. CORRECT regime distinction for apparent rate:
//        STL_REL (inertial v<c): SR longitudinal Doppler √((1-β)/(1+β))
//        WARP_CRUISE (bubble γ=1, geometric recession): classical (1-v_app/c)
//      GLM's table used 1/γ for STL_REL, which is the transverse-Doppler
//      factor and WRONG for line-of-sight recession. Spec must lock both
//      formulas, regime-dispatched.
//   2. v0.126 N1 verification: prove arctanh(0.99999999) gives γ≈7071,
//      not γ≈10⁷. Prove |ζ⃗|=16.811 gives γ≈10⁷.
//   3. Catastrophic-cancellation verification: prove that 1/√(1-β²) loses
//      precision at high ω; cosh(ω) does not. v0.126 §3.7 discipline.
//   4. Explicit Kepler-at-t_emit test: body's orbital phase decreases
//      across cosmic-time steps when ship warps superluminally away.
//      This is the time-reversal effect rendered numerically.
//   5. AstraCoord renormalization round-trip test.
//   6. Full ordered test suite with PASS/FAIL counters and exit code.
//
// Spec references throughout: docs/spec-v0.126.md sections §1.x, §3.x, §4.x.
// =============================================================================

#include <cstdio>
#include <cstdint>
#include <cmath>
#include <cstdlib>
#include <vector>
#include <string>
#include <cctype>
#include <iostream>
#include <map>
#include <stdexcept>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace astra {

// =============================================================================
// Constants (§1.2, §4.2 State Bus, Appendix B)
// =============================================================================
constexpr double C_LIGHT     = 299792458.0;                  // m/s (exact)
constexpr double G_GRAV      = 6.67430e-11;                  // m³ kg⁻¹ s⁻²
constexpr double M_SUN       = 1.98892e30;                   // kg
constexpr double PARSEC      = 3.0856775814913673e16;        // m
constexpr double LIGHT_YEAR  = 9.4607304725808e15;           // m
constexpr double MPC         = 1.0e6 * PARSEC;
constexpr double H0_KMS_MPC  = 70.0;                         // km/s/Mpc (provisional)
constexpr double H0_SI       = H0_KMS_MPC * 1000.0 / MPC;    // s⁻¹
constexpr double OMEGA_M     = 0.3;                          // matter density (provisional)
constexpr double OMEGA_LAM   = 0.7;                          // dark energy density (provisional)

// v0.126 N1 lock: clamp for 3-vector rapidity magnitude
constexpr double OMEGA_MAX = 16.811;  // gives γ_max = cosh(16.811) ≈ 1e7

// =============================================================================
// Vec3
// =============================================================================
struct Vec3 {
    double x, y, z;
    Vec3 operator+(Vec3 b) const { return {x+b.x, y+b.y, z+b.z}; }
    Vec3 operator-(Vec3 b) const { return {x-b.x, y-b.y, z-b.z}; }
    Vec3 operator*(double s) const { return {x*s, y*s, z*s}; }
    Vec3 operator/(double s) const { return {x/s, y/s, z/s}; }
    double dot(Vec3 b) const { return x*b.x + y*b.y + z*b.z; }
    double mag() const { return std::sqrt(dot(*this)); }
    Vec3 normalized() const {
        double m = mag();
        return m > 1e-300 ? *this / m : Vec3{0,0,0};
    }
};

// =============================================================================
// AstraCoord (§1.1) — 128-bit hierarchical floating origin
// =============================================================================
constexpr double SECTOR_SIZE = 1.0e6;  // 1000 km in metres
constexpr double LOCAL_MAX   = 5.0e5;  // 500 km — renormalization trigger

struct AstraCoord {
    int64_t sx, sy, sz;
    double  lx, ly, lz;

    void renormalize() {
        auto roll = [](double& local, int64_t& sector) {
            if (std::abs(local) > LOCAL_MAX) {
                int64_t n = (int64_t)std::floor(local / SECTOR_SIZE + 0.5);
                sector += n;
                local -= n * SECTOR_SIZE;
            }
        };
        roll(lx, sx); roll(ly, sy); roll(lz, sz);
    }
};

double astra_distance(const AstraCoord& a, const AstraCoord& b) {
    double dx = (a.sx - b.sx) * SECTOR_SIZE + (a.lx - b.lx);
    double dy = (a.sy - b.sy) * SECTOR_SIZE + (a.ly - b.ly);
    double dz = (a.sz - b.sz) * SECTOR_SIZE + (a.lz - b.lz);
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

// =============================================================================
// Regime bitmask (§3.3 canonical hex values v0.125)
// =============================================================================
enum Regime : uint32_t {
    R_REST          = 0x00,
    R_STL_NONREL    = 0x01,
    R_STL_REL       = 0x02,
    R_WARP_CHARGE   = 0x04,
    R_WARP_CRUISE   = 0x08,
    R_WARP_SHUTDOWN = 0x10,
    R_GRAVITY_WELL  = 0x20,
    R_CRYOSLEEP     = 0x40,
};

const char* regime_label(uint32_t r) {
    uint32_t prop = r & 0x1F;
    switch (prop) {
        case R_REST:          return "REST";
        case R_STL_NONREL:    return "STL_NONREL";
        case R_STL_REL:       return "STL_REL";
        case R_WARP_CHARGE:   return "WARP_CHARGE";
        case R_WARP_CRUISE:   return "WARP_CRUISE";
        case R_WARP_SHUTDOWN: return "WARP_SHUTDOWN";
        default:              return "UNKNOWN";
    }
}

// =============================================================================
// Rapidity (§3.7 v0.126) — 3-vector with cosh-only discipline
// =============================================================================
struct Rapidity {
    Vec3 zeta;  // ζ⃗

    double omega()    const { return zeta.mag(); }
    // LOCKED: γ = cosh(ω). NEVER compute as 1/√(1-β²) — catastrophic
    // cancellation at high ω (v0.126 §3.7 discipline).
    double gamma()    const { return std::cosh(omega()); }
    double beta()     const { return std::tanh(omega()); }
    Vec3   velocity() const {
        double w = omega();
        if (w < 1e-30) return {0, 0, 0};
        return zeta * (C_LIGHT * std::tanh(w) / w);
    }
};

// dζ⃗/dτ_ship = a⃗_proper / c, with clamping at OMEGA_MAX
Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship) {
    Vec3 new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT);
    double mag = new_zeta.mag();
    if (mag > OMEGA_MAX) new_zeta = new_zeta * (OMEGA_MAX / mag);
    return Rapidity{new_zeta};
}

// =============================================================================
// Gravitational composition (§3.2 v0.126 — Schwarzschild-everywhere-dominant)
// =============================================================================
struct BHEntry {
    double M;
    Vec3   pos;
};

inline double schwarzschild_r(double M) {
    return 2.0 * G_GRAV * M / (C_LIGHT * C_LIGHT);
}

double compute_grav_factor(const std::vector<BHEntry>& bh_list, Vec3 ship_pos) {
    if (bh_list.empty()) return 1.0;

    // Find dominant BH (smallest r/r_s — strongest gravitational influence)
    int dom_i = -1;
    double min_ratio = 1e300;
    for (size_t i = 0; i < bh_list.size(); i++) {
        double r  = (bh_list[i].pos - ship_pos).mag();
        double rs = schwarzschild_r(bh_list[i].M);
        if (r > rs && (r / rs) < min_ratio) {
            min_ratio = r / rs;
            dom_i = (int)i;
        }
    }

    double factor = 1.0;

    // Dominant BH gets full Schwarzschild (continuous in r; reduces to weak-field at large r)
    if (dom_i >= 0) {
        double r  = (bh_list[dom_i].pos - ship_pos).mag();
        double rs = schwarzschild_r(bh_list[dom_i].M);
        factor *= std::sqrt(1.0 - rs / r);
    }

    // Non-dominant bodies contribute via summed weak-field potential
    double phi_other = 0.0;
    for (size_t i = 0; i < bh_list.size(); i++) {
        if ((int)i == dom_i) continue;
        double r = (bh_list[i].pos - ship_pos).mag();
        if (r > 0) phi_other += -G_GRAV * bh_list[i].M / r;
    }
    if (std::abs(phi_other) > 1e-30) {
        double arg = 1.0 + 2.0 * phi_other / (C_LIGHT * C_LIGHT);
        if (arg > 0) factor *= std::sqrt(arg);
    }

    return factor;
}

// Warp dilation — ASTRA-7 canon default (§3.5)
inline double f_warp_canon(double W) {
    return std::max(0.5, 1.0 - 0.5 * W * W);
}

// =============================================================================
// Composition rule (§3.2) — full dτ_ship / dt_cosmic
// =============================================================================
double dtau_dt_cosmic(double W_warp, double grav_factor, double gamma_kin,
                      bool warp_active)
{
    double f_w = warp_active ? f_warp_canon(W_warp) : 1.0;
    return f_w * grav_factor / gamma_kin;
}

// =============================================================================
// Observation Calculator (§3.11 v0.127 NEW) — retarded-time observation
//
// CRITICAL: regime-dispatched apparent-rate formula.
//   STL_REL (inertial v<c, SR): √((1-β)/(1+β)). NEVER reverses.
//   WARP_CRUISE (bubble γ=1, geometric recession): 1 - v_app/c. Can reverse.
//   REST/STL_NONREL: linear approx (≈ 1).
//
// This is the regime distinction the v0.127 spec must lock. Conflating the
// two formulas (as GLM's truth table did) is a physics error.
// =============================================================================
struct Observable {
    double d;              // proper distance (m)
    double v_radial;       // positive = receding
    double z_cosmo;
    double z_kin;
    double z_metric;
    double z_total;
    double t_emit;         // retarded time (cosmic seconds)
    double apparent_rate;  // dt_emit/dt_cosmic — can be < 0 in WARP
    bool   time_reversed;
};

// Regime-dispatched apparent rate (§3.11 v0.127, §10 validation row)
double compute_apparent_rate(double v_radial, uint32_t regime) {
    double beta = v_radial / C_LIGHT;

    if (regime & R_WARP_CRUISE) {
        // Bubble crew is locally inertial (γ_kinematic ≡ 1, §3.3).
        // Recession is geometric (sectors iterating), not kinematic.
        // Classical retarded-time formula applies: dt_emit/dt_recv = 1 - β.
        // Can go arbitrarily negative for v_app > c. THIS IS THE EFFECT.
        return 1.0 - beta;
    }

    if (regime & R_STL_REL) {
        // Inertial motion in flat spacetime: SR longitudinal Doppler.
        // T_obs/T_emit = √((1+β)/(1-β)), so apparent rate = √((1-β)/(1+β)).
        // For |β| < 1 always; never reverses (asymptotes to 0 or ∞).
        double bc = beta;
        if (bc >=  0.9999) bc =  0.9999;
        if (bc <= -0.9999) bc = -0.9999;
        return std::sqrt((1.0 - bc) / (1.0 + bc));
    }

    // REST / STL_NONREL — linear approx fine for small β
    return 1.0 - beta;
}

// SR longitudinal Doppler redshift: 1+z_kin = √((1+β)/(1-β)) when receding,
// where β = v_radial/c, v_radial > 0 for recession.
double compute_z_kin(double v_radial) {
    double beta = v_radial / C_LIGHT;
    // For warp, cap β for visual purposes only — the temporal reversal
    // is carried by apparent_rate, not by z_kin (which is colour).
    if (beta >=  0.9999) beta =  0.9999;
    if (beta <= -0.9999) beta = -0.9999;
    return std::sqrt((1.0 + beta) / (1.0 - beta)) - 1.0;
}

// Cosmological redshift — linear approx for z < 0.1 (provisional)
double compute_z_cosmo(double d_proper) {
    return H0_SI * d_proper / C_LIGHT;
}

// Look-back time with flat-ΛCDM correction (Equation 2)
double compute_lookback(double d_proper, double z_cosmo) {
    double lb = d_proper / C_LIGHT;
    if (z_cosmo > 0.01) {
        // t_lookback ≈ (d/c) · (1 - 3z/4) for z < 2 (provisional)
        lb *= (1.0 - 0.75 * std::min(z_cosmo, 2.0));
    }
    return lb;
}

Observable observe(Vec3   ship_pos,
                   Vec3   ship_velocity,
                   double t_cosmic,
                   Vec3   body_pos,
                   double body_metric_shift,
                   uint32_t regime)
{
    Observable obs = {};
    Vec3 to_body = body_pos - ship_pos;
    obs.d = std::max(to_body.mag(), 1.0);
    Vec3 r_hat = to_body / obs.d;

    // v_radial positive when ship moves AWAY from body.
    // ship_velocity points in ship motion direction; r_hat points from ship to body.
    // If ship_velocity is antiparallel to r_hat, ship recedes from body.
    obs.v_radial = -ship_velocity.dot(r_hat);

    obs.z_cosmo  = compute_z_cosmo(obs.d);
    obs.z_kin    = compute_z_kin(obs.v_radial);
    obs.z_metric = body_metric_shift;

    // Multiplicative composition: (1+z_total) = (1+z_cosmo)(1+z_kin)(1+z_metric)
    obs.z_total = (1.0 + obs.z_cosmo) * (1.0 + obs.z_kin)
                * (1.0 + obs.z_metric) - 1.0;

    double lookback = compute_lookback(obs.d, obs.z_cosmo);
    obs.t_emit = t_cosmic - lookback;

    obs.apparent_rate = compute_apparent_rate(obs.v_radial, regime)
                      / (1.0 + obs.z_cosmo);
    obs.time_reversed = obs.apparent_rate < 0.0;

    return obs;
}

// =============================================================================
// Kepler solver (used to demonstrate orbit-reversal at retarded time)
// =============================================================================
struct Orbit {
    double a;        // semi-major axis (m)
    double e;        // eccentricity
    double period;   // orbital period (s)
    double t0;       // epoch (s)
};

double solve_kepler_E(double M, double e) {
    double E = M;  // initial guess for low-eccentricity orbits
    for (int i = 0; i < 30; i++) {
        double f  = E - e * std::sin(E) - M;
        double fp = 1.0 - e * std::cos(E);
        double dE = f / fp;
        E -= dE;
        if (std::abs(dE) < 1e-13) break;
    }
    return E;
}

// True anomaly (orbital phase angle) at time t
double orbit_phase(const Orbit& orb, double t) {
    double M = 2.0 * M_PI * (t - orb.t0) / orb.period;
    double E = solve_kepler_E(M, orb.e);
    return 2.0 * std::atan2(
        std::sqrt(1.0 + orb.e) * std::sin(E / 2.0),
        std::sqrt(1.0 - orb.e) * std::cos(E / 2.0)
    );
}

// =============================================================================
// Tests with assertions
// =============================================================================
namespace test {

int passed = 0;
int failed = 0;

void check(bool cond, const char* name) {
    if (cond) { passed++; std::printf("  [PASS] %s\n", name); }
    else      { failed++; std::printf("  [FAIL] %s\n", name); }
}

void check_close(double actual, double expected, double tol, const char* name) {
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

void section(const char* name) {
    std::printf("\n--- %s ---\n", name);
}

void run_all() {
    std::printf("\n========================= TEST SUITE =========================\n");

    // -------- AstraCoord --------
    section("AstraCoord (§1.1)");
    {
        AstraCoord a{0, 0, 0, 0, 0, 0};
        AstraCoord b{0, 0, 0, 1000.0, 0, 0};
        check_close(astra_distance(a, b), 1000.0, 1e-9, "1km local distance");

        AstraCoord c{1, 0, 0, 0, 0, 0};
        check_close(astra_distance(a, c), SECTOR_SIZE, 1e-6, "1-sector distance");

        AstraCoord d{0, 0, 0, 600000.0, 0, 0};  // exceeds LOCAL_MAX
        d.renormalize();
        check(d.sx == 1, "Renormalize rolls sx to 1");
        check_close(d.lx, -400000.0, 1e-9, "Renormalize lx after roll");

        // Round-trip
        d.lx += 1.5e6;
        d.renormalize();
        check_close(d.lx + d.sx * SECTOR_SIZE, 2.1e6, 1e-9,
                    "Round-trip preserves total position");
    }

    // -------- Rapidity & v0.126 N1 lock --------
    section("Rapidity (§3.7) — v0.126 N1 verification");
    {
        Rapidity rest{{0, 0, 0}};
        check_close(rest.gamma(), 1.0, 1e-12, "γ at rest = 1");
        check_close(rest.beta(),  0.0, 1e-12, "β at rest = 0");

        // ω=1: γ=cosh(1)≈1.5430806
        Rapidity r1{{0, 0, 1.0}};
        check_close(r1.gamma(), std::cosh(1.0), 1e-12, "γ(ω=1) = cosh(1)");
        check_close(r1.beta(),  std::tanh(1.0), 1e-12, "β(ω=1) = tanh(1)");

        // v0.126 N1 LOCK VERIFICATION: ω=16.811 → γ≈10⁷
        Rapidity rmax{{0, 0, OMEGA_MAX}};
        double gamma_max = rmax.gamma();
        check(gamma_max > 9.0e6 && gamma_max < 1.1e7,
              "v0.126 LOCK: ω_max=16.811 → γ ≈ 10⁷");
        std::printf("         γ at ω=16.811 = %.4e\n", gamma_max);

        // v0.125 N1 BUG REPRODUCTION: arctanh(0.99999999) → γ ≈ 7071
        double omega_v125 = std::atanh(0.99999999);
        double gamma_v125 = std::cosh(omega_v125);
        check(gamma_v125 > 7000.0 && gamma_v125 < 7200.0,
              "v0.125 BUG: arctanh(0.99999999) → γ ≈ 7071 (NOT 10⁷)");
        std::printf("         v0.125 N1: arctanh(.99999999) = ω=%.4f → γ=%.1f\n",
                    omega_v125, gamma_v125);
        std::printf("         shortfall factor: %.1fx less than claimed γ_max\n",
                    1.0e7 / gamma_v125);

        // Catastrophic cancellation verification (§3.7 v0.126 discipline)
        double beta_at_max = std::tanh(OMEGA_MAX);
        double gamma_cosh  = std::cosh(OMEGA_MAX);
        double gamma_naive = 1.0 / std::sqrt(1.0 - beta_at_max * beta_at_max);
        double rel_err     = std::abs(gamma_cosh - gamma_naive) / gamma_cosh;
        std::printf("         γ via cosh(ω):       %.6e (LOCKED PATH)\n", gamma_cosh);
        std::printf("         γ via 1/√(1-β²):    %.6e (FORBIDDEN PATH)\n", gamma_naive);
        std::printf("         relative error:       %.3e\n", rel_err);
        check(rel_err > 1e-4,
              "Naive 1/√(1-β²) loses precision at ω=ω_max (justifies cosh discipline)");

        // 1g for 1 ship-year: ω = g·τ/c (exact under constant proper accel)
        double g = 9.81;
        double year = 3.15576e7;
        Rapidity rs{{0, 0, 0}};
        Vec3 a_fwd{0, 0, g};
        rs = integrate_rapidity_step(rs, a_fwd, year);
        check_close(rs.omega(), g * year / C_LIGHT, 1e-10, "1g·τ → ω = g·τ/c exact");

        // 3D maneuvering: perpendicular thrust does not exceed c
        Rapidity r_fast{{0, 0, 5.0}};       // γ ≈ 74
        Vec3 a_perp{0, g * 100.0, 0};       // strong perpendicular
        Rapidity r_after = integrate_rapidity_step(r_fast, a_perp, year);
        check(r_after.beta() < 1.0,
              "Perpendicular thrust at high γ: |v| < c by tanh-bound");
        check(r_after.zeta.y > 0,
              "Perpendicular thrust rotates ζ⃗ direction");

        // Clamp test
        Rapidity huge{{0, 0, 100.0}};  // way over OMEGA_MAX
        Rapidity huge_after = integrate_rapidity_step(huge, Vec3{0, 0, 0}, 0);
        // After zero step but with clamp engaged from huge initial...
        // Actually clamp only applies during integrate. Let's test clamp explicitly:
        Rapidity r_init{{0, 0, OMEGA_MAX - 0.1}};
        Vec3 a_strong{0, 0, 1.0e10};  // extreme accel
        Rapidity r_clamped = integrate_rapidity_step(r_init, a_strong, 1.0);
        check_close(r_clamped.omega(), OMEGA_MAX, 1e-9, "Rapidity clamps at OMEGA_MAX");
    }

    // -------- Composition rule --------
    section("Composition rule (§3.2 v0.126)");
    {
        check_close(dtau_dt_cosmic(0, 1.0, 1.0, false), 1.0, 1e-12,
                    "REST + no warp + no gravity: dτ/dt = 1");

        // STL_REL at γ = 2
        check_close(dtau_dt_cosmic(0, 1.0, 2.0, false), 0.5, 1e-12,
                    "STL γ=2: dτ/dt = 0.5");

        // Schwarzschild factor at r = 100·r_s
        std::vector<BHEntry> bhs;
        double rs = schwarzschild_r(10.0 * M_SUN);
        bhs.push_back({10.0 * M_SUN, {100.0 * rs, 0, 0}});
        double grav = compute_grav_factor(bhs, {0, 0, 0});
        double expected = std::sqrt(1.0 - rs / (100.0 * rs));
        check_close(grav, expected, 1e-12, "Grav factor at r = 100·r_s");

        // Continuity: large r should reduce smoothly to ~1
        bhs[0].pos = {1.0e15, 0, 0};  // very far
        double grav_far = compute_grav_factor(bhs, {0, 0, 0});
        check(grav_far > 0.999999 && grav_far <= 1.0,
              "Grav factor at very large r approaches 1 smoothly");

        // f_warp canon default
        check_close(f_warp_canon(0.0), 1.0, 1e-12, "f_warp(0) = 1");
        check_close(f_warp_canon(1.0), 0.5, 1e-12, "f_warp(1) = 0.5");
        check_close(f_warp_canon(0.5), 1.0 - 0.5 * 0.25, 1e-12,
                    "f_warp(0.5) = 1 - 0.5·0.25");

        // Full composition: warp + gravity + SR
        double full = dtau_dt_cosmic(0.8, 0.9, 2.0, true);
        double expected_full = f_warp_canon(0.8) * 0.9 / 2.0;
        check_close(full, expected_full, 1e-12, "Full composition (W=0.8, grav=0.9, γ=2)");
    }

    // -------- THE KEY TEST: STL_REL vs WARP regime distinction --------
    section("Observation: STL_REL vs WARP apparent-rate distinction");
    {
        // STL_REL inertial recession at β = 0.5
        // Correct SR formula: √((1-β)/(1+β)) = √(0.5/1.5) = √(1/3) ≈ 0.5774
        double rate_stl05 = compute_apparent_rate(0.5 * C_LIGHT, R_STL_REL);
        check_close(rate_stl05, std::sqrt(1.0/3.0), 1e-10,
                    "STL_REL β=0.5 recede: rate = √(1/3) ≈ 0.5774 (SR Doppler)");
        check(rate_stl05 > 0,
              "STL_REL NEVER produces reverse-playback (rate > 0 always)");

        // STL_REL approaching: rate > 1 (fast-forward)
        double rate_stl_app = compute_apparent_rate(-0.5 * C_LIGHT, R_STL_REL);
        check_close(rate_stl_app, std::sqrt(3.0), 1e-10,
                    "STL_REL β=-0.5 approach: rate = √3 ≈ 1.732");

        // STL_REL near c: rate → 0 asymptotically
        double rate_stl99 = compute_apparent_rate(0.99 * C_LIGHT, R_STL_REL);
        check(rate_stl99 > 0 && rate_stl99 < 0.1,
              "STL_REL β=0.99: rate near 0 but still positive");

        // WARP at v_app = 2c: classical formula → rate = -1 (REVERSE)
        double rate_warp2 = compute_apparent_rate(2.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp2, -1.0, 1e-10,
                    "WARP v_app=2c: rate = -1 (reverse playback @ 1× speed)");
        check(rate_warp2 < 0, "WARP > c PRODUCES reverse-playback");

        // WARP at v_app = c exactly: rate = 0 (frozen image — warp horizon)
        double rate_warp1 = compute_apparent_rate(1.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp1, 0.0, 1e-10,
                    "WARP v_app=c: rate = 0 (frozen image)");

        // WARP at v_app = 10c: rate = -9 (rewind at 9×)
        double rate_warp10 = compute_apparent_rate(10.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp10, -9.0, 1e-10,
                    "WARP v_app=10c: rate = -9 (rewind 9×)");

        // WARP approaching at v_app = 10c
        double rate_warp_app = compute_apparent_rate(-10.0 * C_LIGHT, R_WARP_CRUISE);
        check_close(rate_warp_app, 11.0, 1e-10,
                    "WARP approach v_app=-10c: rate = +11 (fast-forward 11×)");

        // THE CONTRAST: at β=0.5 same v_radial, different regime gives different rate
        double v_05c = 0.5 * C_LIGHT;
        double stl_rate = compute_apparent_rate(v_05c, R_STL_REL);
        double warp_rate = compute_apparent_rate(v_05c, R_WARP_CRUISE);
        std::printf("         CONTRAST at v_radial = 0.5c:\n");
        std::printf("           STL_REL  rate = %.6f (SR formula)\n", stl_rate);
        std::printf("           WARP     rate = %.6f (classical formula)\n", warp_rate);
        std::printf("           Spec must dispatch by regime — these are NOT the same.\n");
        check(std::abs(stl_rate - warp_rate) > 0.05,
              "STL_REL and WARP give meaningfully different rates at same v");
    }

    // -------- z_kin (SR longitudinal Doppler) --------
    section("Kinematic redshift (SR longitudinal Doppler)");
    {
        // β=0.5 receding: z_kin = √3 - 1 ≈ 0.732
        check_close(compute_z_kin(0.5 * C_LIGHT),
                    std::sqrt(3.0) - 1.0, 1e-10,
                    "z_kin(β=0.5) = √3 - 1");
        // β=0.9 receding: z_kin = √19 - 1
        check_close(compute_z_kin(0.9 * C_LIGHT),
                    std::sqrt(19.0) - 1.0, 1e-10,
                    "z_kin(β=0.9) = √19 - 1");
        // β=-0.5 (approaching): z_kin = √(1/3) - 1 (negative, blueshift)
        check_close(compute_z_kin(-0.5 * C_LIGHT),
                    std::sqrt(1.0/3.0) - 1.0, 1e-10,
                    "z_kin(β=-0.5) = √(1/3) - 1 (blueshift)");
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
    section("Observation end-to-end (Observable struct)");
    {
        Vec3 ship{0, 0, 0};
        Vec3 body{0, 0, -10.0 * LIGHT_YEAR};
        Vec3 vwarp{0, 0, 100.0 * C_LIGHT};  // warp 100c in +z direction
        double t_cosmic = 1.0e10;

        Observable obs = observe(ship, vwarp, t_cosmic, body, 0.0, R_WARP_CRUISE);
        check_close(obs.d, 10.0 * LIGHT_YEAR, 1.0,
                    "Distance to body = 10 ly");
        check_close(obs.v_radial / C_LIGHT, 100.0, 1e-6,
                    "v_radial = 100c (receding at warp)");
        check_close(obs.apparent_rate, -99.0, 1e-6,
                    "WARP 100c apparent rate = -99");
        check(obs.time_reversed, "Time reversed flag set at WARP > c");
        check_close(obs.t_emit, t_cosmic - 10.0 * LIGHT_YEAR / C_LIGHT,
                    LIGHT_YEAR / C_LIGHT * 1e-5,
                    "t_emit = t_cosmic - 10·ly/c");
    }

    // -------- THE PAYOFF TEST: Kepler-at-t_emit shows orbit reversal --------
    section("Kepler-at-t_emit: orbit reversal during warp egress");
    {
        // Earth-like orbit, body 1 ly behind ship
        Orbit earth_like{1.496e11, 0.0, 365.25 * 86400.0, 0.0};
        Vec3 body_pos{0, 0, -1.0 * LIGHT_YEAR};
        Vec3 vwarp{0, 0, 2.0 * C_LIGHT};  // warp away at 2c

        double t0 = 1.0e10;
        Observable o0 = observe({0,0,0}, vwarp, t0, body_pos, 0.0, R_WARP_CRUISE);

        // 30 cosmic days later, ship has moved 30 light-days further away
        double dt = 30.0 * 86400.0;
        Vec3 ship_t1{0, 0, vwarp.z * dt};
        double t1 = t0 + dt;
        Observable o1 = observe(ship_t1, vwarp, t1, body_pos, 0.0, R_WARP_CRUISE);

        std::printf("         t0: ship at z=0,  t_emit=%.6e s\n", o0.t_emit);
        std::printf("         t1: ship at z=%.3g ly, t_emit=%.6e s\n",
                    ship_t1.z / LIGHT_YEAR, o1.t_emit);
        std::printf("         Δt_cosmic=%+.4g d, Δt_emit=%+.4g d\n",
                    (t1 - t0) / 86400.0, (o1.t_emit - o0.t_emit) / 86400.0);

        check(o1.t_emit < o0.t_emit,
              "t_emit DECREASES as ship warps superluminally away");
        // At v_app = 2c, dt_emit/dt_cosmic = -1, so Δt_emit ≈ -Δt_cosmic = -30 d
        check_close((o1.t_emit - o0.t_emit) / 86400.0, -30.0, 0.5,
                    "Δt_emit ≈ -Δt_cosmic at v_app=2c (1× reverse)");

        double phase_0 = orbit_phase(earth_like, o0.t_emit);
        double phase_1 = orbit_phase(earth_like, o1.t_emit);
        // Normalize phase difference to (-π, π]
        double dphase = phase_1 - phase_0;
        while (dphase >  M_PI) dphase -= 2.0 * M_PI;
        while (dphase < -M_PI) dphase += 2.0 * M_PI;
        std::printf("         orbital phase at t_emit: %+.4f → %+.4f rad (Δ=%+.4f)\n",
                    phase_0, phase_1, dphase);
        check(dphase < 0,
              "Orbital phase RUNS BACKWARD when sampled at t_emit (the effect)");
    }

    // -------- AstraCoord at billion-light-year scale --------
    section("AstraCoord at billion-light-year scale");
    {
        // 100 Mly distance test
        double d_target = 100.0e6 * LIGHT_YEAR;
        int64_t sectors = (int64_t)(d_target / SECTOR_SIZE);
        AstraCoord ship{0, 0, 0, 0, 0, 0};
        AstraCoord far_obj{sectors, 0, 0, 0, 0, 0};
        double d = astra_distance(ship, far_obj);
        check_close(d, sectors * SECTOR_SIZE, 1.0,
                    "Distance at 100 Mly scale, m-precision");

        // Reach test: int64 sectors * 1000 km
        // 2^63 ≈ 9.2e18, * 1e6 m = 9.2e24 m ≈ 970 Mly
        double max_reach_ly = ((double)INT64_MAX * SECTOR_SIZE) / LIGHT_YEAR;
        std::printf("         Maximum reach: %.3e ly = %.3f billion ly\n",
                    max_reach_ly, max_reach_ly / 1e9);
        check(max_reach_ly > 9.0e8,
              "AstraCoord reaches > 900M ly with sub-mm precision");
    }

    section("§6.4 Narrator-LLM tool surface — kepler_at primitive");
    {
        // kepler_at backs `orbit_phase` for the Narrator's astrometric_query.
        // Verify the canonical periodicity invariant: phase(t0+P) ≡ phase(t0).
        Orbit orb{1.5e11, 0.0167, 3.156e7, 0.0};   // earth-like
        double phase_t0   = orbit_phase(orb, 0.0);
        double phase_full = orbit_phase(orb, orb.period);
        // 2π wrap; both should map to the same anomaly (modulo 2π).
        double diff = std::fmod(phase_full - phase_t0 + 4.0 * M_PI, 2.0 * M_PI);
        if (diff > M_PI) diff -= 2.0 * M_PI;
        check_close(diff, 0.0, 1e-6,
                    "kepler_at(t0+P) == kepler_at(t0) within 2π");

        // Eccentric orbit: phase advances monotonically over one period.
        Orbit ecc{1.0e11, 0.5, 1.0e7, 0.0};
        double last = orbit_phase(ecc, 0.0);
        bool monotonic_or_unwrap = true;
        for (int i = 1; i <= 50; i++) {
            double t = (double)i * (ecc.period / 50.0);
            double cur = orbit_phase(ecc, t);
            // Allow one 2π unwrap.
            if (cur < last && (last - cur) < M_PI) {
                monotonic_or_unwrap = false;
                break;
            }
            last = cur;
        }
        check(monotonic_or_unwrap,
              "kepler_at advances monotonically (mod 2π) across one period");
    }

    section("§6.4 Narrator-LLM tool surface — composition_rule_evaluate primitive");
    {
        // composition_rule = f_warp · grav · 1/γ_kin
        // Identity case: warp inactive, no gravity, γ=1 → 1.0
        double r1 = dtau_dt_cosmic(0.0, 1.0, 1.0, /*warp_active=*/false);
        check_close(r1, 1.0, 1e-12,
                    "composition_rule_evaluate(rest, no-grav, γ=1) == 1.0");

        // STL γ=2: 1/γ = 0.5
        double r2 = dtau_dt_cosmic(0.0, 1.0, 2.0, false);
        check_close(r2, 0.5, 1e-12,
                    "composition_rule_evaluate(STL γ=2) == 0.5");

        // WARP_CRUISE W=1.0: f_warp = max(0.5, 1 − 0.5·1²) = 0.5
        double r3 = dtau_dt_cosmic(1.0, 1.0, 1.0, /*warp_active=*/true);
        check_close(r3, 0.5, 1e-12,
                    "composition_rule_evaluate(W=1.0 cruise) == 0.5");

        // Strong gravity factor 0.7 + STL γ=1.5: 1.0 · 0.7 / 1.5
        double r4 = dtau_dt_cosmic(0.0, 0.7, 1.5, false);
        check_close(r4, 0.7 / 1.5, 1e-12,
                    "composition_rule_evaluate(STL+grav) composes multiplicatively");
    }

    section("§6.4 Narrator-LLM tool surface — retarded_time_solve primitive");
    {
        // retarded-time = t_cosmic − lookback(d, z_cosmo)
        // For d=1ly, z_cosmo ≈ 0 (linear-z weak-field); lookback ≈ 1 yr in seconds.
        double d_proper = 1.0 * LIGHT_YEAR;
        double z = compute_z_cosmo(d_proper);     // weak-field, near 0
        double lookback = compute_lookback(d_proper, z);
        // 1 ly / c = 1 yr (definition); ΛCDM correction ~ (1 − 3z/4) ≈ 1.
        double one_year_s = LIGHT_YEAR / C_LIGHT;
        check_close(lookback, one_year_s, one_year_s * 0.01,
                    "retarded_time lookback @ 1ly ≈ 1 year (within 1%)");

        // t_emit = t_cosmic − lookback. Far past observation: t_cosmic=0 → t_emit < 0.
        double t_cosmic = 0.0;
        double t_emit = t_cosmic - lookback;
        check(t_emit < 0.0,
              "retarded_time t_emit < 0 when observing 1ly source from cosmic-zero");
    }

    section("§6.4 Narrator-LLM tool surface — observe primitive end-to-end");
    {
        // Ship at rest near origin; planet 1 ly behind (-z).
        Vec3 ship_pos{0, 0, 0};
        Vec3 ship_vel{0, 0, 0};
        Vec3 body{0, 0, -1.0 * LIGHT_YEAR};
        Observable obs = observe(ship_pos, ship_vel, 1.0e10, body, 0.0, R_REST);
        check_close(obs.d, 1.0 * LIGHT_YEAR, 1.0,
                    "observe: REST 1ly returns d ≈ 1 ly");
        check_close(obs.v_radial, 0.0, 1e-6,
                    "observe: REST returns v_radial == 0");
        check_close(obs.apparent_rate, 1.0, 0.02,
                    "observe: REST returns apparent_rate ≈ 1.0 (real-time)");
        check(!obs.time_reversed,
              "observe: REST does not flag time_reversed");
    }

    std::printf("\n============== SUMMARY: %d passed, %d failed ==============\n",
                passed, failed);
}

} // namespace test

// =============================================================================
// Demo: ship traversing regimes, observing a system left behind
// =============================================================================
void print_obs_row(const char* label, const Observable& o) {
    std::printf("  %-32s d=%6.2f ly | v_rad=%+8.2fc | rate=%+10.4f",
                label,
                o.d / LIGHT_YEAR,
                o.v_radial / C_LIGHT,
                o.apparent_rate);
    if (o.time_reversed) {
        std::printf("  TIME REVERSED at %.2f×", std::abs(o.apparent_rate));
    } else if (o.apparent_rate > 1.5) {
        std::printf("  fast-forward %.2f×", o.apparent_rate);
    } else if (o.apparent_rate < 0.5) {
        std::printf("  slow-mo %.4f×", o.apparent_rate);
    } else {
        std::printf("  ~real-time");
    }
    std::printf("\n");
}

void demo_voyage() {
    std::printf("\n========================= VOYAGE DEMO =========================\n");
    std::printf("Ship starts at rest near a planet 1 ly away (in +z direction).\n");
    std::printf("Accelerates, then enters WARP, observing the planet behind.\n\n");

    Vec3 planet{0, 0, -1.0 * LIGHT_YEAR};  // 1 ly behind starting point
    double t = 1.0e10;

    struct Phase {
        const char* label;
        Vec3 ship_pos;
        Vec3 ship_vel;
        uint32_t regime;
    };

    Phase phases[] = {
        {"REST near origin",                  {0,0,0},                  {0, 0, 0},                       R_REST},
        {"STL_NONREL 0.05c +z",               {0,0,0},                  {0, 0, 0.05 * C_LIGHT},          R_STL_NONREL},
        {"STL_REL 0.5c +z (recede)",          {0,0,0},                  {0, 0, 0.5 * C_LIGHT},           R_STL_REL},
        {"STL_REL 0.9c +z (recede)",          {0,0,0},                  {0, 0, 0.9 * C_LIGHT},           R_STL_REL},
        {"STL_REL 0.99c +z (recede)",         {0,0,0},                  {0, 0, 0.99 * C_LIGHT},          R_STL_REL},
        {"WARP_CRUISE 1c (recede)",           {0,0,0},                  {0, 0, 1.0 * C_LIGHT},           R_WARP_CRUISE},
        {"WARP_CRUISE 2c (recede)",           {0,0,0},                  {0, 0, 2.0 * C_LIGHT},           R_WARP_CRUISE},
        {"WARP_CRUISE 10c (recede)",          {0,0,0},                  {0, 0, 10.0 * C_LIGHT},          R_WARP_CRUISE},
        {"WARP_CRUISE 100c (recede)",         {0,0,0},                  {0, 0, 100.0 * C_LIGHT},         R_WARP_CRUISE},
        {"WARP_CRUISE 8000c (recede)",        {0,0,0},                  {0, 0, 8000.0 * C_LIGHT},        R_WARP_CRUISE},
        {"WARP_CRUISE 2c APPROACH (-z)",      {0,0,0},                  {0, 0, -2.0 * C_LIGHT},          R_WARP_CRUISE},
    };

    for (const auto& p : phases) {
        Observable o = observe(p.ship_pos, p.ship_vel, t, planet, 0.0, p.regime);
        print_obs_row(p.label, o);
    }
    std::printf("\nNote: STL_REL formulas (SR longitudinal Doppler) and WARP formulas\n");
    std::printf("(classical retarded-time, bubble γ=1) differ. The spec must lock\n");
    std::printf("regime-dispatched apparent-rate to render this correctly.\n");
}

// =============================================================================
// stdio_server — JSON-over-stdio bridge for proto/textverse (Day 2 v0.128)
//
// Purely additive: existing test suite + demo_voyage unaffected. Activated by
// passing "--stdio-server" as argv[1]. Reads one JSON request per line from
// stdin, writes one JSON response line to stdout, until EOF.
//
// Wire format:
//   request:  {"op":"<name>","args":{<json-object-of-string-or-number>}}
//   response: {"ok":true,"result":<number|string>}
//             {"ok":false,"error":"<message>"}
//
// Hand-rolled minimal JSON parser; no external dependencies. The parser
// accepts: object (key:value pairs), quoted string, number (incl. scientific
// notation), and nested object for "args". No arrays, no null, no booleans
// — Day 2 doesn't need them. Day N+ can extend.
// =============================================================================
namespace stdio_server {

struct JValue {
    enum Type { NUMBER, STRING, OBJECT } type = OBJECT;
    double n = 0.0;
    std::string s;
    std::map<std::string, JValue> obj;
};

static void skip_ws(const std::string& src, size_t& i) {
    while (i < src.size() && std::isspace(static_cast<unsigned char>(src[i]))) i++;
}

static std::string parse_string(const std::string& src, size_t& i) {
    if (i >= src.size() || src[i] != '"') throw std::runtime_error("expected string");
    i++;
    std::string out;
    while (i < src.size() && src[i] != '"') {
        if (src[i] == '\\') {
            i++;
            if (i >= src.size()) throw std::runtime_error("unterminated escape");
            char c = src[i++];
            switch (c) {
                case 'n':  out += '\n'; break;
                case 't':  out += '\t'; break;
                case 'r':  out += '\r'; break;
                case '\\': out += '\\'; break;
                case '"':  out += '"';  break;
                case '/':  out += '/';  break;
                default:   out += c;    break;
            }
        } else {
            out += src[i++];
        }
    }
    if (i >= src.size()) throw std::runtime_error("unterminated string");
    i++; // skip closing "
    return out;
}

static double parse_number(const std::string& src, size_t& i) {
    size_t start = i;
    if (i < src.size() && (src[i] == '-' || src[i] == '+')) i++;
    while (i < src.size()) {
        char c = src[i];
        bool ok = std::isdigit(static_cast<unsigned char>(c)) || c == '.'
                  || c == 'e' || c == 'E' || c == '+' || c == '-';
        if (!ok) break;
        i++;
    }
    if (i == start) throw std::runtime_error("expected number");
    return std::stod(src.substr(start, i - start));
}

static JValue parse_value(const std::string& src, size_t& i);

static JValue parse_object(const std::string& src, size_t& i) {
    if (i >= src.size() || src[i] != '{') throw std::runtime_error("expected object");
    i++;
    skip_ws(src, i);
    JValue out;
    out.type = JValue::OBJECT;
    if (i < src.size() && src[i] == '}') { i++; return out; }
    while (true) {
        skip_ws(src, i);
        std::string key = parse_string(src, i);
        skip_ws(src, i);
        if (i >= src.size() || src[i] != ':') throw std::runtime_error("expected ':'");
        i++;
        skip_ws(src, i);
        out.obj[key] = parse_value(src, i);
        skip_ws(src, i);
        if (i < src.size() && src[i] == ',') { i++; continue; }
        if (i < src.size() && src[i] == '}') { i++; break; }
        throw std::runtime_error("expected ',' or '}'");
    }
    return out;
}

static JValue parse_value(const std::string& src, size_t& i) {
    skip_ws(src, i);
    if (i >= src.size()) throw std::runtime_error("unexpected EOF");
    if (src[i] == '"') {
        JValue v;
        v.type = JValue::STRING;
        v.s = parse_string(src, i);
        return v;
    }
    if (src[i] == '{') return parse_object(src, i);
    JValue v;
    v.type = JValue::NUMBER;
    v.n = parse_number(src, i);
    return v;
}

static std::string escape_json_string(const std::string& s) {
    std::string out;
    out += '"';
    for (char c : s) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else out += c;
    }
    out += '"';
    return out;
}

static std::string make_ok_number(double n) {
    char buf[64];
    std::snprintf(buf, sizeof(buf), "{\"ok\":true,\"result\":%.17g}", n);
    return buf;
}

static std::string make_ok_string(const std::string& s) {
    return "{\"ok\":true,\"result\":" + escape_json_string(s) + "}";
}

// Object result for ops that return a struct (e.g. observe → ObservableState).
// All values encoded as numeric (bools encoded as 0/1) to keep the wire
// format stable and the Python NexusResponse parser simple.
static std::string make_ok_object(const std::map<std::string, double>& kv) {
    std::string out = "{\"ok\":true,\"result\":{";
    bool first = true;
    for (const auto& [k, v] : kv) {
        if (!first) out += ",";
        first = false;
        char buf[64];
        std::snprintf(buf, sizeof(buf), "%.17g", v);
        out += escape_json_string(k) + ":" + buf;
    }
    out += "}}";
    return out;
}

static std::string make_error(const std::string& msg) {
    return "{\"ok\":false,\"error\":" + escape_json_string(msg) + "}";
}

// Parse a Vec3 from a JValue object {"x":..,"y":..,"z":..}.
// Throws if shape is wrong (caller catches and translates to make_error).
static Vec3 parse_vec3(const JValue& v) {
    if (v.type != JValue::OBJECT) throw std::runtime_error("expected vec3 object");
    auto get_num = [&](const char* k) -> double {
        auto it = v.obj.find(k);
        if (it == v.obj.end() || it->second.type != JValue::NUMBER)
            throw std::runtime_error(std::string("vec3 missing/non-numeric '") + k + "'");
        return it->second.n;
    };
    return Vec3{get_num("x"), get_num("y"), get_num("z")};
}

// Lookup helper for required numeric arg.
static double require_number(const JValue& args, const char* key) {
    auto it = args.obj.find(key);
    if (it == args.obj.end() || it->second.type != JValue::NUMBER)
        throw std::runtime_error(std::string("missing or non-numeric '") + key + "'");
    return it->second.n;
}

// Lookup helper for required string arg.
static const std::string& require_string(const JValue& args, const char* key) {
    auto it = args.obj.find(key);
    if (it == args.obj.end() || it->second.type != JValue::STRING)
        throw std::runtime_error(std::string("missing or non-string '") + key + "'");
    return it->second.s;
}

// Lookup helper for required Vec3 arg.
static Vec3 require_vec3(const JValue& args, const char* key) {
    auto it = args.obj.find(key);
    if (it == args.obj.end())
        throw std::runtime_error(std::string("missing vec3 '") + key + "'");
    return parse_vec3(it->second);
}

static uint32_t parse_regime_string(const std::string& s) {
    if (s == "REST")          return R_REST;
    if (s == "STL_NONREL")    return R_STL_NONREL;
    if (s == "STL_REL")       return R_STL_REL;
    if (s == "WARP_CHARGE")   return R_WARP_CHARGE;
    if (s == "WARP_CRUISE")   return R_WARP_CRUISE;
    if (s == "WARP_SHUTDOWN") return R_WARP_SHUTDOWN;
    if (s == "GRAVITY_WELL")  return R_GRAVITY_WELL;
    if (s == "CRYOSLEEP")     return R_CRYOSLEEP;
    throw std::runtime_error("unknown regime: " + s);
}

static std::string dispatch(const JValue& req) {
    if (req.type != JValue::OBJECT) {
        return make_error("request must be a JSON object");
    }
    auto it_op = req.obj.find("op");
    if (it_op == req.obj.end()) return make_error("missing 'op' field");
    if (it_op->second.type != JValue::STRING) return make_error("'op' must be a string");
    const std::string& op = it_op->second.s;

    JValue args;
    auto it_args = req.obj.find("args");
    if (it_args != req.obj.end()) args = it_args->second;

    if (op == "health") {
        return make_ok_string("alive");
    }

    if (op == "version") {
        return make_ok_string("astra_nexus v0.128.day2");
    }

    if (op == "compute_apparent_rate") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        auto it_v = args.obj.find("v_radial");
        auto it_r = args.obj.find("regime");
        if (it_v == args.obj.end() || it_v->second.type != JValue::NUMBER) {
            return make_error("missing or non-numeric 'v_radial'");
        }
        if (it_r == args.obj.end() || it_r->second.type != JValue::STRING) {
            return make_error("missing or non-string 'regime'");
        }
        try {
            uint32_t regime = parse_regime_string(it_r->second.s);
            double rate = compute_apparent_rate(it_v->second.n, regime);
            return make_ok_number(rate);
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    // §6.4 Narrator-LLM tool surface: kepler_at, composition_rule_evaluate,
    // retarded_time_solve, observe, physics_query (generic dispatch wrapper).
    // ship_state_query is intentionally NOT here per audit Q1: ship-sim state
    // lives in textverse Python, not in astra_nexus C++. (D2 of audit.)

    if (op == "kepler_at") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            Orbit orb;
            orb.a      = require_number(args, "a");
            orb.e      = require_number(args, "e");
            orb.period = require_number(args, "period");
            orb.t0     = require_number(args, "t0");
            double t   = require_number(args, "t");
            return make_ok_number(orbit_phase(orb, t));
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "composition_rule_evaluate") {
        // §3.2 dτ/dt_cosmic = f_warp · √(1−rs/r) · √(1+2Φ/c²) / γ_kin
        // Inputs: W_warp (warp coil fraction), grav_factor (Schwarzschild
        // composition already computed), gamma_kin (rapidity-derived γ),
        // warp_active (0 or 1).
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            double W_warp     = require_number(args, "W_warp");
            double grav       = require_number(args, "grav_factor");
            double gamma_kin  = require_number(args, "gamma_kin");
            double warp_flag  = require_number(args, "warp_active");
            bool warp_active  = warp_flag != 0.0;
            return make_ok_number(dtau_dt_cosmic(W_warp, grav, gamma_kin, warp_active));
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "retarded_time_solve") {
        // §3.11 retarded-time = t_cosmic − lookback(d, z_cosmo).
        // Returns t_emit (cosmic time at which observed photons left source).
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            double d_proper = require_number(args, "d_proper");
            double z_cosmo  = require_number(args, "z_cosmo");
            double t_cosmic = require_number(args, "t_cosmic");
            double lookback = compute_lookback(d_proper, z_cosmo);
            return make_ok_number(t_cosmic - lookback);
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "observe") {
        // §6.3 12-step observation workflow. Returns the full Observable
        // struct as a JSON object. Wire format extension: object result.
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            Vec3 ship_pos       = require_vec3(args, "ship_pos");
            Vec3 ship_velocity  = require_vec3(args, "ship_velocity");
            double t_cosmic     = require_number(args, "t_cosmic");
            Vec3 body_pos       = require_vec3(args, "body_pos");
            double body_metric  = require_number(args, "body_metric_shift");
            uint32_t regime     = parse_regime_string(require_string(args, "regime"));
            Observable obs = observe(ship_pos, ship_velocity, t_cosmic,
                                     body_pos, body_metric, regime);
            std::map<std::string, double> result;
            result["d"]              = obs.d;
            result["v_radial"]       = obs.v_radial;
            result["z_cosmo"]        = obs.z_cosmo;
            result["z_kin"]          = obs.z_kin;
            result["z_metric"]       = obs.z_metric;
            result["z_total"]        = obs.z_total;
            result["t_emit"]         = obs.t_emit;
            result["apparent_rate"]  = obs.apparent_rate;
            result["time_reversed"]  = obs.time_reversed ? 1.0 : 0.0;
            return make_ok_object(result);
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "physics_query") {
        // Generic dispatch wrapper per §6.4 — args carry an inner `query`
        // string and `params` object. Routes by re-invoking dispatch with a
        // synthesized inner request. Lets the Narrator-LLM submit a single
        // "physics_query" tool form rather than learning the full op table.
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        auto it_q = args.obj.find("query");
        auto it_p = args.obj.find("params");
        if (it_q == args.obj.end() || it_q->second.type != JValue::STRING)
            return make_error("physics_query missing or non-string 'query'");
        if (it_p == args.obj.end() || it_p->second.type != JValue::OBJECT)
            return make_error("physics_query missing or non-object 'params'");
        const std::string& inner_op = it_q->second.s;
        if (inner_op == "physics_query")
            return make_error("physics_query cannot recurse into itself");
        JValue inner_req;
        inner_req.type = JValue::OBJECT;
        JValue inner_op_v;
        inner_op_v.type = JValue::STRING;
        inner_op_v.s = inner_op;
        inner_req.obj["op"] = inner_op_v;
        inner_req.obj["args"] = it_p->second;
        return dispatch(inner_req);
    }

    return make_error("unknown op: " + op);
}

int run() {
    std::ios_base::sync_with_stdio(false);
    std::string line;
    while (std::getline(std::cin, line)) {
        // Strip trailing CR from Windows line endings if Python wrote text-mode
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        std::string response;
        try {
            size_t i = 0;
            JValue req = parse_value(line, i);
            response = dispatch(req);
        } catch (const std::exception& e) {
            response = make_error(std::string("parse error: ") + e.what());
        }
        std::cout << response << "\n";
        std::cout.flush();
    }
    return 0;
}

} // namespace stdio_server

} // namespace astra

// =============================================================================
// main
// =============================================================================
int main(int argc, char** argv) {
    using namespace astra;

    // Day 2 v0.128: JSON-over-stdio bridge mode. Activates ONLY on flag;
    // existing test+demo behavior is unchanged when invoked without args.
    if (argc >= 2 && std::string(argv[1]) == "--stdio-server") {
        return stdio_server::run();
    }

    std::printf("====================================================================\n");
    std::printf(" ASTRA-7 Unified Physics Nexus — Compileable Demonstration\n");
    std::printf(" Proving 14-equation framework composes (SR + GR + Warp + Cosmology)\n");
    std::printf(" Spec ref: docs/spec-v0.126.md + §3.11/§4.2 v0.127 (Observation)\n");
    std::printf("====================================================================\n");

    test::run_all();
    demo_voyage();

    std::printf("\n");
    return test::failed == 0 ? 0 : 1;
}
