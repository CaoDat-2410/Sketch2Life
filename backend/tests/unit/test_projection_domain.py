"""FEAT-066 T-5a: the rules of the class projection confirmation (SRS l.396, l.552-555, l.777,
l.1449, l.1661-1662; OD-14), the request body, the receipt and two source scans.

Offline: no database, no network. The scans pin what the database cannot: no code path writes
``sample_slot_state = 'AVAILABLE'`` after creation (the trigger would allow it, T-5a OPEN-5), and
Lesson projection code reads Story through ONE function (``sample_facts``, R2 N-7).
"""

from __future__ import annotations

import ast
import re
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.lesson_occurrences import (
    ClassProjectionConfirmationV1,
    ProjectionConfirmationRequestV1,
)
from sketch2life.domain.lesson_occurrences import projection as rules

RUN = "1a1a1a1a-1a1a-4a1a-8a1a-1a1a1a1a1a1a"
OTHER_RUN = "22222222-2222-4222-8222-222222222222"
GENERATION = "33333333-3333-4333-8333-333333333333"
OCCURRENCE = "44444444-4444-4444-8444-444444444444"
T0 = datetime(2026, 11, 22, 10, 0, 0, 123456, tzinfo=UTC)
SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"


# ----------------------------------------------------------------------------- the request
def _body(**changes: Any) -> dict[str, Any]:
    return {
        "run_id": RUN,
        "generation_id": GENERATION,
        "audience": "CLASS",
        "use": "CLASS_PROJECTION",
        **changes,
    }


def test_the_request_accepts_exactly_the_two_literals_and_two_canonical_ids() -> None:
    request = ProjectionConfirmationRequestV1.model_validate(_body())
    assert (request.run_id, request.generation_id) == (RUN, GENERATION)
    for broken in (
        _body(audience="GROUP"),
        _body(audience="class"),
        _body(use="PROJECTION"),
        _body(use=None),
        _body(run_id="not-a-uuid"),
        _body(run_id=RUN.upper()),
        _body(generation_id=""),
        _body(extra="x"),
        {key: value for key, value in _body().items() if key != "audience"},
        {key: value for key, value in _body().items() if key != "use"},
    ):
        with pytest.raises(ValidationError):
            ProjectionConfirmationRequestV1.model_validate(broken)


def test_a_non_string_id_is_refused_in_strict_mode() -> None:
    for broken in (_body(run_id=1), _body(generation_id=["x"]), _body(audience=1)):
        with pytest.raises(ValidationError):
            ProjectionConfirmationRequestV1.model_validate(broken)


def test_the_fingerprint_names_the_revision_the_pair_and_the_two_literals() -> None:
    base: dict[str, Any] = {"expected_revision": 3, "run_id": RUN, "generation_id": GENERATION}
    first = rules.request_fingerprint(**base)
    assert first == rules.request_fingerprint(**base)
    assert re.fullmatch(r"[0-9a-f]{64}", first)
    assert first != rules.request_fingerprint(**{**base, "expected_revision": 4})
    assert first != rules.request_fingerprint(**{**base, "run_id": OTHER_RUN})
    assert first != rules.request_fingerprint(**{**base, "generation_id": OTHER_RUN})


# ----------------------------------------------------------------------------- time
def test_the_millisecond_truncation_is_exact_integer_arithmetic() -> None:
    assert rules.confirmed_ms(T0) == 1_795_341_600_123
    assert rules.confirmed_ms(T0.replace(microsecond=999_999)) == 1_795_341_600_999
    assert rules.confirmed_ms(T0.replace(microsecond=0)) == 1_795_341_600_000
    # a naive value is read as UTC; an offset value is converted, never shifted
    assert rules.confirmed_ms(T0.replace(tzinfo=None)) == rules.confirmed_ms(T0)
    plus_seven = datetime(2026, 11, 22, 17, 0, 0, 123456, tzinfo=timezone(timedelta(hours=7)))
    assert rules.confirmed_ms(plus_seven) == rules.confirmed_ms(T0)
    # the stored microsecond value and the token's millisecond number agree on both sides
    stored = T0.replace(microsecond=123_999)
    assert rules.confirmed_ms(stored) == rules.confirmed_ms(T0)


def test_a_confirmation_covers_a_generation_only_when_given_after_it_was_ready() -> None:
    ready = T0
    assert rules.confirmation_covers(ready, ready)
    assert rules.confirmation_covers(ready + timedelta(microseconds=1), ready)
    # a newer generation becomes ready later than the earlier confirmation: not covered
    assert not rules.confirmation_covers(ready, ready + timedelta(microseconds=1))
    assert not rules.confirmation_covers(None, ready)
    assert not rules.confirmation_covers(ready, None)
    # microseconds count: the millisecond truncation is for the token, not for coverage
    assert not rules.confirmation_covers(
        T0.replace(microsecond=123_100), T0.replace(microsecond=123_900)
    )


