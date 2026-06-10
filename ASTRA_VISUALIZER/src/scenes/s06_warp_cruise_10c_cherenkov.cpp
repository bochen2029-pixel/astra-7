// src/scenes/s06_warp_cruise_10c_cherenkov.cpp

#include "scenes/s06_warp_cruise_10c_cherenkov.h"

#include "astra_nexus/cherenkov.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "renderer/gl_helpers.h"
#include "util/log.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdio>
#include <string>

namespace astra::scenes {

namespace {

constexpr float kPixelTol = 0.04f;

const char* kVS = R"(#version 460 core
layout(location=0) in vec2 a_pos;
out vec2 v_local;
uniform float u_aspect;
void main() {
    v_local = a_pos;
    vec2 p  = a_pos;
    p.x    *= u_aspect;
    gl_Position = vec4(p, 0.0, 1.0);
}
)";

// Bubble + Cherenkov cone overlay in a single FS pass.
//   Bubble: S04-style soft disc, scaled by W.
//   Cone:   forward-facing wedge (axis = +y NDC) with half-angle = u_cone_rad.
//           Cyan tint, additive. Only fragments with y > 0 inside the wedge
//           receive the tint. When u_cone_rad < 0 the cone is inactive
//           (libastra signals this with -1.0).
const char* kFS = R"(#version 460 core
in  vec2 v_local;
out vec4 frag;
uniform float u_W;
uniform vec3  u_color;
uniform float u_cone_rad;  // half-angle in radians; <0 if inactive
void main() {
    float r = length(v_local);

    // Bubble (S04 pattern).
    float radius_outer = mix(0.05, 0.45, u_W);
    float radius_inner = radius_outer * 0.60;
    float core = 1.0 - smoothstep(0.0, radius_inner, r);
    float halo = 1.0 - smoothstep(radius_inner, radius_outer, r);
    float intensity = u_W * (core + 0.5 * (halo - core));
    intensity = clamp(intensity, 0.0, 1.0);
    vec3 bubble = u_color * intensity
                + vec3(0.95, 0.85, 1.00) * core * u_W * 0.35;

    // Cherenkov cone overlay (forward = +y).
    vec3 cone = vec3(0.0);
    if (u_cone_rad > 0.0) {
        // Angle of this fragment from the +y axis (forward direction).
        // atan(|x|, y) maps to [0, pi/2] for y > 0, [pi/2, pi] for y < 0.
        float angle_from_axis = atan(abs(v_local.x), v_local.y);
        // Soft membership: 1 inside cone, 0 outside, smooth edge.
        float in_cone = 1.0 - smoothstep(u_cone_rad - 0.04, u_cone_rad + 0.04, angle_from_axis);
        // Only forward half (y > 0).
        in_cone *= step(0.0, v_local.y);
        // Attenuate by distance from origin so the cone has a soft fall-off.
        float fade = smoothstep(0.0, 0.05, r) * (1.0 - smoothstep(0.85, 1.0, r));
        cone = vec3(0.20, 0.85, 1.00) * in_cone * fade * 0.55;  // cyan, semi-transparent
    }

    vec3 final = bubble + cone;
    // V1.14: linear-saturating alpha; bubble core + cone surface stay opaque
    // (intensity >= 0.8 -> alpha = 1; preserves assertions), halo + cone-edge
    // fade smoothly without the smoothstep ring artifact V1.10 had.
    float bubble_alpha = clamp(intensity * 1.25, 0.0, 1.0);
    float cone_alpha   = clamp((cone.x + cone.y + cone.z) * 2.0, 0.0, 1.0);
    frag = vec4(final, max(bubble_alpha, cone_alpha));
}
)";

int ndc_y_to_topleft(float ndc_y, int h) {
    float t = 0.5f * (1.0f - ndc_y);
    int   y = static_cast<int>(t * (h - 1) + 0.5f);
    if (y < 0) y = 0;
    if (y >= h) y = h - 1;
    return y;
}
int ndc_x_to_topleft(float ndc_x, int w) {
    float t = 0.5f * (1.0f + ndc_x);
    int   x = static_cast<int>(t * (w - 1) + 0.5f);
    if (x < 0) x = 0;
    if (x >= w) x = w - 1;
    return x;
}

}  // namespace

void S06_WarpCruise10cCherenkov::setup() {
    cherenkov_angle_rad_ = astra::compute_cherenkov_angle(W_, v_app_over_c_, n_coef_);

    starfield_.setup();

    std::string err;
    program_ = renderer::compile_program(kVS, kFS, &err);
    if (!program_) {
        log::error("S06 shader compile/link: %s", err.c_str());
        return;
    }
    renderer::create_unit_quad(&vao_, &vbo_);
    loc_W_      = glGetUniformLocation(program_, "u_W");
    loc_cone_   = glGetUniformLocation(program_, "u_cone_rad");
    loc_aspect_ = glGetUniformLocation(program_, "u_aspect");
    loc_color_  = glGetUniformLocation(program_, "u_color");
}

void S06_WarpCruise10cCherenkov::tick(float /*dt_seconds*/) {}

