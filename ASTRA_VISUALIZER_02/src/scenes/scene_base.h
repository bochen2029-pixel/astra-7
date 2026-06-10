// scene_base.h - IScene interface + lightweight registration. Scenes own their
// per-scene state, expose tunables for the parameter panel, and provide their
// own assertion list.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "astra_nexus/regime.h"
#include "validation/assertion.h"

namespace astra_viz {

struct SceneRenderInput {
    double t_sim_s;          // sim-time advance, scene-local
    int    fb_w, fb_h;
    const float* view;       // glm::mat4 col-major
    const float* proj;
};

// Per-scene render parameters that the global Application loop consumes so it
// knows how to drive shared passes (starfield Doppler/aberration, named bodies).
// Filled in by each scene before render().
struct SceneRenderParams {
    // Wallclock seconds since the previous prepare_frame() call. Scenes that
    // advance their own sim clock read this instead of touching ImGui's IO
    // (headless mode has no ImGui context).
    double dt_wall_s = 1.0 / 60.0;
    // Ship motion direction in world space (unit vector). The starfield uses
    // this for SR aberration warp and for Doppler tinting per star.
    float ship_velocity_xyz[3] = {0.0f, 0.0f, -1.0f};
    // Magnitude of ship velocity in units of c. STL formula clamps at 0.9999.
    float beta_along            = 0.0f;
    // Regime bits to dispatch apparent_rate inside the starfield shader.
    uint32_t regime             = 0;
    // Render the V3 test volume? STL scenes turn it off; warp scenes turn it on.
    bool show_volume            = false;
    // Sun + planet billboards visible?
    bool show_named_bodies      = true;
    // World-space direction to the sun and the planet. Unit; will be re-normalised
    // by the body vertex shader. Defaults chosen so both sit clear of the hull
    // silhouette from the V1 canonical camera (0, 80, 600) looking at origin.
    float sun_dir_xyz[3]    = { 0.5f,  0.3f, -0.85f};
    float planet_dir_xyz[3] = {-0.4f,  0.2f, -0.90f};
    // Pure tint applied to the planet billboard (Doppler colour). Sun tint is
    // fixed warm yellow inside named_bodies.cpp.
    float planet_color_tint[3]  = {1.0f, 1.0f, 1.0f};
    // ASCII status for the state panel ("REST", "STL_REL 0.5c recede", ...).
    char regime_label[64]       = "REST";
};

class IScene {
public:
    virtual ~IScene() = default;

    // Short identifier (S01, S05, ...).
    virtual const char* id() const = 0;
    // Human-readable label for the dropdown.
    virtual const char* label() const = 0;
    // The base regime this scene runs at (informs state-display panel).
    virtual uint32_t base_regime() const = 0;

    // Called when the user selects the scene.
    virtual void activate() {}
    // Called when the user navigates away.
    virtual void deactivate() {}

    // Compute/refresh per-scene render parameters BEFORE the global passes run.
    // Default implementation fills regime + leaves everything else at defaults.
    virtual void prepare_frame(SceneRenderParams& params) {
        params.regime = base_regime();
    }

    // Per-scene render hook AFTER global hull + starfield + named bodies pass,
    // BEFORE ImGui. Most scenes have nothing to add here.
    virtual void render(const SceneRenderInput&) {}

    // ImGui calls for the per-scene parameter panel.
    virtual void draw_parameter_panel() {}

    // ImGui calls for the per-scene state display.
    virtual void draw_state_panel() {}

    // V4+: assertion lists evaluated after each frame.
    virtual std::vector<ScalarValueAssertion> value_assertions() const { return {}; }
    virtual std::vector<ScalarPixelAssertion> pixel_assertions(int fb_w, int fb_h) const {
        (void)fb_w; (void)fb_h;
        return {};
    }

    // Canonical camera pose for headless evaluation: position + look-at target.
    // Default puts the camera at (0, 80, 600) looking at the origin (matches V1
    // default). Scenes that need a different pose for their pixel assertions
    // override this.
    struct CameraPose { float pos[3]; float target[3]; };
    virtual CameraPose canonical_camera() const {
        return CameraPose{{0.0f, 80.0f, 600.0f}, {0.0f, 0.0f, 0.0f}};
    }

    // ---- Capability hooks (post-polish): replace dynamic_cast dispatch ----
    //
    // Each shared rendering pass that depends on per-scene state asks the
    // active scene through one of these virtuals instead of casting to a
    // concrete type. Default impls return "not interested" so most scenes
    // override nothing. New scenes plug in without editing application.cpp.

    struct WarpVolumeRequest {
        bool  active           = false;     // true -> Application maps + launches warp_field kernel
        float W_amplitude      = 0.0f;
        float bubble_radius_m  = 80.0f;
    };
    virtual WarpVolumeRequest warp_volume_request() const { return {}; }

    struct CherenkovOverlay {
        bool  active            = false;
        float half_angle_rad    = -1.0f;
        float axis_xyz[3]       = {0.0f, 0.0f, 1.0f};
        float apex_xyz[3]       = {0.0f, 0.0f, 0.0f};
        float length_m          = 200.0f;
    };
    virtual CherenkovOverlay cherenkov_overlay() const { return {}; }

    // True when the chaos PDE + Reflex feedback loop should tick this frame
    // (and the chaos field's heat-colormap volume should render).
    virtual bool wants_chaos_tick() const { return false; }

    // Split-screen scenes (S11) fill `left` + `right` with per-half params
    // and return true. Default returns false; Application takes the single-
    // SceneRenderParams render path.
    virtual bool fill_split_screen(SceneRenderParams& /*left*/,
                                    SceneRenderParams& /*right*/) const {
        return false;
    }
};

} // namespace astra_viz
