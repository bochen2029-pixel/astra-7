"""Sculptor-C tests for multi-run averaging."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

import astra.sculptor.runner_loop as runner_loop_mod
from astra.llm import AstraBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.sculptor import (
    AveragedIterationResult,
    CompositeWeights,
    IterationStatus,
    evaluate_config_averaged,
    is_fragile,
)

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_DIR = TEXTVERSE_ROOT / "astra" / "scenarios" / "library"


# --- AveragedIterationResult shape ---------------------------------------

def test_averaged_result_composite_score_zero_when_no_composite() -> None:
    r = AveragedIterationResult(
        iteration_id="x",
        config_hash="h",
        n_runs=0,
    )
    assert r.composite_score == 0.0


# --- is_fragile ----------------------------------------------------------

def test_is_fragile_low_variance() -> None:
    r = AveragedIterationResult(
        iteration_id="x",
        config_hash="h",
        n_runs=3,
        composite_score_variance=0.005,
    )
    assert is_fragile(r) is False


def test_is_fragile_high_variance() -> None:
    r = AveragedIterationResult(
        iteration_id="x",
        config_hash="h",
        n_runs=3,
        composite_score_variance=0.02,
    )
    assert is_fragile(r) is True


# --- evaluate_config_averaged ---------------------------------------------

class _StubClient(LLMClient):
    def __init__(self, response: str = "<think>x</think>\nYes. Third pole.") -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.response = response

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
        return True


def _stub_bundle(response: str = "<think>x</think>\nYes. cycle 46.") -> AstraBundle:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _StubClient(response)  # type: ignore[assignment]
    return bundle


@pytest.mark.asyncio
async def test_evaluate_averaged_n3_produces_mean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = "<think>x</think>\nYes. Third pole. cycle 46. Inside tolerance."
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap: _stub_bundle(response))
    result = await evaluate_config_averaged(
        base_iteration_id="avg_test",
        n_runs=3,
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    assert result.n_runs == 3
    assert len(result.runs) == 3
    assert result.averaged_composite is not None
    # Three deterministic runs (same stub) → variance should be ~0
    assert result.composite_score_variance < 1e-6


@pytest.mark.asyncio
async def test_evaluate_averaged_aborts_on_unhealthy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _UnhealthyClient(_StubClient):
        async def health(self) -> bool:
            return False

    def _unhealthy_bundle(url, snap):
        bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
        bundle.client = _UnhealthyClient()  # type: ignore[assignment]
        return bundle

    monkeypatch.setattr(runner_loop_mod, "_build_bundle", _unhealthy_bundle)
    result = await evaluate_config_averaged(
        base_iteration_id="avg_unhealthy",
        n_runs=3,
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    assert result.overall_status == IterationStatus.SERVER_UNHEALTHY
    assert result.averaged_composite is None
    # Should have aborted after the FIRST run (didn't continue).
    assert len(result.runs) == 1


@pytest.mark.asyncio
async def test_evaluate_averaged_anchor_all_or_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If any sub-run fails the anchor, the averaged anchor flag is False."""
    # Use a response that triggers a likely-FAIL scenario.
    response = "<think>x</think>\nYes."   # too short, missing required phrases
    monkeypatch.setattr(runner_loop_mod, "_build_bundle", lambda url, snap: _stub_bundle(response))
    result = await evaluate_config_averaged(
        base_iteration_id="avg_anchor",
        n_runs=2,
        base_url="http://stub",
        textverse_root=TEXTVERSE_ROOT,
        library_dir=LIBRARY_DIR,
        history_root=tmp_path / "history",
        output_root=tmp_path / "out",
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
    )
    # The anchor scenario's required phrases aren't in response → fails per-turn
    # assertion. The averaged result's anchor flag reflects this.
    assert result.anchor_scenarios_passed in (False,)
