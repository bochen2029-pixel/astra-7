// src/app/gl_init.cpp

#include <glad/gl.h>
#include <GLFW/glfw3.h>

#include "app/gl_init.h"
#include "util/log.h"
#include "kernels.h"

namespace astra::app {

namespace {

bool glfw_initialized = false;

void glfw_error_cb(int code, const char* msg) {
    log::error("GLFW error %d: %s", code, msg);
}

}  // namespace

GlInitResult init_gl_window(const GlInitOptions& opts) {
    GlInitResult r;

    if (!glfw_initialized) {
        glfwSetErrorCallback(glfw_error_cb);
        if (!glfwInit()) {
            log::error("glfwInit failed");
            return r;
        }
        glfw_initialized = true;
    }

    glfwWindowHint(GLFW_CLIENT_API, GLFW_OPENGL_API);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
    glfwWindowHint(GLFW_VISIBLE,   opts.visible   ? GLFW_TRUE : GLFW_FALSE);
    glfwWindowHint(GLFW_RESIZABLE, opts.resizable ? GLFW_TRUE : GLFW_FALSE);

    // For headless we still need a valid window; sized small to dodge OS
    // capping. Caller renders to the requested logical size via offscreen FBO
    // or directly at the small window size (V1.3 path).
    int win_w = opts.visible ? opts.width  : 16;
    int win_h = opts.visible ? opts.height : 16;

    r.window = glfwCreateWindow(win_w, win_h, opts.title, nullptr, nullptr);
    if (!r.window) {
        log::error("glfwCreateWindow failed (%dx%d, visible=%d)",
                   win_w, win_h, opts.visible ? 1 : 0);
        return r;
    }

    glfwMakeContextCurrent(r.window);
    glfwSwapInterval(opts.vsync ? 1 : 0);

    if (!gladLoadGL(reinterpret_cast<GLADloadfunc>(glfwGetProcAddress))) {
        log::error("gladLoadGL failed");
        glfwDestroyWindow(r.window);
        r.window = nullptr;
        return r;
    }
    r.gl_ok = true;

    const GLubyte* gl_ver  = glGetString(GL_VERSION);
    const GLubyte* gl_rndr = glGetString(GL_RENDERER);
    log::info("GL version: %s", gl_ver  ? reinterpret_cast<const char*>(gl_ver)  : "?");
    log::info("GL device : %s", gl_rndr ? reinterpret_cast<const char*>(gl_rndr) : "?");

    // CUDA sanity.
    r.cuda_ok = kernels::run_sanity_check();
    log::info("CUDA sanity: %s", r.cuda_ok ? "PASS" : "FAIL");

    // CUDA-GL interop sanity (requires a current GL context).
    r.interop_ok = kernels::run_cuda_gl_interop_check();
    log::info("CUDA-GL interop sanity: %s", r.interop_ok ? "PASS" : "FAIL");

    return r;
}

void shutdown_gl_window(GLFWwindow* window) {
    if (window) glfwDestroyWindow(window);
    glfwTerminate();
    glfw_initialized = false;
}

}  // namespace astra::app
