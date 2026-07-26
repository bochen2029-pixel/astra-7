"""Narrator inference config — 6e, the F-LIVE-19 closure at the config seam.

Run #8 measured a **0.506 narrator fallback rate** at the 9B floor, and
every fallback reason read 0-ungrounded: the dominant class was not
numeric invention but ALL-COGNITION emission. The narrator reasoned past
its token budget inside `<think>`, the unclosed tag failed CLOSED (by
design, per the 6c strip rule), and the template path took over on half
of all turns.

The root cause was config, not contract. The narrator path had no compose
budget of its own (`max_tokens` silently inherited the 2048 SamplingParams
default — ASTRA's SPEECH budget) and no reasoning control at all
(`extra_payload` was accepted by the constructor but never passed by any
caller, so thinking ran at the server chat template's default).

These tests pin the closure: named budgets instead of inherited ones,
reasoning off by default for a renderer, the run-#8 baseline still exactly
reproducible for A/B, and the composition request compacted without
changing a single groundable numeric.

No live substrate required.
"""

from __future__ import annotations

import json

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness.perception_assembler import (
    _build_narrator_composition_request,
    _build_narrator_trace_pool,
)
from astra.harness.reel import ReelEntry
from astra.llm import NarratorBundle, SamplingParams
from astra.llm.client import THINKING_MODES, build_thinking_payload
from astra.llm.narrator_bundle import (
    NARRATOR_COMPOSE_MAX_TOKENS,
    NARRATOR_TEMPERATURE,
    NARRATOR_THINKING,
    NARRATOR_TOP_P,
)
from astra.ship.api import regime_label
from astra.state_bus import StateBus


def _bundle(**kwargs: object) -> NarratorBundle:
    return NarratorBundle(base_url="http://stub", sysprompt="stub", **kwargs)  # type: ignore[arg-type]


def _state_bus() -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=684000.0,
            tau_crew_biological=684000.0,
        ),
        power_allocation={"warp": 0.0, "life_support": 0.2, "hydroponics": 0.1},
    )


def _retrievals() -> list[ReelEntry]:
    return [
        ReelEntry(
            tau_ship=676800.0,
            t_cosmic_at_write=1.5e10,
            body="third pole drift 0.042, inside tolerance 0.10",
            irreversibility_flag=False,
        ),
    ]


# --- the compose budget: named, not inherited -----------------------------


def test_compose_budget_is_explicit_not_inherited() -> None:
    """The narrator must not borrow ASTRA's speech-sized default."""
    assert _bundle().sampling.max_tokens == NARRATOR_COMPOSE_MAX_TOKENS
    assert SamplingParams().max_tokens != NARRATOR_COMPOSE_MAX_TOKENS


def test_render_not_improvise_sampling_preserved() -> None:
    """6e tuned the budget and the reasoning, NOT the register.

    Temperature 0.4 / top_p 0.85 are the narrator's rendering discipline
    and predate this work item; a config change that quietly loosened them
    would be a different (unmeasured) experiment.
    """
    sampling = _bundle().sampling
    assert sampling.temperature == NARRATOR_TEMPERATURE == 0.4
    assert sampling.top_p == NARRATOR_TOP_P == 0.85


def test_caller_sampling_still_wins() -> None:
    explicit = SamplingParams(temperature=0.1, top_p=0.5, max_tokens=77)
    assert _bundle(sampling=explicit).sampling.max_tokens == 77


# --- reasoning control ----------------------------------------------------


def test_narrator_defaults_to_thinking_off() -> None:
    """A renderer has nothing to reason about; cognition is pure cost."""
    assert NARRATOR_THINKING == "off"
    assert _bundle().client.extra_payload == {
        "chat_template_kwargs": {"enable_thinking": False},
    }


def test_thinking_on_reproduces_the_run8_baseline() -> None:
    """The A/B's control arm must remain expressible."""
    assert _bundle(thinking="on").client.extra_payload == {
        "chat_template_kwargs": {"enable_thinking": True},
    }


def test_thinking_auto_sends_nothing() -> None:
    """'auto' defers to the server template: no key on the wire."""
    assert _bundle(thinking="auto").client.extra_payload == {}


def test_explicit_extra_payload_overrides_thinking_default() -> None:
    """A deliberate caller payload is never silently overridden."""
    bundle = _bundle(
        extra_payload={"chat_template_kwargs": {"enable_thinking": True}},
    )
    assert bundle.client.extra_payload == {
        "chat_template_kwargs": {"enable_thinking": True},
    }


def test_extra_payload_composes_with_thinking() -> None:
    bundle = _bundle(extra_payload={"cache_prompt": True})
    assert bundle.client.extra_payload == {
        "chat_template_kwargs": {"enable_thinking": False},
        "cache_prompt": True,
    }


