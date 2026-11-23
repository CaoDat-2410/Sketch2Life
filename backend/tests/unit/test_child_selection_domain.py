"""FEAT-066 T-4b1: the pure rules of the Teacher random-child selection (offline).

SRS l.341, l.345-350, l.354, l.549, l.1447-1448, AC-56. Covers the candidate predicate statement
(as compiled SQL), the synthetic-only guards, the equal-probability pick, the evidence hash, the
authorization matrix (R1 F-7) and the total D5 table, every case a to h plus the sticky re-offer.
"""

from __future__ import annotations

import ast
import itertools
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.domain.lesson_occurrences import child_selection as domain
from sketch2life.domain.lesson_occurrences.child_selection import (
    Case,
    RowFacts,
    SelectionPolicy,
    candidate_set_hash,
    decide_child_data,
    decide_next,
    pick_child,
    reselect_available,
    selection_sha256,
    view_state,
)
from sketch2life.domain.lesson_occurrences.model import AccessOutcome, AssignmentFact
from sketch2life.infrastructure.lesson_occurrences import child_selection as infra

NOW = datetime(2026, 11, 21, 3, 0, tzinfo=UTC)
PLAN = "plan-1"
ME = "account-me"
HASH_A = "a" * 64
HASH_B = "b" * 64
SRC = Path(infra.__file__).resolve().parents[2]


def row(
    selection_id: str = "s1",
    *,
    kind: str = "DRAW",
    draw_no: int | None = 1,
    state: str = "OPEN",
    child: str | None = "c1",
    plan: str = PLAN,
    teacher: str = ME,
    set_hash: str = HASH_A,
    expires_in: int | None = 600,
    confirm_in: int | None = None,
) -> RowFacts:
    return RowFacts(
        selection_id=selection_id,
        kind=kind,
        draw_no=draw_no,
        state=state,
        child_ref=child,
        plan_revision_id=plan,
        teacher_ref=teacher,
        candidate_set_hash=set_hash,
        expires_at=None if expires_in is None else NOW + timedelta(seconds=expires_in),
        confirmation_expires_at=None if confirm_in is None else NOW + timedelta(seconds=confirm_in),
    )


def decide(
    *,
    live: RowFacts | None = None,
    anchor: RowFacts | None = None,
    latest: RowFacts | None = None,
    candidates: list[str] | None = None,
    candidate_hash: str = HASH_A,
    policy: SelectionPolicy | None = None,
    now: datetime = NOW,
) -> domain.Decision:
    return decide_next(
        live=live,
        anchor=anchor,
        latest=latest if latest is not None else (live or anchor),
        candidates=["c1", "c2"] if candidates is None else candidates,
        candidate_hash=candidate_hash,
        current_plan_revision_id=PLAN,
        caller_account_ref=ME,
        now=now,
        policy=policy or SelectionPolicy(),
    )


# ----------------------------------------------------------------------------- the D5 table
def test_case_c_first_time_empty_set_writes_an_empty_row() -> None:
    result = decide(candidates=[])
    assert result.case is Case.C_EMPTY_FIRST
    assert result.kind == "EMPTY" and result.coalesce_with is None and not result.pick


def test_empty_rows_coalesce_for_the_same_set_and_not_for_a_changed_one() -> None:
    empty = row("e1", kind="EMPTY", draw_no=None, state="EMPTY", child=None, expires_in=None)
    same = decide(candidates=[], latest=empty, candidate_hash=HASH_A)
    assert same.case is Case.C_EMPTY_FIRST and same.coalesce_with == "e1"
    changed = decide(candidates=[], latest=empty, candidate_hash=HASH_B)
    assert changed.coalesce_with is None and changed.kind == "EMPTY"


def test_case_d_first_draw_picks() -> None:
    result = decide(candidates=["c1", "c2", "c3"])
    assert result.case is Case.D_DRAW
    assert (result.kind, result.draw_no, result.pick) == ("DRAW", 1, True)
    assert result.transitions == ()


def test_case_a_returns_the_live_row_unchanged() -> None:
    live = row()
    result = decide(live=live, anchor=live)
    assert result.case is Case.A_RETURN_LIVE and result.return_row == "s1"
    assert result.transitions == ()
    confirmed = row("s9", state="CONFIRMED", confirm_in=300)
    assert decide(live=confirmed, anchor=confirmed).case is Case.A_RETURN_LIVE


