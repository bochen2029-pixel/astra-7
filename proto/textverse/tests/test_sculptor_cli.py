"""Sculptor-E tests for the new CLI subcommands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from astra.cli import app_main

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent

runner = CliRunner()


def test_sculptor_status_no_log() -> None:
    """When no research log exists yet, status prints a marker."""
    log_path = TEXTVERSE_ROOT / "tuning" / "research_log.jsonl"
    if log_path.is_file():
        # Skip if the developer's log exists; the test would need a clean root.
        # We just verify the subcommand is reachable.
        result = runner.invoke(app_main, ["sculptor-status"])
        assert result.exit_code == 0
    else:
        result = runner.invoke(app_main, ["sculptor-status"])
        assert result.exit_code == 0
        assert "no Sculptor activity yet" in result.output


def test_sculptor_help_lists_sculptor_subcommands() -> None:
    result = runner.invoke(app_main, ["--help"])
    assert result.exit_code == 0
    # Typer normalizes subcommand names: sculptor_run → sculptor-run
    assert "sculptor-run" in result.output
    assert "sculptor-status" in result.output
    assert "sculptor-halt" in result.output
    assert "sculptor-pause" in result.output
    assert "sculptor-resume" in result.output


def test_sculptor_pause_writes_flag() -> None:
    """sculptor-pause touches tuning/pause.flag; sculptor-resume removes it."""
    pause_path = TEXTVERSE_ROOT / "tuning" / "pause.flag"
    # Cleanup if a prior test left a flag.
    if pause_path.is_file():
        pause_path.unlink()
    try:
        result = runner.invoke(app_main, ["sculptor-pause"])
        assert result.exit_code == 0
        assert pause_path.is_file()
        # Resume removes the flag.
        result_resume = runner.invoke(app_main, ["sculptor-resume"])
        assert result_resume.exit_code == 0
        assert not pause_path.is_file()
    finally:
        if pause_path.is_file():
            pause_path.unlink()


def test_sculptor_halt_writes_flag() -> None:
    """sculptor-halt touches tuning/halt.flag."""
    halt_path = TEXTVERSE_ROOT / "tuning" / "halt.flag"
    if halt_path.is_file():
        halt_path.unlink()
    try:
        result = runner.invoke(app_main, ["sculptor-halt"])
        assert result.exit_code == 0
        assert halt_path.is_file()
    finally:
        if halt_path.is_file():
            halt_path.unlink()


def test_sculptor_resume_when_no_flag() -> None:
    """sculptor-resume with no flag prints '(no pause.flag present)'."""
    pause_path = TEXTVERSE_ROOT / "tuning" / "pause.flag"
    if pause_path.is_file():
        pause_path.unlink()
    result = runner.invoke(app_main, ["sculptor-resume"])
    assert result.exit_code == 0
    assert "no pause.flag" in result.output
