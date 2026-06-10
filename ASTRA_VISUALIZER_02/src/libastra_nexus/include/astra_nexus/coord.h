// coord.h — AstraCoord 128-bit hierarchical floating origin per spec §1.1.
// Mirrors canon proto/astra_nexus.cpp:89-115.
#pragma once

#include <cstdint>

namespace astra {

constexpr double SECTOR_SIZE = 1.0e6;  // 1000 km in metres
constexpr double LOCAL_MAX   = 5.0e5;  // 500 km - renormalization trigger

struct AstraCoord {
    int64_t sx, sy, sz;
    double  lx, ly, lz;

    void renormalize();
};

double astra_distance(const AstraCoord& a, const AstraCoord& b);

} // namespace astra
