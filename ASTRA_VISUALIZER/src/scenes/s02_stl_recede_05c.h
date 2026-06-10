// src/scenes/s02_stl_recede_05c.h — S02: STL_REL recede at beta=0.5.
//
// Spec: DESIGN_SPEC §6 S02; §3.4 SR longitudinal Doppler; §3.7 rapidity.
//
// V1.7 stage: rear view — planet behind ship is redshifted; starfield
// uniformly redshifted (all stars are behind in rear view). Pixel
// assertions check redshifted planet RGB; numeric assertions check
// gamma and z_kin against libastra.

#pragma once

#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S02_StlRecede05c : public IScene {
public:
    const char* name() const override { return "S02_StlRecede05c"; }
    const char* description() const override {
        return "STL_REL recede at beta=0.5; z_kin ~= 0.732 (sqrt(3)-1)";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 0.0f; }
    float headless_warmup_seconds()  const override { return 0.0f; }

protected:
    // Subclasses override to inject a different beta (used by S03).
    virtual double beta() const { return 0.5; }

private:
    renderer::PlaceholderRenderer       placeholders_renderer_;
    renderer::StarfieldRenderer         starfield_;
    std::vector<renderer::Placeholder>  placeholders_;

    float z_kin_ = 0.0f;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
