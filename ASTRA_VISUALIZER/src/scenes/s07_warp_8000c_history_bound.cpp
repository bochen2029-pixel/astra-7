// src/scenes/s07_warp_8000c_history_bound.cpp

#include "scenes/s07_warp_8000c_history_bound.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdio>

namespace astra::scenes {

namespace {

// Background color as set by glClearColor in render(). Matches the
// `clearcolor` deep-space dark used by all scenes.
constexpr float kBgR = 0.012f;
constexpr float kBgG = 0.018f;
constexpr float kBgB = 0.035f;

// Pixel tolerance accommodates RGBA8 quantization on the background color.
// At RGBA8: R=3/255~0.0118 (target 0.012); G=5/255~0.0196 (target 0.018);
// B=9/255~0.0353 (target 0.035). Quantization error is <1/255 ~0.004.
constexpr float kPixelTol = 0.02f;

astra::ObservableState query_observe(double sim_time, double v_app_c,
                                     double body_distance_m, double t_source_start) {
    astra::Vec3 ship_pos{0.0, 0.0, sim_time * v_app_c * astra::C_LIGHT};
    astra::Vec3 ship_vel{0.0, 0.0, v_app_c * astra::C_LIGHT};
    astra::Vec3 body_pos{0.0, 0.0, -body_distance_m};
    return astra::observe(ship_pos, ship_vel, sim_time,
                          body_pos, 0.0, astra::R_WARP_CRUISE,
                          t_source_start);
}

}  // namespace

void S07_Warp8000cHistoryBound::setup() {
    sim_time_seconds_       = 0.0f;
    current_beyond_history_ = false;
    placeholders_.clear();
    placeholders_renderer_.setup();
}

void S07_Warp8000cHistoryBound::tick(float dt_seconds) {
    sim_time_seconds_ += dt_seconds;
    auto obs = query_observe(static_cast<double>(sim_time_seconds_),
                             v_app_over_c_, body_distance_m_, t_source_start_);
    current_beyond_history_ = obs.beyond_photon_history;
}

void S07_Warp8000cHistoryBound::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(kBgR, kBgG, kBgB, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    // Render planet ONLY when the photon-history bound has not yet been crossed.
    // Disabled starfield in this scene so the center-pixel assertion is
    // deterministic regardless of seeded RNG layout.
    if (!current_beyond_history_) {
        placeholders_ = {
            {"planet", 0.0f, 0.0f, 0.12f, 0.30f, 0.55f, 0.90f},
        };
        placeholders_renderer_.render(viewport_width, viewport_height,
                                      placeholders_, /*z_kin=*/0.0f);
    } else {
        placeholders_.clear();  // nothing to draw — the discrete disappearance
    }
}

void S07_Warp8000cHistoryBound::teardown() {
    placeholders_renderer_.teardown();
    placeholders_.clear();
}

std::vector<validation::NumericAssertion> S07_Warp8000cHistoryBound::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;
    auto obs = query_observe(static_cast<double>(sim_time_seconds_),
                             v_app_over_c_, body_distance_m_, t_source_start_);

    // 1) apparent_rate at v_app=8000c = -7999.
    {
        validation::NumericAssertion a;
        a.name           = "apparent_rate_at_v8000c";
        a.measured_value = compute_apparent_rate(v_app_over_c_ * C_LIGHT, R_WARP_CRUISE);
        a.expected_value = -7999.0;
        a.tolerance      = 1e-6;
        a.spec_section   = "§3.11 apparent rate (WARP); §6 S07";
        a.libastra_call  = "astra::compute_apparent_rate(8000*C_LIGHT, R_WARP_CRUISE)";
        out.push_back(a);
    }

    // 2) beyond_photon_history flag is true at canonical timestamp.
    {
        validation::NumericAssertion a;
        a.name           = "beyond_photon_history_at_t15s";
        a.measured_value = obs.beyond_photon_history ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 photon-source-history bound (audit D1)";
        a.libastra_call  = "astra::observe(..., R_WARP_CRUISE, t_source_start=-5).beyond_photon_history";
        out.push_back(a);
    }

    // 3) t_emit < t_source_start (the underlying inequality producing the flag).
    {
        validation::NumericAssertion a;
        a.name           = "t_emit_below_source_start";
        // Measured: 1 if t_emit < t_source_start, 0 otherwise.
        a.measured_value = (obs.t_emit < t_source_start_) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 t_emit < body t_source_start condition";
        a.libastra_call  = "observe().t_emit < t_source_start";
        out.push_back(a);
    }

    // 4) NOT beyond_hubble_horizon (body is close, well inside Hubble).
    {
        validation::NumericAssertion a;
        a.name           = "not_beyond_hubble_horizon";
        a.measured_value = obs.beyond_hubble_horizon ? 1.0 : 0.0;
        a.expected_value = 0.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.12 Hubble flag; disjoint from §3.11";
        a.libastra_call  = "astra::observe(...).beyond_hubble_horizon";
        out.push_back(a);
    }

    // 5) time_reversed flag is true (apparent_rate < 0).
    {
        validation::NumericAssertion a;
        a.name           = "time_reversed_at_8000c";
        a.measured_value = obs.time_reversed ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 time_reversed flag (paired with retarded-time)";
        a.libastra_call  = "astra::observe(...).time_reversed";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S07_Warp8000cHistoryBound::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    // The headline check: at the planet's former screen position (center),
    // the pixel is background — the planet is GONE not faded.
    int cx = last_viewport_w_  / 2;
    int cy = last_viewport_h_  / 2;

    auto add = [&](const char* nm, int ch, float expected) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = cx;
        a.framebuffer_y  = cy;
        a.channel        = ch;
        a.expected_value = expected;
        a.tolerance      = kPixelTol;
        a.spec_section   = "§3.11 discrete disappearance (no fade) — §6 S07 acceptance #3";
        a.libastra_call  = "n/a (visual = background; planet absent because beyond_photon_history)";
        out.push_back(a);
    };
    add("center_is_background_R", 0, kBgR);
    add("center_is_background_G", 1, kBgG);
    add("center_is_background_B", 2, kBgB);

    return out;
}

}  // namespace astra::scenes
