// assertion.h - per-scene assertions evaluated after each frame.
//
// Two kinds:
//   ScalarValueAssertion - compares a scene-supplied numeric (e.g. the
//     apparent_rate currently being displayed) against a libastra_nexus value.
//     No pixel reads; pure math-vs-math. Most V4 assertions are of this kind.
//
//   ScalarPixelAssertion - reads one pixel via glReadPixels and compares one
//     channel to an expected value. Used for "this pixel is yellow" / "this
//     pixel is bright red" style checks.
//
// Tolerance default: 1% of |expected| or 0.01 absolute, whichever is larger.
#pragma once

#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

namespace astra_viz {

struct ScalarValueAssertion {
    std::string name;
    double      expected;
    double      measured;
    double      tolerance;
};

struct ScalarPixelAssertion {
    std::string name;
    int         fb_x, fb_y;      // pixel coords in the default framebuffer (0,0 = bottom-left)
    int         channel;         // 0 = R, 1 = G, 2 = B, 3 = A
    float       expected;
    float       tolerance;
};

struct AssertionResult {
    std::string name;
    bool        passed;
    double      expected;
    double      measured;
    double      diff;
};

// Default tolerance computation. Callers may pass their own.
inline double default_value_tolerance(double expected, double pct = 0.01, double abs_min = 0.01) {
    double t = std::abs(expected) * pct;
    return (t > abs_min) ? t : abs_min;
}
inline float default_pixel_tolerance(float expected, float pct = 0.05f, float abs_min = 0.05f) {
    float t = std::fabs(expected) * pct;
    return (t > abs_min) ? t : abs_min;
}

} // namespace astra_viz
