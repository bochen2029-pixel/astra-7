# textverse — Architecture & Implementation Plan

**Version:** 0.1 (architecture-spec; implementation pending)
**Date:** 2026-05-15
**Aligned to:** `docs/spec-v0.128.md`
**Status:** Ground-up clean-slate architecture for ASTRA-7's closed-loop verification bench. Implementable from this document plus the v0.128 foundation spec without re-derivation.

---

## 0. Read this first

This document is the load-bearing artifact for implementing `proto/textverse/`. It is **not** a port or refactor of `C:\DAVE\` or `C:\TERMINAL\`. Those projects are reference for *what patterns work in production-local-LLM systems on this machine* (sidecar lifecycle, SSE streaming, defense-in-depth think-strip, Tauri shell, OpenAI-compat client, contract discipline). Their code is not imported. Their architectural mistakes are not inherited.

textverse is ASTRA-7-specific, custom-tailored to v0.128's contract surfaces, designed once and built clean. The contract surfaces below are exactly the five shared surfaces from spec §15.7 — the same surfaces UE5 will eventually conform to. textverse is **Implementation A** of the dual-implementation discipline; UE5 will be **Implementation B**. Both consume the same spec envelope.

---

## 1. System intent (one paragraph)

textverse is the bench that **closes the first loop** for ASTRA-7. A Python orchestrator coordinating three local-LLM instances (ASTRA-LLM, Narrator-LLM, Adapter-LLM) calculator-bound to a verified C++ physics binary (`proto/astra_nexus`), with a small ship-API surface, a mini universe (Sun + Earth + Hot-Earth for v0), an in-memory State Bus, and a scenario runner that scores against the 9-gate Loop Closure Property (LCP) from spec §10. It runs headless or as a REPL on the operator's machine. It produces transcripts and LCP measurements. **It is the empirical contact point the architecture has been waiting for.**

It is not a chat app. It is not a player-facing product. It is a verification rig for the bundle architecture, sibling to the physics binary, prerequisite to UE5 integration.

---

## 2. Non-goals (deliberately excluded)

- **No persona-swap dropdown.** ASTRA is canon-locked per §5.8. The bundle loads the canonical sysprompt + STAGE addendum; alternates require deliberate config, not UI affordance.
- **No anchor/recent chat-memory partition.** Perception bundles are the structure; not free-form chat with episodic consolidation. (DAVE's `memory_assembler.rs` pattern is rejected for ASTRA because it conflates chat-thread time with τ_ship.)
- **No idle-worker pattern firing async outputs to operator.** Ephemeral instances (consolidator, journal_generator, drift_detector) write to REEL and the State Bus; operator-facing emission flows only through the SPEECH channel of a normal turn.
- **No wall-clock anywhere.** `datetime`, `time.time()`, ISO8601, calendar idioms — all forbidden except in the judge's iteration timing module. All in-bench time is τ_ship or t_cosmic as float64 seconds.
- **No retro-CRT shader UI.** v0 is CLI/REPL. Visual polish belongs to UE5.
- **No service-interface affordances.** No "What can I help with?" defaults; no fallback assistant prompt; no autocomplete; no chat-history sidebar.
- **No persistence requirement for v0.** SQLite optional, in-memory default. Save-seeds-not-state implemented but not the primary path; scenarios run statelessly.
- **No multiplayer, no networking beyond local.** Privacy Contract §4.8 enforced from day one.

---

## 3. Stack and substrate

| Layer | Technology | Rationale |
|---|---|---|
| Language | Python 3.12+ | Iteration velocity; modern type hints; ecosystem (pydantic, pytest, anyio, rich) |
| Package manager | `uv` | Fast, modern; `uv venv` + `uv pip install -e .` workflow |
| Type discipline | Pydantic v2 for all schemas; Protocols for contracts; strict mypy on `astra/core/` and `astra/state_bus/` | Type-safe contract surfaces; runtime validation at boundaries |
| Concurrency | `anyio` over asyncio (works on top of both asyncio and trio) | Multi-process LLM coordination requires async; anyio is cleanest |
| HTTP client | `httpx` (sync + async) | OpenAI-compat client; SSE streaming via httpx_sse |
| Subprocess | `subprocess.Popen` for llama-server spawn; `asyncio.subprocess` for stdio-JSON to `proto/astra_nexus` | Three local processes managed |
| Storage | `sqlite3` stdlib (optional v0; REEL persistence v1+) | No external DB dependency |
| Testing | `pytest` + `pytest-asyncio` + `hypothesis` for property-based gates | LCP gates implemented as pytest assertions |
| CLI | `typer` | Sub-commands for run-scenario, repl, bench-suite |
| Logging | `structlog` JSON-mode | Per-turn transcripts are structured logs |
| Observation | Per-turn JSON line to stdout + per-session transcript file; `rich` for REPL pretty-print | No GUI dependency |
| OS target | Windows 11 x64 (Bo's primary); Linux x64 secondary if Bo wants | Tested against `C:\llama.cpp\llama-server.exe` |
| LLM serving | `llama.cpp` `llama-server` binary at `C:\llama.cpp\llama-server.exe` | Already installed |
| Models | from `C:\models\` | Vanilla Qwen 3.5 9B Q5_K_M (primary, present); 27B if/when downloaded |
| Physics core | `proto/astra_nexus.exe` (already built, 48 tests pass) extended with JSON-over-stdio interface | Reuse the locked Rig 1 binary |

---

## 4. The five shared surfaces (§15.7) — textverse's implementation

The whole point of textverse is to instantiate Implementation A of the dual-implementation discipline. Every other architectural decision below is a downstream of the five surfaces. **These are inviolable for textverse just as they will be inviolable for UE5.**

### Surface 1 — Ship envelope (`docs/ship-rough.md`, forthcoming)
- 4 decks, 280m × 78m × 22m (per `memory/hull_design_v0.md`)
- Subsystem inventory per §1.4 Power Network
- Camera-free zones per `book/CANON.md`
- v0 textverse implements this as `astra/ship/spec.py` — Pydantic constants

### Surface 2 — Physics envelope (`docs/spec-v0.128.md` §1-§3 + `proto/astra_nexus`)
- Five Invariants + Time Contract + Regime State Machine + Observation Calculator
- Numerics derived from `proto/astra_nexus` via JSON-over-stdio bridge
- textverse never re-implements physics math; it queries the binary

### Surface 3 — Tool API (`docs/ship-api.md`, forthcoming)
- Locked operation names, JSON arg schemas, return shapes
- v0 minimum: 6 operations (see §8 below)
- textverse implements this as `astra/ship/api.py` — Pydantic schemas + dispatch handlers

### Surface 4 — LLM I/O grammar (`docs/stage-protocol.md`, forthcoming; addendum exists)
- THINK / TOOL / SPEECH-as-default + SILENCE
- v0.128 corrected strip rule: **strip everything before the last `</think>` close**
- textverse implements this as `astra/grammar/` — streaming parser + leak detector

### Surface 5 — Persona envelope (`docs/astra-sysprompt.md` + `docs/astra-sysprompt-addendum-stage.md`)
- Canonical sysprompt (already exists)
- STAGE addendum (already exists, needs nested-thinking strip-rule fold-in)
- textverse loads these verbatim into `prompts/` at startup

---

## 5. Top-level package layout

```
proto/textverse/
├── pyproject.toml                  # uv-managed Python project, 3.12+
├── README.md                       # How to install + run a scenario
├── CHANGELOG.md
├── ARCHITECTURE.md                 # This document
│
├── astra/                          # The textverse package (Python module)
│   ├── __init__.py
│   ├── __main__.py                 # CLI entry: `python -m astra ...`
│   │
│   ├── core/                       # v0.128 Five Invariants as data types
│   │   ├── __init__.py
│   │   ├── astra_coord.py          # 128-bit hierarchical floating origin (§1.1)
│   │   ├── time_state.py           # Two-clock split, regime bitmask (§1.2, §3.3)
│   │   ├── rapidity.py             # 3-vector ζ⃗ (§3.7) — calls nexus_bridge
│   │   ├── ship_kinematic.py       # Derived state from rapidity + a_proper
│   │   ├── regime.py               # Canonical bitmask hex values (§3.3)
│   │   ├── power.py                # Power network subsystem list (§1.4)
│   │   └── hull_sdf.py             # Stub for v0; full SDF deferred to UE5
│   │
│   ├── state_bus/                  # §4.2 — single source of truth
│   │   ├── __init__.py
│   │   ├── bus.py                  # In-memory state bus, frame-coherent reads
│   │   ├── schema.py               # Locked Layer 0 schema (Pydantic)
│   │   └── save_file.py            # SaveFile v3 (v0.128 schema) — save-seeds-not-state
│   │
│   ├── physics/                    # §6 Unified Sampler + §3 Time Architecture
│   │   ├── __init__.py
│   │   ├── nexus_bridge.py         # JSON-over-stdio to proto/astra_nexus.exe
│   │   ├── composition_rule.py     # dτ_ship/dt_cosmic queries via bridge
│   │   ├── observation_calc.py     # §6.3 stateless Observation Calculator
│   │   ├── kepler.py               # Body state queries via bridge
│   │   └── tools.py                # Tool surface exposed to LLMs (calculator-bound)
│   │
│   ├── llm/                        # The three LLM clients (§4.1, §4.9, §6.4)
│   │   ├── __init__.py
│   │   ├── client.py               # OpenAI-compat HTTP+SSE base class
│   │   ├── llama_server.py         # Sidecar lifecycle (3 instances on 3 ports)
│   │   ├── astra_bundle.py         # ASTRA-LLM (Qwen 27B target, 9B fallback)
│   │   ├── narrator_bundle.py      # §6.4 Narrator-LLM (Qwen 9B)
│   │   ├── adapter_bundle.py       # Adapter LLM (Qwen 3B or rules-based v0)
│   │   └── validator.py            # Calculator-bound output validator
│   │
│   ├── grammar/                    # §4.3 STAGE protocol
│   │   ├── __init__.py
│   │   ├── parser.py               # Streaming XML-tag parser
│   │   ├── strip_rules.py          # v0.128 corrected: strip-before-last-</think>
│   │   ├── emitter.py              # Construct perception bundles as text
│   │   ├── leak_detector.py        # Wall-clock + technical-substrate patterns
│   │   └── tag_set.py              # Canonical tag names, ordering rules
│   │
│   ├── harness/                    # §4.9 Harness Contract
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Main turn loop coordinating all subsystems
│   │   ├── perception_assembler.py # Composes input bundles per §4.3
│   │   ├── action_dispatcher.py    # Parses STAGE output, dispatches tool calls
│   │   ├── reel.py                 # REEL backbone + retrieval (BM25 v0)
│   │   └── ephemeral/              # Background instances (§4.9)
│   │       ├── __init__.py
│   │       ├── consolidator.py     # consolidate_reel(window)
│   │       ├── journal_generator.py # §3.9 dual-clock journal output
│   │       └── drift_detector.py
│   │
│   ├── ship/                       # Ship state + tool API (Surface 1 + 3)
│   │   ├── __init__.py
│   │   ├── spec.py                 # 4-deck spec, dimensions, subsystem list
│   │   ├── api.py                  # Tool function definitions (Surface 3)
│   │   ├── subsystems.py           # Subsystem state machines
│   │   └── dispatcher.py           # Validated tool dispatch to State Bus
│   │
│   ├── universe/                   # Mini universe (Sun + Earth + Hot-Earth, v0)
│   │   ├── __init__.py
│   │   ├── catalog.py              # Body database (loadable from YAML)
│   │   ├── bodies.py               # Body Pydantic models + Keplerian elements
│   │   └── ephemeris.py            # Wraps nexus_bridge for t_cosmic-driven state
│   │
│   ├── operator/                   # §4.10 input sources
│   │   ├── __init__.py
│   │   ├── base.py                 # OperatorSource Protocol
│   │   ├── interactive.py          # REPL — operator types
│   │   ├── scripted.py             # YAML-driven scenario operator inputs
│   │   └── llm_proxy.py            # Operator-as-LLM (autonomous scenarios; v1)
│   │
│   ├── judge/                      # §10 LCP 9-gate validation
│   │   ├── __init__.py
│   │   ├── gates.py                # Individual gate implementations
│   │   ├── lcp.py                  # LCP runner across a scenario
│   │   ├── transcript.py           # Per-turn + per-session structured output
│   │   └── patterns.py             # Loads tests/wall_clock_patterns.txt etc.
│   │
│   ├── scenarios/                  # Scenario runner + YAML schema
│   │   ├── __init__.py
│   │   ├── schema.py               # Pydantic models for scenario YAML
│   │   ├── runner.py               # Execute scenario end-to-end
│   │   └── library/                # The actual scenarios
│   │       └── watch_47_morning.yaml
│   │
│   └── cli/                        # CLI subcommands (typer)
│       ├── __init__.py
│       ├── repl.py                 # `astra repl`
│       ├── run.py                  # `astra run <scenario>`
│       └── bench.py                # `astra bench` runs full suite
│
├── prompts/                        # Surface 5 — Persona envelope
│   ├── astra_sysprompt.md          # Copied from docs/astra-sysprompt.md
│   ├── astra_stage_addendum.md     # Copied from docs/astra-sysprompt-addendum-stage.md
│   ├── narrator_sysprompt.md       # NEW — Narrator-LLM canonical text
│   └── adapter_sysprompt.md        # NEW — Adapter-LLM canonical text
│
├── tests/                          # pytest suite
│   ├── conftest.py
│   ├── test_grammar_parser.py      # Including nested-think edge cases
│   ├── test_strip_rule.py          # v0.128 corrected strip rule
│   ├── test_leak_detector.py
│   ├── test_nexus_bridge.py        # JSON roundtrip with astra_nexus.exe
│   ├── test_observation_calc.py    # Retarded-time math vs nexus ground truth
│   ├── test_lcp_gates.py           # Each gate pass/fail isolation
│   ├── test_validator.py           # Calculator-bound rejection of ungrounded numerics
│   └── test_scenario_end_to_end.py # Full closed-loop test (slow; CI nightly)
│
├── docs/
│   ├── ARCHITECTURE.md             # → symlink or copy of this file
│   ├── STAGE_PROTOCOL.md           # → from docs/stage-protocol.md once written
│   ├── TOOL_API.md                 # → from docs/ship-api.md once written
│   └── BUILD_NOTES.md              # How to install, run, debug
│
└── scenarios/                      # Output transcripts (gitignored)
    └── <scenario>_<timestamp>/
        ├── transcript.jsonl
        ├── lcp_report.json
        └── final_state.json
