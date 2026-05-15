"""astra.scenarios — scenario runner + YAML schema.

A scenario is the atomic unit of LCP validation. Each scenario is a YAML file
defining:
- initial_state (ship state, universe bodies, REEL seed entries)
- operator (kind = scripted / interactive / llm_proxy; inputs at τ_ship marks)
- assertions (termination conditions, per-turn gate requirements,
              session-level aggregate pass rates)

The scenario library at `library/` grows as findings surface new edge cases.
Each new scenario must justify its existence by exercising a regime, channel,
or failure mode not covered by existing scenarios.

Files:
- schema.py: Pydantic models for scenario YAML validation
- runner.py: Loads YAML, executes through harness.orchestrator, scores via judge
- library/:  The actual .yaml scenarios

The first canonical scenario lives in proto/textverse/scenarios/watch_47_morning.md
as a manual reference. Day 6 work translates it to library/watch_47_morning.yaml.

Implementation: Day 6.
"""
