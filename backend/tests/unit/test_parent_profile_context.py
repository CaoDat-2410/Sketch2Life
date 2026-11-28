"""FEAT-066 goal v4 T-12a: the entry rules, the v2 snapshot and the selection request (offline)."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.contracts.schemas.parent_profiles import (
    CreateParentContextEntryRequest,
    parent_field_errors,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentContextConfirmationRequestV1,
    ParentRunContextSnapshotV1,
    ParentRunContextSnapshotV2,
)
from sketch2life.domain.parent_profile_context import (
    CONTEXT_ENTRY_KINDS,
    MAX_SHORT_TEXT_CHARS,
    PARENT_CONTEXT_V1_SCHEMA,
    PARENT_CONTEXT_V2_SCHEMA,
    SNAPSHOT_MAX_BYTES,
    ContextEntryDraft,
    SelectedContextEntry,
    build_selected_context_snapshot,
    context_entries_for_worker,
    jsonb_text_size,
    parse_approximate_date,
    validate_entry,
)
from sketch2life.domain.parent_profiles import ParentProfileError
from sketch2life.infrastructure.persistence import parent_story_repository as repository_module

PROFILE_REVISION = "11111111-1111-4111-8111-111111111111"
BASE_V1: dict[str, Any] = {
    "schema_version": PARENT_CONTEXT_V1_SCHEMA,
    "profile_revision_ref": PROFILE_REVISION,
    "age_months": 60,
    "interests_summary": "thich ve ca",
    "topic": "con ca",
    "adult_confirmed_idea": "ca boi",
}


def _draft(**changes: Any) -> ContextEntryDraft:
    values: dict[str, Any] = {
        "entry_kind": "OBSERVATION",
        "short_text": "  thich cho cho an  ",
        "source_kind": "PARENT_NOTE",
        "source_ref": None,
        "approximate_date": None,
    }
    values.update(changes)
    return ContextEntryDraft(**values)


def _field_error(draft: ContextEntryDraft) -> tuple[str, str]:
    with pytest.raises(ParentProfileError) as raised:
        validate_entry(draft)
    assert raised.value.status_code == 400 and raised.value.code == "INVALID_REQUEST"
    assert raised.value.field_errors is not None and len(raised.value.field_errors) == 1
    item = raised.value.field_errors[0]
    return item["field"], item["code"]


def test_entry_kind_is_allowlisted_and_support_needs_are_not_a_kind() -> None:
    assert CONTEXT_ENTRY_KINDS == ("OBSERVATION", "ACHIEVEMENT", "OUTSIDE_EXPERIENCE")
    for kind in CONTEXT_ENTRY_KINDS:
        assert validate_entry(_draft(entry_kind=kind)).entry_kind == kind
    for bad in ("SUPPORT_NEED", "DIAGNOSIS", "observation", ""):
        assert _field_error(_draft(entry_kind=bad)) == ("entry_kind", "INVALID_FORMAT")


def test_entry_rejects_blank_and_over_limit_text_and_stores_it_trimmed() -> None:
    assert validate_entry(_draft()).short_text == "thich cho cho an"
    assert _field_error(_draft(short_text="   \n\t ")) == ("short_text", "EMPTY")
    assert _field_error(_draft(short_text="")) == ("short_text", "EMPTY")
    assert validate_entry(_draft(short_text="a" * MAX_SHORT_TEXT_CHARS)).short_text
    assert _field_error(_draft(short_text="a" * (MAX_SHORT_TEXT_CHARS + 1))) == (
        "short_text",
        "TOO_LONG",
    )
    # 500 four-byte characters are exactly the 2,000-byte bound
    assert validate_entry(_draft(short_text="\U0001f600" * MAX_SHORT_TEXT_CHARS)).short_text


def test_nul_and_control_characters_are_refused_but_newline_and_tab_stay_legal() -> None:
    for bad in ("a\x00b", "a\x01b", "a\x0bb", "a\x0db", "a\x1fb", "a\x7fb"):
        assert _field_error(_draft(short_text=bad)) == ("short_text", "INVALID_FORMAT"), repr(bad)
    note = "line one\n\tline two"
    assert validate_entry(_draft(short_text=note)).short_text == note
    for bad in ("r\x00", "r\nx", "r\tx", "\x7fr"):
        assert _field_error(_draft(source_ref=bad)) == ("source_ref", "INVALID_FORMAT"), repr(bad)
    for bad in ("a\x00b", "a\x01b", "a\x7fb"):
        body = {"entry_kind": "OBSERVATION", "short_text": bad, "source_kind": "PARENT_NOTE"}
        with pytest.raises(ValidationError) as raised:
            CreateParentContextEntryRequest.model_validate(body)
        assert {"field": "short_text", "code": "INVALID_FORMAT"} in parent_field_errors(
            raised.value.errors()
        )
    with pytest.raises(ValidationError) as raised:
        CreateParentContextEntryRequest.model_validate(
            {
                "entry_kind": "OBSERVATION",
                "short_text": "ok",
                "source_kind": "PARENT_NOTE",
                "source_ref": "r\x00",
            }
        )
    assert {"field": "source_ref", "code": "INVALID_FORMAT"} in parent_field_errors(
        raised.value.errors()
    )


def test_source_kind_syntax_and_optional_source_ref() -> None:
    for good in ("PARENT_NOTE", "A", "X9_Y"):
        assert validate_entry(_draft(source_kind=good)).source_kind == good
    for bad in ("parent", "1ABC", "A-B", "A" * 33, ""):
        assert _field_error(_draft(source_kind=bad)) == ("source_kind", "INVALID_FORMAT")
    assert validate_entry(_draft(source_ref="  note-1  ")).source_ref == "note-1"
    assert _field_error(_draft(source_ref="   ")) == ("source_ref", "EMPTY")
    assert _field_error(_draft(source_ref="r" * 257)) == ("source_ref", "TOO_LONG")


def test_the_request_fingerprint_payload_is_the_stored_form() -> None:
    entry = _draft(source_ref=" r ", approximate_date=date(2026, 5, 1))
    assert entry.normalized_payload() == {
        "approximate_date": "2026-05-01",
        "entry_kind": "OBSERVATION",
        "short_text": "thich cho cho an",
        "source_kind": "PARENT_NOTE",
        "source_ref": "r",
    }


def test_approximate_date_is_a_plain_calendar_date() -> None:
    assert parse_approximate_date("2026-02-28") == date(2026, 2, 28)
    for bad in ("2026-02-30", "20260228", "2026-2-28", "2026-02-28T00:00:00", "", " 2026-02-28"):
        with pytest.raises(ValueError):
            parse_approximate_date(bad)


def test_the_create_request_is_strict_and_the_errors_use_the_parent_vocabulary() -> None:
    good = {
        "entry_kind": "ACHIEVEMENT",
        "short_text": "tu dap xe",
        "source_kind": "PARENT_NOTE",
    }
    assert CreateParentContextEntryRequest.model_validate(good).source_ref is None
    cases: list[tuple[dict[str, Any], tuple[str, str]]] = [
        ({**good, "extra": 1}, ("<unknown>", "UNKNOWN_FIELD")),
        ({**good, "entry_kind": "DIAGNOSIS"}, ("entry_kind", "INVALID_FORMAT")),
        ({**good, "short_text": " "}, ("short_text", "EMPTY")),
        ({**good, "short_text": "a" * 501}, ("short_text", "TOO_LONG")),
        ({**good, "short_text": 5}, ("short_text", "INVALID_TYPE")),
        ({**good, "source_kind": "lower"}, ("source_kind", "INVALID_FORMAT")),
        ({**good, "approximate_date": "2026-02-30"}, ("approximate_date", "INVALID_FORMAT")),
        ({**good, "approximate_date": "20260228"}, ("approximate_date", "INVALID_FORMAT")),
        ({k: v for k, v in good.items() if k != "short_text"}, ("short_text", "REQUIRED")),
    ]
    for payload, expected in cases:
        with pytest.raises(ValidationError) as raised:
            CreateParentContextEntryRequest.model_validate(payload)
        assert (expected[0], expected[1]) in {
            (item["field"], item["code"]) for item in parent_field_errors(raised.value.errors())
        }, payload


def test_the_v2_snapshot_holds_only_kind_and_text_of_the_selected_entries() -> None:
    entries = [
        SelectedContextEntry("OBSERVATION", "thich ve ca"),
        SelectedContextEntry("OUTSIDE_EXPERIENCE", "di so thu"),
    ]
    snapshot = build_selected_context_snapshot(BASE_V1, entries)
    assert snapshot == {
        **BASE_V1,
        "schema_version": PARENT_CONTEXT_V2_SCHEMA,
        "selected_entries": [
            {"kind": "OBSERVATION", "text": "thich ve ca"},
            {"kind": "OUTSIDE_EXPERIENCE", "text": "di so thu"},
        ],
    }
    assert BASE_V1["schema_version"] == PARENT_CONTEXT_V1_SCHEMA  # the base is not mutated
    assert ParentRunContextSnapshotV2.model_validate(snapshot).selected_entries[0].kind
    with pytest.raises(ValidationError):
        ParentRunContextSnapshotV1.model_validate(snapshot)  # the v1 schema never takes a v2
    empty = build_selected_context_snapshot(BASE_V1, [])
    assert empty["selected_entries"] == []
    with pytest.raises(ValueError):
        build_selected_context_snapshot(snapshot, entries)  # only a v1 context takes a selection
    with pytest.raises(ValueError):
        build_selected_context_snapshot({"schema_version": "sketch2life.teacher-context.v1"}, [])


def test_the_snapshot_size_is_measured_as_jsonb_text_and_bounded() -> None:
    assert jsonb_text_size({"a": 1, "b": [1, 2]}) == len('{"a": 1, "b": [1, 2]}')
    assert jsonb_text_size({"t": "é\U0001f600"}) == len(b'{"t": "') + 2 + 4 + 2
    assert SNAPSHOT_MAX_BYTES == 32_768 == repository_module._PARENT_CONTEXT_MAX_BYTES
    # Entries alone cannot reach the bound once control characters are refused (ten entries of
    # 500 four-byte characters are about 20 KB); the guard is reachable only when the stored base
    # context is large, because its summary, topic and idea accept control characters, each of
    # which costs six bytes in ``jsonb::text`` (``\u0001``).
    emoji = "😀"
    ten = [SelectedContextEntry("OUTSIDE_EXPERIENCE", emoji * 500)] * 10
    clean_base = {
        **BASE_V1,
        "interests_summary": emoji * 2000,
        "topic": emoji * 120,
        "adult_confirmed_idea": emoji * 500,
    }
    assert jsonb_text_size(build_selected_context_snapshot(clean_base, ten)) <= SNAPSHOT_MAX_BYTES
    heavy_base = {
        **BASE_V1,
        "interests_summary": "\x01" * 2000,
        "topic": "\x01" * 120,
        "adult_confirmed_idea": "\x01" * 500,
    }
    assert jsonb_text_size(build_selected_context_snapshot(heavy_base, ten)) > SNAPSHOT_MAX_BYTES
    # the bound counts the escaped form, not the characters
    assert jsonb_text_size({"t": "\x01"}) == len(b'{"t": "') + 6 + 2


def test_context_entries_for_worker_for_v1_v2_empty_and_teacher_contexts() -> None:
    selected = [{"kind": "ACHIEVEMENT", "text": "tu dap xe"}]
    v2 = build_selected_context_snapshot(
        BASE_V1, [SelectedContextEntry("ACHIEVEMENT", "tu dap xe")]
    )
    assert context_entries_for_worker(v2) == selected
    assert context_entries_for_worker(BASE_V1) == []
    assert context_entries_for_worker(build_selected_context_snapshot(BASE_V1, [])) == []
    assert context_entries_for_worker({"schema_version": "sketch2life.teacher-context.v1"}) == []
    assert context_entries_for_worker({"age_months": 60}) == []
    # a bad stored shape never raises into the worker input
    assert (
        context_entries_for_worker(
            {"schema_version": PARENT_CONTEXT_V2_SCHEMA, "selected_entries": "x"}
        )
        == []
    )


_CONFIRM = {
    "expected_context_revision": 1,
    "context_snapshot_sha256": "a" * 64,
    "confirmed": True,
}


def test_the_confirmation_request_selection_field() -> None:
    ids = [uuid4(), uuid4()]
    absent = ParentContextConfirmationRequestV1.model_validate(_CONFIRM)
    assert absent.selected_context_entry_ids is None
    explicit_null = ParentContextConfirmationRequestV1.model_validate(
        {**_CONFIRM, "selected_context_entry_ids": None}
    )
    assert explicit_null.selected_context_entry_ids is None
    empty = ParentContextConfirmationRequestV1.model_validate(
        {**_CONFIRM, "selected_context_entry_ids": []}
    )
    assert empty.selected_context_entry_ids == []
    parsed = ParentContextConfirmationRequestV1.model_validate(
        {**_CONFIRM, "selected_context_entry_ids": [str(value) for value in ids]}
    )
    assert parsed.selected_context_entry_ids == ids
    assert all(isinstance(value, UUID) for value in parsed.selected_context_entry_ids or [])
    for bad in (
        [str(ids[0]), str(ids[0])],
        [str(uuid4()) for _ in range(11)],
        ["not-a-uuid"],
        "x",
    ):
        with pytest.raises(ValidationError):
            ParentContextConfirmationRequestV1.model_validate(
                {**_CONFIRM, "selected_context_entry_ids": bad}
            )
    assert (
        len(
            ParentContextConfirmationRequestV1.model_validate(
                {**_CONFIRM, "selected_context_entry_ids": [str(uuid4()) for _ in range(10)]}
            ).selected_context_entry_ids
            or []
        )
        == 10
    )


# ------------------------------------------------------------ the Teacher refusal and its order
class _Session:
    def __init__(self) -> None:
        self.events: list[str] = []

    def rollback(self) -> None:
        self.events.append("rollback")


def _repository(actor: RunActor | None, events: list[str]) -> Any:
    session = _Session()
    session.events = events
    return repository_module.SqlParentStoryRunRepository(session, actor=actor)  # type: ignore[arg-type]


def _confirm(repository: Any, **changes: Any) -> Any:
    values: dict[str, Any] = {
        "principal": VerifiedPrincipal("subject-1", "issuer-1", frozenset()),
        "run_id": "22222222-2222-4222-8222-222222222222",
        "expected_context_revision": 1,
        "expected_context_snapshot_sha256": "a" * 64,
        "idempotency_key": "key-1",
        "selected_context_entry_ids": (uuid4(),),
        "resolve_context_entries": lambda _profile, _ids: [],
    }
    values.update(changes)
    return repository.confirm_context(**values)


def test_a_teacher_run_with_a_selection_is_a_400_after_the_owner_lookup_and_before_any_write() -> (
    None
):
    events: list[str] = []
    repository = _repository(RunActor(RunActorKind.TEACHER, "account-1"), events)

    def owned(*_args: Any, **_kwargs: Any) -> tuple[dict[str, Any], None]:
        events.append("owner lookup")
        return {"run_id": "r", "run_state": "SUBJECT_REVIEW", "version": 1}, None

    def locked(**_kwargs: Any) -> None:
        events.append("idempotency lock")

    repository._owned_run_access = owned
    repository._lock_idempotency = locked
    with pytest.raises(ParentStoryRunError) as raised:
        _confirm(repository)
    assert (raised.value.status_code, raised.value.code) == (400, "INVALID_REQUEST")
    assert raised.value.field_errors == [
        {"field": "selected_context_entry_ids", "code": "NOT_ALLOWED"}
    ]
    assert events == ["owner lookup", "rollback"]  # the lock is released; nothing was written


def test_a_foreign_teacher_run_is_the_uniform_404_before_the_selection_is_looked_at() -> None:
    events: list[str] = []
    repository = _repository(RunActor(RunActorKind.TEACHER, "account-1"), events)

    def not_found(*_args: Any, **_kwargs: Any) -> Any:
        events.append("owner lookup")
        raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    repository._owned_run_access = not_found
    with pytest.raises(ParentStoryRunError) as raised:
        _confirm(repository)
    assert (raised.value.status_code, raised.value.code) == (404, "RESOURCE_NOT_FOUND")
    assert events == ["owner lookup"]


def test_a_selection_without_a_resolver_is_refused_before_any_write() -> None:
    events: list[str] = []
    repository = _repository(None, events)
    repository._owned_run_access = lambda *_a, **_k: ({"run_id": "r"}, None)
    with pytest.raises(ParentStoryRunError) as raised:
        _confirm(repository, resolve_context_entries=None)
    assert raised.value.status_code == 503 and events == ["rollback"]
