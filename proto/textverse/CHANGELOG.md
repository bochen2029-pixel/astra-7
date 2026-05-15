# textverse changelog

Per-day implementation entries. Each entry should include: what was built, what tests pass, any findings that affect the spec.

---

## Unreleased

### Day 4.1 — Substrate-portability fix from live smoke test (2026-05-15)

First live smoke test surfaced a real finding. Per §15.4 ("revise only
on adversarial-finding-justified loop measurement"), this is exactly
the kind of measurement that justifies a contained change.

The finding:
- Vanilla Qwen 3.5 9B Q5_K_M + canonical sysprompt + STAGE addendum
  produced excellent speech-channel output on the first attempt:
  brief, no em-dashes, no service phrases, referenced specific sensor
  detail (4.2%, cycle 46, third harmonic, tolerance). All 8 hard-pass
  criteria from watch_47_morning.md met.
- BUT no `<think>` block appeared in the output. Surface 4 register
  check (smoke test) initially failed.
- Root cause: llama-server's `--reasoning-format` defaults to
  extracting reasoning into a separate `reasoning_content` response
  field; `message.content` contained only the speech. The STAGE parser
  saw no `<think>` because there was no `<think>` inline to find.

The fix (substrate-portability normalizer in client.py):
- `LLMClient.chat_complete` now reads BOTH `content` and
  `reasoning_content`. If `reasoning_content` is non-empty, the client
  synthesizes canonical inline `<think>{reasoning}</think>` and
  prepends it to content before returning.
- This keeps the harness substrate-portable: deepseek-r1 (inline
  `<think>` native), Qwen 3.x (extracted reasoning_content), and any
  future model with its own convention all produce the same shape for
  the STAGE parser. The parser doesn't change; the boundary absorbs
  the variance.
- 3 new tests in test_llm_client.py: normalize-reasoning-into-inline,
  pass-content-through-when-no-reasoning, ignore-empty-reasoning.

Deployment recipe (documented in docs/BUILD_NOTES.md):
- Required flags for Qwen 3.x:
    --jinja
    --reasoning on
    --reasoning-format deepseek-legacy
    --chat-template-kwargs "{\"enable_thinking\":true}"
- With this invocation, vanilla 9B produces watch_47_morning-conformant
  output single-shot at temperature 0.7.

Files touched:
- astra/llm/client.py            — normalizer in chat_complete
- tests/test_llm_client.py       — 3 new tests (now 14 total)
- docs/BUILD_NOTES.md            — NEW: empirical deployment recipe

Gates:
- uv run pytest                  → 184 passed (was 181)
- uv run ruff check              → clean
- uv run mypy astra/             → clean (36 files)
- Live smoke test PASS: <think> + speech + no leaks at temp=0.7

This is the empirical loop closing the architecture-hypothesis gap for
Surface 4 (STAGE protocol) at the LLM I/O boundary. The next contact
points are Day 5 (orchestrator + ship + universe) → Day 6 (judge + LCP)
→ Day 7 (first scenario closing all 9 gates).

---

### Day 4 — LLM clients + sidecar + validator + prompts (2026-05-15)

Lands Surface 1 (substrate-portable LLM client) and the three bundle
compositions (ASTRA / Narrator / Adapter) plus the calculator-bound
validator that enforces §15.6 at the SDK boundary. Operator-runnable
smoke test included for the Day 4 spec gate.

What landed:

Prompts (proto/textverse/prompts/):
- `astra_sysprompt.md` — copy of docs/astra-sysprompt.md (canon; DO NOT
  modify in the prompts/ copy).
- `astra_stage_addendum.md` — copy of docs/astra-sysprompt-addendum-stage.md.
- `narrator_sysprompt.md` — NEW: calculator-bound perception renderer
  per §6.4. Composes four-section bundles (`<state>`, `<somatic>`,
  `<recent>`, `<operator>`) in ASTRA-compatible voice. Locked
  discipline: every numeric traces to a tool result.
- `adapter_sysprompt.md` — NEW: loose-form `<tool>` body → validated
  JSON normalizer per §4.9. Emits one `{"ok": bool, "args"|"error": ...}`
  object and stops.

astra/llm/:
- `client.py` — `LLMClient` (async OpenAI-compat HTTP+SSE via httpx +
  httpx_sse), `ChatMessage`, `SamplingParams`, `LLMClientError`,
  `health()` probe. Streaming yields delta tokens; bad SSE chunks
  are skipped not crashed-on.
- `llama_server.py` — `LlamaServerConfig`, `LlamaServerInstance` (one
  subprocess per port with /health polling for startup), and
  `LlamaServerOrchestrator` (multi-instance start/stop with roll-back
  on partial failure). Default binary `C:\\llama.cpp\\llama-server.exe`,
  override via `LLAMA_SERVER_BIN` env or constructor.
- `validator.py` — `CalculatorBoundValidator` per §15.6:
  `find_ungrounded_numerics(speech, trace_pool)` scans digit tokens
  in speech that don't appear in the tool-result trace pool. Whitelist
  covers watch numbers, cycle numbers, deck numbers, regime hex
  values, ASTRA designation. `next_temperature(current, retry_count)`
  halves on each retry with a floor of 0.05.
- `astra_bundle.py` — `AstraBundle` composing client + sysprompt
  (canon + STAGE addendum concatenated) + soft-severity validator
  + StageParser integration via `turn(perception_bundle)`.
- `narrator_bundle.py` — `NarratorBundle` with lower temperature
  default (0.4) and HARD-severity validator (Narrator output is
  ASTRA's trace pool; ungrounded numerics here are the worst leak).
- `adapter_bundle.py` — `AdapterBundle` (LLM-backed) AND
  `RulesBasedAdapter` (pure-Python JSON/key=value parser). v0 may
  use the rules-based path on lower-tier hardware; the orchestrator
  picks based on hardware tier (Day 5).

Tests (71 new):
- `test_llm_client.py` (10 tests) — httpx MockTransport verifies
  request shape, response parsing, SSE streaming, [DONE] terminator,
  malformed-chunk-skipping, health probe, error path.
- `test_validator.py` (22 tests) — every whitelist class, decimal /
  scientific-notation / negative grounding, multi-ungrounded
  reporting, spans, retry policy halving + 0.05 floor, severity
  propagation.
- `test_llama_server.py` (12 tests) — config shape + frozen, argv
  construction with kwargs and extra args, base_url format, custom
  host, default constants, failure paths (binary missing, model
  missing), idempotent stop, orchestrator empty rejection, orchestrator
  rollback on partial start failure.
- `test_bundles.py` (15 tests) — prompt loading from package data,
  default sampling per bundle, RulesBasedAdapter covering pure JSON,
  key=value, colon separator, quoted string values, boolean/integer
  coercion, empty/unparseable rejection, AdapterBundle prompt
  construction.

scripts/smoke_astra_bundle.py:
- Operator-runnable Day 4 gate. Hits a live llama-server at
  http://127.0.0.1:8080 with the canonical watch_47_morning perception
  bundle, parses STAGE output, runs the leak detector, prints results.
  Returns exit code 0 on pass (think block present, speech non-empty
  or tool call, not malformed). Documents the llama-server startup
  invocation in the docstring. CI does NOT run this — it requires the
  operator to have a Qwen 3.x GGUF on disk and llama-server running.

Tooling:
- `tests/test_scaffolding.py` — extended the no-wall-clock-imports
  exemption list to include `astra/llm/llama_server.py` (uses
  `time.monotonic()` / `time.sleep()` for subprocess /health polling,
  which is infrastructure, not fictional-time computation).

Gates:
- uv run pytest                    → 181 passed (37 D1 + 19 D2 + 54 D3 + 71 D4)
- uv run ruff check astra/ tests/ scripts/ → clean
- uv run mypy astra/               → clean (strict, 36 files)
- Smoke script imports cleanly; runs against any reachable
  llama-server with the documented startup invocation.

**Day 4 gate (manual):** ✓ The operator-runnable smoke test
documented in scripts/smoke_astra_bundle.py. Live verification
deferred to the operator's hardware (requires Qwen 3.x GGUF on
disk and llama-server reachable on port 8080).

Design notes:
- Per-bundle sampling defaults reflect role: ASTRA at 0.7
  (in-character cognition), Narrator at 0.4 (rendering, not
  improvising), Adapter at 0.1 (deterministic-ish JSON emission).
- The rules-based adapter handles the v0 cases (pure JSON,
  key=value, key: value, quoted strings, bool/int coercion). The
  LLM-backed adapter is wired but only activates when scenarios
  surface ambiguity the rules can't resolve.
- The CalculatorBoundValidator stops at finding ungrounded numerics;
  it doesn't reject the speech itself. The orchestrator (Day 5)
  decides retry vs LCP-fail-gate-2 based on report.severity +
  retry_count.
- LlamaServerInstance uses `subprocess.DEVNULL` for stdout/stderr.
  llama-server's own logging is verbose; capturing it would either
  inflate memory or require a thread. Day N+ may add a log-tee mode
  for debugging.

Spec finding (none): Day 4 found no v0.128 contradictions.

**Status:** ready for Day 5 — Ship + universe + orchestrator.
`astra/ship/` (4-deck spec + 6 tool API ops + dispatcher),
`astra/universe/` (Sun + Earth + Hot-Earth catalog), `astra/harness/`
(turn loop + perception assembler + REEL).

---

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
