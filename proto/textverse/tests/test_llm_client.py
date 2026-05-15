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
    """Non-retryable HTTP error → raises immediately, no retries.

    Uses 500 (not 429/503) so the retry path doesn't fire; the test
    verifies the failure-path message format.
    """
    transport = httpx.MockTransport(lambda req: httpx.Response(500, text="broken"))
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    with pytest.raises(LLMClientError, match="HTTP 500"):
        await client.chat_complete("ping")


@pytest.mark.asyncio
async def test_chat_complete_normalizes_reasoning_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Day 4 empirical finding: Qwen 3.x emits reasoning_content as a SEPARATE
    field (not inline `<think>`). The client must normalize by injecting
    `<think>{reasoning}</think>` before content so the STAGE parser sees the
    canonical shape regardless of substrate.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Yes. Third pole, 4.2% above baseline.",
                            "reasoning_content": (
                                "Operator is casual; brief is right. "
                                "Reference cycle 46 and the tolerance bound."
                            ),
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    out = await client.chat_complete("perception")
    # Canonical shape: <think>...</think> precedes speech
    assert out.startswith("<think>")
    assert "Operator is casual" in out
    assert "</think>" in out
    speech_start = out.index("</think>") + len("</think>")
    speech = out[speech_start:].strip()
    assert speech == "Yes. Third pole, 4.2% above baseline."


@pytest.mark.asyncio
async def test_chat_complete_no_reasoning_field_passes_content_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the model emits inline `<think>` (deepseek-r1 style), the response
    has no separate `reasoning_content` field — content is passed through
    untouched.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "<think>inline</think>\n\nspeech body",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    out = await client.chat_complete("perception")
    assert out == "<think>inline</think>\n\nspeech body"


@pytest.mark.asyncio
async def test_chat_complete_empty_reasoning_field_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty / whitespace-only reasoning_content is NOT injected as a think block."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "just speech",
                            "reasoning_content": "   \n  \t  ",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    out = await client.chat_complete("perception")
    assert out == "just speech"
    assert "<think>" not in out


@pytest.mark.asyncio
async def test_chat_complete_sends_authorization_header_when_api_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When `api_key` is provided, the request must include
    `Authorization: Bearer <key>` (Novita / OpenAI-compat cloud endpoints).
    """
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(
        base_url="http://test.invalid",
        sysprompt="sys",
        api_key="sk_test_dummy",
    )
    await client.chat_complete("ping")
    assert captured_headers.get("authorization") == "Bearer sk_test_dummy"


@pytest.mark.asyncio
async def test_chat_complete_no_auth_header_when_api_key_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backwards compat: local llama-server has no auth — no Authorization
    header should be sent when api_key is absent.
    """
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    await client.chat_complete("ping")
    assert "authorization" not in captured_headers


@pytest.mark.asyncio
async def test_chat_complete_merges_extra_payload_into_request_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`extra_payload` keys must appear at the JSON top level (Novita's
    `chat_template_kwargs: {"enable_thinking": false}` thinking toggle).
    """
    captured_payload: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payload.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(
        base_url="http://test.invalid",
        sysprompt="sys",
        extra_payload={"chat_template_kwargs": {"enable_thinking": False}},
    )
    await client.chat_complete("ping")
    assert captured_payload.get("chat_template_kwargs") == {"enable_thinking": False}
    # Standard payload keys are still present.
    assert "messages" in captured_payload
    assert "temperature" in captured_payload


@pytest.mark.asyncio
async def test_chat_complete_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    """Novita rate-limits Sculptor's tight judge-call burst with HTTP 429.
    The client must retry with backoff; the test mocks two 429s followed
    by a 200 and verifies the final response is returned.
    """
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] < 3:
            return httpx.Response(429, headers={"retry-after": "0"}, text="slow down")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    out = await client.chat_complete("ping")
    assert out == "ok"
    assert call_count["n"] == 3   # 2 retries + 1 success


@pytest.mark.asyncio
async def test_chat_complete_raises_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the server keeps returning 429 past the retry budget, raise."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(429, headers={"retry-after": "0"}, text="still slow")

    transport = httpx.MockTransport(handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    client = LLMClient(base_url="http://test.invalid", sysprompt="sys")
    with pytest.raises(LLMClientError, match="HTTP 429"):
        await client.chat_complete("ping")
    # MAX_RETRIES=5 means: 1 initial attempt + 5 retries = 6 calls
    assert call_count["n"] == 6


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
