# textverse changelog

Per-day implementation entries. Each entry should include: what was built, what tests pass, any findings that affect the spec.

---

## Unreleased

### Day 3 — Grammar parser + leak detector (2026-05-15)

Lands STAGE channel parsing and defense-in-depth leak detection. The
load-bearing test is the v0.128 corrected strip rule: SPEECH is text
AFTER the LAST `</think>` close — the architectural fix for the Qwen 3.6
nested-thinking pattern surfaced on 2026-05-14.

What landed:

- `astra/grammar/strip_rules.py` — canonical regex constants (`THINK_RE`,
  `TOOL_RE`, `THINK_OPEN_RE`, `THINK_CLOSE_RE`) + helpers
  (`find_speech_start`, `count_think_open_close`, `has_unclosed_think`).
  Tests can verify strip mechanics independent of the parser surface.
- `astra/grammar/parser.py` — `StageParser` (buffered streaming via
  `push(token)` / `finalize()`), `StageOutput`, `ToolCall`, and the
  `parse_stage(raw) → StageOutput` pure function. Pre-think raw outer
  deliberation is captured to `pre_think_raw` and NEVER emitted.
- `astra/grammar/leak_detector.py` — `LeakDetector` with three boundary
  scans (perception / speech / journal), `LeakEvent` records, optional
  warn-vs-strip severity per pattern, custom-canon-dir for tests.
- `astra/grammar/canon/wall_clock_patterns.txt` — 20 patterns: ISO dates,
  HH:MM 24h, AM/PM, weekday + month names (with 'May' constrained to
  date-context to avoid modal-verb false positives), datetime keywords,
  AD/CE year heuristic.
