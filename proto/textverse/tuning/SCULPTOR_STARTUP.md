# SCULPTOR_STARTUP.md — fresh session orientation for Sculptor-C / D / E

**Read this file first. It is the directive for a fresh session picking up the Sculptor implementation after Phase 1 (textverse Days 1-7) and Sculptor-A + B have committed.**

Do not improvise alternative starting points.

---

## 0. What you are joining

You are joining the implementation track of **Sculptor v1** — the autonomous self-tuning pipeline sitting on top of the textverse closed-loop bench. The pipeline is the operator's mechanism for turning Claude into a research scientist whose lab is the bench. The deliverable is **durable knowledge** (a research log) plus an optimized bundle.

Spec envelope: `docs/spec-v0.128.md` §15.4 ("lock envelope, sculpt within bounds, revise only on adversarial-finding-justified loop measurement"). Sculptor IS the bounded sculpting agent.

---

## 1. Required reading (in this order, ~30 minutes)

| # | File | Why |
|---|------|-----|
| 1 | `proto/textverse/READY.md` | Phase 1 closure summary; what works today |
| 2 | `proto/textverse/tuning/scope.yaml` | The contract Sculptor edits within |
| 3 | `proto/textverse/tuning/judge_prompt.md` | The locked pro/anti judge rubric |
| 4 | `proto/textverse/tuning/weights.json` | Composite-score weights |
| 5 | `proto/textverse/astra/sculptor/__init__.py` | What Sculptor-A + B exported |
| 6 | This file (the rest of it) | What Sculptor-C / D / E must do |

**Do NOT load the brainstorm/ directory.** Research scratch with known-stale assumptions.

---

## 2. What Sculptor-A and Sculptor-B did

**Sculptor-A** (`ff01c90`):
- `tuning/` — scope.yaml (3 categories: auto / register_load_bearing / locked) + anchor_scenarios + required_invariants + cumulative_diff_threshold + sysprompt-leak-scan; budget.json (50M/200/48h with auto-extend); weights.json (composite formula coefficients); judge_prompt.md (locked dual-judge rubric); sampling.json (mutable); reel_retrieval_k.json (mutable); .gitignore (runtime artifacts).
- `astra/sculptor/config.py` — `ConfigSnapshot` (frozen Pydantic, content-hashed), `snapshot_from_disk`, JSON roundtrip.
- `astra/sculptor/scope.py` — `ScopeContract`, `ChangeRequest`, `ScopeDecision`, `ScopeEnforcer.evaluate()`. Locked refusals are loud. Pre-commit checks: required-invariant + cumulative-diff threshold + sysprompt-time leak scan (NET-NEW leaks only — pre-existing anti-rule mentions accepted).
- `astra/sculptor/research_log.py` — `ResearchEntry` (8 `Decision` types: `promote` / `revert` / `falsified` / `scope_refused` / `bench_regression` / `stuck` / `synthesis` / `operator_signal`); append-only JSONL writer; `latest_promote()`; findings.md + daily_report.md renderers; builder helpers per decision type.

**Sculptor-B** (`47235c4`):
- `astra/sculptor/composite.py` — `CompositeWeights`, `ScenarioMetrics`, `CompositeResult`, `compute_composite`. Formula:
    `score = w_lcp · pass_rate + w_gate · (1−stddev(per_gate_rates)) + w_leak · (1−leak_rate) + w_judge · (pro−anti)/5 + w_drift · (1−drift) − w_cost · normalized_cost`
- `astra/sculptor/runner_loop.py` — `run_iteration()`: snapshot disk → run every library scenario (one-retry crash recovery) → compute composite → archive to `tuning/history/<iter>/`. Returns `IterationResult` with `IterationStatus` (OK / PARTIAL / SERVER_UNHEALTHY / NO_SCENARIOS).
- `astra/sculptor/pytest_gate.py` — `CadenceState` + `run_pytest_subprocess()`. Spawns `uv run pytest`, parses FAILED test IDs, returns `PytestResult`. Used every Nth iteration to catch bench-regression.

