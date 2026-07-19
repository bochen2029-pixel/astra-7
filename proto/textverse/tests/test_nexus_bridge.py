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
def test_version_op_returns_v0_129() -> None:
    """Version bump verification: version op reports the adopted envelope."""
    with NexusBridge() as bridge:
        r = bridge.call("version")
        assert r.ok
        assert isinstance(r.result, str)
        assert "v0.129" in r.result


# --- §3.3 detect_regime cross-substrate verification (G5 of audit) -------

@pytest.mark.requires_nexus
def test_detect_regime_python_matches_cpp() -> None:
    """Python detect_regime must agree with C++ stdio detect_regime op
    across the canonical state grid. Prevents drift between the two
    implementations of the §3.3 regime-composition algorithm.
    """
    import math

    from astra.core import Regime, detect_regime
    from astra.state_bus import WarpState

    # Grid: (rapidity_omega, warp_phase_or_None, cryosleep, grav_factor)
    grid: list[tuple[float, str | None, bool, float]] = [
        # Baseline: REST.
        (0.0, None, False, 1.0),
        # STL_NONREL: low |β|.
        (0.05, None, False, 1.0),
        # STL_REL: high |β|.
        (1.0, None, False, 1.0),
        # WARP_CHARGE.
        (0.0, "charging", False, 1.0),
        # WARP_CRUISE.
        (0.0, "cruising", False, 1.0),
        # WARP_SHUTDOWN (dropping).
        (0.0, "dropping", False, 1.0),
        # WARP_SHUTDOWN (shutdown).
        (0.0, "shutdown", False, 1.0),
        # CRYOSLEEP + REST.
        (0.0, None, True, 1.0),
        # GRAVITY_WELL + REST.
        (0.0, None, False, 0.8),
        # CRYOSLEEP + WARP_CRUISE.
        (0.0, "cruising", True, 1.0),
        # GRAVITY_WELL + STL_REL.
        (1.0, None, False, 0.8),
        # All three composed: WARP + CRYO + GRAV.
        (0.0, "cruising", True, 0.5),
    ]

    with NexusBridge() as bridge:
        for omega, phase, cryo, grav in grid:
            # Python side
            warp_state = (
                WarpState(W=0.5, phase=phase) if phase is not None else None  # type: ignore[arg-type]
            )
            # Build rapidity_zeta with same omega magnitude
            zeta: tuple[float, float, float] = (
                (0.0, 0.0, 0.0) if omega == 0.0 else (omega, 0.0, 0.0)
            )
            py_regime = detect_regime(
                rapidity_zeta=zeta,
                warp=warp_state,
                cryosleep_active=cryo,
                grav_factor=grav,
            )
            # C++ side via stdio
            cpp_args: dict[str, object] = {
                "rapidity_omega": math.sqrt(sum(z**2 for z in zeta)),
                "warp_present": 1 if phase is not None else 0,
                "cryosleep_active": 1 if cryo else 0,
                "grav_factor": grav,
            }
            if phase is not None:
                cpp_args["warp_phase"] = phase
            r = bridge.call("detect_regime", **cpp_args)
            assert r.ok, f"detect_regime failed for {(omega, phase, cryo, grav)}: {r.error}"
            cpp_regime = Regime(int(float(r.result)))  # type: ignore[arg-type]
            assert cpp_regime == py_regime, (
                f"detect_regime mismatch for ω={omega}, phase={phase}, "
                f"cryo={cryo}, grav={grav}: py={py_regime!r}, cpp={cpp_regime!r}"
            )


# --- §3.2 compute_grav_factor cross-substrate verification (QCR-5) --------

