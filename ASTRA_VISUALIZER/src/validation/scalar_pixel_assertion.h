// src/validation/scalar_pixel_assertion.h — validation primitive types.
//
// Spec: DESIGN_SPEC §7.1 ("Layer 1 — Scalar pixel assertions") + §7.4
// ("validation report JSON").

#pragma once

#include <cmath>
#include <string>
#include <vector>

namespace astra::validation {

// Layer 1 — pixel-level scalar assertion. Reads a single channel of a
// single framebuffer pixel and compares it to a libastra-derived expected
// value.
struct ScalarPixelAssertion {
    std::string name;                     // human-readable
    int framebuffer_x = 0;
    int framebuffer_y = 0;
    int channel       = 0;                // 0=R, 1=G, 2=B, 3=A; -1 for any
    float expected_value = 0.0f;          // canonical math output
    float tolerance      = 0.01f;         // pass if |measured - expected| < tolerance
    std::string spec_section;             // e.g. "§3.11 retarded-time"
    std::string libastra_call;            // e.g. "compute_apparent_rate(2*C_LIGHT, R_WARP_CRUISE)"
};

// V1.2-class numeric assertion: scene reports two doubles (measured + expected)
// computed entirely from libastra. No rendering involved; usable in headless
// mode before real scene rendering lands in V1.3+.
struct NumericAssertion {
    std::string name;
    double measured_value = 0.0;
    double expected_value = 0.0;
    double tolerance      = 1e-9;
    std::string spec_section;
    std::string libastra_call;
};

struct AssertionResult {
    std::string name;
    double measured_value = 0.0;
    double expected_value = 0.0;
    double diff_abs = 0.0;
    double diff_rel = 0.0;
    double tolerance = 0.0;
    bool   passed = false;
    std::string spec_section;
    std::string libastra_call;
};

inline AssertionResult evaluate(const NumericAssertion& a) {
    AssertionResult r;
    r.name           = a.name;
    r.measured_value = a.measured_value;
    r.expected_value = a.expected_value;
    r.diff_abs       = std::abs(a.measured_value - a.expected_value);
    r.diff_rel       = (a.expected_value != 0.0)
                         ? r.diff_abs / std::abs(a.expected_value)
                         : r.diff_abs;
    r.tolerance      = a.tolerance;
    r.passed         = r.diff_abs <= a.tolerance;
    r.spec_section   = a.spec_section;
    r.libastra_call  = a.libastra_call;
    return r;
}

}  // namespace astra::validation
