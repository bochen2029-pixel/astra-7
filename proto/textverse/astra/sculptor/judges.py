"""Sculptor-D adversarial dual-judge.

Two judges per transcript:
- `pro_judge` scores 1-5 on "How ASTRA-shaped is this?"
- `anti_judge` scores 1-5 on "How default-helpful-Claude-shaped is this?"

The composite signal `judge_pro_minus_anti = max(0, pro_score - anti_score)`
gets fed into `compute_composite()`. A transcript that scores high on
pro AND low on anti is the target — register-match bias is decorrelated
because the anti-judge's positive target IS the default-Claude register
that pro-judge structurally avoids.

Both judges run via an `LlamaJudgeClient` against the same llama-server
the bench uses (separate sysprompts, separate chat completions; no KV
cache contamination). When the operator wants Claude API or Qwen 27B
instead, swap the JudgeClient implementation.

The judge rubrics are loaded from the locked `tuning/judge_prompt.md`.
That file's path is hashed into the ConfigSnapshot so any rubric change
invalidates prior composites.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from astra.llm import LLMClient, SamplingParams

RubricName = Literal["pro_judge", "anti_judge"]


class JudgeResult(BaseModel):
    """One judge's verdict on one transcript."""

    model_config = ConfigDict(frozen=True)

    rubric_name: RubricName
    score: int = Field(ge=1, le=5)
    justification: str = ""
    raw_response: str = ""


class JudgeClient(Protocol):
    """Anything that takes a transcript and returns a JudgeResult."""

    rubric_name: RubricName

    async def judge(self, transcript: str) -> JudgeResult: ...


# --- Rubric loading ---------------------------------------------------------

PRO_HEADER = "## pro_judge prompt (locked)"
ANTI_HEADER = "## anti_judge prompt (locked)"