@pytest.mark.requires_nexus
def test_compute_grav_factor_python_matches_cpp() -> None:
    """Python compute_grav_factor must agree with the C++ stdio
    compute_grav_factor op across a mass/distance grid plus multi-body
    and edge configurations. Prevents drift between the two
    implementations of the §3.2 Schwarzschild-dominant composition
    (spec-v0.130-DRAFT QCR-5; the wire's first array-bearing op).
    """
    from dataclasses import dataclass

    from astra.core.astra_coord import SECTOR_SIZE_M, AstraCoord
    from astra.core.grav import compute_grav_factor, schwarzschild_radius_m

    m_sun = 1.98892e30  # kg (matches astra_nexus.cpp M_SUN)

    @dataclass(frozen=True)
    class BH:
        mass_kg: float
        position: AstraCoord

    def coord_of(x_m: float = 0.0, y_m: float = 0.0, z_m: float = 0.0) -> AstraCoord:
        """Decompose metre offsets into (sector, local) per axis."""

        def split(m: float) -> tuple[int, float]:
            sector = round(m / SECTOR_SIZE_M)
            return sector, m - sector * SECTOR_SIZE_M

        sx, lx = split(x_m)
        sy, ly = split(y_m)
        sz, lz = split(z_m)
        return AstraCoord(sx=sx, sy=sy, sz=sz, lx=lx, ly=ly, lz=lz)

    def vec_of(c: AstraCoord) -> dict[str, float]:
        """Serialize an AstraCoord to the wire's flat-metres vec3.

        Per-axis metres use the same `sector * SECTOR_SIZE_M + local`
        expression `astra_distance` evaluates against the origin, so with
        the ship at (0,0,0) both substrates see bit-identical deltas.
        """
        return {
            "x": c.sx * SECTOR_SIZE_M + c.lx,
            "y": c.sy * SECTOR_SIZE_M + c.ly,
            "z": c.sz * SECTOR_SIZE_M + c.lz,
        }

    origin = AstraCoord(sx=0, sy=0, sz=0)

    # Single-BH grid: mass x distance-ratio (in units of r_s), axes cycled.
    configs: list[tuple[str, list[BH], AstraCoord]] = []
    masses = [1.0 * m_sun, 10.0 * m_sun, 1.0e6 * m_sun]
    ratios = [3.0, 10.0, 100.0, 1.0e4, 1.0e8]
    for i, mass in enumerate(masses):
        for j, ratio in enumerate(ratios):
            r = ratio * schwarzschild_radius_m(mass)
            offsets = [0.0, 0.0, 0.0]
            offsets[(i + j) % 3] = r
            configs.append(
                (
                    f"grid m={mass:.3g} r={ratio:.3g}rs axis={(i + j) % 3}",
                    [BH(mass, coord_of(*offsets))],
                    origin,
                )
            )

    # Flat space: empty list is exactly 1.0 on both substrates.
    configs.append(("empty", [], origin))

    # Very far single body: factor approaches 1 smoothly.
    configs.append(("far", [BH(10.0 * m_sun, coord_of(x_m=1.0e15))], origin))

    # Dominant + weak-field partner (mirrors the C++ in-process test).
    rs10 = schwarzschild_radius_m(10.0 * m_sun)
    configs.append(
        (
            "dominant+partner",
            [
                BH(10.0 * m_sun, coord_of(x_m=100.0 * rs10)),
                BH(1.0 * m_sun, coord_of(y_m=1.0e12)),
            ],
            origin,
        )
    )

    # Ship inside the r_s of one body while another dominates: the inside
    # body is excluded from dominance AND its weak-field term hits the
    # arg<=0 guard. Both substrates must agree on both exclusions.
    configs.append(
        (
            "inside-rs partner",
            [
                BH(1.0 * m_sun, coord_of(x_m=1.0e10)),
                BH(1.0e6 * m_sun, coord_of(y_m=1.0e9)),
            ],
            origin,
        )
    )

    # Three bodies, mixed axes and signs.
    configs.append(
        (
            "three-body",
            [
                BH(10.0 * m_sun, coord_of(z_m=5.0e7)),
                BH(1.0 * m_sun, coord_of(x_m=-1.0e11)),
                BH(1.0 * m_sun, coord_of(y_m=2.0e12)),
            ],
            origin,
        )
    )

    # Non-origin ship (small sectors: every value exact in float64).
    configs.append(
        (
            "non-origin ship",
            [BH(10.0 * m_sun, coord_of(x_m=100.0 * rs10 + 2_001_000.0))],
            AstraCoord(sx=2, sy=0, sz=0, lx=1000.0),
        )
    )

    with NexusBridge() as bridge:
        for label, bh_list, ship in configs:
            py = compute_grav_factor(bh_list, ship)
            r = bridge.call(
                "compute_grav_factor",
                bh_list=[
                    {"M": bh.mass_kg, "pos": vec_of(bh.position)} for bh in bh_list
                ],
                ship_pos=vec_of(ship),
            )
            assert r.ok, f"compute_grav_factor failed for {label}: {r.error}"
            cpp = float(r.result)  # type: ignore[arg-type]
            assert cpp == pytest.approx(py, rel=1e-12, abs=1e-15), (
                f"grav-factor mismatch for {label}: py={py!r}, cpp={cpp!r}"
            )
            assert 0.0 < cpp <= 1.0, f"factor out of (0,1] for {label}: {cpp}"


@pytest.mark.requires_nexus
def test_compute_grav_factor_rejects_non_array_bh_list() -> None:
    """A non-array bh_list produces ok=false with an error naming the field."""
    with NexusBridge() as bridge:
        r = bridge.call(
            "compute_grav_factor",
            bh_list=42,
            ship_pos={"x": 0.0, "y": 0.0, "z": 0.0},
        )
        assert r.ok is False
        assert r.error is not None
        assert "bh_list" in r.error


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