- `astra/grammar/canon/astra_substrate_patterns.txt` — 35 patterns:
  model family names (Qwen, Llama, GPT, Claude, Anthropic, ...), substrate
  vocabulary (LLM, transformer, sysprompt, context window, ...), and
  service-interface stock phrases ('As an AI', 'I'm Claude', ...).

Tests:
- `tests/test_strip_rule.py` — 16 tests including the canonical
  `test_strip_rule_handles_qwen_36_nested_thinking` gate that verifies
  outer pre-think deliberation stays out of `speech` and lands in
  `pre_think_raw`. Plus mid-stream tag splits, case-insensitive matching,
  unclosed-think malformed-flag, multi-block speech-start, silence
  primitive, streaming one-char-at-a-time stress.
- `tests/test_grammar_parser.py` — 12 tests for tool-call JSON parsing,
  loose-body raw preservation for adapter normalization, tool calls
  inside `<think>` ignored (cognition not action), tool-without-speech
  is not silence (she's acting), StageOutput frozen, idempotent finalize.
- `tests/test_leak_detector.py` — 26 tests covering canon loading,
  custom-dir isolation, every pattern class fires (date, weekday, month,
  AM/PM, clock, datetime, year, Qwen, LLM, transformer, 'As an AI',
  Anthropic, Claude), boundary-specific scans (journal applies wall-clock
  only), event span/pattern preservation, warn-severity does not strip,
  and — critically — that the canonical watch_47_morning speech passes
  through with zero leak events (no false positives on legitimate
  in-fiction prose like 'morning', 'cycle', 'pole', 'drift').

**Day 3 gate:** ✓ The Qwen 3.6 nested-thinking test passes — outer
deliberation lands in `pre_think_raw`, never in `speech`. Defense-in-depth
holds at the SDK boundary.

Tooling:
- Hatchling default packaging ships `astra/grammar/canon/*.txt` in the
  wheel without explicit configuration (verified by `uv build --wheel`
  and inspecting the built artifact).

Gates:
- uv run pytest                    → 110 passed (37 D1 + 19 D2 + 54 D3)
- uv run ruff check astra/ tests/  → clean
- uv run mypy astra/               → clean (strict, 30 files)
- Wheel build inspection           → canon/*.txt present at install time

Design notes:
- Tool calls *inside* `<think>` blocks are intentionally ignored at parse
  time. Per spec §4.3, `<tool>` is the action channel; `<think>` is
  cognition. A reasoning model that "considers" a tool call inside
  `<think>` is reasoning, not invoking — the dispatcher must not fire.
- The buffered StageParser implementation is correct for mid-token tag
  splits because parsing happens once on the full accumulated buffer.
  Per-token speech-channel emission (live display) is deferred to Day 5
  when the orchestrator wires SSE; correctness is unaffected.
- Leak patterns use raw regex source for diagnostic clarity. The detector
  compiles them with IGNORECASE for defense-in-depth against loose-form
  model output.

**Status:** ready for Day 4 — LLM clients + sidecar. `astra/llm/`
(OpenAI-compat client, llama-server lifecycle, three-bundle composition,
CalculatorBoundValidator wrapper), `prompts/*.md` (canonical sysprompt
+ STAGE addendum + new Narrator + Adapter sysprompts).

---

### Day 2 — Physics bridge: JSON-over-stdio to astra_nexus (2026-05-15)

- `proto/astra_nexus.cpp` — purely additive `--stdio-server` mode (~210 lines):
  hand-rolled JSON parser (object/string/number, scientific notation, no
  external deps), regime-string dispatcher, response emitter. Activates
  ONLY on `--stdio-server` argv[1]; default invocation runs the existing
  test+demo unchanged. Existing 48 assertions still pass post-rebuild.
- Three ops in the v0 server: `health`, `version`, `compute_apparent_rate`.
- `astra/physics/nexus_bridge.py` — Python `NexusBridge` class with start/
  call/close lifecycle, `NexusResponse` Pydantic model, context-manager
  protocol, and a top-level `compute_apparent_rate(v_radial_m_s, regime)`
  convenience that auto-manages the bridge for one-shot use.
- `astra/physics/observation_calc.py` — §6.3 Observation Calculator entry
  point (Day 2 surface: re-exports `compute_apparent_rate`; Day 3+ adds
  body_state_at_t_emit, multi-body observe).
- `astra/physics/__init__.py` — wire public exports.
- `tests/test_nexus_bridge.py` — 19 tests under `requires_nexus` marker,
  auto-skipped when binary missing. Covers: health, version, the spec
  gate (β=0.5/STL_REL → √(1/3) ≈ 0.5774), blueshift, monotonicity of
  STL_REL (rate always > 0), WARP at 2c/c/10c/-2c (reverse playback,
  warp horizon, rewind), STL_REL vs WARP contrast, error paths (unknown
  op, unknown regime, missing required arg), lifecycle (must-start,
  missing-binary, double-start, close-idempotent, persistent across
  20 calls).

**Tests passing:** 56 total = 37 Day 1 + 19 Day 2. `uv run pytest`,
`uv run ruff check astra/ tests/`, `uv run mypy astra/` all clean.
`./astra_nexus.exe` (no args) still reports `SUMMARY: 48 passed, 0 failed`.

**Day 2 gate:** ✓ `compute_apparent_rate(v_radial=0.5c, regime="STL_REL")`
returns 0.5773502691896258 via JSON roundtrip — matches √(1/3) to float64
precision (1e-9 absolute tolerance).

**Design notes:**
- Wire format is line-delimited JSON, one request → one response. Single-
  threaded by design; the orchestrator (Day 5) manages bridge lifecycle
  per scenario. Tests open/close per-test for isolation.
- The JSON parser handles only what Day 2 needs: object, quoted string,
  number (incl. scientific notation), nested objects. No arrays, null,
  or booleans yet — Day N+ extends as ops require.
- `compute_apparent_rate` accepts a regime *string* at this entry, not the
  bitmask integer. Composition (e.g. STL_REL | GRAVITY_WELL) is not yet
  exposed; the spec's apparent-rate formula in §3.11 only depends on the
  propulsion regime, so v0 dispatches on propulsion alone.

**Status:** ready for Day 3 — Grammar parser + leak detector
(`astra/grammar/parser.py` with the v0.128 corrected strip rule:
SPEECH is text after the *last* `</think>` close; outer raw deliberation
goes to `pre_think_raw` and never emits).

---

### Day 1 — Foundation: core types + State Bus schema (2026-05-15)

- `astra/core/regime.py` — `Regime` IntFlag with locked hex values per spec §3.3
  (REST=0x00 through CRYOSLEEP=0x40, GRAVITY_WELL=0x20 as composable flag)
- `astra/core/astra_coord.py` — 128-bit composite position (§1.1), int64 sector
  + float64 local offset, with 500 km magnitude validator
- `astra/core/rapidity.py` — `OMEGA_MAX = 16.811` clamp constant + pure-math
  magnitude helper (§3.7)
- `astra/core/time_state.py` — two-clock split + rapidity_zeta + a_proper +
  regime bitmask (§1.2, §4.4); enforces clamp at construct time
- `astra/core/ship_kinematic.py` — derived state shape (γ, grav_factor,
  dilation_ratio, regime); Day 2 wires computation
- `astra/core/power.py` — locked SUBSYSTEMS tuple per §1.4
- `astra/core/hull_sdf.py` — provisional zone list; full SDF deferred to UE5
- `astra/state_bus/schema.py` — `StateBus`, `BHRecord`, `BodyState`,
  `KeplerianElements`, `CosmologicalParams`, `ChaosFieldSummary` (all frozen)
- `tests/fixtures/state_bus_watch_47_morning.yaml` — Day 1 fixture mirroring
  StateBus shape (full scenario YAML lands Day 6)
- `tests/test_state_bus_schema.py` — 34 tests covering construct/validate/
  reject/roundtrip/frozen/YAML-load semantics for every type
- `tests/test_scaffolding.py` — removed stale `# noqa: F401` directives
  (modern ruff doesn't fire F401 on plain `import x.y` side-effect imports)
- `pyproject.toml` — added `allowed-confusables = ["γ", "β", "ω", "ζ", "α",
  "τ", "λ", "Ω", "Φ", "χ", "−", "·", "×"]` so physics notation in
  docstrings/comments matches spec language

**Tests passing:** 37 (3 scaffolding + 34 Day 1). `uv run pytest`, `uv run
ruff check astra/ tests/`, `uv run mypy astra/` all clean.

**Day 1 gate:** ✓ `watch_47_morning` fixture YAML loads into a `StateBus`
Pydantic instance with regime=REST, τ_ship=47.5, three procedural bodies
present, power allocation summing to 1.0, flat ΛCDM verified.

**Spec finding (minor, no v0.129 needed):** ARCHITECTURE.md §6.1 sketch
nests `bh_list` inside `TimeState`, but v0.128 §4.2 lists `BHList` as a
sibling Layer 0 field of the State Bus. Resolved in favor of v0.128 (canon
over implementation sketch). `bh_list: list[BHRecord]` lives at `StateBus`
root level. This is a §6.1 typo/oversight, not a load-bearing contradiction.

**Status:** ready for Day 2 — Physics bridge (extend `proto/astra_nexus.cpp`
with `--stdio-server` mode + `astra/physics/nexus_bridge.py` + roundtrip
test confirming `compute_apparent_rate(v_radial=0.5c, regime=STL_REL)
≈ 0.5774`).

---

### Day 0 — Scaffolding (2026-05-15)

- `pyproject.toml` — Python 3.12 project, uv-managed, dependency set locked
- `README.md`, `STARTUP.md`, `CHANGELOG.md` — bootstrap docs
- `.gitignore` — Python project ignores + scenario output artifacts
- Empty `astra/` package skeleton matching `ARCHITECTURE.md` §5 layout
- `tests/conftest.py` + one sanity test confirming the package imports

**Status:** ready for Day 1 — Foundation (Pydantic types in `astra/core/` + `astra/state_bus/schema.py`).

---

## Template for future entries

### Day N — <topic> (YYYY-MM-DD)

- What was built (file paths + brief summary)
- Tests passing (count + key assertions)
- Spec findings (if any — flag for v0.129 amendment)
- Deferred items added to backlog
- Next day's blocker (if any)
