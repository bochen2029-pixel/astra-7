"""Pytest configuration shared across the suite.

For now this file is mostly empty; it exists to satisfy pytest's discovery
and to provide a place for future shared fixtures (e.g., a vanilla Qwen 9B
LLM client fixture, a fixtures-mode physics binary).
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def textverse_root() -> str:
    """Absolute path to proto/textverse/ for tests that need to load YAML/MD files."""
    from pathlib import Path

    return str(Path(__file__).parent.parent.resolve())
