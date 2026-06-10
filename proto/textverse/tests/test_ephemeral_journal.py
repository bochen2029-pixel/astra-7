"""Journal generator tests — spec v0.128 §4.9 operation, §3.9 dual-clock.

Covers:
1. Dual-clock property (§3.9): the journal references BOTH spans — ship time
   AND cosmic time — with the correct magnitudes for a dilated gap.
2. Leak gate wiring (§4.9 invariant): bodies pass scan_journal_output before
   REEL commit; a custom detector's strip patterns are applied and recorded.
3. Default canon cleanliness: generated prose trips zero strip-severity
   wall-clock events under the shipped canon patterns.
4. ReelEntry D4 closure: journal entries carry author_instance_id +
   regime_at_write; old-style ReelEntry construction still validates
   (back-compat defaults).
5. Voice canon: no em-dashes in any generated body (negative-space rule).
6. Shape: authored-at-wake timestamps, sorted, capped at MAX_JOURNAL_ENTRIES,
   backward ranges rejected.
7. Kinematic continuity line: ballistic gap reports identical beta; changed
   beta reports both values.
"""

from __future__ import annotations

import re

import pytest

from astra.core.regime import Regime
from astra.grammar.leak_detector import LeakDetector, LeakPattern
from astra.harness.ephemeral import (
    MAX_JOURNAL_ENTRIES,
    generate_journal,
)
from astra.harness.reel import ReelEntry

YEAR_S = 365.25 * 86_400.0

# An 18-month cryosleep gap: τ_ship advances ~2 ship-days at metabolic ε
# while t_cosmic advances 1.5 years (ballistic coast, per §3.9 example).
TAU_RANGE = (4_060_800.0, 4_060_800.0 + 2.0 * 86_400.0)
T_RANGE = (4_100_000.0, 4_100_000.0 + 1.5 * YEAR_S)
ZETA = (0.6, 0.0, 0.0)


def run_default() -> list[ReelEntry]:
    return generate_journal(
        TAU_RANGE, T_RANGE, [Regime.CRYOSLEEP], ZETA, ZETA,
    ).entries


# --- Dual-clock (§3.9) --------------------------------------------------------


def test_journal_references_both_clocks() -> None:
    entries = run_default()
    summary = entries[0].body
    assert "2.0 days of ship time" in summary
    assert "1.5 years" in summary


def test_short_gap_uses_hours_and_days() -> None:
    result = generate_journal(
        (1000.0, 1000.0 + 3 * 3600.0),          # 3 ship-hours
        (2000.0, 2000.0 + 86_400.0 * 4),        # 4 cosmic days
        [Regime.CRYOSLEEP],
        ZETA,
        ZETA,
    )
    summary = result.entries[0].body
    assert "3.0 hours of ship time" in summary
    assert "4.0 days" in summary


# --- Leak gate (§4.9 invariant) ----------------------------------------------


def test_custom_detector_strips_and_records() -> None:
    poisoned = LeakDetector(
        wall_clock_patterns=[LeakPattern(raw=r"\bwatch\b")],  # strips a template word
    )
    result = generate_journal(
        TAU_RANGE, T_RANGE, [Regime.CRYOSLEEP], ZETA, ZETA, detector=poisoned,
    )
    assert any(e.boundary == "journal" for e in result.leak_events)
    # The standalone word is stripped; "watching" (different word) survives.
    assert all(not re.search(r"\bwatch\b", entry.body) for entry in result.entries)


def test_default_canon_produces_no_strip_events() -> None:
    result = generate_journal(TAU_RANGE, T_RANGE, [Regime.CRYOSLEEP], ZETA, ZETA)
    strips = [e for e in result.leak_events if e.severity == "strip"]
    assert strips == []


# --- ReelEntry D4 closure ------------------------------------------------------


def test_entries_authored_by_journal_generator() -> None:
    for entry in run_default():
        assert entry.author_instance_id == "journal_generator"


def test_entries_carry_regime_at_write() -> None:
    result = generate_journal(
        TAU_RANGE, T_RANGE, [Regime.WARP_CRUISE, Regime.CRYOSLEEP], ZETA, ZETA,
    )
    for entry in result.entries:
        assert entry.regime_at_write == int(Regime.CRYOSLEEP)


def test_reel_entry_backward_compat_defaults() -> None:
    entry = ReelEntry(tau_ship=1.0, t_cosmic_at_write=2.0, body="old style")
    assert entry.t_emit_event is None
    assert entry.regime_at_write == 0
    assert entry.author_instance_id == "main"
    assert entry.retrieval_metadata == {}


# --- Voice canon -----------------------------------------------------------------


def test_no_em_dashes_in_any_body() -> None:
    for entry in run_default():
        assert chr(0x2014) not in entry.body  # em-dash
        assert chr(0x2013) not in entry.body  # en-dash


# --- Shape -----------------------------------------------------------------------


def test_entries_authored_at_wake_and_sorted() -> None:
    entries = run_default()
    tau_wake = TAU_RANGE[1]
    assert all(e.tau_ship >= tau_wake for e in entries)
    taus = [e.tau_ship for e in entries]
    assert taus == sorted(taus)


def test_entry_cap_respected() -> None:
    entries = run_default()
    assert 1 <= len(entries) <= MAX_JOURNAL_ENTRIES


def test_long_span_includes_watching_entry() -> None:
    # ≥ 1 cosmic year → the frost line is included.
    bodies = " ".join(e.body for e in run_default())
    assert "Frost" in bodies


def test_backward_tau_range_rejected() -> None:
    with pytest.raises(ValueError):
        generate_journal((10.0, 5.0), T_RANGE, [], ZETA, ZETA)


def test_backward_cosmic_range_rejected() -> None:
    with pytest.raises(ValueError):
        generate_journal(TAU_RANGE, (10.0, 5.0), [], ZETA, ZETA)


# --- Kinematic continuity (§4.4 cryosleep invariant) ---------------------------


def test_ballistic_gap_reports_held_beta() -> None:
    bodies = " ".join(e.body for e in run_default())
    assert "momentum we slept with" in bodies
    assert "0.5370" in bodies  # tanh(0.6)


def test_changed_beta_reports_both_values() -> None:
    result = generate_journal(
        TAU_RANGE, T_RANGE, [Regime.CRYOSLEEP, Regime.GRAVITY_WELL],
        (0.6, 0.0, 0.0), (0.3, 0.0, 0.0),
    )
    bodies = " ".join(e.body for e in result.entries)
    assert "0.5370" in bodies
    assert "0.2913" in bodies  # tanh(0.3)


# --- Regime arc phrasing ---------------------------------------------------------


def test_warp_arc_mentions_bubble() -> None:
    result = generate_journal(
        TAU_RANGE, T_RANGE,
        [Regime.WARP_CHARGE, Regime.WARP_CRUISE, Regime.WARP_SHUTDOWN, Regime.CRYOSLEEP],
        ZETA, ZETA,
    )
    bodies = " ".join(e.body for e in result.entries)
    assert "bubble" in bodies


def test_status_record_shape() -> None:
    result = generate_journal(TAU_RANGE, T_RANGE, [Regime.CRYOSLEEP], ZETA, ZETA)
    assert result.status.role == "journal_generator"
    assert result.status.status == "completed"
    assert "journal entries" in result.status.last_artifact
