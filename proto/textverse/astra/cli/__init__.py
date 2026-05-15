"""astra.cli — Typer-based CLI for the textverse bench.

Subcommands:
- `astra run [scenario]`    — run one scenario end-to-end
- `astra bench`             — run every scenario in the library
- `astra list-scenarios`    — list scenario YAMLs
- `astra version`           — print package version
"""

from astra.cli.__main__ import app, app_main

__all__ = ["app", "app_main"]