def test_case_b_stale_live_row_becomes_stale_then_reselects_once() -> None:
    live = row(child="gone")
    result = decide(live=live, anchor=live)
    assert result.case is Case.F_RESELECT
    assert [(t.selection_id, t.new_state) for t in result.transitions] == [("s1", "STALE")]
    assert (result.kind, result.draw_no, result.pick) == ("RESELECT", 2, True)


def test_case_b_then_empty_set_writes_empty_and_keeps_the_reselect() -> None:
    live = row(child="gone")
    result = decide(live=live, anchor=live, candidates=[])
    assert result.case is Case.G_EMPTY and result.kind == "EMPTY"
    assert [(t.selection_id, t.new_state) for t in result.transitions] == [("s1", "STALE")]


def test_case_h_second_stale_stops_and_writes_nothing() -> None:
    second = row("s2", kind="RESELECT", draw_no=2, child="gone2")
    result = decide(live=second, anchor=second)
    assert result.case is Case.H_STOPPED
    assert result.kind is None and not result.pick and result.return_row is None
    assert [(t.selection_id, t.new_state) for t in result.transitions] == [("s2", "STALE")]
    # a stale second draw stays stopped even when new children appear (permanent, OPEN-3)
    stopped = decide(anchor=second, candidates=["x1", "x2", "x3"])
    assert stopped.case is Case.H_STOPPED


def test_case_e_expired_offer_reoffers_the_same_child() -> None:
    expired = row(state="EXPIRED")
    result = decide(anchor=expired)
    assert result.case is Case.E_REOFFER
    assert (result.kind, result.draw_no, result.reuse_child, result.pick) == (
        "REOFFER",
        1,
        "c1",
        False,
    )


def test_expiry_is_evaluated_not_swept() -> None:
    live = row(expires_in=-1)
    result = decide(live=live, anchor=live)
    assert [(t.selection_id, t.new_state) for t in result.transitions] == [("s1", "EXPIRED")]
    assert result.case is Case.E_REOFFER and result.reuse_child == "c1"
    boundary = row(expires_in=0)
    assert domain.is_past_due(boundary, NOW) is True
    confirmed_past = row("s5", state="CONFIRMED", confirm_in=-5)
    swept = decide(live=confirmed_past, anchor=confirmed_past)
    assert [(t.selection_id, t.new_state) for t in swept.transitions] == [("s5", "EXPIRED")]


def test_plan_reapproval_voids_the_live_row_and_reoffers_the_same_child() -> None:
    live = row(plan="plan-old")
    result = decide(live=live, anchor=live)
    assert [(t.selection_id, t.new_state) for t in result.transitions] == [("s1", "VOID")]
    assert result.case is Case.E_REOFFER and result.reuse_child == "c1"


def test_another_teachers_live_row_is_voided_and_the_caller_continues() -> None:
    live = row(teacher="account-other")
    result = decide(live=live, anchor=live)
    assert [(t.selection_id, t.new_state) for t in result.transitions] == [("s1", "VOID")]
    assert result.case is Case.E_REOFFER and result.reuse_child == "c1"


def test_consumed_row_of_a_cancelled_run_reoffers_the_same_child() -> None:
    consumed = row(state="CONSUMED")
    result = decide(anchor=consumed)
    assert result.case is Case.E_REOFFER and result.reuse_child == "c1" and result.draw_no == 1


def test_reoffer_keeps_the_anchors_draw_number() -> None:
    second = row("s2", kind="RESELECT", draw_no=2, child="c2", state="EXPIRED")
    result = decide(anchor=second)
    assert (result.kind, result.draw_no, result.reuse_child) == ("REOFFER", 2, "c2")


def test_withdrawn_child_after_expiry_goes_to_the_reselect() -> None:
    expired = row(state="EXPIRED", child="gone")
    result = decide(anchor=expired)
    assert result.case is Case.F_RESELECT and result.draw_no == 2 and result.pick


def test_the_cap_is_a_parameter() -> None:
    one = SelectionPolicy(max_draws=1)
    stale = row(child="gone")
    assert decide(live=stale, anchor=stale, policy=one).case is Case.H_STOPPED
    assert reselect_available(1, one) is False
    assert reselect_available(1, SelectionPolicy()) is True
    assert reselect_available(0, SelectionPolicy()) is False
    assert reselect_available(2, SelectionPolicy()) is False
    for bad in (0, 3, -1):
        with pytest.raises(ValueError):
            SelectionPolicy(max_draws=bad)
    with pytest.raises(ValueError):
        SelectionPolicy(open_ttl=timedelta(0))
    assert SelectionPolicy().max_draws == 2 and domain.DEFAULT_MAX_DRAWS == 2


