// libastra_nexus/tests/test_cherenkov.cpp
//
// NEW — closes the AUDIT 5D-F4 gap. Cherenkov formula was locked at 4 spec
// sites (§6 step 10, §6 Appendix B, §10 validation, §15.6) with ZERO code
// implementation. These tests are the code-side empirical anchor.
//
// Formula tested (spec §6 step 10):
//   cos(theta_c) = 1 / (n * beta)
// with n(W) = 1 + n_coefficient * W (default n_coefficient = 1.0).

#include <doctest/doctest.h>
#include "astra_nexus/cherenkov.h"
#include <cmath>

using namespace astra;

TEST_CASE("Cherenkov — cone INACTIVE when n*beta <= 1") {
    // At beta=0.1, W=0: n=1.0, n*beta=0.1 -> cone inactive
    CHECK(compute_cherenkov_angle(0.0, 0.1) == -1.0);

    // At beta=0.5, W=0: n=1.0, n*beta=0.5 -> cone inactive
    CHECK(compute_cherenkov_angle(0.0, 0.5) == -1.0);

    // Exact boundary: n*beta == 1.0 -> still inactive (strict inequality)
    CHECK(compute_cherenkov_angle(0.0, 1.0) == -1.0);
}

TEST_CASE("Cherenkov — angle at canonical W=1, beta=0.6") {
    // W=1.0, n=2.0; beta=0.6: n*beta=1.2; cos(theta)=1/1.2=0.8333;
    // theta=acos(0.8333) ~= 0.5857 rad ~= 33.56 degrees
    double angle = compute_cherenkov_angle(1.0, 0.6);
    CHECK(angle > 0.0);
    CHECK(std::abs(angle - std::acos(1.0 / 1.2)) < 1e-9);
    CHECK(std::abs(angle - 0.585685543) < 1e-6);
}

TEST_CASE("Cherenkov — angle OPENS monotonically as beta increases at fixed n") {
    // EMPIRICAL FINDING (V0 closure, 2026-05-16): For fixed n (here W=1.0, n=2.0),
    // the cone OPENS (theta INCREASES) as beta grows toward 1, approaching the
    // asymptote acos(1/n) = acos(0.5) = 60 degrees = pi/3 rad. This contradicts
    // DESIGN_SPEC §6 S06 acceptance #4 wording ("Cone narrows ... as W increases")
    // and S06 assertion 4 wording ("narrows monotonically"). See
    // docs/KNOWN_ISSUES.md for v0.130 candidate revision.
    //
    // Physics: cos(theta_c) = 1/(n*beta). Fixed n, larger beta -> larger n*beta
    // -> smaller cos(theta) -> larger theta. Cone OPENS.
    double a1 = compute_cherenkov_angle(1.0, 0.55);  // n*beta = 1.10 -> theta ~ 0.430 rad
    double a2 = compute_cherenkov_angle(1.0, 0.75);  // n*beta = 1.50 -> theta ~ 0.841 rad
    double a3 = compute_cherenkov_angle(1.0, 0.95);  // n*beta = 1.90 -> theta ~ 1.017 rad
    CHECK(a1 > 0.0);
    CHECK(a2 > 0.0);
    CHECK(a3 > 0.0);
    CHECK(a1 < a2);  // opens as beta grows
    CHECK(a2 < a3);
    // Upper bound: as beta -> 1, theta -> acos(1/n) = acos(0.5) = pi/3
    CHECK(a3 < std::acos(1.0 / 2.0));
    CHECK(a3 > 1.0);  // already past 1 rad at beta=0.95
}

TEST_CASE("Cherenkov — angle OPENS monotonically as W (and thus n) increases at fixed beta") {
    // EMPIRICAL FINDING (V0 closure, 2026-05-16): For fixed beta=0.8, the cone
    // OPENS (theta INCREASES) as W (and n) grow. Contradicts DESIGN_SPEC §6 S06
    // acceptance #4 description. Physics dictates: larger n -> larger n*beta ->
    // smaller cos(theta) -> larger theta.
    double angle_W050 = compute_cherenkov_angle(0.5, 0.8);  // n=1.5, n*beta=1.20, theta~33.56 deg
    double angle_W100 = compute_cherenkov_angle(1.0, 0.8);  // n=2.0, n*beta=1.60, theta~51.32 deg
    CHECK(angle_W050 > 0.0);
    CHECK(angle_W100 > 0.0);
    CHECK(angle_W050 < angle_W100);  // OPENS as W grows
}

TEST_CASE("Cherenkov — independent check vs spec §6 step 10 formula") {
    // W=0.5 (n=1.5), beta=0.8 (n*beta=1.20)
    // cos(theta_c) = 1/1.2 = 0.8333
    double angle = compute_cherenkov_angle(0.5, 0.8);
    CHECK(std::abs(std::cos(angle) - (1.0 / 1.2)) < 1e-9);
}

TEST_CASE("Cherenkov — n_coefficient tuning parameter scales the index") {
    // n_coefficient = 2.0 doubles the W contribution.
    // At W=0.5: n_coeff=1 -> n=1.5; n_coeff=2 -> n=2.0
    // At beta=0.55: n_coeff=1 -> n*beta=0.825 INACTIVE
    //              n_coeff=2 -> n*beta=1.10  ACTIVE
    double inactive = compute_cherenkov_angle(0.5, 0.55, /*n_coefficient=*/1.0);
    double active   = compute_cherenkov_angle(0.5, 0.55, /*n_coefficient=*/2.0);
    CHECK(inactive == -1.0);
    CHECK(active > 0.0);
    CHECK(std::abs(active - std::acos(1.0 / 1.10)) < 1e-9);
}

TEST_CASE("Cherenkov — n_refractive_default helper parity") {
    // n(W) = 1 + n_coeff * W
    CHECK(std::abs(n_refractive_default(0.0) - 1.0) < 1e-12);
    CHECK(std::abs(n_refractive_default(1.0) - 2.0) < 1e-12);
    CHECK(std::abs(n_refractive_default(0.5) - 1.5) < 1e-12);
    CHECK(std::abs(n_refractive_default(0.5, 2.0) - 2.0) < 1e-12);  // double coefficient
}
