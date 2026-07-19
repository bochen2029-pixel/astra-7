"""Canon mirror identity — spec-v0.130-DRAFT QCR-1 / risk-register gun R-6.

The canonical leak/QC3 canon lives IN-PACKAGE (runtime code reads only
`astra/grammar/canon/` and `astra/harness/ephemeral/canon/`). The repo-root
`tests/` copies survive as byte-identical mirrors until v0.130 adoption
retires them (the adopted spec's §5.7/§11 still cite the root paths, so the
files must exist and must not lie).

Divergence between the pairs was measured on 2026-07-19 (QCR-1: the root
copies were the v0.125 stub; the package copies were the curated runtime
canon; each held content the other lacked). This test is the standing gun
that prevents recurrence. Its first run — red against the measured
divergence, green after unification — is the pre-registered witness that
the gun can see its target.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_TEXTVERSE = Path(__file__).resolve().parents[1]
_REPO_ROOT = _TEXTVERSE.parents[1]

_MIRROR_PAIRS: list[tuple[Path, Path]] = [
    (
        _TEXTVERSE / "astra" / "grammar" / "canon" / "wall_clock_patterns.txt",
        _REPO_ROOT / "tests" / "wall_clock_patterns.txt",
    ),
    (
        _TEXTVERSE / "astra" / "harness" / "ephemeral" / "canon" / "qc3_events.txt",
        _REPO_ROOT / "tests" / "qc3_events.txt",
    ),
]


@pytest.mark.parametrize(
    ("package_file", "root_mirror"),
    _MIRROR_PAIRS,
    ids=[p[0].name for p in _MIRROR_PAIRS],
)
def test_root_mirror_is_byte_identical(package_file: Path, root_mirror: Path) -> None:
    assert package_file.is_file(), f"canonical file missing: {package_file}"
    assert root_mirror.is_file(), (
        f"root mirror missing: {root_mirror} — if it was deliberately retired "
        f"(v0.130 adoption), delete this test in the same commit."
    )
    assert package_file.read_bytes() == root_mirror.read_bytes(), (
        f"canon mirror divergence: {root_mirror} != {package_file}. "
        f"The in-package copy is canonical; re-mirror it to the root path "
        f"(byte-exact). Divergence is the QCR-1 failure class."
    )
