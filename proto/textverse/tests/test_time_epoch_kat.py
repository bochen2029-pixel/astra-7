"""TimeCoord forbidden-path KAT + epoch bound — spec-v0.130-DRAFT §2.1 (QCR-3).

Kept permanently, like the §3.7 catastrophic-cancellation KAT in the C++
suite: it demonstrates WHY the epoch-zero convention and the 2^39 s bound
exist, so the failure mode can never be un-learned.

The finding: §4.2's former "seconds since Big Bang (or epoch zero)" wording
permitted a configuration in which §5.3's locked replay tolerance
(ε < 1e-4 s on t_cosmic) is violated by float64 ULP arithmetic alone —
64 seconds of representational granularity at the cosmological epoch.
Same class as the v0.125 rapidity-clamp bug (N1): a numeric primitive that
passes casual review while silently under-delivering by orders of
magnitude. Caught by the §10 round-trip discipline applied jointly to
§4.2 × §5.3.
"""

from __future__ import annotations

from math import ulp

import pytest
from pydantic import ValidationError

from astra.core.time_state import T_COSMIC_MAX, TimeState

COSMOLOGICAL_EPOCH_S = 4.35e17  # ~13.8 Gyr in seconds (the forbidden origin)
REPLAY_EPSILON_S = 1e-4         # §5.3 REPLAY-EXACT drift tolerance


def test_ulp_wall_at_cosmological_epoch() -> None:
    """At a since-Big-Bang epoch, float64 granularity is 64 whole seconds —
    six orders of magnitude beyond the §5.3 tolerance."""
    assert ulp(COSMOLOGICAL_EPOCH_S) == 64.0
    assert ulp(COSMOLOGICAL_EPOCH_S) > REPLAY_EPSILON_S * 1e5


def test_forbidden_path_increment_vanishes_at_epoch() -> None:
    """The forbidden accumulation pattern `t += dt`: below half-ULP the
    increment is lost ENTIRELY. At the cosmological epoch even a full
    one-second tick does not advance cosmic time at all."""
    t = COSMOLOGICAL_EPOCH_S
    assert t + REPLAY_EPSILON_S == t
    assert t + 1.0 == t          # half-ULP is 32 s; +1 s rounds away
    assert t + 31.0 == t         # still under half-ULP
    assert t + 33.0 != t         # past half-ULP it finally registers


def test_epoch_zero_domain_holds_tolerance() -> None:
    """Within the locked bound the representation honors §5.3 everywhere:
    ULP at the top of the legal domain is ≤ 6.1e-5 s < ε, and bench-scale
    values (~1.5e10 s) sit three orders inside."""
    assert ulp(T_COSMIC_MAX - 1.0) <= REPLAY_EPSILON_S
    assert ulp(1.5e10) < 1e-5


def test_time_state_rejects_beyond_epoch_bound() -> None:
    with pytest.raises(ValidationError, match="epoch-zero domain"):
        TimeState(
            t_cosmic=T_COSMIC_MAX,
            tau_ship=0.0,
            tau_crew_biological=0.0,
        )
    with pytest.raises(ValidationError, match="epoch-zero domain"):
        TimeState(
            t_cosmic=COSMOLOGICAL_EPOCH_S,
            tau_ship=0.0,
            tau_crew_biological=0.0,
        )


def test_time_state_accepts_legal_domain() -> None:
    ts = TimeState(
        t_cosmic=T_COSMIC_MAX - 1.0,
        tau_ship=47.0,
        tau_crew_biological=47.0,
    )
    assert ts.t_cosmic < T_COSMIC_MAX
    bench = TimeState(t_cosmic=1.5e10, tau_ship=47.5, tau_crew_biological=47.5)
    assert bench.t_cosmic == 1.5e10
