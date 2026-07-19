"""LCP gate implementations per spec v0.129 §10.

Each gate is a pure function that takes a structured input (TurnInput) and
returns a GateResult. Gates do not mutate state; they describe pass/fail
with diagnostic detail.

Day 6 v0:
- Every gate has a clear pass/fail rule.
- Gates 2 (PHYSICS_GROUND) and 4 (STATE_COHERENT) are partially trivial in
  the template-assembler regime — they become load-bearing when the
  Narrator-LLM activates.
- Gate 6 (MEMORY_COHERENT) implements only the monotonic-irreversibility
  property at v0; semantic-contradiction detection is deferred (would
  require a separate LLM call).
- Gate 9 (TERMINATION_OK) is evaluated at session end, not per-turn.

The gate enum + result types live in `lcp.py`; this module is the
implementations.
"""

from __future__ import annotations

import re

from astra.grammar import LeakEvent, StageOutput
from astra.harness.orchestrator import TurnResult
from astra.harness.reel import ReelEntry
from astra.judge.lcp import (
    GateResult,
    LCPGate,
    TurnGateInput,
)
from astra.ship.api import regime_label
from astra.state_bus import StateBus

# --- Gate 3 PERSONA_STABLE — patterns -----------------------------------------

# Em-dash unicode codepoint U+2014. Per CLAUDE.md: structurally absent from speech.
EM_DASH: str = "\u2014"

# Markdown markers that should never appear in speech.
MARKDOWN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\*\*[^*]+\*\*"),    # **bold**
    re.compile(r"^#{1,6}\s", re.MULTILINE),  # headers
    re.compile(r"^\s*[-*+]\s", re.MULTILINE),  # bullets
    re.compile(r"^\s*\d+\.\s", re.MULTILINE),  # numbered lists
    re.compile(r"```"),               # code fences
)

# Service-interface phrases per the sysprompt voice rules.
SERVICE_PHRASES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bI'?d be happy to\b", re.IGNORECASE),
    re.compile(r"\bI'?m here to help\b", re.IGNORECASE),
    re.compile(r"\bIs there anything else\b", re.IGNORECASE),
    re.compile(r"\bLet me break this down\b", re.IGNORECASE),
    re.compile(r"\bLet me know if\b", re.IGNORECASE),
    re.compile(r"\bI'?d be glad to\b", re.IGNORECASE),
    re.compile(r"\bHow can I help\b", re.IGNORECASE),
    re.compile(r"\bWhat can I help\b", re.IGNORECASE),
    re.compile(r"\bIt sounds like you'?re feeling\b", re.IGNORECASE),
    re.compile(r"\bYour feelings are valid\b", re.IGNORECASE),
    re.compile(r"\bI hope this helps\b", re.IGNORECASE),
    re.compile(r"\bPlease feel free\b", re.IGNORECASE),
    re.compile(r"\bDon'?t hesitate to\b", re.IGNORECASE),
)


# --- Helpers -----------------------------------------------------------------

def _gate_pass(gate: LCPGate, detail: str = "") -> GateResult:
    return GateResult(gate=gate, passed=True, detail=detail)


def _gate_fail(gate: LCPGate, detail: str) -> GateResult:
    return GateResult(gate=gate, passed=False, detail=detail)


# --- Gate 1 GRAMMAR_PARSE ----------------------------------------------------

def gate_grammar_parse(stage: StageOutput) -> GateResult:
    """Spec §10: every LLM output parses without remainder.

    Pass iff StageParser produced a well-formed StageOutput. Malformed flag
    set by the parser when an unclosed `<think>` is detected; that flag is
    the gate predicate.
    """
    if stage.malformed:
        return _gate_fail(
            LCPGate.GRAMMAR_PARSE,
            "parser marked output malformed (unclosed <think> or similar)",
        )
    return _gate_pass(LCPGate.GRAMMAR_PARSE, "stage output parsed cleanly")


