"""Internal candidate SQL shape/cursor tests, not permission or actual database execution."""

from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect

from sketch2life.contracts.schemas.ai_policy_copy_candidates import (
    CopyCandidateCursor,
    CopyCandidateRequest,
)
from sketch2life.domain.ai_policy.model import PolicyError
from tests.unit.test_ai_policy_copy_operation_pages import transaction
from tests.unit.test_ai_policy_domain import NOW


def request(**changes):
    return CopyCandidateRequest.model_validate(dict(limit=2, as_of=NOW) | changes)


def test_candidates_query_binds_scope_cutoff_statuses_and_bounded_join():
    tx, queries = transaction(("a" * 64, "b" * 64, "c" * 64))
    page = tx.delivery_candidates(request())
    assert page.operation_keys == ("a" * 64, "b" * 64)
    assert page.next_cursor.revision == 7 and page.next_cursor.as_of == NOW
    compiled = queries[0].compile(dialect=dialect())
    sql = str(compiled)
    assert "LEFT OUTER JOIN" in sql and "LIMIT" in sql and "ORDER BY" in sql
    assert "TIMESTAMP WITH TIME ZONE" in sql and "IS NULL" in sql
    assert "school" in compiled.params.values() and "scope" in compiled.params.values()
    assert NOW in compiled.params.values()
    assert any(value == ["pending", "exception"] for value in compiled.params.values())
    assert "unsupported" not in sql and "receipt_available" not in sql


def test_continuation_pins_cutoff_and_scope_revision_even_if_wall_clock_changes():
    tx, _ = transaction(("a" * 64, "b" * 64, "c" * 64))
    first = tx.delivery_candidates(request())
    tx.connection = transaction(("c" * 64,))[0].connection
    last = tx.delivery_candidates(CopyCandidateRequest(limit=2, cursor=first.next_cursor))
    assert last.as_of == first.as_of and last.operation_keys == ("c" * 64,)
    assert last.next_cursor is None
    with pytest.raises(ValidationError):
        CopyCandidateRequest(limit=2, cursor=first.next_cursor, as_of=NOW + timedelta(seconds=1))


@pytest.mark.parametrize(
    "changes",
    [
        {"limit": True},
        {"limit": 0},
        {"limit": 257},
        {"as_of": None},
        {"as_of": NOW.replace(tzinfo=None)},
        {"cursor": {}},
        {"verified": True},
    ],
)
def test_candidate_request_rejects_unbounded_naive_or_asserted_authority(changes):
    with pytest.raises(ValidationError):
        request(**changes)


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"organization_id": "other"}, "AI_POLICY_COPY_SCOPE_MISMATCH"),
        ({"scope_ref": "other"}, "AI_POLICY_COPY_SCOPE_MISMATCH"),
        ({"revision": 6}, "AI_POLICY_COPY_REGISTRY_STALE"),
    ],
)
def test_wrong_scope_or_stale_cursor_rejected_before_query(changes, code):
    tx, queries = transaction()
    cursor = CopyCandidateCursor(
        organization_id="school", scope_ref="scope", revision=7, as_of=NOW, after="a" * 64
    ).model_copy(update=changes)
    with pytest.raises(PolicyError, match=code):
        tx.delivery_candidates(CopyCandidateRequest(limit=2, cursor=cursor))
    assert not queries


def test_missing_scope_read_does_not_mix_post_absence_candidates():
    tx, queries = transaction(("a" * 64,), exists=False)
    page = tx.delivery_candidates(request())
    assert page.revision == 0 and page.as_of == NOW and not page.operation_keys
    assert not queries


@pytest.mark.parametrize("keys", [("bad",), (True,), ("c" * 64, "b" * 64), ("a" * 64, "a" * 64)])
def test_bad_persisted_candidate_keys_fail_closed(keys):
    tx, _ = transaction(keys)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION_STORAGE"):
        tx.delivery_candidates(request())


def test_constructed_native_request_and_cursor_are_revalidated_before_sql():
    tx, queries = transaction()
    bad = request().model_copy(update={"limit": True})
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_CANDIDATE_REQUEST"):
        tx.delivery_candidates(bad)
    assert not queries
