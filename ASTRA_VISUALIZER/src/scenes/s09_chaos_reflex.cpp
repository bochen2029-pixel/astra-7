// src/scenes/s09_chaos_reflex.cpp

#include "scenes/s09_chaos_reflex.h"

#include "renderer/gl_helpers.h"
#include "util/log.h"

#include <glad/gl.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

namespace astra::scenes {

namespace {

constexpr float kPixelTol = 0.04f;

// Vertex shader: NDC quad with aspect squash so heatmap is pixel-square.
const char* kVS = R"(#version 460 core
layout(location=0) in vec2 a_pos;
out vec2 v_uv;
uniform float u_aspect;
void main() {
    v_uv = a_pos * 0.5 + 0.5;     // [-1,+1] -> [0,1] texture coords
    vec2 p = a_pos;
    p.x   *= u_aspect;
    gl_Position = vec4(p, 0.0, 1.0);
}
)";

// Fragment shader: samples the R32F chaos texture + applies viridis colormap.
// Viridis is approximated via piecewise linear interpolation between 5
// canonical color stops. Within ~3% of the matplotlib viridis at every t.
const char* kFS = R"(#version 460 core
in  vec2 v_uv;
out vec4 frag;
uniform sampler2D u_tex;

vec3 viridis(float t) {
    t = clamp(t, 0.0, 1.0);
    const vec3 c0 = vec3(0.267, 0.005, 0.329);
    const vec3 c1 = vec3(0.231, 0.322, 0.545);
    const vec3 c2 = vec3(0.129, 0.565, 0.553);
    const vec3 c3 = vec3(0.369, 0.788, 0.384);
    const vec3 c4 = vec3(0.992, 0.906, 0.145);
    vec3 col;
    if      (t < 0.25) col = mix(c0, c1, (t       ) * 4.0);
    else if (t < 0.50) col = mix(c1, c2, (t - 0.25) * 4.0);
    else if (t < 0.75) col = mix(c2, c3, (t - 0.50) * 4.0);
    else               col = mix(c3, c4, (t - 0.75) * 4.0);
    return col;
}

void main() {
    float v = texture(u_tex, v_uv).r;
    frag = vec4(viridis(v), 1.0);
}
)";

// Same viridis function on CPU — used to compute pixel-assertion expected
// values from the chaos field state. Keep in sync with the GLSL above.
struct Rgb { float r, g, b; };
Rgb mix3(Rgb a, Rgb b, float t) {
    return Rgb{a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t};
}
Rgb viridis_cpu(float t) {
    t = std::clamp(t, 0.0f, 1.0f);
    const Rgb c0{0.267f, 0.005f, 0.329f};
    const Rgb c1{0.231f, 0.322f, 0.545f};
    const Rgb c2{0.129f, 0.565f, 0.553f};
    const Rgb c3{0.369f, 0.788f, 0.384f};
    const Rgb c4{0.992f, 0.906f, 0.145f};
    if      (t < 0.25f) return mix3(c0, c1, (t        ) * 4.0f);
    else if (t < 0.50f) return mix3(c1, c2, (t - 0.25f) * 4.0f);
    else if (t < 0.75f) return mix3(c2, c3, (t - 0.50f) * 4.0f);
    else                return mix3(c3, c4, (t - 0.75f) * 4.0f);
}

}  // namespace

void S09_ChaosReflex::setup() {
    sim_time_seconds_ = 0.0;
    reflex_enabled_   = false;

    chaos_.init(kGridW, kGridH);

    std::string err;
    program_ = renderer::compile_program(kVS, kFS, &err);
    if (!program_) {
        log::error("S09 shader: %s", err.c_str());
        return;
    }
    renderer::create_unit_quad(&vao_, &vbo_);
    loc_tex_    = glGetUniformLocation(program_, "u_tex");
    loc_aspect_ = glGetUniformLocation(program_, "u_aspect");

    glGenTextures(1, &texture_);
    glBindTexture(GL_TEXTURE_2D, texture_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, kGridW, kGridH, 0,
                 GL_RED, GL_FLOAT, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,     GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,     GL_REPEAT);
    glBindTexture(GL_TEXTURE_2D, 0);
}

void S09_ChaosReflex::tick(float dt_seconds) {
    sim_time_seconds_ += static_cast<double>(dt_seconds);

    // RK2 PDE step. CFL bound at D=0.25, dx=1: dt < 1.0; 60Hz dt=0.0167 is safe.
    chaos_.step_rk2(dt_seconds, kDiffusion, kAlphaBase);

    // Reflex stabilizer: enabled at t >= 5s.
    if (sim_time_seconds_ >= kReflexStart) {
        reflex_enabled_ = true;
        chaos_.apply_uniform_damping(kReflexRate, dt_seconds);
    }
}

