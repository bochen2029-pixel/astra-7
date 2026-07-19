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

from astra.grammar import LeakDetector, LeakEvent, StageOutput, parse_stage
from astra.harness.perception_assembler import (
    assemble_perception_bundle,
    assemble_perception_bundle_via_narrator,
)
from astra.harness.reel import Reel, ReelEntry
from astra.llm.adapter_bundle import AdapterResult, RulesBasedAdapter
from astra.llm.astra_bundle import AstraBundle
from astra.llm.narrator_bundle import NarratorBundle, NarratorValidationError
from astra.llm.validator import CalculatorBoundValidator, ValidationReport
from astra.ship.api import ToolResult
from astra.ship.dispatcher import dispatch as dispatch_tool
from astra.state_bus import StateBus


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
    ) -> None:
        self.state_bus = state_bus
        self.astra_bundle = astra_bundle
        self.reel = reel or Reel()
        self.validator = validator or CalculatorBoundValidator(severity="soft")
        self.leak_detector = leak_detector or LeakDetector.from_default_canon()
        self.adapter = adapter or RulesBasedAdapter()
        # T2.3 (2026-05-16): when narrator_bundle is wired, step 1 of the
        # turn loop routes through the LLM-based perception assembler
        # with calculator-bound auto-validation. Falls back to the
        # template path on NarratorValidationError (exhausted retries).
        self.narrator_bundle = narrator_bundle
        self._turn_index: int = 0

    async def run_turn(
        self,
        operator_text: str = "",
        somatic_note: str | None = None,
    ) -> TurnResult:
        """One turn end-to-end. Returns TurnResult; mutations applied to REEL."""
        # 1. Assemble perception — Narrator path if wired (with calculator-
        # bound auto-validation), template path otherwise. On Narrator
        # validation failure (exhausted retries), fall back to template
        # and record the reason on TurnResult for forensics.
        retrievals = self.reel.search(operator_text or "watch reactor", k=3)
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
                )
        else:
            perception = assemble_perception_bundle(
                state_bus=self.state_bus,
                operator_text=operator_text,
                reel_retrievals=retrievals,
                somatic_note=somatic_note,
            )

        # 2. Leak-scan perception before delivery
        cleaned_perception, perception_leaks = self.leak_detector.scan_perception_bundle(
            perception,
        )

        # 3. Send to ASTRA-LLM
        raw = await self.astra_bundle.client.chat_complete(
            cleaned_perception, self.astra_bundle.sampling,
        )

        # 4. Parse STAGE channels
        stage = parse_stage(raw)

        # 5. Leak-scan speech
        cleaned_speech, speech_leaks = self.leak_detector.scan_speech(stage.speech)
        # If the leak scan modified speech, build a new StageOutput with the
        # cleaned version so downstream callers see the post-strip text.
        if cleaned_speech != stage.speech:
            stage = stage.model_copy(update={"speech": cleaned_speech})

        # 6 + 7. Normalize and dispatch each tool call
        tool_results: list[ToolResult] = []
        state_diffs: list[dict[str, object]] = []
        for tc in stage.tool_calls:
            # If arguments dict is already populated (JSON body), use directly;
            # else fall back to the adapter on raw_body.
            args: dict[str, object]
            if tc.arguments:
                args = dict(tc.arguments)
            else:
                adapter_result: AdapterResult = self.adapter.normalize(tc.name, tc.raw_body)
                if not adapter_result.ok:
                    tool_results.append(
                        ToolResult(op=tc.name, ok=False, error=adapter_result.error),
                    )
                    continue
                args = dict(adapter_result.args)
            result = dispatch_tool(tc.name, args)
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
        )

    @property
    def turn_index(self) -> int:
        """Next turn's index (0-based)."""
        return self._turn_index
