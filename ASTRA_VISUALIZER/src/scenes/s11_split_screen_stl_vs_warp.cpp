// src/scenes/s11_split_screen_stl_vs_warp.cpp

#include "scenes/s11_split_screen_stl_vs_warp.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "physics/redshift.h"

#include <glad/gl.h>

#include <cmath>

namespace astra::scenes {

namespace {

constexpr float kPixelTol = 0.04f;

}  // namespace

void S11_SplitScreenStlVsWarp::setup() {
    z_kin_stl_ = static_cast<float>(astra::compute_z_kin(beta_ * astra::C_LIGHT));

    planet_ = {
        // Centered in each panel (NDC 0,0 relative to the panel's viewport).
        {"planet", 0.0f, 0.0f, 0.18f, kPlanetR, kPlanetG, kPlanetB},
    };

    starfield_.setup();
    placeholders_renderer_.setup();
}

void S11_SplitScreenStlVsWarp::tick(float /*dt_seconds*/) {}

void S11_SplitScreenStlVsWarp::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;

    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    int half_w = viewport_width / 2;

    // LEFT half — STL_REL (Doppler redshift visible on planet).
    glViewport(0, 0, half_w, viewport_height);
    starfield_.render(z_kin_stl_);
    placeholders_renderer_.render(half_w, viewport_height, planet_, z_kin_stl_);

    // RIGHT half — WARP_CRUISE (no kinematic redshift; bubble crew gamma=1).
    glViewport(half_w, 0, viewport_width - half_w, viewport_height);
    starfield_.render(/*z_kin=*/0.0f);
    placeholders_renderer_.render(viewport_width - half_w, viewport_height,
                                  planet_, /*z_kin=*/0.0f);

    // Restore full-viewport for any subsequent ImGui rendering.
    glViewport(0, 0, viewport_width, viewport_height);
}

void S11_SplitScreenStlVsWarp::teardown() {
    placeholders_renderer_.teardown();
    starfield_.teardown();
    planet_.clear();
}

std::vector<validation::NumericAssertion> S11_SplitScreenStlVsWarp::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;

    // 1) STL_REL apparent_rate at beta=0.5 == sqrt(1/3).
    {
        validation::NumericAssertion a;
        a.name           = "stl_rel_apparent_rate_at_beta_05";
        a.measured_value = compute_apparent_rate(beta_ * C_LIGHT, R_STL_REL);
        a.expected_value = std::sqrt(1.0 / 3.0);
        a.tolerance      = 1e-10;
        a.spec_section   = "§3.11 STL_REL apparent rate; §10 validation row";
        a.libastra_call  = "astra::compute_apparent_rate(0.5*C_LIGHT, R_STL_REL)";
        out.push_back(a);
    }

    // 2) WARP_CRUISE apparent_rate at v_app=0.5c == 0.5.
    {
        validation::NumericAssertion a;
        a.name           = "warp_cruise_apparent_rate_at_v05c";
        a.measured_value = compute_apparent_rate(beta_ * C_LIGHT, R_WARP_CRUISE);
        a.expected_value = 0.5;
        a.tolerance      = 1e-10;
        a.spec_section   = "§3.11 WARP apparent rate (classical retarded-time)";
        a.libastra_call  = "astra::compute_apparent_rate(0.5*C_LIGHT, R_WARP_CRUISE)";
        out.push_back(a);
    }

    // 3) STL rate > WARP rate (the canonical distinction at same v_radial).
    {
        validation::NumericAssertion a;
        a.name           = "stl_rate_greater_than_warp_rate_at_same_v";
        double stl = compute_apparent_rate(beta_ * C_LIGHT, R_STL_REL);
        double wrp = compute_apparent_rate(beta_ * C_LIGHT, R_WARP_CRUISE);
        a.measured_value = (stl > wrp) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.11 regime-distinction; §6 S11 acceptance #5";
        a.libastra_call  = "compute_apparent_rate(0.5c, R_STL_REL) > compute_apparent_rate(0.5c, R_WARP_CRUISE)";
        out.push_back(a);
    }

    // 4) Rate ratio (STL/WARP) at beta=0.5 ~= 1.155 (sqrt(1/3) / 0.5 = 2/sqrt(3)).
    {
        validation::NumericAssertion a;
        a.name           = "stl_over_warp_rate_ratio";
        double stl = compute_apparent_rate(beta_ * C_LIGHT, R_STL_REL);
        double wrp = compute_apparent_rate(beta_ * C_LIGHT, R_WARP_CRUISE);
        a.measured_value = stl / wrp;
        a.expected_value = 2.0 / std::sqrt(3.0);  // 2/sqrt(3) ~= 1.1547
        a.tolerance      = 1e-10;
        a.spec_section   = "§10 validation row (STL_REL was NOT 1/gamma)";
        a.libastra_call  = "stl_rate / warp_rate at v=0.5c";
        out.push_back(a);
    }

    // 5) z_kin at beta=0.5 (used to color the left-half planet) matches libastra.
    {
        validation::NumericAssertion a;
        a.name           = "z_kin_at_beta_05";
        a.measured_value = compute_z_kin(beta_ * C_LIGHT);
        a.expected_value = std::sqrt((1.0 + beta_) / (1.0 - beta_)) - 1.0;
        a.tolerance      = 1e-10;
        a.spec_section   = "§3.4 SR longitudinal Doppler";
        a.libastra_call  = "astra::compute_z_kin(0.5 * C_LIGHT)";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S11_SplitScreenStlVsWarp::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    // LEFT half center pixel: STL planet with redshift applied.
    int half_w = last_viewport_w_ / 2;
    int left_cx  = half_w / 2;
    int center_y = last_viewport_h_ / 2;
    physics::RGB shifted = physics::apply_kin_redshift(
        physics::RGB{kPlanetR, kPlanetG, kPlanetB}, z_kin_stl_);

    auto add = [&](const char* nm, int x, int y, int ch, float expected,
                   const char* spec) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = x;
        a.framebuffer_y  = y;
        a.channel        = ch;
        a.expected_value = expected;
        a.tolerance      = kPixelTol;
        a.spec_section   = spec;
        a.libastra_call  = "regime-dispatched render: STL_REL with z_kin vs WARP_CRUISE bare";
        out.push_back(a);
    };
    add("left_stl_planet_R", left_cx, center_y, 0, shifted.r, "§6 S11 left panel: STL_REL redshifted");
    add("left_stl_planet_G", left_cx, center_y, 1, shifted.g, "§6 S11 left panel: STL_REL redshifted");
    add("left_stl_planet_B", left_cx, center_y, 2, shifted.b, "§6 S11 left panel: STL_REL redshifted");

    // RIGHT half center pixel: WARP planet with NO redshift (bubble crew gamma=1).
    int right_cx = half_w + (last_viewport_w_ - half_w) / 2;
    add("right_warp_planet_R", right_cx, center_y, 0, kPlanetR,
        "§6 S11 right panel: WARP_CRUISE bare (no kin shift)");
    add("right_warp_planet_G", right_cx, center_y, 1, kPlanetG,
        "§6 S11 right panel: WARP_CRUISE bare");
    add("right_warp_planet_B", right_cx, center_y, 2, kPlanetB,
        "§6 S11 right panel: WARP_CRUISE bare");

    return out;
}

}  // namespace astra::scenes
