#include "validation/golden_diff.h"
#include "validation/screenshot.h"

#include <cmath>
#include <cstdio>

namespace astra_viz {

GoldenDiffResult compare_to_golden(const std::string& golden_path,
                                   int w, int h,
                                   const std::vector<uint8_t>& current,
                                   double mean_pass, double max_pass) {
    GoldenDiffResult r{};
    r.golden_present = false;
    r.passed         = true;

    int gw = 0, gh = 0;
    std::vector<uint8_t> golden;
    if (!load_png_rgba8(golden_path, gw, gh, golden)) {
        char buf[256];
        std::snprintf(buf, sizeof(buf), "golden missing: %s", golden_path.c_str());
        r.note = buf;
        return r;
    }
    r.golden_present = true;

    if (gw != w || gh != h) {
        char buf[256];
        std::snprintf(buf, sizeof(buf),
                      "golden dimension mismatch: %dx%d vs current %dx%d",
                      gw, gh, w, h);
        r.note   = buf;
        r.passed = false;
        return r;
    }

    const size_t pixels = (size_t)w * h;
    double sum_rgb_diff = 0.0;
    double max_diff     = 0.0;
    for (size_t i = 0; i < pixels; i++) {
        const uint8_t* c = current.data() + i * 4;
        const uint8_t* g = golden.data()  + i * 4;
        // Only R, G, B compared - alpha skipped to allow subtle blending order to vary.
        double dr = std::fabs((double)c[0] - (double)g[0]) / 255.0;
        double dg = std::fabs((double)c[1] - (double)g[1]) / 255.0;
        double db = std::fabs((double)c[2] - (double)g[2]) / 255.0;
        double m  = (dr + dg + db) / 3.0;
        sum_rgb_diff += m;
        if (dr > max_diff) max_diff = dr;
        if (dg > max_diff) max_diff = dg;
        if (db > max_diff) max_diff = db;
    }
    r.pixel_count    = (int)pixels;
    r.mean_rgb_diff  = sum_rgb_diff / (double)pixels;
    r.max_rgb_diff   = max_diff;
    r.passed         = (r.mean_rgb_diff <= mean_pass) && (r.max_rgb_diff <= max_pass);
    char buf[256];
    std::snprintf(buf, sizeof(buf),
                  "mean_diff=%.4f (<= %.4f) max_diff=%.4f (<= %.4f) over %d px",
                  r.mean_rgb_diff, mean_pass, r.max_rgb_diff, max_pass, r.pixel_count);
    r.note = buf;
    return r;
}

AssertionResult to_assertion(const std::string& name, const GoldenDiffResult& r) {
    AssertionResult a{};
    a.name     = name;
    a.passed   = r.passed;
    a.expected = 0.0;
    a.measured = r.mean_rgb_diff;
    a.diff     = r.max_rgb_diff;
    return a;
}

} // namespace astra_viz
