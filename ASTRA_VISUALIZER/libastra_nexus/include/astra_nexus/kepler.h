// libastra_nexus/include/astra_nexus/kepler.h
//
// Kepler solver — used to demonstrate orbit-reversal at retarded time.
// Extracted from proto/astra_nexus.cpp lines 368-398 (READ-ONLY source).
// Semantics IDENTICAL.

#pragma once

namespace astra {

struct Orbit {
    double a;       // semi-major axis (m)
    double e;       // eccentricity
    double period;  // orbital period (s)
    double t0;      // epoch (s)
};

// Newton-iterate Kepler's equation E - e*sin(E) = M.
double solve_kepler_E(double M, double e);

// True anomaly (orbital phase angle) at time t.
double orbit_phase(const Orbit& orb, double t);

}  // namespace astra
