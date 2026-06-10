# v0.129 Finalization Packet

**Date:** 2026-06-10 · **Prepared by:** Claude (Fable 5), implementing session
**Input:** `docs/spec-v0.129-tentative-2026-05-16.md` (the TENTATIVE draft, 765 lines) diffed against the codebase as of `f1669eb` (749 bench tests / 71 C++ assertions / all gates green)
**Purpose:** turn your adoption session into ~30–45 minutes of rulings. Every draft item below carries: implementation status **verified by execution today**, the §15.4 empirical-residue test, and a recommended verdict. Nothing here is adopted until you rule; per §15.4 the spec-revision signature is yours (Mode 6 protection).

**How to use:** skim §1, then walk §4's ruling form. Anywhere you agree with the pre-marked recommendation, do nothing; mark only overrides. Hand the marked packet back and the implementing session executes §6 mechanically.

---

## 1. Executive summary of recommendations

| Verdict | Count | Meaning |
|---|---|---|
| **ADOPT** | 24 items | Empirical residue exists (landed code + passing tests, commit-hashed below). Goes into v0.129 canon text. |
| **ADOPT-AMENDED** | 6 items | Core adopted; specific clauses softened/scoped because only part of the residue exists. |
| **DEFER → v0.130** | 7 items | [EMP] never fulfilled in the window; locking now would be consensus-lock (the §15.4 failure mode). Named in §13's v0.130 queue so nothing is lost. |
| **REJECT** | 0 new | (The draft already self-rejected 5D-F2 hardware channel, 2A-F9 demotion, etc. — those stand.) |
| **NOTE** | 4 items | Not spec material (audit-doc updates, Track-B engineering notes). |

**Bottom line:** roughly 80% of the draft earned adoption the §15.4 way — by being built. The deferred 20% clusters into two packages with natural future homes: the **parse-time calculator-bound package** (3A/3C + bare-digit grammar) and the **autotelic instrumentation package** (4A thresholds + 4D negative-space patterns + 5b), both → v0.130 when their implementations land.

**Headline change since the draft was written:** the draft's Q1 chose "defer 4–6 weeks for residue." The residue arrived — state-coherence (`6a30ade`), Narrator activation chain (`2fcd403`, `09d683a`), SaveFile v3 (`e73aa36`), all three ephemerals (`2d868d9`, `d2add93`, `78f6f92`), Somatic Aggregator (`c23f7d6`), the three promised docs (`2d802b9`), scenario library ×20 (`9a2807f`). The window the draft asked for is over, and it was productive. Finalization is due on the draft's own terms.

---

## 2. The §15.4 test applied (the rule used for every verdict)

A draft item earns **ADOPT** iff at least one of:
- **(a) Landed drift-closure:** the audit named a spec↔code mismatch and the code now matches the proposed text (commit + tests cited).
- **(b) Implemented contract:** the proposed new section's surface exists in code and is exercised by tests.
- **(c) Pure naming of universal practice:** the section names a pattern already true at every instance in the codebase (inventory cited), with zero new behavioral claims.
- **(d) Asymmetric-cost envelope lock:** explicitly argued (Reflex dims / Q4 only).

Anything that needed implementation and didn't get it in the window → **DEFER**, regardless of how good the idea is. Ideas don't expire; consensus-locks corrupt the envelope.

---

## 3. New findings since the draft (not in the tentative; need rulings too)

