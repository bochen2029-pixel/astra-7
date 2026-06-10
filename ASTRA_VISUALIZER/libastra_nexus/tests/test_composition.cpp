// libastra_nexus/tests/test_composition.cpp
//
// Composition rule (§3.2 v0.126) — ported from proto/astra_nexus.cpp
// "Composition rule (§3.2 v0.126)" + "§6.4 composition_rule_evaluate primitive".

#include <doctest/doctest.h>
#include "astra_nexus/composition.h"
#include "astra_nexus/constants.h"
#include <cmath>
#include <vector>

using namespace astra;

TEST_CASE("Composition rule §3.2 — REST + STL identities") {
    CHECK(std::abs(dtau_dt_cosmic(0, 1.0, 1.0, false) - 1.0) < 1e-12);  // REST + no warp + no gravity
    CHECK(std::abs(dtau_dt_cosmic(0, 1.0, 2.0, false) - 0.5) < 1e-12);  // STL gamma=2: dtau/dt = 0.5
}

TEST_CASE("Composition rule §3.2 — Schwarzschild factor at r = 100*r_s") {
    std::vector<BHEntry> bhs;
    double rs = schwarzschild_r(10.0 * M_SUN);
    bhs.push_back({10.0 * M_SUN, {100.0 * rs, 0, 0}});
    double grav = compute_grav_factor(bhs, {0, 0, 0});
    double expected = std::sqrt(1.0 - rs / (100.0 * rs));
    CHECK(std::abs(grav - expected) < 1e-12);
}

TEST_CASE("Composition rule §3.2 — Grav factor at very large r approaches 1") {
    std::vector<BHEntry> bhs;
    bhs.push_back({10.0 * M_SUN, {1.0e15, 0, 0}});  // very far
    double grav_far = compute_grav_factor(bhs, {0, 0, 0});
    CHECK(grav_far > 0.999999);
    CHECK(grav_far <= 1.0);
}

TEST_CASE("f_warp canon defaults") {
    CHECK(std::abs(f_warp_canon(0.0) - 1.0) < 1e-12);
    CHECK(std::abs(f_warp_canon(1.0) - 0.5) < 1e-12);
    CHECK(std::abs(f_warp_canon(0.5) - (1.0 - 0.5 * 0.25)) < 1e-12);
}

TEST_CASE("Full composition — W=0.8, grav=0.9, gamma=2") {
    double full = dtau_dt_cosmic(0.8, 0.9, 2.0, true);
    double expected_full = f_warp_canon(0.8) * 0.9 / 2.0;
    CHECK(std::abs(full - expected_full) < 1e-12);
}

TEST_CASE("§6.4 composition_rule_evaluate primitive parity") {
    // composition_rule = f_warp * grav * 1/gamma_kin
    double r1 = dtau_dt_cosmic(0.0, 1.0, 1.0, /*warp_active=*/false);
    CHECK(std::abs(r1 - 1.0) < 1e-12);  // (rest, no-grav, gamma=1) == 1.0

    double r2 = dtau_dt_cosmic(0.0, 1.0, 2.0, false);
    CHECK(std::abs(r2 - 0.5) < 1e-12);  // STL gamma=2 == 0.5

    // WARP_CRUISE W=1.0: f_warp = max(0.5, 1 - 0.5*1^2) = 0.5
    double r3 = dtau_dt_cosmic(1.0, 1.0, 1.0, /*warp_active=*/true);
    CHECK(std::abs(r3 - 0.5) < 1e-12);  // W=1.0 cruise == 0.5

    double r4 = dtau_dt_cosmic(0.0, 0.7, 1.5, false);
    CHECK(std::abs(r4 - (0.7 / 1.5)) < 1e-12);  // STL+grav composes multiplicatively
}
