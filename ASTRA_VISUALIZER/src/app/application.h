// src/app/application.h — interactive Application class.
// Owns GLFW window, GLAD context, ImGui setup, render loop.

#pragma once

#include <cstdint>
#include <memory>
#include <string>

#include "app/scene_router.h"

struct GLFWwindow;

namespace astra::scenes { class IScene; }

namespace astra::app {

struct CliArgs;

class Application {
public:
    Application();
    ~Application();
    Application(const Application&) = delete;
    Application& operator=(const Application&) = delete;

    bool init(const CliArgs& args);
    int  run();
    void shutdown();

private:
    void render_frame();
    void render_ui();
    void render_assertion_overlay();

    GLFWwindow* window_ = nullptr;
    int  width_  = 1280;
    int  height_ = 720;
    uint64_t frame_index_ = 0;
    double   smoothed_fps_ = 60.0;
    double   last_frame_ms_ = 0.0;
    double   last_frame_ts_ = 0.0;

    std::string requested_scene_;
    SceneRouter scene_router_;
    std::unique_ptr<scenes::IScene> current_scene_;
};

}  // namespace astra::app
