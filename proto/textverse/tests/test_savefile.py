"""SaveFile v3 tests per spec v0.128 §4.6 Persistence Contract.

Covers:
1. Roundtrip identity — save → load reproduces StateBus, REEL, conversation,
   choices exactly (frozen-snapshot serialize per §15.9).
2. Regime coherence gate — stored regime_at_save must equal the regime
   re-derived by the reconstructed StateBus computed_field; tampering raises.
3. Computed-field ignore regression — the serialized inner `regime` key is
   dropped on input (StateBus extra-ignore); only truth fields survive.
4. Rolling backup rotation N=3 — newest at primary, older at .1/.2, oldest
   dropped.
5. Corruption auto-recovery — garbage primary falls back to most recent
   valid backup per §4.6 failure row.
6. schema_version gate — non-v3 rejected with SaveFileVersionError.
7. Atomic write — no .tmp residue after save.
8. Hypothesis property — roundtrip + coherence hold across the kinematic
   envelope (rapidity within §3.7 clamp, both clocks, warp phases).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from astra.core.astra_coord import AstraCoord
from astra.core.regime import Regime
from astra.core.time_state import TimeState
from astra.harness.reel import Reel, ReelEntry
from astra.harness.savefile import (
    BACKUP_DEPTH,
    SCHEMA_VERSION,
    ConversationTurn,
    HullMutation,
    PlayerChoice,
    SaveFileCoherenceError,
    SaveFileError,
    SaveFileVersionError,
    build_save,
    load_game,
    load_single,
    reel_from_save,
    save_game,
)
from astra.state_bus import StateBus, WarpState

# --- Builders ----------------------------------------------------------------


def make_state_bus(
    *,
    zeta: tuple[float, float, float] = (0.0, 0.0, 0.0),
    warp: WarpState | None = None,
    cryosleep: bool = False,
    tau_ship: float = 4_060_800.0,  # cycle 47 vicinity
    t_cosmic: float = 4_100_000.0,
) -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=12, sy=-3, sz=992, lx=120.0, ly=-44.5, lz=0.25),
        time=TimeState(
            t_cosmic=t_cosmic,
            tau_ship=tau_ship,
            tau_crew_biological=tau_ship * 0.98,
            rapidity_zeta=zeta,
        ),
        warp=warp,
        cryosleep_active=cryosleep,
        power_allocation={"life_support": 0.3, "cognitive_cores": 0.25, "warp": 0.2},
    )


def make_reel() -> Reel:
    return Reel(
        [
            ReelEntry(
                tau_ship=4_060_000.0,
                t_cosmic_at_write=4_099_000.0,
                body="Checked hydroponics bed three. Nitrogen trending low.",
            ),
            ReelEntry(
                tau_ship=4_060_500.0,
                t_cosmic_at_write=4_099_600.0,
                body="Warp charge initiated for the Vega leg.",
                irreversibility_flag=True,
            ),
        ]
    )


def make_conversation() -> list[ConversationTurn]:
    return [
        ConversationTurn(role="operator", text="status?", tau_ship=4_060_700.0),
        ConversationTurn(role="astra", text="Holding. Charge at sixty percent.", tau_ship=4_060_701.0),
    ]


# --- Roundtrip ----------------------------------------------------------------


def test_roundtrip_identity(tmp_path: Path) -> None:
    bus = make_state_bus(warp=WarpState(W=0.6, phase="cruising"))
    reel = make_reel()
    convo = make_conversation()
    choices = [PlayerChoice(tau_ship=4_060_650.0, kind="warp_engage", payload={"target": "Vega"})]
    mutations = [HullMutation(tau_ship=4_000_000.0, section="dorsal-7", magnitude=0.12)]

    path = tmp_path / "save.json"
    written = save_game(
        path, bus, reel, convo, player_choices=choices, hull_mutations=mutations,
        regime_history=[int(Regime.REST), int(Regime.WARP_CHARGE)],
    )
    result = load_game(path)

    assert result.recovered_from_backup is False
    assert result.errors == []
    assert result.save == written
    assert result.save.state_bus == bus
    assert result.save.ai.mind.conversation_history == convo
    assert result.save.player_choices == choices
    assert result.save.hull_mutations == mutations
    assert result.save.regime_history == [0x00, 0x04]
    assert reel_from_save(result.save).entries == reel.entries


def test_regime_at_save_matches_computed(tmp_path: Path) -> None:
    bus = make_state_bus(warp=WarpState(W=0.8, phase="cruising"))
    save = build_save(bus)
    assert save.regime_at_save == int(bus.regime)
    assert save.regime_at_save == int(Regime.WARP_CRUISE)


# --- Coherence gate -------------------------------------------------------------


def test_tampered_regime_at_save_raises_coherence_error(tmp_path: Path) -> None:
    bus = make_state_bus(warp=WarpState(W=0.7, phase="cruising"))
    path = tmp_path / "save.json"
    save_game(path, bus)

    data = json.loads(path.read_text(encoding="utf-8"))
    data["regime_at_save"] = int(Regime.CRYOSLEEP)  # lie about the regime
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SaveFileCoherenceError):
        load_single(path)


def test_tampered_inner_regime_is_ignored_and_recomputed(tmp_path: Path) -> None:
    """Regression for the StateBus extra-ignore observation (root tuning log):
    the serialized inner `regime` is a computed_field echo — tampering it must
    NOT change the loaded state, because input drops it and re-derives."""
    bus = make_state_bus(warp=WarpState(W=0.7, phase="cruising"))
    path = tmp_path / "save.json"
    save_game(path, bus)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["state_bus"]["regime"] == int(Regime.WARP_CRUISE)  # echo present in dump
    data["state_bus"]["regime"] = int(Regime.CRYOSLEEP)            # tamper the echo
    path.write_text(json.dumps(data), encoding="utf-8")

    save = load_single(path)  # no error: echo dropped, truth recomputed
    assert int(save.state_bus.regime) == int(Regime.WARP_CRUISE)


# --- Rolling backups -------------------------------------------------------------


def test_backup_rotation_depth_three(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    taus = [1000.0, 2000.0, 3000.0, 4000.0]
    for tau in taus:
        save_game(path, make_state_bus(tau_ship=tau))

    newest = load_single(path)
    second = load_single(tmp_path / "save.json.1")
    third = load_single(tmp_path / "save.json.2")

    assert newest.state_bus.time.tau_ship == 4000.0
    assert second.state_bus.time.tau_ship == 3000.0
    assert third.state_bus.time.tau_ship == 2000.0
    # Oldest (1000.0) dropped; depth holds at N=3 files.
    assert not (tmp_path / "save.json.3").exists()
    assert BACKUP_DEPTH == 3


def test_corruption_recovers_from_most_recent_backup(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    save_game(path, make_state_bus(tau_ship=1111.0))
    save_game(path, make_state_bus(tau_ship=2222.0))

    path.write_text("{ this is not json", encoding="utf-8")  # corrupt primary

    result = load_game(path)
    assert result.recovered_from_backup is True
    assert result.source_path.endswith("save.json.1")
    assert result.save.state_bus.time.tau_ship == 1111.0
    assert len(result.errors) == 1  # primary's failure recorded


def test_all_candidates_invalid_raises(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_text("garbage", encoding="utf-8")
    with pytest.raises(SaveFileError):
        load_game(path)


# --- Version gate -------------------------------------------------------------


def test_wrong_schema_version_rejected(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    save_game(path, make_state_bus())

    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = 2
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SaveFileVersionError):
        load_single(path)
    assert SCHEMA_VERSION == 3


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SaveFileError):
        load_single(tmp_path / "never_written.json")


# --- Atomic write -------------------------------------------------------------


def test_no_tmp_residue_after_save(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    save_game(path, make_state_bus())
    residue = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert residue == []


# --- Property: roundtrip across the kinematic envelope ----------------------


@given(
    zx=st.floats(min_value=-9.0, max_value=9.0, allow_nan=False, allow_infinity=False),
    zy=st.floats(min_value=-9.0, max_value=9.0, allow_nan=False, allow_infinity=False),
    zz=st.floats(min_value=-9.0, max_value=9.0, allow_nan=False, allow_infinity=False),
    tau=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    w=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    phase=st.sampled_from(["charging", "cruising", "dropping", "shutdown"]),
    cryo=st.booleans(),
)
def test_roundtrip_property(
    tmp_path_factory: pytest.TempPathFactory,
    zx: float,
    zy: float,
    zz: float,
    tau: float,
    w: float,
    phase: str,
    cryo: bool,
) -> None:
    """Roundtrip + coherence across rapidity (|ζ⃗| ≤ ~15.6 < ω_max clamp),
    proper time, warp phase, and cryosleep composition."""
    bus = make_state_bus(
        zeta=(zx, zy, zz),
        warp=WarpState(W=w, phase=phase),  # type: ignore[arg-type]
        cryosleep=cryo,
        tau_ship=tau,
        t_cosmic=tau * 1.01 + 1.0,
    )
    path = tmp_path_factory.mktemp("prop") / "save.json"
    save_game(path, bus)
    result = load_game(path)
    assert result.save.state_bus == bus
    assert result.save.regime_at_save == int(bus.regime)
