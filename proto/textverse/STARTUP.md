# STARTUP.md — Fresh session orientation for textverse

**Read this file first. It is short by design.** It tells you what to read, in what order, before doing any work.

If you are a fresh Claude Code session, a future-you, or a coding agent picking up where the prior session ended: this is the directive. Do not improvise alternative starting points.

---

## 0. What you are joining

You are joining the implementation track of **ASTRA-7's `proto/textverse/`** — the closed-loop verification bench for the project's bundle architecture. The project repo is `bochen2029-pixel/astra-7` on GitHub. The operator is Bo Chen (solo dev).

The bench is **Implementation A of the dual-implementation discipline** (per spec v0.128 §15.7). It runs ASTRA-LLM, Narrator-LLM, and Adapter-LLM as three local llama-server instances calculator-bound to a verified C++ physics binary. It scores scenarios against a 9-gate Loop Closure Property. **Until the first scenario passes all gates, the project's architecture is hypothesis.** The bench's job is to make it empirical.

---

## 1. Required reading (in this order, ~25 minutes)

| # | File | Why | Approx tokens |
|---|------|-----|---------------|
| 1 | `proto/textverse/ARCHITECTURE.md` | Full ground-up design + 7-day implementation plan + cross-references to v0.128 sections | ~13K |
| 2 | `docs/spec-v0.128.md` §0-§4 (intent, invariants, contracts) | The envelope you conform to | ~6K |
| 3 | `docs/spec-v0.128.md` §15 (the four named disciplines) | The discipline you operate under | ~4K |
| 4 | `docs/astra-sysprompt.md` + `docs/astra-sysprompt-addendum-stage.md` | Surface 5 (Persona envelope) — what ASTRA sounds like + the STAGE I/O grammar | ~3K |
| 5 | `proto/textverse/scenarios/watch_47_morning.md` | The canonical first scenario the bench must close | ~1.5K |
| 6 | `proto/textverse/CHANGELOG.md` | What's been done so far; pick up at the last logged entry | tiny |

**Do NOT load v0.123 / v0.125 / v0.126 / v0.127 unless investigating a historical commitment.** v0.128 is the current envelope. The earlier specs are archived precursors, kept for traceability only.

**Do NOT load the brainstorm/ directory.** It is raw research scratch with 13 known bugs already distilled into the spec. Reading it confuses, not informs.

---

## 2. Day picker

| Day | Status | Deliverables | Gate for "Day done" |
|-----|--------|--------------|---------------------|
| 0 | **DONE** | Scaffolding (pyproject.toml, empty package, .gitignore, this file) | `uv run pytest` passes the 3 scaffolding tests |
| 1 | next | Pydantic types in `astra/core/` + `astra/state_bus/schema.py` + roundtrip tests | `uv run pytest` passes; can load `watch_47_morning.yaml` initial_state into a `StateBus` Pydantic instance |
| 2 | pending | Extend `proto/astra_nexus.cpp` with `--stdio-server` mode; `astra/physics/nexus_bridge.py` + roundtrip test | `pytest tests/test_nexus_bridge.py -m requires_nexus` passes; `compute_apparent_rate(v_radial=0.5c, regime=STL_REL)` returns ≈0.5774 |
| 3 | pending | `astra/grammar/` parser + strip rules + leak detector + tests including nested-thinking test | Last-`</think>` strip rule test passes; outer raw deliberation gets captured to `pre_think_raw`, never leaks into `speech` |
| 4 | pending | `astra/llm/` clients + sidecar + validator + `prompts/*.md` | One smoke test: start ASTRA llama-server, send perception bundle by hand, verify STAGE output parses cleanly |
| 5 | pending | `astra/ship/`, `astra/universe/`, `astra/harness/orchestrator.py`, `astra/harness/reel.py` | A single hand-paste turn completes through the orchestrator end-to-end |
| 6 | pending | `astra/judge/`, `astra/scenarios/` runner, translate watch_47_morning.md → watch_47_morning.yaml | First scenario runs scripted-mode through the orchestrator |
| 7 | pending | `astra/cli/` + close-the-loop | Watch 47 morning scenario passes LCP gates 1, 3, 7 minimum; transcript + LCP report written |

**Pick the next pending day. Do that day's work. Stop. Update CHANGELOG.md. Commit.**

Do not skip days. Do not combine days. Day N+1 depends on Day N's deliverables landing.

---

## 3. What "Day done" looks like

For each day:

1. Code is written and lives in the files named in ARCHITECTURE.md §5.
2. All tests in `tests/` pass. New tests added for the day's deliverables.
3. `uv run ruff check astra/` is clean.
4. `uv run mypy astra/` is clean for the modules touched (strict mode per pyproject.toml).
5. `CHANGELOG.md` gets a new entry: what was built, what tests pass, any spec findings.
6. Git commit with a clear message naming the day and the deliverable. No `--no-verify`. No `--no-gpg-sign`.
7. **Stop.** Do not continue to the next day in the same session.

