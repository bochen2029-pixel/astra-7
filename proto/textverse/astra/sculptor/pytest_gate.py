"""Pytest cadence gate — Sculptor runs the bench's own pytest suite
every N iterations to catch bench-regression.

If pytest fails, Sculptor reverts the offending change and logs a
`bench_regression` entry. This catches changes that game scoring but
invalidate the bench (e.g., a sysprompt edit that causes parser failures
or template incompatibilities).

The gate spawns `uv run pytest` as a subprocess from the textverse root
and parses the result. It does NOT use the in-process pytest API (that
would risk shared state). One subprocess per cadence call.

Per the wall-clock exemption pattern (test_scaffolding.py), this module
needs `time` for subprocess timeout but classifies as judge-tier
infrastructure. We avoid the import by using subprocess.run(timeout=...)
which doesn't need explicit `time` calls in our code.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Cap on pytest runtime so a hang doesn't stall Sculptor.
DEFAULT_PYTEST_TIMEOUT_S: float = 600.0


@dataclass(slots=True)
class PytestResult:
    """Outcome of one pytest run."""

    passed: bool
    exit_code: int
    failed_tests: list[str] = field(default_factory=list)
    timed_out: bool = False
    raw_output: str = ""


_FAILED_LINE_RE = re.compile(r"FAILED (\S+::\S+)")


def _parse_failed_tests(output: str) -> list[str]:
    """Extract `tests/foo.py::test_x` identifiers from pytest's short test summary."""
    return _FAILED_LINE_RE.findall(output)


def run_pytest_subprocess(
    *,
    textverse_root: Path,
    timeout_s: float = DEFAULT_PYTEST_TIMEOUT_S,
    extra_args: list[str] | None = None,
) -> PytestResult:
    """Spawn `uv run pytest` via the current Python interpreter.

    Uses `[sys.executable, "-m", "uv", "run", ...]` rather than bare `uv`
    so the subprocess works on systems where `uv` is installed as a
    Python module but not on the bare PATH (Windows + some Linux configs).
    Cross-platform safe; eliminates the false `bench_regression` reverts
    observed in the first 20-iter Novita run (B1 finding).
    """
    cmd = [sys.executable, "-m", "uv", "run", "pytest", "--tb=line", "--no-header"]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(textverse_root),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        # `text=True` above guarantees stdout/stderr are str, but mypy can't
        # narrow the TimeoutExpired.stdout / .stderr type (bytes | str | None).
        stdout = e.stdout if isinstance(e.stdout, str) else ""
        stderr = e.stderr if isinstance(e.stderr, str) else ""
        return PytestResult(
            passed=False,
            exit_code=-1,
            timed_out=True,
            raw_output=stdout + stderr,
        )
    except FileNotFoundError as e:
        # uv not on PATH
        return PytestResult(
            passed=False,
            exit_code=-2,
            failed_tests=[],
            raw_output=f"uv not found on PATH: {e}",
        )

    combined = (result.stdout or "") + (result.stderr or "")
    return PytestResult(
        passed=result.returncode == 0,
        exit_code=result.returncode,
        failed_tests=_parse_failed_tests(combined),
        raw_output=combined,
    )


@dataclass(slots=True)
class CadenceState:
    """Tracks when the pytest gate should fire.

    Per scope.yaml pytest_cadence_iterations (default 10): every Nth
    iteration triggers a gate run. The meta-agent owns the cadence
    counter; this module just reports whether the current iteration
    should trigger.
    """

    iteration: int = 0
    cadence: int = 10

    def should_run(self) -> bool:
        """True iff this iteration is a cadence checkpoint."""
        if self.cadence <= 0:
            return False
        return self.iteration > 0 and self.iteration % self.cadence == 0
