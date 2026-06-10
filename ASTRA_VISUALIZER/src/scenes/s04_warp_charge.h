// src/scenes/s04_warp_charge.h — S04: Warp Charge scene.
//
// Spec: DESIGN_SPEC §6 S04.
// Initial state: regime=REST, W=0. Script: at t=0..5s, W ramps linearly 0→1
// (WARP_CHARGE phase); at t=5s, regime → WARP_CRUISE with v_app=2c.
//
// V1.6 stage: bubble visualization is a centered soft disc whose radius +
// intensity scale with W. Assertions cover the W ramp + libastra-driven
// composition rule at W=1 + bubble-color pixel at center after warmup.
// V1.7+ stage will use CFD-RBF eval + 3D camera + smooth-min blend with hull SDF.

#pragma once

#include <cstdint>

#include "scenes/i_scene.h"

namespace astra::scenes {

class S04_WarpCharge : public IScene {
public:
    const char* name() const override { return "S04_WarpCharge"; }
    const char* description() const override {
        return "Warp Charge: W ramps 0->1 over 5s; regime WARP_CHARGE -> WARP_CRUISE";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    // Canonical golden timestamp: t=5s, right after W reaches 1 + regime transition.
    float canonical_timestamp_seconds() const override { return 5.0f; }
    // Headless tick warmup: 5s so the W ramp is complete + regime has flipped.
    float headless_warmup_seconds() const override     { return 5.0f; }

private:
    // Computed canonical bubble center color (W=1; spec-loose violet/blue).
    static constexpr float kBubbleCoreR = 0.55f;
    static constexpr float kBubbleCoreG = 0.40f;
    static constexpr float kBubbleCoreB = 0.90f;

    // V1.10: sim_time is double to survive float-accumulation drift under
    // headless 60Hz chunked ticking (300 chunks * float drift could land on
    // either side of 5s threshold; double accumulation is stable).
    double sim_time_seconds_ = 0.0;
    float  current_W_        = 0.0f;
    bool   cruise_engaged_   = false;  // true once W ramp reaches 1.0

    // GL state
    uint32_t program_ = 0;
    uint32_t vao_     = 0;
    uint32_t vbo_     = 0;
    int loc_W_       = -1;
    int loc_color_   = -1;
    int loc_aspect_  = -1;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
