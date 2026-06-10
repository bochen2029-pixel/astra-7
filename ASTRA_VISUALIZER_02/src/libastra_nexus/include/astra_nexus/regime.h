// regime.h — Regime bitmask per spec §3.3 (canonical hex values v0.125).
// Mirrors canon proto/astra_nexus.cpp:120-142.
#pragma once

#include <cstdint>

namespace astra {

enum Regime : uint32_t {
    R_REST          = 0x00,
    R_STL_NONREL    = 0x01,
    R_STL_REL       = 0x02,
    R_WARP_CHARGE   = 0x04,
    R_WARP_CRUISE   = 0x08,
    R_WARP_SHUTDOWN = 0x10,
    R_GRAVITY_WELL  = 0x20,
    R_CRYOSLEEP     = 0x40,
};

const char* regime_label(uint32_t r);

} // namespace astra
