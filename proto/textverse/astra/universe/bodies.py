"""Body queries — name-to-position resolution per spec §3.11 + §6.3.

For static-positioned bodies (sun in v0), this returns the literal
position. For Keplerian bodies, the spec §6.3 retarded-time path
requires t_emit and a Kepler solver — those queries route through
proto/astra_nexus via nexus_bridge.

Day 5 v0 surface:
- `static_position(body)`: literal position if available
- `is_keplerian(body)`: True iff body has Keplerian elements

The orchestrator's perception_assembler uses these to compose the
`<state>` section without invoking the LLM-backed Narrator for v0
scenarios.
"""

from __future__ import annotations

from astra.state_bus.schema import BodyState


def static_position(body: BodyState) -> tuple[float, float, float] | None:
    """Literal position tuple, or None if the body is Keplerian-only."""
    return body.position


def is_keplerian(body: BodyState) -> bool:
    """True iff the body has Kepler elements (orbital, not static)."""
    return body.kepler is not None


def parent_name(body: BodyState) -> str | None:
    """Name of the orbital parent, or None for non-orbiting bodies."""
    if body.kepler is None:
        return None
    return body.kepler.parent
