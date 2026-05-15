"""llama-server sidecar lifecycle per spec v0.128 §4.1 + ARCHITECTURE §6.5.

Spawns one or more `llama-server` processes, each on its own port with its
own GGUF model + sysprompt context. The three-instance setup (ASTRA on 8080,
Narrator on 8081, Adapter on 8082) keeps each model's KV cache stable and
its persona intact — running them as one model with sysprompt-swap mid-
conversation would corrupt context.

The default binary path is `C:\\llama.cpp\\llama-server.exe` per Bo's setup;
override via `LLAMA_SERVER_BIN` env var or constructor argument.

This module is lifecycle-only. The HTTP+SSE protocol lives in client.py.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import time
from pathlib import Path
from types import TracebackType
from typing import Self

import httpx
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_BINARY: str = r"C:\llama.cpp\llama-server.exe"
DEFAULT_HOST: str = "127.0.0.1"


class LlamaServerError(RuntimeError):
    """Raised on spawn failure, health-check timeout, or unexpected exit."""


class LlamaServerConfig(BaseModel):
    """One llama-server instance configuration."""

    model_config = ConfigDict(frozen=True)

    name: str                                    # "astra" / "narrator" / "adapter"
    model_path: Path
    port: int = Field(ge=1, le=65535)
    ctx_size: int = Field(ge=512, default=131_072)
    n_gpu_layers: int = Field(ge=0, default=99)   # 99 = "all on GPU"
    chat_template_kwargs: dict[str, str] = Field(default_factory=dict)
    reasoning_format: str = "deepseek"            # surface <think> cleanly for Qwen 3.x
    extra_args: list[str] = Field(default_factory=list)


class LlamaServerInstance:
    """One llama-server subprocess. Tracks lifecycle and exposes a base URL.

    Not thread-safe. The orchestrator (Day 5) owns one instance per bundle.
    """

    def __init__(
        self,
        config: LlamaServerConfig,
        *,
        binary_path: Path | str | None = None,
        host: str = DEFAULT_HOST,
    ) -> None:
        self.config = config
        self.host = host
        self.binary_path = Path(
            binary_path
            if binary_path is not None
            else os.environ.get("LLAMA_SERVER_BIN", DEFAULT_BINARY)
        )
        self._proc: subprocess.Popen[bytes] | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.config.port}"

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _build_argv(self) -> list[str]:
        argv = [
            str(self.binary_path),
            "--model", str(self.config.model_path),
            "--host", self.host,
            "--port", str(self.config.port),
            "--ctx-size", str(self.config.ctx_size),
            "--n-gpu-layers", str(self.config.n_gpu_layers),
            "--reasoning-format", self.config.reasoning_format,
        ]
        for k, v in self.config.chat_template_kwargs.items():
            argv.extend(["--chat-template-kwargs", f"{k}={v}"])
        argv.extend(self.config.extra_args)
        return argv

    def start(self, *, health_timeout_s: float = 120.0, poll_interval_s: float = 1.0) -> None:
        """Spawn the subprocess and wait for /health to return 200."""
        if self.is_running:
            raise LlamaServerError(f"instance '{self.config.name}' already started")
        if not self.binary_path.is_file():
            raise LlamaServerError(
                f"llama-server binary not found at {self.binary_path}; "
                f"set LLAMA_SERVER_BIN or pass binary_path="
            )
        if not self.config.model_path.is_file():
            raise LlamaServerError(
                f"model GGUF not found at {self.config.model_path}"
            )

        self._proc = subprocess.Popen(
            self._build_argv(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Poll /health until ready or timeout
        deadline = time.monotonic() + health_timeout_s
        last_err: Exception | None = None
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                exit_code = self._proc.returncode
                raise LlamaServerError(
                    f"instance '{self.config.name}' exited "
                    f"during startup (code {exit_code})"
                )
            try:
                resp = httpx.get(self.base_url + "/health", timeout=2.0)
                if resp.status_code == 200:
                    return
            except httpx.HTTPError as e:
                last_err = e
            time.sleep(poll_interval_s)

        # Timed out — terminate and raise
        self.stop()
        raise LlamaServerError(
            f"instance '{self.config.name}' health check timed out "
            f"after {health_timeout_s}s (last error: {last_err})"
        )

    def stop(self, *, terminate_timeout_s: float = 5.0) -> None:
        """Gracefully terminate; SIGKILL after timeout. Idempotent."""
        if self._proc is None:
            return
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=terminate_timeout_s)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    self._proc.wait(timeout=2.0)
        self._proc = None

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()


class LlamaServerOrchestrator:
    """Manages multiple llama-server instances as one unit.

    Day 5 wires this to spawn ASTRA / Narrator / Adapter as a coordinated
    set. start_all() spawns ASTRA first (the heaviest model), then the
    smaller two in parallel. stop_all() reverses the order.

    Failure path: if any instance fails to come healthy, the orchestrator
    stops all previously-started instances. No zombies.
    """

    def __init__(
        self,
        instances: list[LlamaServerInstance],
    ) -> None:
        if not instances:
            raise ValueError("orchestrator requires at least one instance")
        self.instances = instances
        self._started: list[LlamaServerInstance] = []

    def start_all(self, *, health_timeout_s: float = 120.0) -> None:
        """Start every instance in order. Roll back on failure."""
        try:
            for inst in self.instances:
                inst.start(health_timeout_s=health_timeout_s)
                self._started.append(inst)
        except Exception:
            self.stop_all()
            raise

    def stop_all(self) -> None:
        """Stop every started instance in reverse order. Idempotent."""
        while self._started:
            inst = self._started.pop()
            with contextlib.suppress(Exception):
                inst.stop()

    def __enter__(self) -> Self:
        self.start_all()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop_all()
