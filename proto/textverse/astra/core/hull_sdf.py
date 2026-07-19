"""HullSDF — stub for v0; full SDF deferred to Implementation B (UE5).

Per spec v0.129 §1.3, the ship's physical form is one signed-distance field
read through an additive damage map. UE5 (Implementation B) provides the
actual SDF texture; textverse (Implementation A) doesn't render hulls, so it
carries damage state only.

Day 1 exposes the provisional zone list used by StateBus.hull_damage:
    dict[zone_name, damage_scalar in [0, 1]]

Zone names are provisional; locked when the ship spec lands in Day 5.
"""

from __future__ import annotations

PROVISIONAL_ZONES: tuple[str, ...] = (
    "bridge",
    "engineering",
    "habitat",
    "lifesupport",
    "medical",
    "observation",
    "cargo",
    "hull_forward",
    "hull_aft",
    "hull_dorsal",
    "hull_ventral",
)
