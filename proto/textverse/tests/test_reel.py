"""Day 5 tests for the in-memory REEL."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from astra.harness import Reel, ReelEntry

# --- ReelEntry shape ---------------------------------------------------------

def test_entry_frozen() -> None:
    e = ReelEntry(tau_ship=47.5, body="third pole drift noted")
    with pytest.raises(ValidationError):
        e.body = "altered"


def test_entry_negative_tau_rejected() -> None:
    with pytest.raises(ValidationError):
        ReelEntry(tau_ship=-1.0, body="x")


def test_entry_irreversibility_default_false() -> None:
    e = ReelEntry(tau_ship=10.0, body="x")
    assert e.irreversibility_flag is False


# --- Reel writes -------------------------------------------------------------

def test_empty_reel() -> None:
    reel = Reel()
    assert len(reel) == 0
    assert reel.entries == []


def test_write_appends_and_sorts() -> None:
    reel = Reel()
    reel.write(ReelEntry(tau_ship=20.0, body="later"))
    reel.write(ReelEntry(tau_ship=10.0, body="earlier"))
    reel.write(ReelEntry(tau_ship=30.0, body="latest"))
    assert [e.body for e in reel.entries] == ["earlier", "later", "latest"]


def test_write_returns_self_for_chaining() -> None:
    reel = Reel()
    result = reel.write(ReelEntry(tau_ship=1.0, body="x"))
    assert result is reel


def test_extend_preserves_sort_order() -> None:
    reel = Reel()
    reel.extend([
        ReelEntry(tau_ship=5.0, body="five"),
        ReelEntry(tau_ship=1.0, body="one"),
        ReelEntry(tau_ship=3.0, body="three"),
    ])
    assert [e.tau_ship for e in reel.entries] == [1.0, 3.0, 5.0]


def test_construct_from_iterable_sorts() -> None:
    reel = Reel([
        ReelEntry(tau_ship=10.0, body="b"),
        ReelEntry(tau_ship=5.0, body="a"),
    ])
    assert [e.body for e in reel.entries] == ["a", "b"]


# --- recent() ----------------------------------------------------------------

def test_recent_returns_n_latest() -> None:
    reel = Reel([ReelEntry(tau_ship=float(i), body=f"e{i}") for i in range(10)])
    last3 = reel.recent(3)
    assert [e.body for e in last3] == ["e7", "e8", "e9"]


def test_recent_n_zero_returns_empty() -> None:
    reel = Reel([ReelEntry(tau_ship=1.0, body="x")])
    assert reel.recent(0) == []


def test_recent_more_than_total_returns_all() -> None:
    reel = Reel([ReelEntry(tau_ship=1.0, body="only")])
    assert len(reel.recent(10)) == 1


# --- search() ----------------------------------------------------------------

def test_search_empty_reel_returns_empty() -> None:
    reel = Reel()
    assert reel.search("reactor", k=3) == []


def test_search_returns_matching_entries() -> None:
    reel = Reel([
        ReelEntry(tau_ship=10.0, body="hydroponics nominal"),
        ReelEntry(tau_ship=20.0, body="reactor third pole drift noted"),
        ReelEntry(tau_ship=30.0, body="ship vector stable"),
    ])
    results = reel.search("reactor pole drift", k=2)
    assert results
    assert "reactor" in results[0].body or "pole" in results[0].body


def test_search_empty_query_returns_recent() -> None:
    """Empty or whitespace query falls back to recency-only ranking."""
    reel = Reel([ReelEntry(tau_ship=float(i), body=f"e{i}") for i in range(3)])
    # Empty query → recency-only via the .recent(k) fast path.
    results = reel.search("", k=2)
    assert len(results) == 2
    # Returned in chronological order; most recent at the end.
    assert results[-1].body == "e2"
    assert results[0].body == "e1"


def test_search_short_stopword_query_ranks_by_recency() -> None:
    """Tokens shorter than 3 chars are dropped; with no matchable tokens,
    ranking falls through to (0 overlap, tau_ship) and the newest entries win."""
    reel = Reel([ReelEntry(tau_ship=float(i), body=f"e{i}") for i in range(3)])
    results = reel.search("a is on", k=2)
    assert len(results) == 2
    # All tokens dropped (each < 3 chars) -> empty query_tokens -> recent(k)
    assert results[-1].body == "e2"


def test_search_k_zero_returns_empty() -> None:
    reel = Reel([ReelEntry(tau_ship=1.0, body="reactor")])
    assert reel.search("reactor", k=0) == []
