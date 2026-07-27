# Narrator-LLM Contract — v0.2

**DRAFT v0.2 (2026-07-26; anchor refresh for the 6c–6k arc) — documents
implementation; not spec adoption.** v0.1 (2026-06-10) described the
pre-live-run implementation. Code is the source of truth here; the spec
sketch remains the envelope.

## 0. Measured state (v0.2 headline; ledgers are authoritative)

Across the 2026-07 live series (26 runs, ledgers
`proto/textverse/LIVE_RUN_*.md`): fallback rate **0.506 → 0.022**
(F-LIVE-19 closed: the dominant class was reasoning-budget truncation,
config not contract), state_coherent **0.493 → 1.000 zero-variance**
(F-LIVE-20/28/29: sysprompt inventory requirement + the
identifier-vs-prose gate fix), narrator-path Model-Off Replay proven
retry-loops-included. **Development status: FROZEN per F-LIVE-31 (6k)** —
narrator perception shows no measured behavioral effect on ASTRA's
autotelic register at the 9B floor at 4–5× template wall-clock; the path
is maintained contract-conformant infrastructure, re-opened by a
perception-quality instrument or the 27B era.

## 0.1 Inference discipline (NEW at 6e; constants in `narrator_bundle.py`)

- **Reasoning OFF by default** (`NARRATOR_THINKING = "off"` via
  `chat_template_kwargs`): the Narrator is a renderer under §15.6 — it
  transcribes numerics it was handed, never derives, so cognition is pure
  cost. The F-LIVE-11/16 lesson one seam deeper: not "strip the
  cognition" but do not generate it. Caller-supplied `extra_payload`
  overrides compose UNDER it (a deliberate override is never silently
  replaced).
- **Own compose budget** (`NARRATOR_COMPOSE_MAX_TOKENS = 1024`): never
  inherits ASTRA's speech-sized SamplingParams default (the silent
  inheritance was F-LIVE-19's root cause). Temperature 0.4 / top_p 0.85
  unchanged (rendering, not improvising).
- **Think-strip at the seam regardless** (`_strip_reasoning`,
  last-`</think>` rule; unclosed fails CLOSED; strip-before-validate):
  defense-in-depth stays even with thinking off.
- Sampling scope note: `tuning/sampling.json` governs the ASTRA bundle
  only; narrator constants live in code (see the file's `_comment`).

## 0.2 Composition-request contract (NEW at 6e/6h)

- **Compact serialization:** the StateBus JSON in the request is
  byte-identical to the trace pool's first entry — what the narrator is
  shown and what it is grounded against are the same string.
- **Derived presentation values:** the request supplies the regime LABEL
  (`regime_label()`) and the body-name list under an explicit "already
  computed; do not re-derive" instruction (F-LIVE-22: no LLM is asked to
  re-derive what the harness computed — same rule as τ/watch labels).
- **State-section inventory:** the narrator sysprompt requires `<state>`
  to name the regime label and every body, with brevity explicitly
  subordinate ("brevity governs how, never whether") — the F-LIVE-26→29
  closure, guarded by `tests/test_bundles.py`.
- **Prose-channel naming rule (gate side):** `gate_state_coherent`
  normalizes separators when checking names — the `<state>` channel is
  contractually prose, and demanding identifier syntax (`hot_earth`)
  there required the narrator to violate its own voice rules (F-LIVE-28).

## 1. Role (implemented)

The text-substrate's rendering pipeline: where UE5 has Observation
Calculator → pixel shaders, textverse has structured physics state →
Narrator-LLM → text perception bundle. The Narrator is a separate bundle
from ASTRA (own sysprompt at `prompts/narrator_sysprompt.md`, own
llama-server port per ARCHITECTURE.md §6.5), so the universe can author
detail ASTRA references without ASTRA knowing the universe was authored.

## 2. Implemented surface

