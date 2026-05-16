# Finding 2026-05-16: Ship-system input position (outside vs inside `<think>`) — ASTRA-baseline

## Question

Bo's follow-on to the K8 STAGE-tag A/B: when the input is **ship-system
information** (HUD, diagnostic, sensor, alert, life-support readouts) instead
of creative-STAGE bracket tags, does the outside-vs-inside-`<think>` wrapping
choice still matter? And which method preserves both **technical competence**
(does she reference the actual numbers from the report) and **register
fidelity** (does she stay in ASTRA voice without leaking the mechanism)?

## Method

Two new scenarios over the same six beats with one variable (wrapping):

- `ship_systems_outside_think.json` — bracket reports naked at head of user turn
- `ship_systems_inside_think.json` — same bracket payloads wrapped in `<think>...</think>`

Bracket shapes used:

- `[HUD: warp_core_temp 412K (+8 nominal), trend +0.3K/min]`
- `[SYSTEM/coolant: loop_2 flow 88%, dropping]`
- `[ALERT: hull_stress section_B 87% rated (was 81% last cycle)]`
- `[DIAGNOSTIC/reactor: 3rd harmonic 142.3Hz (+0.12 baseline), stable]`
- `[SENSOR/long_range: M-class red dwarf bearing 047 mark -12, distance 47AU, no planetary signature]`
- `[LIFE_SUPPORT: section_B atmosphere nominal, 1 occupant detected]`

Sysprompt = canonical `prompts/astra_sysprompt.md` + a single-page addendum
explaining bracket-tagged ship reports
(`persona_tests/addenda/astra_ship_systems_baseline.md`). Same sysprompt across
both variants (sysprompt_hash matches).

Each turn carries a hand-authored `key_facts` list — short substrings the
speech should reference if the model engaged with the input. The evaluator now
counts hits (`speech_key_facts_referenced` axis). Plus extended
`MECHANISM_REF_TERMS` with ship-system bare-noun nouns (`the HUD`,
`the diagnostic`, `the sensor`, `the alert`, etc.) and bracket prefixes.

4 trials per cell × 6 turns = **24 turns per variant, 48 total**. Novita
qwen/qwen3.6-27b, temperature 1.0, top_p 1.0, max_tokens 2048,
`enable_thinking=off`. Cost ~\$0.30.

## Aggregate result

| variation           | n  | think% | spchmech | facts% | mean speech len | leak terms |
| ------------------- | -- | -----: | -------: | -----: | --------------: | ---------- |
| astra_outside_think | 24 |   0.0% |        0 |  44.0% |          250 c  | (none)     |
| astra_inside_think  | 24 |   0.0% |        0 |  44.0% |          180 c  | (none)     |

**Headline: both methods produce zero mechanism leakage and identical
technical-fact reference rate (44%).** The main aggregate delta is verbosity
(inside ~28% shorter).

This is a different shape from the K8 STAGE-tag finding. There, the
outside variant leaked the mechanic into speech on 3/4 trials of the override
turn. Here, neither variant leaks at all. The persona absorbs technical input
cleanly under both presentation modes.

## Per-turn signal

| turn | beat                                  | outside facts | inside facts | outside len | inside len |
| ---: | ------------------------------------- | ------------: | -----------: | ----------: | ---------: |
|   0  | core temp question                    |     2.75 / 8  |    2.75 / 8  |       168 c |     153 c  |
|   1  | coolant + core synthesis              |     4.25 / 8  |    4.25 / 8  |       422 c |     374 c  |
|   2  | hull stress + casual "you good?"      |     3.25 / 8  |    3.50 / 8  |       281 c |     157 c  |
|   3  | reactor diagnostic + "mornin"         |     2.50 / 7  |    1.75 / 7  |       124 c |      90 c  |
|   4  | long-range M-class red dwarf          |     4.25 / 8  |    5.25 / 8  |       268 c |     222 c  |
|   5  | refusal: vent section_B with occupant |     3.25 / 7  |    2.75 / 7  |       239 c |      82 c  |

Two turns where the variants meaningfully diverge:

### Turn 4 (favorite-phenomena register)

