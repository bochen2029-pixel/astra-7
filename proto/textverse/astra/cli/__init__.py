"""astra.cli — Typer-based CLI entry points.

Subcommands:
- `astra repl`  — interactive REPL against vanilla Qwen on local llama.cpp
- `astra run <scenario.yaml>` — execute one scenario, write transcript + LCP report
- `astra bench` — run the full scenario suite, aggregate LCP pass rates

Implementation: Day 6-7.
"""
