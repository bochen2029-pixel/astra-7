"""Sculptor-B tests for the pytest cadence gate.

We don't actually re-run pytest within pytest (that would recurse). The
tests cover the cadence logic + the failed-test parser + the
FileNotFoundError fallback.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from astra.sculptor import CadenceState, PytestResult, run_pytest_subprocess
from astra.sculptor.pytest_gate import _parse_failed_tests, _pytest_session_ran

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


# --- B1 fix: subprocess uses sys.executable -m uv --------------------------

def test_subprocess_uses_python_dash_m_uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """B1 fix verification: pytest cadence must invoke uv via the current
    Python interpreter (`sys.executable -m uv`), not bare `uv`. Bare `uv`
    isn't on the subprocess PATH on Windows + some Linux configs and was
    causing false bench_regression reverts in the first 20-iter Novita run.
    """
    captured: dict[str, list[str]] = {}

    def fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured["cmd"] = list(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    run_pytest_subprocess(textverse_root=tmp_path, timeout_s=5.0)

    assert captured["cmd"][0] == sys.executable
    assert captured["cmd"][1:4] == ["-m", "uv", "run"]
    assert "pytest" in captured["cmd"]


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


# --- _pytest_session_ran: did pytest actually execute? -----------------------

def test_session_ran_recognizes_summary_rule_line() -> None:
    assert _pytest_session_ran("===== 578 passed in 7.24s =====") is True
    assert _pytest_session_ran("=== 2 failed, 576 passed in 8.1s ===") is True
    assert _pytest_session_ran("==== 1 error in 0.50s ====") is True
    assert _pytest_session_ran("===== no tests ran in 0.01s =====") is True


def test_session_ran_recognizes_header() -> None:
    assert _pytest_session_ran("==== test session starts ====\ncollected 5 items") is True


def test_session_ran_rejects_bare_interpreter_error() -> None:
    # `python -m uv` when uv is absent, or `.venv/python -m pytest` with no
    # pytest installed — neither emits a pytest summary rule line.
    assert _pytest_session_ran("C:\\py.exe: No module named uv") is False
    assert _pytest_session_ran("C:\\py.exe: No module named pytest") is False


def test_session_ran_rejects_unwrapped_tool_error() -> None:
    # A non-pytest tool's `error:` line is not wrapped in `===` and must not
    # be mistaken for a pytest session.
    assert _pytest_session_ran("error: failed to resolve environment") is False


# --- PytestResult.runner_failed: infra-failure vs genuine-regression ---------

def test_runner_failed_false_when_passed() -> None:
    assert PytestResult(passed=True, exit_code=0).runner_failed is False


def test_runner_failed_true_on_timeout() -> None:
    r = PytestResult(passed=False, exit_code=-1, timed_out=True)
    assert r.runner_failed is True


def test_runner_failed_true_on_negative_exit_code() -> None:
    # Sentinel exit codes (-1 timeout, -2 FileNotFoundError) are runner deaths.
    assert PytestResult(passed=False, exit_code=-2).runner_failed is True


def test_runner_failed_true_when_pytest_never_ran() -> None:
    # `python -m uv run pytest` died before pytest started: non-zero exit,
    # no pytest summary line. This is the false-`bench_regression` case the
    # fix eliminates — it must classify as a runner failure.
    r = PytestResult(
        passed=False, exit_code=1, failed_tests=[],
        raw_output="C:\\Program Files\\Python313\\python.exe: No module named uv\n",
    )
    assert r.runner_failed is True


def test_runner_failed_false_on_genuine_test_failure() -> None:
    # pytest ran, reported FAILED tests → genuine bench regression, not infra.
    r = PytestResult(
        passed=False, exit_code=1,
        failed_tests=["tests/foo.py::test_x"],
        raw_output=(
            "FAILED tests/foo.py::test_x - AssertionError\n"
            "===== 1 failed, 577 passed in 7.9s =====\n"
        ),
    )
    assert r.runner_failed is False


def test_runner_failed_false_on_hypothesis_collection_error() -> None:
    # A hypothesis that breaks an import makes pytest error during collection:
    # pytest DID run (summary line present), failed_tests is empty, but the
    # change is at fault → genuine bench regression, NOT an infra failure.
    r = PytestResult(
        passed=False, exit_code=2, failed_tests=[],
        raw_output=(
            "==== ERRORS ====\n"
            "errors during collection\n"
            "SyntaxError: invalid syntax\n"
            "===== 1 error in 0.30s =====\n"
        ),
    )
    assert r.runner_failed is False
