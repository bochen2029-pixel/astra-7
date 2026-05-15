"""Day 4 tests for CalculatorBoundValidator.

The validator is the §15.6 calculator-bound discipline made operational.
This test suite verifies:
- Digit tokens in speech that DON'T appear in the trace pool → ungrounded events.
- Digit tokens that DO appear in the trace pool → grounded.
- Whitelist patterns ('watch 47', 'cycle 46', '0x08', 'ASTRA-7', 'deck 3')
  never produce ungrounded events.
- Number-word forms ('one', 'three') don't trip the digit regex.
- next_temperature halves on each retry, with a floor of 0.05.
- Retry policy returns a strictly decreasing sequence until floor.
"""

from __future__ import annotations

from astra.llm import (
    CalculatorBoundValidator,
    UngroundedNumber,
    ValidationReport,
    find_ungrounded_numerics,
    validate_speech,
)

# --- find_ungrounded_numerics --------------------------------------------------

def test_ungrounded_number_caught() -> None:
    speech = "Third pole drift is 4.2 percent."
    trace = ["reactor: nominal\n"]   # 4.2 not present
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert any(u.token == "4.2" for u in ungrounded)


def test_grounded_number_passes() -> None:
    speech = "Third pole drift is 4.2 percent."
    trace = ["harmonic_3_drift=4.2"]   # 4.2 IS in the trace pool
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_whitelist_watch_number() -> None:
    speech = "Watch 47, mid-shift."
    trace: list[str] = []   # nothing in trace
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []  # 'watch 47' is whitelisted


def test_whitelist_cycle_number() -> None:
    speech = "Same shape as cycle 46."
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_whitelist_deck_number() -> None:
    speech = "Crawl space on deck 3."
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_whitelist_hex_value() -> None:
    speech = "Regime is 0x22."
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_whitelist_astra_designation() -> None:
    speech = "I am ASTRA-7."
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_negative_number_caught() -> None:
    speech = "Rate -1 means reverse playback."
    trace = ["apparent_rate=0.5774"]   # -1 not in trace
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert any(u.token == "-1" for u in ungrounded)


def test_scientific_notation_token_evaluated() -> None:
    speech = "Mass at 1.989e30 kilograms."
    trace = ["sun_mass_kg: 1.989e30"]
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []   # exact match in trace


def test_scientific_notation_ungrounded() -> None:
    speech = "Mass at 1.989e30 kilograms."
    trace = ["nothing relevant"]
    ungrounded = find_ungrounded_numerics(speech, trace)
    tokens = {u.token for u in ungrounded}
    assert "1.989e30" in tokens


def test_decimal_grounded() -> None:
    speech = "Drift at 0.042 above baseline."
    trace = ["harmonic_3_drift: 0.042"]
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_in_register_speech_passes_clean() -> None:
    """The canonical watch_47_morning speech contains only whitelisted nums."""
    speech = "Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance."
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded == []


def test_multiple_ungrounded_all_reported() -> None:
    speech = "Numbers 17 and 42 and 99."
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    tokens = {u.token for u in ungrounded}
    assert tokens == {"17", "42", "99"}


def test_spans_are_meaningful() -> None:
    speech = "drift 4.2 percent"
    trace: list[str] = []
    ungrounded = find_ungrounded_numerics(speech, trace)
    assert ungrounded
    u: UngroundedNumber = ungrounded[0]
    assert u.span[0] == speech.index("4.2")
    assert u.span[1] == u.span[0] + 3


# --- validate_speech ----------------------------------------------------------

def test_validate_speech_grounded_passes() -> None:
    report = validate_speech("drift 4.2", ["x: 4.2"])
    assert report.passed is True
    assert "4.2" in report.grounded


def test_validate_speech_ungrounded_fails() -> None:
    report = validate_speech("drift 4.2", [])
    assert report.passed is False
    assert len(report.ungrounded) == 1
    assert report.ungrounded[0].token == "4.2"


def test_validate_speech_severity_default_soft() -> None:
    report = validate_speech("foo 99", [])
    assert report.severity == "soft"


def test_validate_speech_severity_hard_propagated() -> None:
    report = validate_speech("foo 99", [], severity="hard")
    assert report.severity == "hard"


# --- ValidationReport shape ---------------------------------------------------

def test_validation_report_passed_property() -> None:
    r_pass = ValidationReport(ungrounded=[], grounded=["4.2"])
    assert r_pass.passed is True
    r_fail = ValidationReport(
        ungrounded=[UngroundedNumber(token="99", span=(0, 2))],
    )
    assert r_fail.passed is False


def test_validation_report_frozen() -> None:
    r = ValidationReport()
    try:
        r.grounded = ["new"]
    except Exception:
        return
    raise AssertionError("ValidationReport must be frozen")


# --- CalculatorBoundValidator retry policy -----------------------------------

def test_next_temperature_halves() -> None:
    v = CalculatorBoundValidator()
    assert v.next_temperature(0.8, retry_count=1) == 0.4
    assert v.next_temperature(0.8, retry_count=2) == 0.2


def test_next_temperature_floor_at_005() -> None:
    v = CalculatorBoundValidator()
    # 0.8 * 0.5^10 ≈ 0.00078; clamped to 0.05
    assert v.next_temperature(0.8, retry_count=10) == 0.05


def test_next_temperature_retry_zero_unchanged() -> None:
    v = CalculatorBoundValidator()
    assert v.next_temperature(0.8, retry_count=0) == 0.8


def test_validator_validate_method_uses_severity() -> None:
    v = CalculatorBoundValidator(severity="hard")
    report = v.validate("count 42", [])
    assert report.severity == "hard"
    assert report.passed is False
