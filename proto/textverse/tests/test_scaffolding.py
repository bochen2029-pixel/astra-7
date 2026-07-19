"""Day 0 sanity tests — confirms the package imports + scaffolding is intact.

These tests are intentionally trivial. They exist to verify that
`uv pip install -e ".[dev]"` produces a working install before any
real code is written. If these fail, the scaffolding is broken.

Day 1 work replaces these with real tests on the Pydantic core types.
"""

from __future__ import annotations


def test_astra_package_imports() -> None:
    """The astra package can be imported without errors."""
    import astra

    assert astra.__version__ == "0.1.0"


def test_all_submodules_importable() -> None:
    """Every submodule is importable (catches typos in __init__.py)."""
    import astra.cli
    import astra.core
    import astra.grammar
    import astra.harness
    import astra.harness.ephemeral
    import astra.judge
    import astra.llm
    import astra.operator
    import astra.physics
    import astra.scenarios
    import astra.scenarios.library
    import astra.ship
    import astra.state_bus
    import astra.universe

    # Touch each module so importlib lazy-load and ruff F401 are both satisfied.
    _ = (
        astra.cli,
        astra.core,
        astra.grammar,
        astra.harness,
        astra.harness.ephemeral,
        astra.judge,
        astra.llm,
        astra.operator,
        astra.physics,
        astra.scenarios,
        astra.scenarios.library,
        astra.ship,
        astra.state_bus,
        astra.universe,
    )


def test_no_wall_clock_imports_in_scaffolding() -> None:
    """Per v0.129 §1.2: no module imports datetime, time, or other wall-clock
    sources, with three narrow exceptions:

    - astra/judge/        — measures real-time iteration cost (LCP timing).
    - astra/llm/llama_server.py — polls subprocess /health for sidecar startup;
                                  uses time.monotonic() / time.sleep() for
                                  infrastructure timeouts only, not game state.
    - astra/persona_test/ — research-tier sysprompt-variation harness; timestamps
                            are metadata in JSONL log entries for cross-run
                            comparison, never fed into ASTRA's perception bundle
                            or State Bus. Same rationale as judge/ tier.

    All exceptions are infrastructure-only paths; none feeds wall-clock
    values back into ASTRA's perception bundle, the State Bus, or any
    fictional-time computation. Day 1+ code must keep passing this test.
    """
    from pathlib import Path

    package_root = Path(__file__).parent.parent / "astra"
    forbidden_imports = ["import datetime", "from datetime", "import time\n", "from time"]
    allowed_paths = (
        "astra/judge/",                  # iteration timing
        "astra/llm/llama_server.py",     # subprocess /health polling
        "astra/persona_test/",           # research-log timestamps (metadata only)
    )

    violations: list[str] = []
    for py_file in package_root.rglob("*.py"):
        normalized = str(py_file).replace("\\", "/")
        if any(allowed in normalized for allowed in allowed_paths):
            continue
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_imports:
            if pattern in content:
                violations.append(f"{py_file}: contains '{pattern.strip()}'")

    assert not violations, (
        "Wall-clock imports forbidden outside infrastructure paths per v0.129 §1.2:\n"
        + "\n".join(violations)
    )
