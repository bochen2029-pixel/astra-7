#include "physics/reflex_stub.h"

#include <algorithm>
#include <cmath>

namespace astra_viz {

float ReflexStub::update(float chaos_amplitude, float dt_s) {
    emergency_ = (chaos_amplitude >= emergency_threshold);
    if (!enabled) {
        last_error_ = 0.0f;
        integral_   = 0.0f;
        return 0.0f;
    }
    if (dt_s <= 0.0f) dt_s = 1.0f / 60.0f;

    float error      = chaos_amplitude - setpoint;
    integral_       += error * dt_s;
    // Anti-windup clamp.
    integral_        = std::clamp(integral_, -2.0f, 2.0f);
    float deriv      = (error - last_error_) / dt_s;
    last_error_      = error;

    float u = Kp * error + Ki * integral_ + Kd * deriv;
    // Beta must be non-negative (cubic damping in Fisher-KPP).
    return std::max(0.0f, u);
}

} // namespace astra_viz
