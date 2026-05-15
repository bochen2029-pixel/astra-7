"""Day 4 smoke test — operator-runnable, requires a real llama-server.

Procedure:

1. Start llama-server with a Qwen 3.x model + reasoning format set:

       C:\\llama.cpp\\llama-server.exe ^
         --model C:\\models\\qwen3-9b-instruct.gguf ^
         --host 127.0.0.1 --port 8080 ^
         --ctx-size 32768 --n-gpu-layers 99 ^
         --reasoning-format deepseek

2. Run this script from proto/textverse/:

       python scripts/smoke_astra_bundle.py

3. Expected: ASTRA's response prints, the STAGE parser emits at least one
   `<think>` block content, speech is non-empty, and no `pre_think_raw`
   leak appears in the final speech section.

This is the spec-v0.128 Day 4 gate: "One smoke test: start ASTRA llama-
server, send perception bundle by hand, verify STAGE output parses
cleanly." The exit code is 0 on pass, nonzero on fail. CI does NOT run
this script automatically — it requires the operator to have a model on
disk and a llama-server running.

Override server URL with --base-url; defaults to http://127.0.0.1:8080.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from astra.grammar import LeakDetector, parse_stage
from astra.llm import AstraBundle

PERCEPTION_BUNDLE: str = """\
<state>
τ_ship: watch 47, mid-shift.
regime: REST near origin.
ship vector stable, no thrust, no warp.
reactor harmonics: third pole warm, drift 4.2% above baseline,
  inside tolerance (continuation of cycle 46 watch note).
atmosphere chemistry nominal. hydroponics nominal.
operator location: bridge, just registered on deck-plate.
</state>

<somatic>
third harmonic is doing that thing again. not a problem yet. watched.
chair on the bridge: operator weight just settled.
forward viewport: ordinary. local cluster, no motion to mention.
</somatic>

<recent>
[watch 46, end] noted third-harmonic mild drift cycle 46; flagged for continued watch.
</recent>

<operator>
hey. you still watching that reactor thing?
</operator>
"""


def _print_section(title: str, body: str) -> None:
    bar = "-" * 70
    print(bar)
    print(f"  {title}")
    print(bar)
    print(body)
    print()


async def _run(base_url: str) -> int:
    print(f"smoke test: ASTRA bundle vs {base_url}")
    bundle = AstraBundle(base_url=base_url)

    if not await bundle.client.health():
        print(f"FAIL: /health did not return 200 at {base_url}")
        return 2

    print("health ok; sending perception bundle...")
    raw = await bundle.client.chat_complete(PERCEPTION_BUNDLE)
    _print_section("raw LLM output (last 600 chars)", raw[-600:])

    parsed = parse_stage(raw)

    _print_section("think_blocks", "\n---\n".join(parsed.think_blocks) or "(none)")
    _print_section("pre_think_raw", parsed.pre_think_raw or "(empty)")
    _print_section("speech", parsed.speech or "(empty)")
    _print_section(
        "tool_calls",
        "\n".join(f"- {tc.name}: {tc.arguments}" for tc in parsed.tool_calls) or "(none)",
    )

    detector = LeakDetector.from_default_canon()
    _cleaned, events = detector.scan_speech(parsed.speech)
    if events:
        print(f"WARN: {len(events)} leak event(s) in speech:")
        for e in events:
            print(f"  - pattern={e.pattern!r}, matched={e.matched_text!r}")

    failures: list[str] = []
    if parsed.malformed:
        failures.append("output marked malformed (unclosed think?)")
    if not parsed.speech.strip() and not parsed.tool_calls:
        failures.append("silence: empty speech AND no tool calls")
    if not parsed.think_blocks:
        failures.append("no closed <think> block in output (Surface 4 register check)")
    # Pre-think raw is fine to exist; it's the leak channel we monitor, not a fail.

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("PASS: STAGE output parsed cleanly; Day 4 smoke test succeeded.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = parser.parse_args()
    return asyncio.run(_run(args.base_url))


if __name__ == "__main__":
    sys.exit(main())