def test_the_table_is_total_and_never_exceeds_the_cap() -> None:
    """Every combination lands in one case; at most one live row survives; the cap holds."""
    anchors: list[RowFacts | None] = [
        None,
        row("a1", state="EXPIRED"),
        row("a1", state="EXPIRED", child="gone"),
        row("a2", kind="RESELECT", draw_no=2, state="EXPIRED", child="c1"),
        row("a2", kind="RESELECT", draw_no=2, state="EXPIRED", child="gone"),
    ]
    lives: list[RowFacts | None] = [
        None,
        row("l1"),
        row("l1", child="gone"),
        row("l1", expires_in=-1),
        row("l1", plan="plan-old"),
        row("l1", teacher="account-other"),
        row("l1", state="CONFIRMED", confirm_in=100),
        row("l1", state="CONFIRMED", confirm_in=-1),
    ]
    sets: tuple[list[str], ...] = (["c1", "c2"], ["c2"], [])
    seen: set[Case] = set()
    for anchor, live, candidates, max_draws in itertools.product(anchors, lives, sets, (1, 2)):
        if live is not None and anchor is None:
            # a live row is itself a draw row: derive the anchor from it
            anchor = live
        policy = SelectionPolicy(max_draws=max_draws)
        result = decide(live=live, anchor=anchor, candidates=candidates, policy=policy)
        seen.add(result.case)
        survivors = {t.selection_id for t in result.transitions}
        returned = {result.return_row} if result.return_row else set()
        live_after = ({live.selection_id} - survivors if live else set()) | returned
        wrote_live = result.kind in {"DRAW", "RESELECT", "REOFFER"}
        assert len(live_after) + int(wrote_live) <= 1
        if result.return_row is not None:
            assert not wrote_live
        if result.kind in {"DRAW", "RESELECT"}:
            assert result.draw_no is not None and result.draw_no <= max_draws
        if result.kind == "REOFFER":
            assert anchor is not None
            assert result.reuse_child in candidates and result.draw_no == anchor.draw_no
        if result.pick:
            assert candidates
    assert seen == set(Case)


# ----------------------------------------------------------------------------- the pick
def _always(value: int) -> Callable[[int], int]:
    def generator(_bound: int) -> int:
        return value

    return generator


def test_pick_is_over_the_code_point_sorted_candidates_and_reaches_every_index() -> None:
    candidates = ["b", "a", "B", "c"]
    seen = {pick_child(candidates, _always(position)) for position in range(4)}
    assert seen == {"B", "a", "b", "c"}
    assert pick_child(candidates, lambda _bound: 0) == "B"  # code point order: "B" before "a"
    calls: list[int] = []

    def first(bound: int) -> int:
        calls.append(bound)
        return 0

    pick_child(candidates, first)
    assert calls == [4]


def test_pick_refuses_an_empty_set_and_a_wild_generator() -> None:
    with pytest.raises(ValueError):
        pick_child([], lambda n: 0)
    with pytest.raises(ValueError):
        pick_child(["a"], lambda n: 1)
    with pytest.raises(ValueError):
        pick_child(["a"], lambda n: -1)


def test_pick_is_uniform_with_the_real_generator() -> None:
    import secrets

    counts = {"a": 0, "b": 0, "c": 0}
    for _ in range(3000):
        counts[pick_child(["a", "b", "c"], secrets.randbelow)] += 1
    assert all(800 < value < 1200 for value in counts.values())


# ----------------------------------------------------------------------------- the evidence hash
def test_candidate_set_hash_is_stable_order_free_and_scope_sensitive() -> None:
    base = dict(organization_ref="org", class_ref="cls", plan_revision_id="p1")
    first = candidate_set_hash(**base, children=["b", "a"])
    assert first == candidate_set_hash(**base, children=["a", "b"])
    assert re.fullmatch(r"[0-9a-f]{64}", first)
    assert first != candidate_set_hash(**base, children=["a", "b", "c"])
    assert first != candidate_set_hash(**{**base, "plan_revision_id": "p2"}, children=["a", "b"])
    assert first != candidate_set_hash(**{**base, "class_ref": "c2"}, children=["a", "b"])
    assert first != candidate_set_hash(**{**base, "organization_ref": "o2"}, children=["a", "b"])
    assert candidate_set_hash(**base, children=[]) != first


