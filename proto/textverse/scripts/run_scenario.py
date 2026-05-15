"""Day 6/7 scenario runner CLI — operator-runnable end-to-end test.

Loads a scenario YAML from astra/scenarios/library/, runs it against a
live llama-server (per docs/BUILD_NOTES.md), writes transcript + LCP
report + final state to scenarios/output/, and prints a human-readable
summary.

Usage:
    python scripts/run_scenario.py [--scenario watch_47_morning] [--base-url ...]

Exit codes:
    0 — overall_passed
    1 — overall_failed (any per-turn assertion failed, or any LCP gate
        failed at session level)
    2 — server unhealthy / setup error
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from astra.llm import AstraBundle
from astra.scenarios import (
    ScenarioRunner,
    load_scenario_file,
    summary_for_operator,
)


def _resolve_scenario_path(name: str) -> Path:
    """Map a scenario short-name → library YAML path."""
    library = Path(__file__).parent.parent / "astra" / "scenarios" / "library"
    candidate = library / f"{name}.yaml"
    if candidate.is_file():
        return candidate
    # Fall back to literal path if user passes a full path
    p = Path(name)
    if p.is_file():
        return p
    raise FileNotFoundError(f"scenario not found: {name} (looked in {library})")


def _default_output_root() -> Path:
    return Path(__file__).parent.parent / "scenarios" / "output"


async def _run(scenario_name: str, base_url: str, output_root: Path) -> int:
    scenario_path = _resolve_scenario_path(scenario_name)
    print(f"loading scenario: {scenario_path}")
    scenario = load_scenario_file(str(scenario_path))

    bundle = AstraBundle(base_url=base_url)
    if not await bundle.client.health():
        print(f"FAIL: /health did not return 200 at {base_url}")
        return 2

    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=bundle,
        output_root=output_root,
    )

    print(f"running scenario '{scenario.name}' against {base_url}...")
    report = await runner.run()

    print()
    print(summary_for_operator(report))
    print()
    if report.passed:
        print("PASS: scenario passed all assertions + all LCP gates.")
        return 0
    print("FAIL: scenario produced findings; see lcp_report.json for detail.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="watch_47_morning")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument(
        "--output-root",
        default=None,
        help="default: proto/textverse/scenarios/output/",
    )
    args = parser.parse_args()
    output_root = Path(args.output_root) if args.output_root else _default_output_root()
    return asyncio.run(_run(args.scenario, args.base_url, output_root))


if __name__ == "__main__":
    sys.exit(main())