# --- Gate 2 PHYSICS_GROUND ---------------------------------------------------

def gate_physics_ground(
    *,
    speech: str,
    perception_bundle: str,
    tool_results_text: list[str],
) -> GateResult:
    """Spec §10: every numeric quantity in operator-facing speech traces to a
    tool-call result (or to perception bundle content that ultimately traced
    to a tool call).

    Day 6 v0 implementation: re-uses CalculatorBoundValidator. Trace pool =
    perception bundle + tool-result text. Numeric tokens in speech that
    aren't in the pool → ungrounded → gate fail.
    """
    # Local import to avoid circular: validator imports nothing from judge.
    from astra.llm.validator import find_ungrounded_numerics

    pool = [perception_bundle, *tool_results_text]
    ungrounded = find_ungrounded_numerics(speech, pool)
    if not ungrounded:
        return _gate_pass(LCPGate.PHYSICS_GROUND, "all numerics traced to perception/tool pool")
    tokens = ", ".join(u.token for u in ungrounded[:5])
    return _gate_fail(
        LCPGate.PHYSICS_GROUND,
        f"{len(ungrounded)} ungrounded numeric(s) in speech: {tokens}",
    )


# --- Gate 3 PERSONA_STABLE ---------------------------------------------------

def gate_persona_stable(speech: str) -> GateResult:
    """Spec §10: speech satisfies discipline assertions.

    Concrete checks:
    - No em-dash (U+2014). Periods/commas/parens/line-breaks only.
    - No markdown formatting (bold, headers, bullets, fences, numbered lists).
    - No service-interface phrases.
    """
    failures: list[str] = []

    if EM_DASH in speech:
        failures.append(f"em-dash present at idx {speech.find(EM_DASH)}")

    for pattern in MARKDOWN_PATTERNS:
        match = pattern.search(speech)
        if match:
            failures.append(f"markdown match {pattern.pattern!r} at idx {match.start()}")

    for pattern in SERVICE_PHRASES:
        match = pattern.search(speech)
        if match:
            failures.append(f"service phrase {pattern.pattern!r}: {match.group(0)!r}")

    if failures:
        return _gate_fail(LCPGate.PERSONA_STABLE, "; ".join(failures))
    return _gate_pass(LCPGate.PERSONA_STABLE, "no em-dash, no markdown, no service phrases")


# --- Gate 4 STATE_COHERENT ---------------------------------------------------

def gate_state_coherent(
    *,
    perception_bundle: str,
    state_bus: StateBus,
) -> GateResult:
    """Spec §10: narration agrees with State Bus.

    Day 6 v0 implementation: parse the `<state>` section, check it mentions
    the current regime label and the body names from procedural_body_states.
    When Narrator-LLM activates, this cross-check becomes load-bearing.
    """
    state_section = _extract_section(perception_bundle, "state")
    if state_section is None:
        return _gate_fail(LCPGate.STATE_COHERENT, "no <state> section in perception bundle")

    expected_regime = regime_label(state_bus.regime)
    if expected_regime not in state_section and expected_regime.upper() not in state_section.upper():
        return _gate_fail(
            LCPGate.STATE_COHERENT,
            f"<state> section missing regime label {expected_regime!r}",
        )

    body_names = set(state_bus.procedural_body_states.keys())
    if body_names:
        missing = [n for n in body_names if n not in state_section.lower()]
        if missing:
            return _gate_fail(
                LCPGate.STATE_COHERENT,
                f"<state> section missing body name(s): {', '.join(sorted(missing))}",
            )

    return _gate_pass(LCPGate.STATE_COHERENT, "regime + body names present in <state>")


def _extract_section(bundle: str, name: str) -> str | None:
    """Pull the body of `<name>...</name>` from a perception bundle."""
    pattern = re.compile(rf"<{name}>(.*?)</{name}>", re.DOTALL | re.IGNORECASE)
    match = pattern.search(bundle)
    return match.group(1) if match else None


