// src/validation/pixel_sampler.h — Layer 1 helper.
//
// Reads RGBA8 pixels from the currently-bound (or specified) framebuffer
// and evaluates a list of ScalarPixelAssertions against them.
//
// Spec: DESIGN_SPEC §7.1 Layer 1.

#pragma once

#include <vector>

#include <glad/gl.h>

#include "validation/scalar_pixel_assertion.h"

namespace astra::validation {

class PixelSampler {
public:
    // `framebuffer` = GL framebuffer object name; 0 = default backbuffer.
    explicit PixelSampler(GLuint framebuffer = 0) : framebuffer_(framebuffer) {}

    // Reads the pixels needed for each assertion and returns AssertionResults.
    // Assumes the frame has been fully rendered (glFinish before calling for
    // determinism in headless mode).
    std::vector<AssertionResult> sample_and_compare(
        int framebuffer_width,
        int framebuffer_height,
        const std::vector<ScalarPixelAssertion>& assertions);

private:
    GLuint framebuffer_;
};

}  // namespace astra::validation