void S06_WarpCruise10cCherenkov::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;

    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    // Light starfield in the background.
    starfield_.render(/*z_kin=*/0.0f);

    if (!program_ || !vao_) return;
    float aspect = (viewport_width > 0)
                     ? static_cast<float>(viewport_height) / static_cast<float>(viewport_width)
                     : 1.0f;
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glUseProgram(program_);
    glUniform1f(loc_W_,      static_cast<float>(W_));
    glUniform1f(loc_cone_,   static_cast<float>(cherenkov_angle_rad_));
    glUniform1f(loc_aspect_, aspect);
    glUniform3f(loc_color_,  0.55f, 0.40f, 0.90f);  // bubble core (matches S04)
    renderer::draw_unit_quad(vao_);
    glUseProgram(0);
    glDisable(GL_BLEND);
}

void S06_WarpCruise10cCherenkov::teardown() {
    if (program_) { glDeleteProgram(program_); program_ = 0; }
    if (vbo_)     { glDeleteBuffers(1, &vbo_); vbo_ = 0; }
    if (vao_)     { glDeleteVertexArrays(1, &vao_); vao_ = 0; }
    starfield_.teardown();
}

std::vector<validation::NumericAssertion> S06_WarpCruise10cCherenkov::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;

    // 1) Cherenkov angle at v_app=10c, W=1, n_coef=1:
    //    n = 2; n*beta = 20; cos(theta) = 0.05; theta = acos(0.05).
    {
        validation::NumericAssertion a;
        a.name           = "cherenkov_angle_at_v10c_W1";
        a.measured_value = cherenkov_angle_rad_;
        a.expected_value = std::acos(1.0 / 20.0);
        a.tolerance      = 1e-9;
        a.spec_section   = "§6 step 10 Cherenkov; AUDIT 5D-F4 closure";
        a.libastra_call  = "astra::compute_cherenkov_angle(1.0, 10.0, 1.0)";
        out.push_back(a);
    }

    // 2) Cone INACTIVE when n*beta <= 1 (sanity).
    {
        validation::NumericAssertion a;
        a.name           = "cherenkov_inactive_when_n_beta_le_1";
        a.measured_value = compute_cherenkov_angle(0.0, 0.5, 1.0);  // n=1, beta=0.5 -> n*beta=0.5
        a.expected_value = -1.0;
        a.tolerance      = 1e-12;
        a.spec_section   = "§6 step 10 inactive branch";
        a.libastra_call  = "astra::compute_cherenkov_angle(0.0, 0.5, 1.0)";
        out.push_back(a);
    }

    // 3) Apparent rate at v_app=10c WARP_CRUISE = -9.0 (paired effect; same scene).
    {
        validation::NumericAssertion a;
        a.name           = "apparent_rate_at_v10c";
        a.measured_value = compute_apparent_rate(v_app_over_c_ * C_LIGHT, R_WARP_CRUISE);
        a.expected_value = -9.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 apparent rate (WARP); paired with Cherenkov for S06";
        a.libastra_call  = "astra::compute_apparent_rate(10*C_LIGHT, R_WARP_CRUISE)";
        out.push_back(a);
    }

    // 4) Cone OPENS as W grows at fixed beta (mirrors test_cherenkov assertion).
    //    See KNOWN_ISSUES.md — spec wording says "narrows" but physics says "opens".
    {
        validation::NumericAssertion a;
        a.name           = "cone_opens_with_W_at_fixed_beta";
        double a_W050 = compute_cherenkov_angle(0.5, 0.8, 1.0);
        double a_W100 = compute_cherenkov_angle(1.0, 0.8, 1.0);
        // Measured: 1 if a(W=0.5) < a(W=1.0) [OPENS]; 0 otherwise.
        a.measured_value = (a_W050 > 0.0 && a_W100 > 0.0 && a_W050 < a_W100) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§6 step 10; v0.130 KNOWN_ISSUES finding (OPENS not narrows)";
        a.libastra_call  = "compute_cherenkov_angle(W=0.5, b=0.8) < compute_cherenkov_angle(W=1.0, b=0.8)";
        out.push_back(a);
    }

    // 5) Cone OPENS as beta grows at fixed n (W=1).
    {
        validation::NumericAssertion a;
        a.name           = "cone_opens_with_beta_at_fixed_W";
        double a_b055 = compute_cherenkov_angle(1.0, 0.55, 1.0);
        double a_b095 = compute_cherenkov_angle(1.0, 0.95, 1.0);
        a.measured_value = (a_b055 > 0.0 && a_b095 > 0.0 && a_b055 < a_b095) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§6 step 10; v0.130 KNOWN_ISSUES finding (OPENS not narrows)";
        a.libastra_call  = "compute_cherenkov_angle(W=1, b=0.55) < compute_cherenkov_angle(W=1, b=0.95)";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S06_WarpCruise10cCherenkov::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    // Bubble center color (W=1): same calculation as S04 — see s04_warp_charge.cpp.
    //   R = 0.55 + 0.95*0.35 = 0.8825
    //   G = 0.40 + 0.85*0.35 = 0.6975
    //   B = 0.90 + 1.00*0.35 = 1.0 (clamped)
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
        a.spec_section   = "§6 step 6 + step 10 (bubble core + Cherenkov tint)";
        a.libastra_call  = "n/a (visual baseline; canonical bubble core RGB)";
        out.push_back(a);
    };
    add("bubble_core_R", 0, 0.8825f);
    add("bubble_core_G", 1, 0.6975f);
    add("bubble_core_B", 2, 1.0000f);

    return out;
}

}  // namespace astra::scenes
