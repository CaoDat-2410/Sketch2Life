"""FEAT-066 T-3d: plan state machine, occurrence state after confirm, the body guard, scope reuse.

SRS l.775 (one approved plan), l.1699 (a stale request never overwrites the head), l.396 (§6.1.1
occurrence states), l.864-865 (Teacher scope).
"""

from __future__ import annotations

import asyncio
import itertools
import json
from typing import Any

import pytest

from sketch2life.domain.lesson_occurrences import plan as rules
from sketch2life.domain.lesson_occurrences.model import (
    OCCURRENCE_STATES,
    AccessOutcome,
    AssignmentFact,
    decide_read,
    decide_write,
)
from sketch2life.infrastructure.lesson_occurrences.plans import PlanRevisionService, plan_body
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    MAX_PLAN_CONFIRM_BODY_BYTES,
    MAX_PLAN_CREATE_BODY_BYTES,
    MAX_REVISION_EDIT_BODY_BYTES,
    BoundedImageUploadMiddleware,
)


# ----------------------------------------------------------------------------- state machine
def test_only_draft_to_approved_to_superseded_is_legal() -> None:
    legal = {("DRAFT", "APPROVED"), ("APPROVED", "SUPERSEDED")}
    for old, new in itertools.product(rules.PLAN_STATES, repeat=2):
        assert rules.can_transition(old, new) is ((old, new) in legal), (old, new)
    assert rules.PLAN_STATES == ("DRAFT", "APPROVED", "SUPERSEDED")
    assert not rules.can_transition("SUPERSEDED", "APPROVED")
    assert not rules.can_transition("DRAFT", "SUPERSEDED")


def test_confirm_moves_only_a_pre_approval_occurrence_to_approved() -> None:
    for state in ("DRAFT", "DOCUMENT_REVIEW", "PLAN_REVIEW"):
        assert rules.occurrence_state_after_confirm(state) == "APPROVED"
    for state in ("APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED", "ARCHIVED"):
        assert rules.occurrence_state_after_confirm(state) == state
    assert set(OCCURRENCE_STATES) == {
        "DRAFT",
        "DOCUMENT_REVIEW",
        "PLAN_REVIEW",
        "APPROVED",
        "SAMPLE_AVAILABLE",
        "SAMPLE_USED",
        "ARCHIVED",
    }


# ----------------------------------------------------------------------------- body shape
class Row(dict[str, Any]):
    """A mapping row the way ``RowMapping`` answers ``row["column"]``."""


def plan_row(**overrides: Any) -> Any:
    values: dict[str, Any] = {
        "plan_revision_id": "p-1",
        "occurrence_id": "o-1",
        "revision_no": 2,
        "state": "DRAFT",
        "content_hash": "a" * 64,
        "objectives": ["Mục tiêu"],
        "teacher_direction": "Hướng truyện",
        "safety_notes": None,
        "source_lesson_id": None,
        "source_lesson_version_id": None,
        "source_lesson_version_no": None,
        "source_lesson_version_hash": None,
        "created_at": "2026-11-20T00:00:00+00:00",
        "approved_at": None,
    }
    values.update(overrides)
    return Row(values)


def activity_row(**overrides: Any) -> Any:
    values: dict[str, Any] = {
        "activity_order": 1,
        "activity_kind": "LESSON",
        "catalog_activity_ref": "act-1",
        "custom_title": None,
        "custom_description": None,
        "activity_snapshot": {"title": "Vẽ cây", "instructions_text": "Vẽ thân rồi tán lá"},
        "activity_snapshot_hash": "b" * 64,
        "safety_checklist_version": None,
        "confirmed_at": None,
    }
    values.update(overrides)
    return Row(values)


def test_a_lesson_activity_shows_the_copied_title_and_instructions() -> None:
    body = plan_body(plan_row(), [activity_row()], None)
    assert body["activities"][0] == {
        "order": 1,
        "kind": "LESSON",
        "lesson_activity_id": "act-1",
        "title": "Vẽ cây",
        "description": "Vẽ thân rồi tán lá",
        "snapshot_hash": "b" * 64,
        "checklist_required": False,
        "checklist_version": None,
        "confirmed": False,
    }
    assert body["lesson_version_ref"] is None and body["supersedes_revision_no"] is None


