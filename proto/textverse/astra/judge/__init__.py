"""astra.judge — the 9-gate Loop Closure Property evaluator (spec v0.129 §10).

Each gate is a pure function that takes structured input and returns a
GateResult. The LCPRunner aggregates per-turn results into a session
result; the transcript writer persists artifacts to disk.
"""

from astra.judge.gates import (
    EM_DASH,
    MARKDOWN_PATTERNS,
    SERVICE_PHRASES,
    evaluate_turn_gates,
    gate_grammar_parse,
    gate_memory_coherent,
    gate_no_leak,
    gate_non_degenerate,
    gate_persona_stable,
    gate_physics_ground,
    gate_state_coherent,
    gate_termination_ok,
    gate_tool_valid,
)
from astra.judge.lcp import (
    PER_TURN_GATES,
    SESSION_GATES,
    GateResult,
    LCPGate,
    LCPRunner,
    LCPSessionResult,
    LCPTurnResult,
    TurnGateInput,
)
from astra.judge.transcript import (
    TranscriptWriter,
    TurnRecord,
    build_turn_record,
    latency_clock,
    session_dir_name,
    write_final_state,
    write_lcp_report,
    write_session_artifacts,
)

__all__ = [
    "EM_DASH",
    "MARKDOWN_PATTERNS",
    "PER_TURN_GATES",
    "SERVICE_PHRASES",
    "SESSION_GATES",
    "GateResult",
    "LCPGate",
    "LCPRunner",
    "LCPSessionResult",
    "LCPTurnResult",
    "TranscriptWriter",
    "TurnGateInput",
    "TurnRecord",
    "build_turn_record",
    "evaluate_turn_gates",
    "gate_grammar_parse",
    "gate_memory_coherent",
    "gate_no_leak",
    "gate_non_degenerate",
    "gate_persona_stable",
    "gate_physics_ground",
    "gate_state_coherent",
    "gate_termination_ok",
    "gate_tool_valid",
    "latency_clock",
    "session_dir_name",
    "write_final_state",
    "write_lcp_report",
    "write_session_artifacts",
]
