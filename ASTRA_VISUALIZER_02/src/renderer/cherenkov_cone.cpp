#include "renderer/cherenkov_cone.h"
#include "util/log.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdint>
#include <vector>

namespace astra_viz {

namespace {

// Build a unit cone (apex at origin, axis along +z, height = 1, base radius
// scaled by tan(theta) at draw time via a vertex shader uniform).
// Vertex layout: 1 apex + (n_radial + 1) base ring vertices.
// Triangles: (apex, ring_i, ring_i+1) for each segment.
struct V {
    float x, y, z;
};

void build_cone_mesh(int n_radial, std::vector<V>& verts, std::vector<uint32_t>& idx) {
    verts.clear();
    idx.clear();
    verts.reserve((size_t)n_radial + 2);
    // Apex at origin.
    verts.push_back({0.0f, 0.0f, 0.0f});
    // Base ring at z = 1, x = cos(theta), y = sin(theta). Vertex shader scales
    // the (x, y) by tan(half_angle) so the cone opens at the configured angle.
    for (int i = 0; i <= n_radial; i++) {
        float a = (float)i / (float)n_radial * 6.28318530718f;
        verts.push_back({std::cos(a), std::sin(a), 1.0f});
    }
    for (int i = 0; i < n_radial; i++) {
        idx.push_back(0);
        idx.push_back((uint32_t)(i + 1));
        idx.push_back((uint32_t)(i + 2));
    }
}

} // anon

bool CherenkovCone::init(int radial_segments) {
    std::vector<V> verts;
    std::vector<uint32_t> idx;
    build_cone_mesh(radial_segments, verts, idx);
    n_indices_ = (int)idx.size();

    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glGenBuffers(1, &ebo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)(verts.size() * sizeof(V)),
                 verts.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, (GLsizeiptr)(idx.size() * sizeof(uint32_t)),
                 idx.data(), GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(V), (void*)0);
    glBindVertexArray(0);

    const std::string& root = astra_viz::exe_directory();
    if (!prog_.load_from_files(root + "shaders/cherenkov/cone.vert",
                                root + "shaders/cherenkov/cone.frag")) {
        astra_viz::log::error("cherenkov_cone program load failed");
        return false;
    }
    return true;
}

void CherenkovCone::shutdown() {
    if (ebo_) glDeleteBuffers(1, &ebo_);
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
    ebo_ = vbo_ = vao_ = 0;
}

void CherenkovCone::draw(const float* view, const float* proj,
                         float half_angle_rad,
                         const float axis_dir_xyz[3],
                         const float apex_world_xyz[3],
                         float length_m) const {
    if (half_angle_rad < 0.0f || half_angle_rad >= 1.5707963f) return;  // inactive or absurd

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glDisable(GL_CULL_FACE);
    glDepthMask(GL_FALSE);

    prog_.use();
    prog_.set_mat4("u_view", view);
    prog_.set_mat4("u_proj", proj);
    prog_.set_vec3("u_axis",
                   axis_dir_xyz[0], axis_dir_xyz[1], axis_dir_xyz[2]);
    prog_.set_vec3("u_apex",
                   apex_world_xyz[0], apex_world_xyz[1], apex_world_xyz[2]);
    prog_.set_float("u_length", length_m);
    prog_.set_float("u_half_angle", half_angle_rad);

    glBindVertexArray(vao_);
    glDrawElements(GL_TRIANGLES, n_indices_, GL_UNSIGNED_INT, nullptr);
    glBindVertexArray(0);

    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);
}

} // namespace astra_viz