def test_the_evidence_functions_take_opaque_refs_only() -> None:
    import inspect

    forbidden = ("name", "age", "seed", "index", "random", "draw_index")
    for function in (candidate_set_hash, selection_sha256, decide_next, pick_child):
        for parameter in inspect.signature(function).parameters:
            assert not any(word in parameter for word in forbidden), (function, parameter)


def test_selection_sha256_binds_every_field() -> None:
    base = dict(
        selection_id="s1",
        occurrence_id="o1",
        plan_revision_id="p1",
        plan_hash=HASH_A,
        selected_child_ref="c1",
        candidate_set_hash=HASH_B,
        policy_version=domain.POLICY_VERSION,
    )
    reference = selection_sha256(**base)
    assert re.fullmatch(r"[0-9a-f]{64}", reference)
    for field, other in (
        ("selection_id", "s2"),
        ("occurrence_id", "o2"),
        ("plan_revision_id", "p2"),
        ("plan_hash", HASH_B),
        ("selected_child_ref", "c2"),
        ("candidate_set_hash", HASH_A),
        ("policy_version", "other-v2"),
    ):
        assert selection_sha256(**{**base, field: other}) != reference, field


# ----------------------------------------------------------------------------- views
def test_view_state_computes_without_writing() -> None:
    live = row()
    assert view_state(live, now=NOW, child_is_eligible=True) == "OPEN"
    assert view_state(live, now=NOW, child_is_eligible=False) == "STALE"
    assert view_state(row(expires_in=-1), now=NOW, child_is_eligible=True) == "EXPIRED"
    confirmed = row(state="CONFIRMED", confirm_in=10)
    assert view_state(confirmed, now=NOW, child_is_eligible=True) == "CONFIRMED"
    assert (
        view_state(confirmed, now=NOW + timedelta(seconds=11), child_is_eligible=True) == "EXPIRED"
    )
    assert view_state(row(state="CONSUMED"), now=NOW, child_is_eligible=False) == "CONSUMED"
    assert view_state(row(state="VOID"), now=NOW, child_is_eligible=True) == "VOID"


def test_etag_helpers() -> None:
    assert domain.etag_for_revision(3) == '"3"'
    assert domain.if_none_match_matches('"3"', 3) is True
    assert domain.if_none_match_matches('"2", "3"', 3) is True
    assert domain.if_none_match_matches("*", 3) is True
    assert domain.if_none_match_matches('"4"', 3) is False
    assert domain.if_none_match_matches(None, 3) is False


def test_only_immutable_stored_states_may_answer_not_modified() -> None:
    """T4B1-IR-01: a live row's view state is computed at read time, so its ETag cannot be 304."""
    assert {"CONSUMED", "EXPIRED", "STALE", "VOID", "EMPTY"} == domain.IMMUTABLE_STATES
    assert domain.IMMUTABLE_STATES.isdisjoint(domain.LIVE_STATES)
    assert set(domain.STORED_STATES) == domain.IMMUTABLE_STATES | domain.LIVE_STATES


def test_audit_actions_are_named_and_hold_no_child_text() -> None:
    assert set(domain.AUDIT_ACTIONS) == {"DRAW", "RESELECT", "REOFFER", "EMPTY", "CONFIRM"}
    for action in domain.AUDIT_ACTIONS.values():
        assert action.startswith("lesson.occurrence.child_selection.")


# ----------------------------------------------------------------------------- authorization
T = AssignmentFact
CLS = "class-1"
OTHER = "account-other"


@pytest.mark.parametrize(
    ("rows", "caller", "expected"),
    [
        ([], ME, AccessOutcome.NOT_FOUND),
        ([T("teacher", "class-2")], ME, AccessOutcome.NOT_FOUND),
        ([T("guide", "class-2"), T("observer", "class-3")], ME, AccessOutcome.NOT_FOUND),
        ([T("teacher", CLS)], ME, AccessOutcome.PROCEED),
        ([T("teacher", CLS), T("guide", None)], ME, AccessOutcome.PROCEED),
        ([T("teacher", CLS)], OTHER, AccessOutcome.FORBIDDEN),
        ([T("teacher", None)], ME, AccessOutcome.FORBIDDEN),
        ([T("guide", CLS)], ME, AccessOutcome.FORBIDDEN),
        ([T("observer", CLS)], ME, AccessOutcome.FORBIDDEN),
        ([T("observer", CLS), T("teacher", "class-2")], ME, AccessOutcome.FORBIDDEN),
        ([T("guide", None)], ME, AccessOutcome.FORBIDDEN),
    ],
)
def test_decide_child_data_matrix(
    rows: list[AssignmentFact], caller: str, expected: AccessOutcome
) -> None:
    assert (
        decide_child_data(rows, CLS, caller_account_ref=caller, responsible_teacher_ref=ME)
        is expected
    )


