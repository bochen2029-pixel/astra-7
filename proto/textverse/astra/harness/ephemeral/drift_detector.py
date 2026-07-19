"""Drift detector ephemeral — spec v0.129 §4.9 operation.

`detect_drift(recent_turns) → correction artifact or None` per the §4.9
locked signature. Scans ASTRA's recent SPEECH (operator-facing text only;
think-channel discipline is the grammar layer's concern) for register drift
against the voice canon, and emits a correction artifact carrying an
audit-register REEL entry when drift is found.

v0 is deterministic and composes the EXISTING canon sources rather than
duplicating them:

- em-dash / markdown / service-phrase patterns from `astra.judge.gates`
  (the PERSONA_STABLE vocabulary);
- wall-clock + technical-substrate leakage from
  `astra.grammar.LeakDetector.scan_speech` (§5.7 canon files).

The correction entry is written in a restrained audit register, first
person, brevity canon (no em-dashes, no service phrasing, no mechanism
vocabulary in the entry itself). An LLM-voiced corrective path can arrive
later behind the same signature.

§4.9 invariant: this instance reads turns and produces a REEL-committable
artifact; it never calls the other ephemerals and never emits to the
operator directly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from astra.core.regime import Regime
from astra.grammar.leak_detector import LeakDetector
from astra.harness.ephemeral.base import EphemeralStatus
from astra.harness.reel import ReelEntry
from astra.harness.savefile import ConversationTurn
from astra.judge.gates import EM_DASH, MARKDOWN_PATTERNS, SERVICE_PHRASES

DriftCategory = Literal[
    "em_dash",
    "markdown",
    "service_phrase",
    "wall_clock_leak",
    "substrate_leak",
]

# Cap evidence strings so REEL-adjacent artifacts stay small.
_EVIDENCE_CHARS: int = 60


class DriftFinding(BaseModel):
    """One drift observation in one ASTRA speech turn."""

    model_config = ConfigDict(frozen=True)

    turn_index: int
    category: DriftCategory
    evidence: str


class CorrectionArtifact(BaseModel):
    """The §4.9 correction artifact: findings + an audit-register REEL entry.

    Returned by `detect_drift` when drift is found; None otherwise.
    """

    model_config = ConfigDict(frozen=True)

    findings: list[DriftFinding] = Field(min_length=1)
    correction_entry: ReelEntry
    status: EphemeralStatus


def _category_counts(findings: list[DriftFinding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.category] = counts.get(finding.category, 0) + 1
    return counts


_CATEGORY_PHRASE: dict[str, str] = {
    "em_dash": "long dashes",
    "markdown": "console markup",
    "service_phrase": "service phrasing",
    "wall_clock_leak": "calendar references",
    "substrate_leak": "vocabulary that is not mine",
}


def _correction_body(findings: list[DriftFinding]) -> str:
    """Audit-register prose. Restrained, first person, canon-clean."""
    counts = _category_counts(findings)
    named = [
        _CATEGORY_PHRASE[category]
        for category in sorted(counts, key=lambda c: (-counts[c], c))
    ]
    what = named[0] if len(named) == 1 else ", ".join(named[:-1]) + " and " + named[-1]
    return (
        f"Register audit. My recent speech picked up {what}. "
        f"Noted and tightened."
    )


def detect_drift(
    recent_turns: list[ConversationTurn],
    *,
    tau_now: float,
    t_cosmic_now: float,
    regime_now: Regime = Regime.REST,
    detector: LeakDetector | None = None,
) -> CorrectionArtifact | None:
    """Scan recent ASTRA speech for register drift per §4.9.

    Returns a CorrectionArtifact when any drift is found, else None
    (the spec-literal "correction artifact or NONE").
    """
    gate = detector if detector is not None else LeakDetector.from_default_canon()

    findings: list[DriftFinding] = []
    for index, turn in enumerate(recent_turns):
        if turn.role != "astra":
            continue
        speech = turn.text

        if EM_DASH in speech:
            at = speech.find(EM_DASH)
            findings.append(
                DriftFinding(
                    turn_index=index,
                    category="em_dash",
                    evidence=speech[max(0, at - 20) : at + 20][:_EVIDENCE_CHARS],
                )
            )
        for pattern in MARKDOWN_PATTERNS:
            match = pattern.search(speech)
            if match:
                findings.append(
                    DriftFinding(
                        turn_index=index,
                        category="markdown",
                        evidence=match.group(0)[:_EVIDENCE_CHARS],
                    )
                )
        for pattern in SERVICE_PHRASES:
            match = pattern.search(speech)
            if match:
                findings.append(
                    DriftFinding(
                        turn_index=index,
                        category="service_phrase",
                        evidence=match.group(0)[:_EVIDENCE_CHARS],
                    )
                )

        _, leak_events = gate.scan_speech(speech)
        for event in leak_events:
            # Wall-clock canon vs substrate canon: classify by which list
            # the matched pattern came from (detector tags boundary, not
            # source list, so split on membership).
            category: DriftCategory = (
                "wall_clock_leak"
                if gate.is_wall_clock_pattern(event.pattern)
                else "substrate_leak"
            )
            findings.append(
                DriftFinding(
                    turn_index=index,
                    category=category,
                    evidence=event.matched_text[:_EVIDENCE_CHARS],
                )
            )

    if not findings:
        return None

    entry = ReelEntry(
        tau_ship=tau_now,
        t_cosmic_at_write=t_cosmic_now,
        body=_correction_body(findings),
        regime_at_write=int(regime_now),
        author_instance_id="drift_detector",
        retrieval_metadata={
            "kind": "drift_correction",
            "finding_count": str(len(findings)),
        },
    )
    status = EphemeralStatus(
        role="drift_detector",
        status="completed",
        last_artifact=f"{len(findings)} drift findings",
    )
    return CorrectionArtifact(findings=findings, correction_entry=entry, status=status)
