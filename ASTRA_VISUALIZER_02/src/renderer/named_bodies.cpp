#include "renderer/named_bodies.h"
#include "util/log.h"

#include <glad/gl.h>

namespace astra_viz {

bool NamedBodies::init() {
    glGenVertexArrays(1, &vao_);
    const std::string& root = astra_viz::exe_directory();
    if (!prog_.load_from_files(root + "shaders/named_bodies/body.vert",
                                root + "shaders/named_bodies/body.frag")) {
        astra_viz::log::error("named_bodies program load failed");
        return false;
    }
    return true;
}

void NamedBodies::shutdown() {
    if (vao_) glDeleteVertexArrays(1, &vao_);
    vao_ = 0;
}

void NamedBodies::draw(const float* view, const float* proj,
                       const float sun_dir_xyz[3],
                       const float planet_dir_xyz[3], const float planet_tint_rgb[3]) const {
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glDepthMask(GL_FALSE);

    prog_.use();
    prog_.set_mat4("u_view", view);
    prog_.set_mat4("u_proj", proj);
    glBindVertexArray(vao_);

    // Sun: warm yellow, fixed colour.
    prog_.set_vec3("u_dir",  sun_dir_xyz[0],  sun_dir_xyz[1],  sun_dir_xyz[2]);
    prog_.set_vec3("u_tint", 1.0f, 0.88f, 0.55f);
    prog_.set_float("u_radius_clip", 0.045f);
    glDrawArrays(GL_TRIANGLES, 0, 6);

    // Planet: base white modulated by the scene's tint (Doppler redshift driver).
    prog_.set_vec3("u_dir",  planet_dir_xyz[0],  planet_dir_xyz[1],  planet_dir_xyz[2]);
    prog_.set_vec3("u_tint", planet_tint_rgb[0], planet_tint_rgb[1], planet_tint_rgb[2]);
    prog_.set_float("u_radius_clip", 0.035f);
    glDrawArrays(GL_TRIANGLES, 0, 6);

    glBindVertexArray(0);
    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);
}

} // namespace astra_viz
