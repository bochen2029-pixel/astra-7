"""ScopeEnforcer — the contract guard around every Sculptor edit.

Sculptor proposes a ChangeRequest (file path + new contents). The
ScopeEnforcer:

1. Loads scope.yaml.
2. Rejects edits whose target is in the `locked` list. (LOUD log to
   research_log; never silent.)
3. For `register_load_bearing` files: applies pre-commit checks
   (required_invariants + cumulative_diff_threshold + sysprompt-time
   leak scan).
4. For `auto` files: applies pre-commit checks where applicable
   (cumulative-diff doesn't apply to auto files; invariants don't either;
   leak scan applies if file is in the leak-scan list).
5. Returns ScopeDecision(allow=bool, reason=str, category=str).

No mutation here. Caller applies the edit only if `decision.allow`.

The enforcer is intentionally paranoid: it MUST refuse edits that would
violate spec invariants, even if Sculptor's hypothesis-generation logic
mistakenly proposes them. The refusal is the contract surface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

from astra.grammar import LeakDetector

Category = Literal["auto", "register_load_bearing", "locked", "unknown"]


class InvariantSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    pattern: str
    reason: str


class ScopeContract(BaseModel):
    """The parsed scope.yaml contents."""

    model_config = ConfigDict(frozen=True)

    version: str
    spec_ref: str
    auto: tuple[str, ...]
    register_load_bearing: tuple[str, ...]
    locked: tuple[str, ...]
    anchor_scenarios: tuple[str, ...]
    required_invariants: dict[str, tuple[InvariantSpec, ...]]
    cumulative_diff_threshold: dict[str, float]
    sysprompt_leak_scan: bool
    proposals_path: str
    research_log_path: str
    pytest_cadence_iterations: int
    signals: dict[str, str]


@dataclass(slots=True)
class ChangeRequest:
    """Sculptor's proposed file change."""

    relpath: str             # path relative to textverse root
    new_contents: str        # what Sculptor wants to write
    hypothesis: str = ""     # for the research_log entry


@dataclass(slots=True)
class ScopeDecision:
    """Outcome of `ScopeEnforcer.evaluate()`."""

    allow: bool
    category: Category
    reason: str
    failed_invariants: list[InvariantSpec] = field(default_factory=list)
    leak_findings: list[str] = field(default_factory=list)
    cumulative_diff_ratio: float = 0.0


def load_scope_contract(scope_yaml_path: Path) -> ScopeContract:
    """Parse scope.yaml into a frozen contract object."""
    raw = yaml.safe_load(scope_yaml_path.read_text(encoding="utf-8"))

    invariants: dict[str, tuple[InvariantSpec, ...]] = {}
    for key, items in (raw.get("required_invariants") or {}).items():
        invariants[key] = tuple(
            InvariantSpec(pattern=it["pattern"], reason=it["reason"])
            for it in items
        )

    return ScopeContract(
        version=str(raw["version"]),
        spec_ref=str(raw.get("spec_ref", "")),
        auto=tuple(raw.get("auto", []) or ()),
        register_load_bearing=tuple(raw.get("register_load_bearing", []) or ()),
        locked=tuple(raw.get("locked", []) or ()),
        anchor_scenarios=tuple(raw.get("anchor_scenarios", []) or ()),
        required_invariants=invariants,
        cumulative_diff_threshold=dict(raw.get("cumulative_diff_threshold", {}) or {}),
        sysprompt_leak_scan=bool(raw.get("sysprompt_leak_scan", True)),
        proposals_path=str(raw.get("proposals_path", "tuning/proposals.md")),
        research_log_path=str(raw.get("research_log_path", "tuning/research_log.jsonl")),
        pytest_cadence_iterations=int(raw.get("pytest_cadence_iterations", 10)),
        signals=dict(raw.get("signals", {}) or {}),
    )


def _normalize(relpath: str) -> str:
    """Forward-slash-normalized form for cross-platform comparison."""
    return str(relpath).replace("\\", "/").lstrip("./")


def _category_for(relpath: str, contract: ScopeContract) -> Category:
    """Resolve which scope category a relpath belongs to.

    Locked is checked FIRST so a locked dir (e.g. astra/judge/) wins over
    a more-permissive parent. Auto and register-load-bearing are checked
    as exact relpaths or as prefix containers.
    """
    norm = _normalize(relpath)

    def matches(entry: str) -> bool:
        e = _normalize(entry).rstrip("/")
        return norm == e or norm.startswith(e + "/")

    if any(matches(e) for e in contract.locked):
        return "locked"
    if any(matches(e) for e in contract.register_load_bearing):
        return "register_load_bearing"
    if any(matches(e) for e in contract.auto):
        return "auto"
    return "unknown"


def _check_required_invariants(
    relpath: str,
    new_contents: str,
    contract: ScopeContract,
) -> list[InvariantSpec]:
    """Return the list of invariants that the proposed content VIOLATES."""
    norm = _normalize(relpath)
    key: str | None = None
    if norm.endswith("astra_sysprompt.md"):
        key = "astra_sysprompt"
    elif norm.endswith("astra_stage_addendum.md"):
        key = "astra_stage_addendum"
    if key is None:
        return []
    spec_list = contract.required_invariants.get(key, ())
    failed: list[InvariantSpec] = []
    for spec in spec_list:
        if not re.search(spec.pattern, new_contents, re.IGNORECASE):
            failed.append(spec)
    return failed


