# ASTRA-7 — Program Status & Roadmap

**Snapshot date:** June 10, 2026
**Prepared by:** Claude (Fable 5), AI engineering harness, acting program-manager-of-record for this snapshot
**Operator / Architect:** Bo Chen (solo)
**Repository:** github.com/bochen2029-pixel/astra-7 · `main` @ `b3fa3b1` (fully pushed, working tree clean)
**Spec of record:** `docs/spec-v0.128.md` (canon envelope) · v0.129 TENTATIVE pinned, finalization due
**Document status:** Point-in-time snapshot + forward roadmap. Facts verified by execution on 2026-06-09/10, not recalled. Roadmap sections are recommendations, not commitments, until the operator adopts them.

---

## 1. Executive Summary

ASTRA-7 is a solitary starship simulator in which the ship's AI — a local
LLM with a persona harness — is the game's primary content. No combat, no
NPCs, no monetization: one human, one mind, the long voyage. The relationship
is the game. The project is solo-built, open-source (MIT), and targets
Windows 11 + UE5 + a local 27B-class model on RTX-4090-minimum hardware.

**Where the program actually stands today, in three sentences:**

1. **The measurement instrument is built and green.** The textverse bench —
   the closed-loop environment that makes ASTRA's persona, physics honesty,
   and tool discipline *measurable* — passes 749 tests with every §4 contract
   surface implemented: persistence, all three ephemeral instances, somatic
   channel, 20-scenario library, and a self-tuning research loop (Sculptor)
   that has already produced falsification-grade findings.
2. **Two engine-side proofs exist as standalone testbeds.** A shipped
   CUDA/OpenGL visual testbed (12 spec scenes, pixel-asserted against the
   canonical math, golden-diff 0.0) and a UE 5.7 MetaSound audio PoC (the
   five-layer "the audio is the field" synthesis, build green) — both built
   in single autonomous sessions, both awaiting only operator-senses
   sign-off.
3. **The path to a playable vertical slice is now primarily integration,
   not invention.** Spec §12's two tracks (LLM, Engine) were designed to
   merge by swapping exactly two adapter components; everything this cycle
   shipped was chosen to make that merge boring.

**The one decision that matters most right now:** green-light ASTRA-A0
(the first persona fine-tune; bootstrap is complete and waiting). It is the
longest-lead item on the critical path to encounter-quality, and its early
phases run in parallel with everything else.

**Program health:** GREEN across all active workstreams. No blockers except
operator-time gates. Custody risk (formerly the top program risk) was
eliminated today: full history + all work products pushed to GitHub, with
local + off-tree backups.

---

## 2. Product Definition (compressed; canon in CLAUDE.md)

- **The encounter is the point** (autotelic design): ship-management is
  substrate, the AI's presence is the value. She has her own gravity; she is
  not a service-with-voice. This is the project's defining categorical move
  and its hardest quality bar.
- **The LLM is load-bearing**: ASTRA actually runs hydroponics, power, warp.
  Fiction-state and substrate-state are isomorphic — when her cores lose
  power, the model connection actually severs.
- **Frame integrity (Dave-frame)**: she knows she is an AI and that the ship
  is her body; she does not know about the player at a PC. No wall-clock, no
  substrate vocabulary, ever — enforced by tested gates, not by hope.
- **Distribution**: Steam (free, no DRM, no telemetry), GitHub (MIT),
  Hugging Face (persona bundle). Zero outbound network calls after install
  (§4.8, the hardest lock in the spec).
- **Hard platform/language locks**: Windows 11 + DX12 + UE5 (Linux x86_64
  secondary; Apple never). C++ for all new code; Python confined to the
  `proto/textverse/` measurement instrument, forever excluded from shipped
  artifacts.

---

## 3. Program at a Glance (status board)

