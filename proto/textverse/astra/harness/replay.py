"""Model-Off Replay — spec-v0.130-DRAFT §2.4/§2.5 (suite-level predicate).

Any recorded bench session replays byte-identically on declared state from
(scenario config, trace, turn count) with every LLM server offline and the
network unreachable. The `ReplayClient` below is the whole mechanism: it
satisfies the LLMClient surface from the trace alone, touches no transport,
and *verifies* on every call that the prompt it is asked to answer hashes
identically to the prompt the recorded utterance answered — so any
nondeterminism upstream of the LLM (perception assembly, retrieval,
leak-scan, state advance) is caught at the exact turn it diverges, not as
a downstream diff.

Scope (v0, documented): the astra-role path. Narrator-wired sessions
record their utterances through the same SessionTrace surface but replaying
the Narrator's internal retry loop is future work; the scenario suite runs
the template perception path.

Declared-state digest: TurnRecord minus the non-declared column
(latency_s — §5.3: wall-time is never declared state).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from astra.harness.trace import SessionTrace, TraceRecord, text_sha256
from astra.judge import TurnRecord
from astra.llm import AstraBundle
from astra.llm.client import LLMClient, SamplingParams
from astra.scenarios.runner import RunReport, ScenarioRunner
from astra.scenarios.schema import Scenario


class ReplayDivergenceError(RuntimeError):
    """The replayed pipeline diverged from the recorded session."""


class ReplayClient(LLMClient):
    """LLMClient that answers from the trace and can never reach a network.

    It overrides every transport-touching method; the base class's httpx
    paths are unreachable from here. `base_url` is a sentinel scheme no
    transport would accept, as defense in depth.
    """

    def __init__(self, utterances: list[TraceRecord]) -> None:
        super().__init__(base_url="replay://model-off", sysprompt="replay")
        self._utterances = list(utterances)
        self._next = 0

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        if self._next >= len(self._utterances):
            raise ReplayDivergenceError(
                f"trace exhausted: replay asked for utterance "
                f"#{self._next} but the trace holds {len(self._utterances)}",
            )
        record = self._utterances[self._next]
        got = text_sha256(user_text)
        if record.context_sha256 and got != record.context_sha256:
            raise ReplayDivergenceError(
                f"context divergence at utterance #{self._next} "
                f"(recorded turn {record.turn_index}): the replayed pipeline "
                f"produced a different prompt than the recorded session "
                f"(sha {got[:12]}… != {record.context_sha256[:12]}…)",
            )
        self._next += 1
        return record.payload

    async def chat_stream(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        raise ReplayDivergenceError("streaming is not part of the recorded surface")
        yield ""  # type: ignore[unreachable]  # pragma: no cover — generator marker

    async def health(self) -> bool:
        return True  # no transport; nothing to probe


def replay_bundle_from_trace(trace: SessionTrace, *, role: str = "astra") -> AstraBundle:
    """Build an AstraBundle whose client answers from the trace."""
    bundle = AstraBundle(base_url="replay://model-off", sysprompt="replay")
    bundle.client = ReplayClient(trace.utterances(role))
    return bundle


async def run_model_off_replay(
    scenario: Scenario,
    trace: SessionTrace,
) -> RunReport:
    """Re-run a scenario with all oracles answered from the trace.

    No llama-server, no network, no model. Raises ReplayDivergenceError if
    the recomputed pipeline diverges from the recorded one at any call.
    """
    runner = ScenarioRunner(
        scenario=scenario,
        astra_bundle=replay_bundle_from_trace(trace),
        write_artifacts=False,
    )
    return await runner.run()


def declared_state_digest(turn_records: list[TurnRecord]) -> str:
    """Canonical digest over the declared column of a session.

    Excludes `latency_s` (non-declared wall-time per §5.3). Everything else
    in a TurnRecord is a derived, deterministic function of (config, trace,
    steps) and must be byte-identical under Model-Off Replay.
    """
    canonical = json.dumps(
        [r.model_dump(exclude={"latency_s"}) for r in turn_records],
        sort_keys=True,
        ensure_ascii=False,
    )
    return text_sha256(canonical)
