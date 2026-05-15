"""Stub CLI entry point. Real subcommands land Day 6-7.

When implemented, `astra` (from pyproject.toml [project.scripts]) routes here
and a Typer app dispatches to subcommands. Until then, this stub exists so
`uv pip install -e .` doesn't break.
"""

from __future__ import annotations


def app() -> int:
    """Stub CLI. Real implementation: Day 6-7 (see ARCHITECTURE.md §5)."""
    print("astra-textverse: scaffolding only. No subcommands available yet.")
    print("Read proto/textverse/STARTUP.md to begin implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(app())
