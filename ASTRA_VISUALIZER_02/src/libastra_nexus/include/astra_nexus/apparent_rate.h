// apparent_rate.h — regime-dispatched apparent-rate per spec §3.11 (v0.127).
//
// The locked physics:
//   STL_REL  (inertial v<c):   SR longitudinal Doppler sqrt((1-beta)/(1+beta)).
//                              ALWAYS positive; never reverses.
//   WARP_CRUISE (bubble gamma_kin=1, geometric recession): 1 - v_app/c.
//                              Can go arbitrarily negative for v_app > c.
//                              THIS IS THE EFFECT Scene S05 demonstrates.
//   REST / STL_NONREL: linear approx 1 - beta.
//
// Mirrors canon proto/astra_nexus.cpp:265-288.
#pragma once

#include <cstdint>

namespace astra {

double compute_apparent_rate(double v_radial, uint32_t regime);

} // namespace astra
