"""Tool dispatch — validates one (op, args) call and produces a state diff.

Day 5 v0: dispatcher validates against the locked Pydantic schemas in
`api.py` and produces a ToolResult. Actual state-mutation (committing
the diff to StateBus) lives in the orchestrator's tick step; this module
is purely the parse-validate-describe-effect boundary.

The dispatcher is calculator-bound by transitive property: it never
generates numeric values itself. Everything in `state_diff` traces to
either the args (from ASTRA's tool call) or to a nexus_bridge query
the orchestrator made.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from astra.ship.api import TOOL_API, ToolResult


def dispatch(op_name: str, args: dict[str, Any]) -> ToolResult:
    """Validate args against the locked schema for op_name; describe effect.

    Returns a ToolResult. Day 5 v0 emits *intended* state diffs without
    actually mutating the StateBus — the orchestrator commits the diff
    in a separate phase (so the State Bus stays double-buffered per §1.5).

    On validation error: ToolResult.ok=False, error populated, no state_diff.
    """
    schema_cls = TOOL_API.get(op_name)
    if schema_cls is None:
        return ToolResult(
            op=op_name,
            ok=False,
            error=f"unknown op '{op_name}'; not in TOOL_API",
        )
    try:
        validated = schema_cls.model_validate(args)
    except ValidationError as e:
        return ToolResult(
            op=op_name,
            ok=False,
            error=f"schema validation failed: {e.errors()[0]['msg']}",
        )

    state_diff = _describe_effect(op_name, validated)
    return ToolResult(
        op=op_name,
        ok=True,
        args=validated.model_dump(),
        state_diff=state_diff,
    )


def _describe_effect(op_name: str, validated_args: Any) -> dict[str, Any]:
    """Map (op, validated_args) → minimal state_diff dict.

    Day 5 v0 keeps diffs as plain dicts that the orchestrator's tick step
    applies to StateBus. Each op's diff shape is locked by this module.
    """
    if op_name == "power.allocate":
        return {
            "power_allocation": {validated_args.subsystem: validated_args.fraction},
        }
    if op_name == "warp.engage":
        diff: dict[str, Any] = {"warp_target_factor": validated_args.target_factor}
        if validated_args.target_coords is not None:
            diff["warp_target_coords"] = validated_args.target_coords.model_dump()
        return diff
    if op_name == "warp.disengage":
        return {"warp_disengage_mode": validated_args.mode}
    if op_name == "nav.heading_set":
        target = validated_args.target
        if isinstance(target, str):
            return {"nav_target_body": target}
        return {"nav_target_coords": target.model_dump()}
    if op_name == "sensors.scan":
        return {
            "sensor_scan_pending": {
                "region": validated_args.region,
                "sensitivity": validated_args.sensitivity,
            },
        }
    if op_name == "log.write":
        return {
            "log_appended": {
                "channel": validated_args.channel,
                "text": validated_args.text,
            },
        }
    if op_name == "status.query":
        # Read-only (R-A, v0.130): NO state diff, ever. The orchestrator —
        # the entity holding the live StateBus — fulfils the read into
        # ToolResult.result after dispatch; this module stays the pure
        # parse-validate-describe boundary and a read has no effect to
        # describe.
        return {}
    # Should never reach here — schema_cls lookup above guards this.
    return {}
