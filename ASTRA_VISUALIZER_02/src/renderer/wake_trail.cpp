#include "renderer/wake_trail.h"
#include "util/log.h"

#include <glad/gl.h>

#include <vector>

namespace astra_viz {

bool WakeTrail::init(int max_points) {
    max_points_ = max_points;
    points_.reserve((size_t)max_points * 3);

    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    // Allocate up-front; will reupload data each frame if dirty.
    glBufferData(GL_ARRAY_BUFFER, (GLsizeiptr)(max_points * 3 * sizeof(float)),
                 nullptr, GL_DYNAMIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
    glBindVertexArray(0);

    const std::string& root = astra_viz::exe_directory();
    if (!prog_.load_from_files(root + "shaders/wake/wake.vert",
                                root + "shaders/wake/wake.frag")) {
        astra_viz::log::error("wake_trail program load failed");
        return false;
    }
    return true;
}

void WakeTrail::push_sample(const float xyz[3]) {
    if ((int)(points_.size() / 3) >= max_points_) {
        // Drop oldest entry (shift left by 1 sample). Acceptable cost at 256 pts.
        points_.erase(points_.begin(), points_.begin() + 3);
    }
    points_.push_back(xyz[0]);
    points_.push_back(xyz[1]);
    points_.push_back(xyz[2]);
    dirty_ = true;
}

void WakeTrail::clear() {
    points_.clear();
    dirty_ = true;
}

void WakeTrail::draw(const float* view, const float* proj) const {
    int n = (int)(points_.size() / 3);
    if (n < 2) return;

    if (dirty_) {
        glBindBuffer(GL_ARRAY_BUFFER, vbo_);
        glBufferSubData(GL_ARRAY_BUFFER, 0, (GLsizeiptr)(n * 3 * sizeof(float)), points_.data());
        dirty_ = false;
    }

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE);    // additive
    glDepthMask(GL_FALSE);

    prog_.use();
    prog_.set_mat4("u_view", view);
    prog_.set_mat4("u_proj", proj);
    prog_.set_int("u_total", n);

    glBindVertexArray(vao_);
    glDrawArrays(GL_LINE_STRIP, 0, n);
    glBindVertexArray(0);

    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);
}

void WakeTrail::shutdown() {
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
    vao_ = vbo_ = 0;
}

} // namespace astra_viz
