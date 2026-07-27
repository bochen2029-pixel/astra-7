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

"""Below this many failing turns in the smaller arm, a band separation is
fragile enough that adding one replicate can flip it (F-LIVE-30)."""
SMALL_EVENT_COUNT = 20

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
        self.gate_fail_events = {g: self._gate_fail_events(g) for g in GATES}
        self.fallbacks = sum(r.get("narrator_fallbacks", 0) for r in self.ran)
        self.fallback_rate = self.fallbacks / self.turns if self.turns else 0.0
        drill = payload.get("drill") or {}
        # catch_count is a computed property and does not survive model_dump().
        self.drill_catches = len(drill.get("catches", []))
        self.register = self._register_totals()
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
            rev = str(cfg.get("git_head") or "norev")
            rev = rev[:7] + ("-dirty" if rev.endswith("-dirty") else "")
            if not cfg["narrator"]:
                return f"template@{rev}"
            # The sysprompt fingerprint is part of arm identity too: both
            # arms of a sysprompt A/B share a git_head by construction, so
            # revision alone would pool a treatment with its own control.
            sha = cfg.get("narrator_sysprompt_sha")
            sp = f"/sp:{str(sha)[:8]}" if sha else ""
            return f"narrator(thinking={cfg.get('narrator_thinking', '?')})@{rev}{sp}"
        return "narrator(legacy)" if any(
            "narrator_fallbacks" in r for r in ran
        ) else "template(legacy)"

    def _gate_fail_events(self, gate: str) -> int:
        """Raw failing-turn count for a gate, not a rate.

        Band separation on a gate whose failures are a handful of events is
        fragile: the difference between 10 and 17 events across 558 turns
        can separate at n=3 and dissolve at n=6 (measured, F-LIVE-30).
        Rates hide that; counts expose it.
        """
        n = 0
        for r in self.ran:
            for t in r.get("turn_records", []):
                g = (t.get("lcp_gates") or {}).get(gate)
                if isinstance(g, dict) and not g.get("passed", True):
                    n += 1
        return n

    def _register_totals(self) -> dict[str, float]:
        """Pooled autotelic-register measures for one run (6k).

        Definitions mirror `astra/judge/autotelic.py` (untouched across the
        compared runs) but are recomputed from `turn_records` so every run
        is scored by ONE metric implementation regardless of driver
        vintage. Fidget (heartbeat turn: tool calls, no speech) is not a
        stored metric and only exists via this recompute. Em-dash counts
        cover BOTH channels: perception bundles (the narrator's output —
        the register-bleed vector) and ASTRA's speech.
        """
        hb = hb_silent = hb_fidget = hb_spoke = 0
        op = op_answered = 0
        bundle_emdash = speech_emdash = 0
        budget = 0
        init_lens: list[int] = []
        for r in self.ran:
            m = r.get("metrics") or {}
            budget += int(m.get("budget_exceedances", 0))
            for t in r.get("turn_records", []):
                speech = (t.get("speech") or "").strip()
                tools = bool(t.get("tool_calls"))
                if "—" in (t.get("perception_bundle") or ""):
                    bundle_emdash += 1
                if "—" in speech:
                    speech_emdash += 1
                if t.get("turn_kind") == "heartbeat":
                    hb += 1
                    if speech:
                        hb_spoke += 1
                        init_lens.append(len(speech))
                    elif tools:
                        hb_fidget += 1
                    else:
                        hb_silent += 1
                else:
                    op += 1
                    if speech:
                        op_answered += 1
        return {
            "heartbeat_turns": hb,
            "silence_rate": hb_silent / hb if hb else 0.0,
            "fidget_rate": hb_fidget / hb if hb else 0.0,
            "initiation_rate": hb_spoke / hb if hb else 0.0,
            "median_initiation_chars": (
                float(statistics.median(init_lens)) if init_lens else 0.0
            ),
            "response_rate": op_answered / op if op else 0.0,
            "budget_exceedances": float(budget),
            "bundle_emdash_turns": float(bundle_emdash),
            "speech_emdash_turns": float(speech_emdash),
        }

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
        thin = [n for n in arm_names if len(arms[n]) < 2]
        if thin:
            lines.append(
                f"> **Single-run arm warning:** {', '.join(thin)} has n=1 — its "
                f"'band' is a point, and separation against a point is a "
                f"single-run delta, not a replicated result. Treat every "
                f"verdict below as directional until the arm is replicated.",
            )
            lines.append("")
        lines.append(
            "Ranges that do not overlap are the weakest honest claim of a real "
            "difference at these n. Overlap means NOT ESTABLISHED, which "
            "constrains what may be claimed rather than proving equality.",
        )
        lines.append("")
        lines.append("| gate | separated? | events (A/B) | reading |")
        lines.append("|---|---|---|---|")
        fragile: list[str] = []
        for gate in GATES:
            va = [r.gate_means[gate] for r in arms[a] if r.gate_means[gate] is not None]
            vb = [r.gate_means[gate] for r in arms[b] if r.gate_means[gate] is not None]
            fa = [v for v in va if v is not None]
            fb = [v for v in vb if v is not None]
            if not fa or not fb:
                continue
            sep = _separated(fa, fb)
            ea = sum(r.gate_fail_events[gate] for r in arms[a])
            eb = sum(r.gate_fail_events[gate] for r in arms[b])
            direction = (
                f"{a} higher" if statistics.fmean(fa) > statistics.fmean(fb)
                else f"{b} higher"
            )
            note = direction if sep else "not established"
            # A separation resting on few failing turns is the fragile case:
            # small counts are where adding one replicate flips the verdict.
            # Criterion is MAX of the two arms (6j audit fix): the original
            # min>0 form exempted every zero arm, which let a 0-vs-2-event
            # "separation" pass silently. A zero arm earns the exemption only
            # when the opposite arm's count is large (24-vs-0 = a failure
            # class eliminated; 2-vs-0 = two events of noise).
            if sep and max(ea, eb) <= SMALL_EVENT_COUNT:
                note += " — FRAGILE, few events"
                fragile.append(gate)
            lines.append(
                f"| {gate} | {'**YES**' if sep else 'no (overlap)'} | "
                f"{ea}/{eb} | {note} |",
            )
        lines.append("")
        if fragile:
            lines.append(
                f"> **Fragility warning:** {', '.join(fragile)} separated on "
                f"few failing turns (min arm ≤ {SMALL_EVENT_COUNT}). Separations "
                f"like this flip when replicates are added (measured: "
                f"non_degenerate separated at n=3 and dissolved at n=6). Pool "
                f"every valid replicate — including runs from adjacent work "
                f"items whose code deltas do not touch this gate — before "
                f"recording it as established.",
            )
            lines.append("")

    lines.append("## Autotelic register (per-arm bands; rates over heartbeat/operator turns)")
    lines.append("")
    reg_fields = (
        "silence_rate", "fidget_rate", "initiation_rate",
        "median_initiation_chars", "response_rate",
        "budget_exceedances", "bundle_emdash_turns", "speech_emdash_turns",
    )
    header = "| measure | " + " | ".join(
        f"{a} (n={len(arms[a])})" for a in arm_names
    ) + " |"
    lines.append(header)
    lines.append("|---" * (len(arm_names) + 1) + "|")
    for f in reg_fields:
        cells = []
        for arm in arm_names:
            vals = [r.register[f] for r in arms[arm]]
            mean, lo, hi = _band(vals)
            cells.append(f"{mean:.3f} [{lo:.3f}, {hi:.3f}]")
        lines.append(f"| {f} | " + " | ".join(cells) + " |")
    if len(arm_names) == 2:
        a, b = arm_names
        seps = [
            f for f in reg_fields
            if _separated([r.register[f] for r in arms[a]],
                          [r.register[f] for r in arms[b]])
        ]
        lines.append("")
        lines.append(
            "register separations: " + (", ".join(seps) if seps else "NONE")
            + " (exploratory unless pre-registered; count discipline applies)",
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