def test_a_custom_activity_requires_a_checklist_until_it_is_confirmed() -> None:
    row = activity_row(
        activity_kind="CUSTOM",
        catalog_activity_ref=None,
        custom_title="Tự soạn",
        custom_description="Mô tả",
        activity_snapshot=None,
        activity_snapshot_hash=None,
    )
    view = plan_body(plan_row(), [row], None)["activities"][0]
    assert view["checklist_required"] is True and view["confirmed"] is False
    assert (view["title"], view["description"], view["lesson_activity_id"]) == (
        "Tự soạn",
        "Mô tả",
        None,
    )
    confirmed = activity_row(
        **{**row, "confirmed_at": "2026-11-20T00:00:00+00:00", "safety_checklist_version": "v1"}
    )
    view = plan_body(plan_row(), [confirmed], None)["activities"][0]
    assert view["confirmed"] is True and view["checklist_version"] == "v1"


def test_the_body_carries_the_pin_and_names_no_storage_or_organization() -> None:
    body = plan_body(
        plan_row(
            source_lesson_id="les-1",
            source_lesson_version_id="ver-1",
            source_lesson_version_no=3,
            source_lesson_version_hash="c" * 64,
        ),
        [],
        {"document_id": "doc-1", "revision_no": 2},
        supersedes_revision_no=1,
    )
    assert body["lesson_version_ref"] == {
        "lesson_id": "les-1",
        "version_id": "ver-1",
        "content_sha256": "c" * 64,
    }
    assert body["document_revision_ref"] == {"document_id": "doc-1", "revision_no": 2}
    assert body["supersedes_revision_no"] == 1
    text = json.dumps(body).lower()
    for word in ("bucket", "object_key", "organization", "scanner", "presigned"):
        assert word not in text


