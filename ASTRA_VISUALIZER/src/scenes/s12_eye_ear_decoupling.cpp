// src/scenes/s12_eye_ear_decoupling.cpp

#include "scenes/s12_eye_ear_decoupling.h"

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

void S12_EyeEarDecoupling::setup() {
    sim_time_seconds_ = 0.0;
    phase_           = Phase::WARP;
    audio_t_         = 0.0;
    visual_t_        = 0.0;
    eye_ear_gap_     = 0.0;
    current_phase_   = 0.0;
    planet_ndc_x_    = kOrbitRadiusNdc;
    planet_ndc_y_    = 0.0f;
    starfield_.setup();
    placeholders_renderer_.setup();
}

void S12_EyeEarDecoupling::tick(float dt_seconds) {
    sim_time_seconds_ += static_cast<double>(dt_seconds);
    audio_t_ = sim_time_seconds_;

    if (sim_time_seconds_ < kShutdownStart) {
        phase_   = Phase::WARP;
        // WARP_CRUISE at v_app=2c: rate=-1, visual_t = -sim_time.
        visual_t_ = -sim_time_seconds_;
    } else if (sim_time_seconds_ < kShutdownEnd) {
        phase_   = Phase::SHUTDOWN;
        double progress = (sim_time_seconds_ - kShutdownStart) / kShutdownDuration;
        eye_ear_gap_ = kWarpGapAtShutdown * (1.0 - progress);
        visual_t_    = audio_t_ - eye_ear_gap_;
    } else {
        phase_   = Phase::REST;
        visual_t_ = audio_t_;
    }
    eye_ear_gap_ = audio_t_ - visual_t_;

    // Planet phase derived from visual_t (the retarded-time the operator is
    // actually seeing). At t=10.5, visual_t ~= -6.17, phase ~= -0.646 rad.
    astra::Orbit orb{1.5e11, 0.0, kOrbitPeriodSeconds, 0.0};
    current_phase_ = astra::orbit_phase(orb, visual_t_);
    planet_ndc_x_ = kOrbitRadiusNdc * static_cast<float>(std::cos(current_phase_));
    planet_ndc_y_ = kOrbitRadiusNdc * static_cast<float>(std::sin(current_phase_));
}

void S12_EyeEarDecoupling::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    starfield_.render(/*z_kin=*/0.0f);

    std::vector<renderer::Placeholder> phs = {
        {"planet", planet_ndc_x_, planet_ndc_y_, 0.04f, kPlanetR, kPlanetG, kPlanetB},
    };
    placeholders_renderer_.render(viewport_width, viewport_height, phs, /*z_kin=*/0.0f);
}

void S12_EyeEarDecoupling::teardown() {
    placeholders_renderer_.teardown();
    starfield_.teardown();
}

std::vector<validation::NumericAssertion> S12_EyeEarDecoupling::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;

    // 1) apparent_rate at v_app=2c WARP_CRUISE = -1 (paired with S05).
    {
        validation::NumericAssertion a;
        a.name           = "apparent_rate_warp_2c";
        a.measured_value = compute_apparent_rate(2.0 * C_LIGHT, R_WARP_CRUISE);
        a.expected_value = -1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 apparent rate (WARP); §6 S12 warp-phase coupling";
        a.libastra_call  = "astra::compute_apparent_rate(2*C_LIGHT, R_WARP_CRUISE)";
        out.push_back(a);
    }

    // 2) Phase at canonical t=10.5s is SHUTDOWN (state machine assertion).
    {
        validation::NumericAssertion a;
        a.name           = "phase_at_t10_5_is_shutdown";
        a.measured_value = (phase_ == Phase::SHUTDOWN) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§6 S12 phase machine; t in [10, 13) -> SHUTDOWN";
        a.libastra_call  = "S12 phase machine at sim_time=10.5";
        out.push_back(a);
    }

    // 3) eye-ear gap at canonical t=10.5s ~= 16.667 seconds.
    //    progress = 0.5/3 = 1/6; gap = 20 * (1 - 1/6) = 20 * 5/6 ~= 16.667.
    {
        validation::NumericAssertion a;
        a.name           = "eye_ear_gap_at_t10_5";
        a.measured_value = eye_ear_gap_;
        a.expected_value = kWarpGapAtShutdown * (1.0 - 0.5 / kShutdownDuration);
        a.tolerance      = 1e-4;  // chunked-tick FP drift propagates here (V1.10 finding)
        a.spec_section   = "§6 S12 acceptance #3 — gap shrinks asymptotically over shutdown";
        a.libastra_call  = "S12 shutdown-phase gap: kWarpGapAtShutdown * (1 - (t-10)/3)";
        out.push_back(a);
    }

    // 4) visual_t is still negative at canonical t=10.5 (warp-legacy lag active).
    //    visual_t = audio_t - gap = 10.5 - 16.667 ~= -6.167.
    {
        validation::NumericAssertion a;
        a.name           = "visual_t_still_negative_mid_shutdown";
        a.measured_value = (visual_t_ < 0.0) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§6 S12 acceptance #2 — visual_t continues reverse-walking";
        a.libastra_call  = "S12 visual_t < 0 at t=10.5 (post-warp reverse-time legacy)";
        out.push_back(a);
    }

    // 5) audio_t exactly equals sim_time at canonical timestamp.
    {
        validation::NumericAssertion a;
        a.name           = "audio_t_equals_sim_time";
        a.measured_value = audio_t_;
        a.expected_value = sim_time_seconds_;
        a.tolerance      = 1e-12;
        a.spec_section   = "§6 S12 acceptance #1 — audio = real-time (no retarded lookup)";
        a.libastra_call  = "S12 audio_t = sim_time_seconds_";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S12_EyeEarDecoupling::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    // Pixel assertions at the planet's CURRENT (visual_t-derived) screen position.
    // At canonical t=10.5, visual_t ~= -6.17, phase ~= -0.646 rad, NDC (0.80, -0.60)*0.4
    // = (0.32, -0.24). Pixel: x ~= w*0.66, y ~= h*0.62.
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
        a.spec_section   = "§6 S12 visual-lag planet position at visual_t (mid-decoupling)";
        a.libastra_call  = "astra::orbit_phase(orb, S12::visual_t_) -> NDC -> pixel";
        out.push_back(a);
    };
    add("planet_at_visual_t_R", 0, kPlanetR);
    add("planet_at_visual_t_G", 1, kPlanetG);
    add("planet_at_visual_t_B", 2, kPlanetB);

    return out;
}

}  // namespace astra::scenes
