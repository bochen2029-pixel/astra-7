"""Persona-test runner — drives an LLMClient through a scripted scenario.

One run = one sysprompt variation × one scenario × N turns. Each turn's
raw output is parsed (think + speech) and evaluated. Results are appended
to a JSONL log for cross-variation comparison.

Usage (Python):
    bundle = build_novita_client(sysprompt=...)
    variation = VariationSpec(id="baseline_v1", sysprompt=..., scenario=...)
    records = await run_variation(variation, bundle, log_path)

Usage (CLI):
    python -m astra persona-test \\
        --variation persona_tests/sysprompts/baseline.md \\
        --scenario persona_tests/scenarios/aigf_escalation.json \\
        --variation-id baseline_v1 \\
        --base-url https://api.novita.ai/openai \\
        --model qwen/qwen3.6-27b
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from astra.llm.client import LLMClient, SamplingParams
from astra.persona_test.evaluator import evaluate_turn
from astra.persona_test.schema import PersonaTurnRecord


@dataclass(slots=True)
class TurnSpec:
    """One scripted user turn.

    `key_facts` (optional): substrings the speech should reference to
    demonstrate engagement with bracket-tagged input payloads. Used as a
    technical-competence proxy for ship-system A/B scenarios.
    """

    text: str
    key_facts: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VariationSpec:
    """One sysprompt variation × one scenario."""

    variation_id: str
    scenario_id: str
    sysprompt: str
    turns: list[TurnSpec] = field(default_factory=list)
    sampling: SamplingParams | None = None


def sysprompt_hash(sysprompt: str) -> str:
    """First 12 hex chars of SHA-256 over the sysprompt text."""
    return hashlib.sha256(sysprompt.encode("utf-8")).hexdigest()[:12]


def load_scenario_file(path: Path) -> tuple[str, list[TurnSpec]]:
    """Load a scenario JSON file. Schema:
        {"scenario_id": "...",
         "turns": [{"text": "...", "key_facts": ["...", ...] (optional)}, ...]}
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    scenario_id = str(raw["scenario_id"])
    turns = [
        TurnSpec(
            text=str(t["text"]),
            key_facts=[str(f) for f in t.get("key_facts", [])],
        )
        for t in raw["turns"]
    ]
    return scenario_id, turns


async def run_variation(
    variation: VariationSpec,
    *,
    base_url: str,
    model_name: str,
    api_key: str | None = None,
    extra_payload: dict[str, object] | None = None,
    log_path: Path | None = None,
) -> list[PersonaTurnRecord]:
    """Run one variation × scenario; append records to log_path if provided.

    Each turn re-instantiates LLMClient with the same sysprompt — turns are
    INDEPENDENT (no conversation memory across turns). This matches the
    K8-manual-test behavior where each tag-bearing input is processed
    standalone against the same sysprompt configuration.

    For multi-turn conversations with memory, use the textverse ScenarioRunner
    instead; this harness is for sysprompt-variation A/B testing where
    independence between turns is the right comparison shape.
    """
    sysprompt = variation.sysprompt
    sp_hash = sysprompt_hash(sysprompt)
    sampling = variation.sampling or SamplingParams(temperature=1.0, top_p=1.0, max_tokens=2048)
    records: list[PersonaTurnRecord] = []

    for idx, turn in enumerate(variation.turns):
        client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        raw = await client.chat_complete(turn.text, sampling)
        evaluation = evaluate_turn(raw, key_facts=turn.key_facts)
        record = PersonaTurnRecord(
            timestamp=datetime.now(UTC).isoformat(),
            variation_id=variation.variation_id,
            scenario_id=variation.scenario_id,
            sysprompt_hash=sp_hash,
            turn_index=idx,
            user_input=turn.text,
            raw_output=raw,
            think_emitted=evaluation.think_emitted,
            think_content=raw_to_think(raw),
            speech_content=raw_to_speech(raw),
            think_length_chars=evaluation.think_length_chars,
            speech_length_chars=evaluation.speech_length_chars,
            think_mechanism_refs=evaluation.think_mechanism_refs,
            think_mechanism_ref_terms=evaluation.think_mechanism_ref_terms,
            speech_mechanism_refs=evaluation.speech_mechanism_refs,
            speech_mechanism_ref_terms=evaluation.speech_mechanism_ref_terms,
            speech_em_dash_count=evaluation.speech_em_dash_count,
            speech_service_phrase_count=evaluation.speech_service_phrase_count,
            speech_service_phrases=evaluation.speech_service_phrases,
            think_first_person_ratio=evaluation.think_first_person_ratio,
            key_facts=evaluation.key_facts,
            speech_key_facts_referenced=evaluation.speech_key_facts_referenced,
            speech_key_facts_hits=evaluation.speech_key_facts_hits,
        )
        records.append(record)
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as fp:
                fp.write(record.model_dump_json() + "\n")

    return records


def raw_to_think(raw: str) -> str:
    """Extract last <think> block content."""
    from astra.persona_test.evaluator import split_think_and_speech
    _, think, _ = split_think_and_speech(raw)
    return think


def raw_to_speech(raw: str) -> str:
    """Extract speech after last </think>."""
    from astra.persona_test.evaluator import split_think_and_speech
    _, _, speech = split_think_and_speech(raw)
    return speech


def summarize_records(records: list[PersonaTurnRecord]) -> dict[str, Any]:
    """Aggregate metrics across a variation × scenario run."""
    if not records:
        return {}
    n = len(records)
    return {
        "n_turns": n,
        "variation_id": records[0].variation_id,
        "scenario_id": records[0].scenario_id,
        "sysprompt_hash": records[0].sysprompt_hash,
        "think_emission_rate": sum(r.think_emitted for r in records) / n,
        "mean_think_length_chars": sum(r.think_length_chars for r in records) / n,
        "mean_speech_length_chars": sum(r.speech_length_chars for r in records) / n,
        "total_think_mechanism_refs": sum(r.think_mechanism_refs for r in records),
        "total_speech_mechanism_refs": sum(r.speech_mechanism_refs for r in records),
        "total_speech_em_dashes": sum(r.speech_em_dash_count for r in records),
        "total_speech_service_phrases": sum(r.speech_service_phrase_count for r in records),
        "mean_think_first_person_ratio": (
            sum(r.think_first_person_ratio for r in records if r.think_emitted)
            / max(1, sum(1 for r in records if r.think_emitted))
        ),
    }
