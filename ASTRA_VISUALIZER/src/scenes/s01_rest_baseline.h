// src/scenes/s01_rest_baseline.h — S01: REST baseline scene.
//
// Spec: DESIGN_SPEC §6 S01.
// V1.7: refactored to use shared PlaceholderRenderer + StarfieldRenderer
// from src/renderer/. z_kin = 0 (no Doppler shift; baseline).

#pragma once

#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S01_RestBaseline : public IScene {
public:
    const char* name() const override { return "S01_RestBaseline"; }
    const char* description() const override {
        return "REST baseline; hull + Sun + planet placeholders; gamma=1, dtau/dt=1";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 0.0f; }
    float headless_warmup_seconds()  const override { return 0.0f; }

private:
    float sim_time_seconds_ = 0.0f;

    renderer::PlaceholderRenderer   placeholders_renderer_;
    renderer::StarfieldRenderer     starfield_;
    std::vector<renderer::Placeholder> placeholders_;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