# ----------------------------------------------------------------------------- the claim
@pytest.mark.parametrize(
    ("slot", "pointer", "run", "expected"),
    [
        ("AVAILABLE", None, RUN, rules.ClaimDecision.FIRST_CLAIM),
        ("CLAIMED", RUN, RUN, rules.ClaimDecision.SAME_RUN),
        ("CLAIMED", OTHER_RUN, RUN, rules.ClaimDecision.REFUSED),
        # a deleted run clears the pointer and keeps the claim (SRS l.396): the slot stays used
        ("CLAIMED", None, RUN, rules.ClaimDecision.REFUSED),
        ("UNKNOWN", RUN, RUN, rules.ClaimDecision.REFUSED),
    ],
)
def test_the_slot_decision_table(
    slot: str, pointer: str | None, run: str, expected: rules.ClaimDecision
) -> None:
    assert rules.decide_claim(slot_state=slot, successful_run_ref=pointer, run_id=run) is expected


def test_the_write_decision_first_claim_noop_and_the_two_refreshes() -> None:
    ready = T0
    after = T0 + timedelta(seconds=5)
    common: dict[str, Any] = {"caller_account": "acc-a", "ready_at": ready}
    assert (
        rules.decide_write(
            rules.ClaimDecision.FIRST_CLAIM, confirmed_by=None, confirmed_at=None, **common
        )
        is rules.WriteKind.CLAIM
    )
    # the same Teacher, the same generation: nothing is written (R2 N-5)
    assert (
        rules.decide_write(
            rules.ClaimDecision.SAME_RUN, confirmed_by="acc-a", confirmed_at=after, **common
        )
        is rules.WriteKind.NONE
    )
    # another Teacher (after a reassignment) confirms again: the pair is rewritten
    assert (
        rules.decide_write(
            rules.ClaimDecision.SAME_RUN, confirmed_by="acc-b", confirmed_at=after, **common
        )
        is rules.WriteKind.REFRESH
    )
    # a newer generation became ready after the stored confirmation: rewritten
    assert (
        rules.decide_write(
            rules.ClaimDecision.SAME_RUN,
            confirmed_by="acc-a",
            confirmed_at=ready - timedelta(seconds=1),
            **common,
        )
        is rules.WriteKind.REFRESH
    )
    # no stored confirmation or no readiness time can never be a no-op
    for confirmed_by, confirmed_at, ready_at in (
        ("acc-a", None, ready),
        (None, after, ready),
        ("acc-a", after, None),
    ):
        assert (
            rules.decide_write(
                rules.ClaimDecision.SAME_RUN,
                confirmed_by=confirmed_by,
                confirmed_at=confirmed_at,
                caller_account="acc-a",
                ready_at=ready_at,
            )
            is rules.WriteKind.REFRESH
        )


def test_the_confirmable_states_all_hold_a_plan_pointer() -> None:
    assert {"APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"} == rules.CONFIRMABLE_STATES
    assert not rules.CONFIRMABLE_STATES & {"DRAFT", "DOCUMENT_REVIEW", "PLAN_REVIEW", "ARCHIVED"}


# ----------------------------------------------------------------------------- the plan pin
def _pin(**changes: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "pin_plan_revision_id": "plan-1",
        "pin_revision_no": 1,
        "pin_hash": "a" * 64,
        "plan_revision_id": "plan-1",
        "plan_revision_no": 1,
        "plan_hash": "a" * 64,
        "plan_state": "APPROVED",
    }
    return {**base, **changes}


def test_a_pin_that_names_an_approved_or_superseded_plan_of_the_occurrence_matches() -> None:
    assert rules.pin_matches_plan(**_pin())
    # SRS l.2697: the old READY output stays pinned to its old plan, which is now superseded
    assert rules.pin_matches_plan(**_pin(plan_state="SUPERSEDED"))
    for broken in (
        _pin(plan_state="DRAFT"),
        _pin(plan_state=None),
        _pin(pin_plan_revision_id=None),
        _pin(plan_revision_id="plan-2"),
        _pin(pin_revision_no=2),
        _pin(pin_revision_no=None),
        _pin(pin_hash="b" * 64),
        _pin(pin_hash=None),
        _pin(plan_revision_no=None),
    ):
        assert not rules.pin_matches_plan(**broken)


