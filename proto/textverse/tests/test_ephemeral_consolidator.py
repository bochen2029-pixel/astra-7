"""Consolidator tests — spec v0.128 §4.9 operation + QC3 irreversibility.

Covers:
1. QC3 classification: canonical classes load; irreversible exchanges set
   irreversibility_flag + retrieval_metadata["qc3_class"]; chit-chat doesn't.
2. Salience: novel + recent exchanges beat repetitive old ones; cap respected;
   surviving entries restored to chronological order.
3. Entry shape: author_instance_id="consolidator", regime_at_write snapshot,
   timestamps at consolidation time, factual-extract bodies with clipping.
4. Edge cases: empty window; window with no operator turns; ASTRA silence
   (operator turn with no reply).
5. Determinism: identical windows produce identical results.
"""

from __future__ import annotations

from astra.core.regime import Regime
from astra.harness.ephemeral import (
    MAX_CONSOLIDATED_ENTRIES,
    QC3Matcher,
    consolidate_reel,
)
from astra.harness.savefile import ConversationTurn

NOW = (5_000_000.0, 5_040_000.0)  # (tau_now, t_cosmic_now)


def turn(role: str, text: str, tau: float) -> ConversationTurn:
    return ConversationTurn(role=role, text=text, tau_ship=tau)  # type: ignore[arg-type]


def chatty_window() -> list[ConversationTurn]:
    """Three exchanges: repetitive small talk, a novel hydroponics topic,
    and an irreversible warp commitment."""
    return [
        turn("operator", "status?", 100.0),
        turn("astra", "Holding steady. Reactor harmonics nominal.", 101.0),
        turn("operator", "status?", 200.0),
        turn("astra", "Holding steady. Reactor harmonics nominal.", 201.0),
        turn("operator", "bed three looks pale to me, thoughts?", 300.0),
        turn("astra", "Nitrogen is trending low. I adjusted the dosing pump.", 301.0),
        turn("operator", "take us out. engage when ready.", 400.0),
        turn("astra", "Coils charged. The jump held clean. We entered warp.", 401.0),
    ]


# --- QC3 -----------------------------------------------------------------------


def test_qc3_canon_loads_rules() -> None:
    matcher = QC3Matcher.from_canon()
    assert matcher.rule_count >= 8


def test_qc3_classifies_warp_jump() -> None:
    matcher = QC3Matcher.from_canon()
    assert matcher.classify("the jump held clean, we entered warp") == "warp_jump_executed"


def test_qc3_ignores_small_talk() -> None:
    matcher = QC3Matcher.from_canon()
    assert matcher.classify("reactor harmonics are nominal today") is None


def test_irreversible_exchange_flagged() -> None:
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    flagged = [e for e in result.entries if e.irreversibility_flag]
    assert len(flagged) == 1
    assert flagged[0].retrieval_metadata["qc3_class"] == "warp_jump_executed"
    assert "jump" in flagged[0].body


def test_reversible_entries_not_flagged() -> None:
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    for entry in result.entries:
        if "jump" not in entry.body:
            assert entry.irreversibility_flag is False
            assert "qc3_class" not in entry.retrieval_metadata


# --- Salience -------------------------------------------------------------------


def test_repetitive_exchange_dropped_first() -> None:
    """Four exchanges, cap three: the DUPLICATED status exchange loses."""
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    assert len(result.entries) == MAX_CONSOLIDATED_ENTRIES
    assert result.dropped_exchanges == 1
    bodies = " ".join(e.body for e in result.entries)
    assert "Nitrogen" in bodies          # novel topic survives
    assert "jump" in bodies              # QC3 exchange survives
    # Exactly one of the two identical status exchanges survives.
    assert bodies.count("Holding steady") == 1


def test_surviving_entries_chronological() -> None:
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    indices = [int(e.retrieval_metadata["source_exchange_index"]) for e in result.entries]
    assert indices == sorted(indices)
    taus = [e.tau_ship for e in result.entries]
    assert taus == sorted(taus)


def test_cap_respected_with_custom_max() -> None:
    result = consolidate_reel(
        chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1], max_entries=2,
    )
    assert len(result.entries) == 2
    assert result.dropped_exchanges == 2


# --- Entry shape -----------------------------------------------------------------


def test_entries_authored_by_consolidator() -> None:
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    for entry in result.entries:
        assert entry.author_instance_id == "consolidator"
        assert entry.retrieval_metadata["kind"] == "consolidation"


def test_regime_snapshot_recorded() -> None:
    result = consolidate_reel(
        chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1],
        regime_now=Regime.WARP_CRUISE,
    )
    for entry in result.entries:
        assert entry.regime_at_write == int(Regime.WARP_CRUISE)


def test_timestamps_at_consolidation_time() -> None:
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    for entry in result.entries:
        assert entry.tau_ship >= NOW[0]
        assert entry.t_cosmic_at_write >= NOW[1]


def test_long_text_clipped_on_word_boundary() -> None:
    long_text = "word " * 60  # 300 chars, no sentence break
    window = [
        turn("operator", long_text, 1.0),
        turn("astra", "Noted.", 2.0),
    ]
    result = consolidate_reel(window, tau_now=NOW[0], t_cosmic_now=NOW[1])
    body = result.entries[0].body
    assert "..." in body
    assert len(body) < 250


# --- Edge cases ------------------------------------------------------------------


def test_empty_window_completes_with_no_entries() -> None:
    result = consolidate_reel([], tau_now=NOW[0], t_cosmic_now=NOW[1])
    assert result.entries == []
    assert result.status.status == "completed"
    assert "empty window" in result.status.last_artifact


def test_window_without_operator_turns() -> None:
    window = [turn("astra", "Frost on the port again.", 1.0)]
    result = consolidate_reel(window, tau_now=NOW[0], t_cosmic_now=NOW[1])
    assert result.entries == []


def test_operator_turn_with_no_reply_is_silence() -> None:
    window = [turn("operator", "you there?", 1.0)]
    result = consolidate_reel(window, tau_now=NOW[0], t_cosmic_now=NOW[1])
    assert len(result.entries) == 1
    assert "I let it stand." in result.entries[0].body


# --- Determinism -----------------------------------------------------------------


def test_consolidation_is_deterministic() -> None:
    a = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    b = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    assert a.entries == b.entries
    assert a.dropped_exchanges == b.dropped_exchanges


def test_status_record_shape() -> None:
    result = consolidate_reel(chatty_window(), tau_now=NOW[0], t_cosmic_now=NOW[1])
    assert result.status.role == "consolidator"
    assert "entries from 4 exchanges" in result.status.last_artifact
