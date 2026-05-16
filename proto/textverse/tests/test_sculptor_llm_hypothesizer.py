"""Tests for LLMHypothesisGenerator (Stage A: local Qwen).

Mocks the LLMClient so the tests don't require a running llama-server.
Covers JSON extraction tolerance (fenced/unfenced/prose-wrapped),
schema validation, scope binding, and the four operation→transform
mappings.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest

from astra.llm.client import LLMClient, SamplingParams
from astra.sculptor import LLMHypothesisGenerator
from astra.sculptor.llm_hypothesizer import (
    _extract_json,
    _hypothesis_from_json,
)
from astra.sculptor.research_log import ResearchEntry
from astra.sculptor.scope import load_scope_contract

TEXTVERSE_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
SCOPE_PATH = TEXTVERSE_ROOT / "tuning" / "scope.yaml"


class _StubLLMClient(LLMClient):
    """LLMClient stub that returns canned text for chat_complete.

    Configurable per-test by setting `.canned_response`.
    """

    def __init__(self, canned: str = "{}") -> None:
        super().__init__(base_url="http://stub", sysprompt="stub-sys")
        self.canned_response = canned
        self.last_user_text: str = ""

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        self.last_user_text = user_text
        return self.canned_response

    async def chat_stream(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        if False:
            yield ""  # pragma: no cover

    async def health(self) -> bool:
        return True


# --- JSON extraction tolerance --------------------------------------------

def test_extract_json_plain_object() -> None:
    raw = '{"name": "x", "rationale": "y"}'
    assert _extract_json(raw) == {"name": "x", "rationale": "y"}


def test_extract_json_with_markdown_fence() -> None:
    raw = '```json\n{"name": "x"}\n```'
    assert _extract_json(raw) == {"name": "x"}


def test_extract_json_with_prose_wrapper() -> None:
    raw = 'Here is my proposal:\n\n{"name": "x", "rationale": "y"}\n\nHope this helps.'
    assert _extract_json(raw) == {"name": "x", "rationale": "y"}


def test_extract_json_raises_on_no_object() -> None:
    with pytest.raises(ValueError, match="no JSON object"):
        _extract_json("nothing here")


# --- Hypothesis schema validation -----------------------------------------

def _scope() -> Any:
    return load_scope_contract(SCOPE_PATH)


def test_hypothesis_from_json_append_paragraph() -> None:
    payload = {
        "name": "test_append",
        "rationale": "append a discipline sentence",
        "lesson_class": "persona_stability",
        "relpath": "prompts/astra_sysprompt.md",
        "operation": "append_paragraph",
        "args": {"text": "Stay terse."},
    }
    hyp = _hypothesis_from_json(payload, _scope())
    assert hyp.name == "test_append"
    assert hyp.relpath == "prompts/astra_sysprompt.md"
    assert hyp.lesson_class == "persona_stability"
    # transform_fn appends the paragraph
    out = hyp.transform_fn("baseline\n")
    assert "Stay terse." in out


def test_hypothesis_from_json_replace_substring() -> None:
    payload = {
        "name": "test_replace",
        "rationale": "narrow tone shift",
        "lesson_class": "persona_stability",
        "relpath": "prompts/narrator_sysprompt.md",
        "operation": "replace_substring",
        "args": {"old": "FOO", "new": "BAR"},
    }
    hyp = _hypothesis_from_json(payload, _scope())
    assert hyp.transform_fn("XXX FOO YYY") == "XXX BAR YYY"


def test_hypothesis_from_json_set_json_key() -> None:
    payload = {
        "name": "test_setjson",
        "rationale": "tighten temperature",
        "lesson_class": "sampling",
        "relpath": "tuning/sampling.json",
        "operation": "set_json_key",
        "args": {"key": "temperature", "value": 0.55},
    }
    hyp = _hypothesis_from_json(payload, _scope())
    new = hyp.transform_fn('{"temperature": 0.7}')
    assert json.loads(new)["temperature"] == 0.55


def test_hypothesis_from_json_rejects_out_of_scope_path() -> None:
    payload = {
        "name": "test_evil",
        "rationale": "...",
        "lesson_class": "persona_stability",
        "relpath": "astra/llm/client.py",   # locked path
        "operation": "append_paragraph",
        "args": {"text": "X"},
    }
    with pytest.raises(ValueError, match="out-of-scope"):
        _hypothesis_from_json(payload, _scope())


def test_hypothesis_from_json_rejects_unknown_operation() -> None:
    payload = {
        "name": "test_x",
        "rationale": "...",
        "lesson_class": "persona_stability",
        "relpath": "prompts/narrator_sysprompt.md",
        "operation": "delete_file",   # unknown op
        "args": {},
    }
    with pytest.raises(ValueError, match="unknown operation"):
        _hypothesis_from_json(payload, _scope())


def test_hypothesis_from_json_rejects_missing_fields() -> None:
    payload = {
        "name": "test_missing",
        # missing rationale, lesson_class, relpath, operation, args
    }
    with pytest.raises(ValueError, match="missing fields"):
        _hypothesis_from_json(payload, _scope())


# --- LLMHypothesisGenerator end-to-end via stub client --------------------

def test_llm_hypothesizer_propose_returns_hypothesis() -> None:
    canned = json.dumps({
        "name": "stub_response",
        "rationale": "test",
        "lesson_class": "persona_stability",
        "relpath": "prompts/narrator_sysprompt.md",
        "operation": "append_paragraph",
        "args": {"text": "More tightness."},
    })
    client = _StubLLMClient(canned=canned)
    gen = LLMHypothesisGenerator(client=client)
    hyp = gen.propose(
        latest_composite=None,
        recent_log=[],
        scope_contract=_scope(),
    )
    assert hyp.name == "stub_response"
    assert "More tightness." in hyp.transform_fn("base\n")
    # And the user prompt was built with scope + log context
    assert "narrator_sysprompt" in client.last_user_text
    assert "Recent iteration history" in client.last_user_text


def test_llm_hypothesizer_includes_recent_log_in_prompt() -> None:
    canned = json.dumps({
        "name": "x",
        "rationale": "y",
        "lesson_class": "persona_stability",
        "relpath": "prompts/narrator_sysprompt.md",
        "operation": "append_paragraph",
        "args": {"text": "."},
    })
    client = _StubLLMClient(canned=canned)
    gen = LLMHypothesisGenerator(client=client)
    log = [
        ResearchEntry(
            iteration=1,
            decision="falsified",
            hypothesis="prior anti-perf attempt",
            composite_score=1.45,
            lesson_class="persona_stability",
        ),
    ]
    gen.propose(
        latest_composite=None,
        recent_log=log,
        scope_contract=_scope(),
    )
    assert "iter   1" in client.last_user_text
    assert "falsified" in client.last_user_text
    assert "prior anti-perf attempt" in client.last_user_text


def test_llm_hypothesizer_raises_after_max_parse_retries() -> None:
    client = _StubLLMClient(canned="not json at all")
    gen = LLMHypothesisGenerator(client=client, max_parse_retries=1)
    with pytest.raises(RuntimeError, match="failed after 2 attempts"):
        gen.propose(
            latest_composite=None,
            recent_log=[],
            scope_contract=_scope(),
        )