# ----------------------------------------------------------------------------- the predicate
def _compiled() -> str:
    statement = infra.candidate_statement("org-1", "class-1")
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled: Any = statement.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)


def test_candidate_statement_selects_synthetic_origin_only() -> None:
    sql = _compiled()
    assert "data_origin = 'SYNTHETIC_DEV'" in sql
    for word in ("'REAL'", "'LEGACY_UNCLASSIFIED'"):
        assert word not in sql
    assert "age_months BETWEEN 36 AND 120" in sql
    assert "be1_enrollments.state = 'active'" in sql
    assert "be1_managed_profiles.state = 'active'" in sql
    assert "be1_classrooms.state = 'active'" in sql
    assert "NOT (EXISTS" in sql and "request_type = 'delete'" in sql
    assert "state != 'completed'" in sql or "state <> 'completed'" in sql
    assert "consent" not in sql.lower()
    assert "ORDER BY be1_managed_profiles.child_id" in sql


def test_the_real_origin_never_appears_in_the_selection_source() -> None:
    for relative in (
        "infrastructure/lesson_occurrences/child_selection.py",
        "domain/lesson_occurrences/child_selection.py",
    ):
        text = (SRC / relative).read_text(encoding="utf-8")
        assert not re.search(r"""['"]REAL['"]""", text), relative
        assert "consent_is_effective" not in text and "ConsentRecordModel" not in text
    assert domain.SYNTHETIC_ORIGIN == "SYNTHETIC_DEV" == domain.ELIGIBILITY_BASIS
    assert (domain.MIN_AGE_MONTHS, domain.MAX_AGE_MONTHS) == (36, 120)


@pytest.mark.parametrize(
    ("env", "flag", "expected"),
    [
        ("local", True, True),
        ("test", True, True),
        ("local", False, False),
        ("test", False, False),
        ("staging", True, False),
        ("production", True, False),
        ("local", "yes", False),
    ],
)
def test_the_synthetic_gate_follows_the_parent_runtime_condition(
    env: str, flag: Any, expected: bool
) -> None:
    settings = SimpleNamespace(env=env, synthetic_pilot_enabled=flag)
    assert infra.synthetic_gate_from_settings(settings).enabled is expected


class _NoDatabase:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"the gate is off: no database access ({name})")


def test_gate_off_gives_an_empty_set_without_touching_the_database() -> None:
    service = infra.ChildSelectionService(_NoDatabase(), gate=infra.SyntheticGate(False))  # type: ignore[arg-type]
    occurrence: Any = {"organization_ref": "org", "class_ref": "cls"}
    assert service._candidates(occurrence) == []


def test_the_purge_function_has_no_caller_in_the_source_tree() -> None:
    """OPEN-1: built and unwired; the FR-C-10 executor does not exist at HEAD."""
    callers = [
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if "purge_child_selections" in path.read_text(encoding="utf-8")
    ]
    assert callers == ["infrastructure/lesson_occurrences/child_selection.py"]
    assert infra.PURGE_FLAG == "sketch2life.child_selection_purge"


def _code_words(path: Path) -> set[str]:
    """Identifiers, attributes and string constants of a module, without docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
    }
    words: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            words.add(node.id)
        elif isinstance(node, ast.Attribute):
            words.add(node.attr)
        elif isinstance(node, (ast.arg, ast.keyword)) and node.arg is not None:
            words.add(node.arg)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            words.add(node.value)
    return words


def test_the_service_never_stores_or_logs_the_draw() -> None:
    for relative in (
        "infrastructure/lesson_occurrences/child_selection.py",
        "domain/lesson_occurrences/child_selection.py",
    ):
        words = _code_words(SRC / relative)
        assert not {word for word in words if "seed" in word.lower()}, relative
        assert not {word for word in words if "draw_index" in word or word == "index"}, relative
        assert not words & {"logging", "logger", "print", "getLogger"}, relative
