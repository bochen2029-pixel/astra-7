"""Sculptor-A tests for ConfigSnapshot."""

from __future__ import annotations

from pathlib import Path

from astra.sculptor import (
    ConfigSnapshot,
    SnapshotFile,
    snapshot_from_disk,
    snapshot_from_json,
    snapshot_to_json,
)

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent


# --- Building from disk ------------------------------------------------------

def test_snapshot_from_disk_captures_tracked_files() -> None:
    snap = snapshot_from_disk(iteration_id="0001_baseline", root=TEXTVERSE_ROOT)
    rels = {f.relpath for f in snap.files}
    assert "prompts/astra_sysprompt.md" in rels
    assert "prompts/astra_stage_addendum.md" in rels
    assert "prompts/narrator_sysprompt.md" in rels
    assert "prompts/adapter_sysprompt.md" in rels


def test_snapshot_includes_sampling() -> None:
    snap = snapshot_from_disk(iteration_id="0002", root=TEXTVERSE_ROOT)
    assert "temperature" in snap.sampling
    assert "top_p" in snap.sampling


def test_snapshot_includes_reel_k() -> None:
    snap = snapshot_from_disk(iteration_id="0003", root=TEXTVERSE_ROOT)
    assert snap.reel_retrieval_k >= 1


def test_snapshot_includes_scenario_library() -> None:
    snap = snapshot_from_disk(iteration_id="0004", root=TEXTVERSE_ROOT)
    assert any("watch_47_morning" in p for p in snap.scenario_paths)


# --- Hash stability ----------------------------------------------------------

def test_snapshot_hash_stable() -> None:
    s1 = snapshot_from_disk(iteration_id="0005", root=TEXTVERSE_ROOT)
    s2 = snapshot_from_disk(iteration_id="0005-renamed", root=TEXTVERSE_ROOT)
    # Hash should be content-based, not iteration_id-based.
    assert s1.hash == s2.hash


def test_snapshot_hash_changes_when_sampling_changes() -> None:
    s1 = snapshot_from_disk(iteration_id="0006", root=TEXTVERSE_ROOT)
    # Build a hand-edited snapshot with different sampling.
    s2 = ConfigSnapshot(
        iteration_id=s1.iteration_id,
        files=s1.files,
        sampling={**s1.sampling, "temperature": 0.5},   # different
        reel_retrieval_k=s1.reel_retrieval_k,
        scenario_paths=s1.scenario_paths,
    )
    assert s1.hash != s2.hash


# --- Roundtrip ---------------------------------------------------------------

def test_snapshot_roundtrip_json() -> None:
    s1 = snapshot_from_disk(iteration_id="0007", root=TEXTVERSE_ROOT)
    s2 = snapshot_from_json(snapshot_to_json(s1))
    assert s1 == s2
    assert s1.hash == s2.hash


def test_snapshot_is_frozen() -> None:
    snap = snapshot_from_disk(iteration_id="0008", root=TEXTVERSE_ROOT)
    try:
        snap.iteration_id = "altered"
    except Exception:
        return
    raise AssertionError("ConfigSnapshot must be frozen")


def test_snapshot_file_content_hash_format() -> None:
    snap = snapshot_from_disk(iteration_id="0009", root=TEXTVERSE_ROOT)
    for f in snap.files:
        if f.content_hash != "absent":
            assert len(f.content_hash) == 16


# --- Edge cases --------------------------------------------------------------

def test_snapshot_handles_missing_tracked_file(tmp_path: Path) -> None:
    """If a tracked file is missing from disk, content_hash should be 'absent'."""
    snap = snapshot_from_disk(iteration_id="0010", root=tmp_path)
    for f in snap.files:
        assert f.content_hash == "absent"


def test_snapshot_file_pydantic_frozen() -> None:
    f = SnapshotFile(relpath="x.md", content_hash="aaaa")
    try:
        f.content_hash = "bbbb"
    except Exception:
        return
    raise AssertionError("SnapshotFile must be frozen")