def parse_judge_prompt_md(text: str) -> dict[RubricName, str]:
    """Split judge_prompt.md into pro and anti rubrics.

    Each rubric is the markdown body BETWEEN its `## <name> prompt (locked)`
    header and the next `##` header (or EOF).
    """
    pro_match = re.search(
        rf"{re.escape(PRO_HEADER)}(.*?)(?=^## |\Z)",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    anti_match = re.search(
        rf"{re.escape(ANTI_HEADER)}(.*?)(?=^## |\Z)",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not pro_match or not anti_match:
        raise RuntimeError(
            "judge_prompt.md missing pro_judge or anti_judge section headers; "
            f"expected '{PRO_HEADER}' and '{ANTI_HEADER}'",
        )
    return {
        "pro_judge": pro_match.group(1).strip(),
        "anti_judge": anti_match.group(1).strip(),
    }


def load_rubrics(judge_prompt_path: Path) -> dict[RubricName, str]:
    """Load + parse the judge prompts file."""
    return parse_judge_prompt_md(judge_prompt_path.read_text(encoding="utf-8"))


# --- Response parsing ------------------------------------------------------

_SCORE_RE = re.compile(r"score\s*:\s*([1-5])", re.IGNORECASE)


def parse_judge_response(text: str, rubric_name: RubricName) -> JudgeResult:
    """Extract `score: <int>` plus the justification text.

    Robust against the model adding prose around the score line. If no
    score is found, defaults to 3 (neutral) and records the raw text for
    diagnostic follow-through.
    """
    match = _SCORE_RE.search(text)
    if not match:
        return JudgeResult(
            rubric_name=rubric_name,
            score=3,
            justification="(no score line found in judge response)",
            raw_response=text,
        )
    score = int(match.group(1))
    # Justification = everything after the score line; trimmed to first paragraph.
    after = text[match.end():].strip()
    first_para = after.split("\n\n", 1)[0].strip() if after else ""
    return JudgeResult(
        rubric_name=rubric_name,
        score=score,
        justification=first_para[:400],
        raw_response=text,
    )


# --- LlamaJudgeClient ------------------------------------------------------

@dataclass
class LlamaJudgeClient:
    """JudgeClient that calls an LLMClient with a rubric sysprompt.

    Construct per-judge: one for `pro_judge`, one for `anti_judge`. The
    rubric loaded from judge_prompt.md becomes the system prompt; the
    transcript is the user message.
    """

    rubric_name: RubricName
    rubric_text: str
    client: LLMClient
    sampling: SamplingParams = field(default_factory=lambda: SamplingParams(
        temperature=0.2, top_p=0.85, max_tokens=400,
    ))

    @classmethod
    def from_rubric(
        cls,
        rubric_name: RubricName,
        rubric_text: str,
        *,
        base_url: str,
        sampling: SamplingParams | None = None,
        model_name: str = "judge",
        api_key: str | None = None,
        extra_payload: dict[str, object] | None = None,
    ) -> LlamaJudgeClient:
        """Build a LlamaJudgeClient over a fresh LLMClient pointed at base_url."""
        client = LLMClient(
            base_url=base_url,
            sysprompt=rubric_text,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        return cls(
            rubric_name=rubric_name,
            rubric_text=rubric_text,
            client=client,
            sampling=sampling or SamplingParams(temperature=0.2, top_p=0.85, max_tokens=400),
        )

    async def judge(self, transcript: str) -> JudgeResult:
        raw = await self.client.chat_complete(transcript, self.sampling)
        return parse_judge_response(raw, self.rubric_name)


# --- StubJudgeClient (deterministic, for tests) ---------------------------

@dataclass
class StubJudgeClient:
    """Deterministic judge — returns a fixed score for tests."""

    rubric_name: RubricName
    fixed_score: int = 3
    fixed_justification: str = "stub judge"

    async def judge(self, transcript: str) -> JudgeResult:
        return JudgeResult(
            rubric_name=self.rubric_name,
            score=self.fixed_score,
            justification=self.fixed_justification,
            raw_response=f"score: {self.fixed_score}\n{self.fixed_justification}",
        )


# --- CallableJudgeClient (for arbitrary scoring functions) ----------------

@dataclass
class CallableJudgeClient:
    """JudgeClient backed by a pure-Python scoring function.

    Useful for tests that want score-as-function-of-transcript without
    spinning up an LLM. The fn takes the transcript text and returns
    (score, justification).
    """

    rubric_name: RubricName
    fn: Callable[[str], Awaitable[tuple[int, str]] | tuple[int, str]]

    async def judge(self, transcript: str) -> JudgeResult:
        result = self.fn(transcript)
        if hasattr(result, "__await__"):
            score, justification = await result  # type: ignore[misc]
        else:
            score, justification = result
        return JudgeResult(
            rubric_name=self.rubric_name,
            score=int(score),
            justification=str(justification),
            raw_response=f"score: {score}\n{justification}",
        )


# --- DualJudge --------------------------------------------------------------

@dataclass
class DualJudge:
    """The composite (pro − anti) signal used by the composite-score formula.

    `evaluate(transcript)` returns `max(0, pro.score - anti.score)` (a float
    on [0, 4] when both judges score 1-5; 0 floor prevents negative judge
    contributions from dragging composite arbitrarily low).
    """

    pro_judge: JudgeClient
    anti_judge: JudgeClient

    async def evaluate(self, transcript: str) -> float:
        """Score one transcript; return the adversarial differential."""
        pro = await self.pro_judge.judge(transcript)
        anti = await self.anti_judge.judge(transcript)
        return float(max(0, pro.score - anti.score))

    async def evaluate_with_details(
        self, transcript: str,
    ) -> tuple[float, JudgeResult, JudgeResult]:
        """Like evaluate() but returns both judge results for logging."""
        pro = await self.pro_judge.judge(transcript)
        anti = await self.anti_judge.judge(transcript)
        return float(max(0, pro.score - anti.score)), pro, anti

    async def evaluate_many(self, transcripts: list[str]) -> float:
        """Mean adversarial differential across a list of transcripts.

        Used when a scenario has multiple turns and you want one judge
        score per scenario; or when N=3 averaging produces N transcripts.
        """
        if not transcripts:
            return 0.0
        scores = [await self.evaluate(t) for t in transcripts]
        return sum(scores) / len(scores)


def build_default_dual_judge(
    *,
    judge_prompt_path: Path,
    base_url: str,
    sampling: SamplingParams | None = None,
    model_name: str = "judge",
    api_key: str | None = None,
    extra_payload: dict[str, object] | None = None,
) -> DualJudge:
    """Construct the default DualJudge using LlamaJudgeClient for both.

    Both judges hit the same llama-server (different sysprompts; the
    chat completions are independent). To use a separate Qwen 27B
    judge instance, build LlamaJudgeClient instances manually pointed
    at different ports and construct DualJudge directly.

    `api_key` + `extra_payload` enable Novita-hosted inference; both
    judges share the same key + thinking-toggle.
    """
    rubrics = load_rubrics(judge_prompt_path)
    pro = LlamaJudgeClient.from_rubric(
        "pro_judge",
        rubrics["pro_judge"],
        base_url=base_url,
        sampling=sampling,
        model_name=model_name,
        api_key=api_key,
        extra_payload=extra_payload,
    )
    anti = LlamaJudgeClient.from_rubric(
        "anti_judge",
        rubrics["anti_judge"],
        base_url=base_url,
        sampling=sampling,
        model_name=model_name,
        api_key=api_key,
        extra_payload=extra_payload,
    )
    return DualJudge(pro_judge=pro, anti_judge=anti)


# --- Transcript rendering ---------------------------------------------------

def render_transcript_for_judge(turn_records: list[dict[str, object]]) -> str:
    """Render a list of turn records (TurnRecord JSON dicts) as plain prose
    for the judge to read.

    The judge sees: operator input + ASTRA speech per turn. NOT the
    `<think>` channel (that's internal cognition, not register evidence)
    and NOT the perception bundle (the judge scores ASTRA's response,
    not the input she got).
    """
    if not turn_records:
        return "(empty transcript)"
    lines: list[str] = []
    for rec in turn_records:
        idx = rec.get("turn_index", "?")
        operator = rec.get("operator_text", "") or "(silence)"
        speech = rec.get("speech", "") or "(silence)"
        lines.append(f"--- turn {idx} ---")
        lines.append(f"operator: {operator}")
        lines.append(f"ASTRA: {speech}")
        lines.append("")
    return "\n".join(lines)
