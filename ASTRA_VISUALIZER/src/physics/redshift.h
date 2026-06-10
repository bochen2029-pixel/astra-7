// src/physics/redshift.h — simple linear redshift color model.
//
// Shared between C++ (assertion expected-value precomputation) and GLSL
// (per-fragment color shift in fragment shaders). The GLSL string at the
// bottom is the exact mirror — keep them in sync.
//
// Provisional V1.7 model (spec-loose; visually tuned; recorded as v0.130
// candidate in docs/KNOWN_ISSUES.md):
//   R' = clamp(R + 0.60 * z, 0, 1)
//   G' = clamp(G - 0.10 * z, 0, 1)
//   B' = clamp(B - 0.50 * z, 0, 1)
//
// Tuned so that for the canonical "ocean blue" planet (0.30, 0.55, 0.90),
// the spec assertion "R > B at receding z > 0.5" holds for S02 (z=0.732)
// and S03 (z=3.359). Replace with proper blackbody-temperature shift in v0.130.

#pragma once

#include <algorithm>

namespace astra::physics {

struct RGB { float r, g, b; };

constexpr float kRedshiftCoeffR =  0.60f;
constexpr float kRedshiftCoeffG = -0.10f;
constexpr float kRedshiftCoeffB = -0.50f;

inline RGB apply_kin_redshift(RGB c, float z) {
    return RGB{
        std::clamp(c.r + kRedshiftCoeffR * z, 0.0f, 1.0f),
        std::clamp(c.g + kRedshiftCoeffG * z, 0.0f, 1.0f),
        std::clamp(c.b + kRedshiftCoeffB * z, 0.0f, 1.0f),
    };
}

// GLSL mirror. Update both atomically when tuning coefficients.
constexpr const char* kGlslRedshiftFn = R"(
vec3 apply_kin_redshift(vec3 c, float z) {
    return vec3(
        clamp(c.r + 0.60 * z, 0.0, 1.0),
        clamp(c.g - 0.10 * z, 0.0, 1.0),
        clamp(c.b - 0.50 * z, 0.0, 1.0)
    );
}
)";

}  // namespace astra::physics
