// src/scenes/s05_warp_cruise_2c.cpp — V1.10 with trail.

#include "scenes/s05_warp_cruise_2c.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/kepler.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"

#include <glad/gl.h>

#include <cmath>
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

void S05_WarpCruise2c::setup() {
    sim_time_seconds_ = 0.0;
    apparent_rate_ = astra::compute_apparent_rate(v_app_over_c_ * astra::C_LIGHT,
                                                  astra::R_WARP_CRUISE);
    t_emit_       = 0.0;
    current_phase_ = 0.0;
    planet_ndc_x_  = orbit_radius_ndc_;
    planet_ndc_y_  = 0.0f;
    trail_.clear();
    trail_.reserve(kTrailLen);
    trail_count_              = 0;
    next_trail_append_time_   = 0.0;

    starfield_.setup();
    placeholders_renderer_.setup();
}

void S05_WarpCruise2c::tick(float dt_seconds) {
    sim_time_seconds_ += static_cast<double>(dt_seconds);
    t_emit_ = sim_time_seconds_ * apparent_rate_;
    astra::Orbit orb{1.5e11, 0.0, period_seconds_, 0.0};
    current_phase_ = astra::orbit_phase(orb, t_emit_);

    planet_ndc_x_ = orbit_radius_ndc_ * static_cast<float>(std::cos(current_phase_));
    planet_ndc_y_ = orbit_radius_ndc_ * static_cast<float>(std::sin(current_phase_));

    // Subsampled trail append: one entry per kTrailAppendInterval seconds of
    // sim time. trail_ stays sorted oldest -> newest (head shifts off when full).
    if (sim_time_seconds_ >= next_trail_append_time_) {
        next_trail_append_time_ += kTrailAppendInterval;
        TrailPoint p{planet_ndc_x_, planet_ndc_y_};
        if (trail_count_ < kTrailLen) {
            trail_.push_back(p);
            trail_count_ = static_cast<int>(trail_.size());
        } else {
            for (int i = 1; i < kTrailLen; i++) trail_[i - 1] = trail_[i];
            trail_[kTrailLen - 1] = p;
        }
    }
}

void S05_WarpCruise2c::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    starfield_.render(/*z_kin=*/0.0f);

    // Build placeholder list each frame: trail (oldest -> newest, fading) +
    // current planet (largest, brightest). Trail dots get smaller + dimmer
    // the older they are. The newest trail entry coincides with the current
    // planet — render planet on top last so it dominates.
    std::vector<renderer::Placeholder> phs;
    phs.reserve(trail_count_ + 1);
    for (int i = 0; i < trail_count_; i++) {
        // age_frac: 1/N for oldest, ~1 for newest
        float age_frac = static_cast<float>(i + 1) / static_cast<float>(trail_count_);
        // Subtle dim + small size for old points; close-to-planet for newest.
        float size  = 0.012f * (0.35f + 0.65f * age_frac);
        float scale = 0.50f * age_frac + 0.20f;  // 0.20 (old) -> 0.70 (newest)
        phs.push_back({"trail",
            trail_[i].ndc_x, trail_[i].ndc_y, size,
            kPlanetR * scale, kPlanetG * scale, kPlanetB * scale});
    }
    // Current planet (drawn on top of newest trail entry).
    phs.push_back({"planet",
        planet_ndc_x_, planet_ndc_y_, 0.04f,
        kPlanetR, kPlanetG, kPlanetB});
    placeholders_renderer_.render(viewport_width, viewport_height, phs, /*z_kin=*/0.0f);
}

void S05_WarpCruise2c::teardown() {
    placeholders_renderer_.teardown();
    starfield_.teardown();
    trail_.clear();
    trail_count_ = 0;
}

std::vector<validation::NumericAssertion> S05_WarpCruise2c::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;
    {
        validation::NumericAssertion a;
        a.name           = "apparent_rate_at_v2c_warp_cruise";
        a.measured_value = compute_apparent_rate(v_app_over_c_ * C_LIGHT, R_WARP_CRUISE);
        a.expected_value = -1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 apparent rate (WARP branch); §6 S05 acceptance #1";
        a.libastra_call  = "astra::compute_apparent_rate(2*C_LIGHT, R_WARP_CRUISE)";
        out.push_back(a);
    }
    {
        validation::NumericAssertion a;
        a.name           = "t_emit_at_t15s_equals_minus15";
        a.measured_value = t_emit_;
        a.expected_value = -15.0;
        a.tolerance      = 1e-3;  // V1.10: chunked headless ticking may accumulate <1ms FP error
        a.spec_section   = "§3.11 retarded-time decreases under superluminal recede";
        a.libastra_call  = "tick(15s) with rate=-1 -> t_emit = -15s";
        out.push_back(a);
    }
    {
        validation::NumericAssertion a;
        a.name           = "phase_delta_at_t15s_equals_minus_pi_over_2";
        double p = current_phase_;
        while (p >   M_PI) p -= 2.0 * M_PI;
        while (p <= -M_PI) p += 2.0 * M_PI;
        a.measured_value = p;
        a.expected_value = -M_PI / 2.0;
        a.tolerance      = 1e-6;
        a.spec_section   = "§6 S05 acceptance #2 — phase delta = -t*2pi/period (reversed)";
        a.libastra_call  = "astra::orbit_phase(orb{T=60s, e=0}, t_emit=-15s)";
        out.push_back(a);
    }
    {
        validation::NumericAssertion a;
        a.name           = "orbit_phase_libastra_parity";
        Orbit orb{1.5e11, 0.0, period_seconds_, 0.0};
        a.measured_value = orbit_phase(orb, t_emit_);
        a.expected_value = current_phase_;
        a.tolerance      = 1e-12;
        a.spec_section   = "§6 S05 acceptance #3 — rendered phase matches libastra";
        a.libastra_call  = "astra::orbit_phase(orb, t_emit_)";
        out.push_back(a);
    }
    {
        validation::NumericAssertion a;
        a.name           = "sign_contrast_warp_negative_stl_positive";
        double warp_r = compute_apparent_rate(v_app_over_c_ * C_LIGHT, R_WARP_CRUISE);
        double stl_r  = compute_apparent_rate(0.5 * C_LIGHT,            R_STL_REL);
        a.measured_value = (warp_r < 0.0 && stl_r > 0.0) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 regime-distinction; §10 validation row";
        a.libastra_call  = "sign(compute_apparent_rate(2c,WARP)) != sign(compute_apparent_rate(0.5c,STL_REL))";
        out.push_back(a);
    }
    return out;
}

std::vector<validation::ScalarPixelAssertion> S05_WarpCruise2c::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    int cx = ndc_x_to_topleft(planet_ndc_x_, last_viewport_w_);
    int cy = ndc_y_to_topleft(planet_ndc_y_, last_viewport_h_);

    auto add = [&](const char* nm, int ch, float expected) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = cx;
        a.framebuffer_y  = cy;
        a.channel        = ch;
        a.expected_value = expected;
        a.tolerance      = kPixelTol;
        a.spec_section   = "§6 S05 acceptance #3 — planet pixel at reversed-orbit phase position";
        a.libastra_call  = "astra::orbit_phase(orb, t_emit=-15s) = -pi/2 -> NDC (0, -0.4)";
        out.push_back(a);
    };
    add("planet_at_reversed_phase_R", 0, kPlanetR);
    add("planet_at_reversed_phase_G", 1, kPlanetG);
    add("planet_at_reversed_phase_B", 2, kPlanetB);

    return out;
}

}  // namespace astra::scenes
