"""Day 4 tests for the OpenAI-compat LLM client.

Uses httpx MockTransport to verify request/response shapes, SSE parsing,
and error paths without a real llama-server.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest

from astra.llm import ChatMessage, LLMClient, LLMClientError, SamplingParams

# --- ChatMessage + SamplingParams shapes -------------------------------------

def test_chat_message_frozen() -> None:
    msg = ChatMessage(role="user", content="hello")
    try:
        msg.role = "system"
    except Exception:
        return
    raise AssertionError("ChatMessage must be frozen")


def test_sampling_params_defaults() -> None:
    p = SamplingParams()
    assert 0.0 <= p.temperature <= 2.0
    assert 0.0 < p.top_p <= 1.0
    assert p.top_k >= 0
    assert p.max_tokens > 0
    assert p.seed is None


def test_sampling_params_temperature_bounds() -> None:
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SamplingParams(temperature=-0.1)
    with pytest.raises(ValidationError):
        SamplingParams(temperature=2.5)


# --- chat_complete (non-streaming) -------------------------------------------

@pytest.mark.asyncio
async def test_chat_complete_returns_message_content(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_request: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["json"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "c1",
                "object": "chat.completion",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "hello back"}}],
            },
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="you are a test")
    out = await client.chat_complete("ping", SamplingParams(temperature=0.5, seed=42))

    assert out == "hello back"
    assert captured_request["url"] == "http://test.invalid/v1/chat/completions"
    payload = captured_request["json"]
    assert payload["messages"][0] == {"role": "system", "content": "you are a test"}
    assert payload["messages"][1] == {"role": "user", "content": "ping"}
    assert payload["temperature"] == 0.5
    assert payload["seed"] == 42
    assert payload["stream"] is False


@pytest.mark.asyncio
async def test_chat_complete_http_error_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(503, text="overloaded"))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    with pytest.raises(LLMClientError, match="HTTP 503"):
        await client.chat_complete("ping")


@pytest.mark.asyncio
async def test_chat_complete_malformed_response_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={"choices": []}))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    with pytest.raises(LLMClientError, match="unexpected response shape"):
        await client.chat_complete("ping")


# --- chat_stream (SSE) -------------------------------------------------------


def _sse_response(chunks: list[str]) -> httpx.Response:
    """Build an SSE-encoded response body from a list of delta texts.

    Wraps each delta into an OpenAI-compat SSE event, ends with `[DONE]`.
    """
    parts: list[str] = []
    for text in chunks:
        body = {"choices": [{"index": 0, "delta": {"content": text}}]}
        parts.append(f"data: {json.dumps(body)}\n\n")
    parts.append("data: [DONE]\n\n")
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        text="".join(parts),
    )


async def _collect(it: AsyncIterator[str]) -> list[str]:
    return [chunk async for chunk in it]


@pytest.mark.asyncio
async def test_chat_stream_yields_each_delta(monkeypatch: pytest.MonkeyPatch) -> None:
    deltas = ["hello", " ", "world", "."]
    transport = httpx.MockTransport(lambda req: _sse_response(deltas))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    chunks = await _collect(client.chat_stream("ping"))
    assert chunks == deltas
    assert "".join(chunks) == "hello world."


@pytest.mark.asyncio
async def test_chat_stream_stops_on_done(monkeypatch: pytest.MonkeyPatch) -> None:
    """The `data: [DONE]` sentinel terminates the iterator cleanly."""
    transport = httpx.MockTransport(lambda req: _sse_response(["a", "b"]))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    chunks = await _collect(client.chat_stream("ping"))
    assert chunks == ["a", "b"]


@pytest.mark.asyncio
async def test_chat_stream_skips_malformed_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bad JSON in an SSE event is skipped, not crashed on."""
    sse_body = (
        'data: {"choices":[{"delta":{"content":"good"}}]}\n\n'
        "data: not-valid-json\n\n"
        'data: {"choices":[{"delta":{"content":"also-good"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=sse_body
        )
    )
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    chunks = await _collect(client.chat_stream("ping"))
    assert chunks == ["good", "also-good"]


# --- health probe ------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_returns_true_on_200(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(200, text="ok"))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    assert await client.health() is True


@pytest.mark.asyncio
async def test_health_returns_false_on_500(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(500))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    assert await client.health() is False
