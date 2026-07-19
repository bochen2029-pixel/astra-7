"""Session trace — the oracle column of the §5.3 trace/event-log split.

Per spec-v0.130-DRAFT §2.4 (LOCKED on adoption): every run partitions its
record into

- **trace** — what the system could not have computed: operator inputs and
  LLM utterances (receipted verbatim at generation with model-id, sampling
  fingerprint, and a hash of the exact context they were generated from),
  plus imported external data (none in the bench yet);
- **event log** — everything derived: physics, gates, dispatches,
  ephemeral artifacts, state deltas (the transcript + TurnResult fields).

Replay *reads* the trace and *recomputes* the event log; it never
re-samples an oracle. The `context_sha256` on each utterance is what makes
Model-Off Replay adversarial: at replay time the client verifies that the
prompt it is asked to answer hashes identically to the prompt the original
utterance answered — any nondeterminism anywhere upstream (perception
assembly, REEL retrieval, leak-scan, state advance) surfaces as a
divergence error at the exact turn it appears.

No wall clock anywhere: records are ordered by turn index and carry only
fictional-time-free metadata. Hashing is `hashlib` (not a clock source).

Mechanism precedent: shipped and gate-proven in-lineage (backrooms M11 —
replay bit-identical with the model unreachable).
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def text_sha256(text: str) -> str:
    """Canonical context hash used by trace records and replay verification."""
    return sha256(text.encode("utf-8")).hexdigest()


class TraceRecord(BaseModel):
    """One oracle event, verbatim at the moment it was produced."""

    model_config = ConfigDict(frozen=True)

    kind: Literal["operator_input", "llm_utterance"]
    turn_index: int = Field(ge=0)
    payload: str                       # verbatim text (input or raw LLM output)
    role: str = ""                     # "astra" | "narrator" | "adapter" (utterances)
    model_id: str = ""                 # utterances: client model_name
    params_fingerprint: str = ""       # utterances: sha256 of sampling params JSON
    context_sha256: str = ""           # utterances: sha256 of the exact prompt


class SessionTrace:
    """Append-only in-memory trace for one session; JSONL round-trippable."""

    def __init__(self, records: list[TraceRecord] | None = None) -> None:
        self._records: list[TraceRecord] = list(records or [])

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> list[TraceRecord]:
        return list(self._records)

    def record_operator(self, turn_index: int, text: str) -> None:
        self._records.append(
            TraceRecord(kind="operator_input", turn_index=turn_index, payload=text),
        )

    def record_utterance(
        self,
        turn_index: int,
        *,
        role: str,
        payload: str,
        context: str,
        model_id: str = "",
        params_fingerprint: str = "",
    ) -> None:
        self._records.append(
            TraceRecord(
                kind="llm_utterance",
                turn_index=turn_index,
                payload=payload,
                role=role,
                model_id=model_id,
                params_fingerprint=params_fingerprint,
                context_sha256=text_sha256(context),
            ),
        )

    def utterances(self, role: str) -> list[TraceRecord]:
        """All llm_utterance records for one role, in generation order."""
        return [
            r for r in self._records if r.kind == "llm_utterance" and r.role == role
        ]

    def operator_inputs(self) -> list[TraceRecord]:
        return [r for r in self._records if r.kind == "operator_input"]

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(r.model_dump(), sort_keys=True) for r in self._records)

    @classmethod
    def from_jsonl(cls, text: str) -> SessionTrace:
        records = [
            TraceRecord.model_validate(json.loads(line))
            for line in text.splitlines()
            if line.strip()
        ]
        return cls(records)