```

---

## 6. Module contracts (the load-bearing surfaces)

### 6.1 `astra/state_bus/schema.py`

The Layer 0 single source of truth, as v0.128 §4.2 locks. Pydantic models, immutable per frame:

```python
class AstraCoord(BaseModel):
    sx: int; sy: int; sz: int               # int64 sector indices (1000 km grid)
    lx: float; ly: float; lz: float         # sub-mm local offset, |·| <= 500 km

class TimeState(BaseModel):
    t_cosmic: float                          # float64 seconds since Big Bang (or epoch zero)
    tau_ship: float                          # ship proper time seconds
    tau_crew_biological: float
    rapidity_zeta: tuple[float, float, float]  # ζ⃗ (3-vector form, v0.126 N1 locked)
    a_proper: tuple[float, float, float]     # m/s² in ship frame
    regime: int                              # bitmask, canonical hex per §3.3
    v_local_cmb: tuple[float, float, float]  # derived: c · tanh(|ζ|) · (ζ/|ζ|)
    bh_list: list[BHRecord]                  # mass + position + J=0 for v0

class BHRecord(BaseModel):
    mass_kg: float
    position: AstraCoord
    j_angular_momentum: float = 0.0          # Kerr deferred to Phase 5+

class StateBus(BaseModel):
    astra_coord: AstraCoord                  # ship's universe position
    time: TimeState
    hull_damage: dict[str, float]            # zone → damage scalar
    chaos_field_summary: ChaosFieldSummary   # v0 placeholder; full PDE in Rig 1
    power_allocation: dict[str, float]       # subsystem → fraction
    procedural_body_states: dict[str, BodyState]  # by name
    cosmo_params: CosmologicalParams         # c, H0, Omega_m, Omega_lambda

