// src/renderer/placeholder_renderer.cpp

#include "renderer/placeholder_renderer.h"
#include "renderer/gl_helpers.h"
#include "physics/redshift.h"
#include "util/log.h"

#include <glad/gl.h>

#include <string>

namespace astra::renderer {

namespace {

const char* kVS = R"(#version 460 core
layout(location=0) in vec2 a_pos;
uniform vec2  u_scale;
uniform vec2  u_offset;
uniform float u_aspect;
void main() {
    vec2 p = a_pos * u_scale;
    p.x   *= u_aspect;
    gl_Position = vec4(p + u_offset, 0.0, 1.0);
}
)";

// FS imports the shared GLSL redshift function string (kept in sync with
// the C++ inline definitions in physics/redshift.h).
std::string compose_fs() {
    return std::string("#version 460 core\n")
        + physics::kGlslRedshiftFn
        + R"(
out vec4 frag;
uniform vec3  u_color;
uniform float u_z_kin;
void main() {
    vec3 c = apply_kin_redshift(u_color, u_z_kin);
    frag = vec4(c, 1.0);
}
)";
}

}  // namespace

bool PlaceholderRenderer::setup() {
    std::string fs_src = compose_fs();
    std::string err;
    program_ = compile_program(kVS, fs_src.c_str(), &err);
    if (!program_) {
        log::error("placeholder_renderer shader: %s", err.c_str());
        return false;
    }
    create_unit_quad(&vao_, &vbo_);
    loc_scale_  = glGetUniformLocation(program_, "u_scale");
    loc_offset_ = glGetUniformLocation(program_, "u_offset");
    loc_color_  = glGetUniformLocation(program_, "u_color");
    loc_aspect_ = glGetUniformLocation(program_, "u_aspect");
    loc_z_kin_  = glGetUniformLocation(program_, "u_z_kin");
    return true;
}

void PlaceholderRenderer::teardown() {
    if (program_) { glDeleteProgram(program_); program_ = 0; }
    if (vbo_)     { glDeleteBuffers(1, &vbo_); vbo_ = 0; }
    if (vao_)     { glDeleteVertexArrays(1, &vao_); vao_ = 0; }
    loc_scale_ = loc_offset_ = loc_color_ = loc_aspect_ = loc_z_kin_ = -1;
}

void PlaceholderRenderer::render(int viewport_width,
                                 int viewport_height,
                                 const std::vector<Placeholder>& placeholders,
                                 float z_kin)
{
    if (!program_ || !vao_) return;
    float aspect = (viewport_width > 0)
                     ? static_cast<float>(viewport_height) / static_cast<float>(viewport_width)
                     : 1.0f;
    glUseProgram(program_);
    glUniform1f(loc_aspect_, aspect);
    glUniform1f(loc_z_kin_,  z_kin);
    for (const auto& p : placeholders) {
        glUniform2f(loc_scale_,  p.half_extent, p.half_extent);
        glUniform2f(loc_offset_, p.ndc_x, p.ndc_y);
        glUniform3f(loc_color_,  p.r, p.g, p.b);
        draw_unit_quad(vao_);
    }
    glUseProgram(0);
}

}  // namespace astra::renderer
