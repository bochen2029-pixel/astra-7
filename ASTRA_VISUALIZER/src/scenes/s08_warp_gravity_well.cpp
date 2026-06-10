// src/scenes/s08_warp_gravity_well.cpp

#include "scenes/s08_warp_gravity_well.h"

#include "astra_nexus/composition.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/regime.h"
#include "renderer/gl_helpers.h"
#include "util/log.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdio>

namespace astra::scenes {

namespace {

constexpr float kPixelTol = 0.04f;

const char* kBubbleVS = R"(#version 460 core
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

const char* kBubbleFS = R"(#version 460 core
in  vec2 v_local;
out vec4 frag;
uniform float u_W;
uniform vec3  u_color;
void main() {
    float r = length(v_local);
    float radius_outer = mix(0.05, 0.42, u_W);
    float radius_inner = radius_outer * 0.60;
    float core = 1.0 - smoothstep(0.0, radius_inner, r);
    float halo = 1.0 - smoothstep(radius_inner, radius_outer, r);
    float intensity = u_W * (core + 0.5 * (halo - core));
    intensity = clamp(intensity, 0.0, 1.0);
    vec3 col = u_color * intensity
             + vec3(0.95, 0.85, 1.00) * core * u_W * 0.30;
    // V1.14: linear-saturating alpha removes V1.10's smoothstep halo ring.
    // At bubble center (W=0.8 -> intensity~0.8), alpha saturates to 1
    // (intensity*1.25 = 1.0); halo fades smoothly into background.
    float alpha = clamp(intensity * 1.25, 0.0, 1.0);
    frag = vec4(col, alpha);
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

// Build a BH list at the canonical scene configuration.
std::vector<astra::BHEntry> make_bh_list() {
    using namespace astra;
    double M = 10.0 * M_SUN;
    double rs = schwarzschild_r(M);
    std::vector<BHEntry> bh;
    bh.push_back({M, {25.0 * rs, 0.0, 0.0}});  // ship at origin; BH 25*r_s away
    return bh;
}

}  // namespace

void S08_WarpGravityWell::setup() {
    placeholders_ = {
        {"bh", kBhNdcX, kBhNdcY, kBhSize, 0.0f, 0.0f, 0.0f},
    };
    starfield_.setup();
    placeholders_renderer_.setup();

    std::string err;
    bubble_program_ = renderer::compile_program(kBubbleVS, kBubbleFS, &err);
    if (!bubble_program_) {
        log::error("S08 bubble shader: %s", err.c_str());
        return;
    }
    renderer::create_unit_quad(&bubble_vao_, &bubble_vbo_);
    loc_W_      = glGetUniformLocation(bubble_program_, "u_W");
    loc_aspect_ = glGetUniformLocation(bubble_program_, "u_aspect");
    loc_color_  = glGetUniformLocation(bubble_program_, "u_color");
}

void S08_WarpGravityWell::tick(float /*dt_seconds*/) {}

void S08_WarpGravityWell::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;

    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    starfield_.render(/*z_kin=*/0.0f);

    // Bubble at center.
    if (bubble_program_ && bubble_vao_) {
        float aspect = (viewport_width > 0)
                         ? static_cast<float>(viewport_height) / static_cast<float>(viewport_width)
                         : 1.0f;
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glUseProgram(bubble_program_);
        glUniform1f(loc_W_,      static_cast<float>(W_));
        glUniform1f(loc_aspect_, aspect);
        glUniform3f(loc_color_,  kBubbleR, kBubbleG, kBubbleB);
        renderer::draw_unit_quad(bubble_vao_);
        glUseProgram(0);
        glDisable(GL_BLEND);
    }

    // BH placeholder (overdraws starfield where the disc lands).
    placeholders_renderer_.render(viewport_width, viewport_height,
                                  placeholders_, /*z_kin=*/0.0f);
}

void S08_WarpGravityWell::teardown() {
    if (bubble_program_) { glDeleteProgram(bubble_program_); bubble_program_ = 0; }
    if (bubble_vbo_)     { glDeleteBuffers(1, &bubble_vbo_); bubble_vbo_ = 0; }
    if (bubble_vao_)     { glDeleteVertexArrays(1, &bubble_vao_); bubble_vao_ = 0; }
    placeholders_renderer_.teardown();
    starfield_.teardown();
    placeholders_.clear();
}

std::vector<validation::NumericAssertion> S08_WarpGravityWell::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;

    auto bh_list = make_bh_list();
    double M = 10.0 * M_SUN;
    double rs = schwarzschild_r(M);
    double r = r_over_rs_ * rs;
    double grav = compute_grav_factor(bh_list, Vec3{0, 0, 0});

    // 1) schwarzschild_r at 10 M_sun matches the closed-form 2GM/c^2.
    {
        validation::NumericAssertion a;
        a.name           = "schwarzschild_r_at_10Msun";
        a.measured_value = rs;
        a.expected_value = 2.0 * G_GRAV * M / (C_LIGHT * C_LIGHT);
        a.tolerance      = 1e-3;  // ~30km value; tolerance loose for double-precision
        a.spec_section   = "§3.2 Schwarzschild factor; libastra schwarzschild_r";
        a.libastra_call  = "astra::schwarzschild_r(10 * M_SUN)";
        out.push_back(a);
    }

