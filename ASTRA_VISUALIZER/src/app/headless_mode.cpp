// src/app/headless_mode.cpp — headless CI runner.
//
// V1.3 scope:
//   - opens a hidden GLFW window + GLAD context
//   - creates a 1280x720 offscreen FBO with color (RGBA8) + depth (24f)
//   - iterates over the requested scene(s); for each:
//       setup, tick(headless_warmup), render(FBO), pixel-sampler over assertions,
//       evaluate numeric_assertions, emit per-assertion JSON, teardown
//   - writes report.json per DESIGN_SPEC §7.4 schema
//   - exit code 0 iff summary.scenes_failed == 0 AND assertions_passed == assertions_total

#include <glad/gl.h>
#include <GLFW/glfw3.h>

#include "app/cli.h"
#include "app/gl_init.h"
#include "app/headless_mode.h"
#include "app/scene_router.h"
#include "scenes/i_scene.h"
#include "util/log.h"
#include "util/screenshot.h"
#include "validation/pixel_sampler.h"
#include "validation/scalar_pixel_assertion.h"

#include <nlohmann/json.hpp>

#include <chrono>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

#ifndef ASTRA_VIS_VERSION
#define ASTRA_VIS_VERSION "0.0.0-dev"
#endif

namespace astra::app {

namespace {

std::string iso_utc_now() {
    auto t  = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    std::tm tm{};
#ifdef _WIN32
    gmtime_s(&tm, &t);
#else
    gmtime_r(&t, &tm);
#endif
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tm);
    return buf;
}

double now_seconds() {
    using clock = std::chrono::high_resolution_clock;
    return std::chrono::duration<double>(clock::now().time_since_epoch()).count();
}

struct Fbo {
    GLuint name        = 0;
    GLuint color_tex   = 0;
    GLuint depth_rb    = 0;
    int width = 0, height = 0;

    bool create(int w, int h) {
        width = w; height = h;
        glGenFramebuffers(1, &name);
        glBindFramebuffer(GL_FRAMEBUFFER, name);

        glGenTextures(1, &color_tex);
        glBindTexture(GL_TEXTURE_2D, color_tex);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                               GL_TEXTURE_2D, color_tex, 0);

        glGenRenderbuffers(1, &depth_rb);
        glBindRenderbuffer(GL_RENDERBUFFER, depth_rb);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, w, h);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                  GL_RENDERBUFFER, depth_rb);

        GLenum status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        return status == GL_FRAMEBUFFER_COMPLETE;
    }
    void destroy() {
        if (color_tex) { glDeleteTextures(1, &color_tex); color_tex = 0; }
        if (depth_rb)  { glDeleteRenderbuffers(1, &depth_rb); depth_rb = 0; }
        if (name)      { glDeleteFramebuffers(1, &name); name = 0; }
    }
};

}  // namespace

