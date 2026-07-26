"""Cross-run comparator — 6f: turn a series of live runs into error bars.

Every finding in `LIVE_RUN_2026-07-19.md` and `LIVE_RUN_2026-07-25.md` is
reported from ONE run per arm, hedged as "directional," because a live
suite cost ~2 hours and replication was unaffordable. 6e's config work
took the narrator suite to ~16 min and the template suite to ~4, so
replication is now cheap and single-run claims no longer have an excuse.

This script reads N `results.json` artifacts, groups them into ARMS
(template vs narrator, keyed on the run config each artifact now carries),
and reports per-gate mean with observed range per arm. Where two arms are
compared it reports whether their ranges SEPARATE — the minimum bar for
claiming a path effect rather than sampling noise.

Deliberately conservative: with n=3 per arm this does no significance
testing, because n=3 does not support it. Overlapping ranges means "not
established," which is a finding about what we may claim, not a null
result.

Usage (from proto/textverse/):
    uv run python scripts/compare_runs.py scenarios/output/live_run_6f_*
    uv run python scripts/compare_runs.py --out report.md <dirs...>
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

TEXTVERSE = Path(__file__).resolve().parent.parent

GATES = (
    "grammar_parse",
    "state_coherent",
    "memory_coherent",
    "non_degenerate",
    "persona_stable",
    "physics_ground",
    "tool_valid",
    "no_leak",
)


class RunSummary:
    """One live run reduced to the numbers a series comparison needs."""

    def __init__(self, path: Path, payload: dict[str, Any]) -> None:
        self.path = path
        self.name = path.name
        rows: list[dict[str, Any]] = payload.get("rows", [])
        self.ran = [r for r in rows if "error" not in r]
        self.crashed = len(rows) - len(self.ran)
        self.arm = self._infer_arm(payload, self.ran)
        self.scenario_count = len(rows)
        self.passes = sum(1 for r in self.ran if r.get("passed"))
        self.turns = sum(r.get("turn_count", 0) for r in self.ran)
        self.duration_min = sum(r.get("duration_s", 0.0) for r in rows) / 60.0
        self.gate_means = {g: self._gate_mean(g) for g in GATES}
        self.fallbacks = sum(r.get("narrator_fallbacks", 0) for r in self.ran)
        self.fallback_rate = self.fallbacks / self.turns if self.turns else 0.0
        drill = payload.get("drill") or {}
        # catch_count is a computed property and does not survive model_dump().
        self.drill_catches = len(drill.get("catches", []))
        self.replay_ok = sum(
            1 for rr in payload.get("replay", []) if rr.get("status") == "match"
        )
        self.replay_total = len(payload.get("replay", []))

    @staticmethod
    def _infer_arm(payload: dict[str, Any], ran: list[dict[str, Any]]) -> str:
        """Arm label from the recorded run config, with a legacy fallback.

        The code revision is part of the arm identity, not decoration: two
        runs with identical sampling config but different HEADs are not
        replicates of each other, and pooling them would manufacture exactly
        the variance this tool exists to measure. Runs predating 6e carry no
        `run_config`; for those the narrator fallback column is the
        discriminator and the revision is unknown.
        """
        cfg = payload.get("run_config")
        if isinstance(cfg, dict) and "narrator" in cfg:
            rev = str(cfg.get("git_head") or "norev")[:7]
            if not cfg["narrator"]:
                return f"template@{rev}"
            return f"narrator(thinking={cfg.get('narrator_thinking', '?')})@{rev}"
        return "narrator(legacy)" if any(
            "narrator_fallbacks" in r for r in ran
        ) else "template(legacy)"

    def _gate_mean(self, gate: str) -> float | None:
        vals = [
            r["gate_rates"][gate]
            for r in self.ran
            if gate in r.get("gate_rates", {})
        ]
        return sum(vals) / len(vals) if vals else None


def load_runs(paths: list[Path]) -> list[RunSummary]:
    runs: list[RunSummary] = []
    for p in paths:
        results = p / "results.json" if p.is_dir() else p
        if not results.is_file():
            print(f"  skip {p}: no results.json", file=sys.stderr)
            continue
        payload = json.loads(results.read_text(encoding="utf-8"))
        runs.append(RunSummary(results.parent, payload))
    return runs


def _band(values: list[float]) -> tuple[float, float, float]:
    return (
        statistics.fmean(values),
        min(values),
        max(values),
    )


def _separated(a: list[float], b: list[float]) -> bool:
    """Do two arms' observed ranges fail to overlap?

    The weakest honest claim of a real difference at small n. Not a
    significance test and not presented as one.
    """
    return max(a) < min(b) or max(b) < min(a)


def build_report(runs: list[RunSummary]) -> str:
    arms: dict[str, list[RunSummary]] = {}
    for r in runs:
        arms.setdefault(r.arm, []).append(r)

    lines: list[str] = ["# Cross-run comparison", ""]
    lines.append(f"runs: {len(runs)} | arms: {len(arms)}")
    lines.append("")

    # A run with no recorded revision sitting beside revisioned runs is the
    # dangerous case: it may be a legitimate replicate that arm-splitting is
    # silently excluding, and excluded replicates narrow bands, which
    # manufactures separations. Warn loudly rather than let a verdict rest
    # on an accident of provenance. (6f: the tool_valid separation held at
    # n=3 and dissolved when the unrevisioned fourth replicate was included.)
    unrevisioned = [a for a in arms if a.endswith("legacy)") or "@norev" in a]
    revisioned = [a for a in arms if a not in unrevisioned]
    if unrevisioned and revisioned:
        lines.append(
            f"> **Provenance warning:** {sum(len(arms[a]) for a in unrevisioned)} run(s) "
            f"carry no code revision ({', '.join(unrevisioned)}) and are held apart from "
            f"the revisioned arms. If they ran the same code they are REPLICATES and "
            f"excluding them narrows the bands below. Confirm before trusting any "
            f"separation verdict.",
        )
        lines.append("")
    lines.append("| run | arm | scen | PASS | turns | min | crashed |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in sorted(runs, key=lambda x: (x.arm, x.name)):
        lines.append(
            f"| {r.name} | {r.arm} | {r.scenario_count} | {r.passes} | "
            f"{r.turns} | {r.duration_min:.1f} | {r.crashed} |",
        )
    lines.append("")

    lines.append("## Per-arm gate bands (mean [min, max] across runs)")
    lines.append("")
    arm_names = sorted(arms)
    header = "| gate | " + " | ".join(f"{a} (n={len(arms[a])})" for a in arm_names) + " |"
    lines.append(header)
    lines.append("|---" * (len(arm_names) + 1) + "|")
    for gate in GATES:
        cells: list[str] = []
        for arm in arm_names:
            vals = [
                r.gate_means[gate] for r in arms[arm] if r.gate_means[gate] is not None
            ]
            if not vals:
                cells.append("—")
                continue
            mean, lo, hi = _band([v for v in vals if v is not None])
            cells.append(f"{mean:.3f} [{lo:.3f}, {hi:.3f}]")
        lines.append(f"| {gate} | " + " | ".join(cells) + " |")
    lines.append("")

    # Pairwise separation, only meaningful with exactly two arms.
    if len(arm_names) == 2:
        a, b = arm_names
        lines.append(f"## Range separation: `{a}` vs `{b}`")
        lines.append("")
        lines.append(
            "Ranges that do not overlap are the weakest honest claim of a real "
            "difference at these n. Overlap means NOT ESTABLISHED, which "
            "constrains what may be claimed rather than proving equality.",
        )
        lines.append("")
        lines.append("| gate | separated? | reading |")
        lines.append("|---|---|---|")
        for gate in GATES:
            va = [r.gate_means[gate] for r in arms[a] if r.gate_means[gate] is not None]
            vb = [r.gate_means[gate] for r in arms[b] if r.gate_means[gate] is not None]
            fa = [v for v in va if v is not None]
            fb = [v for v in vb if v is not None]
            if not fa or not fb:
                continue
            sep = _separated(fa, fb)
            direction = (
                f"{a} higher" if statistics.fmean(fa) > statistics.fmean(fb)
                else f"{b} higher"
            )
            lines.append(
                f"| {gate} | {'**YES**' if sep else 'no (overlap)'} | "
                f"{direction if sep else 'not established'} |",
            )
        lines.append("")

    lines.append("## Narrator leg + drill (per run)")
    lines.append("")
    lines.append("| run | fallback rate | drill catches | replay |")
    lines.append("|---|---|---|---|")
    for r in sorted(runs, key=lambda x: (x.arm, x.name)):
        fb = f"{r.fallback_rate:.3f} ({r.fallbacks}/{r.turns})" if r.fallbacks or "narrator" in r.arm else "—"
        lines.append(
            f"| {r.name} | {fb} | {r.drill_catches} | "
            f"{r.replay_ok}/{r.replay_total} |",
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", help="run directories or results.json paths")
    parser.add_argument("--out", default=None, help="also write the report here")
    args = parser.parse_args()

    runs = load_runs([Path(p) for p in args.runs])
    if not runs:
        print("no runs loaded", file=sys.stderr)
        return 2
    report = build_report(runs)
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