`astra/llm/narrator_bundle.py` + `astra/harness/perception_assembler.py`:

**Input** — `_build_narrator_composition_request` renders one user message
containing: the FULL StateBus snapshot as JSON (every numeric the Narrator
may cite, verbatim), recent REEL retrievals as JSON, the somatic note, and
the operator input. Instruction: produce the canonical four-section
`<state>/<somatic>/<recent>/<operator>` bundle, cite only numbers present
in the provided data, τ_ship/watch vocabulary only.

**Output** — the four-section perception bundle (same shape as the
template path), delivered to ASTRA only after validation.

**Calculator-bound validation (§15.6)** —
`_build_narrator_trace_pool` collects the StateBus JSON + somatic note +
REEL bodies/timestamps; `CalculatorBoundValidator` /
`validate_speech` (`astra/llm/validator.py`) scans the Narrator's output
for numeric tokens and requires each to be a substring of the pool. An
ungrounded number fails validation → retry; retries exhausted →
`NarratorValidationError` → the orchestrator **falls back to the template
assembler** and records `narrator_fallback_reason` on the TurnResult.
Strict by default; bypass requires an explicit debug flag.

**Wire-in** — `TurnOrchestrator` step 1 routes through the Narrator when a
`narrator_bundle` is provided, template path otherwise. Scenario
`narrator_grounded_numerics` exercises the path end-to-end.

## 3. Honest deltas from the §6.4 sketch

| §6.4 item | Status |
|---|---|
| Tool surface (`physics_query`, `astrometric_query`, `composition_rule_evaluate`, `retarded_time_solve`, `kepler_at`, `observe`) | Implemented server-side in `proto/astra_nexus --stdio-server` (commit fe91036). The v0 Narrator does NOT call them mid-generation; it receives pre-computed state JSON and is grounded by the validator instead. Mid-generation tool calling is a later tier. |
| `ship_state_query` | Deferred to Python textverse per audit Q1; not yet implemented. |
| Numeric emission as `<val src="...">` tags | TENTATIVE (v0.129 draft §6.4 edit). Current enforcement is post-emission substring grounding, not tagged provenance. |
| Tonal-register style filter | NOT implemented. Register is carried by the Narrator sysprompt; no post-output style gate yet. |
| Narration-continuity buffer + diff | NOT implemented (single-turn composition today). |
| `<somatic_signals>` machine-readable input | NOT implemented; the request carries the somatic note as prose. SomaticSignal producers exist (`astra/harness/somatic.py`). |
| 7–9B model sizing, VRAM coexistence | Untested in textverse (Narrator runs against whatever server the bench wires; sizing is a UE5-phase measurement). |

## 4. Failure modes (implemented behavior)

- Hallucinated number → caught by grounding scan → retry with the same
  request → exhausted retries raise `NarratorValidationError` → template
  fallback + `narrator_fallback_reason` recorded. The turn never silently
  ships ungrounded numerics.
- Narrator server unhealthy → bundle-level health/retry policy in
  `astra/llm/client.py` (429/503 backoff); persistent failure surfaces
  through the orchestrator's substrate-health handling.

## 5. Cross-references

Spec v0.130 §6.4, §15.6 (adopted envelope) · `docs/stage-protocol.md` ·
`proto/textverse/LIVE_RUN_2026-07-25.md` (6e), `…_6f.md`, `…_6gh.md`
(6g/6h + corrections), `…_6k.md` (F-LIVE-31 freeze verdict) ·
`tests/test_narrator_pathway.py`, `test_narrator_calculator_bound.py`,
`test_narrator_think_strip.py`, `test_narrator_replay.py`,
`test_narrator_inference_config.py`.

*(v0.1 sections 1–4 above retain their 2026-06-10 text where still true;
the trace/replay closure (6c: `TracingLLMClient` receipts every attempt,
narrator sessions replay byte-identically model-off) supersedes §2's
silence on tracing.)*
