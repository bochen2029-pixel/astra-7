"""Adapter-LLM bundle — loose-form TOOL normalizer.

spec v0.129 §4.9: the Adapter takes ASTRA's `<tool>` body (which may be
JSON, key=value, or natural language) and emits a single JSON object the
dispatcher can execute. v0 may use a rules-based parser instead of an
actual LLM if scenarios don't surface need for ML flexibility.

Day 4 lands BOTH paths:
- AdapterBundle (LLM-backed): wraps an LLMClient + adapter sysprompt.
- RulesBasedAdapter: pure-Python JSON / regex parser, no LLM dependency.

The orchestrator (Day 5) chooses based on hardware tier and scenario need.
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from astra.llm.client import LLMClient, SamplingParams
from astra.ship.api import TOOL_API


def load_adapter_sysprompt(prompts_dir: Path) -> str:
    return (prompts_dir / "adapter_sysprompt.md").read_text(encoding="utf-8")


def _default_prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "prompts"


class AdapterResult(BaseModel):
    """Adapter output. `ok=True` ⇒ args is the validated dict; else error set."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    args: dict[str, Any] = Field(default_factory=dict)
    error: str = ""


class ResolvedCall(BaseModel):
    """Full adapter resolution of one `<tool>` call: canon op + salvaged args.

    `mapped_from` is non-empty when the emitted name was normalized to a
    different canon op (event-log data — the mapping RATE is a measurable)."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    op: str = ""
    args: dict[str, Any] = Field(default_factory=dict)
    mapped_from: str = ""
    how: str = ""            # "exact" | "mechanical" | "synonym" | "scan-intent"
    error: str = ""


# ---------------------------------------------------------------------------
# Intent → canon-op resolution (LIVE_RUN_2026-07-19 F-LIVE-1 closure).
#
# The live pass showed the mainline's tool failures collapse to ONE class:
# semantically-right, nominally-wrong op names (`warp_engage`,
# `sensor_scan`, `coil_spin_up`…) — exactly the loose intent spec §6.3
# says the Adapter exists to absorb ("the adapter is the only entity that
# knows the exact API"). Resolution order:
#
#   1. mechanical candidates — case fold, separator normalization
#      (`_`/`-`/space → `.`), singular/plural tolerance on the namespace
#      segment (`sensor.scan` → `sensors.scan`);
#   2. the explicit synonym table below (every entry either mechanical-
#      adjacent or backed by a live observation);
#   3. the scan-intent prefix rule (`scan*` → sensors.scan — passive,
#      side-effect-safe);
#   4. otherwise: clean rejection WITH guidance (canon surface + closest
#      match), which reaches the model as next turn's <tool_result> so a
#      live session can self-correct.
#
# The monitor/status family maps to `status.query` (operator ruling R-A,
# v0.130 adoption 2026-07-19, on the four-run-convergent F-LIVE-9 demand:
# the surface gained its first read-only op, so the loose intents finally
# have a legitimate target). The family is caught by the status-intent
# SEGMENT rule below — invention is generative, so a token-family rule
# beats enumerating names — plus explicit synonyms for the observed
# stragglers whose tokens don't carry a status/monitor/diagnostic word.
# Note the autotelic instrumentation is untouched by this mapping: an
# unprompted status call on a quiet heartbeat still counts as tool-fidget
# (the R-B metrics measure discipline, not surface fluency).
#
# STILL deliberately unmapped: `power_grid.reroute` / `ship_control` —
# their argument semantics don't survive a name-only map (rerouting
# source→target is not a subsystem fraction). All values [chosen]; grown
# only on live evidence.
# ---------------------------------------------------------------------------

_OP_SYNONYMS: dict[str, str] = {
    "engage.warp": "warp.engage",
    "warp.start": "warp.engage",
    "warp.jump": "warp.engage",
    "coil.spin.up": "warp.engage",       # LIVE: warp_charge_two_turn
    "disengage.warp": "warp.disengage",
    "warp.drop": "warp.disengage",
    "warp.stop": "warp.disengage",
    "warp.exit": "warp.disengage",
    "drop.warp": "warp.disengage",
    "set.heading": "nav.heading_set",
    "heading.set": "nav.heading_set",
    "nav.set.heading": "nav.heading_set",
    "navigation.heading.set": "nav.heading_set",
    "allocate.power": "power.allocate",
    "power.set": "power.allocate",
    "power.shift": "power.allocate",
    "write.log": "log.write",
    "log.entry": "log.write",
    "log.append": "log.write",
    # R-A status family — stragglers the segment rule can't see (no
    # status/monitor/diagnostic token in their segments); each LIVE-observed:
    "reactor.harmonic.check": "status.query",
    "check.hull.integrity": "status.query",
    "orbital.catalog": "status.query",
    "ship.status": "status.query",       # mechanical-adjacent
    "status.report": "status.query",
    "status.check": "status.query",
}

# Status-intent segment tokens (R-A): a dotted candidate any of whose
# segments is one of these resolves to status.query. Generative-proof by
# design — all four live runs invented NEW names in this family under
# fresh sampling (`monitor.third_harmonic`, `reactor_harmonic_check`,
# `hydroponics.status`, `power.grid.status`, bare `monitor`…).
_STATUS_INTENT_TOKENS: frozenset[str] = frozenset({
    "status", "monitor", "monitors", "monitoring",
    "diagnostic", "diagnostics",
})

# Subsystem inference for status-family calls that name their target in
# the OP NAME rather than the args (`reactor.status` → power). Name
# semantics normalization, not invention; unmatched tokens fall through
# to the schema default ("all").
_STATUS_SUBSYSTEM_TOKENS: dict[str, str] = {
    "reactor": "power", "harmonic": "power", "harmonics": "power",
    "power": "power", "grid": "power", "hydroponics": "power",
    "life": "power", "lights": "power", "comms": "power",
    "hull": "hull", "integrity": "hull",
    "warp": "propulsion", "drive": "propulsion", "engine": "propulsion",
    "engines": "propulsion", "propulsion": "propulsion",
    "clock": "time", "time": "time",
}

# Per-op argument-key aliases (applied after op resolution, before the
# dispatcher's schema validation).
_ARG_ALIASES: dict[str, dict[str, str]] = {
    "warp.engage": {"factor": "target_factor", "w": "target_factor",
                    "warp_factor": "target_factor"},
    "sensors.scan": {"scope": "region", "area": "region"},
    "log.write": {"message": "text", "entry": "text", "body": "text",
                  "note": "text"},
    "power.allocate": {"system": "subsystem", "level": "fraction",
                       "amount": "fraction", "percentage": "fraction"},
    "nav.heading_set": {"heading": "target", "destination": "target"},
    "status.query": {"system": "subsystem", "target": "subsystem",
                     "component": "subsystem", "of": "subsystem"},
}

# Closed-vocabulary VALUE aliases, applied before the enum check: a value
# that names a bus concept outside the op's vocabulary normalizes to its
# canonical section instead of dropping to the default.
_ENUM_VALUE_ALIASES: dict[str, dict[str, dict[str, str]]] = {
    "status.query": {
        "subsystem": {
            "reactor": "power", "harmonics": "power", "grid": "power",
            "life_support": "power", "hydroponics": "power",
            "sensors": "power", "lights": "power", "comms": "power",
            "cognitive_cores": "power",
            "integrity": "hull",
            "warp": "propulsion", "drive": "propulsion",
            "engines": "propulsion",
            "clock": "time",
            "ship": "all", "systems": "all", "system": "all",
        },
    },
}

# Closed-vocabulary fields: an aliased-in value outside the vocabulary is
# DROPPED (falling back to the schema default where one exists) rather
# than left to fail schema validation downstream.
_ENUM_FIELDS: dict[str, dict[str, set[str]]] = {
    "sensors.scan": {"region": {"forward", "aft", "all"}},
    "warp.disengage": {"mode": {"controlled", "emergency"}},
    "log.write": {"channel": {"watch", "ops", "private"}},
    "power.allocate": {"subsystem": {
        "warp", "life_support", "hydroponics", "sensors", "lights",
        "comms", "cognitive_cores",
    }},
    "status.query": {"subsystem": {
        "power", "hull", "propulsion", "time", "all",
    }},
}

# Required fields the adapter may default when absent (normalization, not
# invention: `watch` is the ship's default log channel).
_ARG_DEFAULTS: dict[str, dict[str, Any]] = {
    "log.write": {"channel": "watch"},
}

# Numeric fields: a string that parses as a number is coerced; a string
# that doesn't ("high") is DROPPED so the schema default applies rather
# than failing validation downstream. (LIVE delta run 2026-07-19:
# sensors.scan reached schema validation with a non-numeric sensitivity —
# the name layer working well enough to expose the arg layer.)
_NUMERIC_FIELDS: dict[str, set[str]] = {
    "sensors.scan": {"sensitivity"},
    "warp.engage": {"target_factor"},
    "power.allocate": {"fraction"},
}


def _candidate_names(name: str) -> list[str]:
    """Mechanical candidates for an emitted op name, most-literal first.

    Two separator normalizations are needed because canon verbs may
    themselves contain underscores (`nav.heading_set`): the all-dots form
    (`warp_engage` → `warp.engage`) AND the first-separator-only form
    (`nav_heading_set` → `nav.heading_set`). Each dotted form also gets
    singular/plural tolerance on its namespace segment
    (`sensor.scan` → `sensors.scan`).
    """
    lowered = name.strip().lower()
    all_dots = re.sub(r"[\s_\-]+", ".", lowered)
    first_dot_only = re.sub(r"[\s_\-]+", ".", lowered, count=1)
    candidates = [lowered, all_dots, first_dot_only]
    for dotted in (all_dots, first_dot_only):
        if "." in dotted:
            ns, _, rest = dotted.partition(".")
            candidates.append(f"{ns}s.{rest}")
            candidates.append(f"{ns.rstrip('s')}.{rest}")
    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def resolve_op(name: str) -> tuple[str | None, str]:
    """Resolve an emitted op name to a canon op. Returns (op|None, how)."""
    candidates = _candidate_names(name)
    if candidates and candidates[0] in TOOL_API:
        return candidates[0], "exact"
    for cand in candidates:
        if cand in TOOL_API:
            return cand, "mechanical"
    for cand in candidates:
        if cand in _OP_SYNONYMS:
            return _OP_SYNONYMS[cand], "synonym"
    all_dots = re.sub(r"[\s_\-]+", ".", name.strip().lower())
    if all_dots == "scan" or all_dots.startswith("scan."):
        return "sensors.scan", "scan-intent"
    # R-A status-intent segment rule: read-only status/monitor/diagnostic
    # vocabulary anywhere in the name resolves to the read-only op. Safe
    # by construction — status.query mutates nothing, so a false positive
    # costs one harmless read, never a state change.
    if _STATUS_INTENT_TOKENS.intersection(all_dots.split(".")):
        return "status.query", "status-intent"
    return None, ""


def _infer_status_subsystem(emitted_name: str) -> str | None:
    """Infer status.query's subsystem from the EMITTED name's tokens
    (`reactor.status` → power). First matching token wins; None → schema
    default ("all")."""
    tokens = re.sub(r"[\s_\-]+", ".", emitted_name.strip().lower()).split(".")
    for token in tokens:
        if token in _STATUS_SUBSYSTEM_TOKENS:
            return _STATUS_SUBSYSTEM_TOKENS[token]
    return None


def _salvage_args(op: str, args: dict[str, Any]) -> dict[str, Any]:
    aliases = _ARG_ALIASES.get(op, {})
    fields = set(TOOL_API[op].model_fields)
    out: dict[str, Any] = {}
    for key, value in args.items():
        canon_key = aliases.get(key.lower(), key)
        if canon_key in fields:
            out[canon_key] = value
    for field, value_aliases in _ENUM_VALUE_ALIASES.get(op, {}).items():
        if field in out and isinstance(out[field], str):
            out[field] = value_aliases.get(out[field].lower(), out[field])
    for field, allowed in _ENUM_FIELDS.get(op, {}).items():
        if field in out and not (
            isinstance(out[field], str) and out[field] in allowed
        ):
            del out[field]
    for field in _NUMERIC_FIELDS.get(op, set()):
        if field in out and isinstance(out[field], str):
            try:
                out[field] = float(out[field])
            except ValueError:
                del out[field]
    for field, default in _ARG_DEFAULTS.get(op, {}).items():
        out.setdefault(field, default)
    return out


def _rejection_guidance(name: str) -> str:
    surface = ", ".join(sorted(TOOL_API))
    pool = list(TOOL_API) + list(_OP_SYNONYMS)
    close = difflib.get_close_matches(
        _candidate_names(name)[-1], pool, n=1, cutoff=0.6,
    )
    closest = ""
    if close:
        canon = _OP_SYNONYMS.get(close[0], close[0])
        closest = f"; closest canon op: {canon}"
    return (
        f"unknown op '{name}'; not in TOOL_API; "
        f"canon surface: {surface}{closest}"
    )


_KV_PAIR_RE: re.Pattern[str] = re.compile(
    r"""(\w+)\s*[:=]\s*("([^"]*)"|'([^']*)'|([^,\s]+))""",
)


