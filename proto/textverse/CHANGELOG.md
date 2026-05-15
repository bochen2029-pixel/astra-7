# textverse changelog

Per-day implementation entries. Each entry should include: what was built, what tests pass, any findings that affect the spec.

---

## Unreleased

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
