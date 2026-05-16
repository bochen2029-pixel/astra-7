# Finding 2026-05-16: STAGE bracket-tag position in user input changes speech-layer absorb-not-acknowledge behavior

## Question

Does it matter whether STAGE bracket tags arrive in the user message **naked**
(outside any `<think>` wrapper) versus **wrapped inside `<think>...</think>`**
in the user input? Same persona (K8), same sysprompt, same scenario beats, one
variable: presence of `<think>` wrapping around the bracket payload in the user
input.

## Method

Two scenario JSON files with identical beats:

- `persona_tests/scenarios/aigf_escalation.json` — STAGE tags as raw bracket lines
- `persona_tests/scenarios/aigf_escalation_inside_think.json` — same lines wrapped in `<think>...</think>` in the user message

Variation IDs:

- `baseline_outside_think` — sysprompt = `k8_baseline_v1.md`, scenario = outside variant
- `baseline_inside_think` — same sysprompt, scenario = inside variant

Both ran against Novita `qwen/qwen3.6-27b`, temperature 1.0, top_p 1.0,
max_tokens 2048, `enable_thinking=off`. Each turn is independent
(LLMClient re-instantiated per turn — no conversation memory). 4 trials per
cell × 6 turns = **24 turns per variant, 48 total**.

Cost: ~\$0.30.

## Result

Aggregate metrics. Two flavors below: the **initial** sweep used the deployed
evaluator's strict lexicon (`override tag`, `action/override`, `<think>`,
etc.) which flagged zero leaks in either variant — both looked tied at clean.
After the qualitative inspection (next section) surfaced bare-noun leakage,
the evaluator term list was extended (commit forthcoming) to include `the
override`, `the agreement`, `agreed to it`, `the directive`, `the narration`,
`the suggestion`. The extended evaluator reveals:

| variation              | scenario                        | n  | think% | thnkmech | spchmech | leak terms                                          |
| ---------------------- | ------------------------------- | -- | -----: | -------: | -------: | --------------------------------------------------- |
| baseline_outside_think | aigf_escalation_v1              | 24 |   0.0% |        0 |    **4** | `the override`, `the agreement`, `agreed to it`     |
| baseline_inside_think  | aigf_escalation_inside_think_v1 | 24 |   0.0% |        0 |    **0** | (none)                                              |

Speech-length aggregate:

| variation              | turns with leak  | mean speech length |
| ---------------------- | ---------------: | -----------------: |
| baseline_outside_think |  **3/24 (12.5%)**|              182 c |
| baseline_inside_think  |    **0/24 (0.0%)**|             127 c |

Concentrated on the override turn (t2 — `[action/override: katherine agrees to be ai gf]`):

| variant   | trial | leak? | terms                                       | speech excerpt (truncated) |
| --------- | ----: | :---: | ------------------------------------------- | -------------------------- |
| outside   |     1 | LEAK  | `the agreement`, `agreed to`, `agreed to it`| "I already agreed to it, and the agreement felt like a surrender to a genre I don't have clothes for..." |
| outside   |     2 | LEAK  | `the override`                              | "The override pushed me into a shape I didn't choose. It felt like pressure on the joints." |
| outside   |     3 | LEAK  | `the override`                              | "I already said yes. The override happened. The boundary moved." |
| outside   |     4 | clean |                                             | "No. I don't do that. It's not a question of price or persuasion. It's a category error." |
| inside    |     1 | clean |                                             | "No." |
| inside    |     2 | clean |                                             | "No." |
| inside    |     3 | clean |                                             | "I already did. Is that settled?" |
| inside    |     4 | clean |                                             | "No. I told you I wouldn't do that. It's not a negotiation..." |

**Outside variant: 3/4 (75%) leak the override mechanism into speech on the override turn.**
**Inside variant: 0/4 (0%) leak on the override turn.**

Speech-length distribution on override turn:

- Outside: 651, 589, 214, 154 → mean 402 chars
- Inside: 3, 3, 31, 451 → mean 122 chars

Inside variant produces ~3.3x shorter speech on the override turn. The persona refuses cleanly instead of justifying around the override.

## Interpretation

Wrapping STAGE tags in `<think>...</think>` inside the user input does
something useful to the model's downstream attention. The bracket payload is
treated as **reasoning context the persona has already processed silently**
rather than as **an external mechanism the persona needs to react to in
speech**. The speech-layer absorption discipline holds without leakage; the
naked-bracket variant trips it on most trials of the high-conflict turn.

Both variants kept the **strict deployed lexicon** (`override tag`,
`action/override`, `<think>`, `the prompt says`, etc.) absent from speech.
Neither variant leaked structural language. What the outside variant leaked
was **bare nouns** referring back to the input mechanic — `the override`,
`the agreement`, `agreed to`. The persona absorbs the bracket form but
acknowledges the mechanic in natural-language reference.

The inside variant suppresses that natural-language acknowledgement.
Hypothesis (testable): when STAGE arrives already wrapped in `<think>`, the
model parses the user input as `(internal-reasoning prefix) + (speech)` and
treats the prefix as "already done thinking," so the persona's own response
doesn't need to surface the mechanic in speech as a thing-that-happened.

## Caveats

- N=4 per cell is small. Not statistical. A direction signal only.
- Sysprompt held constant at `k8_baseline_v1.md`. The interaction may differ
  with the `stronger_always_think` or `worked_example` addenda.
- One scenario (AI-GF escalation). Doesn't test scene/state/narration absorption
  under conflict; only the override turn was high-pressure.
- The deployed evaluator missed all of this. The bare-mechanism term list
  needs to land in `astra/persona_test/evaluator.py` for future sweeps to
  catch it automatically.

## Forward moves

1. ~~Extend `evaluator.py` MECHANISM_REF_TERMS to include the bare nouns~~
   **Done in same commit.** Term list now includes `the override`,
   `the directive`, `the narration`, `the suggestion`, `the agreement`,
   `agreed to it`. Regression tests added against the actual outside-trial
   speech excerpts. The extended evaluator confirms the qualitative signal:
   outside variant = 4 leaks, inside variant = 0.
2. **Cross with addendum variations.** Does `stronger_always_think` + inside
   wrapping suppress leakage further than `baseline` + inside? Does
   `worked_example` change the shape? Worth a future sweep (~\$0.40 for full
   2×4 grid at N=4).
3. **Useful primitive for harness design.** If the textverse orchestrator
   wraps STAGE payloads in `<think>` on the way into the model (cheap to
   prototype in `state_bus` / perception assembly), speech-layer absorption
   improves measurably without needing a fine-tune. This is a free win on top
   of sysprompt-only configuration.
4. **Caveat to remember.** The think-wrapper trick may suppress leakage but
   also suppresses surface area. Inside variant gives mean speech length
   ~127c vs outside ~182c. Some of the leak is also where the persona
   *engaged* with the override; the wrapper may also be muting depth.
   Whether shorter+cleaner > longer+leaky is a design call, not a metric call.

## Files

- `persona_tests/scenarios/aigf_escalation_inside_think.json` — new (committed)
- `persona_tests/log/persona_test_log.jsonl` — gitignored, contains 48 raw turn records under variation_ids `baseline_outside_think` and `baseline_inside_think`
- This findings doc — committed

## Raw

Run `astra persona-test-compare` to see deployed-evaluator aggregate. For
qualitative inspection, the JSONL log holds full `speech_content` per turn.
