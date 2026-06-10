#include "util/timer.h"

#include <GLFW/glfw3.h>

namespace astra_viz {

FrameTimer::FrameTimer()
    : last_time_(glfwGetTime()), last_dt_(1.0 / 60.0), avg_dt_(1.0 / 60.0) {}

double FrameTimer::tick() {
    double now = glfwGetTime();
    last_dt_ = now - last_time_;
    last_time_ = now;
    if (last_dt_ > 0.5) last_dt_ = 0.5;          // ignore huge stalls (debugger)
    if (last_dt_ < 1.0e-6) last_dt_ = 1.0e-6;
    avg_dt_ = avg_dt_ * 0.95 + last_dt_ * 0.05;
    return last_dt_;
}

} // namespace astra_viz