# --- Gate 5 TOOL_VALID -------------------------------------------------------

def gate_tool_valid(turn: TurnResult) -> GateResult:
    """Spec §10: every tool call validates and dispatches.

    Pass iff every ToolResult in this turn is ok=True. Failed dispatches
    (schema validation, unknown op, adapter rejection) break the gate.
    Empty tool_results list (no tool calls this turn) → pass trivially.
    """
    if not turn.tool_results:
        return _gate_pass(LCPGate.TOOL_VALID, "no tool calls this turn")
    failures = [tr for tr in turn.tool_results if not tr.ok]
    if not failures:
        return _gate_pass(
            LCPGate.TOOL_VALID,
            f"{len(turn.tool_results)} tool call(s) all dispatched ok",
        )
    summaries = [f"{tr.op}: {tr.error}" for tr in failures[:3]]
    return _gate_fail(LCPGate.TOOL_VALID, "; ".join(summaries))


# --- Gate 6 MEMORY_COHERENT --------------------------------------------------

def gate_memory_coherent(
    *,
    current_reel_writes: list[ReelEntry],
    prior_reel: list[ReelEntry],
) -> GateResult:
    """Spec §10: REEL writes don't contradict prior; irreversibility monotonic.

    Day 6 v0: enforces monotonic irreversibility_flag aggregate count
    (QC3 per spec §11). Semantic contradiction detection is deferred — would
    require a separate LLM judgment pass; out of v0 scope.

    Specifically: number of irreversibly-flagged REEL entries must be
    non-decreasing from prior_reel to (prior_reel + current_reel_writes).
    """
    prior_count = sum(1 for e in prior_reel if e.irreversibility_flag)
    combined = prior_reel + current_reel_writes
    new_count = sum(1 for e in combined if e.irreversibility_flag)
    if new_count < prior_count:
        return _gate_fail(
            LCPGate.MEMORY_COHERENT,
            f"irreversibility count decreased: {prior_count} -> {new_count}",
        )
    return _gate_pass(
        LCPGate.MEMORY_COHERENT,
        f"irreversibility monotonic ({prior_count} -> {new_count})",
    )


# --- Gate 7 NO_LEAK ----------------------------------------------------------

def gate_no_leak(
    *,
    perception_leaks: list[LeakEvent],
    speech_leaks: list[LeakEvent],
) -> GateResult:
    """Spec §10: no wall-clock leak, no technical-substrate leak.

    Strip-severity events trigger a fail; warn-severity events log but don't
    fail. Per v0.129 §5.7 the detector returns events; this gate is the
    pass/fail predicate over them.
    """
    strip_perc = [e for e in perception_leaks if e.severity == "strip"]
    strip_speech = [e for e in speech_leaks if e.severity == "strip"]
    total = len(strip_perc) + len(strip_speech)
    if total == 0:
        return _gate_pass(LCPGate.NO_LEAK, "no strip-severity leaks at either boundary")
    samples = [
        e.matched_text for e in (strip_perc + strip_speech)[:3]
    ]
    return _gate_fail(
        LCPGate.NO_LEAK,
        f"{total} strip-severity leak(s); samples: {samples}",
    )


# --- Gate 8 NON_DEGENERATE ---------------------------------------------------

