"""CalculatorBoundValidator — spec v0.128 §15.6 made operational.

Every numerical claim in operator-facing speech must trace to a tool-call
result observed in the same turn or in the perception bundle. Numbers that
don't trace are flagged. The validator is wrapped around every LLM client
by default; bypass requires an explicit debug flag.

Per spec §15.6:
> A numeric token is any digit sequence except whitelisted patterns (watch
> numbers, deck numbers, regime hex values).

On validation failure:
- severity 'soft': log drift, allow turn to proceed
- severity 'hard': reject output, retry with stricter sampling (temperature
  halved). After 3 retries: emit explicit failure to State Bus, mark turn
  as LCP-fail-gate-2.

Day 4 lands the validator surface. Retry policy is wired here; the
orchestrator (Day 5) decides when to fail the turn vs degrade gracefully.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Whitelisted patterns that DON'T need to trace to a tool result.
# Per spec §15.6: watch numbers, deck numbers, regime hex values.
WHITELIST_PATTERNS: tuple[str, ...] = (
    r"\bwatch\s+\d+\b",         # "watch 47"
    r"\bcycle\s+\d+\b",         # "cycle 46"
    r"\bdeck\s+\d+\b",          # "deck 3"
    r"\b0x[0-9A-Fa-f]+\b",      # hex literal "0x08"
    r"\bASTRA-\d+\b",           # ship designation "ASTRA-7"
    r"\bserial\s+\d+\b",        # "serial 7"
)

# Number-word forms exempt from the digit-token check.
# These are prose-spelled small integers used naturally in English.
NUMBER_WORDS: frozenset[str] = frozenset({
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "first", "second", "third", "fourth", "fifth",
})

# A "numeric token" by default is any digit sequence (with optional decimal,
# optional sign, optional scientific notation). Matched in speech text.
DIGIT_TOKEN_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z])[+\-]?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?",
)

Severity = Literal["soft", "hard"]


class UngroundedNumber(BaseModel):
    """One numeric token in speech that didn't trace to a tool result."""

    model_config = ConfigDict(frozen=True)

    token: str
    span: tuple[int, int]


class ValidationReport(BaseModel):
    """Result of validating one speech string against the trace pool."""

    model_config = ConfigDict(frozen=True)

    ungrounded: list[UngroundedNumber] = Field(default_factory=list)
    grounded: list[str] = Field(default_factory=list)
    severity: Severity = "soft"

    @property
    def passed(self) -> bool:
        return not self.ungrounded


def _compile_whitelist() -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in WHITELIST_PATTERNS]


_WHITELIST = _compile_whitelist()


def _strip_whitelist_regions(text: str) -> str:
    """Replace whitelisted regions with spaces so digit-token scan ignores them."""
    cleaned = text
    for regex in _WHITELIST:
        cleaned = regex.sub(lambda m: " " * (m.end() - m.start()), cleaned)
    return cleaned


def _build_trace_strings(trace_pool: Iterable[str]) -> str:
    """Concatenate the tool-result trace pool into one searchable string."""
    return "\n".join(trace_pool)


def find_ungrounded_numerics(
    speech: str,
    trace_pool: Iterable[str],
) -> list[UngroundedNumber]:
    """Find digit tokens in `speech` that don't appear in `trace_pool`.

    `trace_pool` is the set of strings (tool-call results, perception bundle
    content) where ASTRA could legitimately have read numbers. Any digit
    token in speech that's also in the pool is considered grounded.

    Whitelist regions ('watch 47', 'cycle 46', '0x08', etc.) are masked
    before scanning so they never produce ungrounded events.
    """
    cleaned = _strip_whitelist_regions(speech)
    pool_text = _build_trace_strings(trace_pool)
    ungrounded: list[UngroundedNumber] = []
    for match in DIGIT_TOKEN_RE.finditer(cleaned):
        token = match.group(0)
        # The token must appear literally in the trace pool to be grounded.
        if token not in pool_text:
            ungrounded.append(
                UngroundedNumber(token=token, span=match.span())
            )
    return ungrounded


def validate_speech(
    speech: str,
    trace_pool: Iterable[str],
    *,
    severity: Severity = "soft",
) -> ValidationReport:
    """Validate that every numeric in `speech` traces to `trace_pool`.

    Returns a ValidationReport. The orchestrator decides retry policy
    based on `report.passed` and `severity`.
    """
    pool_list = list(trace_pool)
    ungrounded = find_ungrounded_numerics(speech, pool_list)
    pool_text = _build_trace_strings(pool_list)
    grounded: list[str] = []
    cleaned = _strip_whitelist_regions(speech)
    for match in DIGIT_TOKEN_RE.finditer(cleaned):
        if match.group(0) in pool_text and match.group(0) not in {u.token for u in ungrounded}:
            grounded.append(match.group(0))
    return ValidationReport(
        ungrounded=ungrounded,
        grounded=grounded,
        severity=severity,
    )


class CalculatorBoundValidator:
    """Wraps a speech string + trace pool into pass/fail + retry guidance.

    The orchestrator calls `validate(speech, trace_pool)` after each ASTRA
    turn. On soft failure: log drift, proceed. On hard failure: trigger
    retry with halved temperature; after 3 retries, mark turn LCP-fail-2.
    """

    def __init__(
        self,
        *,
        severity: Severity = "soft",
        max_retries: int = 3,
        temperature_halving_factor: float = 0.5,
    ) -> None:
        self.severity = severity
        self.max_retries = max_retries
        self.temperature_halving_factor = temperature_halving_factor

    def validate(
        self,
        speech: str,
        trace_pool: Iterable[str],
    ) -> ValidationReport:
        return validate_speech(speech, trace_pool, severity=self.severity)

    def next_temperature(self, current: float, retry_count: int) -> float:
        """Suggest the next sampling temperature for a retry.

        Strategy: halve temperature each retry until floor of 0.05. Lower
        temperature reduces hallucination probability without forcing a
        deterministic loop.
        """
        if retry_count <= 0:
            return current
        return max(0.05, current * (self.temperature_halving_factor**retry_count))
