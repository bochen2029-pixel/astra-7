"""Turn orchestrator per spec v0.129 §4.9 + ARCHITECTURE.md §9.

One turn = one operator input + one ASTRA response + state mutations.
The orchestrator coordinates: assemble perception → leak-scan → ASTRA
turn → parse STAGE → leak-scan speech → dispatch tool calls → record
trace pool → validate numerics → commit state diff → write REEL.

Day 5 v0:
- Template-based perception assembler (Narrator LLM is wired but not
  required for first scenario).
- AdapterBundle is wired but defaults to RulesBasedAdapter (no LLM
  call for tool normalization in v0).
- Calculator-bound validation runs but logs ungrounded events; soft
  severity by default (orchestrator does NOT retry yet — that's
  Day 6+ when the LCP gate-fail policy lands).
- State diffs from dispatcher are returned but not applied to the
  StateBus snapshot (Day 6+ wires physics tick).

The contract surface is intentionally simple: `Orchestrator.run_turn(
operator_text) -> TurnResult`. Day 6+ extends with REEL consolidation,
ephemeral-instance triggers, regime change handling, etc.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from astra.grammar import LeakDetector, LeakEvent, StageOutput, parse_stage
from astra.harness.perception_assembler import (
    assemble_perception_bundle,
    assemble_perception_bundle_via_narrator,
    render_status_report,
    render_tool_results,
)
from astra.harness.reel import Reel, ReelEntry
from astra.harness.savefile import ConversationTurn
from astra.harness.trace import SessionTrace, text_sha256
from astra.llm.adapter_bundle import ResolvedCall, RulesBasedAdapter
from astra.llm.astra_bundle import AstraBundle
from astra.llm.narrator_bundle import NarratorBundle, NarratorValidationError
from astra.llm.validator import CalculatorBoundValidator, ValidationReport
from astra.ship.api import ToolResult
from astra.ship.dispatcher import dispatch as dispatch_tool
from astra.state_bus import StateBus
from astra.state_bus.advance import advance_state_bus

# NOTE: astra.harness.ephemeral.{consolidator,drift_detector} are imported
# lazily inside run_turn — the ephemeral package pulls astra.judge.gates
# (for the persona-discipline canon constants), and judge.gates imports
# TurnResult from this module. Function-level import breaks the cycle;
# by the time a heartbeat fires, everything is loaded.

# §4.3.1 scheduling knobs (spec-v0.130-DRAFT §2.6; all provisional [chosen],
# tuned against bench measurement, never against speculation):
# - consolidation fires on a heartbeat once this many un-consolidated
#   conversation turns have accumulated (the §4.9 maintenance window);
# - initiative (speech on a heartbeat) is budgeted per fictional-time
#   window — exceeding the budget is FLAGGED and logged, never suppressed
#   (suppression would be a persona intervention; measurement comes first);
# - the drift detector reads this many recent conversation turns.
CONSOLIDATE_MIN_WINDOW_TURNS: int = 6
INITIATIVE_MAX_PER_WINDOW: int = 2
INITIATIVE_WINDOW_TAU_S: float = 3600.0
DRIFT_CHECK_RECENT_TURNS: int = 8


@dataclass(slots=True)
class TurnResult:
    """Everything one turn produced. Logged to transcript by Day 6 judge."""

    turn_index: int
    perception_bundle: str
    perception_leaks: list[LeakEvent]
    raw_llm_output: str
    stage_output: StageOutput
    speech_leaks: list[LeakEvent]
    tool_results: list[ToolResult] = field(default_factory=list)
    validation: ValidationReport | None = None
    state_diffs: list[dict[str, object]] = field(default_factory=list)
    reel_writes: list[ReelEntry] = field(default_factory=list)
    # T2.3 (2026-05-16): when narrator_bundle is wired, narrator_validation
    # records the auto-validator outcome on the perception bundle itself.
    # None on the template path. Failure mode (exhausted retries) raises
    # NarratorValidationError before this field is populated; orchestrator
    # falls back to the template path in that case and sets
    # narrator_fallback_reason to the exception message.
    narrator_validation: ValidationReport | None = None
    narrator_fallback_reason: str = ""
    # §4.3.1 (spec-v0.130-DRAFT §2.6) event-log fields:
    # turn_kind: "operator" | "heartbeat". interrupted: this turn's
    # generation was cancelled fail-closed (nothing delivered, nothing
    # dispatched); the raw output is retained in interrupted_forensics
    # like pre_think_raw — forensic, never emitted. initiative: speech on
    # a heartbeat turn (she originated). The budget flag records
    # exceedance; it never suppresses. ephemeral_runs: §4.9 maintenance
    # work that rode this heartbeat (QCR-14 closure).
    turn_kind: str = "operator"
    interrupted: bool = False
    interrupted_forensics: str = ""
    initiative: bool = False
    initiative_budget_exceeded: bool = False
    ephemeral_runs: list[str] = field(default_factory=list)
    # §6.3 adapter intent→op normalizations this turn ("emitted -> canon
    # (how)"); event-log data — the mapping rate is a measurable.
    adapter_mappings: list[str] = field(default_factory=list)


class TurnOrchestrator:
    """The closed loop. One operator input → one ASTRA response → diffs.

    Day 5 v0 turn loop:
      1. assemble perception bundle from StateBus + REEL + operator input
      2. leak-scan perception before delivery
      3. send to ASTRA-LLM (via AstraBundle)
      4. parse STAGE output (think + tool + speech + silence)
      5. leak-scan speech
      6. normalize each tool call through the rules-based adapter
      7. dispatch validated tool calls; record ToolResults
      8. validate numerics in speech against trace pool (perception + tool results)
      9. (Day 6+) commit state diffs, advance physics tick

    The orchestrator holds:
      - one StateBus snapshot (read-only for this turn)
      - one REEL (in-memory, mutable across turns)
      - one AstraBundle (LLM client + sysprompt)
      - one CalculatorBoundValidator
      - one LeakDetector loaded from canon
      - one RulesBasedAdapter (or wired AdapterBundle for Day N+)
    """

    def __init__(
        self,
        *,
        state_bus: StateBus,
        astra_bundle: AstraBundle,
        reel: Reel | None = None,
        validator: CalculatorBoundValidator | None = None,
        leak_detector: LeakDetector | None = None,
        adapter: RulesBasedAdapter | None = None,
        narrator_bundle: NarratorBundle | None = None,
        trace: SessionTrace | None = None,
    ) -> None:
        self.state_bus = state_bus
        self.astra_bundle = astra_bundle
        self.reel = reel or Reel()
        self.validator = validator or CalculatorBoundValidator(severity="soft")
        self.leak_detector = leak_detector or LeakDetector.from_default_canon()
        self.adapter = adapter or RulesBasedAdapter()
        # §5.3 trace column (spec-v0.130-DRAFT §2.4): when provided, the
        # orchestrator receipts every oracle event — operator inputs and
        # LLM utterances verbatim at generation, with the context hash
        # that Model-Off Replay later verifies. The rest of TurnResult is
        # the event-log column (derived, recomputed on replay).
        self.trace = trace
        # T2.3 (2026-05-16): when narrator_bundle is wired, step 1 of the
        # turn loop routes through the LLM-based perception assembler
        # with calculator-bound auto-validation. Falls back to the
        # template path on NarratorValidationError (exhausted retries).
        self.narrator_bundle = narrator_bundle
        self._turn_index: int = 0
        # §4.3.1 scheduling state (spec-v0.130-DRAFT §2.6): the
        # conversation buffer feeds the §4.9 ephemerals their windows; the
        # watermark tracks what the consolidator has absorbed; leak events
        # accumulate toward the next heartbeat's drift check; initiations
        # are tracked in τ_ship for the budget window; a pending
        # interruption note surfaces as state in the NEXT turn's
        # perception.
        self._conversation: list[ConversationTurn] = []
        self._consolidated_upto: int = 0
        self._leaks_since_drift_check: int = 0
        self._initiations_tau: list[float] = []
        self._pending_interruption_note: bool = False
        # Tool-result feedback leg (wired with R-A, 2026-07-19): results of
        # turn N's dispatches — including guided rejections — are delivered
        # as `<tool_result>` sections in turn N+1's perception, per the
        # STAGE addendum's documented input shape. Before this, the claim
        # existed only in comments; status.query made it load-bearing.
        self._pending_tool_results: list[ToolResult] = []

    def advance_time(self, delta_tau_s: float) -> None:
        """Advance the held snapshot's clocks by a τ_ship delta (§4.3.1).

        The snapshot itself stays frozen; the orchestrator's pointer moves
        to the new one (turn-to-turn progression, per §1.5).
        """
        self.state_bus = advance_state_bus(self.state_bus, delta_tau_s)

    async def run_turn(
        self,
        operator_text: str = "",
        somatic_note: str | None = None,
        *,
        turn_kind: Literal["operator", "heartbeat"] = "operator",
        interrupted: bool = False,
    ) -> TurnResult:
        """One turn end-to-end. Returns TurnResult; mutations applied to REEL.

        §4.3.1: a `heartbeat` turn is harness-originated (τ advanced past a
        tick with no operator input; `operator_text` must be empty; SILENCE
        is the expected response for most heartbeats; speech on a heartbeat
        is an initiation). `interrupted=True` marks this turn's generation
        as cancelled fail-closed: the LLM is still called (and its
        utterance receipted in the trace — it happened), but nothing is
        delivered, no tool dispatches, no REEL write; the raw output is
        retained as forensics and the next turn's perception carries the
        interruption as state.
        """
        if turn_kind == "heartbeat" and operator_text:
            raise ValueError(
                "heartbeat turns carry no operator text (§4.3.1: the "
                "<operator> section is empty on a heartbeat)"
            )
        if self._pending_interruption_note:
            note = (
                "speech output interrupted mid-emission by incoming operator "
                "audio; that response was not delivered"
            )
            somatic_note = f"{somatic_note}; {note}" if somatic_note else note
            self._pending_interruption_note = False

        # 1. Assemble perception — Narrator path if wired (with calculator-
        # bound auto-validation), template path otherwise. On Narrator
        # validation failure (exhausted retries), fall back to template
        # and record the reason on TurnResult for forensics. Pending tool
        # results from the previous turn are delivered exactly once (an
        # interrupted turn still delivered them — its perception was real
        # and receipted).
        retrievals = self.reel.search(operator_text or "watch reactor", k=3)
        pending_results = self._pending_tool_results
        self._pending_tool_results = []
        narrator_validation: ValidationReport | None = None
        narrator_fallback_reason: str = ""
        if self.narrator_bundle is not None:
            try:
                perception = await assemble_perception_bundle_via_narrator(
                    state_bus=self.state_bus,
                    narrator_bundle=self.narrator_bundle,
                    operator_text=operator_text,
                    reel_retrievals=retrievals,
                    somatic_note=somatic_note,
                )
                # Tool results are harness data, not narrative — the
                # Narrator never rewords them. Appended deterministically
                # after composition (template path renders them in
                # canonical position inside the assembler).
                if pending_results:
                    perception = (
                        f"{perception}\n\n{render_tool_results(pending_results)}"
                    )
                # On success, the bundle was validated against trace pool
                # inside narrator_bundle.compose(). Construct a synthetic
                # passed ValidationReport for the TurnResult.
                narrator_validation = ValidationReport(
                    ungrounded=[],
                    grounded=[],
                    severity=self.narrator_bundle.validator.severity,
                )
            except NarratorValidationError as exc:
                # Hard-failure path: log + fall back to template assembler.
                narrator_validation = exc.report
                narrator_fallback_reason = str(exc)
                perception = assemble_perception_bundle(
                    state_bus=self.state_bus,
                    operator_text=operator_text,
                    reel_retrievals=retrievals,
                    somatic_note=somatic_note,
                    tool_results=pending_results,
                )
        else:
            perception = assemble_perception_bundle(
                state_bus=self.state_bus,
                operator_text=operator_text,
                reel_retrievals=retrievals,
                somatic_note=somatic_note,
                tool_results=pending_results,
            )

        # 2. Leak-scan perception before delivery
        cleaned_perception, perception_leaks = self.leak_detector.scan_perception_bundle(
            perception,
        )

        # 3. Send to ASTRA-LLM
        if self.trace is not None:
            self.trace.record_operator(self._turn_index, operator_text)
        raw = await self.astra_bundle.client.chat_complete(
            cleaned_perception, self.astra_bundle.sampling,
        )
        if self.trace is not None:
            self.trace.record_utterance(
                self._turn_index,
                role="astra",
                payload=raw,
                context=cleaned_perception,
                model_id=self.astra_bundle.client.model_name,
                params_fingerprint=text_sha256(
                    json.dumps(
                        self.astra_bundle.sampling.model_dump(), sort_keys=True,
                    ),
                ),
            )

        # 4. Parse STAGE channels
        stage = parse_stage(raw)

        # §4.3.1 interruption: fail-closed. The parsed output is never
        # delivered — no speech emission, no tool dispatch, no REEL write,
        # no conversation append for ASTRA's side. The raw output is
        # retained as forensics (the pre_think_raw pattern); an interrupted
        # half-thought never half-executes. The operator's words WERE
        # heard, so they enter the conversation buffer; the next turn's
        # perception carries the interruption as state.
        if interrupted:
            if operator_text:
                self._conversation.append(
                    ConversationTurn(
                        role="operator",
                        text=operator_text,
                        tau_ship=self.state_bus.time.tau_ship,
                    ),
                )
            self._pending_interruption_note = True
            self._turn_index += 1
            return TurnResult(
                turn_index=self._turn_index - 1,
                perception_bundle=cleaned_perception,
                perception_leaks=perception_leaks,
                raw_llm_output=raw,
                stage_output=parse_stage(""),
                speech_leaks=[],
                narrator_validation=narrator_validation,
                narrator_fallback_reason=narrator_fallback_reason,
                turn_kind=turn_kind,
                interrupted=True,
                interrupted_forensics=raw,
            )

        # 5. Leak-scan speech. The cleaned perception grounds the scan:
        # a match already present in the (itself pre-scanned) perception
        # is the harness's own content echoed back, not a new leak (live
        # τ-collision finding, 2026-07-19).
        cleaned_speech, speech_leaks = self.leak_detector.scan_speech(
            stage.speech, grounding_text=cleaned_perception,
        )
        # If the leak scan modified speech, build a new StageOutput with the
        # cleaned version so downstream callers see the post-strip text.
        if cleaned_speech != stage.speech:
            stage = stage.model_copy(update={"speech": cleaned_speech})

        # 6 + 7. Adapt and dispatch each tool call. EVERY call routes
        # through the adapter (§4.9 invariant closure, 2026-07-19: the
        # prior JSON-args fast path bypassed it, so the live pass's
        # invented op names never met the entity whose job they are —
        # F-LIVE-1). The adapter resolves intent→canon-op, salvages args,
        # and rejects unmappable intents with guidance the model receives
        # as next turn's <tool_result>.
        tool_results: list[ToolResult] = []
        state_diffs: list[dict[str, object]] = []
        adapter_mappings: list[str] = []
        for tc in stage.tool_calls:
            resolved: ResolvedCall = self.adapter.adapt(
                tc.name, tc.arguments, tc.raw_body,
            )
            if not resolved.ok:
                tool_results.append(
                    ToolResult(op=tc.name, ok=False, error=resolved.error),
                )
                continue
            if resolved.mapped_from:
                adapter_mappings.append(
                    f"{resolved.mapped_from} -> {resolved.op} ({resolved.how})",
                )
            result = dispatch_tool(resolved.op, resolved.args)
            # Read fulfilment (R-A, v0.130): the orchestrator holds the
            # live snapshot, so the read happens here, template-rendered
            # from bus truth (calculator-bound by construction). Effectors
            # are untouched; status.query mutates nothing (its state_diff
            # is empty by dispatcher contract).
            if result.ok and result.op == "status.query":
                subsystem = str(result.args.get("subsystem", "all"))
                result = result.model_copy(
                    update={
                        "result": {
                            "report": render_status_report(
                                self.state_bus, subsystem,
                            ),
                        },
                    },
                )
            tool_results.append(result)
            if result.ok and result.state_diff:
                state_diffs.append(result.state_diff)

        # 8. Calculator-bound validation: trace pool = perception + tool result text
        trace_pool: list[str] = [cleaned_perception]
        trace_pool.extend(
            json.dumps(r.args) for r in tool_results if r.ok
        )
        validation = self.validator.validate(cleaned_speech, trace_pool)

        # REEL append: a turn that produced speech or a tool call writes one
        # short entry. SILENCE turns write nothing (no event to record).
        reel_writes: list[ReelEntry] = []
        if cleaned_speech.strip() or tool_results:
            summary = cleaned_speech.strip()[:280] or " | ".join(
                f"{r.op}({'ok' if r.ok else 'err'})" for r in tool_results
            )
            entry = ReelEntry(
                tau_ship=self.state_bus.time.tau_ship,
                t_cosmic_at_write=self.state_bus.time.t_cosmic,
                body=summary,
                irreversibility_flag=any(
                    r.op in ("warp.engage", "warp.disengage") and r.ok
                    for r in tool_results
                ),
            )
            self.reel.write(entry)
            reel_writes.append(entry)

        # Conversation buffer — the windows the §4.9 ephemerals consume.
        tau_now = self.state_bus.time.tau_ship
        if operator_text:
            self._conversation.append(
                ConversationTurn(role="operator", text=operator_text, tau_ship=tau_now),
            )
        if cleaned_speech.strip():
            self._conversation.append(
                ConversationTurn(role="astra", text=cleaned_speech, tau_ship=tau_now),
            )
        self._leaks_since_drift_check += len(perception_leaks) + len(speech_leaks)

        # §4.3.1 initiative accounting: speech on a heartbeat = she
        # originated. Budget exceedance is flagged and logged — never
        # suppressed (measurement before intervention).
        initiative = turn_kind == "heartbeat" and bool(cleaned_speech.strip())
        initiative_budget_exceeded = False
        if initiative:
            window_start = tau_now - INITIATIVE_WINDOW_TAU_S
            recent = [t for t in self._initiations_tau if t >= window_start]
            initiative_budget_exceeded = len(recent) >= INITIATIVE_MAX_PER_WINDOW
            recent.append(tau_now)
            self._initiations_tau = recent

        # §4.9 maintenance windows ride the heartbeat (QCR-14 closure):
        # the consolidator absorbs the un-consolidated conversation window
        # once it is large enough; the drift detector runs when leak
        # events accumulated since its last check. Results are event-log
        # records; consolidator entries are REEL writes like any other.
        ephemeral_runs: list[str] = []
        if turn_kind == "heartbeat":
            # Lazy imports break the orchestrator↔judge cycle (see the
            # module-top note); cost is one dict lookup after first load.
            from astra.harness.ephemeral.consolidator import consolidate_reel
            from astra.harness.ephemeral.drift_detector import detect_drift

            unconsolidated = self._conversation[self._consolidated_upto:]
            if len(unconsolidated) >= CONSOLIDATE_MIN_WINDOW_TURNS:
                consolidation = consolidate_reel(
                    unconsolidated,
                    tau_now=tau_now,
                    t_cosmic_now=self.state_bus.time.t_cosmic,
                    regime_now=self.state_bus.regime,
                )
                self.reel.extend(consolidation.entries)
                reel_writes.extend(consolidation.entries)
                self._consolidated_upto = len(self._conversation)
                ephemeral_runs.append(
                    f"consolidator: {len(consolidation.entries)} entries "
                    f"from {len(unconsolidated)} turns",
                )
            if self._leaks_since_drift_check > 0:
                artifact = detect_drift(
                    self._conversation[-DRIFT_CHECK_RECENT_TURNS:],
                    tau_now=tau_now,
                    t_cosmic_now=self.state_bus.time.t_cosmic,
                    regime_now=self.state_bus.regime,
                )
                self._leaks_since_drift_check = 0
                ephemeral_runs.append(
                    "drift_detector: correction artifact"
                    if artifact is not None
                    else "drift_detector: no drift",
                )

        # Queue this turn's results — ok and guided-rejection alike — for
        # delivery in the next turn's perception (the feedback leg).
        self._pending_tool_results = tool_results

        self._turn_index += 1
        return TurnResult(
            turn_index=self._turn_index - 1,
            perception_bundle=cleaned_perception,
            perception_leaks=perception_leaks,
            raw_llm_output=raw,
            stage_output=stage,
            speech_leaks=speech_leaks,
            tool_results=tool_results,
            validation=validation,
            state_diffs=state_diffs,
            reel_writes=reel_writes,
            narrator_validation=narrator_validation,
            narrator_fallback_reason=narrator_fallback_reason,
            turn_kind=turn_kind,
            initiative=initiative,
            initiative_budget_exceeded=initiative_budget_exceeded,
            ephemeral_runs=ephemeral_runs,
            adapter_mappings=adapter_mappings,
        )

    @property
    def turn_index(self) -> int:
        """Next turn's index (0-based)."""
        return self._turn_index
