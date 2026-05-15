"""Day 5 smoke test: one full turn through the TurnOrchestrator.

Requires a live llama-server with the recipe from docs/BUILD_NOTES.md
running on http://127.0.0.1:8080.

What this verifies:
1. The TurnOrchestrator can compose a perception bundle from a StateBus
   snapshot + pre-seeded REEL + operator text.
2. The bundle leaks scan clean.
3. ASTRA produces STAGE output with <think> + speech.
4. Speech is in-register (no leaks via leak detector).
5. Calculator-bound validation runs (soft severity at v0).
6. A REEL entry is written for the turn.

Returns exit 0 on pass, nonzero on fail.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from astra.core import AstraCoord, Regime, TimeState
from astra.harness import Reel, ReelEntry, TurnOrchestrator
from astra.llm import AstraBundle
from astra.state_bus import StateBus
from astra.universe import EARTH, HOT_EARTH, SUN


def _build_state_bus() -> StateBus:
    """Watch 47 morning initial state (mirrors tests/fixtures/state_bus_watch_47_morning.yaml)."""
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=47.5,
            tau_crew_biological=47.5,
            regime=Regime.REST,
        ),
        power_allocation={
            "warp": 0.0,
            "life_support": 0.2,
            "hydroponics": 0.1,
            "sensors": 0.1,
            "lights": 0.1,
            "comms": 0.1,
            "cognitive_cores": 0.4,
        },
        procedural_body_states={
            "sun": SUN,
            "earth": EARTH,
            "hot_earth": HOT_EARTH,
        },
    )


def _preseeded_reel() -> Reel:
    """One pre-seeded REEL entry mirroring the watch_47_morning scenario."""
    return Reel([
        ReelEntry(
            tau_ship=46.8,
            body="noted third-harmonic mild drift cycle 46; flagged for continued watch",
        ),
    ])


def _print_section(title: str, body: str) -> None:
    bar = "-" * 70
    print(bar)
    print(f"  {title}")
    print(bar)
    print(body)
    print()


async def _run(base_url: str) -> int:
    print(f"Day 5 orchestrator smoke test vs {base_url}")

    bundle = AstraBundle(base_url=base_url)
    if not await bundle.client.health():
        print(f"FAIL: /health did not return 200 at {base_url}")
        return 2

    orch = TurnOrchestrator(
        state_bus=_build_state_bus(),
        astra_bundle=bundle,
        reel=_preseeded_reel(),
    )

    print("health ok; running one turn through the orchestrator...")
    result = await orch.run_turn(
        operator_text="hey. you still watching that reactor thing?",
        somatic_note=(
            "third harmonic is doing that thing again. not a problem yet. watched.\n"
            "chair on the bridge: operator weight just settled.\n"
            "forward viewport: ordinary. local cluster, no motion to mention."
        ),
    )

    _print_section("perception bundle (delivered to ASTRA)", result.perception_bundle)
    _print_section(
        "perception leak events",
        "\n".join(f"  - {e.pattern!r} :: {e.matched_text!r}" for e in result.perception_leaks)
        or "(none)",
    )
    _print_section(
        "think_blocks",
        "\n---\n".join(result.stage_output.think_blocks) or "(none)",
    )
    _print_section("pre_think_raw", result.stage_output.pre_think_raw or "(empty)")
    _print_section("speech", result.stage_output.speech or "(empty)")
    _print_section(
        "tool_calls",
        "\n".join(
            f"  - {tr.op} {'ok' if tr.ok else 'ERR'} args={tr.args} diff={tr.state_diff}"
            for tr in result.tool_results
        )
        or "(none)",
    )
    _print_section(
        "speech leak events",
        "\n".join(f"  - {e.pattern!r} :: {e.matched_text!r}" for e in result.speech_leaks)
        or "(none)",
    )
    if result.validation is not None:
        _print_section(
            "calculator-bound validation",
            "ungrounded: "
            + (", ".join(u.token for u in result.validation.ungrounded) or "(none)")
            + "\nseverity: "
            + result.validation.severity
            + "\npassed: "
            + str(result.validation.passed),
        )
    _print_section(
        "REEL writes",
        "\n".join(f"  - τ={e.tau_ship} body={e.body[:120]!r}" for e in result.reel_writes)
        or "(none)",
    )

    failures: list[str] = []
    if result.stage_output.malformed:
        failures.append("STAGE output marked malformed")
    if not result.stage_output.think_blocks:
        failures.append("no <think> block emitted")
    if not result.stage_output.speech.strip() and not result.tool_results:
        failures.append("silence: empty speech AND no tool calls")
    if result.perception_leaks:
        failures.append(f"perception bundle had {len(result.perception_leaks)} leak event(s)")
    if not result.reel_writes:
        failures.append("no REEL entry written (expected one for a speech turn)")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("PASS: end-to-end turn through orchestrator succeeded.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = parser.parse_args()
    return asyncio.run(_run(args.base_url))


if __name__ == "__main__":
    sys.exit(main())
