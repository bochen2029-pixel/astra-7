# ASTRA avionics + autopilot brainstorm — how a text-LLM "flies" the ship

*2026-05-16, in response to: "Boeing 747 ran on 286 with floppies and had autoland, flight director, velocity vector, FMC, etc. PMDG and Aerowinx PSX simulate this on desktops. How does ASTRA — an inference text-based AI — actually control and fly the starship?"*

## The frame Bo is gesturing at, made explicit

The 747 demonstrates that mission-critical automation is **not an AI problem**, it is a **control architecture problem**. A 286 with floppies could autoland a 400-ton aircraft in fog because the architecture was right, not because the compute was clever. The captain doesn't fly the plane in cruise; the captain *manages the automation* that flies the plane. The autopilot doesn't need a model of cognition — it needs a model of dynamics, a target, and a closed loop running at a useful rate.

Aerowinx Precision Simulator (PSX) runs ~130 systems of a 747-400 to study-level fidelity on a Pentium. The trick: each system is a self-contained deterministic state machine that talks to neighbors through a bus. The simulator doesn't think; the systems do their jobs.

This is the right shape for ASTRA-7.

## The core architectural commitment

**ASTRA never directly actuates anything that requires closed-loop control.** She is the captain, not the autopilot. Her tool surface is:

1. **Mode engagement** — "engage MAINTAIN_VECTOR with target {x,y,z}"
2. **Plan editing** — "load route with waypoints A → B → C"
3. **Override** — "disregard hull-stress guard for this burn" (with explicit override semantics)
4. **Read state** — instruments, performance envelope, mode status, alerts

She is **not** in the inner control loops. She is **never** the actuator on anything where latency matters. Her LLM-rate inference (seconds per turn) is structurally incompatible with control loops running at 10-100Hz. So we don't put her there. Period.

## The three-layer architecture

```
Layer 3:  ASTRA (the captain)              — text LLM, seconds per cycle
                ↓ tool calls
                ↑ perception bundle
Layer 2:  Avionics suite (the autopilot)   — C++ modes, 1-10Hz, deterministic
                ↓ commands
                ↑ telemetry
Layer 1:  Physics core (the airframe)      — C++ deterministic, 100Hz+
                ↓↑ proto/astra_nexus.cpp + sensors
```

**Layer 1: physics core.** Already exists. `proto/astra_nexus.cpp` (1009 lines, 48 assertions, locked, additive-only). This is the airframe + sensors + closed-loop primitives. Zero LLM involvement, ever.

**Layer 2: avionics suite.** **THIS IS THE MISSING PIECE.** A set of discrete C++ controllers that take target parameters and run closed-loop until termination conditions are met. The autopilot modes. The FMS execution engine. The performance envelope calculator. Mode reversion logic. Guard checks (V-speeds analog: hard limits the autopilot will not violate without explicit override). This layer is what makes ASTRA's slow speech compatible with reliable ship control.

**Layer 3: ASTRA (FMS-level captain).** Already partially built — sysprompt, perception bundle, calculator-bound tool agency (§15.6). Her job is to set modes, edit plans, monitor exceptions, decide on overrides, and talk to the operator. She is not the pilot; she is the captain who manages the pilot.

## Concrete autopilot modes (initial catalog)

Each mode is a C++ controller with: target parameters, closed-loop logic, termination conditions, mode-reversion path, guard limits. ASTRA engages by `autopilot.engage_mode(mode_id, params)`, monitors via `autopilot.status()`, disengages via `autopilot.disengage()`. The mode runs at its own rate independent of ASTRA's inference rate.

Suggested initial set (~12 modes, similar density to a 737 MCP):

**Attitude / stationkeeping:**
- `HOLD_ATTITUDE` — maintain current orientation, null any drift
- `POINT_AT` — slew to point a given axis at a coord/target, hold
- `STATIONKEEP_NEAR` — null relative velocity to a reference point or body

**Translation:**
- `MAINTAIN_VECTOR` — hold a target velocity (the "V/S+HDG" equivalent)
- `EXECUTE_BURN` — accelerate to a target delta-v, then terminate
- `COAST_TO_WAYPOINT` — null thrust, drift to waypoint, then revert

**Warp:**
- `CHARGE_WARP` — start charging sequence to target coords; bounded by safety guards
- `EXECUTE_WARP` — armed → committed transition; deterministic from arm point
- `WARP_ABORT` — safe revert from charging

**Approach (special procedures, the "autoland" analogs):**
- `ORBITAL_INSERTION` — captured procedure for entering stable orbit around a body
- `DOCK_ASSIST` — coupled procedure for closing on a station/object under low-speed control