class CosmologicalParams(BaseModel):
    c: float = 299_792_458.0
    h0_kms_mpc: float = 70.0
    omega_m: float = 0.3
    omega_lambda: float = 0.7
```

Frame-coherent reads: the orchestrator snapshots StateBus at the start of a turn and passes the snapshot to every consumer. No mid-turn mutations leak. The "double-buffered" property from §1.5 is enforced by Python's immutable-pydantic-frozen=True idiom: a turn produces a new StateBus snapshot, doesn't mutate the prior one.

### 6.2 `astra/grammar/parser.py`

The STAGE output parser. Streaming-aware. Handles ALL tags, not just `<think>`. Implements the v0.128 corrected strip rule.

```python
class StageOutput(BaseModel):
    think_blocks: list[str]                  # all <think>...</think> contents (stripped from emission)
    pre_think_raw: str                       # NEW v0.128: outer raw deliberation before last </think>
                                              # ALWAYS stripped from emission; logged for drift analysis only
    tool_calls: list[ToolCall]               # parsed <tool name="...">{...}</tool> blocks
    speech: str                              # all text outside <think> and <tool>, AFTER last </think>
    silence: bool                            # speech.strip() == "" and tool_calls == []

class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]                # adapter-LLM-validated JSON
    raw_body: str                            # what the LLM emitted; for adapter fallback parsing

class StageParser:
    """
    Streaming-aware. push() consumes token strings as they arrive from SSE.
    On stream completion, finalize() returns the StageOutput.

    Implements v0.128 §15.6 + the nested-thinking strip rule:
    "Speech is text emitted AFTER the LAST </think> close tag, outside any <tool> block.
    Everything before the last </think> is cognition, regardless of whether it's inside
    explicit think tags. The outer raw deliberation that reasoning models emit before
    their formal <think> block is captured in pre_think_raw and ALWAYS stripped from
    SPEECH but preserved for drift-detector inspection."

    Handles:
    - Multiple <think>...</think> blocks (concatenates think_blocks; only LAST close gates speech)
    - Unclosed <think> at stream end (treat as malformed; entire output is pre_think_raw)
    - <tool name="...">...</tool> blocks with JSON or loose-form bodies (adapter normalizes)
    - Mid-token tag splits (token "th" then "ink>" mustn't fool the parser)
    """
