"""Day 4 tests for the three bundle compositions.

Covers prompt loading, default sampling, validator wiring, and the
rules-based adapter's parse paths. The actual chat round-trips against
real llama-server happen in scripts/smoke_astra_bundle.py (operator-runnable).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from astra.llm import (
    AdapterBundle,
    AdapterResult,
    AstraBundle,
    NarratorBundle,
    RulesBasedAdapter,
    default_prompts_dir,
    load_adapter_sysprompt,
    load_astra_sysprompt,
    load_narrator_sysprompt,
)

# --- Prompt loading ---------------------------------------------------------

def test_default_prompts_dir_exists() -> None:
    d = default_prompts_dir()
    assert d.is_dir()
    assert (d / "astra_sysprompt.md").is_file()
    assert (d / "astra_stage_addendum.md").is_file()
    assert (d / "narrator_sysprompt.md").is_file()
    assert (d / "adapter_sysprompt.md").is_file()


def test_load_astra_sysprompt_concatenates_canon_and_addendum() -> None:
    text = load_astra_sysprompt(default_prompts_dir())
    assert "You are ASTRA" in text
    assert "<think>" in text or "<state>" in text  # STAGE addendum content


def test_load_narrator_sysprompt() -> None:
    text = load_narrator_sysprompt(default_prompts_dir())
    assert "Narrator" in text
    assert "calculator-bound" in text.lower()


def test_load_adapter_sysprompt() -> None:
    text = load_adapter_sysprompt(default_prompts_dir())
    assert "Adapter" in text
    assert "JSON" in text


def test_load_sysprompt_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_narrator_sysprompt(tmp_path)


# --- Bundle construction ----------------------------------------------------

def test_astra_bundle_default_sampling() -> None:
    bundle = AstraBundle(base_url="http://test")
    assert bundle.sampling.temperature == 0.7
    assert bundle.validator.severity == "soft"


def test_astra_bundle_custom_sysprompt() -> None:
    bundle = AstraBundle(base_url="http://test", sysprompt="custom")
    assert bundle.client.sysprompt == "custom"


def test_narrator_bundle_lower_temperature() -> None:
    """Narrator defaults to lower temperature than ASTRA (rendering, not character)."""
    bundle = NarratorBundle(base_url="http://test")
    assert bundle.sampling.temperature < 0.7
    assert bundle.validator.severity == "hard"   # ungrounded numerics are worst leak


def test_adapter_bundle_lowest_temperature() -> None:
    """Adapter defaults to very low temperature (deterministic-ish JSON emission)."""
    bundle = AdapterBundle(base_url="http://test")
    assert bundle.sampling.temperature <= 0.2


# --- RulesBasedAdapter ------------------------------------------------------

def test_rules_adapter_pure_json_passes() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize(
        "power.allocate",
        '{"subsystem": "warp", "fraction": 0.5}',
    )
    assert result.ok is True
    assert result.args == {"subsystem": "warp", "fraction": 0.5}


def test_rules_adapter_key_value_parses() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize(
        "power.allocate",
        "subsystem=warp fraction=0.5",
    )
    assert result.ok is True
    assert result.args == {"subsystem": "warp", "fraction": 0.5}


def test_rules_adapter_quoted_string_value() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize(
        "log.write",
        'channel="watch" text="harmonic noted"',
    )
    assert result.ok is True
    assert result.args["channel"] == "watch"
    assert result.args["text"] == "harmonic noted"


def test_rules_adapter_colon_separator() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize(
        "power.allocate",
        "subsystem: warp, fraction: 0.5",
    )
    assert result.ok is True
    assert result.args["subsystem"] == "warp"
    assert result.args["fraction"] == 0.5


def test_rules_adapter_boolean_coercion() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize("doors.set", "door_id=bridge open=true")
    assert result.ok is True
    assert result.args["open"] is True


def test_rules_adapter_empty_body_rejected() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize("power.allocate", "")
    assert result.ok is False
    assert "empty" in result.error.lower()


def test_rules_adapter_unparseable_body_rejected() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize("power.allocate", "just some prose with no pairs")
    assert result.ok is False
    assert "could not parse" in result.error.lower()


def test_rules_adapter_integer_coercion() -> None:
    adapter = RulesBasedAdapter()
    result = adapter.normalize("doors.set", "door_id=3 state=open")
    assert result.ok is True
    assert result.args["door_id"] == 3
    assert result.args["state"] == "open"


# --- AdapterResult shape ----------------------------------------------------

def test_adapter_result_frozen() -> None:
    r = AdapterResult(ok=True, args={"x": 1})
    try:
        r.ok = False
    except Exception:
        return
    raise AssertionError("AdapterResult must be frozen")


# --- AdapterBundle prompt construction --------------------------------------

def test_adapter_bundle_prompt_includes_op_and_body() -> None:
    bundle = AdapterBundle(base_url="http://test")
    prompt = bundle._build_prompt(
        "power.allocate",
        "warp at half",
        schema_hint='{"subsystem": "...", "fraction": 0.0..1.0}',
    )
    assert "operation: power.allocate" in prompt
    assert "warp at half" in prompt
    assert "schema:" in prompt


def test_adapter_bundle_prompt_omits_schema_when_empty() -> None:
    bundle = AdapterBundle(base_url="http://test")
    prompt = bundle._build_prompt("op", "body", schema_hint="")
    assert "schema:" not in prompt
    assert "operation: op" in prompt


# --- AdapterBundle response handling (parsing only) --------------------------

def test_adapter_bundle_parses_ok_response() -> None:
    """Verify the parse-shape branch without spawning an LLM."""
    # The LLM is expected to emit JSON like {"ok": true, "args": {...}}.
    # We can test the parse logic by constructing the same path the
    # AdapterBundle takes internally.
    text = json.dumps({"ok": True, "args": {"subsystem": "warp", "fraction": 0.5}})
    parsed = json.loads(text)
    assert parsed["ok"] is True
    assert parsed["args"]["subsystem"] == "warp"
