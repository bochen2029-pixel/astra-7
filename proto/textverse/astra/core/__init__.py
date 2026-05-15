"""astra.core — Five Invariants as data types.

Implements spec v0.128 §1:
- AstraCoord (§1.1): 128-bit hierarchical floating origin
- TimeState (§1.2): two-clock split, regime bitmask
- Rapidity (§3.7): 3-vector ζ⃗
- ShipKinematic: derived state
- Regime: canonical bitmask hex values per §3.3
- Power: subsystem list per §1.4
- HullSDF: stub at v0; full SDF deferred to Implementation B

These are pure data types. No physics is implemented here — physics lives in
`proto/astra_nexus` and is queried via `astra.physics.nexus_bridge`.

Implementation: Day 1.
"""