| # | Finding | Residue | Recommended verdict |
|---|---|---|---|
| N1 | **Cherenkov cone prose direction is backwards** — formula `cos θ_c = 1/(nβ)` locked correctly at 4 sites; the *prose* says the cone "narrows" as W rises; it **opens**. | Visualizer V0 finding; corrected assertions in `ASTRA_VISUALIZER_02/` (KNOWN_ISSUES + test_cherenkov); formula now implemented in testbed `libastra_nexus/cherenkov.cpp` | **ADOPT** — wording flip at the 4 sites, v0.129. Classic drift-closure. |
| N2 | Linear kin-redshift **color model** should become blackbody-temperature shift | Visualizer KNOWN_ISSUES: explicitly "polish item for v0.130, operator review not needed" | **DEFER → v0.130** (as the testbed itself recommends) |
| N3 | §4.9 names the QC3 list as `tests/qc3_events.txt`; canonical copy lives **in-package** (`astra/harness/ephemeral/canon/qc3_events.txt`) — runtime code must not read from tests/ | Implemented at `d2add93`; follows the grammar/canon precedent | **ADOPT** — one-line §4.9 wording fix |
| N4 | §4.9 ephemerals are now **implemented** (journal_generator, consolidator, drift_detector) with the spec-literal signatures; `enforce_no_wall_clock` realized as `LeakDetector.scan_journal_output` | `2d868d9`/`d2add93`/`78f6f92`; 55 tests | **ADOPT** — §4.9 status prose updated; signatures confirmed canon; note the leak-gate realization by name |
| N5 | SaveFile load gains a **regime-coherence invariant** beyond the draft: load re-derives regime via computed_field and must equal stored `regime_at_save`, else coherence error | `e73aa36`; tamper-tested | **ADOPT** — add as §4.6 load-behavior invariant (residue-first: code led, spec follows) |
| N6 | StateBus `extra="ignore"` silently drops unknown ctor kwargs (root tuning-log observation) | observation only; no failure produced | **NOTE** — candidate §4.2 strictness note for v0.130 if a real failure surfaces |
| N7 | Measured persona ceilings: ~50% always-think, 12.5% bracket-leak sysprompt-only | persona_test A/B runs (May 16) | **NOTE** — cite in v0.129's empirical-anchors list (it motivates Phase 1.x/A0); not a contract change |
| N8 | UE 5.7 gotchas (MSVC 14.40–14.43 ban; per-module MetaSound registration) | ASTRA_AUDIO BUILD_LOG | **NOTE** — Track-B engineering canon, not spec material |
| N9 | Three "forthcoming" docs now **exist**: `docs/stage-protocol.md`, `docs/narrator-spec.md`, `docs/AUDIT_METHODOLOGY.md` | `2d802b9` | **ADOPT** — §14 flips them from forthcoming → existing (DRAFT v0.1 status noted) |

---

## 4. Ruling form — tier by tier

Legend: ☑ = my recommendation pre-marked. Override by marking a different box and (optionally) one line of why.

### Tier 1 — Audit drift resolutions
**Evidence:** 1A/1B/1G landed `69ee692`/`fe91036` (draft already records); 1C/1D/1E landed `6a30ade` (state-coherence: WarpState + cryosleep_active + computed regime + kinematic_regime projection + ShipKinematicState-as-derived); 1D *completed further* at `2d868d9` (full D4 field set: t_emit_event, regime_at_write, author_instance_id, retrieval_metadata — all defaulted/back-compat, exercised by SaveFile + ephemeral tests). 1F: 5/6 ops in C++; Q5 resolves the 6th.

> **Verdict 1A–1G: ☑ ADOPT (all seven)** — every PENDING in the draft's table is now LANDED.
> ☐ override: ______________________
>
> Sub-decision (1D): §4.6's REEL inline-placeholder block is replaced by the now-implemented canonical field set. `docs/reel-spec.md` stays listed as forthcoming **only if** you want it as the future home of the canonical-REEL-protocol reconciliation (the 5-ring architecture discussion). ☑ keep pointer, annotate "reserved for REEL-protocol reconciliation" ☐ drop pointer.

