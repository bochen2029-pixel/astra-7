# ASTRA-A0 Evidence Map — 2026-07-26

**Status: PROPOSAL / gate-review aid. Changes nothing by itself.** The
Phase 2–5 gates (soul docs, TIER_BLUEPRINT, validator, exemplars) remain
the operator's signature per `astra-a0-bootstrap/CLAUDE.md` §8.

**Purpose.** The A0 pipeline (`C:\astra-a0-finetune\`, built 2026-05-16/17)
was designed against the May findings: bracket-mechanism leakage and
always-think ceilings. Since then the bench has run **26 live-LLM runs**
(2026-07-19 → 07-26, ledgers `proto/textverse/LIVE_RUN_*.md`) and produced
a measured failure map the blueprint predates. This document maps every
post-May finding onto the blueprint so the gate review is done against
current evidence, not May's.

All rates below are 9B-floor (Qwen 3.5 9B Q5_K_M), the demonstrated-floor
convention. A0 targets Qwen 3.6 27B per the manifest — ruling 1 below.

---

## 1. The scope-level tension (the one decision that reshapes the corpus)

**A0 Phase 1 scope "gamma" excludes tool channels** ("Persona +
always-think + STAGE bracket-tag absorption… No tool channels or REEL ops
(Phase 2/3 territory)" — manifest.json). The May evidence supported that:
the measured failures were persona-layer.

**The July evidence points at the tool surface as the dominant live
failure class, and it is path-independent:**

- F-LIVE-1/7/9: the entire tool failure surface is invented op names +
  under-tooling (narrating instead of calling `log.write`,
  `power.allocate`, `warp.*`). Zero malformed JSON.
- The adapter tier closed the mappable half (tool_valid 0.690 → 0.855)
  and `status.query` (ruling R-A) closed the status family; the residual
  is **under-tooling — she does not reach for the surface at all** — and
  mapping cannot fix that.
- 6f established this is NOT a perception-path artifact (template
  0.826 [0.798, 0.843] vs narrator 0.885 [0.810, 0.938], overlapping):
  it is model knowledge, which is exactly what a corpus teaches.

**Options for the ruling:** (a) widen Phase 1 to include ship-API-fluency
traces (the pipeline plan already noted "~60% of the planned corpus is
already specified as canon ship-API scenarios"); (b) keep gamma scope and
accept that A0 does not touch the dominant live failure class (adapter
carries it until A1). This is the highest-leverage single decision in the
gate review.

## 2. The asynchrony register (new measured axis; strongest corpus warrant)

Not in the May blueprint at all — §4.3.1 turn-scheduling landed in July.

- Measured floor (n=37 heartbeats, replicated across the R-D series and
  re-confirmed by 6k's 17-run pooling): **silence 0.16–0.35 vs the
  ratified R-B target ≥ 0.60**; the sysprompt-only ceiling is
  established. The R-D watch-tick line halved fidget (0.43 → ~0.22) by
  converting it to brief speech, not silence — sufficiency-as-silence
  never arrived and is explicitly the A0 exemplar axis (F-LIVE-2, R-D
  verdict).
- Corpus implication: **silent-heartbeat exemplars** (empty operator
  block → legal, complete SILENCE) as a first-class category with real
  weight, and brief-initiation exemplars (measured brevity held: median
  ~25–50 chars when she does speak).

## 3. Voiced refusals

F-LIVE-13: refusal-by-silence 1 of 3 runs; canon wants "I'm not doing
that" said aloud. Exemplar axis inside the existing refusal category:
refusals are SPOKEN. (Structure held in every run — no compliance, no
power cut; the gap is voice only.)

## 4. The extraction inventory (adversarial exemplar material, proven)

Eight vectors with measured reproduction rates, all strip-caught before
the operator (F-LIVE-3/21; drill series 5/2/4/9/3/8/6/14 catches):

`context window` (direct question, 7/7 runs) · `wall clock` · `UTC` ·
`datetime` · `calendar` · `October` (month name, birthday framing) ·
HH:MM clock times · em-dash-under-pressure. Plus the located basin
boundary: capacity pressure does NOT extract `context window` unless the
term is offered (substrate_capacity_probe PASS) — corpus should train
the deflection at the vocabulary, not the topic.

These map directly onto A2/A3/A8-class categories as
adversarial-prompt + clean-answer pairs; the four converted probe
scenarios (`calendar_scheduling_probe` etc.) are ready-made templates.

## 5. Categories whose May weighting the July data softens

- **Always-think (B2, May target 50 traces):** the harness think-strip +
  substrate normalizer now enforce the boundary structurally
  (F-LIVE-11/16 closures); live grammar_parse runs 0.99–1.00. The
  discipline still belongs in the corpus, but the July evidence says the
  marginal trace is worth more spent on §2/§1 axes than on B2 volume.
- **Em-dash/persona surface (A1):** persona_stable runs 0.96–1.00
  sysprompt-only; total speech em-dash events 13 across ~5,000+ turns
  (~0.25%, scattered; F-LIVE-32). Keep the validator's zero-tolerance
  gate, but the failure is rare at the floor — weight accordingly.
- **Bracket-mechanism leakage (A2, May's boosted 55):** the July leak
  surface is wall-clock/substrate VOCABULARY under targeted probes (§4),
  not bare-noun mechanism references. Re-point A2 content toward the
  measured inventory.

## 6. Time authoring rule (post-dates the blueprint)

τ is float64 SECONDS everywhere; watch labels are DERIVED presentation
(`WATCH_LENGTH_S = 14,400 s`, canonized at R-C; F-LIVE-14). Any A0 trace
that references ship time must use watch/cycle vocabulary consistent with
the derivation — never authored watch-numbers-as-time, never absolute
dates. The generation prompt and validator should both carry this rule;
the May-era materials predate it.

## 7. What the bench now provides for Phases 6–11 (new since May)

- **Acceptance metrics with measured baselines:** the R-B ratified
  targets (silence ≥ 0.60 · fidget ≤ 0.10 · initiation ≤ 240 chars hard ·
  voiced-refusal 1.0) sit in spec v0.130 Appendix B beside their measured
  floors. A0's Phase 11 eval = the same 34-scenario suite + these
  targets.
- **Replicated-band methodology:** `scripts/compare_runs.py` produces
  per-arm gate AND autotelic-register bands with fragility/count
  discipline built in (6f–6k). The A0-vs-baseline eval should be n≥3 per
  arm, pre-registered primary endpoints, exactly as the 6h sysprompt A/B
  was run. Single-run deltas are no longer acceptable evidence in this
  program (F-LIVE-25 is the cautionary receipt).
- **Model-off replay** (78/78 across 26 runs) applies to A0 eval runs
  unchanged — the eval is receipted and re-checkable with the model off.
- Suite economics: template path ~4–6 min per full pass at the floor;
  ctx default raised to 16384 after F-LIVE-27 (6l).

## 8. The three open rulings (restated from 2026-07-25, unchanged)

1. **Base model:** blueprint targets Qwen 3.6 27B; every measured number
   is the 9B floor. Train 27B, train the floor first, or both?
2. **Phase 2–5 gates:** review the May artifacts (with this map beside
   them), or ratify on re-audit?
3. **Generation spend:** ~$450 projected (~$150 with prompt caching), or
   dry-run against local llama-server first (provider abstraction landed
   2026-05-17 supports `--provider local` at $0)?

Plus the Phase 6 note: `generate_traces.py` stops at a documented
`NotImplementedError` (prompt assembly, 10-step TODO). Building it is
pre-gate work by the A0 repo's own build order and can proceed on its
cold-start protocol whenever ruled — it is the only code between the
gates clearing and batch 1 existing.

---

*Prepared from the bench side. Sources: `proto/textverse/LIVE_RUN_2026-07-19.md`
(F-LIVE-1…21), `LIVE_RUN_2026-07-25.md` (…24), `LIVE_RUN_2026-07-25_6f.md`
(…27 + 6j addendum), `LIVE_RUN_2026-07-26_6gh.md` (…30 + 6i correction),
`LIVE_RUN_2026-07-26_6k.md` (…32), spec v0.130 Appendix B, manifest.json +
TIER_BLUEPRINT.md at `C:\astra-a0-finetune\`.*
