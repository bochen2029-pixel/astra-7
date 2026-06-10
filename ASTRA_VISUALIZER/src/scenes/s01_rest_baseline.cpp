// src/scenes/s01_rest_baseline.cpp
//
// V1.7: uses shared PlaceholderRenderer + StarfieldRenderer.

#include "scenes/s01_rest_baseline.h"

#include "astra_nexus/composition.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/rapidity.h"
#include "astra_nexus/regime.h"

#include <glad/gl.h>

#include <cstdio>

namespace astra::scenes {

namespace {

constexpr float kPixelTol = 0.02f;

int ndc_y_to_topleft(float ndc_y, int h) {
    float t = 0.5f * (1.0f - ndc_y);
    int   y = static_cast<int>(t * (h - 1) + 0.5f);
    if (y < 0)  y = 0;
    if (y >= h) y = h - 1;
    return y;
}
int ndc_x_to_topleft(float ndc_x, int w) {
    float t = 0.5f * (1.0f + ndc_x);
    int   x = static_cast<int>(t * (w - 1) + 0.5f);
    if (x < 0)  x = 0;
    if (x >= w) x = w - 1;
    return x;
}

}  // namespace

void S01_RestBaseline::setup() {
    sim_time_seconds_ = 0.0f;
    placeholders_ = {
        {"hull",   0.0f,    0.0f,  0.10f, 0.45f, 0.45f, 0.55f},
        {"sun",    0.0f,   +0.60f, 0.06f, 1.00f, 0.92f, 0.55f},
        {"planet",+0.70f,   0.00f, 0.05f, 0.30f, 0.55f, 0.90f},
    };
    starfield_.setup();
    placeholders_renderer_.setup();
}

void S01_RestBaseline::tick(float dt_seconds) {
    sim_time_seconds_ += dt_seconds;
}

void S01_RestBaseline::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    starfield_.render(/*z_kin=*/0.0f);
    placeholders_renderer_.render(viewport_width, viewport_height,
                                  placeholders_, /*z_kin=*/0.0f);
}

void S01_RestBaseline::teardown() {
    placeholders_renderer_.teardown();
    starfield_.teardown();
    placeholders_.clear();
}

std::vector<validation::NumericAssertion> S01_RestBaseline::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;
    {
        validation::NumericAssertion a;
        a.name = "gamma_at_rest";
        Rapidity r{{0, 0, 0}};
        a.measured_value = r.gamma();
        a.expected_value = 1.0;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.7 v0.126 rapidity";
        a.libastra_call  = "astra::Rapidity{{0,0,0}}.gamma()";
        out.push_back(a);
    }
    {
        validation::NumericAssertion a;
        a.name = "dtau_dt_at_rest";
        a.measured_value = dtau_dt_cosmic(0.0, 1.0, 1.0, false);
        a.expected_value = 1.0;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.2 composition rule";
        a.libastra_call  = "astra::dtau_dt_cosmic(0, 1.0, 1.0, false)";
        out.push_back(a);
    }
    {
        validation::NumericAssertion a;
        a.name = "apparent_rate_at_rest_zero_vrad";
        a.measured_value = compute_apparent_rate(0.0, R_REST);
        a.expected_value = 1.0;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.11 apparent rate (REST branch)";
        a.libastra_call  = "astra::compute_apparent_rate(0, R_REST)";
        out.push_back(a);
    }
    return out;
}

std::vector<validation::ScalarPixelAssertion> S01_RestBaseline::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;
    const char* chan_label[3] = {"R", "G", "B"};
    for (const auto& p : placeholders_) {
        int cx = ndc_x_to_topleft(p.ndc_x, last_viewport_w_);
        int cy = ndc_y_to_topleft(p.ndc_y, last_viewport_h_);
        float channels[3] = {p.r, p.g, p.b};
        for (int c = 0; c < 3; c++) {
            validation::ScalarPixelAssertion a;
            char buf[64];
            std::snprintf(buf, sizeof(buf), "%s_center_%s", p.short_name, chan_label[c]);
            a.name           = buf;
            a.framebuffer_x  = cx;
            a.framebuffer_y  = cy;
            a.channel        = c;
            a.expected_value = channels[c];
            a.tolerance      = kPixelTol;
            a.spec_section   = "§1.3 placeholder geometry (V1.4)";
            a.libastra_call  = "n/a (visual baseline; canonical RGB)";
            out.push_back(a);
        }
    }
    return out;
}

}  // namespace astra::scenes
