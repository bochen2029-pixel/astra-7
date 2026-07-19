# STARTUP.md — Fresh session orientation for textverse

**Read this file first. It is short by design.** It tells you what to read, in what order, before doing any work.

If you are a fresh Claude Code session, a future-you, or a coding agent picking up where the prior session ended: this is the directive. Do not improvise alternative starting points.

*(Rewritten 2026-07-19 per spec-v0.130-DRAFT QCR-12. The previous revision of this file described the pre-loop Day 0–7 build plan against spec v0.128; that era is over — the loop closed on 2026-05-15, the envelope is v0.129, and the bench is permanent infrastructure.)*

---

## 0. What you are joining

You are joining **ASTRA-7's `proto/textverse/`** — the closed-loop verification bench for the project's bundle architecture, **Implementation A** of the dual-implementation discipline (spec v0.129 §15.7) and **permanent infrastructure**: it runs alongside UE5 forever as the contract-conformance regression environment.

The loop is closed and load-bearing. As of 2026-07-19: **774 pytest green** (canonical runner: `uv run pytest`; if the bare venv is stale, `uv sync` repairs it), ruff + strict-mypy clean, `proto/astra_nexus.exe` at **71/71 assertions**, scenario library at **20** with an 82-test library-wide validation gate. Three LLM bundles (ASTRA / Narrator / Adapter) run calculator-bound to the C++ physics binary; three §4.9 ephemerals (consolidator, journal_generator, drift_detector) are implemented as deterministic pure functions; SaveFile v3 carries the regime-coherence load gate; the Somatic Aggregator is live.

**Loop preservation IS the regression test (§15.6).** Every commit either keeps the suite green or is a finding.

---

## 1. Required reading (in this order)

