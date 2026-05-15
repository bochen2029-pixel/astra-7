"""Sculptor-B tests for the auto-runner.

Stubs the llama-server bundle and the scenario runner so we can verify
the aggregation + archive logic without spawning anything live. The full
end-to-end integration against a real llama-server happens via the
operator-runnable smoke script (see scripts/sculptor_iteration.py
when Sculptor-C lands).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

import astra.sculptor.runner_loop as runner_loop_mod
from astra.judge import LCPGate
from astra.llm import AstraBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.sculptor import CompositeWeights, run_iteration
from astra.sculptor.runner_loop import IterationStatus

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_DIR = TEXTVERSE_ROOT / "astra" / "scenarios" / "library"


class _HealthyStubClient(LLMClient):
    """Stub LLMClient returning a canned ASTRA-shaped response."""

    def __init__(self, response: str = "<think>x</think>\nYes. Third pole drift, cycle 46.") -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.response = response
        self._healthy = True

    async def chat_complete(
        self, user_text: str, params: SamplingParams | None = None,
    ) -> str:
        return self.response

    async def chat_stream(
        self, user_text: str, params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        if False:
            yield ""  # pragma: no cover

    async def health(self) -> bool:
        return self._healthy


class _UnhealthyStubClient(_HealthyStubClient):
    async def health(self) -> bool:
        return False


def _stub_bundle(response: str = "<think>x</think>\nYes. Third pole.") -> AstraBundle:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _HealthyStubClient(response)  # type: ignore[assignment]
    return bundle


def _unhealthy_bundle() -> AstraBundle:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _UnhealthyStubClient()  # type: ignore[assignment]
    return bundle


# --- Health / setup paths ----------------------------------------------------

@pytest.mark.asyncio
async def test_iteration_aborts_when_server_unhealthy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap, **_kw: _unhealthy_bundle())
    result = await run_iteration(
        iteration_id="t0_health",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    assert result.status == IterationStatus.SERVER_UNHEALTHY
    assert result.composite is None


@pytest.mark.asyncio
async def test_iteration_aborts_when_library_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap, **_kw: _stub_bundle())
    empty_lib = tmp_path / "empty_lib"
    empty_lib.mkdir()
    result = await run_iteration(
        iteration_id="t_empty",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=empty_lib,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=[],
    )
    assert result.status == IterationStatus.NO_SCENARIOS


# --- Happy path --------------------------------------------------------------

@pytest.mark.asyncio
async def test_iteration_runs_watch_47_and_archives(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stub bundle returns ASTRA-shaped responses; iteration runs to OK status
    and writes history/<iter>/{config.json, composite.json, summary.json}."""
    response = (
        "<think>x</think>\n"
        "Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance."
    )
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap, **_kw: _stub_bundle(response))
    result = await run_iteration(
        iteration_id="t_happy_0001",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    assert result.status == IterationStatus.OK
    assert result.composite is not None
    assert result.archive_dir is not None
    archive_files = list(result.archive_dir.glob("*.json"))
    archive_names = {p.name for p in archive_files}
    assert "config.json" in archive_names
    assert "composite.json" in archive_names
    assert "summary.json" in archive_names


@pytest.mark.asyncio
async def test_iteration_summary_includes_scenario_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use an isolated tmp library with just watch_47_morning so the summary
    assertions don't break when the real library expands."""
    import shutil
    tmp_lib = tmp_path / "lib"
    tmp_lib.mkdir()
    shutil.copy(LIBRARY_DIR / "watch_47_morning.yaml", tmp_lib / "watch_47_morning.yaml")

    response = "<think>x</think>\nYes. Third pole, cycle 46, tolerance."
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap, **_kw: _stub_bundle(response))
    result = await run_iteration(
        iteration_id="t_summary",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=tmp_lib,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    assert result.archive_dir is not None
    summary = json.loads(
        (result.archive_dir / "summary.json").read_text(encoding="utf-8"),
    )
    assert summary["scenario_count"] == 1
    assert summary["scenarios"][0]["name"] == "watch_47_morning"
    assert "aggregate_pass_rate" in summary["scenarios"][0]


# --- Composite computation reflected --------------------------------------

@pytest.mark.asyncio
async def test_iteration_composite_score_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = "<think>x</think>\nYes. Third pole, cycle 46, tolerance."
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap, **_kw: _stub_bundle(response))
    result = await run_iteration(
        iteration_id="t_composite",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    assert result.composite is not None
    assert isinstance(result.composite.composite_score, float)
    # Per-gate session rates must be present after aggregation
    assert LCPGate.GRAMMAR_PARSE in result.composite.per_gate_session_rates


# --- Config-hash stable across same-config runs ------------------------------

@pytest.mark.asyncio
async def test_iteration_config_hash_stable_across_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap, **_kw: _stub_bundle())
    result_a = await run_iteration(
        iteration_id="t_hash_a",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    result_b = await run_iteration(
        iteration_id="t_hash_b",
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    # Same disk state → same hash
    assert result_a.config_hash == result_b.config_hash
