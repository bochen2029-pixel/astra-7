"""Pydantic models for persona-test records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PersonaTurnRecord(BaseModel):
    """One turn's record in the persona-test research log."""

    model_config = ConfigDict(frozen=True)

    timestamp: str
    variation_id: str
    scenario_id: str
    sysprompt_hash: str             # SHA-256 first 12 chars
    turn_index: int
    user_input: str
    raw_output: str
    think_emitted: bool
    think_content: str = ""
    speech_content: str = ""

    # Evaluation metrics (filled by evaluator)
    think_length_chars: int = 0
    speech_length_chars: int = 0
    think_mechanism_refs: int = 0
    think_mechanism_ref_terms: list[str] = Field(default_factory=list)
    speech_mechanism_refs: int = 0
    speech_mechanism_ref_terms: list[str] = Field(default_factory=list)
    speech_em_dash_count: int = 0
    speech_service_phrase_count: int = 0
    speech_service_phrases: list[str] = Field(default_factory=list)
    think_first_person_ratio: float = 0.0