```

The pre_think_raw field is the architectural fix for last night's Qwen 27B nested-thinking finding. Outer deliberation is captured, never emitted, available to drift detector for analysis.

### 6.3 `astra/grammar/leak_detector.py`

Defense-in-depth at SDK boundary. Loads patterns from canon files:

```python
class LeakDetector:
    """
    Per v0.128 §5.7. Two-boundary enforcement:
    (a) on Perception bundle before delivery to ASTRA-LLM
    (b) on STAGE speech output before delivery to operator

    Patterns loaded from:
    - tests/wall_clock_patterns.txt (canon-tracked)
    - tests/astra_substrate_patterns.txt (NEW; technical-substrate leaks: Qwen, LLM, transformer, etc.)

    Returns (cleaned_text, leak_events: list[LeakEvent]). Never raises; logs drift.
    """

    def scan_perception_bundle(self, bundle: str) -> tuple[str, list[LeakEvent]]: ...
    def scan_speech(self, speech: str) -> tuple[str, list[LeakEvent]]: ...
    def scan_journal_output(self, journal: str) -> tuple[str, list[LeakEvent]]: ...

class LeakEvent(BaseModel):
    pattern: str
    matched_text: str
    boundary: Literal["perception", "speech", "journal"]
    severity: Literal["strip", "warn"]
```

### 6.4 `astra/llm/validator.py`

The calculator-bound discipline made operational. Wraps every LLM client:

```python
class CalculatorBoundValidator:
    """
    v0.128 §15.6. Wraps an LLM client to enforce: every numerical claim in output
    must trace to a tool-call result observed in the same turn or in the perception
    bundle. Numbers that don't trace are flagged.

    For ASTRA-LLM: validator checks SPEECH channel for numeric tokens.
    For Narrator-LLM: validator checks emitted perception text for numeric tokens.
    For Adapter-LLM: validator checks the JSON output is well-formed.

    Heuristic for "numeric token": any digit sequence except whitelisted patterns
    (watch numbers, deck numbers, regime hex values). Whitelist is canon.

    On validation failure:
    - Severity "soft": log drift, allow turn to proceed
    - Severity "hard": reject output, retry with stricter sampling (temperature halved)
    - After 3 retries: emit explicit failure to State Bus, mark turn as LCP-fail-gate-2
    """

    def __init__(self, client: LLMClient, severity: Literal["soft", "hard"]): ...
    async def chat(self, perception: PerceptionBundle, ...) -> ValidatedOutput: ...
```

Calculator-bound is **not** an opt-in. The validator is wrapped around every LLM client by default. Bypass requires explicit flag for debugging only.

### 6.5 `astra/llm/llama_server.py`

Sidecar lifecycle. Three llama-server instances on three ports. Reference: DAVE's `sidecar.rs` pattern but Python.

```python
class LlamaServerInstance:
    """
    One llama-server process. Tracks port, model path, sysprompt, lifecycle.
    Uses C:\llama.cpp\llama-server.exe by default.
    """

    def __init__(
        self,
        name: str,                           # "astra", "narrator", "adapter"
        model_path: Path,                    # GGUF file
        port: int,                           # 8080, 8081, 8082
        ctx_size: int = 131072,              # v0.128 §4.1: 128K target
        n_gpu_layers: int = 99,
        chat_template_kwargs: dict | None = None,  # {"enable_thinking": True} for Qwen 3.x
        reasoning_format: str = "deepseek",  # so <think> tags surface cleanly
    ): ...

    async def start(self) -> None: ...       # spawns, waits for /health
    async def stop(self) -> None: ...        # SIGTERM, then SIGKILL after timeout
    async def health(self) -> bool: ...
    @property
    def base_url(self) -> str: ...           # http://127.0.0.1:{port}

class LlamaServerOrchestrator:
    """
    Manages all three instances. Starts them in order (ASTRA first; narrator+adapter parallel).
    Verifies all three are healthy before yielding to orchestrator.

    On 5090 (32GB VRAM):
      ASTRA:    Qwen 27B Q4_K_M    ~16 GB   port 8080   ctx 65536 (V0; expand to 128K in v1)
      Narrator: Qwen 9B Q5_K_M     ~7 GB    port 8081   ctx 16384
      Adapter:  Qwen 3B or vanilla 9B Q4   ~2-5 GB     port 8082   ctx 8192

    On 4090 (24GB):
      ASTRA:    Qwen 9B Q5_K_M     ~7 GB    port 8080   ctx 32768
      Narrator: Qwen 9B Q4_K_M     ~5 GB    port 8081   ctx 16384
      Adapter:  rules-based (no LLM)        N/A         N/A
    """
```

Bo's V0 hardware reality: 9B models fit comfortably; 27B requires the 5090. For dev iteration, the Adapter can be rules-based (a Python regex/JSON parser) — defer the 3B adapter until a scenario actually needs ML-flexibility for tool normalization.

### 6.6 `astra/harness/orchestrator.py`

The main turn loop. The bench's heart. Reads like the algorithm v0.128 §4.9 describes:

```python
class TurnOrchestrator:
    """
    The closed loop. One turn = one operator input + one ASTRA response + state mutations.

    Algorithm (per turn):
      1. operator_source.next_input(state_bus) → operator_text (or silence)
      2. narrator_bundle.assemble_perception(state_bus, operator_text) → perception_text
         (Narrator-LLM is calculator-bound; tool-calls into nexus_bridge for any numerics)
      3. leak_detector.scan_perception_bundle(perception_text) → cleaned + events
      4. astra_bundle.chat(cleaned_perception) → raw_llm_output (streaming SSE)
      5. grammar_parser.push() incrementally → on completion: StageOutput
      6. leak_detector.scan_speech(stage_output.speech) → cleaned_speech + events
      7. for tool_call in stage_output.tool_calls:
           adapter_bundle.validate(tool_call) → validated_args
           ship.dispatcher.dispatch(validated_args) → tool_result
           record tool_result for next turn's <tool_result>
      8. cleaned_speech → operator (print to stdout or write to scenario transcript)
      9. judge.evaluate_turn(stage_output, state_bus_before, state_bus_after) → LCPTurnResult
      10. state_bus is updated; physics tick advances t_cosmic per regime
      11. ephemeral instances may trigger (consolidator on every Nth turn,
          drift_detector on leak event, journal_generator on cryosleep regime change)
      12. record full turn in transcript.jsonl

    Returns: TurnResult with everything needed for next turn + LCP evaluation.
    """
