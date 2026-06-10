// src/renderer/starfield_renderer.cpp

#include "renderer/starfield_renderer.h"
#include "renderer/gl_helpers.h"
#include "physics/redshift.h"
#include "util/log.h"

#include <glad/gl.h>

#include <random>
#include <string>
#include <vector>

namespace astra::renderer {

namespace {

const char* kVS = R"(#version 460 core
layout(location=0) in vec2  a_pos;
layout(location=1) in float a_brightness;
out float v_brightness;
void main() {
    v_brightness = a_brightness;
    gl_Position  = vec4(a_pos, 0.0, 1.0);
    gl_PointSize = 1.5;
}
)";

std::string compose_fs() {
    return std::string("#version 460 core\n")
        + physics::kGlslRedshiftFn
        + R"(
in  float v_brightness;
out vec4  frag;
uniform float u_z_kin;
void main() {
    float b = clamp(v_brightness, 0.0, 1.0);
    // Stars start as a faint cool-white; redshift applies linearly.
    vec3 cool_white = vec3(b, b, b * 1.05);
    vec3 shifted    = apply_kin_redshift(cool_white, u_z_kin);
    frag = vec4(shifted, 1.0);
}
)";
}

}  // namespace

bool StarfieldRenderer::setup(int count, uint32_t seed) {
    std::string fs_src = compose_fs();
    std::string err;
    program_ = compile_program(kVS, fs_src.c_str(), &err);
    if (!program_) {
        log::warn("starfield_renderer shader: %s", err.c_str());
        return false;
    }
    loc_z_kin_ = glGetUniformLocation(program_, "u_z_kin");

    std::vector<float> verts;
    verts.reserve(static_cast<size_t>(count) * 3);
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> u_xy(-1.0f, 1.0f);
    std::uniform_real_distribution<float> u_b (0.15f, 0.95f);
    for (int i = 0; i < count; i++) {
        verts.push_back(u_xy(rng));
        verts.push_back(u_xy(rng));
        verts.push_back(u_b(rng));
    }
    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, verts.size() * sizeof(float), verts.data(), GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 3 * sizeof(float), nullptr);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 3 * sizeof(float),
                          reinterpret_cast<const void*>(2 * sizeof(float)));
    glBindVertexArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    count_ = count;

    glEnable(GL_PROGRAM_POINT_SIZE);
    return true;
}

void StarfieldRenderer::teardown() {
    if (program_) { glDeleteProgram(program_); program_ = 0; }
    if (vbo_)     { glDeleteBuffers(1, &vbo_); vbo_ = 0; }
    if (vao_)     { glDeleteVertexArrays(1, &vao_); vao_ = 0; }
    count_ = 0;
    loc_z_kin_ = -1;
}

void StarfieldRenderer::render(float z_kin) {
    if (!program_ || !vao_ || count_ <= 0) return;
    glUseProgram(program_);
    glUniform1f(loc_z_kin_, z_kin);
    glBindVertexArray(vao_);
    glDrawArrays(GL_POINTS, 0, count_);
    glBindVertexArray(0);
    glUseProgram(0);
}

}  // namespace astra::renderer