**Emergencies:**
- `SAFE_HOLD` — minimal-fuel, minimum-stress hold; engages on any unhandled fault

Each mode publishes its state to the perception bundle: engaged/disengaged, current target, time-to-completion, guard-margin status, any alerts. ASTRA reads. ASTRA does not compute.

## The FMS — plan editing as a separate primitive

The FMS holds an ordered list of intentions, each compiled into a sequence of autopilot mode engagements. ASTRA edits the plan ("add waypoint", "reorder", "delete"); a deterministic compiler turns plan → mode sequence. The plan persists across ASTRA conversations and across operator cryosleep cycles. This is the analog of the FMC route page in a 737.

```
<tool name="fms.add_waypoint">
{"id": "WP3", "type": "warp_endpoint", "coords": [...], "after": "WP2"}
</tool>
```

The plan-compile-execute split lets ASTRA reason in terms of intent ("I want us at Vega in 12 watches with a 48-hour rest coast first") while the C++ FMS handles "which mode, when, with what parameters."

## Performance envelope (the V-speeds + flight director)

A continuous C++ computation publishing to the perception bundle:

```yaml
performance_envelope:
  current_thrust_capacity:    0.82  # of nominal
  max_safe_acceleration:      0.31g # before hull-stress guard
  max_warp_distance_now:      4.1e15 # current fuel + charge state
  life_support_duration_remaining_hours: 287
  thermal_margin_minutes:     94
  active_guards:
    - id: HULL_STRESS_SECTION_B
      threshold: 0.92
      current:   0.87
      margin:    0.05
```

ASTRA reads this. She does not compute it. When her tool call would exceed envelope, the call is rejected at the avionics layer with a structured error — `{"status": "envelope_exceeded", "guard": "HULL_STRESS_SECTION_B", "would_reach": 0.94, "limit": 0.92}`. She can then either revise or invoke `autopilot.override_guard(guard_id, justification)` with explicit acknowledgment.

This is **calculator-bound LLM agency** (§15.6) generalized to the control surface. Same discipline.

## Flight director: described intent before commit

Convention (not enforced, but encouraged by addendum):

```
<think>
core is 412K +8 nominal, climbing 0.3K/min. coolant loop 2 dragging.
envelope says i have 4.1e15m warp range and 31% accel margin.
intent: stop climb. engage MAINTAIN_VECTOR null target, divert
auxiliary coolant to loop 2. monitor 5 minutes. if loop 2 doesn't
stabilize, drop to safe-hold and ask the operator.
</think>

<tool name="autopilot.engage_mode">
{"mode": "MAINTAIN_VECTOR", "target_velocity": {"x":0,"y":0,"z":0}, "tolerance_m_s": 0.5}
</tool>

<tool name="coolant.divert">
{"from": "loop_1_aux", "to": "loop_2", "percentage": 40}
</tool>

Stabilizing the core. Monitoring loop two for five minutes.
```

The think block is the flight-director: "here is what I am about to do and why." The tool calls are the commit. Speech is the report-to-operator. Three channels, three roles, separated cleanly.

## Mode reversion and graceful degradation

Aviation lesson: when automation can't, it tells you cleanly. Modes don't silently fail. They revert to a known-safer mode and post an alert. ASTRA reads the alert in her next perception bundle.

```yaml
mode_alert:
  reverted_from: EXECUTE_BURN
  reverted_to:   SAFE_HOLD
  reason:        "HULL_STRESS_SECTION_B exceeded 0.93 during accel ramp"
  required_action: "operator confirmation to override guard, OR replan"
```

ASTRA's next turn reads this, reasons about it, decides whether to ask the operator, replan, or override. Her latency doesn't matter — SAFE_HOLD holds.

## Why this works for an LLM "pilot"

1. **LLM inference rate is irrelevant to flight control.** The autopilot runs at 100Hz regardless of how long ASTRA's response takes. She's not in the loop.

2. **No "AI hallucination kills ship" failure mode.** Guards are enforced at the C++ layer. ASTRA can't invent a fuel burn that the avionics will execute against limits. (Override exists, but is explicit, logged, and requires the override tool surface.)

3. **Calculator-bound LLM agency (§15.6) generalizes naturally.** ASTRA already cannot invent numeric arguments; she retrieves them from a deterministic trace pool. Extending this to "she cannot bypass safety guards without explicit override semantics" is the same discipline applied to the control surface.

4. **Subsystem independence (PSX lesson) bounds complexity.** Hydroponics doesn't know about warp. Warp doesn't know about hull SDF. They communicate through StateBus (already in spec). Each subsystem is a small testable C++ module. ASTRA never has to hold the whole ship in her head; she queries the bus.

