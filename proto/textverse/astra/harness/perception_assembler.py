"""Perception assembler — composes STAGE input bundles per spec §4.3 + §6.4.

Two paths:
- Template-based (Day 5 default): `assemble_perception_bundle()` —
  deterministic prose rendering from state. Fast, no LLM cost.
- Narrator-LLM-based (T2.3, 2026-05-16): `assemble_perception_bundle_via_narrator()`
  — generates the bundle via NarratorBundle.compose() with
  calculator-bound auto-validation against a trace pool of state
  numerics. The §6.4 production path; falls back to template if
  narrator_bundle is None.

Per §15.5 Progressive Specification: the assembler's surface is
`assemble(state_bus, operator_text, reel_retrievals, somatic_note) →
perception_bundle: str` regardless of impl. The harness contract
doesn't change.

Output shape (four XML-tagged sections, per the canonical perception
bundle in proto/textverse/scenarios/watch_47_morning.md):

    <state>
    [ship and universe state in tight prose]
    </state>

    <somatic>
    [functional-state banner]
    </somatic>

    <recent>
    [REEL retrievals, one per line]
    </recent>

    <operator>
    [operator's input verbatim; empty for SILENCE]
    </operator>
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from astra.harness.reel import ReelEntry
from astra.harness.somatic import SomaticSignal, aggregate
from astra.ship.api import regime_label
from astra.state_bus import StateBus

if TYPE_CHECKING:
    from astra.llm.narrator_bundle import NarratorBundle


def _render_state(state_bus: StateBus) -> str:
    """Compose the `<state>` section from a StateBus snapshot.

    Day 5 v0 produces a 3-5 sentence τ_ship-anchored prose summary. No
    wall-clock leak: all time references are τ_ship or t_cosmic, never
    real-world dates.
    """
    time = state_bus.time
    lines = [
        f"τ_ship: watch {int(time.tau_ship)}, mid-shift.",
        f"regime: {regime_label(state_bus.regime)} near origin.",
    ]
    if time.rapidity_zeta == (0.0, 0.0, 0.0):
        lines.append("ship vector stable, no thrust, no warp.")
    else:
        lines.append("ship in motion; see propulsion telemetry.")

    if state_bus.procedural_body_states:
        names = ", ".join(sorted(state_bus.procedural_body_states))
        lines.append(f"bodies in catalog: {names}.")

    return "\n".join(lines)


def _render_somatic(somatic_note: str | None) -> str:
    """Compose the `<somatic>` section.

    If no note is provided, return an empty body — the orchestrator's
    consumer (ASTRA-LLM) handles empty sections gracefully.
    """
    return somatic_note.strip() if somatic_note else ""


def _render_recent(retrievals: list[ReelEntry]) -> str:
    """Compose the `<recent>` section from REEL retrievals."""
    if not retrievals:
        return ""
    lines = [
        f"[watch {int(e.tau_ship)}] {e.body}"
        for e in retrievals
    ]
    return "\n".join(lines)


def _render_operator(operator_text: str) -> str:
    """Compose the `<operator>` section, preserving SILENCE for empty input."""
    return operator_text.strip()


def assemble_perception_bundle(
    state_bus: StateBus,
    operator_text: str = "",
    reel_retrievals: list[ReelEntry] | None = None,
    somatic_note: str | None = None,
    somatic_signals: list[SomaticSignal] | None = None,
) -> str:
    """Compose the four-section perception bundle for ASTRA-LLM input.

    Template path: deterministic, no LLM cost. The §6.4 Narrator-LLM
    path lives in `assemble_perception_bundle_via_narrator()`.

    Somatic channel (v0.129 §6.3.1 residue): when `somatic_signals` is
    provided it takes precedence and the banner is composed by the Somatic
    Aggregator (an explicitly empty list means "quiet body", empty banner).
    The legacy scenario-author-typed `somatic_note` remains the fallback
    path and is unchanged.

    Returns the assembled string ready to send to ASTRA-LLM as user-message
    content (the canonical sysprompt + STAGE addendum are loaded by the
    AstraBundle at construction time).
    """
    state_body = _render_state(state_bus)
    if somatic_signals is not None:
        somatic_body = aggregate(somatic_signals)
    else:
        somatic_body = _render_somatic(somatic_note)
    recent_body = _render_recent(reel_retrievals or [])
    operator_body = _render_operator(operator_text)

    sections = [
        f"<state>\n{state_body}\n</state>",
        f"<somatic>\n{somatic_body}\n</somatic>",
        f"<recent>\n{recent_body}\n</recent>",
        f"<operator>\n{operator_body}\n</operator>",
    ]
    return "\n\n".join(sections)


def _build_narrator_composition_request(
    state_bus: StateBus,
    operator_text: str,
    retrievals: list[ReelEntry],
    somatic_note: str | None,
) -> str:
    """Render the user-message the Narrator-LLM receives.

    Passes the raw State Bus snapshot as JSON so every numeric the
    Narrator might cite is verifiable against the trace pool. Recent
    REEL entries + somatic note + operator text round out the context.
    The Narrator's sysprompt (loaded by NarratorBundle) defines the
    output shape; this request body provides the data only.
    """
    state_json = state_bus.model_dump_json(indent=2)
    retrievals_json = json.dumps(
        [
            {
                "tau_ship": e.tau_ship,
                "t_cosmic_at_write": e.t_cosmic_at_write,
                "body": e.body,
                "irreversibility_flag": e.irreversibility_flag,
            }
            for e in retrievals
        ],
        indent=2,
    )
    return (
        "Generate a four-section perception bundle for ASTRA-LLM in "
        "the canonical <state>/<somatic>/<recent>/<operator> form.\n\n"
        f"State Bus snapshot (JSON):\n{state_json}\n\n"
        f"Recent REEL retrievals (JSON):\n{retrievals_json}\n\n"
        "Somatic note (sensor reading this tick):\n"
        f"{somatic_note or '(none)'}\n\n"
        "Operator input (verbatim; may be empty for SILENCE):\n"
        f"{operator_text or '(none)'}\n\n"
        "Every numeric you cite MUST appear in the State Bus snapshot "
        "or REEL entries above. Use τ_ship + watch numbers (no Earth "
        "dates). Brief — this is ASTRA's input, not narrative."
    )


def _build_narrator_trace_pool(
    state_bus: StateBus,
    somatic_note: str | None,
    retrievals: list[ReelEntry],
) -> list[str]:
    """Build the trace pool the calculator-bound validator searches.

    Concatenated as a single string by `validate_speech`; any numeric
    token in the Narrator's output that's a substring of any pool
    entry is considered grounded. State Bus is serialized as JSON so
    every numeric field is present.
    """
    pool: list[str] = [state_bus.model_dump_json()]
    if somatic_note:
        pool.append(somatic_note)
    for entry in retrievals:
        pool.append(entry.body)
        pool.append(str(entry.tau_ship))
        pool.append(str(entry.t_cosmic_at_write))
    return pool


async def assemble_perception_bundle_via_narrator(
    state_bus: StateBus,
    narrator_bundle: NarratorBundle,
    operator_text: str = "",
    reel_retrievals: list[ReelEntry] | None = None,
    somatic_note: str | None = None,
) -> str:
    """§6.4 Narrator-LLM path: compose the perception bundle via the LLM.

    The NarratorBundle's calculator-bound validator (hard severity by
    default) wraps the compose() call: any numeric in the generated
    bundle that doesn't trace to the State Bus JSON snapshot or REEL
    entry text triggers a retry with halved temperature, up to
    `validator.max_retries` attempts. After exhausted retries, raises
    `NarratorValidationError`.

    Closes audit Tier 2 #4 (G15 Narrator track) by making the §6.4
    surface usable end-to-end; combined with the Narrator-side
    validator from T2.2, §15.6 universality holds in the live path.
    """
    retrievals = reel_retrievals or []
    composition_request = _build_narrator_composition_request(
        state_bus, operator_text, retrievals, somatic_note,
    )
    trace_pool = _build_narrator_trace_pool(state_bus, somatic_note, retrievals)
    return await narrator_bundle.compose(composition_request, trace_pool=trace_pool)
