"""OpenAI-compat HTTP+SSE client for llama-server instances.

This is the substrate-portable Surface 1 implementation (spec v0.128 §4.1):
chat completions endpoint, SSE streaming, sampling parameter modulation,
sysprompt grounding. Used by the three bundles (ASTRA / Narrator / Adapter)
against three independent llama-server instances on three ports.

The client is async-only (anyio-friendly). Day 5 orchestrator coordinates
all three concurrently. Day 4 wires the protocol; the smoke test verifies
the chain works end-to-end against a real llama-server.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, Literal

import httpx
from httpx_sse import aconnect_sse
from pydantic import BaseModel, ConfigDict, Field

# OpenAI-compat default; llama.cpp accepts this path
DEFAULT_CHAT_PATH: str = "/v1/chat/completions"


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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.sysprompt = sysprompt
        self.chat_path = chat_path
        self.timeout_s = timeout_s
        self.model_name = model_name

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
        return payload

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        """Non-streaming completion. Returns the full assistant text."""
        params = params or SamplingParams()
        messages = self._build_messages(user_text)
        payload = self._build_payload(messages, params, stream=False)
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.post(self.base_url + self.chat_path, json=payload)
            if resp.status_code != 200:
                raise LLMClientError(
                    f"chat_complete HTTP {resp.status_code}: {resp.text[:200]}"
                )
            data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMClientError(f"unexpected response shape: {data}") from e
        if not isinstance(content, str):
            raise LLMClientError(f"non-string content: {type(content).__name__}")
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
        async with httpx.AsyncClient(timeout=self.timeout_s) as client, aconnect_sse(
            client, "POST", self.base_url + self.chat_path, json=payload
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
        """Probe `/health`. Returns True iff the server reports OK."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.base_url + "/health")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
