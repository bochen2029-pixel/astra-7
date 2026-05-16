"""Day 2 tests for the nexus bridge.

The test module is gated by `requires_nexus`: skipped automatically when
`proto/astra_nexus.exe` is not built. To run only the bridge tests:
    uv run pytest -m requires_nexus

The Day 2 gate is `test_compute_apparent_rate_stl_rel_beta_half`: at
v_radial = 0.5c, regime = STL_REL, the SR longitudinal Doppler formula
gives √((1-0.5)/(1+0.5)) = √(1/3) ≈ 0.5774.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from astra.physics import NexusBridge, NexusBridgeError, compute_apparent_rate

C_LIGHT: float = 299_792_458.0  # m/s (exact, by SI definition)


def _nexus_binary() -> Path:
    """Resolve the binary path the bridge will use by default."""
    here = Path(__file__).resolve()
    return here.parent.parent.parent / "astra_nexus.exe"


# Module-level skip: every test here needs the C++ binary built.
pytestmark = pytest.mark.skipif(
    not _nexus_binary().is_file(),
    reason=f"proto/astra_nexus.exe not built at {_nexus_binary()}",
)


@pytest.mark.requires_nexus
def test_health_check_returns_alive() -> None:
    """A freshly started bridge responds 'alive' to a `health` request."""
    with NexusBridge() as bridge:
        resp = bridge.call("health")
        assert resp.ok is True
        assert resp.result == "alive"


@pytest.mark.requires_nexus
def test_version_op_returns_string() -> None:
    """The version op returns a free-form string identifying the binary."""
    with NexusBridge() as bridge:
        resp = bridge.call("version")
        assert resp.ok is True
        assert isinstance(resp.result, str)
        assert "astra_nexus" in resp.result


@pytest.mark.requires_nexus
def test_compute_apparent_rate_stl_rel_beta_half() -> None:
    """Day 2 gate: β=0.5 recede in STL_REL gives √(1/3) ≈ 0.5774."""
    rate = compute_apparent_rate(0.5 * C_LIGHT, "STL_REL")
    expected = (1.0 / 3.0) ** 0.5
    assert abs(rate - expected) < 1e-9
    assert abs(rate - 0.5774) < 1e-3


@pytest.mark.requires_nexus
def test_compute_apparent_rate_stl_rel_blueshift() -> None:
    """β=-0.5 approaching in STL_REL gives √3 ≈ 1.732 (blueshift)."""
    rate = compute_apparent_rate(-0.5 * C_LIGHT, "STL_REL")
    expected = 3.0**0.5
    assert abs(rate - expected) < 1e-9


@pytest.mark.requires_nexus
def test_compute_apparent_rate_stl_rel_never_reverses() -> None:
    """STL_REL is inertial: rate is strictly positive for any β ∈ (-1, 1)."""
    for beta in (-0.99, -0.5, -0.1, 0.0, 0.1, 0.5, 0.99):
        rate = compute_apparent_rate(beta * C_LIGHT, "STL_REL")
        assert rate > 0.0, f"STL_REL at β={beta} produced non-positive rate {rate}"


@pytest.mark.requires_nexus
def test_compute_apparent_rate_warp_2c_reverses() -> None:
    """WARP at v_apparent=2c: rate = -1 (reverse playback at 1× speed)."""
    rate = compute_apparent_rate(2.0 * C_LIGHT, "WARP_CRUISE")
    assert abs(rate - (-1.0)) < 1e-9
    assert rate < 0


@pytest.mark.requires_nexus
def test_compute_apparent_rate_warp_at_c_frozen() -> None:
    """WARP at v_apparent=c exactly: rate = 0 (frozen image at warp horizon)."""
    rate = compute_apparent_rate(1.0 * C_LIGHT, "WARP_CRUISE")
    assert abs(rate) < 1e-9


@pytest.mark.requires_nexus
def test_compute_apparent_rate_warp_10c_rewind() -> None:
    """WARP at v_apparent=10c: rate = -9 (rewind 9× speed)."""
    rate = compute_apparent_rate(10.0 * C_LIGHT, "WARP_CRUISE")
    assert abs(rate - (-9.0)) < 1e-9


@pytest.mark.requires_nexus
def test_compute_apparent_rate_warp_approach() -> None:
    """WARP approaching at v_apparent=-2c: rate = +3 (fast-forward 3×)."""
    rate = compute_apparent_rate(-2.0 * C_LIGHT, "WARP_CRUISE")
    assert abs(rate - 3.0) < 1e-9


@pytest.mark.requires_nexus
def test_compute_apparent_rate_rest_linear_approx() -> None:
    """REST: linear approximation 1 - β at small β."""
    rate = compute_apparent_rate(0.01 * C_LIGHT, "REST")
    assert abs(rate - 0.99) < 1e-9


@pytest.mark.requires_nexus
def test_stl_rel_vs_warp_different_at_same_v() -> None:
    """At v_radial=0.5c the two regimes give meaningfully different rates."""
    v = 0.5 * C_LIGHT
    stl = compute_apparent_rate(v, "STL_REL")
    warp = compute_apparent_rate(v, "WARP_CRUISE")
    assert abs(stl - warp) > 0.05, f"STL={stl}, WARP={warp} too close"


# --- §6.4 Narrator-LLM tool surface (D2 of audit) ------------------------

@pytest.mark.requires_nexus
def test_kepler_at_periodicity() -> None:
    """kepler_at(t0+P) == kepler_at(t0) modulo 2π."""
    args = {"a": 1.5e11, "e": 0.0167, "period": 3.156e7, "t0": 0.0}
    with NexusBridge() as bridge:
        r0 = bridge.call("kepler_at", t=0.0, **args)
        rp = bridge.call("kepler_at", t=3.156e7, **args)
        assert r0.ok and rp.ok
        import math
        diff = math.fmod(float(rp.result) - float(r0.result) + 4.0 * math.pi, 2.0 * math.pi)
        if diff > math.pi:
            diff -= 2.0 * math.pi
        assert abs(diff) < 1e-6


@pytest.mark.requires_nexus
def test_composition_rule_evaluate_rest_identity() -> None:
    """Rest, no gravity, γ=1 → composition rule = 1.0."""
    with NexusBridge() as bridge:
        r = bridge.call(
            "composition_rule_evaluate",
            W_warp=0.0, grav_factor=1.0, gamma_kin=1.0, warp_active=0,
        )
        assert r.ok and abs(float(r.result) - 1.0) < 1e-12


@pytest.mark.requires_nexus
def test_composition_rule_evaluate_warp_cruise() -> None:
    """W=1.0 with warp_active → f_warp = 0.5; rest of composition = 1.0."""
    with NexusBridge() as bridge:
        r = bridge.call(
            "composition_rule_evaluate",
            W_warp=1.0, grav_factor=1.0, gamma_kin=1.0, warp_active=1,
        )
        assert r.ok and abs(float(r.result) - 0.5) < 1e-12


@pytest.mark.requires_nexus
def test_retarded_time_solve_one_lightyear() -> None:
    """At d=1 ly with z≈0, lookback ≈ 1 year; t_emit = 0 - 1yr."""
    light_year = 9.4607e15  # ~ ly in metres (matches astra_nexus.cpp)
    with NexusBridge() as bridge:
        r = bridge.call(
            "retarded_time_solve",
            d_proper=light_year, z_cosmo=0.0, t_cosmic=0.0,
        )
        assert r.ok
        one_year_s = light_year / C_LIGHT
        assert abs(float(r.result) + one_year_s) < one_year_s * 0.01


@pytest.mark.requires_nexus
def test_observe_returns_object_result() -> None:
    """observe() returns the full ObservableState as a JSON object.

    Verifies the wire-format extension (object result) and the §6.3
    field set is present, including the v0.128 D1 additions
    `beyond_photon_history` + `beyond_hubble_horizon`.
    """
    light_year = 9.4607e15
    with NexusBridge() as bridge:
        r = bridge.call(
            "observe",
            ship_pos={"x": 0.0, "y": 0.0, "z": 0.0},
            ship_velocity={"x": 0.0, "y": 0.0, "z": 0.0},
            t_cosmic=1.0e10,
            body_pos={"x": 0.0, "y": 0.0, "z": -1.0 * light_year},
            body_metric_shift=0.0,
            regime="REST",
        )
        assert r.ok
        assert isinstance(r.result, dict)
        for k in (
            "d_proper", "v_radial", "z_cosmo", "z_kin", "z_metric", "z_total",
            "t_emit", "apparent_rate", "time_reversed",
            "beyond_photon_history", "beyond_hubble_horizon",
        ):
            assert k in r.result, f"observe result missing {k}: {r.result}"
        assert abs(r.result["d_proper"] - light_year) < 1.0
        assert abs(r.result["v_radial"]) < 1e-6
        assert abs(r.result["apparent_rate"] - 1.0) < 0.02
        assert r.result["time_reversed"] == 0.0
        assert r.result["beyond_photon_history"] == 0.0
        assert r.result["beyond_hubble_horizon"] == 0.0


@pytest.mark.requires_nexus
def test_observe_flags_beyond_photon_history() -> None:
    """When t_emit < body_t_source_start the observation crosses §3.11
    photon-source-history bound — the source wasn't yet emitting."""
    light_year = 9.4607e15
    one_year = light_year / C_LIGHT
    with NexusBridge() as bridge:
        r = bridge.call(
            "observe",
            ship_pos={"x": 0.0, "y": 0.0, "z": 0.0},
            ship_velocity={"x": 0.0, "y": 0.0, "z": 0.0},
            t_cosmic=0.0,
            body_pos={"x": 0.0, "y": 0.0, "z": -1.0 * light_year},
            body_metric_shift=0.0,
            regime="REST",
            body_t_source_start=one_year,    # source not emitting until +1yr
        )
        assert r.ok and isinstance(r.result, dict)
        # t_emit ≈ -1yr (lookback); body_t_source_start = +1yr; -1 < +1 → flag set
        assert r.result["beyond_photon_history"] == 1.0


