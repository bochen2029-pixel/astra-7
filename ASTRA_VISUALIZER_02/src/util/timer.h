// timer.h - frame timing with rolling-average FPS readout.
#pragma once

namespace astra_viz {

class FrameTimer {
public:
    FrameTimer();

    // Call once per frame. Returns dt in seconds since the last call.
    double tick();

    double last_dt_s() const { return last_dt_; }
    double avg_dt_s() const  { return avg_dt_; }
    double avg_fps()  const  { return avg_dt_ > 0.0 ? 1.0 / avg_dt_ : 0.0; }

private:
    double last_time_;
    double last_dt_;
    double avg_dt_;       // simple EMA, alpha = 0.05
};

} // namespace astra_viz
