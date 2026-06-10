// src/validation/pixel_sampler.cpp

#include "validation/pixel_sampler.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace astra::validation {

std::vector<AssertionResult> PixelSampler::sample_and_compare(
    int framebuffer_width,
    int framebuffer_height,
    const std::vector<ScalarPixelAssertion>& assertions)
{
    std::vector<AssertionResult> results;
    results.reserve(assertions.size());
    if (framebuffer_width <= 0 || framebuffer_height <= 0 || assertions.empty()) {
        return results;
    }

    // Bind the requested framebuffer for reading.
    GLint prev_read = 0;
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &prev_read);
    glBindFramebuffer(GL_READ_FRAMEBUFFER, framebuffer_);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);

    // GL pixel coordinates have origin at bottom-left; assertions provide
    // top-left-origin coordinates (matches Image / framebuffer-grid intuition).
    // Convert at sample time.
    for (const auto& a : assertions) {
        int x = std::clamp(a.framebuffer_x, 0, framebuffer_width  - 1);
        int y_top = std::clamp(a.framebuffer_y, 0, framebuffer_height - 1);
        int y_gl  = (framebuffer_height - 1) - y_top;

        unsigned char px[4] = {0, 0, 0, 0};
        glReadPixels(x, y_gl, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, px);

        float measured = 0.0f;
        if (a.channel >= 0 && a.channel <= 3) {
            measured = px[a.channel] / 255.0f;
        } else {
            // -1 = average of RGB (alpha excluded).
            measured = (px[0] + px[1] + px[2]) / (3.0f * 255.0f);
        }

        AssertionResult r;
        r.name           = a.name;
        r.measured_value = measured;
        r.expected_value = a.expected_value;
        r.diff_abs       = std::abs(measured - a.expected_value);
        r.diff_rel       = (std::abs(a.expected_value) > 1e-12)
                             ? r.diff_abs / std::abs(a.expected_value)
                             : r.diff_abs;
        r.tolerance      = a.tolerance;
        r.passed         = r.diff_abs <= a.tolerance;
        r.spec_section   = a.spec_section;
        r.libastra_call  = a.libastra_call;
        results.push_back(r);
    }

    glBindFramebuffer(GL_READ_FRAMEBUFFER, static_cast<GLuint>(prev_read));
    return results;
}

}  // namespace astra::validation
