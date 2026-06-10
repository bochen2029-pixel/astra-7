// src/scenes/s04_warp_charge.cpp — V1.6 minimal bubble visualization.
//
// Bubble rendered as a centered fullscreen quad whose fragment shader draws
// a soft disc with radius + intensity proportional to W. At W=0 nothing
// visible; at W=1 a warm violet bubble fills ~half the viewport with a
// brighter core.
//
// V1.7+ will replace the analytic bubble with a CFD-RBF eval per spec §6
// step 3 (RBF spatial-hash). For now the bubble is a stand-in.

#include "scenes/s04_warp_charge.h"

#include "astra_nexus/composition.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "renderer/gl_helpers.h"
#include "util/log.h"

#include <glad/gl.h>

#include <algorithm>
#include <cstdio>

namespace astra::scenes {

namespace {

// Vertex shader: NDC quad with X squashed by aspect (h/w) so the quad
// renders pixel-square. v_local stays in [-1, +1] within the rendered quad.
const char* kVS = R"(#version 460 core
layout(location=0) in vec2 a_pos;
out vec2 v_local;
uniform float u_aspect;  // height / width
void main() {
    v_local = a_pos;
    vec2 p  = a_pos;
    p.x    *= u_aspect;  // squash to pixel-square
    gl_Position = vec4(p, 0.0, 1.0);
}
)";

// Fragment shader: soft circular bubble; brightness proportional to W.
// V1.10: alpha = smoothstep(0.05, 0.4, intensity) so bubble core stays
// opaque (preserves pixel assertions) while halo blends with background.
const char* kFS = R"(#version 460 core
in  vec2 v_local;
out vec4 frag;
uniform float u_W;       // [0, 1]
uniform vec3  u_color;   // bubble core color
void main() {
    float r = length(v_local);

    float radius_outer = mix(0.05, 0.85, u_W);
    float radius_inner = radius_outer * 0.60;

    float core = 1.0 - smoothstep(0.0, radius_inner, r);
    float halo = 1.0 - smoothstep(radius_inner, radius_outer, r);

    float intensity = u_W * (core + 0.5 * (halo - core));
    intensity       = clamp(intensity, 0.0, 1.0);

    vec3 col = u_color * intensity
             + vec3(0.95, 0.85, 1.00) * core * u_W * 0.35;
    // V1.14: linear-saturating alpha curve removes the halo-ring artifact
    // that smoothstep(0.05, 0.4) left at the alpha-saturation boundary.
    // Bubble center (intensity >= 0.8) stays opaque -> assertions stable.
    float alpha = clamp(intensity * 1.25, 0.0, 1.0);
    frag = vec4(col, alpha);
}
)";

}  // namespace

void S04_WarpCharge::setup() {
    sim_time_seconds_ = 0.0;
    current_W_        = 0.0f;
    cruise_engaged_   = false;

    std::string err;
    program_ = renderer::compile_program(kVS, kFS, &err);
    if (!program_) {
        log::error("S04 shader compile/link: %s", err.c_str());
        return;
    }
    renderer::create_unit_quad(&vao_, &vbo_);
    loc_W_      = glGetUniformLocation(program_, "u_W");
    loc_color_  = glGetUniformLocation(program_, "u_color");
    loc_aspect_ = glGetUniformLocation(program_, "u_aspect");
}

void S04_WarpCharge::tick(float dt_seconds) {
    sim_time_seconds_ += static_cast<double>(dt_seconds);
    // W ramps linearly 0 -> 1 over the first 5 seconds, then holds at 1.
    if (sim_time_seconds_ < 5.0) {
        current_W_ = static_cast<float>(sim_time_seconds_ / 5.0);
        cruise_engaged_ = false;
    } else {
        current_W_      = 1.0f;
        cruise_engaged_ = true;  // regime: WARP_CRUISE
    }
}

void S04_WarpCharge::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;

    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    if (!program_ || !vao_) return;
    float aspect = (viewport_width > 0)
                     ? static_cast<float>(viewport_height) / static_cast<float>(viewport_width)
                     : 1.0f;

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glUseProgram(program_);
    glUniform1f(loc_W_,      current_W_);
    glUniform3f(loc_color_,  kBubbleCoreR, kBubbleCoreG, kBubbleCoreB);
    glUniform1f(loc_aspect_, aspect);
    renderer::draw_unit_quad(vao_);
    glUseProgram(0);
    glDisable(GL_BLEND);
}

