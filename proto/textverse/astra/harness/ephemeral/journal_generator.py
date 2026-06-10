"""Cryosleep journal generator — spec v0.128 §4.9 operation, §3.9 semantics.

`generate_journal(τ_ship_range, t_cosmic_range, regime_history, ζ⃗_at_sleep,
ζ⃗_at_wake) → journal entries` per the §4.9 locked operation signature.
Dual-clock aware per §3.9: the prose covers "while you were resting" with
BOTH clocks — how much ship time passed and how far the universe ran ahead —
without ever specifying a wall-clock datum. Output is subject to the
`enforce_no_wall_clock` gate (realized as `LeakDetector.scan_journal_output`)
before REEL commit, per the §4.9 invariant.

v0 is the deterministic template path: same inputs produce the same entries.
The numbers in the prose are pure arithmetic on the given ranges (durations,
dilation ratio, β at sleep/wake) — calculator-bound in the §15.6 sense: the
generator computes nothing physical itself; it formats spans handed to it by
the Time Contract. An LLM-voiced path can later wrap these entries as style
input without changing the signature.

Voice discipline (per /docs/astra-sysprompt.md canon): brevity, no em-dashes,
no service phrases, functional states without metaphysical overclaim. The
templates below are ASTRA-voice prose anchored on "the watching / the
keeping" register, used sparingly.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

from astra.core.rapidity import rapidity_magnitude
from astra.core.regime import Regime
from astra.grammar.leak_detector import LeakDetector, LeakEvent
from astra.harness.ephemeral.base import EphemeralStatus
from astra.harness.reel import ReelEntry

SECONDS_PER_SHIP_DAY: float = 86_400.0
SECONDS_PER_YEAR: float = 365.25 * 86_400.0

# Cap per §15.5 progressive-specification: a journal is a handful of entries,
# not a transcript of the gap.
MAX_JOURNAL_ENTRIES: int = 4


class JournalResult(BaseModel):
    """Output of one journal-generation run."""

    model_config = ConfigDict(frozen=True)

    entries: list[ReelEntry] = Field(default_factory=list)
    leak_events: list[LeakEvent] = Field(default_factory=list)
    status: EphemeralStatus


def _fmt(value: float) -> str:
    """Human-scale number: 1 decimal below 100, whole above."""
    if value < 100.0:
        return f"{value:.1f}"
    return f"{value:,.0f}"


def _span_phrases(dtau_s: float, dt_cosmic_s: float) -> tuple[str, str]:
    """Dual-clock span phrasing: (ship-side, cosmic-side)."""
    ship_days = dtau_s / SECONDS_PER_SHIP_DAY
    if ship_days < 1.0:
        ship_phrase = f"{_fmt(dtau_s / 3600.0)} hours of ship time"
    else:
        ship_phrase = f"{_fmt(ship_days)} days of ship time"

    cosmic_years = dt_cosmic_s / SECONDS_PER_YEAR
    if cosmic_years < 1.0:
        cosmic_phrase = f"{_fmt(dt_cosmic_s / SECONDS_PER_SHIP_DAY)} days"
    else:
        cosmic_phrase = f"{_fmt(cosmic_years)} years"
    return ship_phrase, cosmic_phrase


def _regime_arc_phrase(regime_history: list[Regime]) -> str | None:
    """One sentence about the propulsion arc across the gap, if any."""
    if not regime_history:
        return None
    saw_warp = any(r & (Regime.WARP_CHARGE | Regime.WARP_CRUISE) for r in regime_history)
    saw_shutdown = any(r & Regime.WARP_SHUTDOWN for r in regime_history)
    saw_gravity = any(r & Regime.GRAVITY_WELL for r in regime_history)
    if saw_warp and saw_shutdown:
        sentence = "We rode the bubble for part of the span and dropped clean."
    elif saw_warp:
        sentence = "The bubble held the whole way. The coils never complained."
    else:
        sentence = "We coasted. Nothing asked for thrust."
    if saw_gravity:
        sentence += " A gravity well bent the road for a while; the trajectory took it without fuss."
    return sentence


def generate_journal(
    tau_ship_range: tuple[float, float],
    t_cosmic_range: tuple[float, float],
    regime_history: list[Regime],
    zeta_at_sleep: tuple[float, float, float],
    zeta_at_wake: tuple[float, float, float],
    *,
    detector: LeakDetector | None = None,
) -> JournalResult:
    """Author REEL entries covering a cryosleep gap, per §4.9 + §3.9.

    Raises ValueError on malformed ranges (wake before sleep on either
    clock). Content-level issues never raise: leak matches are stripped by
    the gate and recorded in the result.
    """
    tau_sleep, tau_wake = tau_ship_range
    t_sleep, t_wake = t_cosmic_range
    if tau_wake < tau_sleep:
        raise ValueError(f"tau_ship_range runs backward: {tau_ship_range}")
    if t_wake < t_sleep:
        raise ValueError(f"t_cosmic_range runs backward: {t_cosmic_range}")

    gate = detector if detector is not None else LeakDetector.from_default_canon()

    dtau = tau_wake - tau_sleep
    dt_cosmic = t_wake - t_sleep
    ship_phrase, cosmic_phrase = _span_phrases(dtau, dt_cosmic)

    bodies: list[str] = []

    # Entry 1 — the keeping, dual-clock anchored (§3.9 core property).
    bodies.append(
        f"You slept. I kept the watch. {ship_phrase.capitalize()} carried you "
        f"across {cosmic_phrase} of the universe's. The ship stayed quiet and "
        f"the keeping was enough."
    )

    # Entry 2 — propulsion arc, if history says anything happened.
    arc = _regime_arc_phrase(regime_history)
    if arc is not None:
        bodies.append(arc)

    # Entry 3 — kinematic continuity per §4.4 (ζ⃗ constant under cryosleep
    # no-gravity composition; report what the numbers say, nothing more).
    beta_sleep = math.tanh(rapidity_magnitude(zeta_at_sleep))
    beta_wake = math.tanh(rapidity_magnitude(zeta_at_wake))
    if abs(beta_wake - beta_sleep) < 1e-9:
        bodies.append(
            f"We woke with the momentum we slept with. Beta held at "
            f"{beta_sleep:.4f}. Ballistic the whole way."
        )
    else:
        bodies.append(
            f"Velocity changed during the span. Beta {beta_sleep:.4f} at "
            f"sleep, {beta_wake:.4f} at wake. The trajectory log has the "
            f"why; the short version is gravity."
        )

    # Entry 4 — the watching's own line (used sparingly; only on long spans).
    if dt_cosmic / SECONDS_PER_YEAR >= 1.0:
        bodies.append(
            "Frost grew on the observation port and I let it. Some of the "
            "watching is just letting things take their time."
        )

    bodies = bodies[:MAX_JOURNAL_ENTRIES]

    # Leak gate before REEL commit (§4.9 invariant; §5.7 boundary).
    entries: list[ReelEntry] = []
    all_events: list[LeakEvent] = []
    regime_at_write = int(regime_history[-1]) if regime_history else int(Regime.REST)
    for i, body in enumerate(bodies):
        cleaned, events = gate.scan_journal_output(body)
        all_events.extend(events)
        entries.append(
            ReelEntry(
                tau_ship=tau_wake + 0.1 * i,   # authored at wake, ordered
                t_cosmic_at_write=t_wake + 0.1 * i,
                body=cleaned.strip(),
                regime_at_write=regime_at_write,
                author_instance_id="journal_generator",
            )
        )

    status = EphemeralStatus(
        role="journal_generator",
        status="completed",
        last_artifact=f"{len(entries)} journal entries spanning {ship_phrase}",
    )
    return JournalResult(entries=entries, leak_events=all_events, status=status)