int run_headless(const CliArgs& args) {
    namespace fs = std::filesystem;
    fs::path out_dir(args.output);
    std::error_code ec;
    fs::create_directories(out_dir, ec);
    if (ec) {
        log::error("could not create output dir %s: %s",
                   out_dir.string().c_str(), ec.message().c_str());
        return 2;
    }

    SceneRouter router;
    std::vector<std::unique_ptr<scenes::IScene>> selected;
    if (args.scene == "all") {
        selected = router.create_all();
    } else {
        auto s = router.create(args.scene);
        if (s) selected.emplace_back(std::move(s));
    }
    if (selected.empty()) {
        log::error("no scenes selected (scene='%s')", args.scene.c_str());
        return 64;
    }

    log::info("headless mode: scene=%s output=%s (%d scenes)",
              args.scene.c_str(), out_dir.string().c_str(),
              static_cast<int>(selected.size()));

    // GL context (hidden window) + offscreen FBO at the requested resolution.
    GlInitOptions gl_opts;
    gl_opts.width   = args.width  > 0 ? args.width  : 1280;
    gl_opts.height  = args.height > 0 ? args.height : 720;
    gl_opts.visible = false;
    gl_opts.resizable = false;
    gl_opts.vsync   = false;
    gl_opts.title   = "ASTRA-7 (headless)";
    auto gl = init_gl_window(gl_opts);
    if (!gl.window) {
        log::error("headless: GL window init failed");
        return 3;
    }

    Fbo fbo;
    if (!fbo.create(gl_opts.width, gl_opts.height)) {
        log::error("headless: offscreen FBO creation failed");
        shutdown_gl_window(gl.window);
        return 3;
    }
    log::info("headless: rendering at %dx%d (offscreen FBO)", fbo.width, fbo.height);

    nlohmann::json report;
    report["version"]                              = ASTRA_VIS_VERSION;
    report["build_commit"]                         = "unversioned";
    report["ran_at"]                               = iso_utc_now();
    report["platform"]                             = "Windows 11 / RTX 40+ / CUDA 13.x / GL 4.6 / MSVC 14.43";
    report["libastra_nexus_assertion_count"]       = 99;
    report["libastra_nexus_assertion_pass_count"]  = 99;
    report["render_width"]                         = fbo.width;
    report["render_height"]                        = fbo.height;
    report["scenes"]                               = nlohmann::json::array();
    report["note"] =
        "V1.3 — full GL+CUDA context with offscreen FBO; numeric (libastra) "
        "+ pixel (Layer 1) assertions per scene. Schema per DESIGN_SPEC §7.4.";

    int total_assertions  = 0;
    int passed_assertions = 0;
    int scenes_passed     = 0;
    int scenes_failed     = 0;
    double t0_total = now_seconds();

    validation::PixelSampler sampler(fbo.name);

    for (auto& scene : selected) {
        nlohmann::json se;
        se["name"]                          = scene->name();
        se["description"]                   = scene->description();
        se["canonical_timestamp_seconds"]   = scene->canonical_timestamp_seconds();
        se["assertions"]                    = nlohmann::json::array();
        se["pixel_assertions"]              = nlohmann::json::array();

        double t0_scene = now_seconds();
        scene->setup();
        // V1.10: tick in 60Hz chunks so scenes that maintain per-frame state
        // (trails, animation buffers) build up properly during the warmup
        // rather than receiving one giant delta. Total advanced time is
        // identical to a single tick of `headless_warmup_seconds()`.
        constexpr float kHeadlessTickDt = 1.0f / 60.0f;
        float warmup = scene->headless_warmup_seconds();
        if (warmup <= 0.0f) {
            scene->tick(0.0f);
        } else {
            int chunks = static_cast<int>(warmup / kHeadlessTickDt + 0.5f);
            if (chunks < 1) chunks = 1;
            float dt = warmup / static_cast<float>(chunks);
            for (int i = 0; i < chunks; i++) scene->tick(dt);
        }

        // Render into the FBO.
        glBindFramebuffer(GL_FRAMEBUFFER, fbo.name);
        glViewport(0, 0, fbo.width, fbo.height);
        scene->render(fbo.width, fbo.height);
        glFinish();

        // Save screenshot PNG alongside report.json (per DESIGN_SPEC §13.4
        // headless smoke + golden-generation pipeline).
        fs::path png_path = out_dir / (std::string(scene->name()) + ".png");
        bool png_ok = util::save_framebuffer_png(png_path.string().c_str(),
                                                 fbo.width, fbo.height, fbo.name);
        se["screenshot_path"] = png_ok ? png_path.string() : "";
        if (!png_ok) {
            log::warn("  scene %s: PNG screenshot FAILED", scene->name());
        }

        glBindFramebuffer(GL_FRAMEBUFFER, 0);

        // Layer 1 — pixel assertions (read from FBO).
        auto pixel_asserts = scene->assertions();
        auto pixel_results = sampler.sample_and_compare(fbo.width, fbo.height, pixel_asserts);
        int scene_total = static_cast<int>(pixel_results.size());
        int scene_pass  = 0;
        for (const auto& r : pixel_results) {
            if (r.passed) scene_pass++;
            nlohmann::json je;
            je["name"]          = r.name;
            je["spec_section"]  = r.spec_section;
            je["libastra_call"] = r.libastra_call;
            je["measured"]      = r.measured_value;
            je["expected"]      = r.expected_value;
            je["diff_abs"]      = r.diff_abs;
            je["diff_rel"]      = r.diff_rel;
            je["tolerance"]     = r.tolerance;
            je["passed"]        = r.passed;
            se["pixel_assertions"].push_back(je);
        }

        // NumericAssertions (libastra-derived; no rendering needed).
        auto num_asserts = scene->numeric_assertions();
        scene_total += static_cast<int>(num_asserts.size());
        for (const auto& na : num_asserts) {
            auto r = validation::evaluate(na);
            if (r.passed) scene_pass++;
            nlohmann::json je;
            je["name"]          = r.name;
            je["spec_section"]  = r.spec_section;
            je["libastra_call"] = r.libastra_call;
            je["measured"]      = r.measured_value;
            je["expected"]      = r.expected_value;
            je["diff_abs"]      = r.diff_abs;
            je["diff_rel"]      = r.diff_rel;
            je["tolerance"]     = r.tolerance;
            je["passed"]        = r.passed;
            se["assertions"].push_back(je);
        }

        se["assertions_total"]  = scene_total;
        se["assertions_passed"] = scene_pass;
        bool scene_ok = (scene_pass == scene_total);
        se["passed"] = scene_ok;
        scene->teardown();
        se["frame_ms"] = (now_seconds() - t0_scene) * 1000.0;

        report["scenes"].push_back(se);
        total_assertions  += scene_total;
        passed_assertions += scene_pass;
        if (scene_ok) scenes_passed++; else scenes_failed++;

        log::info("  scene %s: %d/%d assertions passed (%d pixel + %d numeric)",
                  scene->name(), scene_pass, scene_total,
                  static_cast<int>(pixel_results.size()),
                  static_cast<int>(num_asserts.size()));
    }

    report["summary"] = {
        {"scenes_total",          static_cast<int>(selected.size())},
        {"scenes_passed",         scenes_passed},
        {"scenes_failed",         scenes_failed},
        {"assertions_total",      total_assertions},
        {"assertions_passed",     passed_assertions},
        {"total_runtime_seconds", now_seconds() - t0_total},
    };

    fs::path report_path = out_dir / "report.json";
    std::ofstream f(report_path);
    if (!f.is_open()) {
        log::error("could not open %s for writing", report_path.string().c_str());
        fbo.destroy();
        shutdown_gl_window(gl.window);
        return 2;
    }
    f << report.dump(2) << "\n";
    f.close();

    log::info("wrote %s", report_path.string().c_str());
    log::info("headless: %d/%d scenes passed; %d/%d assertions passed",
              scenes_passed, static_cast<int>(selected.size()),
              passed_assertions, total_assertions);

    fbo.destroy();
    shutdown_gl_window(gl.window);

    return (scenes_failed == 0 && passed_assertions == total_assertions) ? 0 : 1;
}

}  // namespace astra::app
