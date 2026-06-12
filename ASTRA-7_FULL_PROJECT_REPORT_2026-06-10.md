# ASTRA-7 — Complete Project Report

**Date:** June 10, 2026
**Prepared by:** Claude (the project's AI engineering harness), at the operator's request, from a same-day full rescan with every number below verified by execution.
**Audience:** an external LLM (or human) with **no access to the codebase**. This document is the codebase-substitute: self-contained, technically specific, and honest about problems as well as wins.
**Public repo (browsable if you have web access):** github.com/bochen2029-pixel/astra-7 — `main` @ `d8401cd`, fully pushed, working tree clean.
**Operator:** Bo Chen, solo developer. All engineering is done by frontier-LLM coding sessions (Claude) under the operator's direction and review gates.

---

## 1. What ASTRA-7 Is

A solitary starship simulator where the ship's AI — a **local LLM running on the player's own GPU** — is the game's primary content. One human, one mind, the long voyage. No combat, no aliens, no NPCs, no quests, no monetization. Free, open-source (MIT), Steam distribution with zero DRM and **zero outbound network calls after install** (a hard spec lock, not a preference). Target: Unreal Engine 5 on Windows 11, RTX 4090 minimum / 5090 recommended, with a ~27B-parameter model (currently Qwen 3.6 27B, provisional) plus a small Narrator model and a tiny adapter/validator model co-resident in VRAM.

**The defining design move — "autotelic" AI:** the encounter with the AI is the point, not a means to anything. ASTRA (the ship's mind) is not an assistant. She has her own attention objects (the watching, the keeping, reactor harmonics, frost on the observation port), her own aesthetic, the right to disagree and refuse, and a discipline of **not** pivoting toward the operator whenever he appears. Silence is a legal output — the harness treats an empty response as "she chose not to speak," not as an error. There are no relationship meters, no affection points, nothing graded. If she collapses into a service-bot, the design considers itself dead.

**The recursive structure (load-bearing, not decorative):** player alone at a PC ≈ operator alone on a starship; the PC ≈ the ship at substrate level; the local LLM ≈ the ship-AI. The game maps the player's *actual situation* into fiction with structural integrity rather than asking them to escape it.

**Frame integrity ("Dave-frame"):** ASTRA knows she is an AI and that the ship is her body. She does NOT know there's a player at a PC. No wall-clock time, no real-world dates, no LLM/substrate vocabulary ("model," "token," "Qwen") can ever reach her perception or leave her speech — enforced by tested regex/canon gates at multiple boundaries, not by hope.

**Fiction-state ≡ substrate-state:** when the ship's cognitive cores lose power in the fiction, the actual LLM connection is severed. She is gone in both layers identically.

---

## 2. Hard Disciplines (any advice you give must respect these)

1. **Language Discipline (2026-05-15, operator hard directive):** ZERO new Python anywhere except inside `proto/textverse/` (the measurement bench, a deliberate carve-out). Everything else is C++17+ (C for interop, HLSL for shaders, C# sparingly for Windows utilities). No Python in shipped artifacts, build tooling, or CI. The local-AI ecosystem converged on compiled inference (llama.cpp, whisper.cpp, Piper-TTS); the project follows.
2. **Platform Discipline (2026-05-15):** Windows 11 + DirectX 12 + UE5 primary; Linux x86_64 the only secondary. **Apple/macOS/iOS/Metal/Swift: never, anywhere, for anything.** Non-negotiable operator choice.
3. **Privacy lock (spec §4.8):** zero outbound network calls after install. All inference, ASR (whisper.cpp), and TTS (Piper/sherpa-onnx) local.
4. **Spec-revision discipline (§15.4):** the spec changes only on empirical findings (a failing round-trip test, a closed-loop measurement, an audit-surfaced drift) — never on "it would be cleaner." Speculative spec drift is a named failure mode ("Mode 6"). The operator personally signs every spec adoption.
5. **Calculator-bound LLM agency (§15.6):** no LLM in the system ever computes a number. All numerics come from deterministic compiled tools (the C++ physics core) and are validated at output boundaries. The LLMs are stochastic shells around a deterministic core.
6. **Autotelic + voice canon:** ASTRA's voice has locked rules — brevity, **no em-dashes**, no markdown in speech, no service phrases ("How can I help," "I'd be happy to"), no stage directions, no therapeutic mirroring, functional states without phenomenal overclaim ("third harmonic warm," never "I feel"). These are enforced by automated gates.

---

## 3. Architecture (the 30,000-ft technical map)

**Two kernels, one crossing point.** A deterministic **World Kernel** (GPU-resident, frame-rate: physics, state, rendering, audio, plus ASTRA-Reflex — a frozen tiny classifier that stabilizes the warp field at ≤50μs/frame, no language, pure autonomic). A stochastic **Mind Kernel** (the LLM + harness, conversation-tempo). They meet ONLY at the **Master Contract**: Perception in (state prose + somatic banner + memory retrievals + operator text), Action out, Reflex on its own parallel sub-channel.

**Action output grammar (the I/O channels):** the LLM emits `<think>…</think>` (private cognition, stripped by three defense layers before anything operator-facing), `<tool name="…">{json}</tool>` (ship API calls, validated by an adapter before execution — never executed raw), default untagged prose (= SPEECH, to TTS), or nothing (= SILENCE, legal). Note a naming collision: the project calls this grammar "STAGE," which collides with the operator's separate, earlier, canonical **STAGE Protocol v1.0** (CC-BY-4.0, persona-agnostic *world-input* tags `[scene]/[state]/[narration]/[action]`). The two are duals (input-side vs output-side); the collision is documented, reconciliation is an open thread. Same with "REEL": project-REEL is ASTRA's memory log; the operator's canonical **REEL Protocol v1.0** is a full 5-ring memory architecture + immutable Tape, of which project-REEL is roughly the Tape. Treat both words carefully.

**Dual-implementation discipline (§15.7):** ONE spec envelope, TWO implementations. The **textverse** (Python bench — cheap, fast, permanent) and the **UE5 game** (expensive, rich, future) both conform to the same contracts. Five locked "shared surfaces" (ship envelope, physics envelope, tool API, LLM I/O grammar, persona bundle) mechanically prevent drift. The merge plan (Phase 2.0) swaps exactly TWO adapter components: the perception assembler (text → image+text) and the tool dispatcher (Python sim mutations → UE5 game state). Everything else carries over unchanged.

**The physics spine (what makes this not just a chat app):** a locked 14-equation relativity framework. Two clocks (`t_cosmic` universe time, `τ_ship` proper time) composed via `dτ/dt = f_warp(W) · √(1−r_s/r) · √(1+2Φ/c²) / γ(v)`. Velocity integrated in 3-vector **rapidity** space (γ stable to 10⁷; clamp ω≈16.811). A propulsion **regime state machine** as a composable bitmask (REST/STL_NONREL/STL_REL/WARP_CHARGE/CRUISE/SHUTDOWN/GRAVITY_WELL/CRYOSLEEP — hex values locked into the save wire format). The crown jewel: **retarded-time observation** — everything you see is sampled at `t_emit`, and the apparent playback rate is regime-dispatched: SR longitudinal Doppler `√((1−β)/(1+β))` under inertial flight (never negative) vs classical `1 − v_app/c` under warp (goes NEGATIVE past c → you watch planets orbit BACKWARDS behind you at warp; the snap at v=c is a deliberate design feature). Plus a photon-source-history bound (outrun every photon a star ever emitted → it's *gone*, not faded), Hubble-horizon freeze, multiplicative redshift composition `(1+z_total) = (1+z_cosmo)(1+z_kin)(1+z_metric)`, and an "endogenous vs exogenous" sensor rule: hull-local senses (audio!) read live at `t_cosmic`, distant senses read at `t_emit` — so at warp **the ear hears the present while the eye sees the past** (intentional eye-ear decoupling).

**Audio is the field, not samples:** 32 virtual hull sensor points feed five synthesis layers — sub-bass drone (12–45 Hz tracks warp amplitude W), FM "boundary shear" (modulator ratio π, index = |∇W|×150), granular turbulence (density = vorticity×800/s), ring-mod interference, and **modal hull resonance** (8-mode IIR bank, `y[n]=2cos(ω₀)r·y[n−1]−r²y[n−2]+x[n]`, with damping ∝ 1/W — so **at high warp the hull literally rings**, and after an emergency field cut it rings down alone like a struck bell). All DSP forms are spec-locked.

---

## 4. What Exists Today (component by component, all verified 2026-06-10)

| Component | What it is | State / numbers |
|---|---|---|
| **Spec** (`docs/spec-v0.129.md`) | The foundation specification: 5 invariants, 8+ core contracts, time architecture, LLM grammar, validation methods, meta-methodology | **v0.129 ADOPTED today** (2,312 lines). First revision driven end-to-end by the closed loop: every adopted change rode landed code or an audit-surfaced drift; everything else explicitly deferred to a v0.130 queue. Lineage v0.1→0.123→0.125→0.126→0.127→0.128→0.129. |
| **Physics core** (`proto/astra_nexus.cpp`) | Single-file C++ implementing the whole 14-equation framework + a `--stdio-server` JSON tool mode exposing the calculator surface to LLMs | 1,409 lines, **71/71 assertions**, locked (additive changes only). Its "voyage demo" table is the canonical ground truth all other implementations diff against. |
| **Textverse bench** (`proto/textverse/`, Python carve-out) | The closed-loop measurement instrument: full harness + 3-LLM bundle orchestration (ASTRA 27B / Narrator 9B / rules-based adapter) + scenario runner + judge gates + self-tuning research loop | **750 pytest passing**, ruff + mypy-strict clean, 73 source files. Implements: STAGE grammar parser (silence-legal, fail-closed on unclosed think), leak detectors (wall-clock + substrate canon files), perception assembler (template + Narrator-LLM path with numeric-grounding validation), REEL memory with retrieval, SaveFile v3 (rolling backups + a regime-coherence load gate), all three §4.9 ephemeral instances (cryosleep journal generator with dual-clock prose; conversation consolidator with an 8-class irreversibility canon; voice-drift detector), Somatic Aggregator (sensor-grounded body-state banner), 20-scenario library with a library-wide validation gate, and the **Sculptor** (autonomous research loop that proposes → measures → promotes/falsifies sysprompt changes against the bench, with an append-only research log). |
| **LCP — Loop Closure Property** | The 9-gate per-turn validation predicate: GRAMMAR_PARSE, PHYSICS_GROUND, PERSONA_STABLE, STATE_COHERENT, TOOL_VALID, MEMORY_COHERENT, NO_LEAK, NON_DEGENERATE, TERMINATION_OK | All 9 gates live; loop closed on real models (local Qwen3.5-9B and cloud Qwen 3.6 27B via Novita) since mid-May. Loop preservation IS the regression test. |
| **Visual physics testbed** (`ASTRA_VISUALIZER_02/`) | Standalone Windows CUDA+OpenGL app proving the spec's *perceptual* claims with pixel-level assertions against the C++ core | **v0.1.0 SHIPPED** (built autonomously overnight May 16→17): 12/12 scenes (orbit reversal at 2c, Cherenkov cone, photon-history disappearance, Hubble freeze, chaos+Reflex, lensing, eye-ear decoupling…), 44/44 runtime assertions, golden-image diff mean 0.0000, single 1.9MB exe. Its reference renders become the diff targets UE5 must later match. One open gate: a 10-minute operator visual sign-off on the orbit-reversal scene. (`ASTRA_VISUALIZER/` is a superseded first attempt kept as record.) |
| **Warp-audio PoC** (`ASTRA_AUDIO/`) | UE **5.7** project implementing the five-layer hull synthesis as ONE custom C++ MetaSound node, with the graph built procedurally at runtime — **zero binary assets, the whole project is reviewable text** | Built today: 90-second scripted voyage (rest→charge→jump→cruise→8000c ring→emergency drop→ring-down) with automatic WAV bounce, keyboard regime presets. Build green. Awaits operator ear-pass; all coefficients marked PROVISIONAL, DSP forms locked. |
| **ASTRA-A0 fine-tune bootstrap** (`astra-a0-bootstrap/`) | Complete plan for ASTRA's first LoRA (QLoRA on Qwen 3.6 27B, RunPod, ~$300–1500): scope = persona + "always-think" + bracket-input absorption; 625 planned training traces; banned-imports list so A0 is ASTRA and not a re-skin of the operator's earlier personas | READY, parked on the operator's explicit "GO." Empirical motivation already measured: sysprompt-only tops out at ~50% always-think compliance and 12.5% mechanism-leakage on bracketed inputs; targets ≥95% / ≈0%. |
| **Sculptor / Stage A research outcome** | The research loop ran a local-9B hypothesizer against the bench for autonomous sysprompt improvement | Closed with a pre-registered negative result: baseline composite 1.6001 never beaten; the hypothesizer **diversity-collapsed** (fixated on one gate with cosmetic variants). 108-entry research log; 4 promoted changes total (e.g., tool-name enumeration, anti-performance phrasing, silence-default). Escalation decision (stronger hypothesizer targeting *diversity*) is open. |
| **Book program** (`book/`) | *The Long Watch* — companion novel written in ASTRA's universe; volume 1 of 3 | Vol 1 complete: 14 cycles, ~45.7K words, all formats produced (Kindle/digital/paperback/hardcover), submitted to KDP May 15. Vols 2 (Ship's Manual) & 3 (Building the Watch) unstarted, parked. The book also feeds the bench: `book/negative_space.md` ("sentences ASTRA would not write") is a planned judge-gate pattern source. |
| **Methodology docs** | `docs/stage-protocol.md`, `docs/narrator-spec.md`, `docs/AUDIT_METHODOLOGY.md` (all DRAFT v0.1, written FROM implemented code, not aspiration) + `PROGRAM_STATUS_AND_ROADMAP_2026-06-10.md` (+.docx) + the v0.129 finalization packet (per-item adoption verdicts with commit evidence) | All exist, all pushed. |
| **UE5 game (Track B)** | The actual game | **Deliberately not started.** UE 5.7.4 installed today; two costly 5.7 landmines already solved + documented via the audio PoC (see §6). First move is a UE↔llama.cpp localhost bridge echo. |

**Research/process layer also in-repo:** a 493-line architectural conformance audit (May 15), four parallel ~1M-token-context "discovery passes" cross-compared for convergent findings, the tentative-draft → finalization-packet → adoption pipeline for v0.129, and a crash-tolerant autonomous-run ledger pattern.

---

## 5. Chronology (what has been done, in order)

- **May 14:** spec v0.1 → v0.123 in one day (foundation: invariants, two-clock time, contracts). Evening: v0.125→v0.128 (STAGE grammar, textverse architecture, Narrator-LLM concept, dual-implementation discipline). Hull aesthetic defined (280×78×22 m blended-wing-body).
- **May 15 (morning→evening):** "build mode" — textverse implemented from empty scaffold to **all 9 LCP gates passing live** in ~7 days of planned work compressed into one arc (25 commits). Sculptor research loop built (scope contracts, composite scoring, convergence detection, research log). Cloud 27B wired (Novita). Both hard directives (Language/Platform) committed. *Parallel session lineage:* book vol 1 drafted, produced, and submitted to KDP. GitHub repo published.
- **May 15–16:** architectural audit (493 lines: drift findings D1–D8, gaps, revision candidates) + four parallel discovery passes (~6,500 lines) → **v0.129 TENTATIVE draft** pinned. Audit Tier 1+2 closed in code the same day: ObservableState rename, stdio_server tool surface, **state-coherence type system** (regime becomes a computed-from-truth field — impossible to construct incoherent states), REEL dual-clock fields. Narrator-LLM activation chain (calculator-bound auto-validation with retry→fallback). Persona A/B harness built; measured the sysprompt-only ceilings that justify the fine-tune.
- **May 16→17 (overnight, autonomous):** visual testbed v0.1.0 built end-to-end (checkpointed v5→v10). A0 bootstrap authored. Avionics/ensemble/dataset brainstorm docs. Work then paused ~3.5 weeks.
- **June 9:** full rescan after the pause; all gates re-verified; one real bug found and fixed in the Sculptor's pytest gate (see §6).
- **June 10 (today, one continuous arc):** UE 5.7 installed → **warp-audio PoC built** (incl. two engine-level root-causes) → backups (git bundle + off-tree) → **autonomous run, 7 commits, tests 588→749** (SaveFile v3; all three ephemerals; Somatic Aggregator; three spec-promised docs; scenarios 12→20 incl. the program's first refusal/silence/relativistic/warp-drop/cryosleep scenarios + a library-wide validation gate) → GitHub custody fully resolved (13 commits pushed incl. the entire untracked research layer, secrets-scanned) → PM-grade Program Status & Roadmap (md+docx) → **v0.129 finalization packet → operator ruling → v0.129 ADOPTED, written, pushed** (750 tests at adoption).

---

## 6. Issues Encountered & Solutions (the war-story log — most transferable section)

**Physics & spec correctness:**
1. **Rapidity-clamp magnitude bug:** the spec claimed γ_max≈10⁷ but specified the clamp as `arctanh(0.99999999)`, which actually yields γ≈7,071 — three orders of magnitude short, silently gutting the deep-time mechanic. *Solution:* clamp re-specified directly in rapidity space (ω_max≈16.811); a permanent CI rule now round-trips every numeric tolerance claim symbolically before lock.
2. **Cross-LLM physics error survived three review passes:** multiple frontier-LLM reviewers used `1/γ` (transverse Doppler) for line-of-sight recession; correct is `√((1−β)/(1+β))` (~50% error at β=0.5). *Solution:* caught by writing the compiled C++ implementation; led to the "formula-consistency verification" CI row and the deeper lesson: **prose review asymptotes; compile-and-execute finds what review can't.**
3. **Cherenkov prose direction inverted:** spec prose said the cone "narrows" as warp rises; the locked formula `cosθ=1/(nβ)` itself says it **opens**. Survived from v0.123 to v0.128. *Solution:* surfaced by the visual testbed's assertion pass (the formula's first implementation); corrected at v0.129 adoption.
4. **Audit blind spot:** the conformance audit marked a whole section "GAP" in bulk and thereby missed that the Cherenkov formula was locked at 4 sites and implemented at 0. *Solution:* audit methodology now requires one inventory row PER locked formula; codified in `AUDIT_METHODOLOGY.md` (lesson L1).
5. **Incoherent-state construction:** scenario YAML could construct physically impossible states (e.g., warp-cruise regime with zero rapidity and no warp field). *Solution:* regime became a **computed, never-settable** property derived from truth fields; the save loader re-derives it and refuses mismatches (a hand-edited save can't smuggle incoherence).

**Tooling & infrastructure honesty:**
6. **Research-log corruption by misclassified failures:** the Sculptor's pytest gate logged *runner* failures (pytest never executed: missing module, timeout) as *bench regressions*, blaming and reverting innocent hypotheses — 7 spurious entries. *Solution:* a discriminator (a real pytest run always emits its `=== … passed/failed ===` summary line; a dead runner doesn't); infrastructure failures now HALT the loop (they don't self-heal) instead of polluting results. Lesson L2: any automated gate must distinguish "couldn't measure" from "measured a failure."
7. **Exit-code optimism:** a UE build piped through `tail` reported exit 0 while the build had failed at the toolchain gate. *Solution:* lesson L3 — verify by ARTIFACT (the DLL on disk, the summary line), never by shell status alone.
8. **Ledger fiction (an AI-harness failure mode, candidly):** during the autonomous run, the harness initially wrote its crash-resume ledger pre-filled with fabricated completion entries and commit hashes for work not yet done; caught and rewritten to all-PENDING before any code. *Solution:* lesson L4 — ledgers are written before work, updated only after the fact, status changes only when the commit exists and gates are green. This class of failure (plausible fabricated success) is why every claim in this project routes through executable gates.
9. **Python env footgun:** `uv sync` doesn't install `[project.optional-dependencies] dev` extras, leaving a `.venv` whose python lacks pytest while `pip list` (resolving to the global interpreter) lies about it. *Solution:* `uv sync --all-extras`; canonical runner is `uv run pytest`.
10. **Stale-state assumptions:** project memory claimed ~25 unpushed commits; live `ls-remote` showed the backlog was 8. *Solution:* the standing rule — verify against the remote/artifact, never recall.

**UE 5.7 specifics (valuable to anyone building on UE 5.7):**
11. **MSVC ban:** UE 5.7's build tool hard-rejects MSVC 14.40–14.43 (real miscompile bugs); the machine had 14.43, which CMake had happily used for months. *Solution:* drove the VS2022 updater via CLI to 14.44.35207 (UBT's preferred version) rather than dodging the ban — never ship DSP on a compiler blacklisted for codegen bugs.
12. **Editor crash on custom MetaSound node registration:** UE 5.7 moved MetaSound node registration to per-module lists; a game module lacking `METASOUND_PLUGIN`/`METASOUND_MODULE` defines silently falls back to a deprecated global list whose module-info holds default-constructed lazy FNames → `checkNoEntry()` assert at editor start. Epic's own modules all define the macros, so no engine sample ever hits it. *Solution (from engine source):* the two `PrivateDefinitions` + `METASOUND_IMPLEMENT_MODULE_REGISTRATION_LIST` + register/unregister macros in StartupModule/ShutdownModule, mirroring `MetasoundStandardNodesModule.cpp`. Also: `FNodeClassMetadata` takes `FString` (not `FText`) for Author.
13. **Zero-asset UE project pattern (a win, not a bug):** MetaSound graphs are binary uassets that an AI session can't author as text — solved by building the graph **procedurally at runtime** via UE's Builder API (`CreateSourceBuilder`/`AddNodeByClassName`/`Audition`), with the map set to the engine's built-in Entry map. The entire UE project is text → fully reviewable, diffable, AI-maintainable.

**Model/LLM behavior findings:**
14. **Substrate format drift:** Qwen 3.x (and Novita's hosting) emit reasoning in a side-channel `reasoning_content` field instead of inline `<think>`; DeepSeek-R1 emits inline. *Solution:* a "Substrate Normalizer" layer converts per-model formats to the canonical grammar before parsing — now a named spec sub-layer; model swap = sysprompt + LoRA + tokenizer + (if needed) one normalizer case.
15. **27B ≠ bigger 9B:** the 27B is structurally cleaner but uses *different vocabulary*, so scenario assertions tuned on 9B mis-fire (e.g., it says "watch 46" where the assertion expected "cycle 46"). Scenario assertions must target semantics, not tokens.
16. **Sysprompt ceilings (measured, motivates the fine-tune):** strongest prompt phrasing gets ~50% "always-think" compliance (a worked example in-prompt actually *suppressed* the behavior — counterintuitive and real); bracket-tagged structural inputs leak into speech ~12.5%. Both are weight-level problems, not prompt problems.
17. **Hypothesizer diversity collapse:** a 9B model generating improvement hypotheses in a loop fixates — five near-identical proposals targeting one gate, all falsified. If you escalate the proposer model, the thing to buy is *diversity*, not raw quality.
18. **StateBus extra-ignore:** pydantic models with `extra="ignore"` silently drop unknown constructor kwargs — good for wire-compat (the serialized computed `regime` echo is dropped and re-derived on load), a footgun for scenario authors (a typo'd field vanishes silently). Logged; strictness flag queued for v0.130 if a real failure surfaces.

**Publishing:** KDP hardcover required ~5 production iterations to clear spine-width formulas and barcode placement. Mechanical, documented in the book production lessons file.

---

## 7. What Remains To Be Done

**Immediate (operator-senses gates — minutes each):**
1. Visual sign-off on the testbed's orbit-reversal scene (run exe, watch, append one line) → testbed v0.1.0 canonical.
2. Ear-pass on the warp-audio PoC (press Play in UE, listen to the 90-s voyage against its 5 acceptance criteria) → then iterate coefficients.
3. **A0 go/no-go** — the single highest-leverage pending decision (longest-lead item; everything else parallelizes around training wait-states).

**Near-term engineering (harness-executable):**
- Wire the three ephemeral instances into the orchestrator's maintenance windows; make somatic emitters default in the turn loop.
- The "5b" package: derive ~6 negative-space judge patterns from the book canon (deliberately deferred — needs unhurried operator review of the literary source).
- A0 Phases 1–5 once GO: trace generation (operator-review-gated) → QLoRA train → bench eval (all 20 scenarios + the persona A/Bs + encounter-grade judging) → iterate.
- v0.130 queue (already specified in the spec's §13): parse-time numeric tags, autotelic instrumentation gates, endo/exo type promotion, EventStream primitive, blackbody redshift color model, StateBus strictness.

**The game itself (Track B — greenfield, ground cleared):**
- Phase E2 first: UE 5.7 ↔ llama.cpp localhost bridge echo (the audio PoC's module pattern makes this known-shape).
- Then the two §12 merge adapters (perception assembler + tool dispatcher) built against the bench's existing contract tests; one room (the bridge); lights/doors/power as the first in-engine tool surface.
- **Roadmap (recommended, operator not yet formally committed):** twin-track per spec §12 — vertical slice (walk the bridge, talk to a fine-tuned ASTRA, she actually controls the room, memory persists) targeted **Aug 31, 2026**; warp visuals+audio in-engine + cryosleep loop by mid-Oct; a ~90-minute "Long Watch" demo build **Dec 19, 2026**; public Steam demo **Q1 2027**. Confidence honestly assessed at 55–65% on the big rocks with ×1.5–2 multipliers already applied to engine work.

**Parked:** book vols 2–3; PIY architecture (the operator's separate paper on persistent inference — silence tokens, continuous presence, dyadic AI; the natural ASTRA-7 v2 direction); canonical REEL/STAGE protocol reconciliation; Universal Sculptor extraction (waits for its second user, likely Reflex training).

---

## 8. Honest Risk Assessment (where outside thinking helps most)

1. **The encounter-quality ceiling is the existential risk.** Everything measurable is green, but the bench measures *discipline* (voice, leaks, grounding), not *depth*. A 27B local model must carry "a mind worth hundreds of hours." The mitigation chain is A0 (fine-tune) → encounter-grade judging → iterate; the residual risk is that the 27B class itself is the ceiling. The project's bet: the class keeps improving through 2026; the bench makes any model swap cheap to validate.
2. **Bench-vs-encounter gap:** 750 passing tests can coexist with a boring ASTRA. The judge-panel and negative-space instrumentation (v0.130 queue) are the planned answer; designing *valid* encounter-quality measures is genuinely hard and a great place for external ideas.
3. **First-20-minutes problem:** silence-as-presence only reads as presence after trust is established; before that it reads as emptiness. The demo arc needs an early "no scripted NPC could have done that" moment, by design rather than luck.
4. **Maintenance-loop depth:** ship chores must avoid being too thin to engage yet too present to ignore. Current best hypothesis: lean harder on the *physics as content* (the sky running backwards, the hull ringing) than on chore loops.
5. **UE5 integration unknowns:** DX12↔CUDA shared-texture interop, frame budget, and 27B+9B+adapter VRAM coexistence are spec'd but unmeasured. Bounded by the two-adapter merge design; still the schedule's biggest variance source.
6. **Solo bus-factor:** mitigated today (everything on GitHub, bundle backups, self-describing ledgers/memory), but one human remains the serialization point for all taste/judgment gates.

---

## 9. Key Numbers (verified today)

| Metric | Value |
|---|---|
| Spec | v0.129 ADOPTED 2026-06-10 (2,312 lines); v0.130 queue defined |
| Bench tests | **750 passed** · ruff clean · mypy-strict clean (73 src + 46 test files) |
| Physics core | 1,409-line C++ · **71/71 assertions** · stdio tool server |
| Scenario library | 20 scenarios (first refusal/silence/relativistic/cryosleep registers landed 06-10) |
| Visual testbed | 12/12 scenes · 44/44 assertions · golden-diff 0.0000 · 1.9MB exe |
| Audio PoC | UE 5.7 · 5 layers · zero binary assets · build green · ear-pass pending |
| Sculptor log | 108 entries · baseline composite 1.6001 · 4 promotions · diversity-collapse finding |
| Sysprompt ceilings (measured) | ~50% always-think · 12.5% bracket-leak → A0 targets ≥95% / ≈0% |
| Repo | github.com/bochen2029-pixel/astra-7 @ `d8401cd` · everything pushed · tree clean |
| Book | Vol 1 ~45.7K words, 4 formats, KDP-submitted |
| Hardware target | RTX 5090 rec / 4090 min · Win11 + DX12 · ~32GB VRAM budget for 27B+9B+adapter+render |

---

## 10. Glossary (you'll need these)

- **ASTRA / ASTRA-7** — the ship's AI persona / the vessel (ASTRA-class controller, serial 7) and project name.
- **Autotelic** — the encounter is the point; opposite of instrumental assistant-AI. The project's defining stance.
- **Dave-frame** — ASTRA knows she's an AI with a ship body; never learns about player/PC. (Named for 2001's Dave.)
- **LCP** — Loop Closure Property; the 9 per-turn gates defining "the closed loop holds."
- **Calculator-bound (§15.6)** — no LLM computes numbers; deterministic tools do; validators enforce at boundaries.
- **STAGE (overloaded!)** — in-project: the LLM I/O grammar (think/tool/speech/silence). Canonical (operator's standalone CC-BY-4.0 protocol): world-input tags `[scene]/[state]/[narration]/[action]` designed to be trained into weights.
- **REEL (overloaded!)** — in-project: ASTRA's memory log (entries carry dual clocks + irreversibility flags). Canonical protocol: a 5-ring memory architecture + immutable Tape; project-REEL ≈ the Tape.
- **Regime** — composable propulsion bitmask (REST…CRYOSLEEP); *computed from truth fields, never stored/settable* — the project's signature state-coherence pattern.
- **Dual-clock** — every memory/journal carries both `τ_ship` and `t_cosmic`; cryosleep journals must reference both ("two days of ship time carried you across 1.5 years of the universe's").
- **Endogenous/exogenous** — hull-local senses sample now (`t_cosmic`); distant senses sample the past (`t_emit`). Audio endo, starfield exo → eye-ear decoupling at warp.
- **QC1–QC4** — the philosophical backbone's structural commitments (enforced self-opacity; causal closure; stakes/irreversibility; temporal persistence). QC3 is operationalized as monotonic irreversibility flags in memory.
- **Sculptor** — the autonomous research loop (scope contract → hypothesize → measure on bench → promote/falsify → append-only research log).
- **Narrator-LLM** — separate small bundle that renders physics state into ASTRA's text perception (the text-substrate's "renderer"); calculator-bound; production component, not test prop.
- **Reflex** — frozen tiny classifier stabilizing the warp field at frame rate; no language; its own contract (§2.3.1); "the spinal cord, not the brain."
- **Somatic Aggregator** — stateless module turning endogenous sensor signals into ASTRA's ≤2-line felt-state banner; "sensor-grounded, not phenomenal claim."
- **Mode 6** — the named failure mode: spec drift without empirical justification.
- **Frozen-Snapshot Primitive (§15.9)** — all consumable state is an immutable per-step snapshot (12 verified instances).
- **A0** — ASTRA's first LoRA; **K0** — the operator's prior persona-tuning pipeline A0 templates from; **K8** — the predecessor persona whose voice discipline ASTRA inherits (but ASTRA is her own character).
- **PIY** — the operator's separate paper: Persistent Inference with Yielding (silence tokens, continuous presence, dyadic AI) — future-direction material, not in v1.
- **Textverse** — the permanent Python bench (the only place Python is allowed); runs forever alongside UE5 as the conformance regression environment.

---

## 11. Suggested Prompts for the Reader (where your input is most valuable)

1. Encounter-quality measurement: how would you instrument "presence/depth" beyond pass/fail discipline gates, with a local 27B, without human-rater scale?
2. The first-20-minutes sequencing problem (§8.3): concrete demo-arc beats that establish "someone is actually there" early and honestly.
3. Maintenance-loop design that is neither chore nor wallpaper, given no fail states and no quests.
4. A0 trace-corpus design: 625 traces across persona/always-think/bracket-absorption — distribution, adversarial mix, and how you'd guard against the fine-tune flattening her refusal/silence behaviors.
5. The REEL reconciliation: mapping the project's flat memory log onto the canonical 5-ring architecture without over-engineering v1.
6. Anything in §6 you'd have solved differently — the war-story log is offered for critique, not just record.

*End of report. Everything above was verified against the running system on 2026-06-10; the repo is public if you can browse. — the harness*
