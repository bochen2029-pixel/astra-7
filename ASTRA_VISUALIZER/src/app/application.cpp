// src/app/application.cpp — interactive Application class implementation.
//
// GLAD must be included before GLFW (so GLFW's gl.h shim is skipped).
// ImGui backends include their own GL header guards.

#include <glad/gl.h>
#include <GLFW/glfw3.h>

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>

#include "app/application.h"
#include "app/cli.h"
#include "app/gl_init.h"
#include "scenes/i_scene.h"
#include "util/log.h"

#include <chrono>
#include <cstdio>
#include <cstdlib>

namespace astra::app {

namespace {

double now_seconds() {
    using clock = std::chrono::high_resolution_clock;
    return std::chrono::duration<double>(clock::now().time_since_epoch()).count();
}

}  // namespace

Application::Application() = default;
Application::~Application() = default;

bool Application::init(const CliArgs& args) {
    width_  = args.width  > 0 ? args.width  : 1280;
    height_ = args.height > 0 ? args.height : 720;
    requested_scene_ = args.scene;

    GlInitOptions opts;
    opts.width   = width_;
    opts.height  = height_;
    opts.visible = true;
    auto gl = init_gl_window(opts);
    if (!gl.window) return false;
    window_ = gl.window;
    // CUDA + interop status logged by init_gl_window. We continue regardless;
    // V2 volume rendering will refuse to run if interop_ok is false.

    // ImGui setup
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;
    io.LogFilename = nullptr;
    ImGui::StyleColorsDark();
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding   = 4.0f;
    style.WindowBorderSize = 1.0f;
    style.Colors[ImGuiCol_WindowBg] = ImVec4(0.04f, 0.05f, 0.10f, 0.88f);

    if (!ImGui_ImplGlfw_InitForOpenGL(window_, true)) {
        log::error("ImGui_ImplGlfw_InitForOpenGL failed");
        shutdown();
        return false;
    }
    if (!ImGui_ImplOpenGL3_Init("#version 460 core")) {
        log::error("ImGui_ImplOpenGL3_Init failed");
        ImGui_ImplGlfw_Shutdown();
        shutdown();
        return false;
    }

    // Load requested scene (default S01 if none given).
    std::string scene_id = requested_scene_.empty() ? "S01" : requested_scene_;
    current_scene_ = scene_router_.create(scene_id);
    if (!current_scene_) {
        log::warn("scene '%s' not found; falling back to S01_RestBaseline",
                  scene_id.c_str());
        current_scene_ = scene_router_.create("S01");
    }
    if (current_scene_) {
        current_scene_->setup();
        log::info("scene loaded: %s", current_scene_->name());
    }

    last_frame_ts_ = now_seconds();
    return true;
}

int Application::run() {
    if (!window_) return 1;
    while (!glfwWindowShouldClose(window_)) {
        glfwPollEvents();

        int fb_w = 0, fb_h = 0;
        glfwGetFramebufferSize(window_, &fb_w, &fb_h);
        if (fb_w > 0 && fb_h > 0) { width_ = fb_w; height_ = fb_h; }

        if (current_scene_) current_scene_->tick(static_cast<float>(last_frame_ms_ / 1000.0));
        render_frame();
        render_ui();

        glfwSwapBuffers(window_);

        double now = now_seconds();
        double dt  = now - last_frame_ts_;
        last_frame_ts_ = now;
        last_frame_ms_ = dt * 1000.0;
        if (dt > 1e-6) {
            double inst_fps = 1.0 / dt;
            smoothed_fps_   = 0.95 * smoothed_fps_ + 0.05 * inst_fps;
        }
        frame_index_++;

        if (glfwGetKey(window_, GLFW_KEY_ESCAPE) == GLFW_PRESS) break;
    }
    return 0;
}

void Application::shutdown() {
    if (current_scene_) {
        current_scene_->teardown();
        current_scene_.reset();
    }
    if (ImGui::GetCurrentContext()) {
        ImGui_ImplOpenGL3_Shutdown();
        ImGui_ImplGlfw_Shutdown();
        ImGui::DestroyContext();
    }
    if (window_) {
        shutdown_gl_window(window_);
        window_ = nullptr;
    }
}

void Application::render_frame() {
    glViewport(0, 0, width_, height_);
    if (current_scene_) {
        current_scene_->render(width_, height_);
    } else {
        // Deep-space dark; not pure black so we can distinguish "rendered" from "nothing".
        glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    }
}

void Application::render_ui() {
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    ImGui::SetNextWindowPos(ImVec2(12, 12), ImGuiCond_Always);
    ImGui::Begin("ASTRA-7 Visual Physics Testbed", nullptr,
                 ImGuiWindowFlags_NoMove
                 | ImGuiWindowFlags_AlwaysAutoResize
                 | ImGuiWindowFlags_NoFocusOnAppearing
                 | ImGuiWindowFlags_NoCollapse);
    ImGui::Text("Hello, ASTRA-7 Visualizer");
    ImGui::Separator();
    ImGui::Text("fps   %6.1f   (%5.2f ms)", smoothed_fps_, last_frame_ms_);
    ImGui::Text("frame %llu", static_cast<unsigned long long>(frame_index_));
    ImGui::Text("vp    %d x %d", width_, height_);
    ImGui::Separator();
    if (current_scene_) {
        ImGui::Text("scene: %s", current_scene_->name());
        ImGui::Text("%s", current_scene_->description());
    } else {
        ImGui::Text("scene: (none)");
    }
    ImGui::Separator();
    ImGui::Text("Esc: quit");
    ImGui::End();

    // Per-scene UI panel (right side).
    if (current_scene_) {
        current_scene_->render_ui();
    }

    render_assertion_overlay();

    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}

void Application::render_assertion_overlay() {
    if (!current_scene_) return;
    auto num_asserts = current_scene_->numeric_assertions();
    if (num_asserts.empty()) return;

    ImGui::SetNextWindowPos(ImVec2(static_cast<float>(width_) - 360.0f, 12.0f),
                            ImGuiCond_Always);
    ImGui::Begin("Validation (libastra)", nullptr,
                 ImGuiWindowFlags_NoMove
                 | ImGuiWindowFlags_AlwaysAutoResize
                 | ImGuiWindowFlags_NoFocusOnAppearing
                 | ImGuiWindowFlags_NoCollapse);
    int passed = 0;
    for (const auto& na : num_asserts) {
        auto r = validation::evaluate(na);
        if (r.passed) passed++;
        ImVec4 color = r.passed ? ImVec4(0.3f, 0.95f, 0.3f, 1.0f)
                                : ImVec4(0.95f, 0.35f, 0.30f, 1.0f);
        ImGui::TextColored(color, "%s %s", r.passed ? "[PASS]" : "[FAIL]", r.name.c_str());
        ImGui::Text("  measured: %.6g", r.measured_value);
        ImGui::Text("  libastra: %.6g", r.expected_value);
        ImGui::Text("  diff: %.3g (tol %.3g)", r.diff_abs, r.tolerance);
        if (!r.spec_section.empty()) {
            ImGui::TextDisabled("  %s", r.spec_section.c_str());
        }
        ImGui::Separator();
    }
    ImGui::Text("%d / %d PASS", passed, static_cast<int>(num_asserts.size()));
    ImGui::End();
}

}  // namespace astra::app
