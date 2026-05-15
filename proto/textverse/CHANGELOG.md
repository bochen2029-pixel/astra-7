# textverse changelog

Per-day implementation entries. Each entry should include: what was built, what tests pass, any findings that affect the spec.

---

## Unreleased

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
