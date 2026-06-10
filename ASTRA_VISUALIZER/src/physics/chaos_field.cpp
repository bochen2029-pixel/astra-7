// src/physics/chaos_field.cpp

#include "physics/chaos_field.h"

#include <algorithm>
#include <cmath>
#include <random>

namespace astra::physics {

void ChaosField::init(int width, int height, uint32_t seed) {
    width_  = width;
    height_ = height;
    state_.assign(static_cast<size_t>(width) * height, 0.0f);
    mid_.assign  (static_cast<size_t>(width) * height, 0.0f);
    rhs_.assign  (static_cast<size_t>(width) * height, 0.0f);

    // Initial state: small Gaussian bump at center. Magnitude ~0.05 so the
    // Fisher-KPP nonlinear growth term has room to ramp before saturating.
    // Plus a sprinkle of seed noise so growth isn't perfectly radial.
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> noise(0.0f, 0.01f);

    float cx = width  * 0.5f;
    float cy = height * 0.5f;
    float sigma = width * 0.10f;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float dx_n = (static_cast<float>(x) - cx) / sigma;
            float dy_n = (static_cast<float>(y) - cy) / sigma;
            float gauss = 0.05f * std::exp(-(dx_n * dx_n + dy_n * dy_n));
            state_[static_cast<size_t>(y) * width + x] = gauss + noise(rng);
        }
    }
}

void ChaosField::compute_rhs(const std::vector<float>& src,
                             std::vector<float>& dst,
                             float D, float alpha) const
{
    // Periodic-BC 5-point Laplacian. dx = 1 (grid units).
    for (int y = 0; y < height_; y++) {
        int yp = (y + 1) % height_;
        int ym = (y - 1 + height_) % height_;
        for (int x = 0; x < width_; x++) {
            int xp = (x + 1) % width_;
            int xm = (x - 1 + width_) % width_;
            float c   = src[static_cast<size_t>(y)  * width_ + x];
            float vyp = src[static_cast<size_t>(yp) * width_ + x];
            float vym = src[static_cast<size_t>(ym) * width_ + x];
            float vxp = src[static_cast<size_t>(y)  * width_ + xp];
            float vxm = src[static_cast<size_t>(y)  * width_ + xm];
            float lapl = vyp + vym + vxp + vxm - 4.0f * c;
            dst[static_cast<size_t>(y) * width_ + x] =
                D * lapl + alpha * c * (1.0f - c);
        }
    }
}

void ChaosField::step_rk2(float dt, float D, float alpha) {
    if (state_.empty()) return;
    const size_t N = state_.size();

    // k1 = f(state); mid = state + dt/2 * k1
    compute_rhs(state_, rhs_, D, alpha);
    float half_dt = 0.5f * dt;
    for (size_t i = 0; i < N; i++) {
        mid_[i] = state_[i] + half_dt * rhs_[i];
    }

    // k2 = f(mid); state = state + dt * k2
    compute_rhs(mid_, rhs_, D, alpha);
    for (size_t i = 0; i < N; i++) {
        state_[i] = state_[i] + dt * rhs_[i];
    }

    // Clamp to [0, 1] — Fisher-KPP analytic invariant; numerical drift
    // may push slightly outside, especially near boundaries.
    for (size_t i = 0; i < N; i++) {
        state_[i] = std::clamp(state_[i], 0.0f, 1.0f);
    }
}

void ChaosField::apply_uniform_damping(float damping_rate, float dt) {
    if (state_.empty() || damping_rate <= 0.0f || dt <= 0.0f) return;
    float factor = std::max(0.0f, 1.0f - damping_rate * dt);
    for (size_t i = 0; i < state_.size(); i++) {
        state_[i] *= factor;
    }
}

float ChaosField::max_value() const {
    if (state_.empty()) return 0.0f;
    float m = state_[0];
    for (size_t i = 1; i < state_.size(); i++) {
        if (state_[i] > m) m = state_[i];
    }
    return m;
}

float ChaosField::mean_value() const {
    if (state_.empty()) return 0.0f;
    double sum = 0.0;
    for (float v : state_) sum += v;
    return static_cast<float>(sum / state_.size());
}

float ChaosField::at(int x, int y) const {
    if (state_.empty()) return 0.0f;
    int xc = std::clamp(x, 0, width_  - 1);
    int yc = std::clamp(y, 0, height_ - 1);
    return state_[static_cast<size_t>(yc) * width_ + xc];
}

}  // namespace astra::physics
