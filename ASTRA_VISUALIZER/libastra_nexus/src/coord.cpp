// libastra_nexus/src/coord.cpp
// Extracted from proto/astra_nexus.cpp lines 88-115. Semantics IDENTICAL.

#include "astra_nexus/coord.h"
#include <cmath>
#include <cstdlib>

namespace astra {

void AstraCoord::renormalize() {
    auto roll = [](double& local, int64_t& sector) {
        if (std::abs(local) > LOCAL_MAX) {
            int64_t n = (int64_t)std::floor(local / SECTOR_SIZE + 0.5);
            sector += n;
            local  -= n * SECTOR_SIZE;
        }
    };
    roll(lx, sx);
    roll(ly, sy);
    roll(lz, sz);
}

double astra_distance(const AstraCoord& a, const AstraCoord& b) {
    double dx = (a.sx - b.sx) * SECTOR_SIZE + (a.lx - b.lx);
    double dy = (a.sy - b.sy) * SECTOR_SIZE + (a.ly - b.ly);
    double dz = (a.sz - b.sz) * SECTOR_SIZE + (a.lz - b.lz);
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

}  // namespace astra