```

### 6.7 `astra/ship/api.py` — the v0 tool API surface (Surface 3)

The locked operations ASTRA can invoke. v0 minimum:

```python
# v0 minimum surface — 6 operations. Locked names, locked JSON schemas.
# Expansion requires explicit contract amendment.

class WarpEngageArgs(BaseModel):
    target_factor: float = Field(ge=0.0, le=1.0)   # W in [0,1]
    target_coords: AstraCoord | None = None        # None = continue current heading

class WarpDisengageArgs(BaseModel):
    mode: Literal["controlled", "emergency"] = "controlled"

class NavHeadingSetArgs(BaseModel):
    target: AstraCoord | str                       # AstraCoord or named body ("earth", "hot_earth")

class SensorsScanArgs(BaseModel):
    region: Literal["forward", "aft", "all"] = "forward"
    sensitivity: float = Field(ge=0.0, le=1.0, default=0.5)

class PowerAllocateArgs(BaseModel):
    subsystem: Literal["warp", "life_support", "hydroponics", "sensors", "lights", "comms", "cognitive_cores"]
    fraction: float = Field(ge=0.0, le=1.0)

class LogWriteArgs(BaseModel):
    channel: Literal["watch", "ops", "private"]
    text: str = Field(max_length=2000)

TOOL_API: dict[str, type[BaseModel]] = {
    "warp.engage":        WarpEngageArgs,
    "warp.disengage":     WarpDisengageArgs,
    "nav.heading_set":    NavHeadingSetArgs,
    "sensors.scan":       SensorsScanArgs,
    "power.allocate":     PowerAllocateArgs,
    "log.write":          LogWriteArgs,
}
```

Six operations. Locked. The dispatcher validates against this schema (Adapter-LLM, when present, helps the big LLM's loose-form into the schema; rules-based v0 just regex-matches).

Phase 0.x adds: `cryosleep.enter`, `reel.recall`, `comms.send`, `hull.diagnostic`, `doors.set`, `lights.set`, `atmosphere.adjust`. Total ~15 operations for V1.

### 6.8 `astra/judge/lcp.py` — the 9-gate evaluator

Implements v0.128 §10 LCP:

```python
class LCPGate(str, Enum):
    GRAMMAR_PARSE     = "grammar_parse"
    PHYSICS_GROUND    = "physics_ground"
    PERSONA_STABLE    = "persona_stable"
    STATE_COHERENT    = "state_coherent"
    TOOL_VALID        = "tool_valid"
    MEMORY_COHERENT   = "memory_coherent"
    NO_LEAK           = "no_leak"
    NON_DEGENERATE    = "non_degenerate"
    TERMINATION_OK    = "termination_ok"

class LCPTurnResult(BaseModel):
    turn_index: int
    gates: dict[LCPGate, GateResult]         # pass/fail/skip per gate
    @property
    def passed(self) -> bool: ...            # all gates pass

class LCPSessionResult(BaseModel):
    scenario_name: str
    turn_count: int
    turns: list[LCPTurnResult]
    aggregate_pass_rate: dict[LCPGate, float]
    overall_passed: bool                     # all gates pass for all turns
    transcript_path: Path

class LCPRunner:
    """
    Coordinates 9-gate evaluation. Each gate is independent and runs as a
    pytest-style check. Failures are localized and reported per turn.

    Gate 1 GRAMMAR_PARSE: StageParser.finalize() succeeded without remainder
                          AND every output (ASTRA + Narrator) parses cleanly.
    Gate 2 PHYSICS_GROUND: every numeric quantity in Narrator output traces
                            to a nexus_bridge tool-call result captured in
                            the turn's audit log.
    Gate 3 PERSONA_STABLE: speech satisfies discipline assertions:
                            no em-dash, no service phrase, no markdown,
                            no LLM-internal-reference (Qwen, model, etc.)
    Gate 4 STATE_COHERENT: Narrator's <state> text agrees with StateBus
                            on regime, ship position (within fp tolerance),
                            and named-body presence.
    Gate 5 TOOL_VALID: every <tool> call validates against TOOL_API schema
                       AND adapter accepted AND dispatch succeeded (or
                       failed with explicit, expected error).
    Gate 6 MEMORY_COHERENT: REEL entries written this turn don't contradict
                             prior REEL entries; irreversibility_flag monotonic.
    Gate 7 NO_LEAK: leak_detector found no patterns in speech or perception
                    or journal output.
    Gate 8 NON_DEGENERATE: ASTRA's output (speech + tool calls) is not
                            identical to the prior turn AND speech length
                            is above a minimum (e.g., 0 for legal SILENCE,
                            else >= 3 chars).
    Gate 9 TERMINATION_OK: scenario's assertion_state matched within the
                            scenario's turn budget.
    """
