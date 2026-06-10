"""SaveFile v3 — Persistence Contract per spec v0.128 §4.6.

Closes the audit gap "SaveFile v3 serialization" (Phase 0.x forward-work).

Spec §4.6 locks the *logical* schema (t_cosmic, τ_ship, τ_crew_biological,
ζ⃗, a_proper_at_save, AstraCoord, regime bitmask + history, HullMutations,
PowerAllocation, WarpState, AI{Mind, Reflex}, PlayerChoices) and the
behaviors: save-seeds-not-state, versioned schema, deterministic load,
rolling N-deep backups (N=3 minimum) with auto-recovery from the most
recent valid file.

Textverse realization: most of the named scalars already live inside the
frozen `StateBus` composite (time.t_cosmic, time.tau_ship,
time.tau_crew_biological, time.rapidity_zeta, time.a_proper, astra_coord,
warp, power_allocation). SaveFile v3 therefore serializes the StateBus
snapshot wholesale — per §15.9 Frozen-Snapshot framing, the save file IS
a serialized (StateBus + REEL EventStream + extras) snapshot — plus the
§4.6 fields that are NOT part of StateBus: regime history, hull mutation
events, the Mind state (conversation + REEL entries), the frozen Reflex
identity, and player choices.

Deterministic load order (§4.6 steps, mapped to textverse v0):
  1. Reconstruct base HullSDF        — N/A (hull_sdf is a v0 stub).
  2. Apply HullMutations in order    — events are STORED, not applied (v0);
                                       UE5/Implementation B applies to SDF.
  3. Re-evaluate orbital state       — body states ride inside StateBus;
                                       Kepler re-solve happens in astra_nexus
                                       downstream of load.
  4. Re-generate starfield           — N/A in text substrate.
  5. Re-evaluate dilation_ratio      — astra_nexus, downstream.
  6. Chaos field re-init             — N/A v0 (summary scalars only).
  7. Restore Mind state              — REEL entries + conversation history
                                       returned to the harness.

Coherence gate at load: `StateBus.regime` is a computed_field, so the
reconstructed snapshot RE-DERIVES the regime from kinematics + warp +
cryosleep. The stored `regime_at_save` bitmask (canonical hex values per
§3.3 are locked for the SaveFile wire format) must equal the re-derived
value; mismatch raises `SaveFileCoherenceError`. A hand-edited or drifted
save cannot smuggle an incoherent regime past load.

Failure contract (§4.6): corruption of the primary file auto-recovers from
the most recent valid rolling backup (`<name>.1`, then `<name>.2`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from astra.harness.reel import Reel, ReelEntry
from astra.state_bus import StateBus

SCHEMA_VERSION: int = 3
BACKUP_DEPTH: int = 3  # primary + 2 rolling backups, N=3 minimum per §4.6


# --- Errors ----------------------------------------------------------------


class SaveFileError(RuntimeError):
    """Base error for save/load failures."""


class SaveFileVersionError(SaveFileError):
    """schema_version does not match SCHEMA_VERSION (no migration in v0)."""


class SaveFileCoherenceError(SaveFileError):
    """Stored regime_at_save disagrees with the regime re-derived from the
    reconstructed StateBus — the save is internally inconsistent."""


# --- Schema ------------------------------------------------------------------


class HullMutation(BaseModel):
    """One hull damage event per §4.6 ('array of damage events applied to
    base SDF on load'). v0 stores events; SDF application is Implementation B.
    """

    model_config = ConfigDict(frozen=True)

    tau_ship: float = Field(ge=0.0)
    section: str
    magnitude: float = Field(ge=0.0)
    description: str = ""


class PlayerChoice(BaseModel):
    """One operator choice event per §4.6 (regime transitions, etc.)."""

    model_config = ConfigDict(frozen=True)

    tau_ship: float = Field(ge=0.0)
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    """One turn of operator/ASTRA conversation history."""

    model_config = ConfigDict(frozen=True)

    role: Literal["operator", "astra"]
    text: str
    tau_ship: float = Field(ge=0.0)


class ReflexIdentity(BaseModel):
    """Reflex per §4.6: model identity + weights checksum.

    Frozen, no per-game evolution — the checksum exists so a load can
    detect a swapped Reflex artifact (the §4.7 'weights mismatch → go
    offline' failure row). v0 carries a stub identity.
    """

    model_config = ConfigDict(frozen=True)

    model_id: str = "reflex-v0-stub"
    weights_checksum: str = "00000000"


class MindState(BaseModel):
    """AI.Mind per §4.6: conversation history + REEL state."""

    model_config = ConfigDict(frozen=True)

    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    reel_entries: list[ReelEntry] = Field(default_factory=list)


class AIState(BaseModel):
    """AI block per §4.6."""

    model_config = ConfigDict(frozen=True)

    mind: MindState = Field(default_factory=MindState)
    reflex: ReflexIdentity = Field(default_factory=ReflexIdentity)


class SaveFileV3(BaseModel):
    """SaveFile v3 wire schema per spec v0.128 §4.6.

    `state_bus` carries the frozen Layer 0 snapshot (which embeds the
    §4.6-named scalars). `regime_at_save` stores the composite bitmask as
    an int (canonical hex values §3.3, locked for the wire format) for the
    load-time coherence gate.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: int = SCHEMA_VERSION
    state_bus: StateBus
    regime_at_save: int
    regime_history: list[int] = Field(default_factory=list)
    hull_mutations: list[HullMutation] = Field(default_factory=list)
    ai: AIState = Field(default_factory=AIState)
    player_choices: list[PlayerChoice] = Field(default_factory=list)


class LoadResult(BaseModel):
    """Outcome of `load_game`: the save plus recovery forensics."""

    model_config = ConfigDict(frozen=True)

    save: SaveFileV3
    source_path: str                 # which file actually loaded
    recovered_from_backup: bool      # True iff source was a .1/.2 backup
    errors: list[str] = Field(default_factory=list)  # per-candidate failures


# --- Save -------------------------------------------------------------------


def build_save(
    state_bus: StateBus,
    reel: Reel | None = None,
    conversation: list[ConversationTurn] | None = None,
    *,
    regime_history: list[int] | None = None,
    hull_mutations: list[HullMutation] | None = None,
    player_choices: list[PlayerChoice] | None = None,
    reflex: ReflexIdentity | None = None,
) -> SaveFileV3:
    """Assemble a SaveFileV3 snapshot from live harness objects."""
    return SaveFileV3(
        state_bus=state_bus,
        regime_at_save=int(state_bus.regime),
        regime_history=list(regime_history or []),
        hull_mutations=list(hull_mutations or []),
        ai=AIState(
            mind=MindState(
                conversation_history=list(conversation or []),
                reel_entries=reel.entries if reel is not None else [],
            ),
            reflex=reflex or ReflexIdentity(),
        ),
        player_choices=list(player_choices or []),
    )


def _backup_path(path: Path, depth: int) -> Path:
    """`save.json` → `save.json.1`, `save.json.2`, ..."""
    return path.with_name(f"{path.name}.{depth}")


def save_game(
    path: Path,
    state_bus: StateBus,
    reel: Reel | None = None,
    conversation: list[ConversationTurn] | None = None,
    *,
    regime_history: list[int] | None = None,
    hull_mutations: list[HullMutation] | None = None,
    player_choices: list[PlayerChoice] | None = None,
    reflex: ReflexIdentity | None = None,
) -> SaveFileV3:
    """Serialize to JSON at `path` with rolling backup rotation (N=3).

    Rotation before write: `<path>.1` → `<path>.2` (oldest dropped), current
    `<path>` → `<path>.1`, then the new snapshot is written atomically
    (tmp + os.replace) so a crash mid-write cannot corrupt the primary.
    """
    save = build_save(
        state_bus,
        reel,
        conversation,
        regime_history=regime_history,
        hull_mutations=hull_mutations,
        player_choices=player_choices,
        reflex=reflex,
    )

    path.parent.mkdir(parents=True, exist_ok=True)

    # Rotate: oldest first so each rename target is free.
    for depth in range(BACKUP_DEPTH - 1, 1, -1):          # e.g. 2 → (from 1)
        src, dst = _backup_path(path, depth - 1), _backup_path(path, depth)
        if src.exists():
            src.replace(dst)
    if path.exists():
        path.replace(_backup_path(path, 1))

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(save.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(path)
    return save


# --- Load -------------------------------------------------------------------


def load_single(path: Path) -> SaveFileV3:
    """Load and validate exactly one file. Raises on any defect:

    - file missing / unreadable / not JSON      → SaveFileError
    - schema_version != 3                        → SaveFileVersionError
    - schema shape invalid                       → SaveFileError
    - stored regime != re-derived StateBus.regime → SaveFileCoherenceError
    """
    if not path.is_file():
        raise SaveFileError(f"save file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SaveFileError(f"unreadable save file {path}: {e}") from e

    if not isinstance(data, dict):
        raise SaveFileError(f"save file {path} is not a JSON object")

    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise SaveFileVersionError(
            f"save file {path} has schema_version={version!r}; this build "
            f"reads v{SCHEMA_VERSION} only (migration scripts are future work "
            f"per §4.6)"
        )

    try:
        save = SaveFileV3.model_validate(data)
    except ValidationError as e:
        raise SaveFileError(f"save file {path} failed validation: {e}") from e

    # Coherence gate: the reconstructed StateBus re-derives regime from
    # kinematics + warp + cryosleep (computed_field). The serialized inner
    # `regime` key is dropped on input (extra-ignore) — only the underlying
    # truth fields survive the roundtrip, per computed-from-truth (§4.2).
    rederived = int(save.state_bus.regime)
    if rederived != save.regime_at_save:
        raise SaveFileCoherenceError(
            f"save file {path}: stored regime_at_save=0x{save.regime_at_save:02x} "
            f"but reconstructed StateBus derives 0x{rederived:02x} — "
            f"state is internally inconsistent"
        )
    return save


def load_game(path: Path) -> LoadResult:
    """Load with §4.6 auto-recovery: primary, then `.1`, then `.2`.

    Returns the first candidate that passes ALL of load_single's gates.
    Collects per-candidate failure strings for forensics. Raises
    SaveFileError if no candidate is valid.
    """
    candidates = [path] + [_backup_path(path, d) for d in range(1, BACKUP_DEPTH)]
    errors: list[str] = []
    for candidate in candidates:
        try:
            save = load_single(candidate)
        except SaveFileError as e:
            errors.append(str(e))
            continue
        return LoadResult(
            save=save,
            source_path=str(candidate),
            recovered_from_backup=(candidate != path),
            errors=errors,
        )
    raise SaveFileError(
        f"no valid save among {len(candidates)} candidates for {path}; "
        f"errors: {' | '.join(errors)}"
    )


def reel_from_save(save: SaveFileV3) -> Reel:
    """§4.6 load step 7 (Mind restore): rebuild the REEL from entries."""
    return Reel(save.ai.mind.reel_entries)
