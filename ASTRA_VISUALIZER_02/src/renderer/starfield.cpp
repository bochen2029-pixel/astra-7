#include "renderer/starfield.h"
#include "util/log.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <vector>

namespace astra_viz {

namespace {

// Linear-congruential PRNG, seeded; reproducible across runs.
struct Rng {
    uint32_t state;
    uint32_t next() { state = state * 1664525u + 1013904223u; return state; }
    float    f01()  { return (next() >> 8) * (1.0f / 16777216.0f); }
    float    fpm1() { return f01() * 2.0f - 1.0f; }
};

// Crude blackbody -> RGB at temperature T (Kelvin). Approximation good enough for
// pinpoint star sprites; we keep it short and avoid CIE colour code in V1.
void blackbody_rgb(float T, float& r, float& g, float& b) {
    float t = std::max(1000.0f, std::min(40000.0f, T)) / 100.0f;
    if (t <= 66.0f) {
        r = 1.0f;
        g = 0.39008157f * std::log(t) - 0.63184144f;
        b = (t <= 19.0f) ? 0.0f : 0.54320678f * std::log(t - 10.0f) - 1.19625408f;
    } else {
        r = 1.29293618f * std::pow(t - 60.0f, -0.1332047592f);
        g = 1.12989086f * std::pow(t - 60.0f, -0.0755148492f);
        b = 1.0f;
    }
    if (r < 0) r = 0; if (r > 1) r = 1;
    if (g < 0) g = 0; if (g > 1) g = 1;
    if (b < 0) b = 0; if (b > 1) b = 1;
}

struct Star {
    float px, py, pz;
    float r, g, b;
    float size;
};

} // anon

bool Starfield::init(int n_stars, uint32_t seed) {
    n_stars_ = n_stars;

    Rng rng{seed};
    std::vector<Star> stars(n_stars_);
    constexpr float SHELL_R = 50000.0f;     // 50 km virtual sphere radius (camera-local backdrop)
    for (int i = 0; i < n_stars_; i++) {
        // Uniform direction on unit sphere via rejection or trig; use trig for speed.
        float u  = rng.f01();
        float v  = rng.f01();
        float th = 6.28318530718f * u;
        float ph = std::acos(2.0f * v - 1.0f);
        float sx = std::sin(ph) * std::cos(th);
        float sy = std::sin(ph) * std::sin(th);
        float sz = std::cos(ph);
        stars[i].px = sx * SHELL_R;
        stars[i].py = sy * SHELL_R;
        stars[i].pz = sz * SHELL_R;

        // Distribute T with a bias toward cooler stars (more M-class than O-class).
        float T = 2500.0f + rng.f01() * rng.f01() * 30000.0f;
        blackbody_rgb(T, stars[i].r, stars[i].g, stars[i].b);

        // Magnitude as a uniform-in-area sample so the sprite "size" approximates
        // an inverse-square brightness without doing real photometry.
        stars[i].size = 0.6f + rng.f01() * 1.8f;
    }

    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);

    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)(stars.size() * sizeof(Star)),
                 stars.data(), GL_STATIC_DRAW);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Star), (void*)0);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Star),
                          (void*)(sizeof(float) * 3));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, sizeof(Star),
                          (void*)(sizeof(float) * 6));

    glBindVertexArray(0);

    const std::string& root = astra_viz::exe_directory();
    if (!prog_.load_from_files(root + "shaders/starfield/starfield.vert",
                                root + "shaders/starfield/starfield.frag")) {
        astra_viz::log::error("starfield program load failed");
        return false;
    }

    astra_viz::log::info("Starfield: %d stars", n_stars_);
    return true;
}

void Starfield::shutdown() {
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
    vbo_ = vao_ = 0;
}

void Starfield::draw(const float* view, const float* proj,
                     const float ship_vel_dir_xyz[3], float beta) const {
    glDepthMask(GL_FALSE);
    prog_.use();
    prog_.set_mat4("u_view", view);
    prog_.set_mat4("u_proj", proj);
    prog_.set_vec3("u_ship_vel_dir",
                   ship_vel_dir_xyz[0], ship_vel_dir_xyz[1], ship_vel_dir_xyz[2]);
    prog_.set_float("u_beta", beta);
    glBindVertexArray(vao_);
    glDrawArrays(GL_POINTS, 0, (GLsizei)n_stars_);
    glBindVertexArray(0);
    glDepthMask(GL_TRUE);
}

} // namespace astra_viz
