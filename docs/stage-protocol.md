# ASTRA-7 STAGE I/O Grammar — v0.1

**DRAFT v0.1 — documents implementation; not spec adoption.** This file
closes the `docs/stage-protocol.md` "forthcoming" pointer in spec v0.128
(§4.3, §14) by describing what `proto/textverse/astra/grammar/` actually
parses and enforces today. Where v0.129-TENTATIVE items appear they are
marked TENTATIVE. Authored 2026-06-10 from code, not from intention.

**Name collision, on purpose:** ASTRA-7's spec uses "STAGE" for the
LLM-facing I/O grammar described here (perception bundle in, four output
channels back). Bo Chen's standalone **STAGE Protocol v1.0** (CC-BY-4.0,
2026-02-18) is a different, persona-agnostic standard for world-state
INPUT tags (`[scene]`/`[state]`/`[narration]`/`[action]` + implicit
dialogue, trained into weights). The two are duals, not synonyms: canonical
STAGE governs how a persona receives its world; this grammar governs how
ASTRA's harness exchanges structured text with the model. Reconciliation
(possible renaming of this side to "Emission Channels") is an open operator
decision; until then this document always says "I/O grammar" for the
ASTRA-7-local thing.

---

## 1. Input: the perception bundle

Composed by `astra/harness/perception_assembler.py` (template path) or by
the Narrator-LLM (`docs/narrator-spec.md`). Four XML-tagged sections, in
this order:

```
<state>    ship + universe state in tight prose (from StateBus)
<somatic>  functional-state banner (Somatic Aggregator; sensor-grounded,
           not phenomenal claim — v0.129 §6.3.1 residue)
<recent>   REEL retrievals, one per line
<operator> operator input verbatim; empty section = operator SILENCE
```

Before delivery the whole bundle passes
`LeakDetector.scan_perception_bundle` (`astra/grammar/leak_detector.py`):
wall-clock patterns AND technical-substrate patterns are stripped, every
match logged as a `LeakEvent`. Canon pattern files live at
`astra/grammar/canon/{wall_clock_patterns,astra_substrate_patterns}.txt`.

## 2. Output: four channels

Parsed by `astra/grammar/parser.py::parse_stage` into a frozen
`StageOutput`:

| Channel | Form | Disposition |
|---|---|---|
| THINK | `<think>...</think>` | Private cognition. Stripped before anything operator-facing. `think_blocks` retained for forensics. |
| TOOL | `<tool name="...">body</tool>` | Ship API invocation. JSON body parsed best-effort; on parse failure `arguments={}` and `raw_body` is preserved for the adapter LLM to normalize. Never executed directly. |
| SPEECH | default-untagged prose | Operator-facing; leak-scanned (`scan_speech`), then TTS (UE5) / transcript (textverse). |
| SILENCE | empty output | Legal primitive: `silence = (speech == "") and (not tool_calls)`. She chose not to speak. |

Order rule (§4.3): `<think>` first matches the reasoning-model training
distribution; tool calls and speech interleave freely after.

## 3. Parser rules that carry weight

Implemented in `parser.py` + `strip_rules.py`; tested in
`tests/test_grammar_parser.py` + `tests/test_strip_rule.py`:

- **Tools inside think are cognition, not action.** Tool discovery runs on
  the text with think-block contents scrubbed; a `<tool>` written inside
  `<think>` is never dispatched.
- **Unclosed `<think>` ⇒ malformed.** The entire output is treated as
  cognition: no speech, no tools, `malformed=True`. Fail-closed — a runaway
  think block cannot leak to the operator.
- **A single malformed tool block never crashes parsing** (best-effort JSON,
  exceptions do not propagate).
- **Speech start** is computed after stripping think and tool spans
  (`find_speech_start`); surviving prose is SPEECH by definition.

## 4. Substrate Normalizer (§15.7 Surface 4 sub-layer)

`astra/llm/client.py::chat_complete` normalizes model-specific reasoning
formats into the canonical inline form before parsing:

| Substrate | Native form | Normalization |
|---|---|---|
| DeepSeek-R1 family | inline `<think>...</think>` | none needed |
| Qwen 3.x (`--reasoning-format deepseek-legacy`) | side-channel `reasoning_content` | synthesized into inline `<think>` |
| Novita Qwen 3.6 | side-channel `reasoning_content` | same |
| future models | per-substrate instance | add a normalizer case |

This keeps the parser substrate-portable: one grammar, many models. A model
swap requires sysprompt loader + LoRA + tokenizer config + (if needed) a
normalizer case (§4.1 plus the v0.129-TENTATIVE fourth item).

**Variant-tag rule (v0.130 / F-LIVE-11, caught live):** variant reasoning
tags (`<thinking>`, model-family spellings) canonicalize to `<think>`
BEFORE parsing (`normalize_reasoning_tags`); an UNCLOSED variant fails
CLOSED — the whole emission is treated as private cognition, never
speech. The live catch (1153 chars of raw cognition entering the SPEECH
channel through an unknown tag spelling) is the permanent regression
test (`tests/test_live_instrument_fixes.py`).

## 5. Defense in depth for the think channel

Three independent layers (§4.3): LoRA discipline (future fine-tune),
sampling grammar (future llama.cpp grammar), and the regex post-filter
(implemented: think-strip + leak scan). Today the post-filter carries the
load; the other two arrive with ASTRA-A0 and the llama.cpp integration.

## 6. TENTATIVE (v0.129 draft; NOT yet enforced in grammar)

- `<grounded src="...">` on ASTRA speech numerics and `<val src="...">` on
  Narrator numerics, with bare-digit rejection at parse time (§15.6
  parse-time enforcement). Current state: numerics are validated
  post-emission by `CalculatorBoundValidator` (numeric-substring grounding
  against a trace pool), not at the grammar layer.
- Somatic input as machine-readable `<somatic_signals>` for the Narrator
  (the SomaticSignal list exists; the Narrator request carries prose).

## 7. Cross-references

Spec v0.128 §4.3 (Master Contract), §6.2, §15.6, §15.7 · v0.129-TENTATIVE
§4.3 edits + §15.7.x · `docs/narrator-spec.md` · canonical STAGE Protocol
v1.0 (external, CC-BY-4.0).