void S09_ChaosReflex::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    if (!program_ || !vao_ || !texture_) return;

    // Upload current chaos field to GL texture.
    glBindTexture(GL_TEXTURE_2D, texture_);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, kGridW, kGridH,
                    GL_RED, GL_FLOAT, chaos_.data().data());
    glBindTexture(GL_TEXTURE_2D, 0);

    float aspect = (viewport_width > 0)
                     ? static_cast<float>(viewport_height) / static_cast<float>(viewport_width)
                     : 1.0f;
    glUseProgram(program_);
    glUniform1f(loc_aspect_, aspect);
    glUniform1i(loc_tex_, 0);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, texture_);
    renderer::draw_unit_quad(vao_);
    glBindTexture(GL_TEXTURE_2D, 0);
    glUseProgram(0);
}

void S09_ChaosReflex::teardown() {
    if (texture_)  { glDeleteTextures(1, &texture_); texture_ = 0; }
    if (program_)  { glDeleteProgram(program_); program_ = 0; }
    if (vbo_)      { glDeleteBuffers(1, &vbo_); vbo_ = 0; }
    if (vao_)      { glDeleteVertexArrays(1, &vao_); vao_ = 0; }
}

std::vector<validation::NumericAssertion> S09_ChaosReflex::numeric_assertions() const {
    std::vector<validation::NumericAssertion> out;

    // 1) Chaos field bounded in [0, 1] (Fisher-KPP analytic invariant).
    {
        validation::NumericAssertion a;
        a.name           = "chaos_field_max_in_bounds";
        a.measured_value = chaos_.max_value();
        a.expected_value = 0.5;     // approximate target: well below 1.0 because Reflex damped
        a.tolerance      = 0.5;     // wide tolerance — just asserts max in [0, 1]
        a.spec_section   = "§7.1 Fisher-KPP analytic invariant; §6 S09 acceptance #1";
        a.libastra_call  = "ChaosField::max_value() <= 1.0";
        out.push_back(a);
    }

    // 2) Chaos field max > 0 (proves PDE actually evolved from seed).
    {
        validation::NumericAssertion a;
        a.name           = "chaos_field_max_above_zero";
        a.measured_value = (chaos_.max_value() > 0.001f) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§7.1 PDE evolution from seed";
        a.libastra_call  = "ChaosField::max_value() > 0.001";
        out.push_back(a);
    }

    // 3) Reflex enabled at canonical t=8s (3s past kReflexStart=5).
    {
        validation::NumericAssertion a;
        a.name           = "reflex_enabled_at_t8s";
        a.measured_value = reflex_enabled_ ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§2.3.1 Reflex Contract; §6 S09 acceptance #6";
        a.libastra_call  = "S09::reflex_enabled_ at t > kReflexStart";
        out.push_back(a);
    }

    // 4) Mean chaos at t=8s is below the (undamped) saturated value (Reflex worked).
    //    Without Reflex, mean would converge toward ~1.0. With Reflex damping
    //    applied 3s at rate 0.5, mean should be substantially below 1.0.
    {
        validation::NumericAssertion a;
        a.name           = "reflex_lowered_mean_below_saturation";
        a.measured_value = (chaos_.mean_value() < 0.9f) ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§6 S09 acceptance #6 (Reflex damps chaos toward target)";
        a.libastra_call  = "ChaosField::mean_value() < 0.9 (Reflex active for 3s)";
        out.push_back(a);
    }

    // 5) Chaos field non-NaN (sentinel against numerical blowup).
    {
        validation::NumericAssertion a;
        a.name           = "chaos_field_non_nan";
        bool any_nan = false;
        for (float v : chaos_.data()) {
            if (std::isnan(v) || std::isinf(v)) { any_nan = true; break; }
        }
        a.measured_value = any_nan ? 0.0 : 1.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§4.4 CFL stability; §6 S09 acceptance #1 sentinel";
        a.libastra_call  = "all !isnan(ChaosField::data())";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S09_ChaosReflex::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;

    // Pixel at the heatmap CENTER (matches the chaos field center cell).
    // Since the quad is aspect-squashed in X, the heatmap occupies the
    // CENTRAL pixel-square area; framebuffer center maps to texture (0.5,0.5)
    // which maps to grid (kGridW/2, kGridH/2).
    float chaos_at_center = chaos_.at(kGridW / 2, kGridH / 2);
    Rgb expected = viridis_cpu(chaos_at_center);

    int cx = last_viewport_w_ / 2;
    int cy = last_viewport_h_ / 2;
    auto add = [&](const char* nm, int ch, float exp) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = cx;
        a.framebuffer_y  = cy;
        a.channel        = ch;
        a.expected_value = exp;
        a.tolerance      = kPixelTol;
        a.spec_section   = "§7.1 chaos heatmap; viridis(chaos at center grid cell)";
        a.libastra_call  = "viridis_cpu(ChaosField::at(W/2, H/2))";
        out.push_back(a);
    };
    add("heatmap_center_R", 0, expected.r);
    add("heatmap_center_G", 1, expected.g);
    add("heatmap_center_B", 2, expected.b);

    return out;
}

}  // namespace astra::scenes