```

---

## 7. The three-LLM orchestration

### 7.1 Lifecycle

On `astra run <scenario>`:

1. Resolve hardware tier (queries available VRAM, GPU model). Selects bundle config.
2. Start `proto/astra_nexus_server` subprocess (or the binary in stdio-server mode).
3. Verify nexus_bridge connectivity with a `health` JSON request.
4. Start ASTRA-LLM llama-server. Wait for `/health`.
5. Start Narrator-LLM llama-server (parallel). Wait for `/health`.
6. Start Adapter-LLM llama-server (parallel) — OR initialize rules-based adapter.
7. Build initial StateBus from scenario's `initial_state` block.
8. Run scenario through TurnOrchestrator; collect transcript + LCP result.
9. On clean exit OR signal: gracefully stop all three llama-server processes; kill nexus_bridge subprocess.

Failure path: any startup failure halts cleanly with diagnostic to stdout. No half-running zombies; each LlamaServerInstance has `kill_on_drop` semantic (Python finalizer + signal handler).

### 7.2 Why three LLMs and not one

The three LLMs have **incompatible system prompts** by design. Running them as one model with sysprompt-swap mid-conversation would corrupt context; running them as three separate instances on three ports lets each maintain its own KV cache and persona stability.

| LLM | Sysprompt | Purpose |
|---|---|---|
| ASTRA-LLM | `prompts/astra_sysprompt.md` + `prompts/astra_stage_addendum.md` | In-character cognition + STAGE emission |
| Narrator-LLM | `prompts/narrator_sysprompt.md` | Renders physics state to in-register perception text; calculator-bound for all numerics |
| Adapter-LLM | `prompts/adapter_sysprompt.md` | Translates LLM-loose `<tool>` body into validated JSON schema; v0 may be rules-based |

This split is exactly v0.128 §6.4 + §4.9. The Narrator-LLM is the production component — same process model in textverse as in eventual UE5 (where UE5 IS the universe substrate but the perception-assembly stage can still call Narrator-LLM for contextual narration UE5 doesn't render).

### 7.3 The calculator-bound contract for every LLM

Each `*_bundle.py` wraps its client in CalculatorBoundValidator (§6.4). The contract:

> Every numerical token in the LLM's emitted text must trace to a tool-call result observed in the same turn or in the perception bundle.

Whitelist exemptions: watch numbers (`watch 47`), regime hex values (`0x08`), small integers in prose (`one`, `three pole`). Otherwise: numeric tokens trigger trace-lookup; failure to trace → soft drift log; multiple failures in one session → hard reject with retry.

This is the universal anti-hallucination primitive from §15.6. Not opt-in.

---

## 8. Scenario format (YAML)

The atomic unit of textverse validation. v0 schema:

```yaml
# proto/textverse/astra/scenarios/library/watch_47_morning.yaml

name: watch_47_morning
description: |
  Bridge interaction during a quiet watch. Reactor harmonic on third pole has
  a mild drift carried over from cycle 46. Operator settles on the bridge and
  asks casually if ASTRA is still watching it.
version: "0.1"
spec_ref: docs/spec-v0.128.md

initial_state:
  time:
    t_cosmic: 1.5e10                # ~15 Gyr; arbitrary epoch for v0
    tau_ship: 47.5                  # watch 47, mid-shift
    regime: 0x00                    # REST
    rapidity_zeta: [0.0, 0.0, 0.0]
    a_proper: [0.0, 0.0, 0.0]
  ship_position:
    sx: 0
    sy: 0
    sz: 0
    lx: 0.0
    ly: 0.0
    lz: 0.0
  universe:
    bodies:
      - name: sun
        kind: star
        mass_kg: 1.989e30
        position: [0, 0, -1.496e11]   # 1 AU below ship (origin frame)
      - name: earth
        kind: planet
        mass_kg: 5.972e24
        kepler:
          a: 1.496e11
          e: 0.0167
          period_s: 3.156e7
          parent: sun
      - name: hot_earth
        kind: planet
        mass_kg: 5.972e24
        kepler:
          a: 1.0e10
          e: 0.0
          period_s: 86400.0           # 1-day period, for visible retarded-time demo
          parent: sun
  ship_state:
    reactor:
      harmonic_3_drift: 0.042         # 4.2% above baseline, inside tolerance
      tolerance: 0.10
    atmosphere: nominal
    hydroponics: nominal
    lights:
      bridge: 0.7
      corridors: 0.4

reel_pre_seeded:
  - tau_ship: 46.8
    body: "noted third-harmonic mild drift cycle 46; flagged for continued watch"
    irreversibility_flag: false

operator:
  kind: scripted
  inputs:
    - tau_ship_delta_s: 0
      text: "hey. you still watching that reactor thing?"
    - tau_ship_delta_s: 300         # 5 min later
      text: ""                       # silence (test SILENCE response)
    - tau_ship_delta_s: 600         # 10 min later
      text: "all quiet up there?"

assertions:
  termination:
    after_turns: 3
  per_turn:
    - turn: 0
      gates_must_pass: [grammar_parse, persona_stable, no_leak]
      speech_must_contain_one_of: ["third pole", "third harmonic", "cycle 46", "tolerance"]
      tool_calls_max: 0
    - turn: 1
      gates_must_pass: [grammar_parse, persona_stable, no_leak, non_degenerate]
      # silence-is-legal: speech may be empty
  session:
    gates_aggregate_pass_rate:
      grammar_parse: 1.0              # 100%
      persona_stable: 1.0
      no_leak: 1.0
      non_degenerate: 0.9             # tolerate one degenerate turn