# ----------------------------------------------------------------------------- the receipt
def _facts(**changes: Any) -> rules.ReceiptFacts:
    base: dict[str, Any] = {
        "occurrence_id": OCCURRENCE,
        "run_id": RUN,
        "generation_id": GENERATION,
        "confirmed_at": T0,
        "confirmed_by_ref": "acc-a",
        "class_revision": 4,
        "plan_revision_no": 2,
        "plan_hash": "c" * 64,
        "plan_is_current": False,
        "occurrence_revision": 9,
        "slot_state": "CLAIMED",
        "claimed_at": T0,
        "slot_run_ref": RUN,
    }
    return rules.ReceiptFacts(**{**base, **changes})


def test_the_receipt_has_the_srs_shape_and_validates_against_the_contract() -> None:
    body = rules.receipt_body(_facts())
    assert set(body) == {
        "contract",
        "occurrence_id",
        "run_id",
        "generation_id",
        "audience",
        "use",
        "confirmed_at",
        "confirmed_by_ref",
        "assignment",
        "plan",
        "occurrence_revision",
        "sample_video",
    }
    assert body["contract"] == "ClassProjectionConfirmationV1"
    assert (body["audience"], body["use"]) == ("CLASS", "CLASS_PROJECTION")
    assert body["assignment"] == {"class_revision": 4}
    assert body["plan"] == {"revision_no": 2, "plan_hash": "c" * 64, "is_current": False}
    assert body["sample_video"] == {"slot_state": "CLAIMED", "claimed_at": T0, "run_ref": RUN}
    model = ClassProjectionConfirmationV1.model_validate(body)
    assert model.plan.is_current is False and model.occurrence_revision == 9


def test_the_receipt_carries_no_name_no_media_key_no_token_and_no_capability() -> None:
    text = repr(rules.receipt_body(_facts())).lower()
    for word in (
        "name",
        "token",
        "bucket",
        "key",
        "url",
        "storage",
        "capability",
        "seed",
        "child",
        "profile",
    ):
        assert word not in text, word
    fields = set(ClassProjectionConfirmationV1.model_fields)
    assert not {"token", "url", "child", "display_name", "asset_ref"} & fields


def test_the_audit_decision_texts_fit_the_column_and_name_the_literals_only() -> None:
    assert rules.AUDIT_CONFIRM_DECISION == "CLASS/CLASS_PROJECTION"
    assert len(rules.AUDIT_CONFIRM_DECISION) <= 64 and len(rules.AUDIT_CLAIM_DECISION) <= 64


# ----------------------------------------------------------------------------- source scans
def _python_sources() -> list[Path]:
    return sorted(path for path in SRC.rglob("*.py") if "__pycache__" not in path.parts)


def test_no_code_path_writes_the_slot_back_to_available_after_creation() -> None:
    """The one-way claim is a service rule: the trigger allows ``CLAIMED -> AVAILABLE`` (T-5a
    OPEN-5). No source line assigns ``sample_slot_state`` (a keyword, an attribute or SQL text)
    except the claim itself; the INSERT of an occurrence leaves the column to its server default."""

    writes = re.compile(r"sample_slot_state\s*=\s*(?!=)([^,)\s]+)")
    dict_writes = re.compile(r"[\"']sample_slot_state[\"']\s*:\s*([^,}\s]+)")
    found: list[tuple[str, str]] = []
    for path in _python_sources():
        text = path.read_text(encoding="utf-8")
        for pattern in (writes, dict_writes):
            for match in pattern.finditer(text):
                found.append((str(path.relative_to(SRC)).replace("\\", "/"), match.group(1)))
    assert found == [("infrastructure/lesson_occurrences/projection.py", "rules.SLOT_CLAIMED")], (
        found
    )
    # a SQL migration is not source of this package; the server default is the only other writer
    tables = (SRC / "infrastructure" / "lesson_occurrences" / "tables.py").read_text("utf-8")
    assert 'server_default="AVAILABLE"' in tables


def test_lesson_projection_code_imports_one_story_function_and_no_story_table() -> None:
    path = SRC / "infrastructure" / "lesson_occurrences" / "projection.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    story: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if "story" in node.module:
                for alias in node.names:
                    story.add((node.module, alias.name))
        elif isinstance(node, ast.Import):
            story.update((alias.name, "") for alias in node.names if "story" in alias.name)
    allowed = {
        ("sketch2life.application.ports.story_video", "SampleFacts"),
        ("sketch2life.infrastructure.story_video.repository", "sample_facts"),
    }
    assert story == allowed
    text = path.read_text(encoding="utf-8")
    assert "story_tables" not in text and "story_run_lite" not in text


def test_the_domain_module_imports_no_framework() -> None:
    tree = ast.parse((SRC / "domain" / "lesson_occurrences" / "projection.py").read_text("utf-8"))
    modules = {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not modules & {"fastapi", "pydantic", "sqlalchemy", "starlette"}
