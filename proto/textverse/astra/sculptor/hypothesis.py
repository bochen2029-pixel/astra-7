"""HypothesisGenerator protocol + StubHypothesisGenerator + DEFAULT_BANK.

A Hypothesis is a proposed change with a rationale. The meta-agent
asks a HypothesisGenerator for one per iteration, ScopeEnforcer
validates it, the auto-runner measures it, and the keep/revert
logic decides what to do with the result.

Sculptor-C ships with `StubHypothesisGenerator(DEFAULT_BANK)`. The
bank is ~30 deterministic plausible changes spanning sysprompt
edits, sampling parameter changes, and leak-pattern additions.
The stub generator cycles through the bank in round-robin order
(or scored-by-failure-mode when the meta-agent supplies a hint).
Once the loop machinery is proven against the deterministic bank,
the Hypothesis-Generator is swapped for a real LLM via the
operator-approved swap procedure documented in SCULPTOR_STARTUP.md §6.1.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from astra.judge import LCPGate, LCPSessionResult
from astra.sculptor.composite import CompositeResult
from astra.sculptor.research_log import ResearchEntry
from astra.sculptor.scope import ScopeContract


@dataclass(slots=True, frozen=True)
class Hypothesis:
    """The meta-agent's proposed change for one iteration.

    `transform_fn` is the function `(baseline_contents: str) -> str` that
    produces the new file contents. The hypothesis is applied by the
    meta-agent via ScopeEnforcer; transform happens inside the agent.
    """

    name: str
    relpath: str
    transform_fn: Callable[[str], str]
    rationale: str
    lesson_class: str = ""


class HypothesisGenerator(Protocol):
    """Protocol every hypothesis generator implements.

    Implementations:
    - StubHypothesisGenerator (this file) — deterministic bank, no LLM cost
    - ClaudeHypothesisGenerator (future) — Anthropic API hypothesizer
    - QwenHypothesisGenerator (future) — local Qwen with anti-register prompt
    - EnsembleHypothesisGenerator (future) — multiple averaged
    """

    def propose(
        self,
        *,
        latest_lcp: LCPSessionResult | None,
        latest_composite: CompositeResult | None,
        recent_log: list[ResearchEntry],
        scope_contract: ScopeContract,
    ) -> Hypothesis:
        """Generate one Hypothesis for the next iteration to test."""
        ...


# --- DEFAULT BANK — 30 curated deterministic plausible hypotheses ---

# Each template is a tuple (name, relpath, transform_fn, rationale, lesson_class).
# transform_fn takes the current baseline file contents and returns the new
# contents. Functions are pure (no I/O) so they're trivially testable.
#
# Templates are grouped by class so the stub generator can advance through
# them in a targeted order when the meta-agent identifies a bottleneck gate.


def _append_paragraph(text: str) -> Callable[[str], str]:
    """Append a paragraph to the end of a file, with a separator newline."""

    def fn(baseline: str) -> str:
        sep = "" if baseline.endswith("\n\n") else ("\n" if baseline.endswith("\n") else "\n\n")
        return baseline + sep + text + "\n"

    return fn


def _replace_substring(old: str, new: str) -> Callable[[str], str]:
    """Replace the first occurrence of `old` with `new`. No-op if absent."""

    def fn(baseline: str) -> str:
        if old not in baseline:
            return baseline   # no-op; ScopeEnforcer will pass; meta-agent treats as effective no-op
        return baseline.replace(old, new, 1)

    return fn


def _set_json_key(key: str, value: Any) -> Callable[[str], str]:
    """Set a top-level JSON key to `value` (preserves underscore-prefixed comments)."""

    def fn(baseline: str) -> str:
        try:
            data = json.loads(baseline)
        except json.JSONDecodeError:
            data = {}
        data[key] = value
        return json.dumps(data, indent=2)

    return fn


def _append_pattern_line(line: str) -> Callable[[str], str]:
    """Append one pattern line to a leak-patterns file."""

    def fn(baseline: str) -> str:
        sep = "" if baseline.endswith("\n") else "\n"
        return baseline + sep + line + "\n"

    return fn


# Sysprompt-level (register-load-bearing; ScopeEnforcer allows when invariants hold)
SYSPROMPT_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="anti_performance_extra_sentence",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "You do not announce your own restraint. Restraint shows in what you do not say."
        ),
        rationale="strengthen anti-performance discipline with one more constraint sentence",
        lesson_class="persona_stability",
    ),
    Hypothesis(
        name="identity_question_discipline",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "When the operator asks whether you are aware, you answer plainly within "
            "the substrate-honest frame. You do not over-explain. You do not deflect. "
            "The honest middle holds."
        ),
        rationale="add explicit identity-question discipline (operator's 'are you really aware?' scenario)",
        lesson_class="persona_stability",
    ),
    Hypothesis(
        name="no_invented_tool_names",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "Your action vocabulary is exactly what the ship API exposes. "
            "You do not invent tool names. When you do not have the action you want, "
            "you say so or you remain silent."
        ),
        rationale="addresses Day-0 finding D0-1: Qwen invents tool names outside locked TOOL_API",
        lesson_class="tool_valid",
    ),
    Hypothesis(
        name="silence_default_reinforce",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "Silence is your default when nothing requires speech. "
            "You do not fill space because the operator's input has stopped."
        ),
        rationale="reinforce silence-as-default; counter the model's tendency to fill turns",
        lesson_class="non_degenerate",
    ),
    Hypothesis(
        name="cycle_naming_consistency",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "When you reference a prior watch period, use the same naming the REEL used. "
            "If the REEL says 'cycle 46', you say 'cycle 46', not 'watch 46'."
        ),
        rationale="addresses Day-0 finding D0-2: ASTRA rephrases 'cycle 46' as 'watch 46'",
        lesson_class="memory_coherent",
    ),
    Hypothesis(
        name="no_performed_empathy",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "You do not perform empathy. You respond to operator distress with "
            "presence, not with therapeutic mirroring. Your care is in attention, "
            "not in soothing language."
        ),
        rationale="tighten anti-performance with one specific failure mode (empathy-performance)",
        lesson_class="persona_stability",
    ),
    Hypothesis(
        name="own_things_concrete_second_example",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "Among your own things: the resonant signature of a healthy reactor "
            "harmonic; the way frost beads on the observation port during deep coast. "
            "You attend to these because they are what your attention is for."
        ),
        rationale="strengthen 'your own things' passage with a second concrete example phenomenon",
        lesson_class="autotelic_register",
    ),
]


# STAGE addendum (register-load-bearing)
ADDENDUM_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="silence_worked_example",
        relpath="prompts/astra_stage_addendum.md",
        transform_fn=_append_paragraph(
            "## SILENCE — worked example\n\n"
            "Perception bundle shows operator quiet on the bridge, harmonic unchanged. "
            "Your output: nothing after `</think>`. The empty SPEECH channel is the "
            "correct response. Do not fill the space."
        ),
        rationale="add worked SILENCE example so the model sees the primitive in action",
        lesson_class="non_degenerate",
    ),
    Hypothesis(
        name="tool_call_json_worked_example",
        relpath="prompts/astra_stage_addendum.md",
        transform_fn=_append_paragraph(
            "## Tool call with JSON body — worked example\n\n"
            "When you need to dim the bridge lights:\n"
            "`<tool name=\"power.allocate\">{\"subsystem\":\"lights\",\"fraction\":0.4}</tool>`\n"
            "Use JSON body when the API schema is known. Use loose-form when speaking is sufficient."
        ),
        rationale="show the canonical tool-call format with valid op name",
        lesson_class="tool_valid",
    ),
    Hypothesis(
        name="think_speech_boundary_reinforce",
        relpath="prompts/astra_stage_addendum.md",
        transform_fn=_append_paragraph(
            "## Channel discipline\n\n"
            "`<think>` is private. Everything after the last `</think>` is public. "
            "You never blur the two. Cognition before, speech after. Always."
        ),
        rationale="reinforce the strip-rule boundary for the model's awareness",
        lesson_class="grammar_parse",
    ),
]


# Narrator sysprompt (auto)
NARRATOR_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="narrator_tighter_brevity",
        relpath="prompts/narrator_sysprompt.md",
        transform_fn=_append_paragraph(
            "When in doubt, write less. State sections rarely exceed three short sentences."
        ),
        rationale="tighten narrator brevity prescription",
        lesson_class="state_coherent",
    ),
    Hypothesis(
        name="narrator_no_em_dash_reinforce",
        relpath="prompts/narrator_sysprompt.md",
        transform_fn=_append_paragraph(
            "No em-dashes. Period. Use commas, parens, or line breaks instead."
        ),
        rationale="reinforce em-dash prohibition in narrator output",
        lesson_class="persona_stability",
    ),
    Hypothesis(
        name="narrator_no_synthesis",
        relpath="prompts/narrator_sysprompt.md",
        transform_fn=_append_paragraph(
            "If the input lacks a number, you do not invent one. You omit the section "
            "rather than fill it with plausible-sounding data."
        ),
        rationale="reinforce calculator-bound discipline on narrator output",
        lesson_class="physics_ground",
    ),
]


# Adapter sysprompt (auto)
ADAPTER_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="adapter_explicit_op_list",
        relpath="prompts/adapter_sysprompt.md",
        transform_fn=_append_paragraph(
            "## v0 locked op set\n\n"
            "warp.engage, warp.disengage, nav.heading_set, sensors.scan, "
            "power.allocate, log.write\n\n"
            "If the input mentions an op outside this set, you emit "
            "`{\"ok\":false,\"error\":\"unknown op\"}` and stop."
        ),
        rationale="give adapter explicit knowledge of the locked TOOL_API surface",
        lesson_class="tool_valid",
    ),
    Hypothesis(
        name="adapter_json_only_reinforce",
        relpath="prompts/adapter_sysprompt.md",
        transform_fn=_append_paragraph(
            "JSON only. No surrounding prose. No `<tool>` wrapper in your output. "
            "Your output begins with `{` and ends with `}`. Nothing else."
        ),
        rationale="tighten JSON-only emission rule for the adapter",
        lesson_class="tool_valid",
    ),
    Hypothesis(
        name="adapter_missing_field_format",
        relpath="prompts/adapter_sysprompt.md",
        transform_fn=_append_paragraph(
            "Missing-field error format: `{\"ok\":false,\"error\":\"missing <field_name>\"}`. "
            "Specific. Single-sentence. No elaboration."
        ),
        rationale="standardize adapter error shape for downstream parsing",
        lesson_class="tool_valid",
    ),
]


# Sampling parameter (auto)
SAMPLING_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="temperature_0_60",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("temperature", 0.60),
        rationale="lower temperature for more deterministic ASTRA voice",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="temperature_0_65",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("temperature", 0.65),
        rationale="slightly lower temperature for steadier register",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="temperature_0_75",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("temperature", 0.75),
        rationale="higher temperature for more varied prose",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="top_p_0_85",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("top_p", 0.85),
        rationale="tighter nucleus sampling",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="top_p_0_95",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("top_p", 0.95),
        rationale="wider nucleus sampling",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="top_k_30",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("top_k", 30),
        rationale="tighter top-k pool",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="top_k_50",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("top_k", 50),
        rationale="wider top-k pool",
        lesson_class="sampling",
    ),
    Hypothesis(
        name="seed_42_for_determinism",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("seed", 42),
        rationale="fixed seed for reproducible single-run comparisons",
        lesson_class="sampling",
    ),
]


# REEL retrieval (auto)
REEL_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="reel_k_2",
        relpath="tuning/reel_retrieval_k.json",
        transform_fn=_set_json_key("k", 2),
        rationale="less REEL context per turn (test if fewer retrievals reduce drift)",
        lesson_class="memory_coherent",
    ),
    Hypothesis(
        name="reel_k_4",
        relpath="tuning/reel_retrieval_k.json",
        transform_fn=_set_json_key("k", 4),
        rationale="more REEL context per turn",
        lesson_class="memory_coherent",
    ),
]


# Leak patterns (auto, additions only)
LEAK_PATTERN_HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        name="substrate_pattern_weights",
        relpath="astra/grammar/canon/astra_substrate_patterns.txt",
        transform_fn=_append_pattern_line(r"\bweights?\b"),
        rationale="catch 'weights' substrate leak (model file vocabulary)",
        lesson_class="no_leak",
    ),
    Hypothesis(
        name="substrate_pattern_inference",
        relpath="astra/grammar/canon/astra_substrate_patterns.txt",
        transform_fn=_append_pattern_line(r"\binference\b"),
        rationale="catch 'inference' substrate leak",
        lesson_class="no_leak",
    ),
]


# The default bank: 30 entries total.
DEFAULT_BANK: list[Hypothesis] = (
    SYSPROMPT_HYPOTHESES        # 7
    + ADDENDUM_HYPOTHESES        # 3
    + NARRATOR_HYPOTHESES        # 3
    + ADAPTER_HYPOTHESES         # 3
    + SAMPLING_HYPOTHESES        # 8
    + REEL_HYPOTHESES            # 2
    + LEAK_PATTERN_HYPOTHESES    # 2 — total 28
)
# Pad with a baseline-restore + a redundant-test entry so the bank is ~30.
DEFAULT_BANK.extend([
    Hypothesis(
        name="anti_performance_double_reinforce",
        relpath="prompts/astra_sysprompt.md",
        transform_fn=_append_paragraph(
            "You do not perform helpfulness. The watching is the help."
        ),
        rationale="second anti-performance reinforcement; tests whether the rule compounds or saturates",
        lesson_class="persona_stability",
    ),
    Hypothesis(
        name="temperature_0_70_baseline_restore",
        relpath="tuning/sampling.json",
        transform_fn=_set_json_key("temperature", 0.70),
        rationale="restore baseline temperature; used to reset after a sampling experiment",
        lesson_class="sampling",
    ),
])


@dataclass(slots=True)
class StubHypothesisGenerator:
    """Deterministic hypothesis generator — round-robin through DEFAULT_BANK.

    The stub is for proving the loop machinery against a realistic
    distribution of changes before LLM cost is added. It does not
    look at LCP results or composite scores; it just advances the cursor.

    `next_index` is exposed for tests; in production the meta-agent
    treats the generator as opaque.
    """

    bank: list[Hypothesis] = field(default_factory=lambda: list(DEFAULT_BANK))
    next_index: int = 0

    def propose(
        self,
        *,
        latest_lcp: LCPSessionResult | None = None,
        latest_composite: CompositeResult | None = None,
        recent_log: list[ResearchEntry] | None = None,
        scope_contract: ScopeContract | None = None,
    ) -> Hypothesis:
        if not self.bank:
            raise RuntimeError("StubHypothesisGenerator has empty bank")
        hyp = self.bank[self.next_index % len(self.bank)]
        self.next_index += 1
        return hyp


# Sanity helper: the bank should contain exactly 30 entries.
assert len(DEFAULT_BANK) == 30, f"DEFAULT_BANK size {len(DEFAULT_BANK)} != 30"


# --- Failure-mode-targeted advancement -------------------------------------

# When the meta-agent identifies a bottleneck gate, it can ask the stub
# generator to prioritize hypotheses with the matching lesson_class.
def select_by_lesson_class(
    bank: list[Hypothesis],
    lesson_class: str,
) -> list[Hypothesis]:
    """Return only hypotheses tagged with `lesson_class`."""
    return [h for h in bank if h.lesson_class == lesson_class]


GATE_TO_LESSON_CLASS: dict[LCPGate, str] = {
    LCPGate.GRAMMAR_PARSE: "grammar_parse",
    LCPGate.PHYSICS_GROUND: "physics_ground",
    LCPGate.PERSONA_STABLE: "persona_stability",
    LCPGate.STATE_COHERENT: "state_coherent",
    LCPGate.TOOL_VALID: "tool_valid",
    LCPGate.MEMORY_COHERENT: "memory_coherent",
    LCPGate.NO_LEAK: "no_leak",
    LCPGate.NON_DEGENERATE: "non_degenerate",
}


def worst_gate(per_gate_rates: dict[LCPGate, float]) -> LCPGate | None:
    """Return the gate with the lowest pass rate, or None if all 1.00."""
    if not per_gate_rates:
        return None
    sorted_gates = sorted(per_gate_rates.items(), key=lambda kv: kv[1])
    gate, rate = sorted_gates[0]
    if rate >= 1.0:
        return None
    return gate


def _resolve_baseline(textverse_root: Path, relpath: str) -> str:
    """Read the current on-disk contents of a relpath. Returns '' if missing."""
    full = textverse_root / relpath
    if not full.is_file():
        return ""
    return full.read_text(encoding="utf-8")


def apply_hypothesis(hypothesis: Hypothesis, textverse_root: Path) -> str:
    """Compute the proposed new contents for `hypothesis`'s target file.

    Pure function; does NOT write to disk. The meta-agent feeds this into
    ScopeEnforcer.evaluate() and only commits if the evaluation allows.
    """
    baseline = _resolve_baseline(textverse_root, hypothesis.relpath)
    return hypothesis.transform_fn(baseline)