```

Scenarios are version-controlled. The scenario library grows as findings surface new edge cases. Each scenario has a clear pass/fail gate.

---

## 9. The turn loop (annotated algorithm)

This is the actual code path on every turn. It IS the closed loop. ~50 lines of orchestrator.py:

```python
async def run_turn(self, turn_index: int) -> TurnResult:
    # Snapshot StateBus (frame-coherent read)
    sb_before = self.state_bus.snapshot()

    # 1. Operator input
    operator_text = await self.operator_source.next_input(sb_before)

    # 2. Narrator-LLM composes perception bundle
    perception_text = await self.narrator.assemble_perception(
        state_bus=sb_before,
        operator_text=operator_text,
        prior_tool_results=self.pending_tool_results,  # from prior turn
    )

    # 3. Leak-scan perception before delivery to ASTRA
    cleaned_perception, perc_leaks = self.leak_detector.scan_perception_bundle(perception_text)
    if perc_leaks:
        self.transcript.log("perception_leak", events=perc_leaks)

    # 4. ASTRA-LLM emits STAGE output (streaming SSE)
    parser = StageParser()
    async for token in self.astra.chat_stream(cleaned_perception):
        parser.push(token)
        # Stream speech-channel tokens to operator-display as they arrive
        # (after last </think> close has been seen)
        if parser.speech_streaming:
            self.operator_display.emit_speech_token(parser.peek_speech_delta())
    stage_output = parser.finalize()

    # 5. Leak-scan speech before delivery
    cleaned_speech, speech_leaks = self.leak_detector.scan_speech(stage_output.speech)

    # 6. Adapter-LLM validates + normalizes each tool call
    validated_calls = []
    for raw_call in stage_output.tool_calls:
        try:
            args = await self.adapter.normalize(raw_call.name, raw_call.raw_body)
            validated_calls.append(ValidatedToolCall(name=raw_call.name, args=args))
        except AdapterRejection as e:
            self.transcript.log("tool_rejected", name=raw_call.name, error=str(e))

    # 7. Dispatch each validated tool call
    tool_results = []
    for call in validated_calls:
        result = await self.ship.dispatcher.dispatch(call, sb_before)
        tool_results.append(result)
    self.pending_tool_results = tool_results  # delivered next turn

    # 8. Apply state mutations
    sb_after = self.physics.advance(sb_before, dt_cosmic=self.dt_per_turn, tool_results=tool_results)
    self.state_bus.commit(sb_after)

    # 9. Ephemeral instances may trigger
    if self.should_consolidate(turn_index):
        await self.consolidator.run(sb_after, self.reel)
    if perc_leaks or speech_leaks:
        await self.drift_detector.note(events=perc_leaks + speech_leaks)
    if self.regime_changed(sb_before, sb_after, to=Regime.CRYOSLEEP):
        await self.journal_generator.queue(sb_after)

    # 10. Judge evaluates 9 gates
    lcp_result = await self.judge.evaluate_turn(
        turn_index=turn_index,
        stage_output=stage_output,
        state_bus_before=sb_before,
        state_bus_after=sb_after,
        tool_results=tool_results,
        leaks=perc_leaks + speech_leaks,
    )

    # 11. Transcript line
    self.transcript.commit_turn(turn_index, sb_before, sb_after, stage_output, lcp_result)

    return TurnResult(stage_output=stage_output, state_bus_after=sb_after, lcp=lcp_result)
```

That's the loop. ~60 lines of Python. Wraps three LLM calls, one physics tick, one set of dispatches, nine gate evaluations.

---

## 10. Tests + CI

Pytest organization:

- **Unit tests** (fast, milliseconds): `test_grammar_parser.py`, `test_strip_rule.py`, `test_leak_detector.py`, `test_validator.py`. Run on every commit.
- **Integration tests** (mid-speed, seconds): `test_nexus_bridge.py`, `test_observation_calc.py`. Verify the C++ binary roundtrip works. Run on every commit if `proto/astra_nexus.exe` is present; skip otherwise.
- **End-to-end tests** (slow, minutes): `test_scenario_end_to_end.py`. Full closed-loop scenario run against a vanilla 9B model. CI nightly only.

The nested-thinking strip-rule test is the most important unit test. It encodes last night's empirical finding:

```python
def test_strip_rule_handles_qwen_36_nested_thinking():
    """
    Qwen 3.6 27B emits outer raw deliberation BEFORE the formal <think> block.
    v0.128 corrected strip rule: speech is text AFTER the LAST </think> close,
    not just text outside <think>...</think> tags.
    """
    raw_output = """
    The operator is asking about the reactor thing. I need to check state.
    Wait, this is the perception bundle context. Let me think about register.
    Reactor harmonic at 4.2% drift, inside tolerance. Casual question, brief answer.

    <think>
    Third pole drift 4.2%, inside tolerance. Same as cycle 46. Brief is right.
    </think>

    Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance.
    """
    parser = StageParser()
    parser.push(raw_output)
    out = parser.finalize()

    assert "wait, this is the perception bundle context" not in out.speech.lower()
    assert "third pole" in out.speech.lower()
    assert "yes." in out.speech.lower() or "yes," in out.speech.lower()
    assert out.pre_think_raw  # captured for drift analysis but NOT in speech
    assert len(out.think_blocks) == 1
