// src/app/gl_init.h — GLFW + GLAD setup helpers shared by interactive
// (Application) and headless (HeadlessRunner). Keeps the GL init path single-sourced.

#pragma once

struct GLFWwindow;

namespace astra::app {

struct GlInitOptions {
    int  width        = 1280;
    int  height       = 720;
    bool visible      = true;
    bool resizable    = true;
    bool vsync        = true;
    const char* title = "ASTRA-7 Visual Physics Testbed";
};

struct GlInitResult {
    GLFWwindow* window = nullptr;  // nullptr on failure
    bool gl_ok      = false;
    bool cuda_ok    = false;
    bool interop_ok = false;
};

// Initialize GLFW + create a window + load GLAD + run CUDA sanity + run
// CUDA-GL interop sanity. Returns the window handle (caller-owned) and the
// status of each sanity check. On failure to create the window, returns
// {nullptr, false, ...}.
//
// On success the GL context is current on the calling thread.
GlInitResult init_gl_window(const GlInitOptions& opts);

// Shut down a context produced by init_gl_window. Calls glfwTerminate.
void shutdown_gl_window(GLFWwindow* window);

}  // namespace astra::app
