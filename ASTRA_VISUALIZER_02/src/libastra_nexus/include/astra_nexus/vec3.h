// vec3.h — minimal 3-vector. Header-only, host code (no CUDA __device__ here).
// Mirrors canon proto/astra_nexus.cpp:74-86.
#pragma once

#include <cmath>

namespace astra {

struct Vec3 {
    double x, y, z;

    Vec3 operator+(Vec3 b) const { return {x + b.x, y + b.y, z + b.z}; }
    Vec3 operator-(Vec3 b) const { return {x - b.x, y - b.y, z - b.z}; }
    Vec3 operator*(double s) const { return {x * s, y * s, z * s}; }
    Vec3 operator/(double s) const { return {x / s, y / s, z / s}; }

    double dot(Vec3 b) const { return x * b.x + y * b.y + z * b.z; }
    double mag() const { return std::sqrt(dot(*this)); }

    Vec3 normalized() const {
        double m = mag();
        return m > 1e-300 ? *this / m : Vec3{0, 0, 0};
    }
};

} // namespace astra
