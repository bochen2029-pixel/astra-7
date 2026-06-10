// src/scenes/s08_warp_gravity_well.h — S08: Warp + Gravity Well composition.
//
// Spec: DESIGN_SPEC §6 S08; §3.2 composition rule; §7.4 warp exclusion zone.
//
// Composite regime: WARP_CRUISE | GRAVITY_WELL = 0x28. At r = 25 * r_s with
// M_BH = 10 * M_sun: grav_factor = sqrt(1 - 1/25) ~= 0.9798 < 0.99 -> the
// GRAVITY_WELL bit composes into the regime.
//
// V1.9 stage: inline bubble shader (warm-tinted to indicate gravity well
// presence) + BH placeholder rendered as a tiny black disc. Numeric
// assertions cover the full composition: grav_factor, dtau/dt with warp + grav,
// and composite-regime bit assembly.

#pragma once

#include <cstdint>
#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S08_WarpGravityWell : public IScene {
public:
    const char* name() const override { return "S08_WarpGravityWell"; }
    const char* description() const override {
        return "Warp 0.8W + 10 M_sun BH at r=25*r_s; composite WARP_CRUISE | GRAVITY_WELL";
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
    // Scene parameters.
    static constexpr double W_                  = 0.8;
    static constexpr double M_bh_solar_         = 10.0;       // M_sun units
    static constexpr double r_over_rs_          = 25.0;       // distance from BH in r_s units

    // Bubble visual color (warm-tinted to suggest gravity influence).
    static constexpr float kBubbleR = 0.65f;
    static constexpr float kBubbleG = 0.45f;
    static constexpr float kBubbleB = 0.75f;

    // BH placeholder NDC position + RGB (pure black; rendered as a "hole").
    static constexpr float kBhNdcX  = 0.60f;
    static constexpr float kBhNdcY  = -0.40f;
    static constexpr float kBhSize  = 0.045f;

    renderer::StarfieldRenderer        starfield_;
    renderer::PlaceholderRenderer      placeholders_renderer_;
    std::vector<renderer::Placeholder> placeholders_;  // BH placeholder

    // Bubble GL state.
    uint32_t bubble_program_ = 0;
    uint32_t bubble_vao_     = 0;
    uint32_t bubble_vbo_     = 0;
    int loc_W_       = -1;
    int loc_aspect_  = -1;
    int loc_color_   = -1;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