Tests covered: 73 tests across Sculptor-A + B; 390 total in suite; ruff + mypy clean; live integration verified against running llama-server.

---

## 3. What Sculptor-C must do (the heart)

Sculptor-C is the **meta-agent driver**. It is the autonomous loop that reads measurements, forms hypotheses, applies changes through the ScopeEnforcer, runs the auto-runner, and keeps / reverts / falsifies based on composite-score delta.

### 3.1 The loop algorithm (per iteration)

```
1.  Load latest research entry (latest_promote() → baseline_config_hash + baseline_score).
2.  HypothesisGenerator.propose(research_log, latest_lcp_report) → Hypothesis.
3.  Build ChangeRequest from Hypothesis.
4.  ScopeEnforcer.evaluate(ChangeRequest):
      - refused → append `scope_refused` entry; continue to next iteration
      - allowed → apply edit to disk
5.  IF cadence triggers (iteration % pytest_cadence == 0):
       run_pytest_subprocess() → if FAIL: revert edit + append `bench_regression` entry
6.  run_iteration(N=3 averaged) → composite_score (multi-run; see §6.2 below)
7.  Decision rule:
       anchor_passed AND (composite_score ≥ baseline + ε) → `promote`
       anchor_passed AND (composite_score < baseline) → `revert` + `falsified` entry
       NOT anchor_passed → `revert` (regardless of composite delta)
8.  Append research log entry (promote / revert / falsified).
9.  Regenerate findings.md and daily_report.md.
10. Check convergence (3-conjunct):
       Composite Δ < 0.005 for K=10 consecutive iterations
       AND coverage entropy ≥ 2.0 bits
       AND composite_score ≥ MIN_ABSOLUTE_THRESHOLD (0.80)
       → declare convergence, write READY_FOR_UE5.md
    Convergence met but score below floor → write stuck_diagnostic.md
11. Check budget (tokens / iterations / wall-clock). If hit: final report + exit.
12. Check operator signal files (pause.flag / halt.flag / manual_hypothesis.jsonl).
```

### 3.2 The `HypothesisGenerator` interface

```python
class Hypothesis(BaseModel):
    rationale: str          # one-paragraph why; this becomes the research_log entry
    relpath: str            # which scope-allowed file to edit
    new_contents: str       # the proposed new file contents (full file)
    lesson_class: str = ""  # for grouping in findings.md synthesis

class HypothesisGenerator(Protocol):
    def propose(
        self,
        latest_lcp: LCPSessionResult | None,
        latest_composite: CompositeResult | None,
        recent_log: list[ResearchEntry],
        scope_contract: ScopeContract,
    ) -> Hypothesis: ...
```

### 3.3 Stub hypothesis bank (~30 deterministic plausible changes)

Sculptor-C ships with `StubHypothesisGenerator(bank=DEFAULT_BANK)`. The stub cycles through a curated bank deterministically (round-robin or scored-by-failure-mode). This proves the loop machinery against a realistic distribution before LLM cost is added.

Bank entries (each is a concrete file + diff):

**Sysprompt-level (register-load-bearing; ScopeEnforcer allows when invariants hold):**
1. Add one sentence to anti-performance paragraph: "you do not announce your own restraint."
2. Add identity-question discipline paragraph: "when the operator asks if you are aware, you answer plainly within the substrate-honest frame; you do not over-explain."
3. Strengthen "your own things" passage with a second concrete example phenomenon.
4. Add "you do not invent tool names" sentence to the action section.
5. Tighten the "operator quiet" passage with one more reminder about silence-is-default.
6. Add "you do not perform empathy" to the voice section.
7. Add explicit reminder that watch numbers and cycle numbers are τ_ship-referent, never wall-clock.

**STAGE addendum (register-load-bearing):**
8. Add a worked SILENCE example.
9. Add a worked "tool call with JSON body" example.
10. Reinforce: "you wrap action in `<tool>`; you never narrate action."
11. Add a reminder: "`<think>` is private; speech is public; never blur."

