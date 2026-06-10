// camera.h - free-fly perspective camera. Origin in metres; viewing the hull
// from ~600 m default. Mouse-look enabled while right-mouse held; WASD/QE for
// position. We DO NOT use GLM in the public header so it stays a thin contract.
#pragma once

#include <glm/glm.hpp>

struct GLFWwindow;

namespace astra_viz {

struct CameraInput {
    bool fwd, back, left, right, up, down;
    bool boost;            // shift = 10x speed
    bool look;             // right-mouse held
    double dx, dy;         // mouse delta this frame (in px)
    double dt_s;
};

class Camera {
public:
    Camera();

    void update(const CameraInput& in);

    // View matrix + perspective. fov_deg is vertical.
    glm::mat4 view() const;
    glm::mat4 proj(int fb_w, int fb_h, float fov_deg, float znear, float zfar) const;

    glm::vec3 position() const { return pos_; }
    glm::vec3 forward()  const { return fwd_; }
    glm::vec3 up_axis()  const { return up_; }

    void set_position(glm::vec3 p) { pos_ = p; }
    void look_at(glm::vec3 target);

    // Sets the camera to a known canonical pose: position + look-at target.
    // Used by headless mode and scene activate() so pixel assertions can fire
    // at a deterministic camera state.
    void set_pose(glm::vec3 position, glm::vec3 target);

    // Tunables. base_speed_mps = 30 means "30 m/s while flying around a 280m hull"
    // which lets the operator orbit it in ~10s. boost_factor=10 gives 300 m/s.
    float base_speed_mps = 30.0f;
    float boost_factor   = 10.0f;
    float mouse_sens_radpx = 0.0025f;

private:
    glm::vec3 pos_;
    float yaw_rad_;    // around world-up; 0 = +z
    float pitch_rad_;  // 0 = horizon; clamped to +-89 deg

    // derived each update():
    glm::vec3 fwd_;
    glm::vec3 right_;
    glm::vec3 up_;
};

} // namespace astra_viz
