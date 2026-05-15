"""astra.physics — bridge to the verified C++ physics core.

Implements spec v0.128 §3 (Time Architecture) and §6 (Unified Sampler) by
querying `proto/astra_nexus` via JSON-over-stdio. No physics math implemented
here — this is a thin adapter that respects the Calculator-bound LLM Agency
primitive (§15.6): every LLM that needs a number routes through this module.

Files:
- nexus_bridge.py: JSON-over-stdio client to proto/astra_nexus.exe
- composition_rule.py: dτ_ship/dt_cosmic queries via bridge
- observation_calc.py: §6.3 Observation Calculator (stateless, parallel-friendly)
- kepler.py: body state queries via bridge
- tools.py: tool function surface exposed to LLMs (the calculator they call)

Prerequisite: proto/astra_nexus.exe must support --stdio-server mode (Day 2 work
adds this; ~50 lines C++ to the existing binary).

Implementation: Day 2.
"""
