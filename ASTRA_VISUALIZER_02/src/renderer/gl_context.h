// gl_context.h - GLFW + GLAD bootstrap. Owns the GLFW window and its GL 4.6 context.
#pragma once

struct GLFWwindow;

namespace astra_viz {

class GLContext {
public:
    // Creates a window with the given dims + title. Pass visible=false for the
    // headless code path so GLFW creates the GL context without popping a
    // window on screen.
    bool init(int width, int height, const char* title, bool visible = true);
    void shutdown();

    GLFWwindow* window() const { return window_; }
    int framebuffer_width()  const { return fb_w_; }
    int framebuffer_height() const { return fb_h_; }

    // Re-queries the framebuffer size each call. Cheap.
    void refresh_framebuffer_size();

private:
    GLFWwindow* window_ = nullptr;
    int fb_w_ = 0;
    int fb_h_ = 0;
};

} // namespace astra_viz
