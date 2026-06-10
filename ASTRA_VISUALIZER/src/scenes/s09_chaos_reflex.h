// src/scenes/s09_chaos_reflex.h — S09: Chaos PDE Fisher-KPP + Reflex stabilizer.
//
// Spec: DESIGN_SPEC §6 S09; §7.1 chaos PDE; §2.3.1 Reflex Contract.
//
// Phase machine:
//   t < 5s            -> Reflex DISABLED; chaos grows from seeded Gaussian
//                        toward the saturated state.
//   t >= 5s           -> Reflex ENABLED; uniform damping at kReflexRate=0.5/s
//                        applied each tick.
//
// V1.13 stage: CPU-side Fisher-KPP RK2 step (128x128 grid); R32F GL texture
// upload each render; viridis colormap in fragment shader. V1.14 will port
// the PDE step to a CUDA kernel + cudaGraphicsGLRegisterImage surface write
// (the §6.4 chaos pipeline).
//
// Canonical timestamp: t=8s (3s into Reflex damping). Chaos partially damped;
// heatmap shows mid-viridis colors at canonical capture.

#pragma once

#include <cstdint>

#include "physics/chaos_field.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S09_ChaosReflex : public IScene {
public:
    const char* name() const override { return "S09_ChaosReflex"; }
    const char* description() const override {
        return "Fisher-KPP chaos PDE (Reflex damping enabled at t=5s)";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 8.0f; }
    float headless_warmup_seconds()  const override     { return 8.0f; }

private:
    // PDE parameters (V1.13 tuned empirically; v0.130 candidate for §7.1 lock).
    static constexpr int    kGridW         = 128;
    static constexpr int    kGridH         = 128;
    static constexpr float  kDiffusion     = 0.25f;
    static constexpr float  kAlphaBase     = 1.0f;
    static constexpr float  kReflexStart   = 5.0f;
    static constexpr float  kReflexRate    = 0.5f;

    double sim_time_seconds_ = 0.0;
    bool   reflex_enabled_   = false;

    physics::ChaosField chaos_;

    // GL state for heatmap rendering.
    uint32_t program_  = 0;
    uint32_t vao_      = 0;
    uint32_t vbo_      = 0;
    uint32_t texture_  = 0;  // R32F upload of chaos_.data()
    int loc_tex_       = -1;
    int loc_aspect_    = -1;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
