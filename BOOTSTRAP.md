# BOOTSTRAP — fresh-session entry point

**You are joining ASTRA-7.** This file orients fresh sessions (humans or coding agents) in under 60 seconds. After reading this file you will know: where you are, what's auto-loaded, which track you're on, what to read next.

This file is not the project canon. It is the **doorway** into the canon.

---

## 0. Quick-check before doing anything

**Confirm your working directory is `C:\ASTRA-7\` (the project root).** Not a subdirectory. The reason: Claude Code's memory auto-load is keyed to project root, and a session opened at a subdirectory may not get the right initial context.

If your cwd isn't `C:\ASTRA-7\`, exit and restart there.

---

## 1. What auto-loaded before this prompt

When a session opens at `C:\ASTRA-7\`, the following are loaded into your initial context **before** the user types anything:

| File | What it contains | Approx tokens |
|------|------------------|----------------|
| `CLAUDE.md` | Project canon: design philosophy, autotelic discipline, ASTRA's character, the architecture's why, the **measured current state**, working conventions | ~18K |
| `MEMORY.md` (from `C:\Users\user\.claude\projects\C--ASTRA-7\memory\`) | Three-line index into three small fact files | <1K |

**Corrected 2026-08-02.** An earlier revision of this file described the harness memory as a rich session-dump lineage with `project_status.md`, `user_profile.md`, `resources_external.md`, and `hull_design_v0.md`. Those files do not exist. The memory directory holds `MEMORY.md` plus three fact files, and there is **no `memory/` directory in this repo at all**. Treat `CLAUDE.md` §Current Status as the authoritative state snapshot; repo state is reconstructable from `proto/textverse/CHANGELOG.md` + `STARTUP.md`.

You already have enough to know **what ASTRA-7 is**, **what the current state is**, and **which discipline you operate under**.

What you do NOT yet have without further reading: the full spec text, the ASTRA sysprompt, the textverse architecture, the canonical scenarios, the book's voice rules. Those load on-demand via the track-specific STARTUP.md.

---

## 2. Pick your track

| Track | Read first | What you're doing |
|-------|------------|-------------------|
| **A — textverse** (LLM bundle bench, **current build focus**) | `proto/textverse/STARTUP.md` | The closed-loop verification bench. **The Day 1–7 build plan is history** — the loop closed 2026-05-15 and the bench is permanent infrastructure. Work routing is STARTUP §2. |
| **B — UE5 game plugin** (engine) | **Nothing to read — not begun.** `proto/ue5plugin/STARTUP.md` does not exist. | Unstarted. When it starts, §15.7 binds it to the same contract surfaces textverse consumes. |
| **C — physics binary** (proto/astra_nexus) | `proto/astra_nexus.cpp` + the spec's §6.3 / §3.7 (`verify_nexus.py` is a frozen-legacy mirror) | Locked except for additive changes. `--stdio-server` already landed. **82 assertions must keep passing** — rebuild and rerun in the same commit. |
| **Visual testbed** | `ASTRA_VISUALIZER_02/CLAUDE.md` then `DESIGN_SPEC.md` | CUDA + OpenGL, 12 scenes, SHIPPED v0.1.0. Scope-locked: read anywhere under `C:\ASTRA-7\`, write only inside that folder. `ASTRA_VISUALIZER/` (no suffix) is the superseded first attempt. |
| **Audio PoC** | `ASTRA_AUDIO/CLAUDE.md` then `DESIGN_SPEC.md` | UE 5.7, five-layer MetaSound warp-hull synthesis, procedurally built at runtime, zero binary assets. Ear-tuning sign-off pending. |
| **A0 fine-tune** | `astra-a0-bootstrap/WAKE_UP.md`, then `C:\astra-a0-finetune\CLAUDE.md` | **Separate git repo** outside this one. Phase 6 complete. Next gate is operator authorization for SOTA batch generation. |
| **Book drafting** | `book/RESUME.md` + `book/CANON.md` + `book/negative_space.md` | The Long Watch novel. **Manuscript is complete** (14 cycles + front + back matter). Separate discipline. |
| **Spec revision** | `docs/spec-v0.130.md` §15.4 + §15.11 first (current envelope; adopted 2026-07-19 per the finalization packet, rulings R-A…R-D) | **Forbidden absent an empirical finding from a closed loop.** Mode 6 risk. Route findings into a dated proposal note or the next revision's QC register; never edit the adopted spec in place. |

If you're not sure which track: the operator (Bo Chen) will tell you. The default current-build-focus is **Track A textverse**.

---

## 3. Standard fresh-session prompts (paste-ready)

These are minimal user prompts that, combined with the auto-loaded context above, are sufficient to begin work cleanly.

*(Rewritten 2026-08-02. The prior revision's prompts were written for the Day 1–7 build era and cited assertion counts that have since moved.)*

### Track A textverse — next work item

```
Read proto/textverse/STARTUP.md. Pick the next work item from §2 routing
(or execute the one the operator names). One item per session: land it,
gate it, log it in CHANGELOG.md, commit, stop.
```

### Track A textverse — live-LLM pass

```
Run the live suite against local llama-server + Qwen3.5-9B-Q5_K_M at C:\models\.
  uv run python scripts/live_suite_pass.py