# ----------------------------------------------------------------------------- the body guard
class Harness:
    def __init__(self) -> None:
        self.app_calls = 0
        self.sent: list[dict[str, Any]] = []

    async def app(self, scope: Any, receive: Any, send: Any) -> None:
        self.app_calls += 1
        try:
            while True:
                message = await receive()
                if not message.get("more_body", False):
                    break
        except Exception:
            await send({"type": "http.response.start", "status": 400, "headers": []})
            await send({"type": "http.response.body", "body": b"{}"})
            return
        await send({"type": "http.response.start", "status": 201, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    def run(
        self,
        chunks: list[bytes],
        *,
        path: str,
        method: str = "POST",
        content_length: int | None = None,
    ) -> None:
        headers: list[tuple[bytes, bytes]] = []
        if content_length is not None:
            headers.append((b"content-length", str(content_length).encode()))
        scope = {"type": "http", "method": method, "path": path, "headers": headers}
        pending = list(chunks)

        async def receive() -> dict[str, Any]:
            body = pending.pop(0) if pending else b""
            return {"type": "http.request", "body": body, "more_body": bool(pending)}

        async def send(message: dict[str, Any]) -> None:
            self.sent.append(message)

        asyncio.run(BoundedImageUploadMiddleware(self.app)(scope, receive, send))  # type: ignore[arg-type]

    @property
    def status(self) -> int:
        return int(next(m["status"] for m in self.sent if m["type"] == "http.response.start"))

    @property
    def body(self) -> dict[str, Any]:
        raw = b"".join(m.get("body", b"") for m in self.sent if m["type"] == "http.response.body")
        return dict(json.loads(raw))


CREATE_PATH = "/v1/lesson-occurrences/occ-1/plan-revisions"
CONFIRM_PATH = "/v1/lesson-occurrences/occ-1/plan-revisions/3/confirm"


def test_the_plan_caps_are_small_but_hold_a_full_request() -> None:
    assert MAX_PLAN_CREATE_BODY_BYTES == 1024 * 1024
    assert MAX_PLAN_CONFIRM_BODY_BYTES == 256 * 1024
    # worst case characters of a create, each JSON-escaped to six bytes
    characters = 12 * 1000 + 2000 + 2000 + 24 * (4000 + 160 + 80)
    assert 6 * characters < MAX_PLAN_CREATE_BODY_BYTES
    # worst case confirm: 24 entries of 64 items of about 100 bytes
    assert MAX_PLAN_CONFIRM_BODY_BYTES > 24 * 64 * 100 + 24 * 100
    assert MAX_REVISION_EDIT_BODY_BYTES == 13 * 1024 * 1024  # T-3c is unchanged


@pytest.mark.parametrize(
    ("path", "limit"),
    [(CREATE_PATH, MAX_PLAN_CREATE_BODY_BYTES), (CONFIRM_PATH, MAX_PLAN_CONFIRM_BODY_BYTES)],
)
def test_a_plan_body_over_the_cap_is_413_before_the_application(path: str, limit: int) -> None:
    declared = Harness()
    declared.run([b"x"], path=path, content_length=limit + 1)
    assert declared.status == 413 and declared.app_calls == 0
    assert declared.body["code"] == "MEDIA_TOO_LARGE" and declared.body["message"]
    assert len(declared.sent) == 2

    streamed = Harness()
    streamed.run([b"a" * (limit // 2), b"a" * (limit // 2), b"a" * 10], path=path)
    assert streamed.status == 413 and streamed.body["code"] == "MEDIA_TOO_LARGE"
    assert [m["type"] for m in streamed.sent].count("http.response.start") == 1

    garbled = Harness()
    scope = {"type": "http", "method": "POST", "path": path, "headers": [(b"content-length", b"x")]}

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        garbled.sent.append(message)

    asyncio.run(BoundedImageUploadMiddleware(garbled.app)(scope, receive, send))  # type: ignore[arg-type]
    assert garbled.status == 413 and garbled.app_calls == 0


@pytest.mark.parametrize(
    ("path", "limit"),
    [(CREATE_PATH, MAX_PLAN_CREATE_BODY_BYTES), (CONFIRM_PATH, MAX_PLAN_CONFIRM_BODY_BYTES)],
)
def test_a_plan_body_at_the_cap_reaches_the_application(path: str, limit: int) -> None:
    harness = Harness()
    harness.run([b"a" * (limit // 2), b"a" * (limit // 2)], path=path, content_length=limit)
    assert harness.status == 201 and harness.app_calls == 1


def test_the_guard_matches_only_the_plan_write_routes() -> None:
    over = MAX_PLAN_CREATE_BODY_BYTES + 1
    for method, path in (
        ("GET", CREATE_PATH),
        ("GET", CONFIRM_PATH),
        ("POST", "/v1/lesson-occurrences/occ-1/plan-revisions/3"),
        ("POST", "/v1/lesson-occurrences/occ-1/plan-revisions/3/confirm/extra"),
        ("POST", "/v1/lesson-occurrences/occ-1/plan-revisions/3/other"),
        ("POST", "/v1/lesson-occurrences/occ-1/plan-revisions/a/b/confirm"),
        ("POST", "/v1/other/occ-1/plan-revisions"),
        ("POST", "/v1/lesson-occurrences/occ-1/plan"),
    ):
        harness = Harness()
        harness.run([b"x"], method=method, path=path, content_length=over)
        assert harness.app_calls == 1, (method, path)
        assert harness.status == 201
    trailing = Harness()
    trailing.run([b"x"], path=CREATE_PATH + "/", content_length=over)
    assert trailing.status == 413
    trailing = Harness()
    trailing.run([b"x"], path=CONFIRM_PATH + "/", content_length=MAX_PLAN_CONFIRM_BODY_BYTES + 1)
    assert trailing.status == 413


def test_the_two_plan_routes_have_their_own_limits() -> None:
    harness = Harness()
    harness.run([b"x"], path=CONFIRM_PATH, content_length=MAX_PLAN_CONFIRM_BODY_BYTES + 1)
    assert harness.status == 413
    harness = Harness()
    harness.run([b"x"], path=CREATE_PATH, content_length=MAX_PLAN_CONFIRM_BODY_BYTES + 1)
    assert harness.status == 201  # still under the create cap


# ----------------------------------------------------------------------------- scope reuse
def test_the_plan_routes_reuse_the_occurrence_decision_tables() -> None:
    teacher = AssignmentFact("teacher", "class-1")
    guide = AssignmentFact("guide", "class-1")
    other = AssignmentFact("teacher", "class-2")
    args = {"caller_account_ref": "acc-1", "responsible_teacher_ref": "acc-1"}
    assert decide_write([teacher], "class-1", **args) is AccessOutcome.PROCEED
    assert decide_write([guide], "class-1", **args) is AccessOutcome.FORBIDDEN
    assert decide_write([other], "class-1", **args) is AccessOutcome.NOT_FOUND
    assert (
        decide_write(
            [teacher], "class-1", caller_account_ref="acc-2", responsible_teacher_ref="acc-1"
        )
        is AccessOutcome.FORBIDDEN
    )
    assert decide_read([guide], "class-1") is AccessOutcome.PROCEED
    assert decide_read([other], "class-1") is AccessOutcome.NOT_FOUND


def test_the_service_never_hands_a_database_error_to_the_client_as_a_500() -> None:
    from sqlalchemy.exc import DBAPIError

    from sketch2life.infrastructure.lesson_occurrences.plans import _db_failure

    checklist = _db_failure(DBAPIError("stmt", {}, Exception("LESSON_PLAN_CHECKLIST_REQUIRED")))
    assert (checklist.status_code, checklist.code) == (409, "INVALID_STATE_TRANSITION")
    other = _db_failure(DBAPIError("stmt", {}, Exception("PLAN_ILLEGAL_TRANSITION")))
    assert (other.status_code, other.code) == (503, "PROVIDER_UNAVAILABLE")
    assert PlanRevisionService  # the service is importable without a framework fixture
