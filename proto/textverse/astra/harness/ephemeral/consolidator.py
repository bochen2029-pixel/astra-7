"""Consolidator ephemeral — spec v0.128 §4.9 operation.

`consolidate_reel(window) → REEL entries`: reviews recent conversation,
scores salience, produces clean long-term entries, and sets
`irreversibility_flag` per the canonical QC3 event-class list.

v0 is deterministic (same window, same entries):

- The window is grouped into exchanges (operator turn + ASTRA's reply turns).
- Salience per exchange = 0.4·recency + 0.4·novelty + 0.5·QC3 bonus, where
  novelty is 1 minus the best token-overlap against EARLIER exchanges
  (repetition consolidates poorly; new topics consolidate well) and the QC3
  bonus fires when the exchange text matches an irreversible-event class.
- The top `max_entries` exchanges (restored to chronological order) become
  REEL entries with factual extract bodies in a brevity-compatible register,
  `author_instance_id="consolidator"`, `regime_at_write` snapshot, and
  `retrieval_metadata` carrying the QC3 class when one matched.

The QC3 list ships in-package at `astra/harness/ephemeral/canon/
qc3_events.txt` (spec §4.9 names `tests/qc3_events.txt`; the in-package
location follows the grammar/canon precedent so runtime code never reads
from tests/ — flagged as a v0.129 wording candidate).

LLM-voiced consolidation arrives later behind the same signature; the
salience machinery and QC3 gating stay.
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from astra.core.regime import Regime
from astra.harness.ephemeral.base import EphemeralStatus
from astra.harness.reel import ReelEntry
from astra.harness.savefile import ConversationTurn

MAX_CONSOLIDATED_ENTRIES: int = 3
_CLIP_CHARS: int = 90

# Salience weights (PROVISIONAL; deterministic v0 tuning).
_W_RECENCY: float = 0.4
_W_NOVELTY: float = 0.4
_W_QC3: float = 0.5


class QC3Matcher:
    """Canonical irreversible-event classifier (first match wins)."""

    def __init__(self, rules: list[tuple[str, re.Pattern[str]]]) -> None:
        self._rules = rules

    @classmethod
    def from_canon(cls) -> QC3Matcher:
        return cls.from_file(
            Path(__file__).resolve().parent / "canon" / "qc3_events.txt"
        )

    @classmethod
    def from_file(cls, path: Path) -> QC3Matcher:
        rules: list[tuple[str, re.Pattern[str]]] = []
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or " | " not in stripped:
                    continue
                label, raw = stripped.split(" | ", 1)
                rules.append((label.strip(), re.compile(raw.strip(), re.IGNORECASE)))
        return cls(rules)

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def classify(self, text: str) -> str | None:
        """Return the first matching QC3 class label, or None."""
        for label, regex in self._rules:
            if regex.search(text):
                return label
        return None

    def classify_with_sentence(self, text: str) -> tuple[str, str] | None:
        """Return (class label, the sentence containing the match), or None.

        A consolidated entry about an irreversible event must PRESERVE the
        irreversible fact in its body — clipping to the first sentence would
        otherwise drop it. Rule order is canonical precedence; within a rule,
        the earliest matching sentence wins.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for label, regex in self._rules:
            for sentence in sentences:
                if regex.search(sentence):
                    return label, sentence.strip()
        return None


class ConsolidationResult(BaseModel):
    """Output of one consolidation run."""

    model_config = ConfigDict(frozen=True)

    entries: list[ReelEntry] = Field(default_factory=list)
    dropped_exchanges: int = 0
    status: EphemeralStatus


class _Exchange(BaseModel):
    model_config = ConfigDict(frozen=True)

    operator_text: str
    astra_text: str
    tau_ship: float
    index: int

    @property
    def combined(self) -> str:
        return f"{self.operator_text} {self.astra_text}"


