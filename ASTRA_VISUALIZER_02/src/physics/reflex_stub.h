// reflex_stub.h - tiny PID controller for the V7 Reflex feedback loop.
// Per spec §2.3.1 (v0.129 NEW Reflex Contract); V7 ships the stub. The real
// NNE / TensorRT-backed Reflex is deferred to Phase 2+ per DESIGN_SPEC §8.
//
// Input:  chaos amplitude (proxy for max(chi); cheap centre-voxel read).
// Output: a damping coefficient that the chaos PDE consumes as beta (cubic term).
//         When chaos > setpoint, output rises -> beta increases -> chaos shrinks.
//         When chaos < setpoint, output falls -> beta drops -> chaos grows.
//
// The "emergency dump" is a separate one-shot signal triggered when chaos
// exceeds emergency_threshold; the host calls ChaosField::clear() and re-seeds.
#pragma once

namespace astra_viz {

class ReflexStub {
public:
    // PID gains. Defaults tuned by inspection: rapidly damps chaos within ~1s.
    float Kp = 5.0f;
    float Ki = 0.2f;
    float Kd = 0.5f;

    float setpoint            = 0.30f;
    float emergency_threshold = 0.90f;

    bool  enabled             = false;

    // Per-frame update. Returns the recommended `beta` value (cubic damping) for
    // the next chaos_pde step. When disabled, returns 0 (no damping).
    float update(float chaos_amplitude, float dt_s);

    // True if the last update saw chaos >= emergency_threshold (one-shot per
    // update; the caller is responsible for executing the dump).
    bool  emergency_trigger() const { return emergency_; }

    void  reset() { integral_ = 0.0f; last_error_ = 0.0f; emergency_ = false; }

private:
    float integral_   = 0.0f;
    float last_error_ = 0.0f;
    bool  emergency_  = false;
};

} // namespace astra_viz