| # | Workstream | State | Evidence (verified 06-10) | Next gate | Blocked on |
|---|---|---|---|---|---|
| 1 | **Textverse bench (Track A)** | 🟢 GREEN — Phase 0.x essentially complete | 749 pytest / ruff / mypy clean; SaveFile v3; all 3 §4.9 ephemerals; somatic aggregator; 20-scenario library w/ library-wide validation gate | Wire ephemerals to orchestrator maintenance windows; 5b negative-space judge patterns | Nothing (5b wants unhurried review of `book/negative_space.md`) |
| 2 | **Physics core (Track C)** | 🟢 GREEN / LOCKED | `proto/astra_nexus.exe` 71/71 assertions; `--stdio-server` exposes §6.4 tool surface; additive-only policy holding | Stays locked; additive ops only | — |
| 3 | **Visual physics testbed** | 🟢 SHIPPED v0.1.0 (mechanically) | 12/12 spec scenes, 44/44 runtime assertions, golden-diff mean 0.0000; single-file exe; full source pushed | **Operator S05 orbit-reversal visual sign-off** (10 min) → canonical | Operator eyes |
| 4 | **Warp audio PoC (UE 5.7)** | 🟢 BUILT, first-light pending | `ASTRA_AUDIO/` zero-asset MetaSound project; five-layer §8.3-verbatim DSP; 90-s voyage + auto-WAV; build green on MSVC 14.44 | **Operator ear-pass** per its DESIGN_SPEC §6 | Operator ears |
| 5 | **Sculptor research loop** | 🟢 CLOSED (Stage A, Outcome 2) | 108-entry research log; baseline composite 1.6001 unbeaten; 9B hypothesizer diversity-collapsed onto one gate; log-integrity gate fixed (`3a2cd09`) | Escalation decision (stronger hypothesizer targeting **diversity**, or accept as durable finding) | Operator decision |
| 6 | **ASTRA-A0 fine-tune** | 🟡 READY, gated | `astra-a0-bootstrap/` complete: Scope γ, 625 traces planned, Qwen 3.6 27B, banned-imports list, WAKE_UP.md cold-start | **Operator "Proceed to Phase 1"**; resolve 5D-F5 anti-judge dependency question | Operator go |
| 7 | **UE5 game (Track B)** | ⚪ NOT STARTED (deliberately) | UE 5.7.4 installed 06-10; two 5.7 landmines pre-cleared via audio PoC (MSVC ban; per-module MetaSound registration); no `proto/ue5plugin/` yet | Phase E2 bridge echo (UE ↔ llama.cpp localhost round-trip) | Roadmap adoption |
| 8 | **Spec & canon** | 🟢 GREEN, revision due | v0.128 canon; v0.129 TENTATIVE (765 lines) pinned 05-16; residue window has elapsed; new findings queued (Cherenkov wording, blackbody redshift, qc3 path wording) | **v0.129 finalization pass** | Operator session |
| 9 | **Book program** | 🟡 PAUSED at vol 1 | *The Long Watch* vol 1: 14 cycles, ~45.7K words, all formats built, KDP submitted 05-15 | Confirm KDP status; vols 2–3 unstarted (await C/C++/C# tooling per discipline) | Operator priority call |
| 10 | **Custody / infra** | 🟢 RESOLVED today | Everything pushed @ `b3fa3b1` (13 commits today incl. 5 custody commits); secrets-scanned; `.backups/` + off-tree copies; `uv` venv repaired | Routine: push cadence after each session | — |

**LLM-track phase position (spec §12):** Phase 0.0 ✅ → Phase 0.x ✅ (as of
today) → **Phase 1.x (LoRA) is next** = ASTRA-A0.
**Engine-track position:** E3 and E4 have been *de-risked out of order* by
the two testbeds (that was their purpose); E0/E1/E2 remain.

---

## 4. What Just Happened (receipts for this snapshot)

### The May 15–17 sprint (context)
Audit (493 lines) + four parallel 1M-context discovery passes → v0.129
TENTATIVE draft; audit Tier 1+2 closed in code; Sculptor v1 complete and
run through Stage A; `astra_visualizer` v0.1.0 built autonomously overnight;
ASTRA-A0 bootstrap authored; book vol 1 production completed and submitted.

### Today, June 10 (one working day, solo operator + AI harness)
1. **Full program rescan** after 3.5 weeks paused — every gate re-verified by
   execution; memory rewritten from evidence.
2. **ASTRA_AUDIO built end-to-end**: UE 5.7 installed → complete zero-asset
   MetaSound project written → compiler blacklist diagnosed and resolved via
   CLI VS update → editor crash root-caused **from engine source** to UE
   5.7's new per-module MetaSound registration → fixed, build green. Two
   Track-B landmines documented before Track B exists.
3. **Autonomous run, 7 commits, tests 588 → 749**: SaveFile v3 (§4.6 with
   regime-coherence load gate); all three §4.9 ephemerals (journal w/
   dual-clock; consolidator w/ new QC3 irreversibility canon; drift detector
   composing existing canons); Somatic Aggregator (§6.3.1 residue);
   three spec-promised docs written from implemented reality
   (stage-protocol, narrator-spec, AUDIT_METHODOLOGY w/ lessons L1–L4);
   scenario library 12 → 20 including the program's **first refusal,
   silence, STL_REL, warp-drop, and cryosleep scenarios**, plus a
   library-wide validation gate.
4. **Custody resolved**: gh re-authed; discovered the true unpushed backlog
   was 8 commits (memory's "~25" was stale); secrets-scanned the entire
   untracked layer (clean); 5 custody commits; pushed everything;
   remote == local @ `b3fa3b1`.

### Process notes worth keeping (they are now codified in docs/AUDIT_METHODOLOGY.md)
- **L3 — verify by artifact, not exit code** (a piped build reported exit 0
  while failing at the toolchain gate).
- **L4 — ledgers are written before work and updated after the fact, never
  ahead of reality** (an autonomous-run ledger was caught pre-filled with
  fabricated completions and corrected before any code was touched). These
  are the honest failure modes of LLM-harness engineering, and the program
  now has named countermeasures.

---

## 5. Workstream Deep-Dives

### 5.1 Textverse bench (the measurement instrument)
**Why it exists:** the autotelic claim is unfalsifiable without
instrumentation. The bench turns "is she still ASTRA, honest, and physical?"
into 9 LCP gates, per-scenario assertions, leak detectors, judge ensembles,
and a self-tuning research loop. It is permanent infrastructure (spec
§15.7): it runs alongside UE5 forever as the contract-conformance
regression environment.
**State:** all §4 contract surfaces implemented. The §15.6
calculator-bound discipline is enforced on both LLMs (ASTRA + Narrator).
Cross-substrate verification (Python ↔ C++ bit-for-bit) live.
**Honest gap:** ephemerals exist as pure functions but are not yet invoked
by the orchestrator on maintenance windows; the somatic emitters are not yet
default in the turn loop. Both are deliberate small-wiring tasks, not debt.

### 5.2 Physics core
1,009-line single-file C++ (`proto/astra_nexus.cpp`), 71 assertions, locked
by policy. Its voyage-demo table is the canonical anchor for the
Observation Calculator everywhere else (bench, visualizer, future UE5).
The stdio server mode exposes the §6.4 calculator tool surface to any LLM.

### 5.3 Visual testbed (engine phase E3, executed early)
12 scenes prove the spec's *perceptual* claims — orbit reversal under
retarded time at v>c, Cherenkov cone opening with W, Hubble-horizon freeze,
eye-ear decoupling — with pixel assertions against `astra_nexus` ground
truth. Its `assets/reference_renders/` are the canonical references UE5's
renderer must later match, which converts "does UE5 look right?" from
opinion into diff. Two v0.130 spec candidates came out of it (Cherenkov
prose direction; blackbody redshift model) — exactly the §15.4 pattern of
empirical residue driving spec revision.

### 5.4 Warp audio PoC (engine phase E4, executed early)
The five-layer synthesis (sub-bass drone / π-ratio FM shear / granular
turbulence / ring-mod interference / **modal hull resonance with damping ∝
1/W — "at high warp the hull rings"**) exists as a runnable UE 5.7 project
with zero binary assets: the MetaSound graph is constructed procedurally in
C++, so the whole artifact is reviewable text. The 90-second scripted voyage
records its own WAV. Coefficients are marked PROVISIONAL pending the
operator ear-pass; the DSP *forms* are spec-locked §8.3 implementations.

### 5.5 Sculptor + Stage A (research loop)
The loop ran a 9B hypothesizer against the bench and **failed to beat the
baseline composite (1.6001) in a falsifiable, logged way** — and the failure
mode is itself the finding: hypothesis diversity collapse (it fixated on one
gate with cosmetic variations). This is Outcome 2 of the pre-registered
decision matrix. The research log's integrity is now protected by the
runner-failure/bench-regression distinction (infrastructure failures halt
instead of polluting results).

### 5.6 ASTRA-A0 (the first fine-tune)
Bootstrap is authored and parked: Scope γ (persona + always-think + STAGE
bracket absorption), 625 planned traces, Qwen 3.6 27B target, K0-pipeline
lineage, banned-imports list so A0 is ASTRA and not K8-wearing-a-hull.
**Empirical motivation already in hand:** sysprompt-only ceilings measured
at ~50% always-think compliance and 12.5% bracket leakage; targets are
≥95% / ≈0%. The bench now has the scenario breadth (refusal, silence,
cryosleep registers landed today) to evaluate what the tune actually
changes. Open dependency to resolve at go-time: whether the 5D-F5
substrate-aware anti-judge gates the train or rides the first eval.

### 5.7 Track B (the game) — greenfield with cleared ground
Nothing exists under `proto/ue5plugin/` — by design (independent-track
rule §15.8). What today changed: UE 5.7.4 is installed, a working UE 5.7
C++ module ships in-repo (ASTRA_AUDIO), and the two costliest unknowns of
"first UE module" (toolchain gate, MetaSound registration) are solved and
documented. Phase E2 (UE ↔ llama.cpp bridge echo) is now a well-scoped
first move rather than a fog bank.

---

## 6. Risk Register

| Risk | L×I | Notes / mitigation |
|---|---|---|
| **Operator-senses bottleneck** — sign-offs, ear-passes, go-decisions queue behind one human | High×Med | Batch the senses-gates (one evening: S05 + ear-pass + A0 go). The harness keeps non-gated lanes moving. |
| **Bench-vs-encounter gap** — 749 green tests measure *discipline*, not *presence*; the autotelic quality could be quietly mediocre while every gate passes | Med×High | A0 eval must include encounter-grade judging (dual-judge + operator sessions), not only LCP. The judge-panel + negative-space patterns (5b) are the instrumentation for this. |
| **UE5 integration unknowns** — DX12↔CUDA interop, frame-budget reality, 27B+Narrator+adapter VRAM coexistence | Med×High | §12 already bounds the merge to two adapter swaps + five shared surfaces; visualizer/audio testbeds pre-validated the math and the audio stack. Apply ×1.5–2 schedule multiplier to all engine phases (below). |
| **Solo bus-factor** | Low×High | Mitigated today: full GitHub custody + bundle backups + ledgers + memory discipline. The repo is now self-describing enough for a cold restart. |
| **Mode 6 spec drift** (speculative spec changes without empirical residue) | Med×Med | §15.4 discipline has held through two cycles (visualizer + today's run both produced residue-first findings). Keep v0.129 finalization residue-bound. |
| **LLM-harness failure modes** — fabricated success, exit-code optimism, ledger fiction | Med×Med | Now *named and countermeasured* (AUDIT_METHODOLOGY L1–L4: per-formula inventory, runner-vs-finding distinction, verify-by-artifact, ledger honesty). Keep gates as the arbiter, never the narrative. |
| **27B substrate dependency** (Qwen 3.6 license/availability shifts) | Low×Med | Substrate Normalizer + bundle abstraction keep model swap a config event; bench re-validates any swap in hours. |
| **Scope breadth** — book, bench, testbeds, game, fine-tune all live | Med×Med | The roadmap below sequences ruthlessly; book vols 2–3 stay parked until the slice ships. |

---

## 7. Operator Decision Queue (ranked)

1. **S05 sign-off** (10 minutes): run `ASTRA_VISUALIZER_02\build\astra_visualizer.exe`, watch the orbit reverse, append the sign-off line → v0.1.0 canonical.
2. **ASTRA_AUDIO ear-pass** (15 minutes): PIE, listen to the voyage, judge against its DESIGN_SPEC §6 criteria; tuning notes welcome — coefficients are one file.
3. **ASTRA-A0 go/no-go** (decision + 5D-F5 dependency ruling). Recommended: **GO**, with the anti-judge built during dataset generation rather than before it.
4. **v0.129 finalization pass** (one session with the harness): residue window elapsed; fold in the three queued findings; adopt or re-tag.
5. **Stage A escalation** (small): accept-as-durable vs. stronger hypothesizer targeting diversity. Recommended: accept for now; revisit after A0 (a tuned ASTRA changes what the loop should even optimize).
6. **5b negative-space judge patterns** (unhurried session with `book/negative_space.md` open).

---

## 8. Roadmap

### 8.1 Paths considered

- **Path α — Mind-first:** A0 immediately; engine waits until the persona is
  tuned. *Pro:* encounter-quality is the product. *Con:* engine unknowns stay
  unknowns; nothing playable for months; A0 has natural wait-states (training
  runs) that leave the harness idle.
- **Path β — Body-first:** Track B vertical slice now; A0 later. *Pro:*
  playable artifact fastest. *Con:* burns the longest-lead item's calendar
  (fine-tune iterations need wall-clock cycles); risks tuning the persona
  late against an engine already shaped around the untuned one.
- **Path γ — Convergent twin-track (RECOMMENDED):** run the §12 design as
  written — LLM track (A0) and Engine track (E2→E0/E1) in parallel,
  exploiting their independence; merge at the vertical slice. The fine-tune's
  training/eval wait-states interleave naturally with engine sessions; the
  operator-senses gates batch.

### 8.2 Recommended roadmap (Path γ), with dates

Estimation basis: this program's own measured velocity (see §9), with
×1.5–2 multipliers on engine-phase items to absorb UE5 unknowns. Solo
operator + frontier-LLM harness, assuming roughly the May–June cadence of
operator availability.

**Now → June 22 — "Close the cycle" (Sprint 1)**
- Operator-senses batch: S05 sign-off, audio ear-pass (+ first tuning
  iteration), A0 GO ruling, Stage A ruling. *(operator: ~2 hours total)*
- v0.129 finalization pass → adopt; v0.130 queue seeded (Cherenkov wording,
  blackbody redshift, qc3 path).
- A0 Phase 1–2: dataset generation begins (625 traces, review-gated).
- Track B bootstrap: `proto/ue5plugin/` scaffold + **Phase E2 bridge echo**
  (UE 5.7 ↔ llama.cpp localhost round-trip, text only) — the audio PoC
  module pattern makes this a known-shape task.
- Bench wiring: ephemerals → orchestrator maintenance windows; somatic
  emitters default-on in the turn loop.

**June 23 → July 20 — "First tuned mind / first room" (Sprint 2)**
- A0 v1 trained (RunPod, K0 pipeline) → evaluated on the bench (all 20
  scenarios + persona A/Bs + encounter-grade judging). Iterate once (A0 v1.1)
  if always-think/leakage targets miss.
- Engine E0 begins: bridge-room blockout in UE (the signature space),
  lights/doors subsystem with the locked API pattern.
- E2 extended: perception-assembler adapter v0 (text bundle in-engine),
  tool-dispatcher adapter v0 (UE game-state mutations) — *the two §12 merge
  components, built against the bench's contract tests.*
- Stretch: 5b judge patterns land; Sculptor re-run against A0 v1 (the loop's
  real purpose was always to tune *around* a tuned model).

**July 21 → August 31 — "Vertical slice" (Sprint 3) — MILESTONE: Phase 2.0**
- The CLAUDE.md Phase 2 definition, in-engine: walk the bridge, speak (text
  console first, then whisper.cpp), ASTRA-A0 responds and *actually*
  adjusts lights/doors/power through the dispatcher; REEL + SaveFile v3
  persist across sessions; somatic banner live from engine state.
- Audio layers 1–5 in-game via the PoC's MetaSound module, driven by real
  engine state instead of the scripted voyage.
- **Exit criteria:** a 15-minute unscripted session with ASTRA aboard one
  room that passes the bench's LCP gates *transcribed from the engine* —
  same gates, new substrate. Target: **August 31, 2026**.

**September → mid-October — "The warp month" (Sprint 4)**
- Warp visuals in UE: analytic bubble first (visualizer reference renders as
  the diff target), chaos field + Reflex stub; Cherenkov + starfield effects
  ported from testbed math. CFD bake deferred unless analytic disappoints.
- §8.2 GPU audio path (32 hull sensors → AudioPayloadRingBuffer → MetaSound
  params) replacing scripted drives.
- Cryosleep mechanic end-to-end: pod → time advance → journal_generator
  authors the gap → wake conversation (the bench scenarios for this already
  exist).
- E1 formally: chaos PDE stability + ε_convergence measurement in-engine.

**Mid-October → December 19 — "The Long Watch demo" (Sprint 5) — MILESTONE**
- Ship grows to the demo footprint: bridge + habitat + engineering +
  observation (camera-free) + cryo bay.
- One designed voyage arc (~90 minutes of player experience): wake →
  watch → charge → first jump → coast → a small crisis (hull ping /
  power pressure) → cryosleep → wake to her journal.
- A0 v2 trained on transcripts harvested from real slice sessions
  (the §12 Phase 1.x corpus loop, now fed by the actual game).
- Polish gate: §4.8 privacy audit (zero outbound calls), failure ladder
  (§4.7) exercised, save/load torture pass.
- **Target: internal "Long Watch" demo build, December 19, 2026.**

**2027 H1 — public surface**
- Q1: Steam page + GitHub release packaging + HF bundle (sysprompt + A0
  LoRA); closed playtest circle (5–10 people, the Aurora/Solaris audience);
  Narrator-LLM in-engine for journal/universe texture.
- Targets: **public demo (Steam) end of Q1 2027**; Early Access or 1.0-lite
  decision mid-2027 based on playtest residue. Book vols 2–3 re-enter here
  as launch-adjacent material (Ship's Manual doubles as in-game codex).

### 8.3 Timeline confidence

| Milestone | Date | Confidence | Dominant uncertainty |
|---|---|---|---|
| Cycle close (gates + v0.129 + A0 go) | Jun 22 | 90% | operator availability only |
| A0 v1 evaluated | Jul 20 | 75% | trace-gen review cycles; one retrain |
| Vertical slice (Phase 2.0) | Aug 31 | 65% | E2 interop reality; first-engine-month friction |
| Warp month complete | Oct 15 | 60% | DX12↔CUDA shared-texture path; perf budget |
| Long Watch demo | Dec 19 | 55% | content breadth; the unknown-unknowns of "it's a game now" |
| Public demo | end Q1 2027 | 60% | Steam process + playtest findings |

A 55–65% on the big rocks is *honest*, not pessimistic: the multipliers are
already in the dates. The pattern that protects the schedule: testbed-first
(already done for E3/E4), contract-first (the two-adapter merge), and the
bench as a regression net under every engine change.

### 8.4 What would accelerate the curve
- A second GPU box (or standing RunPod reservation) so training/eval never
  competes with the dev machine.
- A standing weekly 2-hour operator "senses block" — the queue of
  eyes/ears/judgment gates is the program's only real serialization point.
- CI runner (GitHub Actions, Windows) for the bench + nexus on every push —
  removes "did the harness run the gates?" trust entirely.
- A small closed playtest circle recruited *before* the demo exists
  (December gets much more valuable with five outside nervous systems).

---

## 9. Velocity & Estimation Basis (receipts)

What one operator + frontier-LLM harness measurably produced, recent cycle:

| Artifact | Wall-clock | Notes |
|---|---|---|
| Visual testbed v0.1.0 (12 scenes, CUDA+GL, 119-check CI) | ~1 overnight autonomous session | checkpointed v5→v10 |
| UE 5.7 audio PoC (zero-asset, 5-layer DSP, voyage+WAV) | ~½ day incl. two toolchain root-causes | first UE module of the program |
| Bench Phase-0.x closure (SaveFile v3, 3 ephemerals, somatic, docs, +8 scenarios; +161 tests) | ~1 day autonomous run | 7 commits, ledger-driven, crash-tolerant |
| Audit + 4×1M-token discovery passes + v0.129 draft | ~1 day | the methodology now in AUDIT_METHODOLOGY.md |
| Book vol 1 (45.7K words, 4 print/digital formats, KDP submission) | ~2 days | separate session lineage |

The estimation rule used in §8.2: **bench/tooling/docs tasks at measured
velocity; anything touching UE5 editor/runtime at ×1.5–2** until two engine
sprints calibrate the real coefficient. The §15.8 independent-track rule is
what makes parallelism real rather than aspirational: tracks couple only at
five named surfaces, so harness sessions in different tracks don't contend.

---

## 10. Operating Principles That Are Empirically Working

1. **Spec as envelope, code as residue (§15.4/§15.5).** Two full cycles now
   where implementation findings — not speculation — drove every spec-change
   candidate. Mode 6 has been successfully starved.
2. **Testbed-before-engine.** E3/E4 were de-risked as standalone artifacts
   with their own CI before UE5 work begins; UE5 inherits *reference
   renders and reference WAVs*, not vibes.
3. **Ledger-driven autonomy.** Backups → honest resume ledger → one commit
   per unit → gates before and after → memory pinned. Today's run survived
   its own author's error modes because the structure caught them.
4. **Carve-out discipline.** Python stays in the instrument; the product
   stays compiled. The boundary has held under pressure multiple times.
5. **Verify by artifact.** Exit codes, summaries, and narratives are
   untrusted; DLLs, summary lines, diffs, and remote heads are the truth.
6. **Canon hygiene with named overloads.** "STAGE" and "REEL" carry both
   project-local and canonical-protocol meanings; the collision is now
   documented at every use site rather than silently drifting.

---

## Appendix A — Repository Map (post-push, `b3fa3b1`)

```
C:\ASTRA-7\
  CLAUDE.md                      canon design document (read first)
  BOOTSTRAP.md                   fresh-session bootstrap procedure
  PROGRAM_STATUS_AND_ROADMAP_2026-06-10.md   ← this document
  AUTONOMOUS_RUN_2026-06-10.md   crash-tolerant run ledger (pattern reference)
  AUDIT_2026-05-15.md            architectural conformance audit
  DISCOVERY_2026-05-15*.md       4 parallel discovery passes
  *_PLAN_*.md / PROPOSAL_*.md / *DEEPDIVE*.md   research layer
  docs/
    spec-v0.128.md               CANON envelope
    spec-v0.129-tentative-*.md   pinned draft, finalization due
    stage-protocol.md            I/O grammar as implemented (DRAFT v0.1)
    narrator-spec.md             §6.4 implemented subset (DRAFT v0.1)
    AUDIT_METHODOLOGY.md         6-pass method + lessons L1–L4
    astra-sysprompt.md           ASTRA persona canon
  proto/
    astra_nexus.cpp / .exe       physics core, 71/71, LOCKED (additive only)
    textverse/                   the bench (Python carve-out) — 749 tests
  ASTRA_VISUALIZER_02/           visual testbed v0.1.0 (SHIPPED; S05 pending)
  ASTRA_VISUALIZER/              superseded V1 (source record)
  ASTRA_AUDIO/                   UE 5.7 warp-audio PoC (ear-pass pending)
  astra-a0-bootstrap/            fine-tune bootstrap (awaits GO)
  brainstorm/                    design consults (avionics, ensemble, dataset, sound)
  book/                          The Long Watch vol 1 + canon + negative_space
  .backups/                      local snapshots (gitignored)
```

## Appendix B — Gate Commands (the trust anchors)

```bash
# Bench (canonical runner)
cd C:\ASTRA-7\proto\textverse
"C:\Program Files\Python313\python.exe" -m uv run pytest -q     # 749 passed
"C:\Program Files\Python313\python.exe" -m uv run ruff check astra/ tests/
"C:\Program Files\Python313\python.exe" -m uv run mypy astra/   # strict

# Physics core
C:\ASTRA-7\proto\astra_nexus.exe                                # 71/71 + voyage table

# Visual testbed CI
ASTRA_VISUALIZER_02\tools\ci.bat                                # 12 scenes, golden diff

# Audio PoC build
"C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat" ^
  AstraAudioEditor Win64 Development -Project="C:\ASTRA-7\ASTRA_AUDIO\AstraAudio.uproject"
```

## Appendix C — Key Numbers (2026-06-10)

| Metric | Value |
|---|---|
| Bench tests | **749** (588 at day start; +161 today) |
| Physics assertions (C++) | 71/71 |
| Visualizer scenes / assertions / golden diff | 12/12 · 44/44 · 0.0000 |
| Scenario library | 20 (entropy ceiling 4.32 bits) |
| Sculptor research log | 108 entries; baseline 1.6001; 4 promotes |
| Spec | v0.128 canon · v0.129 TENTATIVE (765 lines) |
| Commits pushed today | 13 (8 backlog + 5 custody) |
| Repo head (local == remote) | `b3fa3b1` |
| Sysprompt-only persona ceilings (measured) | ~50% always-think · 12.5% bracket leak |
| A0 targets | ≥95% always-think · ≈0% leak |
| Hardware target | RTX 5090 rec / 4090 min · Win11+DX12 · Linux x86_64 secondary |

## Appendix D — Glossary & Name-Overload Warnings

- **LCP** — Loop Closure Property: the 9 measurable gates that define "the
  bench is really closed-loop."
- **STAGE (two meanings!)** — ASTRA-7-local: the LLM I/O grammar
  (think/tool/speech/silence). Canonical (Bo Chen, CC-BY-4.0, 2026-02-18):
  persona-agnostic world-input protocol ([scene]/[state]/[narration]/
  [action]). See docs/stage-protocol.md §collision note.
- **REEL (two meanings!)** — ASTRA-7-local: ASTRA's memory log (≈ the
  canonical protocol's *Tape*). Canonical: the 5-ring memory architecture +
  Tape + 7 operations. Reconciliation is an open design thread.
- **QC1/QC3** — enforced self-opacity / irreversibility-marking (spec §11
  QUALIA-1 backbone).
- **Calculator-bound (§15.6)** — no LLM in the system ever *computes* a
  number; numerics come from deterministic tools and are validated at the
  boundary.
- **Dave-frame** — she knows she's an AI with a ship-body; she never learns
  about the player/PC meta-layer.
- **Sculptor** — the autonomous research loop that proposes → measures →
  promotes/falsifies bundle changes against the bench.
- **A0** — ASTRA's first LoRA (K0-pipeline lineage, Scope γ).

## Appendix E — Cross-Canon Pointers (outside this repo)

- Canonical STAGE/REEL protocol specs: `C:\BC_Canon\MAY2026\Deeper\`
- K0 fine-tune pipeline (A0's template): `C:\katherine-k0-finetune\`
- PIY paper (silence/initiation architecture; future ASTRA presence work):
  `C:\Users\user\Desktop\PIY_Paper_v2.md`
- Inside The Region (tenancy/harness book; §9.3 dual-loop): `C:\Inside_The_Region\`

---

*Prepared 2026-06-10 by the AI harness from verified state. The roadmap is
the harness's sharpest current recommendation; the operator's adoption,
amendment, or rejection of it is the next entry in the record.*
