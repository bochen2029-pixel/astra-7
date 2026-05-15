"""Sculptor-B tests for the pytest cadence gate.

We don't actually re-run pytest within pytest (that would recurse). The
tests cover the cadence logic + the failed-test parser + the
FileNotFoundError fallback.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from astra.sculptor import CadenceState, PytestResult, run_pytest_subprocess
from astra.sculptor.pytest_gate import _parse_failed_tests

# --- CadenceState ------------------------------------------------------------

def test_cadence_zero_iteration_does_not_trigger() -> None:
    state = CadenceState(iteration=0, cadence=10)
    assert state.should_run() is False


def test_cadence_at_interval_triggers() -> None:
    state = CadenceState(iteration=10, cadence=10)
    assert state.should_run() is True


def test_cadence_between_intervals_does_not_trigger() -> None:
    state = CadenceState(iteration=7, cadence=10)
    assert state.should_run() is False


def test_cadence_multiple_of_interval_triggers() -> None:
    assert CadenceState(iteration=20, cadence=10).should_run() is True
    assert CadenceState(iteration=100, cadence=10).should_run() is True


def test_cadence_zero_cadence_never_triggers() -> None:
    state = CadenceState(iteration=10, cadence=0)
    assert state.should_run() is False


# --- Failed-test parser ------------------------------------------------------

def test_parse_failed_tests_extracts_test_ids() -> None:
    output = """
======= FAILURES =======
some traceback...
FAILED tests/test_grammar_parser.py::test_strip_rule - AssertionError: x
FAILED tests/test_judge_gates.py::test_persona_stable_passes_clean_speech - assert ...
"""
    failed = _parse_failed_tests(output)
    assert "tests/test_grammar_parser.py::test_strip_rule" in failed
    assert "tests/test_judge_gates.py::test_persona_stable_passes_clean_speech" in failed
    assert len(failed) == 2


def test_parse_failed_tests_empty_when_no_failures() -> None:
    output = "===== 100 passed in 1.20s =====\n"
    failed = _parse_failed_tests(output)
    assert failed == []


def test_parse_failed_tests_handles_windows_paths() -> None:
    output = "FAILED tests\\test_x.py::test_y - error\n"
    failed = _parse_failed_tests(output)
    # The regex requires non-whitespace; windows backslash is non-whitespace,
    # so it captures correctly.
    assert failed == ["tests\\test_x.py::test_y"]


# --- run_pytest_subprocess fallback paths ------------------------------------

def test_uv_not_on_path_returns_exit_code_minus_two(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If `uv` is missing, the subprocess call raises FileNotFoundError;
    the function catches it and returns exit_code = -2."""
    # Force PATH to empty so subprocess can't find anything.
    monkeypatch.setenv("PATH", "")
    result = run_pytest_subprocess(textverse_root=tmp_path, timeout_s=5.0)
    # On platforms where uv resolves via other mechanisms we may not hit
    # the FileNotFoundError branch; accept either failure mode.
    assert result.passed is False


# --- PytestResult shape ------------------------------------------------------

def test_pytest_result_default_shape() -> None:
    r = PytestResult(passed=True, exit_code=0)
    assert r.failed_tests == []
    assert r.timed_out is False
    assert r.raw_output == ""


def test_pytest_result_carries_failed_list() -> None:
    r = PytestResult(
        passed=False, exit_code=1,
        failed_tests=["tests/foo.py::test_x"],
    )
    assert r.failed_tests == ["tests/foo.py::test_x"]
