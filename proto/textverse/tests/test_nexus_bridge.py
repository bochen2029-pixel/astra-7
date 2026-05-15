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
