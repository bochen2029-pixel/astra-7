// src/scenes/s06_warp_cruise_10c_cherenkov.h — S06: Warp Cruise 10c +
// Cherenkov cone (CLOSES AUDIT 5D-F4 GAP AT VISUALIZER LEVEL).
//
// Spec: DESIGN_SPEC §6 S06; §6 step 10 Cherenkov formula; AUDIT 5D-F4.
//
// libastra_nexus already closed 5D-F4 at the math layer via
// `astra::compute_cherenkov_angle(W, beta, n_coef)`. S06 closes it at the
// rendering layer by:
//   1) Calling that function from the scene
//   2) Visualizing the cone in the fragment shader
//   3) Asserting libastra's angle matches the rendered cone's drawn
//      angle within tolerance (V1.8: numeric assertions only; V1.9 will
//      add pixel-cone-edge assertion once we wire 2D->NDC angle inversion).
//
// At v_app=10c, W=1, n_coef=1:
//   n(W) = 1 + 1*1 = 2
//   n*beta = 2 * 10 = 20
//   cos(theta_c) = 1/20 = 0.05
//   theta_c = acos(0.05) ~= 1.5208 rad ~= 87.13 degrees
//
// (Very wide cone — at v_app >> c/n, the cone surface is nearly perpendicular
// to the velocity direction. Spec-loose visual stylization in V1.8; cone is
// rendered as a forward-facing wedge.)

#pragma once

#include <cstdint>
#include <vector>

#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S06_WarpCruise10cCherenkov : public IScene {
public:
    const char* name() const override { return "S06_WarpCruise10cCherenkov"; }
    const char* description() const override {
        return "Warp Cruise 10c + Cherenkov cone (closes 5D-F4 at visualizer layer)";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 0.0f; }
    float headless_warmup_seconds()  const override     { return 0.0f; }

private:
    // Scene parameters (locked V1.8).
    static constexpr double v_app_over_c_ = 10.0;
    static constexpr double W_            = 1.0;
    static constexpr double n_coef_       = 1.0;

    // Cached libastra output, populated in setup().
    double cherenkov_angle_rad_ = 0.0;

    // GL state.
    renderer::StarfieldRenderer starfield_;
    uint32_t program_ = 0;
    uint32_t vao_     = 0;
    uint32_t vbo_     = 0;
    int loc_W_       = -1;
    int loc_cone_    = -1;
    int loc_aspect_  = -1;
    int loc_color_   = -1;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
