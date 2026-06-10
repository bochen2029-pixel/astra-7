#include "renderer/hull.h"
#include "util/log.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdint>
#include <vector>

namespace astra_viz {

namespace {

// Hull silhouette function: half-width as a function of normalized arc t in [0, 1]
// where t=0 is the nose and t=1 is the engine bell. Roughly drop-tank with a
// blended forward section. Matches the qualitative profile in hull_design_v0.md.
float profile_radius(float t) {
    // smooth peak around t ~ 0.5, narrower forward, slight flare aft
    float x  = (t - 0.55f) * 2.5f;
    float r  = std::exp(-x * x);
    float aft = (t > 0.85f) ? (1.0f + 0.5f * (t - 0.85f) / 0.15f) : 1.0f;
    return r * aft;
}

struct Vertex {
    float px, py, pz;
    float nx, ny, nz;
};

void build_hull_mesh(std::vector<Vertex>& verts, std::vector<uint32_t>& idx,
                     float length_m = 280.0f,
                     float half_width_m = 39.0f,
                     float half_height_m = 11.0f,
                     int   nlong = 64,
                     int   nradial = 32) {
    verts.clear(); idx.clear();
    verts.reserve((nlong + 1) * (nradial + 1));

    for (int i = 0; i <= nlong; i++) {
        float t = (float)i / (float)nlong;
        float x = (t - 0.5f) * length_m;
        float r = profile_radius(t);
        for (int j = 0; j <= nradial; j++) {
            float a = (float)j / (float)nradial * 6.28318530718f;
            float ca = std::cos(a);
            float sa = std::sin(a);
            // elliptical cross-section: wider than tall (blended-wing-body silhouette)
            float y = r * half_height_m * sa;
            float z = r * half_width_m  * ca;

            // normal: outward radial in y/z, tiny x component for nose/tail taper
            float nx = -profile_radius(t + 0.02f) + profile_radius(t - 0.02f);
            float ny = sa;
            float nz = ca;
            float nlen = std::sqrt(nx*nx + ny*ny + nz*nz);
            if (nlen < 1e-6f) nlen = 1.0f;
            verts.push_back({x, y, z, nx/nlen, ny/nlen, nz/nlen});
        }
    }

    int stride = nradial + 1;
    for (int i = 0; i < nlong; i++) {
        for (int j = 0; j < nradial; j++) {
            uint32_t a = (uint32_t)(i * stride + j);
            uint32_t b = (uint32_t)((i + 1) * stride + j);
            uint32_t c = (uint32_t)((i + 1) * stride + j + 1);
            uint32_t d = (uint32_t)(i * stride + j + 1);
            idx.push_back(a); idx.push_back(b); idx.push_back(c);
            idx.push_back(a); idx.push_back(c); idx.push_back(d);
        }
    }
}

} // anon

bool Hull::init() {
    std::vector<Vertex> verts;
    std::vector<uint32_t> idx;
    build_hull_mesh(verts, idx);
    tri_count_ = (uint32_t)(idx.size() / 3);

    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glGenBuffers(1, &ebo_);

    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)(verts.size() * sizeof(Vertex)),
                 verts.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, (GLsizeiptr)(idx.size() * sizeof(uint32_t)),
                 idx.data(), GL_STATIC_DRAW);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)0);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                          (void*)(sizeof(float) * 3));

    glBindVertexArray(0);

    const std::string& root = astra_viz::exe_directory();
    if (!prog_.load_from_files(root + "shaders/hull/hull.vert",
                                root + "shaders/hull/hull.frag")) {
        astra_viz::log::error("hull program load failed");
        return false;
    }

    astra_viz::log::info("Hull: %zu verts, %u tris", verts.size(), tri_count_);
    return true;
}

void Hull::shutdown() {
    if (ebo_) glDeleteBuffers(1, &ebo_);
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
    ebo_ = vbo_ = vao_ = 0;
}

void Hull::draw(const float* view, const float* proj, float t) const {
    prog_.use();
    prog_.set_mat4("u_view", view);
    prog_.set_mat4("u_proj", proj);
    prog_.set_float("u_time", t);
    glBindVertexArray(vao_);
    glDrawElements(GL_TRIANGLES, (GLsizei)(tri_count_ * 3), GL_UNSIGNED_INT, nullptr);
    glBindVertexArray(0);
}

} // namespace astra_viz
