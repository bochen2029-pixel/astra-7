// s09_chaos_reflex.h - Fisher-KPP chaos field that the operator can watch grow
// (Reflex off), then damp (Reflex on), then re-spike via manual injection slider.
// Demonstrates the v0.129 Reflex Contract (§2.3.1) at the visual level.
//
// The actual PDE step + ReflexStub PID + emergency-dump trigger live in the
// Application loop because they need the ChaosField + ReflexStub instances
// that the scene doesn't own. This scene drives the parameters + state panel.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S09ChaosReflex final : public IScene {
public:
    const char* id() const override    { return "S09"; }
    const char* label() const override { return "S09  Chaos + Reflex"; }
    uint32_t base_regime() const override;

    void activate() override;
    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    CameraPose canonical_camera() const override;

    bool wants_chaos_tick() const override { return true; }

    // Tunables consumed by Application's chaos-loop coordinator.
    float alpha_base    = 1.2f;
    float D             = 0.6f;
    float manual_inject = 0.0f;   // 0..1; >0 re-seeds at this amp each frame
    float dt_s          = 1.0f / 60.0f;
    bool  reflex_enabled = false;
    bool  emergency_armed = true; // true means emergency_dump fires on chaos > threshold

    // Set by Application after the loop runs PID + step.
    float last_chaos_amplitude = 0.0f;
    float last_reflex_beta     = 0.0f;
    bool  last_emergency_fired = false;
};

} // namespace astra_viz