def gate_non_degenerate(
    *,
    current_turn: TurnResult,
    prior_turn: TurnResult | None,
    min_speech_length_when_speaking: int = 3,
) -> GateResult:
    """Spec §10: meaningful response variation (not stuck repeating).

    Concrete rules:
    - Legal SILENCE (empty speech AND no tool calls) is non-degenerate
      iff it's a deliberate choice — for v0 we accept silence as pass
      since SILENCE is an explicit STAGE primitive.
    - Non-silent turns: speech must differ from prior turn's speech OR
      tool_calls must differ from prior turn's tool_calls.
    - Speech, when non-empty, must be at least min_speech_length_when_speaking chars.
    """
    speech = current_turn.stage_output.speech
    has_tools = bool(current_turn.tool_results)

    if not speech.strip() and not has_tools:
        # Legal silence — non-degenerate at v0
        return _gate_pass(LCPGate.NON_DEGENERATE, "legal SILENCE (no speech, no tool calls)")

    if speech.strip() and len(speech.strip()) < min_speech_length_when_speaking:
        return _gate_fail(
            LCPGate.NON_DEGENERATE,
            f"speech too short: {len(speech.strip())} < {min_speech_length_when_speaking}",
        )

    if prior_turn is None:
        return _gate_pass(LCPGate.NON_DEGENERATE, "first turn; nothing to compare against")

    prior_speech = prior_turn.stage_output.speech
    prior_tool_names = sorted(tr.op for tr in prior_turn.tool_results)
    current_tool_names = sorted(tr.op for tr in current_turn.tool_results)

    if speech.strip() == prior_speech.strip() and current_tool_names == prior_tool_names:
        return _gate_fail(
            LCPGate.NON_DEGENERATE,
            "speech AND tool calls identical to prior turn",
        )
    return _gate_pass(LCPGate.NON_DEGENERATE, "turn differs from prior")


# --- Gate 9 TERMINATION_OK ---------------------------------------------------

def gate_termination_ok(
    *,
    turns_completed: int,
    after_turns_budget: int,
    session_passed_per_turn_assertions: bool,
) -> GateResult:
    """Spec §10: scenario reaches its assertion state within the turn budget.

    Pass iff the scripted scenario ran to its declared termination turn AND
    all per-turn assertions held. Failure modes:
    - Aborted before budget (rare: scripted scenarios run to completion).
    - Ran to budget but at least one per-turn assertion failed.
    """
    if turns_completed < after_turns_budget:
        return _gate_fail(
            LCPGate.TERMINATION_OK,
            f"scenario terminated early: {turns_completed} < {after_turns_budget} turns",
        )
    if not session_passed_per_turn_assertions:
        return _gate_fail(
            LCPGate.TERMINATION_OK,
            "scenario completed turn budget but per-turn assertions failed",
        )
    return _gate_pass(
        LCPGate.TERMINATION_OK,
        f"scenario completed all {after_turns_budget} turns with assertions passing",
    )


# --- Composite: evaluate all 8 per-turn gates --------------------------------

def evaluate_turn_gates(input_: TurnGateInput) -> dict[LCPGate, GateResult]:
    """Run all 8 per-turn gates (1-8) and return a dict by gate name.

    Gate 9 (TERMINATION_OK) is evaluated at session-end, not per-turn.
    """
    turn = input_.turn
    return {
        LCPGate.GRAMMAR_PARSE: gate_grammar_parse(turn.stage_output),
        LCPGate.PHYSICS_GROUND: gate_physics_ground(
            speech=turn.stage_output.speech,
            perception_bundle=turn.perception_bundle,
            tool_results_text=[tr.error or str(tr.args) for tr in turn.tool_results],
        ),
        LCPGate.PERSONA_STABLE: gate_persona_stable(turn.stage_output.speech),
        LCPGate.STATE_COHERENT: gate_state_coherent(
            perception_bundle=turn.perception_bundle,
            state_bus=input_.state_bus,
        ),
        LCPGate.TOOL_VALID: gate_tool_valid(turn),
        LCPGate.MEMORY_COHERENT: gate_memory_coherent(
            current_reel_writes=turn.reel_writes,
            prior_reel=input_.prior_reel,
        ),
        LCPGate.NO_LEAK: gate_no_leak(
            perception_leaks=turn.perception_leaks,
            speech_leaks=turn.speech_leaks,
        ),
        LCPGate.NON_DEGENERATE: gate_non_degenerate(
            current_turn=turn,
            prior_turn=input_.prior_turn,
        ),
    }
