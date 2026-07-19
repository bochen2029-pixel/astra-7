"""OpenAI-compat HTTP+SSE client for llama-server instances.

This is the substrate-portable Surface 1 implementation (spec v0.129 §4.1):
chat completions endpoint, SSE streaming, sampling parameter modulation,
sysprompt grounding. Used by the three bundles (ASTRA / Narrator / Adapter)
against three independent llama-server instances on three ports.

The client is async-only (anyio-friendly). Day 5 orchestrator coordinates
all three concurrently. Day 4 wires the protocol; the smoke test verifies
the chain works end-to-end against a real llama-server.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, Literal

import httpx
from httpx_sse import aconnect_sse
from pydantic import BaseModel, ConfigDict, Field

# OpenAI-compat default; llama.cpp accepts this path
DEFAULT_CHAT_PATH: str = "/v1/chat/completions"

# Retry policy for transient cloud-API failures (Novita 429s during Sculptor's
# tight judge-call burst, etc.). Local llama-server doesn't return these so
# the retry path is a no-op there.
_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 503})
_MAX_RETRIES: int = 5
_BASE_RETRY_DELAY_S: float = 1.0
_MAX_RETRY_DELAY_S: float = 30.0


def _retry_delay(resp: httpx.Response, attempt: int) -> float | None:
    """Return seconds to sleep before next attempt, or None if no more retries.

    Honors a numeric `Retry-After` header when the server provides one;
    otherwise uses exponential backoff capped at `_MAX_RETRY_DELAY_S`.
    """
    if resp.status_code not in _RETRYABLE_STATUSES:
        return None
    if attempt >= _MAX_RETRIES:
        return None
    retry_after = resp.headers.get("retry-after")
    if retry_after:
        try:
            parsed = float(retry_after)
        except ValueError:
            parsed = None
        if parsed is not None:
            return min(_MAX_RETRY_DELAY_S, max(0.0, parsed))
    backoff: float = _BASE_RETRY_DELAY_S * (2 ** attempt)
    return min(_MAX_RETRY_DELAY_S, backoff)


class ChatMessage(BaseModel):
    """One message in the chat completion request."""

    model_config = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


class SamplingParams(BaseModel):
    """Inference parameter modulation per spec §4.1 Substrate Contract."""

    model_config = ConfigDict(frozen=True)

    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    top_p: float = Field(gt=0.0, le=1.0, default=0.9)
    top_k: int = Field(ge=0, default=40)
    max_tokens: int = Field(gt=0, default=2048)
    seed: int | None = None  # None = nondeterministic; int = reproducible


class LLMClientError(RuntimeError):
    """Raised on HTTP failure, SSE parse error, or invalid response shape."""


class LLMClient:
    """Async OpenAI-compat client for one llama-server instance.

    The base URL is per-instance: each bundle owns its own client pointed at
    the appropriate port (ASTRA: 8080, Narrator: 8081, Adapter: 8082 per
    ARCHITECTURE.md §6.5).

    Sysprompt is set at construct time and prepended to every chat. The
    client holds no other conversation state — the harness owns memory.
    """

    def __init__(
        self,
        base_url: str,
        sysprompt: str,
        *,
        chat_path: str = DEFAULT_CHAT_PATH,
        timeout_s: float = 600.0,
        model_name: str = "default",
        api_key: str | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.sysprompt = sysprompt
        self.chat_path = chat_path
        self.timeout_s = timeout_s
        self.model_name = model_name
        self.api_key = api_key
        self.extra_payload = dict(extra_payload) if extra_payload else {}

    def _build_messages(self, user_text: str) -> list[ChatMessage]:
        return [
            ChatMessage(role="system", content=self.sysprompt),
            ChatMessage(role="user", content=user_text),
        ]

    def _build_payload(
        self,
        messages: list[ChatMessage],
        params: SamplingParams,
        stream: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": params.temperature,
            "top_p": params.top_p,
            "top_k": params.top_k,
            "max_tokens": params.max_tokens,
            "stream": stream,
        }
        if params.seed is not None:
            payload["seed"] = params.seed
        # Merge extra_payload at top level. Used for Novita's
        # `chat_template_kwargs: {"enable_thinking": false}` and similar
        # OpenAI-compat extensions. Caller-provided keys override defaults.
        if self.extra_payload:
            payload.update(self.extra_payload)
        return payload

    def _build_headers(self) -> dict[str, str]:
        """Build request headers. Includes Authorization when api_key is set."""
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        """Non-streaming completion. Returns the full assistant text.

        Substrate normalization: if the server response includes a
        `reasoning_content` field separate from `content` (some models
        — Qwen 3.x with --reasoning-format deepseek, etc. — extract
        thinking into a side-channel), the client merges them into the
        canonical inline-`<think>` form the STAGE parser expects.

        This keeps the harness substrate-portable: the same parser
        works against deepseek-r1 (inline `<think>`), Qwen 3.x
        (extracted reasoning_content), and any future model with its
        own reasoning convention.
        """
        params = params or SamplingParams()
        messages = self._build_messages(user_text)
        payload = self._build_payload(messages, params, stream=False)
        headers = self._build_headers()
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            for attempt in range(_MAX_RETRIES + 1):
                resp = await client.post(
                    self.base_url + self.chat_path, json=payload, headers=headers,
                )
                if resp.status_code == 200:
                    break
                delay = _retry_delay(resp, attempt)
                if delay is None:
                    raise LLMClientError(
                        f"chat_complete HTTP {resp.status_code}: {resp.text[:200]}"
                    )
                await asyncio.sleep(delay)
            else:  # pragma: no cover — for-else only fires if loop exhausted without break
                raise LLMClientError(
                    f"chat_complete exhausted {_MAX_RETRIES} retries; "
                    f"last status {resp.status_code}",
                )
            data = resp.json()
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMClientError(f"unexpected response shape: {data}") from e
        content = message.get("content", "")
        if not isinstance(content, str):
            raise LLMClientError(f"non-string content: {type(content).__name__}")
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning.strip():
            # Substrate-portability: synthesize inline <think>...</think>
            # so the STAGE parser sees canonical shape.
            content = f"<think>\n{reasoning.strip()}\n</think>\n\n{content}"
        return content

    async def chat_stream(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        """Streaming completion. Yields delta token strings as they arrive.

        Stops yielding when the server sends `[DONE]` or closes the stream.
        Each yielded chunk is the `choices[0].delta.content` from one SSE event.
        """
        params = params or SamplingParams()
        messages = self._build_messages(user_text)
        payload = self._build_payload(messages, params, stream=True)
        headers = self._build_headers()
        async with httpx.AsyncClient(timeout=self.timeout_s) as client, aconnect_sse(
            client, "POST", self.base_url + self.chat_path, json=payload, headers=headers,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.data == "[DONE]":
                    return
                try:
                    chunk = json.loads(sse.data)
                except json.JSONDecodeError:
                    continue
                try:
                    delta = chunk["choices"][0]["delta"]
                except (KeyError, IndexError, TypeError):
                    continue
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield content

    async def health(self) -> bool:
        """Probe `/health`. Returns True iff the server reports OK.

        Some endpoints (llama-server) expose `/health`; others (Novita,
        Anthropic, OpenAI) don't. When `/health` returns non-200, fall
        back to a minimal chat completion (max_tokens=1) as the liveness
        probe. The fallback also validates auth.

        Same retry-with-backoff policy as `chat_complete`: transient
        429/503 on the chat-probe path get retried before reporting
        unhealthy (B2 fix — the first 20-iter Novita run hit per-hour
        quota mid-run and 8 iterations aborted without retry).
        """
        headers = self._build_headers()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.base_url + "/health", headers=headers)
                if resp.status_code == 200:
                    return True
                # Fallback: tiny chat completion to confirm endpoint + auth.
                probe = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": "."}],
                    "max_tokens": 1,
                    "temperature": 0.0,
                }
                for attempt in range(_MAX_RETRIES + 1):
                    resp2 = await client.post(
                        self.base_url + self.chat_path, json=probe, headers=headers,
                    )
                    if resp2.status_code == 200:
                        return True
                    delay = _retry_delay(resp2, attempt)
                    if delay is None:
                        return False
                    await asyncio.sleep(delay)
                return False
        except httpx.HTTPError:
            return False
