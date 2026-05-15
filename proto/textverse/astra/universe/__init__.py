"""astra.universe — the mini universe (Sun + Earth + Hot-Earth at v0).

For v0, three bodies are sufficient to demonstrate retarded-time observation:
- Sun: fixed at origin frame (or 1 AU below ship in scenario default)
- Earth: 1-year Keplerian orbit
- Hot-Earth: 1-day Keplerian orbit (synthetic; for visible retarded-time demo
             at warp 100c receding, you watch a full reverse-orbit every ~36s)

Files:
- catalog.py:   Body database, loadable from YAML
- bodies.py:    Pydantic models + Keplerian elements
- ephemeris.py: Wraps astra.physics.nexus_bridge for t_cosmic-driven body state

The Solar System full body catalog is V1+ work; defer per Progressive Spec.

Implementation: Day 5.
"""