def _group_exchanges(window: list[ConversationTurn]) -> list[_Exchange]:
    """Pair each operator turn with the ASTRA reply text that follows it."""
    exchanges: list[_Exchange] = []
    i = 0
    while i < len(window):
        turn = window[i]
        if turn.role != "operator":
            i += 1
            continue
        astra_parts: list[str] = []
        j = i + 1
        while j < len(window) and window[j].role == "astra":
            astra_parts.append(window[j].text)
            j += 1
        exchanges.append(
            _Exchange(
                operator_text=turn.text.strip(),
                astra_text=" ".join(astra_parts).strip(),
                tau_ship=turn.tau_ship,
                index=len(exchanges),
            )
        )
        i = j
    return exchanges


def _tokens(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-z0-9']+", text.lower()) if len(tok) > 2}


def _novelty(exchange: _Exchange, earlier: list[_Exchange]) -> float:
    """1 − best Jaccard overlap against earlier exchanges. First is fully novel."""
    mine = _tokens(exchange.combined)
    if not mine or not earlier:
        return 1.0
    best = 0.0
    for prior in earlier:
        theirs = _tokens(prior.combined)
        if not theirs:
            continue
        overlap = len(mine & theirs) / len(mine | theirs)
        best = max(best, overlap)
    return 1.0 - best


def _clip(text: str, limit: int = _CLIP_CHARS) -> str:
    """First-sentence-or-limit extract, cut on a word boundary."""
    sentence = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0].strip()
    if len(sentence) <= limit:
        return sentence
    cut = sentence[:limit].rsplit(" ", 1)[0]
    return cut + "..."


def consolidate_reel(
    window: list[ConversationTurn],
    *,
    tau_now: float,
    t_cosmic_now: float,
    regime_now: Regime = Regime.REST,
    max_entries: int = MAX_CONSOLIDATED_ENTRIES,
    qc3: QC3Matcher | None = None,
) -> ConsolidationResult:
    """Consolidate a conversation window into long-term REEL entries (§4.9)."""
    matcher = qc3 if qc3 is not None else QC3Matcher.from_canon()
    exchanges = _group_exchanges(window)

    if not exchanges:
        return ConsolidationResult(
            entries=[],
            dropped_exchanges=0,
            status=EphemeralStatus(
                role="consolidator",
                status="completed",
                last_artifact="0 entries (empty window)",
            ),
        )

    n = len(exchanges)
    scored: list[tuple[float, _Exchange, tuple[str, str] | None]] = []
    for k, exchange in enumerate(exchanges):
        recency = (k + 1) / n
        novelty = _novelty(exchange, exchanges[:k])
        qc3_hit = matcher.classify_with_sentence(exchange.combined)
        score = (
            _W_RECENCY * recency
            + _W_NOVELTY * novelty
            + (_W_QC3 if qc3_hit is not None else 0.0)
        )
        scored.append((score, exchange, qc3_hit))

    keep = sorted(scored, key=lambda item: item[0], reverse=True)[:max_entries]
    keep.sort(key=lambda item: item[1].index)  # chronological in the REEL

    entries: list[ReelEntry] = []
    for offset, (_, exchange, qc3_hit) in enumerate(keep):
        qc3_class = qc3_hit[0] if qc3_hit is not None else None
        op = _clip(exchange.operator_text)
        if not exchange.astra_text:
            ast = "I let it stand."
        elif qc3_hit is not None and qc3_hit[1] in exchange.astra_text:
            # Preserve the irreversible fact: clip the QC3 sentence itself.
            ast = _clip(qc3_hit[1])
        else:
            ast = _clip(exchange.astra_text)
        metadata: dict[str, str] = {
            "kind": "consolidation",
            "source_exchange_index": str(exchange.index),
        }
        if qc3_class is not None:
            metadata["qc3_class"] = qc3_class
        entries.append(
            ReelEntry(
                tau_ship=tau_now + 0.1 * offset,
                t_cosmic_at_write=t_cosmic_now + 0.1 * offset,
                body=f"The operator said: {op} I said: {ast}",
                irreversibility_flag=qc3_class is not None,
                regime_at_write=int(regime_now),
                author_instance_id="consolidator",
                retrieval_metadata=metadata,
            )
        )

    return ConsolidationResult(
        entries=entries,
        dropped_exchanges=n - len(keep),
        status=EphemeralStatus(
            role="consolidator",
            status="completed",
            last_artifact=f"{len(entries)} entries from {n} exchanges",
        ),
    )
