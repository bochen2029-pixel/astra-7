"""Cross-run comparator — 6f.

The comparator exists to stop the bench claiming path effects from single
runs. Its own failure modes would be silent and would corrupt conclusions
rather than crash, so they are pinned here: arm mis-grouping (pooling runs
from different code revisions as replicates), overlap misread as
separation, and legacy artifacts without a run config.

`scripts/` is not importable as a package, so the module is loaded by path
the same way the bench's other script tests do it.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "compare_runs", SCRIPTS / "compare_runs.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["compare_runs"] = module
    spec.loader.exec_module(module)
    return module


cr = _load_module()


def _payload(
    *,
    narrator: bool,
    tool_valid: float,
    git_head: str | None = "abc1234",
    with_config: bool = True,
    passes: int = 1,
    tool_valid_fail_turns: int = 0,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "scenario": "s1",
        "passed": bool(passes),
        "turn_count": 3,
        "duration_s": 12.0,
        "gate_rates": {
            "grammar_parse": 1.0,
            "state_coherent": 0.9,
            "memory_coherent": 1.0,
            "non_degenerate": 1.0,
            "persona_stable": 0.98,
            "physics_ground": 0.9,
            "tool_valid": tool_valid,
            "no_leak": 0.91,
        },
    }
    if narrator:
        row["narrator_fallbacks"] = 1
    row["turn_records"] = [
        {"lcp_gates": {"tool_valid": {"passed": False, "detail": "x"}}}
        for _ in range(tool_valid_fail_turns)
    ]
    payload: dict[str, Any] = {
        "rows": [row],
        "drill": {"scenarios_run": ["p1"], "catches": [{"kind": "x"}, {"kind": "y"}]},
        "replay": [{"scenario": "a", "status": "match"}],
    }
    if with_config:
        payload["run_config"] = {
            "narrator": narrator,
            "narrator_thinking": "off" if narrator else None,
            "git_head": git_head,
        }
    return payload


def _write(tmp_path: Path, name: str, payload: dict[str, Any]) -> Path:
    d = tmp_path / name
    d.mkdir()
    (d / "results.json").write_text(json.dumps(payload), encoding="utf-8")
    return d


# --- arm identity ----------------------------------------------------------


def test_template_and_narrator_are_different_arms(tmp_path: Path) -> None:
    a = _write(tmp_path, "t1", _payload(narrator=False, tool_valid=0.88))
    b = _write(tmp_path, "n1", _payload(narrator=True, tool_valid=0.81))
    runs = cr.load_runs([a, b])
    assert len({r.arm for r in runs}) == 2


def test_different_code_revisions_do_not_pool_as_replicates(tmp_path: Path) -> None:
    """The confound this tool exists to prevent.

    Run #10 and run #11 shared a sampling config but straddled the F-LIVE-22
    fix; pooling them would have reported a state_coherent band of
    [0.052, 0.922] as if it were sampling noise.
    """
    a = _write(
        tmp_path, "before", _payload(narrator=True, tool_valid=0.81, git_head="aaaaaaa"),
    )
    b = _write(
        tmp_path, "after", _payload(narrator=True, tool_valid=0.85, git_head="bbbbbbb"),
    )
    runs = cr.load_runs([a, b])
    assert runs[0].arm != runs[1].arm


def test_same_revision_and_config_pools(tmp_path: Path) -> None:
    a = _write(tmp_path, "r1", _payload(narrator=True, tool_valid=0.81))
    b = _write(tmp_path, "r2", _payload(narrator=True, tool_valid=0.85))
    runs = cr.load_runs([a, b])
    assert runs[0].arm == runs[1].arm


def test_legacy_artifact_without_run_config_is_labelled_legacy(tmp_path: Path) -> None:
    a = _write(
        tmp_path, "old", _payload(narrator=True, tool_valid=0.88, with_config=False),
    )
    assert cr.load_runs([a])[0].arm == "narrator(legacy)"


def test_legacy_template_artifact_detected(tmp_path: Path) -> None:
    a = _write(
        tmp_path, "oldt", _payload(narrator=False, tool_valid=0.88, with_config=False),
    )
    assert cr.load_runs([a])[0].arm == "template(legacy)"


# --- the separation predicate ---------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ([0.80, 0.81, 0.82], [0.88, 0.89, 0.90], True),   # clean separation
        ([0.80, 0.85], [0.84, 0.90], False),              # overlap
        ([0.80], [0.80], False),                          # identical
        ([0.80, 0.95], [0.85], False),                    # b inside a's range
    ],
)
def test_separation_predicate(a: list[float], b: list[float], expected: bool) -> None:
    assert cr._separated(a, b) is expected


def test_separation_is_symmetric() -> None:
    lo, hi = [0.1, 0.2], [0.8, 0.9]
    assert cr._separated(lo, hi) == cr._separated(hi, lo)


# --- summary arithmetic ----------------------------------------------------


def test_drill_catches_counted_from_list_not_missing_property(tmp_path: Path) -> None:
    """catch_count is computed and does not survive model_dump()."""
    a = _write(tmp_path, "d1", _payload(narrator=False, tool_valid=0.9))
    assert cr.load_runs([a])[0].drill_catches == 2


def test_fallback_rate_uses_turn_denominator(tmp_path: Path) -> None:
    a = _write(tmp_path, "f1", _payload(narrator=True, tool_valid=0.9))
    run = cr.load_runs([a])[0]
    assert run.fallbacks == 1
    assert run.fallback_rate == pytest.approx(1 / 3)


def test_crashed_scenarios_excluded_from_gate_means(tmp_path: Path) -> None:
    payload = _payload(narrator=False, tool_valid=0.90)
    payload["rows"].append({"scenario": "boom", "error": "RuntimeError: x"})
    a = _write(tmp_path, "c1", payload)
    run = cr.load_runs([a])[0]
    assert run.crashed == 1
    assert run.gate_means["tool_valid"] == pytest.approx(0.90)


def test_report_renders_both_arms_and_a_verdict(tmp_path: Path) -> None:
    dirs = [
        _write(tmp_path, "t1", _payload(narrator=False, tool_valid=0.88)),
        _write(tmp_path, "t2", _payload(narrator=False, tool_valid=0.89)),
        _write(tmp_path, "n1", _payload(narrator=True, tool_valid=0.80)),
        _write(tmp_path, "n2", _payload(narrator=True, tool_valid=0.81)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "Range separation" in report
    assert "tool_valid" in report
    # 0.88-0.89 vs 0.80-0.81 do not overlap.
    assert "**YES**" in report


def test_sysprompt_change_splits_arms_at_the_same_revision(tmp_path: Path) -> None:
    """A sysprompt A/B shares a git_head by construction (6g).

    Without the sysprompt fingerprint the treatment arm would pool with its
    own control and the comparison would silently compare nothing.
    """
    ctrl = _payload(narrator=True, tool_valid=0.90)
    ctrl["run_config"]["narrator_sysprompt_sha"] = "aaaaaaaaaaaa"
    treat = _payload(narrator=True, tool_valid=0.94)
    treat["run_config"]["narrator_sysprompt_sha"] = "bbbbbbbbbbbb"
    runs = cr.load_runs(
        [_write(tmp_path, "ctrl", ctrl), _write(tmp_path, "treat", treat)],
    )
    assert runs[0].arm != runs[1].arm


def test_same_sysprompt_at_same_revision_pools(tmp_path: Path) -> None:
    a = _payload(narrator=True, tool_valid=0.90)
    a["run_config"]["narrator_sysprompt_sha"] = "aaaaaaaaaaaa"
    b = _payload(narrator=True, tool_valid=0.94)
    b["run_config"]["narrator_sysprompt_sha"] = "aaaaaaaaaaaa"
    runs = cr.load_runs([_write(tmp_path, "r1", a), _write(tmp_path, "r2", b)])
    assert runs[0].arm == runs[1].arm


def test_dirty_tree_is_a_distinct_arm_from_its_commit(tmp_path: Path) -> None:
    clean = _payload(narrator=True, tool_valid=0.90, git_head="abc1234")
    dirty = _payload(narrator=True, tool_valid=0.94, git_head="abc1234-dirty")
    runs = cr.load_runs(
        [_write(tmp_path, "clean", clean), _write(tmp_path, "dirty", dirty)],
    )
    assert runs[0].arm != runs[1].arm


def test_unrevisioned_run_beside_revisioned_raises_a_warning(tmp_path: Path) -> None:
    """The 6f trap: an excluded replicate narrows bands and fakes separation."""
    dirs = [
        _write(tmp_path, "n1", _payload(narrator=True, tool_valid=0.93)),
        _write(tmp_path, "n2", _payload(narrator=True, tool_valid=0.94)),
        _write(
            tmp_path, "old",
            _payload(narrator=True, tool_valid=0.81, with_config=False),
        ),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "Provenance warning" in report
    assert "REPLICATES" in report


def test_no_warning_when_every_run_is_revisioned(tmp_path: Path) -> None:
    dirs = [
        _write(tmp_path, "n1", _payload(narrator=True, tool_valid=0.93)),
        _write(tmp_path, "t1", _payload(narrator=False, tool_valid=0.83)),
    ]
    assert "Provenance warning" not in cr.build_report(cr.load_runs(dirs))


def test_separation_on_few_events_is_flagged_fragile(tmp_path: Path) -> None:
    """F-LIVE-30: an n=3 separation on a handful of failing turns flipped at n=6.

    The rate table alone made 10-vs-17 failing turns look like a clean
    result. Counts plus a warning are what stop that being recorded as
    established.
    """
    dirs = [
        _write(tmp_path, "t1", _payload(
            narrator=False, tool_valid=0.99, tool_valid_fail_turns=3)),
        _write(tmp_path, "n1", _payload(
            narrator=True, tool_valid=0.90, tool_valid_fail_turns=8)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "FRAGILE, few events" in report
    assert "Fragility warning" in report


def test_zero_event_arm_with_large_opposite_is_not_flagged(tmp_path: Path) -> None:
    """Absence is not a small sample — WHEN the opposite arm is large.

    The state_coherent closure went 24 failing turns to ZERO; that is a
    different kind of claim from 10-vs-17 and must not be diluted by the
    same warning.
    """
    dirs = [
        _write(tmp_path, "t1", _payload(
            narrator=False, tool_valid=0.99, tool_valid_fail_turns=0)),
        _write(tmp_path, "n1", _payload(
            narrator=True, tool_valid=0.90, tool_valid_fail_turns=24)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "Fragility warning" not in report


def test_zero_vs_few_events_is_flagged_fragile(tmp_path: Path) -> None:
    """6j audit fix: the original min>0 criterion exempted every zero arm,
    so a 0-vs-2-event 'separation' — two turns of noise — passed silently.
    Max-based catches it while leaving 0-vs-24 alone."""
    dirs = [
        _write(tmp_path, "t1", _payload(
            narrator=False, tool_valid=0.999, tool_valid_fail_turns=0)),
        _write(tmp_path, "n1", _payload(
            narrator=True, tool_valid=0.90, tool_valid_fail_turns=2)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "FRAGILE, few events" in report


def test_single_run_arm_raises_a_warning(tmp_path: Path) -> None:
    """A band of n=1 is a point; separation against a point is a single-run
    delta wearing a replicated result's clothes."""
    dirs = [
        _write(tmp_path, "t1", _payload(narrator=False, tool_valid=0.99)),
        _write(tmp_path, "n1", _payload(narrator=True, tool_valid=0.90)),
        _write(tmp_path, "n2", _payload(narrator=True, tool_valid=0.91)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "Single-run arm warning" in report


def test_no_single_run_warning_when_both_arms_replicated(tmp_path: Path) -> None:
    dirs = [
        _write(tmp_path, "t1", _payload(narrator=False, tool_valid=0.99)),
        _write(tmp_path, "t2", _payload(narrator=False, tool_valid=0.98)),
        _write(tmp_path, "n1", _payload(narrator=True, tool_valid=0.90)),
        _write(tmp_path, "n2", _payload(narrator=True, tool_valid=0.91)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "Single-run arm warning" not in report


# --- autotelic register extraction (6k) --------------------------------------


def _register_payload() -> dict[str, Any]:
    """Two heartbeats (one silent, one fidget), one answered operator turn,
    one em-dash in a bundle."""
    p = _payload(narrator=True, tool_valid=0.9)
    p["rows"][0]["metrics"] = {"budget_exceedances": 2}
    p["rows"][0]["turn_records"] = [
        {"turn_kind": "heartbeat", "speech": "", "tool_calls": [],
         "perception_bundle": "<state>quiet</state>", "lcp_gates": {}},
        {"turn_kind": "heartbeat", "speech": "", "tool_calls": [{"op": "x"}],
         "perception_bundle": "<state>drift — warm</state>", "lcp_gates": {}},
        {"turn_kind": "operator", "speech": "Here.", "tool_calls": [],
         "perception_bundle": "<state>ok</state>", "lcp_gates": {}},
    ]
    return p


def test_register_totals_extracted(tmp_path: Path) -> None:
    run = cr.load_runs([_write(tmp_path, "r1", _register_payload())])[0]
    reg = run.register
    assert reg["heartbeat_turns"] == 2
    assert reg["silence_rate"] == pytest.approx(0.5)
    assert reg["fidget_rate"] == pytest.approx(0.5)
    assert reg["initiation_rate"] == 0.0
    assert reg["response_rate"] == 1.0
    assert reg["budget_exceedances"] == 2.0
    assert reg["bundle_emdash_turns"] == 1.0   # the bleed vector
    assert reg["speech_emdash_turns"] == 0.0


def test_register_section_renders_with_separation_line(tmp_path: Path) -> None:
    dirs = [
        _write(tmp_path, "a1", _register_payload()),
        _write(tmp_path, "b1", _payload(narrator=False, tool_valid=0.9)),
    ]
    report = cr.build_report(cr.load_runs(dirs))
    assert "Autotelic register" in report
    assert "register separations:" in report


def test_gate_fail_events_counted_per_run(tmp_path: Path) -> None:
    a = _write(tmp_path, "r1", _payload(
        narrator=False, tool_valid=0.9, tool_valid_fail_turns=5))
    assert cr.load_runs([a])[0].gate_fail_events["tool_valid"] == 5


def test_missing_results_json_is_skipped_not_fatal(tmp_path: Path) -> None:
    empty = tmp_path / "nothing"
    empty.mkdir()
    good = _write(tmp_path, "g1", _payload(narrator=False, tool_valid=0.9))
    assert len(cr.load_runs([empty, good])) == 1