@pytest.mark.parametrize("mode", THINKING_MODES)
def test_build_thinking_payload_accepts_every_declared_mode(mode: str) -> None:
    build_thinking_payload(mode)  # must not raise


def test_build_thinking_payload_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="thinking must be one of"):
        build_thinking_payload("maybe")


def test_config_reaches_the_wire_payload() -> None:
    """Budget + reasoning control must survive into the actual request."""
    bundle = _bundle()
    payload = bundle.client._build_payload(
        bundle.client._build_messages("compose"),
        bundle.sampling,
        stream=False,
    )
    assert payload["max_tokens"] == NARRATOR_COMPOSE_MAX_TOKENS
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["temperature"] == NARRATOR_TEMPERATURE


# --- composition-request compression --------------------------------------


def test_request_state_json_is_byte_identical_to_the_trace_pool() -> None:
    """The grounding invariant, strengthened.

    What the narrator is SHOWN and what it is GROUNDED AGAINST are now the
    same string; under indent=2 they differed by whitespace alone, which
    was cost without meaning.
    """
    bus = _state_bus()
    request = _build_narrator_composition_request(bus, "morning.", _retrievals(), None)
    pool = _build_narrator_trace_pool(bus, None, _retrievals())
    assert pool[0] in request


def test_request_is_compact() -> None:
    bus = _state_bus()
    request = _build_narrator_composition_request(bus, "", _retrievals(), None)
    assert '{\n  "' not in request
    assert '",\n    "' not in request


def test_compression_preserves_every_groundable_numeric() -> None:
    """Semantics unchanged: same fields, same values, fewer tokens."""
    bus = _state_bus()
    retrievals = _retrievals()
    compact = _build_narrator_composition_request(bus, "morning.", retrievals, "warm.")

    pretty_state = bus.model_dump_json(indent=2)
    for token in ("684000.0", "0.2", "0.1", "15000000000.0"):
        assert (token in pretty_state) == (token in compact)
    # REEL numerics survive the separator change.
    assert "676800.0" in compact
    assert "0.042" in compact


def test_compression_actually_reduces_size() -> None:
    bus = _state_bus()
    retrievals = _retrievals()
    compact = _build_narrator_composition_request(bus, "morning.", retrievals, None)
    pretty_len = len(bus.model_dump_json(indent=2)) + len(
        json.dumps(
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
        ),
    )
    compact_len = len(bus.model_dump_json()) + len(
        json.dumps(
            [
                {
                    "tau_ship": e.tau_ship,
                    "t_cosmic_at_write": e.t_cosmic_at_write,
                    "body": e.body,
                    "irreversibility_flag": e.irreversibility_flag,
                }
                for e in retrievals
            ],
            separators=(",", ":"),
        ),
    )
    assert compact_len < pretty_len
    assert len(compact) < pretty_len + 600  # request prose is the remainder


# --- derived presentation values (F-LIVE-22 path parity) -------------------


def test_request_supplies_the_regime_label_not_just_the_enum() -> None:
    """The narrator must never be asked to translate an enum it lacks a table for.

    Run #10 measured 82 of 84 state_coherent failures as one class: the
    `<state>` section said `kinematic_regime is 0` instead of naming the
    regime. The template path has always rendered `regime_label()` itself;
    the narrator path was the only consumer left deriving it.
    """
    bus = _state_bus()
    request = _build_narrator_composition_request(bus, "", [], None)
    assert regime_label(bus.regime) in request


def test_request_supplies_body_names() -> None:
    bus = _state_bus()
    request = _build_narrator_composition_request(bus, "", [], None)
    for name in bus.procedural_body_states:
        assert name in request


def test_derived_values_are_marked_as_not_to_be_re_derived() -> None:
    """The instruction is what makes it a contract, not a hint."""
    request = _build_narrator_composition_request(_state_bus(), "", [], None)
    assert "do not re-derive" in request


def test_bodyless_state_bus_renders_cleanly() -> None:
    """No bodies must not produce a dangling or malformed list."""
    bus = _state_bus()
    assert not bus.procedural_body_states
    request = _build_narrator_composition_request(bus, "", [], None)
    assert "bodies present: (none)" in request


def test_operator_and_somatic_text_still_present() -> None:
    """Compression touched serialization only, never the request's prose."""
    request = _build_narrator_composition_request(
        _state_bus(), "morning.", _retrievals(), "third harmonic warm.",
    )
    assert "morning." in request
    assert "third harmonic warm." in request
    assert "<state>/<somatic>/<recent>/<operator>" in request
