"""ConfigSnapshot — the immutable bundle Sculptor measures and edits.

A ConfigSnapshot identifies one "variant" of the bundle for evaluation:
sysprompt paths (with content hashes), sampling parameters, REEL retrieval
k, validator severity, and the scenario library state. Two snapshots with
the same content hashes are equivalent for measurement purposes.

Snapshots are produced from disk state via `ConfigSnapshot.from_disk()`,
versioned by a stable hash, and used as the input to the auto-runner.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Defaults — Sculptor textverse root (relative to this file's grandparent).
def _textverse_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _hash_file(path: Path) -> str:
    """16-char content hash; stable across runs."""
    if not path.is_file():
        return "absent"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


class SnapshotFile(BaseModel):
    """One file's path + content hash. Frozen."""

    model_config = ConfigDict(frozen=True)

    relpath: str            # relative to textverse root
    content_hash: str       # sha256[:16] or "absent"


class ConfigSnapshot(BaseModel):
    """An immutable bundle identifying one Sculptor variant for measurement.

    The hash field is a stable identifier across re-runs. Two snapshots
    with the same hash are bit-equivalent.
    """

    model_config = ConfigDict(frozen=True)

    iteration_id: str       # e.g. "0001_baseline"
    files: list[SnapshotFile] = Field(default_factory=list)
    sampling: dict[str, Any] = Field(default_factory=dict)
    reel_retrieval_k: int = 3
    scenario_paths: list[str] = Field(default_factory=list)

    @property
    def hash(self) -> str:
        """Stable 16-char hash of the snapshot's content."""
        payload = {
            "files": sorted((f.relpath, f.content_hash) for f in self.files),
            "sampling": self.sampling,
            "reel_retrieval_k": self.reel_retrieval_k,
            "scenario_paths": sorted(self.scenario_paths),
        }
        s = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(s).hexdigest()[:16]


# The set of files Sculptor tracks in every snapshot. Paths are relative
# to the textverse root.
TRACKED_FILES: tuple[str, ...] = (
    "prompts/astra_sysprompt.md",
    "prompts/astra_stage_addendum.md",
    "prompts/narrator_sysprompt.md",
    "prompts/adapter_sysprompt.md",
    "astra/grammar/canon/wall_clock_patterns.txt",
    "astra/grammar/canon/astra_substrate_patterns.txt",
    "astra/harness/perception_assembler.py",
)


def snapshot_from_disk(
    *,
    iteration_id: str,
    root: Path | None = None,
    tracked_files: tuple[str, ...] = TRACKED_FILES,
    sampling_path: str = "tuning/sampling.json",
    reel_k_path: str = "tuning/reel_retrieval_k.json",
    scenario_library_dir: str = "astra/scenarios/library",
) -> ConfigSnapshot:
    """Produce a ConfigSnapshot from current disk state.

    The snapshot captures every tracked file's content hash plus the
    sampling JSON and REEL retrieval k. Scenario library entries are
    listed (not hashed; scenario YAMLs are stable per iteration).
    """
    root = root or _textverse_root()
    files = [
        SnapshotFile(
            relpath=rel,
            content_hash=_hash_file(root / rel),
        )
        for rel in tracked_files
    ]

    sampling: dict[str, Any] = {}
    sampling_full = root / sampling_path
    if sampling_full.is_file():
        sampling = {
            k: v for k, v in json.loads(sampling_full.read_text(encoding="utf-8")).items()
            if not k.startswith("_")
        }

    reel_k = 3
    reel_full = root / reel_k_path
    if reel_full.is_file():
        reel_data = json.loads(reel_full.read_text(encoding="utf-8"))
        reel_k = int(reel_data.get("k", 3))

    library_dir = root / scenario_library_dir
    scenario_paths = (
        sorted(str(p.relative_to(root)) for p in library_dir.glob("*.yaml"))
        if library_dir.is_dir()
        else []
    )

    return ConfigSnapshot(
        iteration_id=iteration_id,
        files=files,
        sampling=sampling,
        reel_retrieval_k=reel_k,
        scenario_paths=scenario_paths,
    )


def snapshot_to_json(snapshot: ConfigSnapshot) -> str:
    """Serialize for history/ archival."""
    return snapshot.model_dump_json(indent=2)


def snapshot_from_json(s: str) -> ConfigSnapshot:
    """Inverse of snapshot_to_json."""
    return ConfigSnapshot.model_validate_json(s)