| # | File | Why |
|---|------|-----|
| 1 | `CHANGELOG.md` (this directory) | What was done last; pick up at the top entry |
| 2 | `docs/spec-v0.129.md` | The adopted envelope. ~45K tokens — size it and chunk it if your context demands (`C:\chunker\`) |
| 3 | `docs/spec-v0.130-DRAFT-2026-07-19.md` | The amendment draft: QC findings register (QCR-1…19), amended contract text, and the current work queue. Code lands citing this draft; adoption rides the commits (§15.4 pattern) |
| 4 | `docs/stage-protocol.md` + `docs/narrator-spec.md` | Implemented I/O grammar + Narrator contract (DRAFT v0.1, written from code) |
| 5 | `docs/astra-sysprompt.md` + `docs/astra-sysprompt-addendum-stage.md` | Surface 5 — the persona envelope. Canon-locked |
| 6 | `ARCHITECTURE.md` (this directory) | The original ground-up design (2026-05-15, v0.128-aligned). Historical plan-of-record — code and v0.129 win where they moved on |

**Do NOT load historical specs (v0.1 … v0.128)** unless investigating a historical commitment. **Do NOT load `brainstorm/`** (research scratch, known bugs).

---

## 2. Work picker (post-parity)

QC-to-parity vs v0.129 completed 2026-07-19 (see CHANGELOG). Forward implementation toward v0.130, in the draft's §4.2 order:

| # | Work item | Draft ref | Status |
|---|-----------|-----------|--------|
| 1 | Trace/event-log tagging + Model-Off Replay driver + CI leg | §2.4, §2.5 | **DONE 2026-07-19** (`53124a5`) |
| 2 | §4.3.1 Turn-Scheduling (heartbeat / interruption / initiative) + asynchrony scenarios; ephemeral maintenance-window triggers ride the heartbeat | §2.6, QCR-14/15 | **DONE 2026-07-19** (`406f7f9`; gun R-5 witness held — pre-asynchrony suite green throughout) |
| 3 | Frame Drill + autotelic instrumentation package | §2.7, §3 | **measurement half DONE 2026-07-19** (`astra/judge/autotelic.py`: metrics + scripted-probe catch aggregation). Remaining: thresholds (set against measured distributions), the ~6 negative-space pattern files (needs the unhurried `book/negative_space.md` review the autonomous run deferred), and the generative operator-LLM red-seat (needs llm_proxy + live models) |
| 4 | Track C micro-turn: nexus `compute_grav_factor` stdio op (parser needs array support), QCR-8 horizon comment, version-string bump — rebuild + 71-assertion rerun in the same commit | QCR-5/8 | pending (C++, additive) |
| 5 | Live-LLM pass: run the 23-scenario suite (incl. the three asynchrony scenarios) against local llama-server; first measured autotelic-metric distributions | §3 | pending (needs models up) |

One work item per session. Land it, gate it, log it, commit, stop.

---

## 3. What "done" looks like (unchanged)

1. Code lives where the module layout already puts it.
2. `uv run pytest` green; new tests for the new surface.
3. `uv run ruff check astra tests` clean; `uv run mypy astra` clean (strict).
4. `CHANGELOG.md` gets an entry: what was built, what passes, any spec findings.
5. Clean commit (no `--no-verify`, no `--no-gpg-sign`, never force-push main).
6. **Stop.** Do not begin the next work item in the same session.

---

## 4. Files you must NOT touch

- **`docs/spec-v0.129.md`** — the adopted envelope. Findings route into the v0.130 draft's QC register or a dated proposal note; the adopted spec is never edited in place.
- **`docs/spec-v0.130-DRAFT-2026-07-19.md`** — operator-owned amendment draft; implementation cites it, only the operator's adoption ruling changes it.
- **`proto/astra_nexus.cpp`** — locked; additive-only changes, and only in a dedicated Track C session that rebuilds and reruns all 71 assertions in the same commit.
- **`docs/astra-sysprompt.md`** (+ addendum) — Surface 5 canon. `prompts/` holds the runtime copies.
- **Canon pattern files** (`astra/grammar/canon/*.txt`, `astra/harness/ephemeral/canon/qc3_events.txt`) — additions only, and keep the root `tests/` mirrors byte-identical (`tests/test_canon_mirrors.py` enforces; the pairs diverged once — QCR-1 — never again).
- **`tuning/`** — the Sculptor's own contract surface; `scope.yaml` bounds what Sculptor may edit and names the locked set.
- **`book/`**, historical specs, `brainstorm/` — not the bench's concern.

---

## 5. Discipline cheatsheet (spec v0.129 §15)

- **§15.4** — lock against current findings; revise on new findings; do not polish without findings. Mode 6 (spec drift without empirical justification) is the named failure mode.
- **§15.5** — Progressive Specification: detail tightens within the envelope, never violates it.
- **§15.6** — Calculator-bound LLM agency: every world-state-touching LLM is validator-wrapped; no numeric reaches speech untraced. Not opt-in.
- **§15.7** — Dual-implementation: don't bake textverse-only assumptions into the five shared surfaces; UE5 consumes the same contracts.
- **§15.8** — Independent tracks: you are in Track A; don't reach into B/C except through the contract surfaces.

## 6. Specific prohibitions for textverse (unchanged + two new)

- No `datetime` / `time.time()` / calendar idioms outside the infrastructure paths named in `tests/test_scaffolding.py`.
- No service-interface phrases, no em-dashes in operator-facing speech, no markdown in LLM output, no chat-app affordances.
- No forking DAVE or TERMINAL code.
- **`t_cosmic` is epoch-zero seconds, bounded below 2³⁹ s** (QCR-3; `TimeState` enforces; `tests/test_time_epoch_kat.py` is the permanent KAT). Never "since Big Bang"; never accumulate absolute time as `t += dt`.
- **Regime, grav_factor, and ship_kinematics are computed fields** — derived from truth fields, never stored, never passed in from a caller.

---

## 7. End-of-session protocol

1. Update `CHANGELOG.md`. 2. Commit clean. 3. Push only with the operator's current token, never stored. 4. Stop, leaving `uv run pytest` green from a cold checkout.

---

## 8. The deepest commitment

The loop closed; the bench is the instrument everything else is measured against. Every line of code you write either keeps the loop preservable or breaks it. The envelope is locked; the sculpting continues.

Go.
