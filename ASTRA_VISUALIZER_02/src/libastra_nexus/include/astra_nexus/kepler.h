// kepler.h — Kepler orbit solver + true-anomaly evaluation.
// Backs the Narrator-LLM `astrometric_query` primitive (§6.4) AND Scene S05's
// "orbit runs backward at v_app=2c" payoff (proto/astra_nexus.cpp:371-398).
#pragma once

namespace astra {

struct Orbit {
    double a;        // semi-major axis (m)
    double e;        // eccentricity
    double period;   // orbital period (s)
    double t0;       // epoch (s)
};

double solve_kepler_E(double M, double e);
double orbit_phase(const Orbit& orb, double t);

} // namespace astra