    // 2) grav_factor at r=25*r_s matches sqrt(1 - r_s/r) = sqrt(0.96) ~= 0.9798.
    {
        validation::NumericAssertion a;
        a.name           = "grav_factor_at_r25rs";
        a.measured_value = grav;
        a.expected_value = std::sqrt(1.0 - rs / r);  // closed-form
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.2 dominant-BH Schwarzschild composition";
        a.libastra_call  = "astra::compute_grav_factor(bh_list, ship_pos)";
        out.push_back(a);
    }

    // 3) grav_factor < 0.99 -> composite regime includes GRAVITY_WELL bit (per stdio_server::detect_regime).
    {
        validation::NumericAssertion a;
        a.name           = "grav_well_bit_activates";
        // Reproduce the detect_regime logic: bit set when grav_factor < 0.99.
        uint32_t composite = R_WARP_CRUISE | ((grav < 0.99) ? R_GRAVITY_WELL : 0u);
        a.measured_value  = static_cast<double>(composite);
        a.expected_value  = static_cast<double>(R_WARP_CRUISE | R_GRAVITY_WELL);  // 0x28 = 40
        a.tolerance       = 1e-9;
        a.spec_section    = "§3.3 detect_regime composite (G5 audit); WARP_CRUISE | GRAVITY_WELL";
        a.libastra_call   = "detect_regime logic: WARP_CRUISE | (grav<0.99 ? GRAVITY_WELL : 0)";
        out.push_back(a);
    }

    // 4) Full composition dtau/dt = f_warp(0.8) * grav / gamma_kin = 0.68 * 0.9798 / 1.0.
    {
        validation::NumericAssertion a;
        a.name           = "dtau_dt_warp_plus_gravity";
        a.measured_value = dtau_dt_cosmic(W_, grav, /*gamma_kin=*/1.0, /*warp_active=*/true);
        a.expected_value = f_warp_canon(W_) * grav / 1.0;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.2 composition rule full (warp + grav + STL)";
        a.libastra_call  = "astra::dtau_dt_cosmic(0.8, grav_factor, 1.0, true)";
        out.push_back(a);
    }

    // 5) f_warp(0.8) = 1 - 0.5*0.64 = 0.68 (NOT clamped to 0.5; W < W_threshold).
    {
        validation::NumericAssertion a;
        a.name           = "f_warp_at_W08";
        a.measured_value = f_warp_canon(W_);
        a.expected_value = 1.0 - 0.5 * W_ * W_;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.5 f_warp canon defaults";
        a.libastra_call  = "astra::f_warp_canon(0.8)";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S08_WarpGravityWell::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    // Bubble center color at W=0.8 with the warm-tinted core:
    //   intensity ~ 0.8 (at r=0 inner core fully on, halo=core)
    //   col = color * intensity + warm_white * core * 0.8 * 0.30
    //   R = 0.65*0.8 + 0.95*1.0*0.8*0.30 = 0.52 + 0.228  = 0.748
    //   G = 0.45*0.8 + 0.85*1.0*0.8*0.30 = 0.36 + 0.204  = 0.564
    //   B = 0.75*0.8 + 1.00*1.0*0.8*0.30 = 0.60 + 0.240  = 0.840
    int cx = last_viewport_w_  / 2;
    int cy = last_viewport_h_  / 2;
    auto add_b = [&](const char* nm, int ch, float expected) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = cx;
        a.framebuffer_y  = cy;
        a.channel        = ch;
        a.expected_value = expected;
        a.tolerance      = kPixelTol;
        a.spec_section   = "§6 step 6 bubble core (warm-tinted under gravity well)";
        a.libastra_call  = "n/a (canonical bubble core RGB at W=0.8)";
        out.push_back(a);
    };
    add_b("bubble_core_R", 0, 0.748f);
    add_b("bubble_core_G", 1, 0.564f);
    add_b("bubble_core_B", 2, 0.840f);

    // BH center: pure black (no light from event horizon).
    int bh_cx = ndc_x_to_topleft(kBhNdcX, last_viewport_w_);
    int bh_cy = ndc_y_to_topleft(kBhNdcY, last_viewport_h_);
    auto add_bh = [&](const char* nm, int ch) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = bh_cx;
        a.framebuffer_y  = bh_cy;
        a.channel        = ch;
        a.expected_value = 0.0f;
        a.tolerance      = kPixelTol;
        a.spec_section   = "§7.4 warp exclusion zone; event-horizon disc (no light escape)";
        a.libastra_call  = "n/a (BH placeholder = pure black)";
        out.push_back(a);
    };
    add_bh("bh_event_horizon_R", 0);
    add_bh("bh_event_horizon_G", 1);
    add_bh("bh_event_horizon_B", 2);

    return out;
}

}  // namespace astra::scenes