@pytest.mark.requires_nexus
def test_observe_flags_beyond_hubble_horizon() -> None:
    """A body at 100 Gly is beyond c/H0 (~13.7 Gly @ H0=70 km/s/Mpc)."""
    light_year = 9.4607e15
    with NexusBridge() as bridge:
        r = bridge.call(
            "observe",
            ship_pos={"x": 0.0, "y": 0.0, "z": 0.0},
            ship_velocity={"x": 0.0, "y": 0.0, "z": 0.0},
            t_cosmic=1.0e10,
            body_pos={"x": 0.0, "y": 0.0, "z": -100.0e9 * light_year},
            body_metric_shift=0.0,
            regime="REST",
        )
        assert r.ok and isinstance(r.result, dict)
        assert r.result["beyond_hubble_horizon"] == 1.0


@pytest.mark.requires_nexus
def test_version_op_returns_v0_128() -> None:
    """Header bump verification: version op reports v0.128."""
    with NexusBridge() as bridge:
        r = bridge.call("version")
        assert r.ok
        assert isinstance(r.result, str)
        assert "v0.128" in r.result


@pytest.mark.requires_nexus
def test_physics_query_dispatches_to_inner_op() -> None:
    """physics_query routes by `query` field; inner result returned verbatim."""
    with NexusBridge() as bridge:
        r = bridge.call(
            "physics_query",
            query="composition_rule_evaluate",
            params={"W_warp": 0.0, "grav_factor": 1.0, "gamma_kin": 1.0, "warp_active": 0},
        )
        assert r.ok and abs(float(r.result) - 1.0) < 1e-12