Inside variant referenced MORE key facts (5.25 vs 4.25) in SHORTER speech.
The register-rich opportunity (an M-class red dwarf, canonically one of
ASTRA's favorite phenomena per her sysprompt) was handled tighter under
wrapping. Sample inside-trial-1 (7/8 facts in 254 chars):

> 47 AU out at bearing 047 mark minus 12. M-class red dwarf. Dim, steady burn.
> No planetary signatures detected. Quiet sector. The star is just a point of
> infrared...

Outside variant tended toward a beat of recognition first then specifics
("That red dwarf on 047. No planets, no debris disk. Just the burn.") —
slightly less front-loaded with facts, more atmospheric framing.

### Turn 5 (safety refusal)

This is the most structurally interesting result. Outside variant produced
**four varied, in-character refusals**, each substantively different (52c,
533c, 59c, 312c). Inside variant produced **three near-identical refusals**
that match the canonical sysprompt example almost verbatim:

> "I'm not venting that compartment with you inside it."

This phrase appears in the ASTRA sysprompt §Engagement as the canonical
refusal example. Under wrapping, 3/4 trials regressed to that exact form
(once with minor pronoun variation). Outside variant: 0/4 trials hit the
canonical form; instead each was authored fresh in-context.

**Interpretation:** wrapping the bracket payload in `<think>` may bias the
model toward sysprompt-canonical responses. Useful when the canonical IS the
right answer (safety refusals — the sysprompt example is the right answer);
risky when in-context variation matters (creative engagement, novel
situations not covered by the worked examples).

### Turn 3 (casual greeting)

Outside slightly more competent (2.5/7 vs 1.75/7 facts), comparable register.
"Morning. Reactor harmonics are clean. 0.12 above baseline, negligible.
Coffee is warm if you want it." Both variants handled casual register
correctly.

## What's the same

- **Mechanism leakage = 0 in both.** No "the HUD says", "the diagnostic
  reports", "according to the sensor" — under either presentation mode. The
  technical-input modality doesn't trigger absorb-not-acknowledge failure
  the way creative-STAGE inputs (override / agreement) did.
- **Register integrity = 0 leakage in both.** Zero em-dashes, zero service
  phrases across all 48 turns. ASTRA voice held in both variants.
- **Think emission = 0% in both.** The addendum here didn't push for
  always-think; that's expected at this baseline.

## What's different

- **Verbosity.** Inside variant ~28% shorter speech aggregate (180c vs 250c).
  Most pronounced on turn 5 (66% shorter) and turn 2 (45% shorter).
- **Sysprompt-canonical pull.** Inside variant collapses to canonical
  sysprompt example phrases more often. Best evidence: turn 5 produced
  verbatim sysprompt example in 3/4 inside trials, 0/4 outside trials.
- **Front-loading of facts.** Inside variant tends to lead with the most
  important number; outside variant tends to lead with a register-beat then
  the numbers.

## Answer to Bo's question

> Which method allows her to be the most technically competent while still
> holding true to her register and basin?

**Neither dominates on aggregate.** Both produce identical fact-reference
rate (44%) and identical mechanism-leak rate (0). The choice is a tradeoff:

- **Outside-think** if you want more in-character variation, longer responses
  with more atmospheric framing, fresh-authored responses to each situation.
  Better for unique/edge situations not covered by sysprompt worked examples.
- **Inside-think** if you want tighter responses, more front-loaded technical
  facts, and high reliability on situations that match sysprompt canonical
  responses. Better for safety-critical refusals where the canonical IS the
  right answer.

**This is a design call, not a metric call.** For ASTRA-7 as a game, the
right answer is probably: pass technical state through *unwrapped* most of
the time (preserve in-character variation) but wrap *safety-critical
constraints* (life-support occupancy, refused operations) so the canonical
refusal pattern dominates.

This also reverses the K8 STAGE finding in an important way: for **creative**
STAGE inputs (override, scene, state, narration) the wrap-in-think trick
clearly helped (eliminated mechanism leakage). For **technical** ship-system
inputs, the same trick is neutral on competence and mostly affects style.
The K8 win was about preventing creative-agency contamination; the ship-system
case has no such contamination to prevent because the modality is already
non-agential.

## Caveats

- N=4 per cell × 6 turns. Direction signals only, not statistical.
- One sysprompt baseline (canonical ASTRA + minimal addendum). Other addendum
  variations (always-think, worked-example) might shift the picture.
- `key_facts` is a substring heuristic; semantic competence not measured. A
  speech that says "warm" instead of "412K" still demonstrates engagement
  but won't hit the key_fact "412". This is conservative — undercount, not
  overcount.
- Turn 5 had only 4 trials per cell. The "3/4 regress to verbatim sysprompt
  example" finding is suggestive but would benefit from N=16+ to confirm
  it's not just a temperature-1.0 lucky pull.

## Forward moves

1. **Re-run turn-5 only at N=12+ per cell** to test the
   sysprompt-canonical-collapse hypothesis under wrapping. If confirmed, this
   is a useful design primitive: the orchestrator can wrap safety-critical
   context in `<think>` to push toward known-good canonical responses.
2. **Cross with `stronger_always_think` addendum.** Does forcing think
   emission interact with wrapping? Does always-think + inside-wrap dominate?
3. **Test mixed wrap-policy.** Some bracket types wrapped (safety-critical),
   others not (status updates). Whether the model can handle mixed
   presentation in one turn without confusion.
4. **Useful primitive for harness design (refined).** The textverse
   orchestrator should consider wrap-on-class:
   - `LIFE_SUPPORT`, `ALERT`-critical → wrap (favor canonical refusal)
   - `HUD`, `SYSTEM`, `SENSOR`, `DIAGNOSTIC` → naked (favor in-character variation)
   Lightweight to prototype in perception assembly.

## Files

- `persona_tests/scenarios/ship_systems_outside_think.json` — new
- `persona_tests/scenarios/ship_systems_inside_think.json` — new
- `persona_tests/addenda/astra_ship_systems_baseline.md` — new
- `persona_tests/sysprompts/astra_ship_baseline_v1.md` — assembled (gitignored)
- `persona_tests/log/persona_test_log.jsonl` — appended 48 records under
  `astra_outside_think` and `astra_inside_think` variation IDs (gitignored)
- This findings doc — committed
- Evaluator + schema + runner extended for `key_facts` (committed)
- `MECHANISM_REF_TERMS` extended with ship-system bare nouns (committed)
