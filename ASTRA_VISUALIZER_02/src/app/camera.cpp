#include "app/camera.h"

#include <glm/gtc/matrix_transform.hpp>

#include <algorithm>
#include <cmath>

namespace astra_viz {

static constexpr float WORLD_UP_X = 0.0f;
static constexpr float WORLD_UP_Y = 1.0f;
static constexpr float WORLD_UP_Z = 0.0f;
static constexpr float PITCH_LIMIT = 1.5533f;  // ~89 degrees in radians

Camera::Camera()
    : pos_(0.0f, 80.0f, 600.0f),
      yaw_rad_(3.14159265f),       // facing -z toward the origin where the hull sits
      pitch_rad_(-0.10f),
      fwd_(0, 0, -1),
      right_(1, 0, 0),
      up_(0, 1, 0) {}

void Camera::update(const CameraInput& in) {
    if (in.look) {
        yaw_rad_   -= (float)in.dx * mouse_sens_radpx;
        pitch_rad_ -= (float)in.dy * mouse_sens_radpx;
        pitch_rad_ = std::clamp(pitch_rad_, -PITCH_LIMIT, PITCH_LIMIT);
    }

    float cy = std::cos(yaw_rad_), sy = std::sin(yaw_rad_);
    float cp = std::cos(pitch_rad_), sp = std::sin(pitch_rad_);
    fwd_   = glm::vec3(cp * sy, sp, cp * cy);
    fwd_   = glm::normalize(fwd_);
    right_ = glm::normalize(glm::cross(fwd_, glm::vec3(WORLD_UP_X, WORLD_UP_Y, WORLD_UP_Z)));
    up_    = glm::normalize(glm::cross(right_, fwd_));

    float v = base_speed_mps * (in.boost ? boost_factor : 1.0f) * (float)in.dt_s;
    if (in.fwd)   pos_ += fwd_   * v;
    if (in.back)  pos_ -= fwd_   * v;
    if (in.right) pos_ += right_ * v;
    if (in.left)  pos_ -= right_ * v;
    if (in.up)    pos_ += glm::vec3(WORLD_UP_X, WORLD_UP_Y, WORLD_UP_Z) * v;
    if (in.down)  pos_ -= glm::vec3(WORLD_UP_X, WORLD_UP_Y, WORLD_UP_Z) * v;
}

glm::mat4 Camera::view() const {
    return glm::lookAt(pos_, pos_ + fwd_, up_);
}

glm::mat4 Camera::proj(int fb_w, int fb_h, float fov_deg, float znear, float zfar) const {
    float aspect = fb_h > 0 ? (float)fb_w / (float)fb_h : 1.0f;
    return glm::perspective(glm::radians(fov_deg), aspect, znear, zfar);
}

void Camera::look_at(glm::vec3 target) {
    glm::vec3 to = glm::normalize(target - pos_);
    pitch_rad_ = std::asin(std::clamp(to.y, -1.0f, 1.0f));
    yaw_rad_   = std::atan2(to.x, to.z);
}

void Camera::set_pose(glm::vec3 position, glm::vec3 target) {
    pos_ = position;
    look_at(target);
    // Apply the orientation immediately so fwd_/right_/up_ are consistent
    // before the first update() call.
    CameraInput zero{};
    update(zero);
}

} // namespace astra_viz