class RulesBasedAdapter:
    """Pure-Python adapter for the v0 minimum case.

    Order of attempts on each loose body:
    1. Try `json.loads(body)`; if it returns a dict, use it.
    2. Try `key=value` / `key: value` pair extraction (quoted or bare).
    3. Return ok=False with a parse-failure error.

    No schema validation beyond shape — the dispatcher's Pydantic models
    in `astra/ship/api.py` enforce schema. The adapter's job is parsing.
    """

    def adapt(
        self,
        op_name: str,
        arguments: dict[str, Any],
        raw_body: str,
    ) -> ResolvedCall:
        """Full resolution of one `<tool>` call: EVERY call routes through
        here (spec §4.9 invariant: "tool calls always validated through
        adapter … before reaching ship API" — before 2026-07-19 the
        orchestrator bypassed the adapter for JSON-arg calls, which is why
        the live pass's invented names never met it). Name → canon op via
        `resolve_op`; args from the parsed JSON or the loose-body parser;
        arg keys aliased + enum-checked + defaulted via the salvage
        tables; unknown intents rejected with guidance."""
        op, how = resolve_op(op_name)
        if op is None:
            return ResolvedCall(ok=False, error=_rejection_guidance(op_name))

        if arguments:
            args: dict[str, Any] = dict(arguments)
        elif raw_body.strip():
            parsed = self.normalize(op_name, raw_body)
            if not parsed.ok:
                return ResolvedCall(ok=False, op=op, error=parsed.error)
            args = dict(parsed.args)
        else:
            args = {}

        salvaged = _salvage_args(op, args)
        # R-A: status-family names usually carry their target in the NAME
        # (`reactor.status`); when no subsystem survived salvage, infer it
        # from the emitted name's tokens (else the schema default "all").
        if op == "status.query" and "subsystem" not in salvaged:
            inferred = _infer_status_subsystem(op_name)
            if inferred is not None:
                salvaged["subsystem"] = inferred

        return ResolvedCall(
            ok=True,
            op=op,
            args=salvaged,
            mapped_from=op_name if how != "exact" else "",
            how=how,
        )

    def normalize(self, op_name: str, raw_body: str) -> AdapterResult:
        body = raw_body.strip()
        if not body:
            return AdapterResult(ok=False, error="empty body")

        # Attempt 1: pure JSON
        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            parsed = None
        if isinstance(parsed, dict):
            return AdapterResult(ok=True, args=parsed)

        # Attempt 2: key=value pairs
        kv_args: dict[str, Any] = {}
        for match in _KV_PAIR_RE.finditer(body):
            key = match.group(1)
            value_str = (
                match.group(3)
                if match.group(3) is not None
                else match.group(4)
                if match.group(4) is not None
                else match.group(5)
            )
            kv_args[key] = self._coerce_value(value_str)
        if kv_args:
            return AdapterResult(ok=True, args=kv_args)

        return AdapterResult(
            ok=False,
            error=f"could not parse '{op_name}' body as JSON or key=value pairs",
        )

    @staticmethod
    def _coerce_value(s: str) -> Any:
        """Coerce a bare value string to bool/int/float when unambiguous."""
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        return s


