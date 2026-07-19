"""Day 7 tests for the typer-based CLI surface.

Subcommand wiring + scenario discovery. Live scenario execution is
covered by the run-scenario live smoke test, not unit tests.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from astra.cli import app_main

runner = CliRunner()


def test_version_subcommand() -> None:
    result = runner.invoke(app_main, ["version"])
    assert result.exit_code == 0
    assert "astra-textverse" in result.output
    assert "spec: docs/spec-v0.129.md" in result.output


def test_list_scenarios_includes_watch_47() -> None:
    result = runner.invoke(app_main, ["list-scenarios"])
    assert result.exit_code == 0
    assert "watch_47_morning" in result.output


def test_list_scenarios_custom_empty_dir_reports_empty(tmp_path: Path) -> None:
    result = runner.invoke(app_main, ["list-scenarios", "--library-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


def test_run_subcommand_missing_scenario_fails(tmp_path: Path) -> None:
    """An unknown scenario name exits with code 2."""
    result = runner.invoke(
        app_main,
        ["run", "definitely_not_a_real_scenario"],
    )
    assert result.exit_code == 2


def test_help_lists_subcommands() -> None:
    result = runner.invoke(app_main, ["--help"])
    assert result.exit_code == 0
    output = result.output
    assert "run" in output
    assert "bench" in output
    assert "list-scenarios" in output
    assert "version" in output