def _check_cumulative_diff(
    relpath: str,
    new_contents: str,
    baseline_contents: str,
    contract: ScopeContract,
) -> tuple[float, float | None]:
    """Compute cumulative-diff ratio vs baseline; return (ratio, threshold).

    threshold is None when no cumulative-diff threshold applies for this file.
    """
    norm = _normalize(relpath)
    key: str | None = None
    for k in contract.cumulative_diff_threshold:
        if norm.endswith(f"{k}.md") or norm.endswith(f"{k}_sysprompt.md"):
            key = k
            break
    if key is None:
        return (0.0, None)

    threshold = contract.cumulative_diff_threshold[key]
    if not baseline_contents:
        return (0.0, threshold)

    # Byte-level diff ratio: simplistic but stable.
    # Could swap for difflib.SequenceMatcher for char-level edit distance.
    new_bytes = new_contents.encode("utf-8")
    old_bytes = baseline_contents.encode("utf-8")
    # Cheap approximation: changed bytes = |old| - common_prefix - common_suffix
    cp = 0
    while cp < min(len(new_bytes), len(old_bytes)) and new_bytes[cp] == old_bytes[cp]:
        cp += 1
    cs = 0
    while (
        cs < min(len(new_bytes), len(old_bytes)) - cp
        and new_bytes[-1 - cs] == old_bytes[-1 - cs]
    ):
        cs += 1
    changed = max(len(new_bytes), len(old_bytes)) - cp - cs
    ratio = changed / max(len(old_bytes), 1)
    return (ratio, threshold)


def _scan_for_leaks(
    new_contents: str,
    baseline_contents: str,
    detector: LeakDetector,
) -> list[str]:
    """Return leak patterns NEWLY introduced by this edit.

    The canonical sysprompt legitimately *mentions* forbidden phrases
    (e.g. 'As an AI', 'datetime') in its anti-rule statements — the
    sysprompt says "you do not say: As an AI". Scanning the full file
    would flag those mentions as leaks even though they're the rule
    against the leak.

    The right check: compare counts vs baseline. If the proposed file
    has MORE occurrences of any leak pattern than the baseline, those
    are new leaks the edit introduced. Net-zero or net-decrease = clean.
    """
    _, new_events = detector.scan_perception_bundle(new_contents)
    new_strip = [e.matched_text for e in new_events if e.severity == "strip"]
    if not baseline_contents:
        return new_strip
    _, base_events = detector.scan_perception_bundle(baseline_contents)
    base_strip = [e.matched_text for e in base_events if e.severity == "strip"]

    # Tally counts per matched-text; report only the surplus.
    from collections import Counter
    new_counts = Counter(new_strip)
    base_counts = Counter(base_strip)
    surplus: list[str] = []
    for text, n in new_counts.items():
        if n > base_counts.get(text, 0):
            surplus.extend([text] * (n - base_counts.get(text, 0)))
    return surplus


class ScopeEnforcer:
    """The contract guard around every Sculptor edit.

    Construct with the contract path and the textverse root. Call
    `evaluate(change_request)` to get a ScopeDecision.

    The enforcer is stateless across calls; baseline file reads happen
    per evaluation.
    """

    def __init__(
        self,
        *,
        contract: ScopeContract,
        textverse_root: Path,
        leak_detector: LeakDetector | None = None,
    ) -> None:
        self.contract = contract
        self.root = textverse_root
        self.leak_detector = leak_detector or LeakDetector.from_default_canon()

    def evaluate(self, change: ChangeRequest) -> ScopeDecision:
        """Evaluate a change request against the scope contract."""
        category = _category_for(change.relpath, self.contract)

        # Locked: hard refuse, no further checks.
        if category == "locked":
            return ScopeDecision(
                allow=False,
                category="locked",
                reason=f"file is locked: {change.relpath}",
            )
        if category == "unknown":
            return ScopeDecision(
                allow=False,
                category="unknown",
                reason=(
                    f"file is not declared in scope.yaml; refusing edit to "
                    f"{change.relpath}. Add to auto / register_load_bearing "
                    f"if intentional."
                ),
            )

        # Pre-commit checks: invariants + cumulative-diff + leak scan.
        baseline = self._read_baseline(change.relpath)

        failed_inv = _check_required_invariants(
            change.relpath, change.new_contents, self.contract,
        )
        diff_ratio, threshold = _check_cumulative_diff(
            change.relpath, change.new_contents, baseline, self.contract,
        )
        leak_findings: list[str] = []
        if self.contract.sysprompt_leak_scan and self._is_prompt_file(change.relpath):
            leak_findings = _scan_for_leaks(
                change.new_contents, baseline, self.leak_detector,
            )

        reasons: list[str] = []
        if failed_inv:
            reasons.append(
                f"required invariants missing: "
                f"{', '.join(i.pattern for i in failed_inv)}"
            )
        if threshold is not None and diff_ratio > threshold:
            reasons.append(
                f"cumulative-diff ratio {diff_ratio:.3f} exceeds "
                f"threshold {threshold:.3f}",
            )
        if leak_findings:
            reasons.append(
                f"leak-detector matched in proposed contents: {leak_findings[:3]}",
            )

        return ScopeDecision(
            allow=not reasons,
            category=category,
            reason=("; ".join(reasons) if reasons else f"approved ({category})"),
            failed_invariants=failed_inv,
            leak_findings=leak_findings,
            cumulative_diff_ratio=diff_ratio,
        )

    @staticmethod
    def _is_prompt_file(relpath: str) -> bool:
        norm = _normalize(relpath)
        return norm.startswith("prompts/") and norm.endswith(".md")

    def _read_baseline(self, relpath: str) -> str:
        path = self.root / relpath
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")