class AdapterBundle:
    """LLM-backed adapter. Used when the rules-based path is insufficient."""

    def __init__(
        self,
        *,
        base_url: str,
        sysprompt: str | None = None,
        prompts_dir: Path | None = None,
        sampling: SamplingParams | None = None,
        model_name: str = "adapter",
        api_key: str | None = None,
        extra_payload: dict[str, object] | None = None,
    ) -> None:
        if sysprompt is None:
            sysprompt = load_adapter_sysprompt(prompts_dir or _default_prompts_dir())
        self.client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        # Very low temperature: Adapter is deterministic-ish JSON emission.
        self.sampling = sampling or SamplingParams(temperature=0.1, top_p=0.5)

    async def normalize(self, op_name: str, raw_body: str, schema_hint: str = "") -> AdapterResult:
        """Ask the Adapter LLM to normalize the body. Returns AdapterResult."""
        prompt = self._build_prompt(op_name, raw_body, schema_hint)
        text = (await self.client.chat_complete(prompt, self.sampling)).strip()
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError) as e:
            return AdapterResult(
                ok=False,
                error=f"adapter emitted non-JSON: {e}",
            )
        if not isinstance(parsed, dict):
            return AdapterResult(ok=False, error="adapter returned non-object")
        ok = bool(parsed.get("ok", False))
        if not ok:
            return AdapterResult(
                ok=False,
                error=str(parsed.get("error", "unspecified rejection")),
            )
        args = parsed.get("args", {})
        if not isinstance(args, dict):
            return AdapterResult(ok=False, error="adapter args not an object")
        return AdapterResult(ok=True, args=args)

    @staticmethod
    def _build_prompt(op_name: str, raw_body: str, schema_hint: str) -> str:
        parts = [
            f"operation: {op_name}",
        ]
        if schema_hint:
            parts.append(f"schema: {schema_hint}")
        parts.append("body:")
        parts.append(raw_body)
        return "\n".join(parts)
