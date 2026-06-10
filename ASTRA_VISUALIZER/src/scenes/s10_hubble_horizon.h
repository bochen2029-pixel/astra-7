// src/scenes/s10_hubble_horizon.h — S10: Hubble horizon body.
//
// Spec: DESIGN_SPEC §6 S10; §3.12 cosmological expansion + Hubble horizon.
//
// Body at d > c/H0 (proper distance beyond Hubble horizon) is causally
// disconnected — `observe()` returns beyond_hubble_horizon=true. Body
// rendered as a frozen + dim red-shifted dot (visual representation of the
// horizon-cross / dimming state).
//
// V1.9 stage: body at d = 1.2 * D_HUBBLE_SI (~16 Gly). z_cosmo ~= 1.2.
// PlaceholderRenderer applies the same kin_redshift function as a visual
// proxy for cosmological redshift (spec-loose; KNOWN_ISSUES finding logs
// the proper blackbody-temp replacement for v0.130).

#pragma once

#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S10_HubbleHorizon : public IScene {
public:
    const char* name() const override { return "S10_HubbleHorizon"; }
    const char* description() const override {
        return "Body at d = 1.2*c/H0; frozen + extremely redshifted (beyond Hubble)";
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
    // d_proper = 1.2 * c/H0 (just past the Hubble horizon).
    static constexpr double d_multiplier_ = 1.2;

    float z_cosmo_ = 0.0f;

    renderer::PlaceholderRenderer       placeholders_renderer_;
    renderer::StarfieldRenderer         starfield_;
    std::vector<renderer::Placeholder>  placeholders_;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