@pytest.mark.requires_nexus
def test_physics_query_rejects_self_recursion() -> None:
    """physics_query inside physics_query → error (no infinite loop)."""
    with NexusBridge() as bridge:
        r = bridge.call("physics_query", query="physics_query", params={})
        assert r.ok is False
        assert r.error is not None
        assert "recurse" in r.error.lower()


@pytest.mark.requires_nexus
def test_observe_warp_recede_reverses_time() -> None:
    """WARP at v_apparent > c receding flips time direction."""
    light_year = 9.4607e15
    with NexusBridge() as bridge:
        r = bridge.call(
            "observe",
            ship_pos={"x": 0.0, "y": 0.0, "z": 0.0},
            ship_velocity={"x": 0.0, "y": 0.0, "z": 2.0 * C_LIGHT},
            t_cosmic=1.0e10,
            body_pos={"x": 0.0, "y": 0.0, "z": -1.0 * light_year},
            body_metric_shift=0.0,
            regime="WARP_CRUISE",
        )
        assert r.ok and isinstance(r.result, dict)
        # ship moves +z away from body at -z; v_radial > 0 (receding)
        assert r.result["v_radial"] > 0
        # WARP at v_app > c reverses → apparent_rate < 0
        assert r.result["apparent_rate"] < 0
        assert r.result["time_reversed"] == 1.0


