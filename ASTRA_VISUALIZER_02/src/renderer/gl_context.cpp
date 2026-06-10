#include "renderer/gl_context.h"
#include "util/log.h"

#include <glad/gl.h>
#include <GLFW/glfw3.h>

namespace astra_viz {

static void glfw_error_callback(int code, const char* desc) {
    astra_viz::log::error("GLFW error %d: %s", code, desc);
}

static void GLAPIENTRY gl_debug_callback(GLenum source, GLenum type, GLuint id,
                                         GLenum severity, GLsizei,
                                         const GLchar* message, const void*) {
    if (severity == GL_DEBUG_SEVERITY_NOTIFICATION) return;
    astra_viz::log::warn("GL[src=0x%x type=0x%x id=%u sev=0x%x]: %s",
                         source, type, id, severity, message);
}

bool GLContext::init(int width, int height, const char* title, bool visible) {
    glfwSetErrorCallback(glfw_error_callback);
    if (!glfwInit()) {
        astra_viz::log::error("glfwInit failed");
        return false;
    }

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
    glfwWindowHint(GLFW_SAMPLES, 4);
    glfwWindowHint(GLFW_VISIBLE, visible ? GLFW_TRUE : GLFW_FALSE);
#ifndef NDEBUG
    glfwWindowHint(GLFW_OPENGL_DEBUG_CONTEXT, GLFW_TRUE);
#endif

    window_ = glfwCreateWindow(width, height, title, nullptr, nullptr);
    if (!window_) {
        astra_viz::log::error("glfwCreateWindow failed");
        glfwTerminate();
        return false;
    }

    glfwMakeContextCurrent(window_);
    glfwSwapInterval(1);  // V-Sync; we still log FPS so 60+ is measurable

    int v = gladLoadGL(glfwGetProcAddress);
    if (v == 0) {
        astra_viz::log::error("gladLoadGL failed");
        return false;
    }
    astra_viz::log::info("GL %d.%d %s", GLAD_VERSION_MAJOR(v), GLAD_VERSION_MINOR(v),
                         glGetString(GL_RENDERER));

#ifndef NDEBUG
    if (GLAD_GL_KHR_debug) {
        glEnable(GL_DEBUG_OUTPUT);
        glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
        glDebugMessageCallback(gl_debug_callback, nullptr);
    }
#endif

    glEnable(GL_DEPTH_TEST);
    glEnable(GL_PROGRAM_POINT_SIZE);
    glClearColor(0.01f, 0.01f, 0.02f, 1.0f);

    refresh_framebuffer_size();
    return true;
}

void GLContext::refresh_framebuffer_size() {
    if (window_) {
        glfwGetFramebufferSize(window_, &fb_w_, &fb_h_);
    }
}

void GLContext::shutdown() {
    if (window_) {
        glfwDestroyWindow(window_);
        window_ = nullptr;
    }
    glfwTerminate();
}

} // namespace astra_viz
