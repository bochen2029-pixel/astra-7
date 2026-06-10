// src/physics/chaos_field.h — 2D Fisher-KPP chaos field (CPU-side).
//
// Spec: DESIGN_SPEC §7.1 (chaos PDE Fisher-KPP); §4.4 (CFL bound).
//
// Equation:
//   dchi/dt = D * laplacian(chi) + alpha * chi * (1 - chi)
//
// Discretization:
//   Spatial: 5-point Laplacian on uniform grid (periodic BCs)
//   Temporal: RK2 midpoint method
//   CFL bound: dt < dx^2 / (4*D); for dx=1 and D=0.5, dt < 0.5 (safely above 1/60).
//
// V1.13 implements CPU-side; V1.14 will port to CUDA kernel + double-buffered
// surface for §6 12-step pipeline integration. CPU implementation lets V1.13
// land 12/12 spec scenes without expanding CUDA risk surface.

#pragma once

#include <cstdint>
#include <vector>

namespace astra::physics {

class ChaosField {
public:
    ChaosField() = default;
    void init(int width, int height, uint32_t seed = 0xA57DA7U);

    // Advance one RK2 step. dt should obey CFL: dt < dx^2 / (4*D); dx = 1.
    void step_rk2(float dt, float D, float alpha);

    // Reflex stub: uniform-rate damping applied directly to the field.
    // Models the Reflex controller's "nacelle_damping" effect at the field level.
    // damping_rate units: 1/sec. Each tick: field *= (1 - damping_rate*dt).
    void apply_uniform_damping(float damping_rate, float dt);

    float max_value() const;
    float mean_value() const;

    const std::vector<float>& data() const { return state_; }
    int width()  const { return width_; }
    int height() const { return height_; }

    // Read the value at a single grid cell (clamped to bounds).
    float at(int x, int y) const;

private:
    int width_ = 0, height_ = 0;
    std::vector<float> state_;
    std::vector<float> mid_;
    std::vector<float> rhs_;

    void compute_rhs(const std::vector<float>& src, std::vector<float>& dst,
                     float D, float alpha) const;
};

}  // namespace astra::physics