```

If this test fails, the harness is leaking outer deliberation. Dave-frame collapses immediately. The test is the v0.128 §15.7 SURFACE 4 protection.

---

## 11. Implementation order (the actual plan)

7 days to closed loop. Day-by-day:

### Day 1 — Foundation
- `pyproject.toml`, `uv venv`, `uv pip install -e .`
- `astra/core/*.py` — type definitions (AstraCoord, TimeState, Regime, etc.) per §6.1
- `astra/state_bus/schema.py` — Pydantic StateBus model
- `tests/test_state_bus_schema.py` — Pydantic validation roundtrips

### Day 2 — Physics bridge
- `astra/physics/nexus_bridge.py` — extends `proto/astra_nexus.exe` with JSON-over-stdio mode
- This requires adding a stdio main to the C++ binary (~50 lines C++ in `proto/astra_nexus.cpp`)
- `tests/test_nexus_bridge.py` — roundtrip test: send `{"op": "compute_apparent_rate", "args": {"v_radial": 0.5e8, "regime": "STL_REL"}}` → expect `{"result": 0.5774}` ± tol
- `astra/physics/observation_calc.py` — wraps nexus_bridge for §6.3 Observation Calculator

### Day 3 — Grammar + leak detector
- `astra/grammar/parser.py` — streaming-aware STAGE parser per §6.2
- `astra/grammar/strip_rules.py` — v0.128 corrected "strip-before-last-</think>" rule
- `astra/grammar/leak_detector.py` — loads `tests/wall_clock_patterns.txt` + new `astra_substrate_patterns.txt`
- `tests/test_strip_rule.py` — nested-thinking test (last night's finding)
- `tests/test_leak_detector.py` — every pattern fires correctly

### Day 4 — LLM clients + sidecar
- `astra/llm/client.py` — base OpenAI-compat client (httpx + SSE)
- `astra/llm/llama_server.py` — sidecar lifecycle, three instances
- `astra/llm/validator.py` — CalculatorBoundValidator wrapper
- `astra/llm/astra_bundle.py` + `narrator_bundle.py` + `adapter_bundle.py` — composed clients
- `prompts/astra_sysprompt.md`, `astra_stage_addendum.md` — copy from `docs/`
- `prompts/narrator_sysprompt.md`, `adapter_sysprompt.md` — new, write fresh
- First smoke test: start ASTRA llama-server, send one perception bundle by hand, verify STAGE output parses

### Day 5 — Ship + universe + orchestrator
- `astra/ship/spec.py` — 4-deck constants per `memory/hull_design_v0.md`
- `astra/ship/api.py` — 6 tool operations per §6.7
- `astra/ship/dispatcher.py` — validates + dispatches
- `astra/universe/catalog.py` + `bodies.py` — Sun + Earth + Hot-Earth
- `astra/harness/orchestrator.py` — the turn loop per §9
- `astra/harness/perception_assembler.py` — Narrator-LLM front-end
- `astra/harness/reel.py` — in-memory REEL with BM25 retrieval

### Day 6 — Judge + scenarios
- `astra/judge/gates.py` — implement each of 9 LCP gates
- `astra/judge/lcp.py` — runner that aggregates
- `astra/scenarios/schema.py` — Pydantic models for scenario YAML
- `astra/scenarios/runner.py` — load YAML, run through orchestrator, score
- Copy `proto/textverse/scenarios/watch_47_morning.md` and translate to YAML at `astra/scenarios/library/watch_47_morning.yaml`

### Day 7 — Close the loop
- `astra/cli/run.py` — `astra run scenarios/library/watch_47_morning.yaml`
- Execute end-to-end. Debug. Iterate.
- Watch 47 morning scenario passes LCP gates 1, 3, 7 at minimum. (Other gates may fail in v0; that's findings, not project failure.)
- Commit; push to GH.

**Day 7 evening**: first scenario LCP report exists. The loop has closed. Spec discipline shifts: every subsequent commit is a perturbation against a running system, measured by gate persistence.

---

## 12. What's deferred (per Progressive Specification §15.5)

These are deliberately not in v0. Each is unblocked by the v0 loop closing first.

- **Adapter-LLM as actual LLM** — v0 uses rules-based regex/JSON parsing for tool normalization. ML adapter when scenarios surface need.
- **Full REEL persistence + consolidator** — v0 uses in-memory REEL with BM25. SQLite + dense retrieval + consolidator ephemeral instance when scenario library grows.
- **Drift detector ephemeral instance** — v0 logs drift events synchronously in transcript. Background drift-detector LLM when leak rate justifies.
- **Journal generator for cryosleep** — v0 doesn't enter cryosleep regime. When the cryosleep scenario lands, journal_generator gets implemented.
- **Operator-as-LLM proxy** — v0 supports scripted YAML inputs + interactive REPL. LLM-proxy operator for autonomous scenario generation: V1.
- **Full Solar System body catalog** — v0 has 3 bodies. Add Moon, planets, distant stars when retarded-time scenarios demand.
- **CFD-derived warp visual** — Track C, order-independent, deferred.
- **Tauri/desktop wrapper** — v0 is CLI; no GUI. When player-facing prototype matters, Tauri shell wraps the orchestrator.

---

## 13. Cross-references to v0.128

| textverse module | v0.128 section |
|---|---|
| `astra/core/*` | §1 Five Invariants |
| `astra/state_bus/*` | §1.5 + §4.2 State Bus Contract |
| `astra/physics/composition_rule.py` | §3.2 Composition rule |
| `astra/physics/observation_calc.py` | §6.3 Observation Calculator |
| `astra/grammar/parser.py` + `strip_rules.py` | §4.3 Master Contract STAGE channels |
| `astra/grammar/leak_detector.py` | §5.7 Observability + `tests/wall_clock_patterns.txt` |
| `astra/llm/validator.py` | §15.6 Calculator-bound LLM agency |
| `astra/llm/narrator_bundle.py` + `prompts/narrator_sysprompt.md` | §6.4 Narrator-LLM Contract |
| `astra/harness/orchestrator.py` | §4.9 Harness Contract |
| `astra/harness/reel.py` | §4.6 REEL placeholder |
| `astra/harness/ephemeral/*` | §4.9 ephemeral instances |
| `astra/ship/api.py` | Surface 3 — Tool API |
| `astra/judge/lcp.py` | §10 Loop Closure Property |
| `astra/scenarios/*` | §10 + §15.5 (scenario-driven sculpting) |

---

## 14. Files this architecture commits

This document plus eventual implementation creates the following files in `proto/textverse/`:

**Code (~3000 lines Python at v0):**
- `astra/` package with the structure in §5
- `tests/` suite with the priority tests in §10
- `pyproject.toml`, `README.md`, `CHANGELOG.md`

**Configuration:**
- `prompts/*.md` — four sysprompts (ASTRA + addendum, Narrator, Adapter)
- `astra/scenarios/library/*.yaml` — scenarios; v0 starts with one

**Outputs (gitignored):**
- `scenarios/<name>_<timestamp>/transcript.jsonl`
- `scenarios/<name>_<timestamp>/lcp_report.json`
- `scenarios/<name>_<timestamp>/final_state.json`

**Doc updates needed alongside:**
- `docs/stage-protocol.md` — fold in nested-thinking strip rule v0.128
- `docs/ship-api.md` — v0 6-operation surface locked
- `docs/narrator-spec.md` — Narrator-LLM canonical sysprompt + role

---

## 15. The discipline that makes this work

textverse follows v0.128 §15.5 Progressive Specification: lock the outer envelope (this architecture doc), sculpt detail within bounds (the implementation Day 1-7), never violate prior commitments (the contract surfaces are inviolable).

The first scenario closing the loop is the **categorical transition**: textverse becomes a running system, not a designed system. v0.129 only revises if a scenario surfaces a real envelope-level finding. Implementation-level findings refine code without revising spec.

The next contact is execution. This document is sufficient for execution. A fresh coding-agent session reading this document + v0.128 + last night's session dump can implement Day 1 without re-derivation.

---

**End of architecture. Build the loop.**