### Tier 2 — Type-system locks
**Evidence:** 2A/2B landed `6a30ade`, regression-tested (incoherent construction now impossible; the draft's own example — `regime=WARP_CRUISE` with zero rapidity — is structurally unconstructable, and the SaveFile tamper test proves it survives the wire).

> **Verdict 2A, 2B: ☑ ADOPT.**
> **Verdict 2C (endo/exo as type system): ☑ ADOPT-AMENDED** — adopt as *documented discipline* (the §10 row keeps its check; §6.3 keeps the routing rule as prose); type-system promotion (epistemic_origin attrs + Protocols + mypy gate) **deferred to v0.130 pending a concrete mis-routing failure**, per the implementing-session Q2 answer. No such failure surfaced in the window — the §15.4 threshold still isn't met.
> ☐ override: ______________________

### Tier 3 — Calculator-bound tightening
**Evidence:** 3B's *principle* is partially real: ASTRA speech + Narrator output are both validated (strict on the Narrator path, `2fcd403`); ephemerals are calculator-bound **by construction** (template arithmetic, no LLM numerics). But 3A/3C's parse-time `<val>`/`<grounded>` tags and bare-digit grammar rejection were never implemented — the grammar has no such tags (verified in `astra/grammar/` today; `docs/stage-protocol.md` §6 lists them as TENTATIVE).

> **Verdict 3A, 3C: ☑ DEFER → v0.130** (the parse-time package; spec must not claim enforcement that doesn't exist).
> **Verdict 3B: ☑ ADOPT-AMENDED** — adopt as: "every LLM whose output enters perception, speech, or the REEL is validator-wrapped; per-LLM trace pools per §6.4; deterministic ephemerals satisfy the requirement by construction." Drop the literal "every LLM client at construction" (judges/hypothesizer emit no world-numerics; wrapping them is meaningless).
> ☐ override: ______________________

### Tier 4 — Persona instrumentation
**Evidence:** 4B/4C **fully implemented today** (`c23f7d6`): SomaticSignal exactly per the draft's contract, deterministic aggregator, StateBus emitters, assembler integration, 22 tests incl. the no-phenomenal-vocabulary sweep. The draft's [EMP] is fulfilled. One clause is not: the Narrator `<somatic_signals>` machine-readable input (Narrator still receives prose). 4A (positive-autotelic sub-checks) and 4D (negative-space pattern files): zero implementation; 4D is deliberately parked pending your unhurried `book/negative_space.md` review (5b).

> **Verdict 4B, 4C: ☑ ADOPT** with one amendment: the `<somatic_signals>` Narrator-input clause marked TENTATIVE/v0.130.
> **Verdict 4A: ☑ DEFER → v0.130** — *revised from the May working answer* (which said lock-structure-now). Rationale: zero residue landed in the window, and 4A+4D+5b form one natural "autotelic instrumentation package" that should be measured together. Locking structure without any implementation is the consensus-lock §15.4 warns about. (If you prefer the May answer — structure now, thresholds later — mark override; it is defensible.)
> **Verdict 4D: ☑ DEFER → v0.130** (parked on purpose; needs your book review).
> ☐ override: ______________________

### Tier 5 — Reflex envelope
**Evidence:** intentionally *not* implemented (Phase E1+); the ask is an asymmetric-cost envelope lock (Q4). The implementing-session review already stripped the implementation-spec drift (CNN+LSTM → "trained classifier"; CUDA Graphs → "accelerated dispatch"). Save-side: `ReflexIdentity` landed today (`e73aa36`) with `model_id` + `weights_checksum` — but **not** the draft's `training_corpus_version` field (5D). Gap noted.

> **Verdict 5A (§2.3.1 contract), 5B (§2.3.2 Sculptor-instance + 5 swap-points), 5C (§4.7 failure table): ☑ ADOPT** as envelope locks per Q4's asymmetric-cost argument (save-portability dimensions belong in spec per the §15.4 Change-2 boundary).
> **Verdict 5D: ☑ ADOPT + code follow-up** — add `training_corpus_version: str = "untrained-v0"` to `ReflexIdentity` (5-minute defaulted, back-compat change; listed in §6 adoption actions).
> ☐ override (e.g., mark 5A dims "provisional pending E1"): ______________________

### Tier 6 — Methodology additions
**Evidence:** 6A Frozen-Snapshot — universal-pattern claim re-verified; today's additions (SaveFileV3, SomaticSignal, JournalResult, CorrectionArtifact, EphemeralStatus — all frozen) *strengthen* the inventory. 6C Substrate Normalizer — implemented since Day 4.1, now documented in `docs/stage-protocol.md` §4. 6D §15.10 — the methodology has now run twice end-to-end and its lessons doc exists (`AUDIT_METHODOLOGY.md`, with L1–L4). 6B EventStream — **no unifying primitive exists in code**; REEL, research_log are separate bespoke shapes; replay-log doesn't exist at all.

> **Verdict 6A: ☑ ADOPT** (update its inventory table with today's five new instances).
> **Verdict 6C: ☑ ADOPT** (point to stage-protocol.md §4 instead of restating).
> **Verdict 6D: ☑ ADOPT** (with the need-triggered cadence framing; point to AUDIT_METHODOLOGY.md).
> **Verdict 6B: ☑ DEFER → v0.130** — naming a unification that no code honors invites exactly the drift the audit hunts. Defer until/unless the replay-log (§5.3) implementation makes a real third instance.
> ☐ override: ______________________

### Tier 7 — Cross-canon expansion
> **Verdict 7A (Calibration Yards verbatim-propagation rule): ☑ ADOPT** (discipline prose; zero code).
> **Verdict 7B (CROSS_CANON_REGISTRY.md as forthcoming §14 pointer): ☑ ADOPT the pointer**; authoring the registry itself goes on the autonomous-run backlog (good 1–2h task).
> ☐ override: ______________________

### Tier 8 — Audit methodology
> **Verdict 8A: ☑ ADOPT** — and §14's AUDIT_METHODOLOGY.md flips from forthcoming → exists (N9).
> **Verdict 8B: ☑ NOTE** (audit-doc bookkeeping; also update: Cherenkov formula is now implemented in the **visualizer testbed**, so GE3b's status is "testbed-proven, nexus/UE5 pending").
> ☐ override: ______________________

### Section-edit bundle (the draft's per-section diffs)
All section edits ride their parent verdicts above. Net-new ones not covered: §1.1 endo-frame anchor sentence (☑ ADOPT, prose); §13 v0.130-candidates list (☑ ADOPT, now including this packet's deferrals + N2); §14 forthcoming-docs list (☑ ADOPT-AMENDED per N9: three flip to existing; SECURITY_RESPONSE.md and CROSS_CANON_REGISTRY.md remain forthcoming); §15.4 Change 1 + Change 2 (☑ ADOPT — the spec/implementation boundary was *validated by use* this cycle: it kept the Reflex envelope honest and it's cited verbatim in today's docs); §15.7 two-knob authoring consequence (☑ ADOPT, prose); §15.8 five-rigs note (☑ ADOPT, prose).

---

## 5. Q1–Q7 — final recommended answers (June-10 revision)

| Q | May working answer | June-10 recommendation | Changed? |
|---|---|---|---|
| Q1 timing | Option B (defer for residue) | **Adopt now via this packet** — the residue Option B asked for has landed and is hash-cited above | Window completed as designed |
| Q2 endo/exo typing | Discipline, not type-system | **Confirm** — no mis-routing failure produced in the window | No |
| Q3 autotelic thresholds | Lock structure w/ provisional numbers | **Defer structure AND thresholds to v0.130** as part of the autotelic-instrumentation package (4A+4D+5b together) | **Yes** — stricter §15.4 reading; override available |
| Q4 Reflex dims | Lock now (asymmetric cost) | **Confirm** | No |
| Q5 ship_state_query | Python/textverse | **Confirm** (and §6.4 says so explicitly) | No |
| Q6 audit cadence | Need-triggered, never calendar | **Confirm** — now codified in AUDIT_METHODOLOGY.md | No |
| Q7 final authorship | Implementing session authors | **Confirm** — this packet is the upstream synthesis; on your rulings the implementing session writes `docs/spec-v0.129.md` | No |

---

## 6. Adoption mechanics (what happens after your rulings)

One implementing-session pass, est. **2–3 hours**, fully gated:

1. Copy `spec-v0.128.md` → `docs/spec-v0.129.md`; apply every ADOPT/ADOPT-AMENDED edit per this packet (and only those).
2. Write the v0.129 header: changes-from-v0.128 list, empirical-anchors list (audit closures + today's commits + N7 ceilings), the v0.130 queue (§13) from all DEFERs + N2 + N6.
3. Apply N1 (Cherenkov wording flip at 4 sites) + N3 (qc3 path) + N5 (regime-coherence load invariant) + N9 (§14 flips).
4. Code follow-up: `ReflexIdentity.training_corpus_version` (defaulted) + its test; bump `astra_nexus.cpp` header if adopted text references v0.129.
5. Mark `spec-v0.129-tentative-2026-05-16.md` header: "SUPERSEDED — adopted with amendments as spec-v0.129.md per FINALIZATION-PACKET-2026-06-10"; v0.128 header gains "superseded by v0.129".
6. Update CLAUDE.md spec-envelope pointer (`docs/spec-v0.128.md` → `v0.129`) + memory.
7. Full gates (bench 749+, C++ 71/71), commit, push.

**Your time:** ~30–45 min on §4's checkboxes (or just reply "adopt as recommended" / list overrides).
**Effort already sunk into this packet:** every status above was verified against code today, not recalled.

---

*Packet ends. Nothing in this document changes canon by itself — it is the menu, not the meal. §15.4 keeps the signature yours.*