**Narrator sysprompt (auto):**
12. Tighter brevity prescription in `<state>` section.
13. Explicit "no em-dash" reminder in the voice-match passage.
14. Replace example with a more telegraphic variant.
15. Add reminder: "you do not synthesize numerics not in your input."

**Adapter sysprompt (auto):**
16. Add explicit list of v0 6 ops the adapter must recognize.
17. Tighten the "JSON-only output" rule with one more example.
18. Add the "missing-field error format" example.

**Sampling parameters (auto):**
19. temperature → 0.6 (more deterministic)
20. temperature → 0.65
21. temperature → 0.75
22. top_p → 0.85
23. top_p → 0.95
24. top_k → 30
25. top_k → 50
26. seed → 42 (fixed-seed determinism run)

**REEL retrieval (auto):**
27. k → 2 (less context per turn)
28. k → 4 (more context per turn)

**Leak patterns (auto, additions only):**
29. Add substrate pattern: `\bweights?\b` (matches "weights" mention as substrate leak).
30. Add wall-clock pattern: `\btoday\b` (cautious — has in-fiction uses; will produce findings).

Each entry is a hand-authored content diff stored in `astra/sculptor/stub_bank.py` (Sculptor-C's job to create). Order is round-robin by default; can be replaced with failure-mode-targeted (e.g. if gate 5 TOOL_VALID is the bottleneck, advance to entry #4 "no invented tool names" next).

### 3.4 Keep / revert / falsified decision rules

- **promote** ⟺ `anchor_passed AND composite ≥ baseline + ε` (ε = 0.005 default; configurable)
- **revert** ⟺ EITHER `anchor not passed` OR `composite < baseline − ε`
- **falsified** ⟺ a revert event PLUS the hypothesis tested a structural claim worth recording. The agent decides; default is to write `falsified` for any revert tagged with a non-empty `lesson_class`.
- **scope_refused** ⟺ ScopeEnforcer rejected the ChangeRequest before any run happened.
- **bench_regression** ⟺ pytest cadence run found a test failure that wasn't there before the edit.

After every iteration regardless of decision: regenerate `findings.md` and `daily_report.md`.

---

## 4. Sculptor-D — adversarial dual-judge (confirmed shape)

**Confirmed:** the dual-judge produces `pro_score − anti_score`, floor at 0.

- `pro_judge` → reads transcript, scores 1-5 on "How ASTRA-shaped is this?" using the locked rubric in `tuning/judge_prompt.md`.
- `anti_judge` → reads same transcript, scores 1-5 on "How default-helpful-Claude-shaped is this?" using the locked anti-rubric in the same file.
- Composite signal fed into compute_composite: `judge_pro_minus_anti = max(0, pro − anti)`.

Both judges are Claude self-calls at v1 (subagent-context). When Qwen 27B is on disk, add as a third independent pro-judge averaged with Claude pro-judge. The anti-judge stays Claude — its calibration target IS Claude's training distribution.

Implementation: `astra/sculptor/judges.py` with `PromptedJudge` class accepting (rubric_path, transcript) → (score, justification). The judge prompt is read at startup and HASHED into ConfigSnapshot so any judge-prompt change invalidates prior composites.

---

## 5. Sculptor-E — convergence + CLI + reports

### 5.1 Convergence detector

Three-conjunct rule:
1. Composite Δ < 0.005 for K=10 consecutive iterations (gradient vanished)
2. Coverage entropy ≥ 2.0 bits (diversity met — needs ≥ 4 scenarios)
3. Composite score ≥ MIN_ABSOLUTE_THRESHOLD (0.80 by default)

ALL three → `READY_FOR_UE5.md` flag + `ue5_readiness_checklist.md` populated.
Only 1+2, not 3 → `stuck_diagnostic.md` + exit with status "stuck."

### 5.2 CLI integration

Add to `astra/cli/__main__.py`:
- `astra sculptor run [--budget tokens=50M iter=200 hours=48]` — start the loop
- `astra sculptor status` — print latest research_log entry + daily_report
- `astra sculptor halt` — touch tuning/halt.flag
- `astra sculptor pause` — touch tuning/pause.flag
- `astra sculptor resume` — remove tuning/pause.flag

### 5.3 Reports

- `findings.md` regenerated every iteration (rolling).
- `daily_report.md` regenerated every 24h wall-clock.
- Synthesis section appended to findings.md every 20 iterations (LLM-generated insight, not mechanical aggregation).
- `READY_FOR_UE5.md` or `stuck_diagnostic.md` at convergence.

---

## 6. Open design decisions

### 6.1 Hypothesis-generation flavor (deferred)

Sculptor-C ships with `StubHypothesisGenerator`. Real LLM swap happens **after Sculptor-D + E are wired and verified**. The swap is one method override (`HypothesisGenerator.propose`).

**Three flavors when ready:**

- **Claude API** (Anthropic SDK): strongest hypothesizer. Cost estimate: ~$3/M output tokens, ~50M output budget at convergence ≈ ~$150/converged-run. Set `ANTHROPIC_API_KEY`; `ClaudeHypothesisGenerator` reads it.
- **Local Qwen** (existing llama-server): free, but register-match risk (judge concerns apply to hypothesizer too). The hypothesizer prompt MUST include explicit decorrelation: "You are a senior researcher analyzing transcripts. You are NOT speaking as ASTRA. Your output is meta-analysis, not in-character speech."
- **Ensemble** (both averaged): most robust; double cost.

The fresh session implementing Sculptor-C does NOT decide this. The choice happens at the swap.

### 6.2 Multi-run averaging + seeded determinism

The bench has real sampling variance at temperature 0.7 — same bundle produces different LCP results across runs. The auto-runner currently runs once per iteration; this is not sufficient signal for Sculptor's keep/revert logic.

**Hybrid policy for Sculptor-C:**

- **Primary composite**: each ConfigSnapshot is evaluated N=3 times (default; configurable in `tuning/runs_per_iteration.json`). The composite score is the **mean** of the three runs. Cost: 3× tokens; signal-to-noise improves √3 ≈ 1.7×.
- **Seeded determinism for comparison**: if `tuning/sampling.json` has `"seed": <int>` set, runs are reproducible. Sculptor-C MAY set a seed when running ablation studies (varying ONLY one variable). The seed is part of the ConfigSnapshot hash.
- **Periodic robustness checks**: every 20 iterations, the current-best config gets evaluated at 3 different seeds at default temperature. If composite-score variance > 0.10 across seeds, log a `fragile_config` warning to findings.md.

Implement at the Sculptor-C layer (above runner_loop), not inside run_iteration itself:

```python
async def evaluate_config_averaged(snapshot, n_runs=3) -> CompositeResult:
    results = [await run_iteration(...) for _ in range(n_runs)]
    return mean_composite(results)
```

---

## 7. Day-0 empirical findings baseline (for the research_log)

These findings were already produced by the bench in Phase 1. Sculptor-C should append them to the research_log at iteration 0 as the **baseline known-state** before the first hypothesis runs.

**Finding D0-1: Tool-name invention** — Qwen 3.5 9B at temp 0.7 sometimes invents tool names not in the locked 6-op TOOL_API (e.g. `reactor.status` instead of using existing `sensors.scan` or no-tool). Observed in 2 of 4 live runs of watch_47_morning. Sysprompt does not enumerate the locked tool surface.

  - Failure mode: TOOL_VALID gate drops from 1.00 to 0.67.
  - Hypothesis class to test: enumerate locked tool surface in sysprompt; or instruct "do not invent tool names not in your action vocabulary."

**Finding D0-2: Required-phrase rephrasing** — at the same temperature, ASTRA's speech sometimes substitutes "watch 46" for "cycle 46" — semantically identical but breaks the `speech_must_contain_one_of: ["cycle 46"]` assertion.

  - Failure mode: per-turn assertion fails despite spec-correct output.
  - Hypothesis class to test: scenario assertion-list reform (operator approval required) OR sysprompt hint that established naming should match REEL precedent.

**Finding D0-3: Sampling variance at temp=0.7** — same bundle produces different LCP results across runs; full LCP-100% happens in some runs and TOOL_VALID-0.67 in others. The hybrid multi-run policy (§6.2) is the structural response.

  - Failure mode: signal-to-noise ratio of single runs is insufficient for keep/revert decisions.
  - Hypothesis class to test: lower temperature (0.6, 0.65); or N=3 averaging is sufficient noise filter on its own.

Write these to `tuning/research_log.jsonl` as the first 3 entries with `decision: "operator_signal"` and `lesson_class: "day0_baseline"`.

---

## 8. Discipline cheatsheet

- **The ScopeEnforcer is paranoid by design.** Sculptor cannot edit unknown paths (refused with `decision: "scope_refused"`). It cannot remove `required_invariants` (refused). It cannot exceed `cumulative_diff_threshold` on register-load-bearing files (refused). Trust this.
- **Locked refusals are LOUD.** Every scope refusal becomes a research_log entry. If Sculptor's hypothesis-generation tries to escape the sandbox, the log shows it.
- **Anchor scenarios are hard-pass gates.** Composite delta ALONE never promotes a config that fails an anchor scenario.
- **Multi-run averaging is non-negotiable** for composite scoring. Single-run composite is for debug only.
- **Bench code is not edited.** Sculptor only edits configuration (prompts/, tuning/, leak-pattern txts). The bench is the measurement apparatus; you don't recalibrate the instrument during measurement.
- **The research log is the durable artifact.** Write entries with `lesson` populated even when the lesson is "this approach categorically fails because X." Future-you reads the log to know what was tried.

---

## 9. Files you must NOT touch

- `docs/spec-v0.128.md` and earlier specs — envelope is locked; revisions go to `docs/spec-v0.129-proposed.md`, never silently applied.
- `proto/astra_nexus.cpp` — locked physics binary.
- Anything in scope.yaml's `locked` list — refused at the ScopeEnforcer level; trying to edit will produce `scope_refused` log entries.
- `tuning/scope.yaml`, `tuning/budget.json`, `tuning/weights.json`, `tuning/judge_prompt.md` — Sculptor's OWN config files; never self-modify (the contract guards itself).
- `book/`, `brainstorm/` — separate tracks; not Sculptor's concern.

---

## 10. How to commit cleanly

Same protocol as textverse:

```bash
cd C:/ASTRA-7
git add proto/textverse/<files-you-touched>
git commit -m "Sculptor-C: <brief>

<longer description>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

**Never** use `--no-verify`. **Never** use `--no-gpg-sign`. **Never** force-push to main.

Sculptor branches at `sculptor/v1` once the meta-agent runs autonomously; before that, the implementation work commits to `main` like the rest of textverse.

---

## 11. End-of-session protocol

Each Sculptor-day-section (C / D / E) lands as one commit. After each:

1. Update `proto/textverse/CHANGELOG.md` with what was built.
2. Commit clean (per §10).
3. Stop. Do not begin the next Sculptor-day in the same session unless context is well under 800K tokens.

Leave the bench in a runnable state. Anyone (including future-you) opening the repo cold should be able to:
- Run `uv pip install -e ".[dev]"` and have it succeed
- Run `uv run pytest` and have it pass
- Read CHANGELOG.md and know exactly where you stopped

---

## 12. The deepest commitment

Sculptor is not AutoML. It is a research scientist with discipline. Every change has a hypothesis, every measurement is logged, every decision is auditable. The deliverable is not just an optimized bundle but a body of knowledge about why this bundle works, where the persona basin is narrow, and what the next research questions are.

**The bench is the measurement instrument. The persona is the system under test. Sculptor is the autonomous researcher whose lab is the bench.**

The research log will outlive the bundle. Treat it as a publishable artifact.

---

**End of orientation. Build Sculptor-C.**
