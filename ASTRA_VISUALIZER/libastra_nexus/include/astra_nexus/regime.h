// libastra_nexus/include/astra_nexus/regime.h
//
// Regime bitmask + label (per spec §3.3, canonical hex values v0.125).
// Extracted from proto/astra_nexus.cpp lines 118-142 (READ-ONLY source).

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

// Return the propulsion-state label for the low 5 bits of `r`.
// GRAVITY_WELL / CRYOSLEEP are composite bits and not labelled here.
inline const char* regime_label(uint32_t r) {
    uint32_t prop = r & 0x1F;
    switch (prop) {
        case R_REST:          return "REST";
        case R_STL_NONREL:    return "STL_NONREL";
        case R_STL_REL:       return "STL_REL";
        case R_WARP_CHARGE:   return "WARP_CHARGE";
        case R_WARP_CRUISE:   return "WARP_CRUISE";
        case R_WARP_SHUTDOWN: return "WARP_SHUTDOWN";
        default:              return "UNKNOWN";
    }
}

}  // namespace astra
