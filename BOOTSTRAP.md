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
| `CLAUDE.md` | Project canon: design philosophy, autotelic discipline, ASTRA's character, the architecture's why, working conventions | ~15K |
| `memory/MEMORY.md` (from `C:\Users\user\.claude\projects\C--ASTRA-7\memory\`) | Index of session dumps + a one-screen current-state summary | ~5K |

Together: ~20K tokens of project-level orientation. You already have it. No additional reading is required to know **what ASTRA-7 is**, **what the current state is**, or **which discipline you operate under**.

What you do NOT yet have without further reading: the full spec text, the ASTRA sysprompt, the textverse architecture, the canonical scenarios, the book's voice rules. Those load on-demand via the track-specific STARTUP.md.

---

## 2. Pick your track

| Track | Read first | What you're doing |
|-------|------------|-------------------|
| **A — textverse** (LLM bundle bench, **current build focus**) | `proto/textverse/STARTUP.md` | Build the closed-loop verification rig in Python. Pure code work. Days 1-7 plan. |
| **B — UE5 plugin** (engine / visual) | `proto/ue5plugin/STARTUP.md` *(forthcoming)* | C++ plugin work in Unreal Engine. Parallel to Track A. |
| **C — physics binary** (proto/astra_nexus) | `proto/astra_nexus.cpp` + the spec's §6.3 / §3.7 (`verify_nexus.py` is a frozen-legacy mirror) | Locked except for additive changes (e.g., Day 2's `--stdio-server` mode). Existing 82 assertions must keep passing. |
| **Book drafting** | Latest `memory/session_dump_*_book_drafting.md` + `book/CANON.md` + `book/negative_space.md` | The Long Watch novel. Parallel session lineage; separate discipline. |
| **Spec revision** | `docs/spec-v0.130.md` §15.4 + §15.11 first (current envelope; adopted 2026-07-19 per the finalization packet, rulings R-A…R-D) | **Forbidden absent an empirical finding from a closed loop.** Mode 6 risk. Route findings into a dated proposal note or the next revision's QC register; never edit the adopted spec in place. |

If you're not sure which track: the operator (Bo Chen) will tell you. The default current-build-focus is **Track A textverse**.

---

## 3. Standard fresh-session prompts (paste-ready)

These are minimal user prompts that, combined with the auto-loaded context above, are sufficient to begin work cleanly.

### Track A textverse, Day N

```
Day N textverse. Read proto/textverse/STARTUP.md and execute Day N per §2.
Stop and commit when Day N deliverables are landed; do not begin Day N+1.
```

(Replace `N` with 1, 2, 3, etc.)

### Track A textverse, interactive REPL exploration (post-Day-7)

```
Run a textverse REPL session against the local llama.cpp + Qwen 9B at C:\models\.
Use the watch_47_morning.yaml scenario as the seed. Print transcript to stdout
and write LCP report to scenarios/output/.
```

### Track C physics binary — Day 2 stdio-server extension

```
Extend proto/astra_nexus.cpp with --stdio-server mode per ARCHITECTURE.md §6.4
+ proto/textverse/ARCHITECTURE.md Day 2. ~50 lines C++ additive change.
Existing 48 assertions must still pass. Build with build.bat, run both:
  proto/astra_nexus.exe          (existing test mode)
  proto/astra_nexus.exe --stdio-server  (new mode; accepts JSON queries on stdin)
Commit when both pass.
```

### Book drafting — next cycle

```
Read latest memory/session_dump_*_book_drafting.md to find the next cycle
to draft. Honor book/CANON.md + book/negative_space.md. Write to
book/manuscript/cycle_NN_<topic>.md. Commit when cycle is complete.
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

If you find yourself proposing v0.129 without a specific empirical finding from a closed loop measurement: stop. The methodology has graduated; the loop is the new oracle, not another adversarial review pass.

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
- Run `uv pip install -e ".[dev]"` from `proto/textverse/` and have it succeed
- Run `uv run pytest` from `proto/textverse/` and have it pass
- Read CHANGELOG.md and know exactly where you stopped

---

## 6. When something is unclear

If the spec and the architecture and the track STARTUP are silent on a question:

1. **Default to deferral.** Make the smallest commitment that lets the current task proceed. Mark the deferred decision as a TODO in your CHANGELOG entry.
2. **Don't invent new contract surfaces.** v0.128 named the surfaces; honor them.
3. **If a spec contradiction surfaces:** that's a finding. Write a brief dated `docs/spec-v0.13x-proposed.md` with the contradiction, your proposed resolution, and which scenario or empirical event surfaced it. Then continue your task using the conservative interpretation.
4. **Ask the operator** rather than guessing on ambiguous architectural choices.

---

## 7. Quick file-location reference

```
C:\ASTRA-7\
├── CLAUDE.md                       project canon (auto-loaded)
├── BOOTSTRAP.md                    this file
├── README.md
├── LICENSE
├── docs/
│   ├── spec-v0.130.md              the envelope (read for any track; adopted 2026-07-19)
│   ├── spec-v0.130-FINALIZATION-PACKET-2026-07-19.md  the adoption record (rulings R-A…R-D)
│   ├── spec-v0.130-DRAFT-2026-07-19.md  QC-register amendment draft (superseded by adoption)
│   ├── astra-sysprompt.md          canonical persona text
│   ├── astra-sysprompt-addendum-stage.md  STAGE protocol addendum
│   ├── qualia-1-bridge.md          philosophical backbone
│   ├── synthesis.md                v0.1 architectural through-line (historical)
│   ├── architecture.md             provisional tactical specifics (historical)
│   └── spec-v0.{1,123,125,126,127,128,129}.md  historical precursors (superseded)
├── book/
│   ├── CANON.md                    universe-separation + Gap Thesis quote
│   ├── negative_space.md           no-Bo grep list + voice prohibitions
│   ├── long_watch_dev.md           14-cycle plan
│   └── manuscript/
│       └── cycle_*.md              drafted novel cycles
├── proto/
│   ├── astra_nexus.cpp             physics binary source
│   ├── astra_nexus.exe             compiled binary (Windows)
│   ├── verify_nexus.py             Python mirror (45 assertions; FROZEN legacy —
│   │                               cross-substrate checks live in textverse tests)
│   ├── build.bat                   MSVC build
│   └── textverse/
│       ├── ARCHITECTURE.md         the full design
│       ├── STARTUP.md              Track A orientation directive
│       ├── pyproject.toml          Python project
│       ├── astra/                  package skeleton (Day 0)
│       ├── tests/                  3 sanity tests
│       └── scenarios/              first scenario as markdown
└── tests/
    ├── wall_clock_patterns.txt     byte-identical MIRROR of the canonical copy at
    │                               proto/textverse/astra/grammar/canon/ (CI-enforced)
    └── qc3_events.txt              byte-identical MIRROR of the canonical copy at
                                    proto/textverse/astra/harness/ephemeral/canon/
```

Memory (auto-loaded, not in repo):

```
C:\Users\user\.claude\projects\C--ASTRA-7\memory\
├── MEMORY.md                       auto-loaded index + one-screen state
├── project_status.md               current state snapshot
├── user_profile.md                 operator profile
├── resources_external.md           handles + URLs
├── hull_design_v0.md               2026 hull aesthetic spec
└── session_dump_*.md               session lineage
```

---

## 8. The deepest commitment

You are not building software for users. You are sculpting an architecture against an empirical loop. The loop closing is the categorical transition; everything before it is hypothesis. Every line of code, every line of prose, every commit either keeps the loop preservable or breaks it.

**The envelope is locked. The sculpting begins.**

Go to your track's STARTUP. Read it. Execute. Stop when done.