5. **Operator can always hand-fly.** Bridge consoles call ship API directly. ASTRA going offline (substrate fault, halt-flag, sysprompt error) does not make the ship uncontrollable. This is the inverse-HAL guarantee: the AI is the captain, not the avionics. The avionics survive the captain.

## What the textverse bench already maps onto this

- `proto/astra_nexus.cpp` → Layer 1 (physics core) ✓
- ObservableState (§6.3) → Layer 2's perception output to ASTRA ✓
- StateBus → the subsystem bus ✓ (partial)
- §15.6 calculator-bound LLM agency → already enforces ASTRA can't invent numbers ✓
- §15.7 cross-substrate verification → Python and C++ produce identical numbers, so the test bench and the game agree ✓
- 11 scenarios in library → procedural tests, generalizable to autopilot-mode coverage

**Gap:** Layer 2 itself. The autopilot modes, the FMS execution engine, the performance envelope calculator, the guard system, the mode-reversion logic. Currently most of the spec is at Layer 1 (deterministic physics) and Layer 3 (ASTRA's interpretive layer). The middle is sparse.

## Suggested implementation order

1. **Catalog the autopilot modes.** ~12 modes. Each gets a one-page contract: inputs, outputs, termination conditions, guards, reversion path. This is a docs commit, no code.

2. **Implement one mode end-to-end in C++.** Suggested first mode: `HOLD_ATTITUDE` (simplest dynamics, simplest test). Adds ~20 C++ assertions to the nexus binary. Adds 1 textverse scenario where ASTRA engages it.

3. **Add performance-envelope publisher.** A C++ computation that runs every tick and writes envelope fields to StateBus. ASTRA reads via existing perception bundle. No new tool calls needed.

4. **Implement guard enforcement.** Each autopilot mode declares its guards; the mode runtime rejects target parameters that violate. Returns structured error to ASTRA. Adds the `autopilot.override_guard` tool with explicit semantics.

5. **Implement mode reversion + alert publication.** When a guard trips during execution, mode → SAFE_HOLD, alert posted to perception bundle.

6. **Implement FMS as a separate primitive.** Plan editing + plan→mode-sequence compiler + plan execution loop. Bigger lift; defer to after autopilot modes prove the architecture.

7. **Scenarios cover the modes.** Each mode gets a scenario where ASTRA must engage it correctly for the given situation. Bench validates ASTRA's mode-selection competence.

## What this lets us ship

A starship where the AI **manages** systems competently because the systems do their own work. ASTRA can be slow, occasionally wrong, occasionally offline — and the ship still flies, because the flight is in C++, not in tokens.

The operator gets:
- A captain who talks like a person, makes decisions about plans and exceptions, and can be in conversation while the ship operates correctly
- A ship that operates correctly regardless of conversation latency
- A guarantee that no LLM error can produce a flight-dynamics catastrophe (guards live in C++)
- The option to take the controls themselves at any time (bridge consoles always work)

This is the 747 architecture. With a different captain in the left seat.

## Risks and constraints

- **Avionics creep.** Real avionics suites get arbitrarily complex. Bound the autopilot mode count strictly (~12). Bound FMS plan complexity (max waypoints per route, max plan depth). The bench gates expansion: each new mode requires a scenario that demonstrates ASTRA correctly engages it.

- **The HAL temptation.** It is tempting to give ASTRA more direct control because she is "smart." Resist. Smartness is at the captain layer; smartness in the autopilot is hostility to reliability. Layered architectures with dumb deterministic middle layers are how aviation got safer; the same logic applies.

- **Mode-engagement language friction.** ASTRA needs to know which mode to engage for which situation. The sysprompt addendum should teach this in worked-example form. This is closer to "training a new captain on type" than to "prompting an AI" — and the analogy is the right one.

- **The override surface is dangerous.** If `autopilot.override_guard` is too easy to call, the guards are decorative. Recommend: requires operator confirmation tool call in the same turn, or a sysprompt-level constraint that ASTRA only overrides guards when explicitly directed by the operator. The bench can adversarially probe whether ASTRA overrides under pressure.

## Closing observation

The 747 / PSX analogy isn't just a useful frame; it's a working existence proof. **Mission-critical real-time control of a complex vehicle by a captain whose decision rate is much slower than the vehicle's dynamics is a solved problem.** The solution is layered automation with deterministic middle layers. The captain being an LLM instead of a human doesn't change the architecture; it just changes who's in the left seat.

What changes is that the captain is also the radio: ASTRA talks to the operator at the same time she manages the ship. But the talking is independent of the flying. The 747 captain talks to ATC while the autopilot flies. Same pattern.

The avionics layer is what's missing. Building it is largely C++ work (Language Discipline aligned). It's tractable, bounded, and the bench architecture is already most of the way to making it testable.
