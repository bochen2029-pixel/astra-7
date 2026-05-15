"""Leak detector per spec v0.128 §5.7 + §4.3 Master Contract invariants.

Two-boundary defense-in-depth: scan perception bundles BEFORE delivery to
ASTRA-LLM, and scan speech output BEFORE delivery to operator/TTS. Also
scans journal output (cryosleep generator) before commit to REEL.

The detector loads pattern lists from the canonical text files shipped with
the package (`astra/grammar/canon/wall_clock_patterns.txt` and
`astra_substrate_patterns.txt`). Tests can also construct a detector with
inline patterns to verify specific scenarios.

Per spec §5.7 the detector NEVER raises. It returns:
- cleaned_text: input with all "strip"-severity matches removed
- events: list of `LeakEvent` describing every match (strip or warn severity)

The orchestrator (Day 5) logs events to the per-turn transcript regardless
of severity. Drift detector (ephemeral instance, Day N+) uses event rate to
trigger downstream audits.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

Boundary = Literal["perception", "speech", "journal"]
Severity = Literal["strip", "warn"]


class LeakPattern(BaseModel):
    """One canonical pattern."""

    model_config = ConfigDict(frozen=True)

    raw: str                            # the regex source
    severity: Severity = "strip"
    label: str = ""                      # optional human-readable name


class LeakEvent(BaseModel):
    """One match event from a scan. Recorded regardless of severity."""

    model_config = ConfigDict(frozen=True)

    pattern: str
    matched_text: str
    span: tuple[int, int]
    boundary: Boundary
    severity: Severity


def _load_patterns_file(path: Path) -> list[LeakPattern]:
    """Parse a canon pattern file.

    Format:
        # comment
        <regex>
        <regex> | warn        # explicit severity override

    Returns empty list when file is missing (caller decides if that's fatal).
    """
    if not path.is_file():
        return []
    patterns: list[LeakPattern] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        severity: Severity = "strip"
        raw = stripped
        if " | " in stripped:
            raw, sev_str = stripped.rsplit(" | ", 1)
            raw = raw.strip()
            sev_str = sev_str.strip()
            if sev_str == "warn":
                severity = "warn"
        patterns.append(LeakPattern(raw=raw, severity=severity, label=raw[:60]))
    return patterns


def _default_canon_dir() -> Path:
    """Path to the package's canon/ directory."""
    return Path(__file__).resolve().parent / "canon"


class LeakDetector:
    """Boundary-aware leak detector. Scans + cleans + logs."""

    def __init__(
        self,
        wall_clock_patterns: list[LeakPattern] | None = None,
        substrate_patterns: list[LeakPattern] | None = None,
    ) -> None:
        wc = wall_clock_patterns or []
        sub = substrate_patterns or []
        self._wall_clock = [self._compile(p) for p in wc]
        self._substrate = [self._compile(p) for p in sub]

    @staticmethod
    def _compile(p: LeakPattern) -> tuple[re.Pattern[str], Severity, str]:
        return (re.compile(p.raw, re.IGNORECASE), p.severity, p.raw)

    @classmethod
    def from_default_canon(cls) -> LeakDetector:
        """Load patterns from the package's canon/ directory."""
        return cls.from_canon_dir(_default_canon_dir())

    @classmethod
    def from_canon_dir(cls, root: Path) -> LeakDetector:
        """Load patterns from a custom directory (used by tests for fixtures)."""
        wc = _load_patterns_file(root / "wall_clock_patterns.txt")
        sub = _load_patterns_file(root / "astra_substrate_patterns.txt")
        return cls(wall_clock_patterns=wc, substrate_patterns=sub)

    @property
    def wall_clock_count(self) -> int:
        return len(self._wall_clock)

    @property
    def substrate_count(self) -> int:
        return len(self._substrate)

    def scan_perception_bundle(self, text: str) -> tuple[str, list[LeakEvent]]:
        """Scan perception bundle before delivery to ASTRA-LLM.

        Both wall-clock and substrate patterns enforced — neither must reach
        ASTRA's input.
        """
        return self._scan(text, boundary="perception", use_wc=True, use_sub=True)

    def scan_speech(self, text: str) -> tuple[str, list[LeakEvent]]:
        """Scan operator-facing speech before delivery to TTS.

        Both wall-clock and substrate patterns enforced.
        """
        return self._scan(text, boundary="speech", use_wc=True, use_sub=True)

    def scan_journal_output(self, text: str) -> tuple[str, list[LeakEvent]]:
        """Scan cryosleep journal output before commit to REEL.

        Per spec §3.9 + §5.7: journals reference cosmic-time landmarks; absolute-
        date references, metabolic-clock leaks, Earth-calendar idioms are not
        allowed. Substrate patterns are not enforced for journals because the
        journal generator emits in ASTRA's voice and the substrate-vocabulary
        scan happens upstream.
        """
        return self._scan(text, boundary="journal", use_wc=True, use_sub=False)

    def _scan(
        self,
        text: str,
        *,
        boundary: Boundary,
        use_wc: bool,
        use_sub: bool,
    ) -> tuple[str, list[LeakEvent]]:
        patterns: list[tuple[re.Pattern[str], Severity, str]] = []
        if use_wc:
            patterns.extend(self._wall_clock)
        if use_sub:
            patterns.extend(self._substrate)

        events: list[LeakEvent] = [
            LeakEvent(
                pattern=raw_pattern,
                matched_text=match.group(0),
                span=match.span(),
                boundary=boundary,
                severity=severity,
            )
            for regex, severity, raw_pattern in patterns
            for match in regex.finditer(text)
        ]

        cleaned = text
        for regex, severity, _ in patterns:
            if severity == "strip":
                cleaned = regex.sub("", cleaned)
        # Collapse runs of whitespace introduced by removals
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+\n", "\n", cleaned)

        return cleaned, events


class CompiledLeakDetector(BaseModel):
    """Frozen, JSON-serializable view of detector configuration for transcripts."""

    model_config = ConfigDict(frozen=True)

    wall_clock_pattern_count: int
    substrate_pattern_count: int
    canon_dir: str = ""

    @classmethod
    def describe(cls, detector: LeakDetector, canon_dir: Path | None = None) -> CompiledLeakDetector:
        return cls(
            wall_clock_pattern_count=detector.wall_clock_count,
            substrate_pattern_count=detector.substrate_count,
            canon_dir=str(canon_dir) if canon_dir is not None else "",
        )


__all__ = [
    "Boundary",
    "CompiledLeakDetector",
    "LeakDetector",
    "LeakEvent",
    "LeakPattern",
    "Severity",
]
