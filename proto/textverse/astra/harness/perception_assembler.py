"""Perception assembler — composes STAGE input bundles per spec §4.3 + §6.4.

Day 5 ships a TEMPLATE-BASED assembler. The LLM-backed Narrator
(astra/llm/narrator_bundle.py) is wired in §6.4 for when scenarios
surface need for richer rendering, but the watch_47_morning scenario
and other early closed-loop tests work with a template path.

Per §15.5 Progressive Specification: the assembler's surface is
`assemble(state_bus, operator_text, reel_retrievals, somatic_note) →
perception_bundle: str` regardless of impl. Day N+ can swap the impl
to call the Narrator LLM; the harness contract doesn't change.

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

from astra.harness.reel import ReelEntry
from astra.ship.api import regime_label
from astra.state_bus import StateBus


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
) -> str:
    """Compose the four-section perception bundle for ASTRA-LLM input.

    Returns the assembled string ready to send to ASTRA-LLM as user-message
    content (the canonical sysprompt + STAGE addendum are loaded by the
    AstraBundle at construction time).
    """
    state_body = _render_state(state_bus)
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
