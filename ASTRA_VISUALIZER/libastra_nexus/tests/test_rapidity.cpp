// libastra_nexus/tests/test_rapidity.cpp
//
// Rapidity (§3.7 v0.126) — ported from proto/astra_nexus.cpp
// "Rapidity (§3.7) — v0.126 N1 verification" section.

#include <doctest/doctest.h>
#include "astra_nexus/rapidity.h"
#include "astra_nexus/constants.h"
#include <cmath>

using namespace astra;

TEST_CASE("Rapidity §3.7 — rest + omega=1 closed-form") {
    Rapidity rest{{0, 0, 0}};
    CHECK(std::abs(rest.gamma() - 1.0) < 1e-12);  // gamma at rest = 1
    CHECK(std::abs(rest.beta()  - 0.0) < 1e-12);  // beta  at rest = 0

    // omega=1: gamma = cosh(1) ~= 1.5430806
    Rapidity r1{{0, 0, 1.0}};
    CHECK(std::abs(r1.gamma() - std::cosh(1.0)) < 1e-12);
    CHECK(std::abs(r1.beta()  - std::tanh(1.0)) < 1e-12);
}

TEST_CASE("v0.126 N1 lock — omega_max=16.811 yields gamma ~= 1e7") {
    Rapidity rmax{{0, 0, OMEGA_MAX}};
    double gamma_max = rmax.gamma();
    CHECK(gamma_max > 9.0e6);
    CHECK(gamma_max < 1.1e7);
}

TEST_CASE("v0.125 BUG reproduction — arctanh(0.99999999) -> gamma ~= 7071") {
    double omega_v125 = std::atanh(0.99999999);
    double gamma_v125 = std::cosh(omega_v125);
    CHECK(gamma_v125 > 7000.0);
    CHECK(gamma_v125 < 7200.0);
}

TEST_CASE("§3.7 catastrophic cancellation discipline (cosh vs 1/sqrt)") {
    // Verify naive 1/sqrt(1-beta^2) diverges from cosh(omega) at omega_max.
    double beta_at_max = std::tanh(OMEGA_MAX);
    double gamma_cosh  = std::cosh(OMEGA_MAX);
    double gamma_naive = 1.0 / std::sqrt(1.0 - beta_at_max * beta_at_max);
    double rel_err     = std::abs(gamma_cosh - gamma_naive) / gamma_cosh;
    // The naive path loses precision (justifies the cosh-only discipline).
    CHECK(rel_err > 1e-4);
}

TEST_CASE("Rapidity integration — 1g for 1 ship-year") {
    double g = 9.81;
    double year = 3.15576e7;
    Rapidity rs{{0, 0, 0}};
    Vec3 a_fwd{0, 0, g};
    rs = integrate_rapidity_step(rs, a_fwd, year);
    // omega = g*tau/c (exact under constant proper accel)
    CHECK(std::abs(rs.omega() - g * year / C_LIGHT) < 1e-10);
}

TEST_CASE("Rapidity 3D maneuvering — perpendicular thrust at high gamma") {
    double g = 9.81;
    double year = 3.15576e7;
    Rapidity r_fast{{0, 0, 5.0}};       // gamma ~= 74
    Vec3 a_perp{0, g * 100.0, 0};       // strong perpendicular
    Rapidity r_after = integrate_rapidity_step(r_fast, a_perp, year);
    CHECK(r_after.beta() < 1.0);        // |v| < c by tanh bound
    CHECK(r_after.zeta.y > 0);          // perpendicular thrust rotates zeta direction
}

TEST_CASE("Rapidity clamp at OMEGA_MAX") {
    Rapidity r_init{{0, 0, OMEGA_MAX - 0.1}};
    Vec3 a_strong{0, 0, 1.0e10};
    Rapidity r_clamped = integrate_rapidity_step(r_init, a_strong, 1.0);
    CHECK(std::abs(r_clamped.omega() - OMEGA_MAX) < 1e-9);
}