void S04_WarpCharge::teardown() {
    if (program_) { glDeleteProgram(program_); program_ = 0; }
    if (vbo_)     { glDeleteBuffers(1, &vbo_); vbo_ = 0; }
    if (vao_)     { glDeleteVertexArrays(1, &vao_); vao_ = 0; }
}

std::vector<validation::NumericAssertion> S04_WarpCharge::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;

    // After headless_warmup (5s) the ramp is complete.
    {
        validation::NumericAssertion a;
        a.name           = "W_at_t5s_equals_1";
        a.measured_value = current_W_;
        a.expected_value = 1.0;
        a.tolerance      = 1e-6;
        a.spec_section   = "§3.3 regime WARP_CHARGE ramp 0..5s";
        a.libastra_call  = "S04::current_W_ after tick(5s) warmup";
        out.push_back(a);
    }

    // Regime transition flag flipped to WARP_CRUISE at t=5s.
    {
        validation::NumericAssertion a;
        a.name           = "regime_at_t5s_is_cruise";
        a.measured_value = cruise_engaged_ ? static_cast<double>(R_WARP_CRUISE) : 0.0;
        a.expected_value = static_cast<double>(R_WARP_CRUISE);
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.3 regime transition WARP_CHARGE -> WARP_CRUISE";
        a.libastra_call  = "S04::cruise_engaged_ == true -> R_WARP_CRUISE (0x08)";
        out.push_back(a);
    }

    // Libastra-derived: dtau/dt at W=1, no gravity, gamma=1, warp_active=true.
    //   f_warp(1) = max(0.5, 1 - 0.5*1*1) = 0.5
    //   dtau/dt = 0.5 * 1.0 / 1.0 = 0.5
    {
        validation::NumericAssertion a;
        a.name           = "dtau_dt_at_W1_cruise";
        a.measured_value = dtau_dt_cosmic(1.0, 1.0, 1.0, /*warp_active=*/true);
        a.expected_value = 0.5;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.2 composition rule + §3.5 f_warp canon";
        a.libastra_call  = "astra::dtau_dt_cosmic(1.0, 1.0, 1.0, true)";
        out.push_back(a);
    }

    // Libastra-derived: f_warp(1.0) = 0.5 by the canonical formula.
    {
        validation::NumericAssertion a;
        a.name           = "f_warp_at_W1_equals_half";
        a.measured_value = f_warp_canon(1.0);
        a.expected_value = 0.5;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.5 f_warp canon";
        a.libastra_call  = "astra::f_warp_canon(1.0)";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S04_WarpCharge::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;
    if (current_W_ < 0.999f) return out;  // Pre-warmup: bubble not at full

    int cx = last_viewport_w_  / 2;
    int cy = last_viewport_h_  / 2;

    // At center, with W=1 and core glow contribution:
    //   intensity ~ 1.0; col = u_color * 1.0 + warm-white * 0.35
    //   R = 0.55 * 1.0 + 0.95 * 0.35 = 0.55 + 0.3325 = 0.8825  (clamped < 1.0)
    //   G = 0.40 * 1.0 + 0.85 * 0.35 = 0.40 + 0.2975 = 0.6975
    //   B = 0.90 * 1.0 + 1.00 * 0.35 = 0.90 + 0.3500 = 1.0     (clamped to 1.0)
    auto add = [&](const char* nm, int ch, float expected) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = cx;
        a.framebuffer_y  = cy;
        a.channel        = ch;
        a.expected_value = expected;
        a.tolerance      = 0.04f;
        a.spec_section   = "§6 step 6 chaos modulation (V1.6 stand-in)";
        a.libastra_call  = "n/a (bubble visual; canonical post-FS color at W=1)";
        out.push_back(a);
    };
    add("bubble_center_R", 0, 0.8825f);
    add("bubble_center_G", 1, 0.6975f);
    add("bubble_center_B", 2, 1.0000f);
    return out;
}

}  // namespace astra::scenes