Default ctx is 16384 (F-LIVE-27). Findings go in a dated LIVE_RUN_*.md ledger.
Series claims carry bands: replicate, pool, report counts not rates.
```

### Track C physics binary — additive change

```
Additive change to proto/astra_nexus.cpp only. Rebuild with build.bat and
rerun all 82 assertions in the SAME commit:
  proto/astra_nexus.exe                 (test suite; expect "82 passed, 0 failed")
  proto/astra_nexus.exe --stdio-server  (JSON queries on stdin)
Also verify the textverse cross-substrate parity grid still passes:
  uv run pytest tests/test_nexus_bridge.py
```

### Book drafting

```
The manuscript is complete (14 cycles + front + back matter). For revisions,
read book/RESUME.md, book/CANON.md, book/negative_space.md, and the target
cycle. Em-dash check before filing.
```

### A0 fine-tune pipeline

```
Separate repo at C:\astra-a0-finetune\. Read its CLAUDE.md + MAINTENANCE_LOG.md
+ PILOT_2026-07-26.md. Phase 6 is complete and proven; the next step needs an
explicit operator gate on generation spend. Do not start paid generation
without it.
```

### Hygiene / one-off operations

For small operator-driven tasks (token rotation help, log scrub, README edit, commit a single file), no track-specific orientation needed; the auto-loaded context is sufficient. Just describe what to do.

---

## 4. Universal discipline (binds all tracks)

These hold regardless of which track you're on. Pulled from `docs/spec-v0.130.md` §15:

- **§15.4 — Envelope locked; sculpting begins.** Don't propose spec revisions absent empirical findings.
- **§15.5 — Progressive Specification.** Lock the outer envelope; sculpt detail within bounds; never violate prior locks.
- **§15.6 — Calculator-bound LLM agency.** Every LLM call in the project routes through verified deterministic tools for any numerical claim. No exception.
- **§15.7 — Dual-implementation discipline.** Don't bake textverse-specific assumptions into the contract; the harness will eventually run against UE5 too.
- **§15.8 — Triple-rig methodology.** Tracks A/B/C iterate independently against contract conformance, not against each other.

### Mode 6 (the named failure mode)

> Operator cannot resist further spec revision.

If you find yourself proposing v0.131 without a specific empirical finding from a closed-loop measurement: stop. The methodology has graduated; the loop is the oracle, not another adversarial review pass. Mode 6 applies to tooling choices too (Agentic Dev Reference R1) — no adopting tools in anticipation of need.

### Universal prohibitions

- No wall-clock anywhere in textverse code except `astra/judge/` (enforced by `tests/test_scaffolding.py`).
- No service-interface phrases anywhere (operator-facing speech, sysprompt templates, narrator outputs).
- No em-dashes in any text routed to operator-facing speech.
- No markdown in LLM-emitted text.
- No `--no-verify`, no `--no-gpg-sign`, no force-push to main.
- No use of project tokens (GitHub PAT, HF token) from prior session logs; ask operator for current credentials when push is needed.

---

## 5. End-of-session protocol

When you stop work for the session:

1. Update the relevant CHANGELOG:
   - For textverse work: `proto/textverse/CHANGELOG.md`
   - For book work: append to the latest book session dump
   - For spec work: this is forbidden by default; if you must, write a dated `docs/spec-v0.13x-proposed.md` with reasoning
2. Commit clean (no `--no-verify`, etc.)
3. If pushing: use the operator's current token in the push URL only; never write it to `.git/config`
4. **Stop.** Do not begin the next day's work in the same session.

Leave the project in a runnable state. The next session (which may be cold) should be able to:
- Run `uv sync` from `proto/textverse/` and have it repair a stale venv
- Run `uv run pytest` from `proto/textverse/` and see **1003 passed** (floor as of 2026-08-02; it only goes up)
- Read CHANGELOG.md and know exactly where you stopped

---

## 6. When something is unclear

If the spec and the architecture and the track STARTUP are silent on a question:

1. **Default to deferral.** Make the smallest commitment that lets the current task proceed. Mark the deferred decision as a TODO in your CHANGELOG entry.
2. **Don't invent new contract surfaces.** v0.130 names the five surfaces; honor them.
3. **If a spec contradiction surfaces:** that's a finding. Write a brief dated `docs/spec-v0.13x-proposed.md` with the contradiction, your proposed resolution, and which scenario or empirical event surfaced it. Then continue your task using the conservative interpretation.
4. **Ask the operator** rather than guessing on ambiguous architectural choices.

---

## 7. Quick file-location reference

*(File counts verified 2026-08-02. The prior revision of this map described the Day-0 skeleton — "3 sanity tests", "first scenario as markdown", "45 assertions" — and omitted the visualizers and the audio project entirely. It was off by roughly three orders of magnitude on the bench and blind to 45% of the tracked repo.)*

```
C:\ASTRA-7\                         647 tracked files
├── CLAUDE.md                       project canon (auto-loaded); §Current Status is the state snapshot
├── BOOTSTRAP.md                    this file
├── README.md   LICENSE
├── ASTRA-A0_EVIDENCE_MAP_2026-07-26.md   A0 finding→corpus traceability
├── docs/                           26 files
│   ├── spec-v0.130.md              THE ENVELOPE (adopted 2026-07-19, rulings R-A…R-D)
│   ├── spec-v0.130-FINALIZATION-PACKET-2026-07-19.md   the adoption record
│   ├── spec-v0.130-DRAFT-2026-07-19.md   QC-register evidence base (superseded)
│   ├── astra-sysprompt.md          canonical persona text (Surface 5)
│   ├── astra-sysprompt-addendum-stage.md  STAGE protocol addendum
│   ├── stage-protocol.md           implemented I/O grammar
│   ├── narrator-spec.md            Narrator contract (DRAFT v0.1, written from code)
│   ├── qualia-1-bridge.md          philosophical backbone
│   ├── synthesis.md  architecture.md   historical through-lines
│   ├── external/                   github / huggingface / steam copy
│   └── spec-v0.{1,123,125,126,127,128,129}.md   historical precursors
│       (there is NO ship-api.md — the Tool API lives in code, 7 ops, test-enforced)
├── proto/                          225 tracked files
│   ├── astra_nexus.cpp             physics binary source (~70 KB C++)
│   ├── astra_nexus.exe             compiled; run bare for the suite → "82 passed, 0 failed"
│   ├── build.bat                   MSVC build (builds source beside itself via %~dp0)
│   ├── verify_nexus.py             FROZEN legacy mirror; cross-substrate checks now
│   │                               live in textverse tests/test_nexus_bridge.py
│   └── textverse/                  TRACK A — the bench
│       ├── STARTUP.md              orientation directive — READ FIRST
│       ├── CHANGELOG.md            ~179 KB running implementation record
│       ├── ARCHITECTURE.md         original ground-up design (historical plan-of-record)
│       ├── LIVE_RUN_*.md           5 live-LLM findings ledgers
│       ├── astra/                  78 .py, ~13.8K LOC across 14 subpackages
│       ├── tests/                  59 .py, ~12.6K LOC — 1003 passing
│       ├── scenarios/library/      34 scenario YAMLs + library-wide validation gate
│       ├── prompts/                4 runtime prompt copies (ASTRA / narrator / adapter / addendum)
│       ├── scripts/                live_suite_pass.py · compare_runs.py (permanent infra)
│       └── tuning/                 Sculptor contract surface; scope.yaml bounds it
├── ASTRA_VISUALIZER_02/            173 tracked files — CUDA+OpenGL, SHIPPED v0.1.0
│   ├── CLAUDE.md  DESIGN_SPEC.md  BUILD_LOG.md  SCENES.md  VALIDATION.md  KNOWN_ISSUES.md
│   ├── src/                        122 files, ~7.2K LOC C++/CUDA
│   └── ci_results/                 12 scene PNGs + report.json (44/44, golden diffs 0.0000)
├── ASTRA_VISUALIZER/               103 tracked files — SUPERSEDED first attempt (v1.14)
├── ASTRA_AUDIO/                    18 tracked files — UE 5.7 MetaSound warp-hull PoC
│   └── Source/AstraAudio/          WarpHullSynthNode.cpp · AstraVoyageActor · GameMode
├── book/                           57 tracked files — "The Long Watch"
│   ├── CANON.md                    universe-separation + Gap Thesis quote
│   ├── negative_space.md           no-Bo grep list + voice prohibitions
│   ├── RESUME.md                   cold-start drafting protocol
│   ├── manuscript/                 14 cycles + 5 front + 5 back matter — COMPLETE
│   └── production/                 DORMANT (Python; closed to new work)
├── astra-a0-bootstrap/             A0 build orchestration docs (CLAUDE.md · WAKE_UP.md)
├── brainstorm/                     research scratch — do NOT load
├── tests/
│   ├── wall_clock_patterns.txt     byte-identical MIRROR of proto/textverse/astra/grammar/canon/
│   └── qc3_events.txt              byte-identical MIRROR of .../astra/harness/ephemeral/canon/
└── game/ · ai/ · infra/            EMPTY scaffolding from the 2026-05-12 layout. Zero
                                    tracked files. Do not assume anything lives here.
