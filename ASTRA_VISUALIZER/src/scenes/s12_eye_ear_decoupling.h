// src/scenes/s12_eye_ear_decoupling.h — S12: Eye-ear decoupling at warp egress.
//
// Spec: DESIGN_SPEC §6 S12; §6.3 + §8.3 endogenous/exogenous principle.
//
// Phase machine over the warp-shutdown event:
//   t < 10s            -> WARP_CRUISE at v_app=2c; visual_t = -sim_time (rate=-1);
//                         eye-ear gap grows at 2 s/s.
//   10 <= t < 13s      -> SHUTDOWN; gap linearly shrinks from kWarpGapAtShutdown (=20s)
//                         toward 0; visual_t = audio_t - gap (visual catches up).
//   t >= 13s           -> REST; visual_t = audio_t; gap = 0.
//
// Canonical timestamp: t=10.5s — mid-decoupling. At this moment:
//   - phase = SHUTDOWN
//   - audio_t = 10.5 (current)
//   - gap = 20 * (1 - 0.5/3) ~= 16.667
//   - visual_t = 10.5 - 16.667 ~= -6.167 (reverse-warp legacy still active)
//   - Planet rendered at orbit_phase(visual_t = -6.167) — reversed orbit position.
//
// V1.12 stage: numeric assertions on the phase machine + eye-ear gap. Pixel
// assertions on planet RGB at the visual_t-derived NDC position. The audio
// frequency display is a DESIGN_SPEC element that lives in the ImGui overlay
// for interactive mode (V1.13 polish); headless coverage is the numeric
// gap math.

#pragma once

#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S12_EyeEarDecoupling : public IScene {
public:
    const char* name() const override { return "S12_EyeEarDecoupling"; }
    const char* description() const override {
        return "Warp egress eye-ear decoupling; visual lags audio post-shutdown";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    // Canonical: 10.5s = mid-decoupling (0.5s into the 3s shutdown).
    float canonical_timestamp_seconds() const override { return 10.5f; }
    float headless_warmup_seconds()  const override     { return 10.5f; }

    enum class Phase { WARP, SHUTDOWN, REST };

private:
    // Phase boundaries.
    static constexpr double kShutdownStart       = 10.0;
    static constexpr double kShutdownDuration    = 3.0;
    static constexpr double kShutdownEnd         = kShutdownStart + kShutdownDuration;

    // Steady-state eye-ear gap at the moment of shutdown initiation.
    // At v_app=2c rate=-1 for 10s, visual_t = -10. audio_t = 10. gap = 20.
    static constexpr double kWarpGapAtShutdown   = 20.0;

    // Orbit period for the rendered planet.
    static constexpr double kOrbitPeriodSeconds  = 60.0;
    static constexpr float  kOrbitRadiusNdc      = 0.40f;

    // Planet rendering color (canonical ocean-blue; matches S01/S05).
    static constexpr float kPlanetR = 0.30f;
    static constexpr float kPlanetG = 0.55f;
    static constexpr float kPlanetB = 0.90f;

    // Sim state.
    double sim_time_seconds_ = 0.0;
    Phase  phase_            = Phase::WARP;
    double audio_t_          = 0.0;
    double visual_t_         = 0.0;
    double eye_ear_gap_      = 0.0;
    double current_phase_    = 0.0;
    float  planet_ndc_x_     = kOrbitRadiusNdc;
    float  planet_ndc_y_     = 0.0f;

    renderer::PlaceholderRenderer       placeholders_renderer_;
    renderer::StarfieldRenderer         starfield_;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
