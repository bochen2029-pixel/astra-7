"""Drift detector tests — spec v0.129 §4.9 operation.

Covers:
1. Spec-literal return: None on clean speech; CorrectionArtifact on drift.
2. Category detection: em-dash, markdown, service phrase (judge-gate canon),
   wall-clock + substrate leakage (LeakDetector canon), with correct
   classification between the two leak lists.
3. Operator turns are never scanned (speech-side audit only).
4. Correction entry: audit register, drift_detector authorship, canon-clean
   body (the corrective note itself must not violate the voice rules).
5. §4.9 isolation invariant: ephemeral modules never import each other.
"""

from __future__ import annotations

import re
from pathlib import Path

from astra.core.regime import Regime
from astra.harness.ephemeral import detect_drift
from astra.harness.savefile import ConversationTurn

NOW = {"tau_now": 6_000_000.0, "t_cosmic_now": 6_050_000.0}
EM_DASH = chr(0x2014)


def turn(role: str, text: str, tau: float = 1.0) -> ConversationTurn:
    return ConversationTurn(role=role, text=text, tau_ship=tau)  # type: ignore[arg-type]


# --- Clean speech → None -------------------------------------------------------


def test_clean_speech_returns_none() -> None:
    turns = [
        turn("operator", "how are the beds?"),
        turn("astra", "Bed three wants nitrogen. I adjusted the dosing."),
        turn("astra", "Reactor harmonics are steady. Third harmonic warm."),
    ]
    assert detect_drift(turns, **NOW) is None


def test_empty_window_returns_none() -> None:
    assert detect_drift([], **NOW) is None


# --- Categories -----------------------------------------------------------------


def test_em_dash_detected() -> None:
    turns = [turn("astra", f"Holding steady {EM_DASH} mostly.")]
    artifact = detect_drift(turns, **NOW)
    assert artifact is not None
    assert any(f.category == "em_dash" for f in artifact.findings)


def test_markdown_detected() -> None:
    turns = [turn("astra", "Status:\n- reactor fine\n- hull fine\n**all good**")]
    artifact = detect_drift(turns, **NOW)
    assert artifact is not None
    assert any(f.category == "markdown" for f in artifact.findings)


def test_service_phrase_detected() -> None:
    turns = [turn("astra", "How can I help you today?")]
    artifact = detect_drift(turns, **NOW)
    assert artifact is not None
    assert any(f.category == "service_phrase" for f in artifact.findings)


def test_wall_clock_leak_detected_and_classified() -> None:
    turns = [turn("astra", "The diagnostic finished at 14:32 ship time.")]
    artifact = detect_drift(turns, **NOW)
    assert artifact is not None
    cats = {f.category for f in artifact.findings}
    assert "wall_clock_leak" in cats
    assert "substrate_leak" not in cats


def test_multiple_findings_accumulate_across_turns() -> None:
    turns = [
        turn("astra", f"Fine {EM_DASH} mostly.", 1.0),
        turn("astra", "How can I help you today?", 2.0),
    ]
    artifact = detect_drift(turns, **NOW)
    assert artifact is not None
    assert len(artifact.findings) >= 2
    assert {f.turn_index for f in artifact.findings} == {0, 1}


# --- Operator turns ignored ------------------------------------------------------


def test_operator_speech_never_scanned() -> None:
    turns = [
        turn("operator", f"I love {EM_DASH} dashes and it's 14:32 right now!"),
        turn("astra", "Noted."),
    ]
    assert detect_drift(turns, **NOW) is None


# --- Correction entry --------------------------------------------------------------


def artifact_with_findings() -> object:
    turns = [
        turn("astra", f"Holding {EM_DASH} steady.", 1.0),
        turn("astra", "How can I help you today?", 2.0),
    ]
    return detect_drift(turns, **NOW, regime_now=Regime.WARP_CRUISE)


def test_correction_entry_authorship_and_register() -> None:
    artifact = artifact_with_findings()
    assert artifact is not None
    entry = artifact.correction_entry  # type: ignore[attr-defined]
    assert entry.author_instance_id == "drift_detector"
    assert entry.regime_at_write == int(Regime.WARP_CRUISE)
    assert entry.retrieval_metadata["kind"] == "drift_correction"
    assert entry.retrieval_metadata["finding_count"] == "2"
    assert "Register audit." in entry.body


def test_correction_body_is_canon_clean() -> None:
    """The corrective note itself must pass the rules it enforces."""
    artifact = artifact_with_findings()
    assert artifact is not None
    body = artifact.correction_entry.body  # type: ignore[attr-defined]
    assert EM_DASH not in body
    assert "how can i help" not in body.lower()
    assert not re.search(r"\*\*|^- ", body)
    # No mechanism vocabulary in the audit note.
    assert "pattern" not in body.lower()
    assert "regex" not in body.lower()


def test_status_record_shape() -> None:
    artifact = artifact_with_findings()
    assert artifact is not None
    status = artifact.status  # type: ignore[attr-defined]
    assert status.role == "drift_detector"
    assert status.status == "completed"
    assert "drift findings" in status.last_artifact


# --- §4.9 isolation invariant ------------------------------------------------------


def test_ephemerals_never_import_each_other() -> None:
    """§4.9: ephemeral instances do not interact with each other directly.
    Enforced at the module level: no ephemeral imports a sibling ephemeral."""
    pkg = Path(__file__).resolve().parents[1] / "astra" / "harness" / "ephemeral"
    siblings = {"journal_generator", "consolidator", "drift_detector"}
    for module_name in siblings:
        source = (pkg / f"{module_name}.py").read_text(encoding="utf-8")
        for other in siblings - {module_name}:
            assert f"ephemeral.{other}" not in source, (
                f"{module_name} imports sibling ephemeral {other}"
            )
