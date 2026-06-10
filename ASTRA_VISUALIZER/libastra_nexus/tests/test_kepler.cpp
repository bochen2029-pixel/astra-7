// libastra_nexus/tests/test_kepler.cpp
//
// Kepler solver + orbit-reversal during warp egress.
// Ported from proto/astra_nexus.cpp sections:
//   "Kepler-at-t_emit: orbit reversal during warp egress"
//   "§6.4 Narrator-LLM tool surface — kepler_at primitive"

#include <doctest/doctest.h>
#include "astra_nexus/kepler.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/constants.h"
#include <cmath>

using namespace astra;

TEST_CASE("Kepler-at-t_emit: orbit REVERSAL during 2c warp egress (THE PAYOFF)") {
    // Earth-like orbit, body 1 ly behind ship
    Orbit earth_like{1.496e11, 0.0, 365.25 * 86400.0, 0.0};
    Vec3 body_pos{0, 0, -1.0 * LIGHT_YEAR};
    Vec3 vwarp{0, 0, 2.0 * C_LIGHT};  // warp away at 2c

    double t0 = 1.0e10;
    ObservableState o0 = observe({0, 0, 0}, vwarp, t0, body_pos, 0.0, R_WARP_CRUISE);

    // 30 cosmic days later, ship has moved 30 light-days further away
    double dt = 30.0 * 86400.0;
    Vec3 ship_t1{0, 0, vwarp.z * dt};
    double t1 = t0 + dt;
    ObservableState o1 = observe(ship_t1, vwarp, t1, body_pos, 0.0, R_WARP_CRUISE);

    CHECK(o1.t_emit < o0.t_emit);  // t_emit DECREASES as ship warps superluminally away

    // At v_app = 2c, dt_emit/dt_cosmic = -1, so Delta t_emit ~= -Delta t_cosmic = -30 d
    CHECK(std::abs((o1.t_emit - o0.t_emit) / 86400.0 - (-30.0)) < 0.5);

    double phase_0 = orbit_phase(earth_like, o0.t_emit);
    double phase_1 = orbit_phase(earth_like, o1.t_emit);
    // Normalize phase difference to (-pi, pi]
    double dphase = phase_1 - phase_0;
    while (dphase >  M_PI) dphase -= 2.0 * M_PI;
    while (dphase < -M_PI) dphase += 2.0 * M_PI;

    CHECK(dphase < 0);  // Orbital phase RUNS BACKWARD when sampled at t_emit (the effect)
}

TEST_CASE("§6.4 kepler_at primitive — periodicity invariant") {
    // kepler_at backs orbit_phase for the Narrator's astrometric_query.
    // Verify phase(t0+P) == phase(t0) (mod 2*pi).
    Orbit orb{1.5e11, 0.0167, 3.156e7, 0.0};   // earth-like
    double phase_t0   = orbit_phase(orb, 0.0);
    double phase_full = orbit_phase(orb, orb.period);
    double diff = std::fmod(phase_full - phase_t0 + 4.0 * M_PI, 2.0 * M_PI);
    if (diff > M_PI) diff -= 2.0 * M_PI;
    CHECK(std::abs(diff - 0.0) < 1e-6);
}

TEST_CASE("§6.4 kepler_at primitive — eccentric orbit advances monotonically") {
    Orbit ecc{1.0e11, 0.5, 1.0e7, 0.0};
    double last = orbit_phase(ecc, 0.0);
    bool monotonic_or_unwrap = true;
    for (int i = 1; i <= 50; i++) {
        double t = (double)i * (ecc.period / 50.0);
        double cur = orbit_phase(ecc, t);
        // Allow one 2*pi unwrap.
        if (cur < last && (last - cur) < M_PI) {
            monotonic_or_unwrap = false;
            break;
        }
        last = cur;
    }
    CHECK(monotonic_or_unwrap);
}
