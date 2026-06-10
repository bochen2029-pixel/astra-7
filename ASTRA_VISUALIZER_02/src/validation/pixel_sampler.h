// pixel_sampler.h - reads pixels via glReadPixels for ScalarPixelAssertion
// evaluation. Stateless apart from a small reusable RGBA pixel buffer.
#pragma once

#include "validation/assertion.h"

namespace astra_viz {

class PixelSampler {
public:
    AssertionResult evaluate(const ScalarPixelAssertion& a);
    AssertionResult evaluate(const ScalarValueAssertion& a);

    // Convenience: sample a single pixel and return all 4 channels in [0, 1].
    struct RGBA { float r, g, b, a; };
    RGBA sample(int fb_x, int fb_y);
};

} // namespace astra_viz
