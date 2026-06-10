"""REEL — Reactor of Episodic Lifelong memory per spec v0.128 §4.6.

In-memory v0 implementation: list of entries indexed by τ_ship timestamp,
keyword retrieval. Day 5 ships the minimum surface; Day N+ swaps the
retrieval to BM25 dense retrieval and adds SQLite persistence per §4.6.

The REEL is ASTRA's continuous identity — not a chat log but a substrate-
agnostic stream of what she's attended to. Entries are short factual
prose, written in her voice, indexed by τ_ship time and tagged with
optional irreversibility flag.

v0 deliberate exclusions (Progressive Specification §15.5):
- No SQLite persistence (in-memory only).
- No consolidator ephemeral instance (Day N+).
- No dense retrieval (BM25 lib is optional; v0 falls back to keyword).
- No drift detector wiring (consumes REEL but is also Day N+).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Self

from pydantic import BaseModel, ConfigDict, Field


class ReelEntry(BaseModel):
    """One REEL entry — ASTRA-voice prose about what she attended to.

    Per spec §4.6 v0.126 (required) and §3.9 (dual-clock invariant):
    both `tau_ship` and `t_cosmic` must be recorded at write time. The
    cryosleep journal generator (§3.9) cannot satisfy its input contract
    without `t_cosmic_at_write` — it's the only way to reconstruct
    "while you were resting" prose with the correct cosmic-time span.

    Full §4.6 canonical field set (audit D4 closure, completed with the
    §4.9 ephemeral-instance work 2026-06-10): `t_emit_event` records the
    source-frame cosmic time for entries about observed distant events
    (v0.127 two-clock memory of observation); `regime_at_write` snapshots
    the composite regime bitmask (§3.3 canonical hex, wire-stable int);
    `author_instance_id` distinguishes main-loop writes from ephemeral
    instances (consolidator / journal_generator / drift_detector);
    `retrieval_metadata` carries retrieval hints. All default — entries
    written before this closure load unchanged.
    """

    model_config = ConfigDict(frozen=True)

    tau_ship: float = Field(ge=0.0)              # τ_ship at write time
    t_cosmic_at_write: float = Field(ge=0.0)     # required per §4.6 v0.126 / §3.9
    body: str                                    # prose; ASTRA's voice
    irreversibility_flag: bool = False           # True for entries about
                                                  # decisions / outcomes that
                                                  # cannot be undone (per §4.6
                                                  # monotonic-irreversibility
                                                  # gate)
    t_emit_event: float | None = None            # §4.6 v0.127: when the observed
                                                  # distant event happened at the
                                                  # source (cosmic time); None for
                                                  # local entries
    regime_at_write: int = 0                     # §3.3 bitmask at write time
    author_instance_id: str = "main"             # §4.9: main | consolidator |
                                                  # journal_generator | drift_detector
    retrieval_metadata: dict[str, str] = Field(default_factory=dict)


class Reel:
    """In-memory REEL with keyword + recency retrieval.

    Day 5 v0 retrieval = (recency-decay + keyword-overlap) score. The
    BM25 library `rank-bm25` is in the project's dependency set but not
    required at v0 — keyword overlap is adequate for the watch_47_morning
    scenario.
    """

    def __init__(self, entries: Iterable[ReelEntry] = ()) -> None:
        self._entries: list[ReelEntry] = sorted(entries, key=lambda e: e.tau_ship)

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> list[ReelEntry]:
        return list(self._entries)

    def write(self, entry: ReelEntry) -> Self:
        """Append a new entry and return self (for chaining)."""
        self._entries.append(entry)
        self._entries.sort(key=lambda e: e.tau_ship)
        return self

    def extend(self, entries: Iterable[ReelEntry]) -> Self:
        """Append many entries; preserves τ_ship sort order."""
        self._entries.extend(entries)
        self._entries.sort(key=lambda e: e.tau_ship)
        return self

    def recent(self, n: int = 5) -> list[ReelEntry]:
        """Return the last n entries by τ_ship time, newest last."""
        if n <= 0:
            return []
        return self._entries[-n:]

    def search(self, query: str, k: int = 3) -> list[ReelEntry]:
        """Keyword-overlap + recency retrieval.

        Day 5 v0: tokenize query (whitespace + lowercase), score each entry
        by token-set overlap, break ties by recency. No BM25 yet — that's
        Day N+ when scenarios surface need for fuzzier matching.
        """
        if k <= 0 or not self._entries:
            return []
        query_tokens = {tok for tok in query.lower().split() if len(tok) > 2}
        if not query_tokens:
            return self.recent(k)

        def score(entry: ReelEntry) -> tuple[int, float]:
            entry_tokens = {tok for tok in entry.body.lower().split() if len(tok) > 2}
            overlap = len(query_tokens & entry_tokens)
            return (overlap, entry.tau_ship)

        ranked = sorted(self._entries, key=score, reverse=True)
        return ranked[:k]
