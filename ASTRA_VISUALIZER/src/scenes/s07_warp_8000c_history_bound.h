// src/scenes/s07_warp_8000c_history_bound.h — S07: photon-source-history
// bound. Spec: DESIGN_SPEC §6 S07; §3.11 audit D1 (beyond_photon_history flag).
//
// At v_app=8000c >> c, t_emit decreases rapidly. With a body whose
// t_source_start is just before t_cosmic=0, the ship quickly "outruns" the
// body's emission history: t_emit < t_source_start, and physically no
// photon exists to be received. The body becomes GONE — not faded — per
// the spec's distinguishing claim vs typical fictional "fading at warp".
//
// V1.9 stage: at canonical t=15s with the chosen parameters,
// `astra::observe()` returns beyond_photon_history=true. Scene renders no
// planet (cleared background). Pixel assertion confirms center pixel is
// background-dark — the planet's absence is empirically the spec's discrete
// disappearance.

#pragma once

#include <vector>

#include "astra_nexus/constants.h"
#include "renderer/placeholder_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S07_Warp8000cHistoryBound : public IScene {
public:
    const char* name() const override { return "S07_Warp8000cHistoryBound"; }
    const char* description() const override {
        return "Warp 8000c photon-history bound: planet is GONE not faded";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 15.0f; }
    float headless_warmup_seconds()  const override     { return 15.0f; }

private:
    static constexpr double v_app_over_c_   = 8000.0;
    static constexpr double body_distance_m_= 3.0e8;     // ~1 light-second behind
    static constexpr double t_source_start_ = -5.0;      // body emitted from -5s onward

    float sim_time_seconds_ = 0.0f;

    // Computed every tick via libastra::observe — gates rendering.
    bool  current_beyond_history_ = false;

    renderer::PlaceholderRenderer       placeholders_renderer_;
    std::vector<renderer::Placeholder>  placeholders_;  // populated only when planet is visible

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
