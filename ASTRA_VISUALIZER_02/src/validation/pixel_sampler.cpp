#include "validation/pixel_sampler.h"

#include <glad/gl.h>

#include <cmath>

namespace astra_viz {

PixelSampler::RGBA PixelSampler::sample(int fb_x, int fb_y) {
    float px[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    glFinish();  // flush before read to avoid race with the just-drawn frame
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(fb_x, fb_y, 1, 1, GL_RGBA, GL_FLOAT, px);
    return RGBA{px[0], px[1], px[2], px[3]};
}

AssertionResult PixelSampler::evaluate(const ScalarPixelAssertion& a) {
    RGBA c = sample(a.fb_x, a.fb_y);
    float m = (a.channel == 0) ? c.r
            : (a.channel == 1) ? c.g
            : (a.channel == 2) ? c.b
            :                    c.a;
    float d = std::fabs(m - a.expected);
    return AssertionResult{a.name, d <= a.tolerance, (double)a.expected, (double)m, (double)d};
}

AssertionResult PixelSampler::evaluate(const ScalarValueAssertion& a) {
    double d = std::fabs(a.measured - a.expected);
    return AssertionResult{a.name, d <= a.tolerance, a.expected, a.measured, d};
}

} // namespace astra_viz