---

## 4. Files you must NOT touch

- **`docs/spec-v0.128.md`** — the envelope. Only revise on adversarial-finding-justified loop measurement, never on speculative improvement. If you believe a spec change is warranted, write the proposed change to a new file `docs/spec-v0.129-proposed.md` with reasoning; do not edit v0.128 in place.
- **`proto/astra_nexus.cpp`** — the locked physics binary, except for Day 2's `--stdio-server` mode addition, which is purely additive (new flag + new code path; existing 48 assertions still pass).
- **`docs/astra-sysprompt.md`** — canonical Surface 5. Copy into `proto/textverse/prompts/astra_sysprompt.md`; do not modify the canon.
- **`book/`** — novel-side work; not the bench's concern.
- **`brainstorm/`** — research scratch with known bugs.
- **Any historical spec (`v0.1`, `v0.123`, etc.)** — archived; read-only.

---

## 5. Discipline cheatsheet

Pulled from `docs/spec-v0.128.md` §15:

- **§15.4 — Lock envelope; sculpt within bounds.** Findings from running the bench justify spec revision. Speculative improvements do not. If in doubt, don't.
- **§15.5 — Progressive Specification.** Each round adds detail within prior commitments. Never violates earlier locks. Forward-compatible vagueness is a design move, not a gap.
- **§15.6 — Calculator-bound LLM agency.** Every LLM call in this bench routes through `CalculatorBoundValidator`. No numeric token reaches operator-facing speech unless it traces to a tool-call result. Enforced at the SDK boundary.
- **§15.7 — Dual-implementation discipline.** The textverse harness code is substrate-portable. The same harness will eventually run against UE5 (Implementation B). Only perception assembler + tool dispatcher are substrate-specific. Don't bake in textverse-only assumptions.
- **§15.8 — Triple-rig methodology + independent tracks.** Track A (LLM bundle) = this bench. Track B (Engine/UE5) = parallel, independent. Track C (Physics binary) = locked. You are in Track A.

---

## 6. Specific prohibitions for textverse

- **No `datetime`, no `time.time()`, no calendar idioms anywhere except in `astra/judge/` for iteration timing.** Enforced by `tests/test_scaffolding.py::test_no_wall_clock_imports_in_scaffolding`. This test must keep passing as code is added.
- **No service-interface phrases in any sysprompt or prompt template.** No "I'd be happy to", "Is there anything else", "As an AI", etc.
- **No em-dashes in any text routed to operator-facing speech.** The leak detector catches these; don't write them in templates either.
- **No markdown in LLM output.** ASTRA emits prose; no `**bold**`, no headers, no bullet lists.
- **No chat-app UI affordances.** No regenerate button, no model selector, no "new chat", no copy-to-clipboard. The bench is a verification rig; aesthetics belong to UE5.
- **No forking DAVE or TERMINAL code.** Reference for patterns is fine. Code import is not. ARCHITECTURE.md §0 explains why.

---

## 7. How to commit cleanly

When ready to commit at end of a day:

```bash
cd C:/ASTRA-7
git add proto/textverse/<files-you-touched>
git commit -m "textverse Day N: <brief>

<longer description>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

**Never** use `--no-verify`. **Never** use `--no-gpg-sign`. **Never** force-push to main.

For pushing to GitHub: use a token only in the push URL, never in `.git/config`. The token is operator-managed; ask the operator for it if needed.

---

## 8. When something is unclear

If the architecture doc and the spec are silent on a question, **default to deferral**: the smallest possible commitment that lets the current day's work proceed, with a TODO noting the deferred decision. Do not invent new architecture surfaces. Do not add commitments that v0.128 doesn't already lock.

If a spec contradiction surfaces — two sections that disagree — that's a finding. Stop coding. Write a brief note to `docs/spec-v0.129-proposed.md` with the contradiction, your proposed resolution, and which scenario surfaced it. Then continue with the day's work using the most conservative interpretation.

---

## 9. End-of-session protocol

When you stop for the day:

1. Update `CHANGELOG.md` with what was built.
2. Commit clean (per §7).
3. If pushing to GH: use the operator's current token; never store it locally.
4. Stop. Do not begin the next day's work in the same session.

Leave the project in a runnable state. Anyone (including future-you) opening the repo cold should be able to:
- Run `uv pip install -e ".[dev]"` and have it succeed
- Run `uv run pytest` and have it pass
- Read CHANGELOG.md and know exactly where you stopped

---

## 10. The deepest commitment

You are not building software. You are sculpting an architecture against an empirical loop. The loop closing is the categorical transition; everything before it is hypothesis. Every line of code you write either keeps the loop preservable or breaks it.

**The envelope is locked. The sculpting begins.**

Go.
