# Narrator-LLM Contract — v0.1

**DRAFT v0.1 — documents implementation; not spec adoption.** Closes the
`docs/narrator-spec.md` "forthcoming" pointer (spec v0.128 §6.4, §14) by
describing the implemented subset in `proto/textverse/` as of 2026-06-10,
and naming the §6.4 items that are NOT yet implemented. Code is the source
of truth here; the spec sketch remains the envelope.

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

Spec v0.128 §6.4, §15.6 · v0.129-TENTATIVE §6.4 edits · `docs/stage-protocol.md`
· `tests/test_narrator_pathway.py`, `tests/test_narrator_calculator_bound.py`.
