#include "app/application.h"
#include "app/camera.h"
#include "app/scene_router.h"
#include "physics/reflex_stub.h"
#include "renderer/chaos_field.h"
#include "renderer/cherenkov_cone.h"
#include "renderer/gl_context.h"
#include "renderer/hull.h"
#include "renderer/named_bodies.h"
#include "renderer/starfield.h"
#include "renderer/wake_trail.h"
#include "renderer/warp_volume.h"
#include "scenes/s09_chaos_reflex.h"            // dynamic_cast survives in tick_chaos_loop for field access
#include "scenes/scene_base.h"
#include "validation/golden_diff.h"
#include "validation/json_report.h"
#include "validation/pixel_sampler.h"
#include "validation/screenshot.h"
#include "ui/assertion_panel.h"
#include "ui/parameter_panel.h"
#include "ui/physics_calc_panel.h"
#include "ui/scenario_selector.h"
#include "ui/state_display.h"
#include "util/log.h"
#include "util/timer.h"

#include <glad/gl.h>
#include <GLFW/glfw3.h>
#include <imgui.h>
#include <backends/imgui_impl_glfw.h>
#include <backends/imgui_impl_opengl3.h>

#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>

#include <cstdio>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>

namespace astra_viz {

namespace {

// Snap the camera to a scene's canonical pose. Used in headless mode and any
// time the operator wants pixel assertions to fire from a known viewpoint.
void apply_canonical_pose(Camera& camera, IScene& scene) {
    IScene::CameraPose pose = scene.canonical_camera();
    camera.set_pose(glm::vec3(pose.pos[0], pose.pos[1], pose.pos[2]),
                    glm::vec3(pose.target[0], pose.target[1], pose.target[2]));
}

// Pull the active scene's volume parameters via IScene::warp_volume_request().
// Defaults are sensible for any non-warp caller.
void resolve_warp_params(IScene* scene, WarpFieldParams& out) {
    out.bubble_center[0] = 0.0f;
    out.bubble_center[1] = 0.0f;
    out.bubble_center[2] = 0.0f;
    out.bubble_radius_m  = 80.0f;
    out.W_amplitude      = 0.0f;
    out.world_half_extent = 0.0f;  // WarpVolume::update overrides this
    if (!scene) return;
    IScene::WarpVolumeRequest req = scene->warp_volume_request();
    if (req.active) {
        out.W_amplitude     = req.W_amplitude;
        out.bubble_radius_m = req.bubble_radius_m;
    }
}

// Drives the S09 chaos PDE + Reflex feedback loop. Called once per frame; the
// virtual gate short-circuits when the active scene isn't chaos-bearing. Inside
// we still need a typed pointer to S09's many tunable fields, so the
// dynamic_cast survives one site.
void tick_chaos_loop(IScene* scene, ChaosField& chaos, ReflexStub& reflex,
                     bool chaos_seeded_already, bool& chaos_seeded_out) {
    chaos_seeded_out = chaos_seeded_already;
    if (!scene || !scene->wants_chaos_tick()) return;
    auto* s9 = dynamic_cast<S09ChaosReflex*>(scene);
    if (!s9) return;

    if (!chaos_seeded_out) {
        chaos.seed(0.6f, 8.0f);
        chaos_seeded_out = true;
    }
    if (s9->manual_inject > 0.0f) {
        chaos.seed(s9->manual_inject, 8.0f);
    }

    float chi_centre = chaos.read_centre_amplitude();
    if (chi_centre < 0.0f) chi_centre = s9->last_chaos_amplitude;

    reflex.enabled = s9->reflex_enabled;
    float beta_recommend = reflex.update(chi_centre, s9->dt_s);

    ChaosPDEParams p{};
    p.alpha_eff = s9->alpha_base;
    p.beta      = beta_recommend;
    p.D         = s9->D;
    p.dt        = s9->dt_s;
    chaos.step(p);

    bool fire = s9->emergency_armed && reflex.emergency_trigger();
    if (fire) {
        chaos.clear();
        chaos_seeded_out = false;
    }

    s9->last_chaos_amplitude = chi_centre;
    s9->last_reflex_beta     = beta_recommend;
    s9->last_emergency_fired = fire;
}

// Per-scene render of the "global" passes - hull, starfield, named bodies,
// warp volume, chaos field, Cherenkov cone, wake trail.
void render_world(const SceneRenderParams& params,
                  Hull& hull, Starfield& starfield, NamedBodies& named_bodies,
                  WarpVolume& volume, bool volume_ready,
                  ChaosField& chaos, bool chaos_ready,
                  CherenkovCone& cone, bool cone_ready,
                  WakeTrail& wake, bool wake_ready,
                  IScene* scene, const Camera& camera,
                  int fb_w, int fb_h, float t_sim_s,
                  const float* view, const float* proj,
                  int viewport_x = 0, int viewport_y = 0) {
    glViewport(viewport_x, viewport_y, fb_w, fb_h);
    // For split-screen halves we let the outer caller clear once before both halves.
    if (viewport_x == 0 && viewport_y == 0) {
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    }

    starfield.draw(view, proj, params.ship_velocity_xyz, params.beta_along);
    hull.draw(view, proj, t_sim_s);
    if (params.show_named_bodies) {
        named_bodies.draw(view, proj,
                          params.sun_dir_xyz, params.planet_dir_xyz,
                          params.planet_color_tint);
    }
    if (volume_ready && params.show_volume) {
        WarpFieldParams wp{};
        resolve_warp_params(scene, wp);
        volume.update(wp);
        float cam_xyz[3] = { camera.position().x, camera.position().y, camera.position().z };
        volume.draw(view, proj, cam_xyz);
    }
    if (chaos_ready && scene && scene->wants_chaos_tick()) {
        float cam_xyz[3] = { camera.position().x, camera.position().y, camera.position().z };
        chaos.draw(view, proj, cam_xyz);
    }
    if (cone_ready && scene) {
        IScene::CherenkovOverlay c = scene->cherenkov_overlay();
        if (c.active) {
            cone.draw(view, proj, c.half_angle_rad, c.axis_xyz, c.apex_xyz, c.length_m);
        }
    }
    if (wake_ready && wake.point_count() >= 2) {
        wake.draw(view, proj);
    }
}

// Returns 0 if all assertions across the chosen scene(s) pass, else 1.
int run_headless(const AppOptions& opts) {
    GLContext ctx;
    if (!ctx.init(opts.width, opts.height, "ASTRA-7 Visualizer (headless)", /*visible=*/false)) {
        return 1;
    }

    Hull hull;
    Starfield starfield;
    NamedBodies named_bodies;
    WarpVolume volume;
    ChaosField chaos;
    CherenkovCone cone;
    WakeTrail wake;
    if (!hull.init() || !starfield.init() || !named_bodies.init()) {
        ctx.shutdown();
        return 2;
    }
    bool volume_ready = opts.enable_volume && volume.init(128, 150.0f);
    bool chaos_ready  = opts.enable_volume && chaos.init(128, 150.0f);
    bool cone_ready   = cone.init();
    bool wake_ready   = wake.init(256);
    ReflexStub reflex;
    bool chaos_seeded = false;

    SceneRouter router;
    Camera camera;
    PixelSampler sampler;

    std::vector<int> targets;
    if (opts.headless_scene_id == "all") {
        for (int i = 0; i < router.scene_count(); i++) {
            // Only run scenes that actually have assertions defined.
            router.set_current(i);
            IScene* s = router.current_scene();
            if (s && (!s->value_assertions().empty() ||
                       !s->pixel_assertions(opts.width, opts.height).empty())) {
                targets.push_back(i);
            }
        }
    } else {
        for (int i = 0; i < router.scene_count(); i++) {
            if (opts.headless_scene_id == router.id(i)) { targets.push_back(i); break; }
        }
    }
    if (targets.empty()) {
        std::fprintf(stderr, "no matching scenes for --scene=%s\n",
                     opts.headless_scene_id.c_str());
        ctx.shutdown();
        return 64;
    }

    if (opts.regenerate_goldens) {
        std::printf(
            "WARNING: --regenerate-goldens supplied; new golden PNGs will be written.\n"
            "         Commit them only with operator sign-off per CLAUDE.md §11.2.\n");
    }

    int total_pass = 0, total_fail = 0;
    int scenes_pass = 0, scenes_fail = 0;
    HeadlessReport report;

    for (int idx : targets) {
        router.set_current(idx);
        IScene* scene = router.current_scene();
        if (!scene) continue;

        apply_canonical_pose(camera, *scene);

        // Render warm-up frames so the GL state, named-body uniforms, etc.
        // are stable before we sample pixels.
        SceneRenderParams params{};
        for (int f = 0; f < opts.headless_frames; f++) {
            params = SceneRenderParams{};
            params.dt_wall_s = 1.0 / 60.0;
            scene->prepare_frame(params);

            ctx.refresh_framebuffer_size();
            int fw = ctx.framebuffer_width(), fh = ctx.framebuffer_height();
            glm::mat4 view = camera.view();
            glm::mat4 proj = camera.proj(fw, fh, 60.0f, 0.5f, 200000.0f);
            const float* vp = glm::value_ptr(view);
            const float* pp = glm::value_ptr(proj);
            tick_chaos_loop(scene, chaos, reflex, chaos_seeded, chaos_seeded);
            // Split-screen scenes (S11) fill two SceneRenderParams via the virtual.
            SceneRenderParams left{}, right{};
            if (scene->fill_split_screen(left, right)) {
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
                render_world(left,  hull, starfield, named_bodies,
                              volume, volume_ready, chaos, chaos_ready,
                              cone, cone_ready, wake, wake_ready,
                              scene, camera, fw / 2, fh, (float)f, vp, pp,
                              /*viewport_x=*/0, /*viewport_y=*/0);
                render_world(right, hull, starfield, named_bodies,
                              volume, volume_ready, chaos, chaos_ready,
                              cone, cone_ready, wake, wake_ready,
                              scene, camera, fw / 2, fh, (float)f, vp, pp,
                              /*viewport_x=*/fw / 2, /*viewport_y=*/0);
            } else {
                render_world(params, hull, starfield, named_bodies,
                              volume, volume_ready, chaos, chaos_ready,
                              cone, cone_ready, wake, wake_ready,
                              scene, camera, fw, fh, (float)f, vp, pp);
            }
            // No per-frame glFinish: read_framebuffer_rgba8 already syncs before
            // the final sample. Intermediate stalls just throttle the warmup
            // (~30x flush per scene) for no observable benefit.
        }

        // Now evaluate assertions on the just-rendered final frame.
        std::vector<AssertionResult> results;
        for (const auto& va : scene->value_assertions()) {
            results.push_back(sampler.evaluate(va));
        }
        for (const auto& pa : scene->pixel_assertions(ctx.framebuffer_width(),
                                                      ctx.framebuffer_height())) {
            results.push_back(sampler.evaluate(pa));
        }

        // V9: capture the just-rendered frame as RGBA8 pixels. Used for
        // golden regeneration, golden diff, and the JSON report screenshot.
        std::vector<uint8_t> frame_rgba;
        int fb_w = ctx.framebuffer_width(), fb_h = ctx.framebuffer_height();
        read_framebuffer_rgba8(0, 0, fb_w, fb_h, frame_rgba);

        const std::string golden_dir   = astra_viz::exe_directory() + "../assets/reference_renders/";
        const std::string golden_path  = golden_dir + scene->id() + ".png";
        GoldenDiffResult  golden{};
        if (opts.regenerate_goldens) {
            // Make sure the directory exists. We rely on the user/CI to mkdir
            // first because Windows doesn't have a portable POSIX mkdir in C++17
            // without filesystem; falling back to "save fails noisily if dir missing".
            bool ok = save_png_rgba8(golden_path, fb_w, fb_h, frame_rgba.data());
            golden.golden_present = ok;
            golden.passed         = ok;
            golden.note           = ok ? "golden regenerated" : "golden write failed";
        } else {
            golden = compare_to_golden(golden_path, fb_w, fb_h, frame_rgba);
            if (golden.golden_present) {
                results.push_back(to_assertion(std::string(scene->id()) + ".golden_diff", golden));
            }
        }

        // Optional: dump the screenshot to the output_dir for the operator's eyes.
        std::string screenshot_path;
        if (!opts.output_dir.empty()) {
            screenshot_path = opts.output_dir + "/" + scene->id() + ".png";
            save_png_rgba8(screenshot_path, fb_w, fb_h, frame_rgba.data());
        }

        int sp = 0, sf = 0;
        std::printf("\n=== %s (%s) ===\n", scene->id(), scene->label());
        for (const auto& r : results) {
            std::printf("  [%s] %-48s  got=%-14.6g exp=%-14.6g diff=%.3g\n",
                        r.passed ? "PASS" : "FAIL",
                        r.name.c_str(), r.measured, r.expected, r.diff);
            if (r.passed) sp++; else sf++;
        }
        if (golden.golden_present) {
            std::printf("  golden: %s  (%s)\n",
                        golden.passed ? "PASS" : "FAIL", golden.note.c_str());
        } else if (!opts.regenerate_goldens) {
            std::printf("  golden: SKIPPED  (%s)\n", golden.note.c_str());
        } else {
            std::printf("  golden: %s\n", golden.note.c_str());
        }
        std::printf("  %d PASS / %d FAIL\n", sp, sf);
        if (sf == 0) scenes_pass++; else scenes_fail++;
        total_pass += sp; total_fail += sf;

        SceneReportRow row;
        row.scene_id    = scene->id();
        row.scene_label = scene->label();
        row.results     = results;
        row.golden      = golden;
        row.screenshot_path = screenshot_path;
        report.scenes.push_back(std::move(row));
    }

    std::printf(
        "\n=== HEADLESS SUMMARY ===\n"
        "  scenes:     %d PASS / %d FAIL\n"
        "  assertions: %d PASS / %d FAIL\n",
        scenes_pass, scenes_fail, total_pass, total_fail);

    report.scenes_passed     = scenes_pass;
    report.scenes_failed     = scenes_fail;
    report.total_assertions  = total_pass + total_fail;
    report.assertions_passed = total_pass;
    if (!opts.output_dir.empty()) {
        std::string json_path = opts.output_dir + "/report.json";
        if (write_json_report(json_path, report)) {
            std::printf("\n  report: %s\n", json_path.c_str());
        }
    }

    if (wake_ready)   wake.shutdown();
    if (cone_ready)   cone.shutdown();
    if (chaos_ready)  chaos.shutdown();
    if (volume_ready) volume.shutdown();
    named_bodies.shutdown();
    starfield.shutdown();
    hull.shutdown();
    ctx.shutdown();
    return (total_fail == 0) ? 0 : 1;
}

// Track which scene index to navigate to from a number key (1..9 + Shift+1..3).
int hotkey_scene_index(GLFWwindow* win) {
    bool shift = (glfwGetKey(win, GLFW_KEY_LEFT_SHIFT)  == GLFW_PRESS) ||
                 (glfwGetKey(win, GLFW_KEY_RIGHT_SHIFT) == GLFW_PRESS);
    for (int k = 0; k < 9; k++) {
        if (glfwGetKey(win, GLFW_KEY_1 + k) == GLFW_PRESS) {
            if (!shift) return k;            // 1..9 -> S01..S09
            if (k < 3)  return 9 + k;        // Shift+1..3 -> S10..S12
        }
    }
    return -1;
}

void collect_camera_input(GLFWwindow* win, CameraInput& in, double dt_s) {
    in.fwd   = glfwGetKey(win, GLFW_KEY_W) == GLFW_PRESS;
    in.back  = glfwGetKey(win, GLFW_KEY_S) == GLFW_PRESS;
    in.left  = glfwGetKey(win, GLFW_KEY_A) == GLFW_PRESS;
    in.right = glfwGetKey(win, GLFW_KEY_D) == GLFW_PRESS;
    in.up    = glfwGetKey(win, GLFW_KEY_E) == GLFW_PRESS ||
               glfwGetKey(win, GLFW_KEY_SPACE) == GLFW_PRESS;
    in.down  = glfwGetKey(win, GLFW_KEY_Q) == GLFW_PRESS ||
               glfwGetKey(win, GLFW_KEY_LEFT_CONTROL) == GLFW_PRESS;
    in.boost = glfwGetKey(win, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS;
    in.look  = glfwGetMouseButton(win, GLFW_MOUSE_BUTTON_RIGHT) == GLFW_PRESS;
    in.dt_s  = dt_s;
}

} // anon

int Application::run(const AppOptions& opts) {
    if (!opts.headless_scene_id.empty()) {
        return run_headless(opts);
    }

    GLContext ctx;
    if (!ctx.init(opts.width, opts.height, "ASTRA-7 Visualizer V4")) return 1;
    if (opts.bench_frames > 0) glfwSwapInterval(0);  // unbounded for FPS measurement

    Hull hull;
    Starfield starfield;
    NamedBodies named_bodies;
    WarpVolume warp_volume;
    ChaosField chaos;
    CherenkovCone cone;
    WakeTrail wake;
    if (!hull.init()) { ctx.shutdown(); return 2; }
    if (!starfield.init()) { hull.shutdown(); ctx.shutdown(); return 3; }
    if (!named_bodies.init()) { starfield.shutdown(); hull.shutdown(); ctx.shutdown(); return 4; }
    bool volume_ready = false;
    if (opts.enable_volume) {
        volume_ready = warp_volume.init(128, 150.0f);
        if (!volume_ready) astra_viz::log::warn("WarpVolume init failed; continuing without volume");
    }
    bool chaos_ready = false;
    if (opts.enable_volume) {
        chaos_ready = chaos.init(128, 150.0f);
        if (!chaos_ready) astra_viz::log::warn("ChaosField init failed; continuing without chaos");
    }
    bool cone_ready = cone.init();
    if (!cone_ready) astra_viz::log::warn("CherenkovCone init failed; continuing without cone");
    bool wake_ready = wake.init(256);
    if (!wake_ready) astra_viz::log::warn("WakeTrail init failed; continuing without wake");
    ReflexStub reflex;
    bool chaos_seeded = false;

    Camera camera;
    camera.set_position({0.0f, 80.0f, 600.0f});
    camera.look_at({0, 0, 0});

    SceneRouter router;
    if (!opts.start_scene_id.empty()) {
        for (int i = 0; i < router.scene_count(); i++) {
            if (opts.start_scene_id == router.id(i)) { router.set_current(i); break; }
        }
    }

    // ImGui setup
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;          // don't write imgui.ini next to the exe
    ImGui::StyleColorsDark();
    ImGui_ImplGlfw_InitForOpenGL(ctx.window(), true);
    ImGui_ImplOpenGL3_Init("#version 460");

    FrameTimer timer;
    PixelSampler sampler;
    std::vector<AssertionResult> last_assertion_results;

    ui::PhysicsCalcPanel calc_panel;

    double prev_mouse_x = 0, prev_mouse_y = 0;
    glfwGetCursorPos(ctx.window(), &prev_mouse_x, &prev_mouse_y);

    double t_sim_s = 0.0;
    bool paused = false;

    astra_viz::log::info("V1 main loop entering; %d scenes registered, starting %s",
                         router.scene_count(),
                         router.current_scene() ? router.current_scene()->id() : "(none)");

    // Bench-mode bookkeeping
    int      frame_idx = 0;
    double   bench_t0  = 0.0;
    double   bench_dt_sum = 0.0;
    double   bench_dt_min = 1e30;
    double   bench_dt_max = 0.0;

    while (!glfwWindowShouldClose(ctx.window())) {
        double dt = timer.tick();
        glfwPollEvents();

        // Hotkey scene switch (1..9, Shift+1..3). Ignore while ImGui owns the kb.
        if (!io.WantCaptureKeyboard) {
            int hi = hotkey_scene_index(ctx.window());
            if (hi >= 0 && hi < router.scene_count() && hi != router.current_index()) {
                router.set_current(hi);
            }
            if (glfwGetKey(ctx.window(), GLFW_KEY_ESCAPE) == GLFW_PRESS) {
                glfwSetWindowShouldClose(ctx.window(), GLFW_TRUE);
            }
            static bool space_was_pressed = false;
            bool space_now = glfwGetKey(ctx.window(), GLFW_KEY_P) == GLFW_PRESS;
            if (space_now && !space_was_pressed) paused = !paused;
            space_was_pressed = space_now;

            // F12: screenshot the current framebuffer to YYYY-MM-DD_HHMMSS.png next to the exe.
            static bool f12_was_pressed = false;
            bool f12_now = glfwGetKey(ctx.window(), GLFW_KEY_F12) == GLFW_PRESS;
            if (f12_now && !f12_was_pressed) {
                std::vector<uint8_t> px;
                int fw_s = ctx.framebuffer_width(), fh_s = ctx.framebuffer_height();
                read_framebuffer_rgba8(0, 0, fw_s, fh_s, px);
                char fname[128];
                std::time_t now = std::time(nullptr);
                std::tm tm;
                localtime_s(&tm, &now);
                std::snprintf(fname, sizeof(fname),
                              "%04d-%02d-%02d_%02d%02d%02d.png",
                              tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
                              tm.tm_hour, tm.tm_min, tm.tm_sec);
                std::string out_path = astra_viz::exe_directory() + fname;
                if (save_png_rgba8(out_path, fw_s, fh_s, px.data())) {
                    astra_viz::log::info("screenshot saved: %s", out_path.c_str());
                }
            }
            f12_was_pressed = f12_now;
        }

        // Mouse delta
        double mx, my;
        glfwGetCursorPos(ctx.window(), &mx, &my);
        double dmx = mx - prev_mouse_x;
        double dmy = my - prev_mouse_y;
        prev_mouse_x = mx; prev_mouse_y = my;

        // Camera
        CameraInput cin{};
        if (!io.WantCaptureMouse) {
            cin.dx = dmx; cin.dy = dmy;
            collect_camera_input(ctx.window(), cin, dt);
        } else {
            cin.dt_s = dt;
        }
        camera.update(cin);

        if (!paused) t_sim_s += dt;

        // Per-scene: prepare frame params, drive shared passes accordingly.
        SceneRenderParams params{};
        params.dt_wall_s = dt;
        if (auto* s = router.current_scene()) {
            s->prepare_frame(params);
        }

        ctx.refresh_framebuffer_size();
        int fw = ctx.framebuffer_width(), fh = ctx.framebuffer_height();
        glm::mat4 view = camera.view();
        glm::mat4 proj = camera.proj(fw, fh, 60.0f, 0.5f, 200000.0f);
        const float* vp = glm::value_ptr(view);
        const float* pp = glm::value_ptr(proj);

        tick_chaos_loop(router.current_scene(), chaos, reflex, chaos_seeded, chaos_seeded);

        // Push a wake sample if the active scene is a warp scene with motion.
        // S05/S07/S12 advance ship_z; we sample camera pos as a proxy.
        if (wake_ready) {
            float cam_xyz[3] = { camera.position().x, camera.position().y, camera.position().z };
            wake.push_sample(cam_xyz);
        }

        // Split-screen scenes (S11) fill two SceneRenderParams via the virtual.
        SceneRenderParams left{}, right{};
        IScene* active = router.current_scene();
        if (active && active->fill_split_screen(left, right)) {
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
            render_world(left,  hull, starfield, named_bodies,
                          warp_volume, volume_ready, chaos, chaos_ready,
                          cone, cone_ready, wake, wake_ready,
                          active, camera,
                          fw / 2, fh, (float)t_sim_s, vp, pp,
                          /*viewport_x=*/0, /*viewport_y=*/0);
            render_world(right, hull, starfield, named_bodies,
                          warp_volume, volume_ready, chaos, chaos_ready,
                          cone, cone_ready, wake, wake_ready,
                          active, camera,
                          fw / 2, fh, (float)t_sim_s, vp, pp,
                          /*viewport_x=*/fw / 2, /*viewport_y=*/0);
        } else {
            render_world(params, hull, starfield, named_bodies,
                          warp_volume, volume_ready, chaos, chaos_ready,
                          cone, cone_ready, wake, wake_ready,
                          active, camera,
                          fw, fh, (float)t_sim_s, vp, pp);
        }

        if (auto* s = router.current_scene()) {
            SceneRenderInput sin{};
            sin.t_sim_s = t_sim_s;
            sin.fb_w = fw; sin.fb_h = fh;
            sin.view = vp; sin.proj = pp;
            s->render(sin);
        }

        // Evaluate value assertions (camera-independent) for the UI panel.
        last_assertion_results.clear();
        if (auto* s = router.current_scene()) {
            for (const auto& va : s->value_assertions()) {
                last_assertion_results.push_back(sampler.evaluate(va));
            }
        }

        // ImGui
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();
        ui::draw_scenario_selector(router);
        ui::draw_parameter_panel(router);
        ui::draw_state_display(router, timer, camera);
        ui::draw_assertion_panel(router, last_assertion_results);
        calc_panel.draw();
        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(ctx.window());

        if (opts.bench_frames > 0) {
            if (frame_idx == 0) bench_t0 = glfwGetTime();
            if (frame_idx >= 5) {                       // skip first 5 frames as warmup
                bench_dt_sum += dt;
                if (dt < bench_dt_min) bench_dt_min = dt;
                if (dt > bench_dt_max) bench_dt_max = dt;
            }
            if (++frame_idx >= opts.bench_frames) {
                double elapsed = glfwGetTime() - bench_t0;
                int measured = opts.bench_frames - 5;
                double avg_dt_ms = (measured > 0) ? bench_dt_sum / measured * 1000.0 : 0.0;
                std::printf(
                    "bench: %d frames, %.3f s wall, "
                    "avg %.2f ms / %.0f FPS, min %.2f ms, max %.2f ms\n",
                    opts.bench_frames, elapsed,
                    avg_dt_ms, avg_dt_ms > 0 ? 1000.0 / avg_dt_ms : 0.0,
                    bench_dt_min * 1000.0, bench_dt_max * 1000.0);
                break;
            }
        }
    }

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();

    if (wake_ready)   wake.shutdown();
    if (cone_ready)   cone.shutdown();
    if (chaos_ready)  chaos.shutdown();
    if (volume_ready) warp_volume.shutdown();
    named_bodies.shutdown();
    starfield.shutdown();
    hull.shutdown();
    ctx.shutdown();
    return 0;
}

} // namespace astra_viz
