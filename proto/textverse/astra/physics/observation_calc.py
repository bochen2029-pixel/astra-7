"""Observation Calculator — spec v0.128 §6.3.

Every render-path body query and every Narrator-LLM physics_query routes
through this module. No other module computes `body_state(t_cosmic)` for
rendering. The Time Contract evolves on `t_cosmic`; observation is a
derived query, not a state mutation.

The math lives in proto/astra_nexus; this module wraps the C++ stdio
ops and returns typed Pydantic results. Routing every numeric through
here gives the calculator-bound LLM agency (§15.6) its enforcement point.

**T2.1 (2026-05-16, audit D5 + G3 closure):** the prior surface was a
33-line re-export shim. This commit converts it to the real §6.3 module
by adding:
- `ObservableState` Pydantic model mirroring the C++ struct (with
  d_proper, the 6 redshift fields, t_emit, apparent_rate,
  time_reversed, and the v0.128 D1 flags beyond_photon_history +
  beyond_hubble_horizon).
- `observe()` typed wrapper that calls the C++ `observe` stdio op
  and returns ObservableState.
- `kepler_at()`, `composition_rule_evaluate()`, `retarded_time_solve()`
  thin wrappers around the corresponding §6.4 Narrator-LLM tool ops.

The wrappers can be called in two modes:
- **Standalone**: pass a NexusBridge instance, or default-construct
  one (spawns its own astra_nexus.exe subprocess; closes on garbage
  collection).
- **Shared**: pass an existing NexusBridge to share a single
  subprocess across many calls (more efficient for hot paths like
  perception assembly).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from astra.physics.nexus_bridge import (
    NexusBridge,
    NexusBridgeError,
    NexusResponse,
    compute_apparent_rate,
)

# Regime label literal — matches astra_nexus parse_regime_string acceptance.
RegimeLabel = Literal[
    "REST", "STL_NONREL", "STL_REL",
    "WARP_CHARGE", "WARP_CRUISE", "WARP_SHUTDOWN",
    "GRAVITY_WELL", "CRYOSLEEP",
]


class Vec3Arg(BaseModel):
    """Vec3 wire shape for the stdio `observe` op."""

    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    z: float


class ObservableState(BaseModel):
    """Per spec v0.128 §6.3 — full retarded-time + redshift composition.

    Renamed from `Observable` per audit D1 (2026-05-15). Fields mirror
    the C++ `ObservableState` struct in [proto/astra_nexus.cpp:245+].
    Booleans on the wire are 0/1 numerics; this model coerces them to
    Python bool.
    """

    model_config = ConfigDict(frozen=True)

    d_proper: float = Field(ge=0.0)
    v_radial: float                     # positive = receding
    z_cosmo: float
    z_kin: float
    z_metric: float
    z_total: float
    t_emit: float                       # retarded time (cosmic seconds)
    apparent_rate: float                # dt_emit/dt_cosmic; < 0 in WARP recede
    time_reversed: bool
    beyond_photon_history: bool         # §3.11: t_emit < body_t_source_start
    beyond_hubble_horizon: bool         # §3.12: d_proper > c/H_0


def _coerce_observable(raw: dict[str, float]) -> ObservableState:
    """Map the C++ stdio dict result (with 0/1 bool encoding) to ObservableState."""
    return ObservableState(
        d_proper=raw["d_proper"],
        v_radial=raw["v_radial"],
        z_cosmo=raw["z_cosmo"],
        z_kin=raw["z_kin"],
        z_metric=raw["z_metric"],
        z_total=raw["z_total"],
        t_emit=raw["t_emit"],
        apparent_rate=raw["apparent_rate"],
        time_reversed=bool(raw["time_reversed"]),
        beyond_photon_history=bool(raw["beyond_photon_history"]),
        beyond_hubble_horizon=bool(raw["beyond_hubble_horizon"]),
    )


def observe(
    *,
    ship_pos: tuple[float, float, float],
    ship_velocity: tuple[float, float, float],
    t_cosmic: float,
    body_pos: tuple[float, float, float],
    body_metric_shift: float = 0.0,
    regime: RegimeLabel = "REST",
    body_t_source_start: float | None = None,
    bridge: NexusBridge | None = None,
) -> ObservableState:
    """Full §6.3 observe(): retarded-time + redshift composition for one body.

    Calls the C++ `observe` stdio op (added in commit fe91036) and
    returns a typed ObservableState. When `bridge` is None, a fresh
    NexusBridge is spawned for this call and closed on completion;
    pass a long-lived bridge for hot-path calls.

    `body_t_source_start` is the cosmic-time epoch at which the body
    began emitting; when omitted, defaults to -inf (no anchor; the
    `beyond_photon_history` flag is always False).
    """
    args: dict[str, object] = {
        "ship_pos": {"x": ship_pos[0], "y": ship_pos[1], "z": ship_pos[2]},
        "ship_velocity": {
            "x": ship_velocity[0], "y": ship_velocity[1], "z": ship_velocity[2],
        },
        "t_cosmic": t_cosmic,
        "body_pos": {"x": body_pos[0], "y": body_pos[1], "z": body_pos[2]},
        "body_metric_shift": body_metric_shift,
        "regime": regime,
    }
    if body_t_source_start is not None:
        args["body_t_source_start"] = body_t_source_start

    if bridge is not None:
        resp = bridge.call("observe", **args)
    else:
        with NexusBridge() as br:
            resp = br.call("observe", **args)
    if not resp.ok or not isinstance(resp.result, dict):
        raise NexusBridgeError(
            f"observe() failed: ok={resp.ok}, error={resp.error}, "
            f"result_type={type(resp.result).__name__}",
        )
    return _coerce_observable(resp.result)


def kepler_at(
    *,
    a: float,
    e: float,
    period: float,
    t0: float,
    t: float,
    bridge: NexusBridge | None = None,
) -> float:
    """§6.4 Narrator tool — orbital true anomaly at time t."""
    args: dict[str, object] = {"a": a, "e": e, "period": period, "t0": t0, "t": t}
    if bridge is not None:
        resp = bridge.call("kepler_at", **args)
    else:
        with NexusBridge() as br:
            resp = br.call("kepler_at", **args)
    if not resp.ok or not isinstance(resp.result, float):
        raise NexusBridgeError(
            f"kepler_at() failed: ok={resp.ok}, error={resp.error}",
        )
    return resp.result


def composition_rule_evaluate(
    *,
    w_warp: float,
    grav_factor: float,
    gamma_kin: float,
    warp_active: bool,
    bridge: NexusBridge | None = None,
) -> float:
    """§3.2 dτ/dt_cosmic = f_warp · grav_factor / γ_kin."""
    args: dict[str, object] = {
        "W_warp": w_warp,
        "grav_factor": grav_factor,
        "gamma_kin": gamma_kin,
        "warp_active": 1 if warp_active else 0,
    }
    if bridge is not None:
        resp = bridge.call("composition_rule_evaluate", **args)
    else:
        with NexusBridge() as br:
            resp = br.call("composition_rule_evaluate", **args)
    if not resp.ok or not isinstance(resp.result, float):
        raise NexusBridgeError(
            f"composition_rule_evaluate() failed: ok={resp.ok}, error={resp.error}",
        )
    return resp.result


def retarded_time_solve(
    *,
    d_proper: float,
    z_cosmo: float,
    t_cosmic: float,
    bridge: NexusBridge | None = None,
) -> float:
    """§3.11 retarded-time solve: t_emit = t_cosmic − lookback(d, z)."""
    args: dict[str, object] = {
        "d_proper": d_proper,
        "z_cosmo": z_cosmo,
        "t_cosmic": t_cosmic,
    }
    if bridge is not None:
        resp = bridge.call("retarded_time_solve", **args)
    else:
        with NexusBridge() as br:
            resp = br.call("retarded_time_solve", **args)
    if not resp.ok or not isinstance(resp.result, float):
        raise NexusBridgeError(
            f"retarded_time_solve() failed: ok={resp.ok}, error={resp.error}",
        )
    return resp.result


__all__ = [
    "NexusBridge",
    "NexusBridgeError",
    "NexusResponse",
    "ObservableState",
    "RegimeLabel",
    "Vec3Arg",
    "composition_rule_evaluate",
    "compute_apparent_rate",
    "kepler_at",
    "observe",
    "retarded_time_solve",
]
