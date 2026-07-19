"""AstraCoord — 128-bit hierarchical floating origin per spec v0.129 §1.1.

The ship is anchored at sector (0,0,0), local (0,0,0) in her own frame.
The universe moves backward around her. Renormalization rolls integer
sector indices when local offset magnitude exceeds 500 km.

Maximum reach: ~974 million light-years at sub-millimeter precision via
int64 sectors plus float64 local offsets.

Locked: composite-tensor primitive, renormalization rule, ship-at-origin.
Tolerable: sector size (1000 km design center; ±decade permitted).
"""

from __future__ import annotations

from math import sqrt
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

SECTOR_SIZE_M: float = 1_000_000.0      # 1000 km macro-grid sector edge
LOCAL_OFFSET_MAX_M: float = 500_000.0   # |local offset| ≤ 500 km per spec §1.1


class AstraCoord(BaseModel):
    """128-bit composite position: int64 sector + float64 local offset (m).

    Field shape:
    - sx, sy, sz: int64 sector indices (1000 km grid)
    - lx, ly, lz: meters, local offset; ‖(lx,ly,lz)‖₂ ≤ 500_000 m

    Frame-coherent reads are enforced at the StateBus level: AstraCoord
    instances are frozen, so a frame's snapshot cannot be mutated.
    """

    model_config = ConfigDict(frozen=True)

    sx: int
    sy: int
    sz: int
    lx: float = 0.0
    ly: float = 0.0
    lz: float = 0.0

    @model_validator(mode="after")
    def _check_local_offset_bound(self) -> Self:
        mag = sqrt(self.lx * self.lx + self.ly * self.ly + self.lz * self.lz)
        if mag > LOCAL_OFFSET_MAX_M:
            raise ValueError(
                f"AstraCoord local offset magnitude {mag:.3f} m exceeds the "
                f"{LOCAL_OFFSET_MAX_M} m bound (spec v0.129 §1.1). "
                f"Renormalize sector indices before constructing."
            )
        return self


def astra_distance(a: AstraCoord, b: AstraCoord) -> float:
    """Euclidean separation in meters, sector-first.

    Mirrors the C++ `astra_distance` in proto/astra_nexus.cpp (§1.1): the
    int64 sector delta is exact and the local delta is clean — positions
    are never flattened into a single float64 before differencing, so
    nearby pairs are exact to double and far pairs are relatively precise.
    """
    dx = (a.sx - b.sx) * SECTOR_SIZE_M + (a.lx - b.lx)
    dy = (a.sy - b.sy) * SECTOR_SIZE_M + (a.ly - b.ly)
    dz = (a.sz - b.sz) * SECTOR_SIZE_M + (a.lz - b.lz)
    return sqrt(dx * dx + dy * dy + dz * dz)
