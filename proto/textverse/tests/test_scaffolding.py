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
    """Every empty submodule is importable (catches typos in __init__.py)."""
    import astra.cli  # noqa: F401
    import astra.core  # noqa: F401
    import astra.grammar  # noqa: F401
    import astra.harness  # noqa: F401
    import astra.harness.ephemeral  # noqa: F401
    import astra.judge  # noqa: F401
    import astra.llm  # noqa: F401
    import astra.operator  # noqa: F401
    import astra.physics  # noqa: F401
    import astra.scenarios  # noqa: F401
    import astra.scenarios.library  # noqa: F401
    import astra.ship  # noqa: F401
    import astra.state_bus  # noqa: F401
    import astra.universe  # noqa: F401


def test_no_wall_clock_imports_in_scaffolding() -> None:
    """Per v0.128 invariant: no module imports datetime, time, or other wall-clock
    sources except astra.judge (which needs real-time for iteration measurement).

    This test scans the source tree at the scaffolding stage. Day 1+ code must
    keep passing this test.
    """
    from pathlib import Path

    package_root = Path(__file__).parent.parent / "astra"
    forbidden_imports = ["import datetime", "from datetime", "import time\n", "from time"]
    allowed_in_module = "astra/judge/"  # judge can measure real-time iteration cost

    violations: list[str] = []
    for py_file in package_root.rglob("*.py"):
        if allowed_in_module in str(py_file).replace("\\", "/"):
            continue
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_imports:
            if pattern in content:
                violations.append(f"{py_file}: contains '{pattern.strip()}'")

    assert not violations, (
        "Wall-clock imports forbidden outside astra/judge/ per v0.128 §1.2:\n"
        + "\n".join(violations)
    )
