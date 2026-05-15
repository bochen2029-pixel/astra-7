"""Entry point for `python -m astra` — delegates to the CLI app."""

from __future__ import annotations

from astra.cli import app_main

if __name__ == "__main__":
    app_main()