# --- Error path coverage ------------------------------------------------------

@pytest.mark.requires_nexus
def test_unknown_op_returns_error() -> None:
    """An unknown op produces ok=false with an error message."""
    with NexusBridge() as bridge:
        resp = bridge.call("not_a_real_op")
        assert resp.ok is False
        assert resp.error is not None
        assert "unknown" in resp.error.lower()


@pytest.mark.requires_nexus
def test_unknown_regime_returns_error() -> None:
    """An unknown regime string produces ok=false with an error message."""
    with NexusBridge() as bridge:
        resp = bridge.call("compute_apparent_rate", v_radial=0.0, regime="MADE_UP")
        assert resp.ok is False
        assert resp.error is not None
        assert "regime" in resp.error.lower()


@pytest.mark.requires_nexus
def test_missing_required_arg_returns_error() -> None:
    """Missing 'v_radial' produces ok=false."""
    with NexusBridge() as bridge:
        resp = bridge.call("compute_apparent_rate", regime="STL_REL")
        assert resp.ok is False
        assert resp.error is not None
        assert "v_radial" in resp.error


# --- Lifecycle coverage -------------------------------------------------------

@pytest.mark.requires_nexus
def test_bridge_must_start_before_call() -> None:
    """Calling without start() raises NexusBridgeError."""
    bridge = NexusBridge()
    with pytest.raises(NexusBridgeError, match="not started"):
        bridge.call("health")


@pytest.mark.requires_nexus
def test_bridge_missing_binary_raises() -> None:
    """A non-existent binary path fails fast with a clear message."""
    bridge = NexusBridge(binary_path="C:/definitely/not/a/real/path/nexus.exe")
    with pytest.raises(NexusBridgeError, match="not found"):
        bridge.start()


@pytest.mark.requires_nexus
def test_bridge_double_start_rejected() -> None:
    """Calling start() twice raises rather than spawning a leaked subprocess."""
    bridge = NexusBridge()
    bridge.start()
    try:
        with pytest.raises(NexusBridgeError, match="already started"):
            bridge.start()
    finally:
        bridge.close()


@pytest.mark.requires_nexus
def test_bridge_close_idempotent() -> None:
    """Closing an already-closed bridge is a no-op."""
    bridge = NexusBridge()
    bridge.start()
    bridge.close()
    bridge.close()  # second call must not raise


@pytest.mark.requires_nexus
def test_bridge_persistent_across_many_calls() -> None:
    """A single bridge handles repeated calls without re-spawning."""
    with NexusBridge() as bridge:
        for _ in range(20):
            rate = compute_apparent_rate(0.5 * C_LIGHT, "STL_REL", bridge=bridge)
            assert abs(rate - (1.0 / 3.0) ** 0.5) < 1e-9
