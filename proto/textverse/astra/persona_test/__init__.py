"""astra.persona_test — sysprompt-variation test harness for STAGE discipline.

Wires LLMClient (Novita-ready) + StageParser + heuristic evaluator into a
loop that runs N sysprompt variations × M scenarios and writes structured
results to a JSONL log for cross-variation comparison.

Motivating use case (2026-05-16 K8 manual test):
- Bo tested whether sysprompt-alone could elicit always-think + absorb-not-
  acknowledge + STAGE-tag absorption inside the think tag.
- Result: always-think discipline broke inconsistently; think-content
  referenced sysprompt rules verbatim when STAGE override conflicted with
  K8 constitutional refusals.
- Question: do different sysprompt wordings change these failure rates?
- Manual testing is slow; this harness makes it automated.

Output: research_log-style JSONL at persona_tests/log/persona_test_log.jsonl
with per-turn metrics for later comparison across variations.
"""

from astra.persona_test.evaluator import (
    PersonaTestEvaluation,
    evaluate_turn,
)
from astra.persona_test.runner import (
    TurnSpec,
    VariationSpec,
    run_variation,
)
from astra.persona_test.schema import PersonaTurnRecord

__all__ = [
    "PersonaTestEvaluation",
    "PersonaTurnRecord",
    "TurnSpec",
    "VariationSpec",
    "evaluate_turn",
    "run_variation",
]