```

Outside the repo, load-bearing:

```
C:\astra-a0-finetune\               SEPARATE GIT REPO — the A0 fine-tune pipeline.
                                    Phase 6 complete (2026-07-26), 67 tests green.
                                    CLAUDE.md · MAINTENANCE_LOG.md · PILOT_2026-07-26.md
                                    TIER_BLUEPRINT.{md,csv} · dataset/ · scripts/ · tests/
C:\models\                          local GGUF weights. Qwen3.5-9B-Q5_K_M is the current
                                    measurement floor; also 8B, 4B, embedding, reranker,
                                    whisper (ggml-large-v3-turbo, base.en), mmproj.
C:\Users\user\.claude\projects\C--ASTRA-7\memory\
├── MEMORY.md                       three-line index (auto-loaded)
├── project-textverse-state.md      bench state
├── measurement-discipline.md       pre-register · pool replicates · counts not rates
└── operator-bo-workflow.md         authorization / locked-surface conventions
                                    (NOTE: no project_status.md, no user_profile.md,
                                     no session_dump_*.md — earlier docs claimed these)
___INDEX_CACHE/                     untracked. 000_MASTER_INDEX_2026-06-24.md is the
                                    operator's whole-repo deep-read index, 14 buckets.
```

---

## 8. The deepest commitment

You are not building software for users. You are sculpting an architecture against an empirical loop. The loop closing is the categorical transition; everything before it is hypothesis. Every line of code, every line of prose, every commit either keeps the loop preservable or breaks it.

**The envelope is locked. The sculpting begins.**

Go to your track's STARTUP. Read it. Execute. Stop when done.
