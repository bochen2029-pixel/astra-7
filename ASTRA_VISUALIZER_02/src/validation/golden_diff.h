// golden_diff.h - heatmap-style golden-image comparison.
// Pass criteria per CLAUDE.md §11.2: max_mean_diff = 0.01 (1% mean pixel
// diff), max_pixel_diff = 0.10 (no single pixel may differ by >10%). The
// diff is computed in normalized [0, 1] RGB space (alpha excluded so subtle
// blending differences in alpha-overlapped passes don't pollute results).
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "validation/assertion.h"

namespace astra_viz {

struct GoldenDiffResult {
    bool   golden_present;        // false if golden file missing - PASS in that case (gated by caller)
    int    pixel_count;
    double mean_rgb_diff;         // [0, 1]
    double max_rgb_diff;          // [0, 1]
    bool   passed;
    std::string note;             // human-readable
};

// Compares a current frame buffer (RGBA8, top-left origin, w*h*4 bytes) against
// a golden PNG on disk. Returns golden_present=false if the file doesn't exist
// (which the caller treats as "regenerate me, don't fail"). Dimensions must
// match exactly; otherwise the result is a fail with a note.
GoldenDiffResult compare_to_golden(const std::string& golden_path,
                                   int w, int h,
                                   const std::vector<uint8_t>& current_rgba8,
                                   double mean_pass = 0.01,
                                   double max_pass  = 0.10);

// Helper: format the result as an AssertionResult for the standard summary table.
AssertionResult to_assertion(const std::string& name, const GoldenDiffResult& r);

} // namespace astra_viz
