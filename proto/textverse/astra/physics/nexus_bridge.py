"""nexus_bridge — JSON-over-stdio bridge to proto/astra_nexus.exe.

Spawns the C++ binary in --stdio-server mode and exchanges line-delimited
JSON requests/responses. The bridge is the calculator-bound SDK boundary
(spec v0.129 §15.6): every numeric value used in operator-facing speech
must trace to a result returned by this bridge.

Lifecycle:
- `NexusBridge()` constructs (does not spawn yet).
- `start()` spawns the subprocess and verifies `health`.
- `call(op, **args)` sends a JSON line and returns the parsed response.
- `close()` closes stdin, waits for clean exit (or terminate after timeout).
- Context-manager friendly: `with NexusBridge() as b: ...`.

The bridge is single-threaded (one in-flight request at a time). Day 5
orchestrator manages bridge lifecycle per scenario; tests open/close
per-test for isolation.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class NexusBridgeError(RuntimeError):
    """Raised on JSON-RPC error, parse failure, or unexpected EOF."""


class NexusResponse(BaseModel):
    """Parsed response from the C++ stdio server.

    Wire format: one JSON object per line. `ok=true` with `result`, or
    `ok=false` with `error`. No interleaved noise.

    `result` may be a number, string, OR object — the object form is
    used by §6.4 ops that return a struct (e.g. `observe` returns the
    full Observable as a JSON object). Booleans inside object results
    are encoded by C++ as 0/1 numerics for wire-format simplicity.
    """

    model_config = ConfigDict(frozen=True)

    ok: bool
    result: float | str | dict[str, Any] | None = None
    error: str | None = None


def _resolve_default_binary() -> Path:
    """Locate astra_nexus.exe. Override path via ASTRA_NEXUS_BIN env var."""
    env = os.environ.get("ASTRA_NEXUS_BIN")
    if env:
        return Path(env)
    # This file is at proto/textverse/astra/physics/nexus_bridge.py;
    # the binary lives at proto/astra_nexus.exe (three parents up).
    here = Path(__file__).resolve()
    return here.parent.parent.parent.parent / "astra_nexus.exe"


class NexusBridge:
    """JSON-over-stdio bridge to proto/astra_nexus.exe."""

    def __init__(self, binary_path: Path | str | None = None) -> None:
        self.binary_path = (
            Path(binary_path) if binary_path is not None else _resolve_default_binary()
        )
        self._proc: subprocess.Popen[str] | None = None

    def start(self) -> None:
        """Spawn the subprocess and verify connectivity via a health call."""
        if self._proc is not None:
            raise NexusBridgeError("bridge already started")
        if not self.binary_path.is_file():
            raise NexusBridgeError(
                f"nexus binary not found at {self.binary_path}; "
                f"set ASTRA_NEXUS_BIN or build proto/astra_nexus.exe via "
                f"proto/build.bat"
            )
        self._proc = subprocess.Popen(
            [str(self.binary_path), "--stdio-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
        )
        resp = self.call("health")
        if not resp.ok or resp.result != "alive":
            self.close()
            raise NexusBridgeError(f"health check failed: {resp}")

    def call(self, op: str, /, **args: Any) -> NexusResponse:
        """Send one request, read one response. Raises on protocol failure."""
        if self._proc is None:
            raise NexusBridgeError("bridge not started (call start() first)")
        if self._proc.stdin is None or self._proc.stdout is None:
            raise NexusBridgeError("subprocess pipes closed unexpectedly")
        req: dict[str, Any] = {"op": op}
        if args:
            req["args"] = args
        line = json.dumps(req, separators=(",", ":"))
        try:
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
        except (OSError, BrokenPipeError) as e:
            raise NexusBridgeError(f"failed to send request: {e}") from e
        out = self._proc.stdout.readline()
        if not out:
            raise NexusBridgeError(f"EOF from nexus subprocess; op={op}")
        try:
            return NexusResponse.model_validate_json(out.strip())
        except Exception as e:
            raise NexusBridgeError(f"bad response JSON: {out!r}: {e}") from e

    def close(self, timeout_s: float = 2.0) -> None:
        """Gracefully terminate the subprocess. Idempotent."""
        if self._proc is None:
            return
        if self._proc.stdin is not None:
            with contextlib.suppress(OSError):
                self._proc.stdin.close()
        try:
            self._proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
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
        self.close()


def compute_apparent_rate(
    v_radial_m_s: float,
    regime: str,
    *,
    bridge: NexusBridge | None = None,
) -> float:
    """Regime-dispatched apparent rate `dt_emit/dt_recv` (spec §3.11).

    Formulas:
        STL_REL:           √((1-β)/(1+β))         (SR longitudinal Doppler)
        WARP_CRUISE:       1 - β                  (classical retarded-time)
        REST/STL_NONREL:   1 - β                  (linear approx)

    where β = v_radial / c, v_radial > 0 for recession.

    Args:
        v_radial_m_s: ship's radial velocity in m/s, positive = receding.
        regime: regime name string ("REST", "STL_NONREL", "STL_REL",
            "WARP_CHARGE", "WARP_CRUISE", "WARP_SHUTDOWN", "GRAVITY_WELL",
            "CRYOSLEEP"). Bitmask composition not supported at this entry;
            pass the propulsion regime directly.
        bridge: optional pre-started bridge (saves spawn cost on hot path).
            If None, a transient bridge is created for this call only.

    Returns:
        The apparent rate. Strictly positive in STL_REL; can be zero
        (warp horizon) or negative (warp v_app > c) in WARP_CRUISE.
    """
    if bridge is not None:
        resp = bridge.call("compute_apparent_rate", v_radial=v_radial_m_s, regime=regime)
        if not resp.ok or not isinstance(resp.result, int | float):
            raise NexusBridgeError(f"compute_apparent_rate failed: {resp}")
        return float(resp.result)
    with NexusBridge() as b:
        return compute_apparent_rate(v_radial_m_s, regime, bridge=b)
