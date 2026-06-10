#include "astra_nexus/regime.h"

namespace astra {

const char* regime_label(uint32_t r) {
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

} // namespace astra
