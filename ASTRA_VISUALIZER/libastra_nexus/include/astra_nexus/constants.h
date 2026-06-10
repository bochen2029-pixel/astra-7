// libastra_nexus/include/astra_nexus/constants.h
//
// Physical constants + Vec3 — used by every other libastra header.
// Extracted from proto/astra_nexus.cpp lines 52-86 (READ-ONLY source).
// Semantics IDENTICAL to the original. Do not modify.
//
// Spec refs: §1.1 (AstraCoord), §1.2 (two-clock split), §3.7 (rapidity clamp),
// Appendix B (canonical constants).

#pragma once

#include <cmath>
#include <cstdint>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace astra {

// =============================================================================
// Physical constants (per spec Appendix B + §1.2)
// =============================================================================
constexpr double C_LIGHT     = 299792458.0;                  // m/s (exact)
constexpr double G_GRAV      = 6.67430e-11;                  // m^3 kg^-1 s^-2
constexpr double M_SUN       = 1.98892e30;                   // kg
constexpr double PARSEC      = 3.0856775814913673e16;        // m
constexpr double LIGHT_YEAR  = 9.4607304725808e15;           // m
constexpr double MPC         = 1.0e6 * PARSEC;
constexpr double H0_KMS_MPC  = 70.0;                         // km/s/Mpc (provisional)
constexpr double H0_SI       = H0_KMS_MPC * 1000.0 / MPC;    // s^-1
constexpr double OMEGA_M     = 0.3;                          // matter density (provisional)
constexpr double OMEGA_LAM   = 0.7;                          // dark energy density (provisional)
constexpr double D_HUBBLE_SI = C_LIGHT / H0_SI;              // m, Hubble horizon (~13.7 Gly @ H0=70)

// v0.126 N1 lock: clamp for 3-vector rapidity magnitude.
// cosh(16.811) ~= 1e7 (the spec-locked gamma ceiling).
constexpr double OMEGA_MAX = 16.811;

// =============================================================================
// AstraCoord scale (per spec §1.1) — sector grid + local renormalize trigger.
// SECTOR_SIZE: 1000 km in metres. LOCAL_MAX: 500 km, the renormalize threshold.
// =============================================================================
constexpr double SECTOR_SIZE = 1.0e6;
constexpr double LOCAL_MAX   = 5.0e5;

// =============================================================================
// Vec3 — minimal 3-vector. Plain-old-data; trivially copyable.
// =============================================================================
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

}  // namespace astra
