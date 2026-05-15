# textverse — ASTRA-7 closed-loop verification bench

The Python orchestrator that closes the first LCP loop for ASTRA-7. Coordinates three local-LLM instances (ASTRA-LLM, Narrator-LLM, Adapter-LLM) calculator-bound to the verified C++ physics binary (`proto/astra_nexus`). Runs scenarios from YAML; scores via the 9-gate Loop Closure Property.

**Status:** scaffolding only. v0 implementation Day 1+ pending. See `ARCHITECTURE.md`.

---

## Read these first

1. **`STARTUP.md`** — orientation directive for fresh sessions (humans or coding agents)
2. **`ARCHITECTURE.md`** — full ground-up design + 7-day implementation plan
3. **`../../docs/spec-v0.128.md`** — the spec envelope this conforms to
4. **`../../docs/astra-sysprompt.md` + `../../docs/astra-sysprompt-addendum-stage.md`** — Surface 5 (persona envelope)

---

## Install (when implementation begins)

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
cd C:/ASTRA-7/proto/textverse
uv venv
uv pip install -e ".[dev]"
```

Verify:

```bash
uv run pytest
```

Expected at scaffold stage: one passing sanity test confirming the package imports.

---

## Run (when implementation lands; not yet available)

Interactive REPL against vanilla Qwen on local llama.cpp:

```bash
uv run astra repl
```

Run a scenario:

```bash
uv run astra run astra/scenarios/library/watch_47_morning.yaml
```

Full LCP suite:

```bash
uv run astra bench
```

---

## What's in this directory

```
proto/textverse/
├── ARCHITECTURE.md             clean-slate architecture, 7-day plan
├── STARTUP.md                  orientation directive for fresh sessions
├── README.md                   this file
├── CHANGELOG.md                version history
├── pyproject.toml              uv-managed Python project
├── .gitignore
│
├── astra/                      Python package (scaffolded; implementation pending)
├── prompts/                    Surface 5 — persona sysprompts (forthcoming)
├── tests/                      pytest suite
├── scenarios/                  manual scenario .md docs (not YAML-yet)
└── docs/                       additional docs (e.g., this file linked into spec)
```

---

## Discipline

Per `docs/spec-v0.128.md` §15.4: the envelope is locked; the sculpting begins. Implementation findings revise the spec when they surface real envelope-level issues. Don't pre-optimize; close the loop first, refine after.

Per `docs/spec-v0.128.md` §15.6: every LLM call in this bench is calculator-bound. No numeric token in any LLM output is acceptable unless it traces to a verified tool-call result. Enforced by `astra/llm/validator.py`.

Per `docs/spec-v0.128.md` §15.7: this is Implementation A of the dual-implementation discipline. UE5 will be Implementation B. Both consume the same spec envelope. Never let textverse drift the envelope to fit textverse-specific needs; if the envelope needs to change, change the spec, not the bench.
