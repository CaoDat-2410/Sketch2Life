"""Synthetic PostgreSQL acceptance coverage for immutable Teacher presentation revisions.

This test reuses the disposable-occurrence harness from T-4b1. It is authored for the scoped
``frc08*be1_acceptance`` test database only and was not run during the T-SLD1 implementation.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import struct
import zlib
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import DBAPIError
from test_child_selection_postgres import (
    ISSUER,
    Api,
    _build,
    headers,
    make_occurrence,
    reapprove,
)

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import MalwareScanResult
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.presentation_svg import (
    PresentationSvgDrafterUnavailable,
    PresentationSvgDraftInput,
    PresentationSvgDraftOutput,
)
from sketch2life.domain.lesson_occurrences.presentation import command_fingerprint
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    ChecklistDefinition,
    ChecklistItem,
    ChecklistRegistry,
)
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.lesson_occurrences.presentation_svg_fake import (
    DeterministicPresentationSvgDrafter,
)
from sketch2life.infrastructure.lesson_occurrences.presentations import (
    CREATE_SCOPE,
    SVG_CREATE_SCOPE,
    LessonPresentationService,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    OCCURRENCES,
    PRESENTATION_REVISIONS,
    PRESENTATION_SVG_DRAFTS,
    PRESENTATIONS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ClassroomModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
)
from sketch2life.infrastructure.persistence.svg_catalog_tables import SVG_CATALOG_ASSETS
from sketch2life.interfaces.http.routers.lesson_occurrences import get_checklist_registry


@pytest.fixture
def presentation_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    yield from _build(monkeypatch, real_service=True, pilot=True)


class _MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.reads: list[str] = []

    def put_object(
        self,
        key: str,
        body: Any,
        *,
        content_type: str,
        content_length: int,
        metadata: Any,
    ) -> None:
        content = body.read()
        assert len(content) == content_length
        self.objects[key] = (content, content_type)

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, media_type = item
        self.reads.append(key)
        return StoredObject(io.BytesIO(content), len(content), media_type, {})

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


class _CleanScanner:
    def scan(self, file_obj: Any) -> MalwareScanResult:
        file_obj.seek(0)
        return MalwareScanResult("presentation-test-scanner", "1", "CLEAN")


def _install_upload_adapters(api: Api) -> _MemoryStorage:
    storage = _MemoryStorage()
    api.app.state.lesson_library_storage = storage
    api.app.state.lesson_document_scanner = _CleanScanner()
    api.app.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
    return storage


def _png_chunk(chunk_type: bytes, content: bytes) -> bytes:
    payload = chunk_type + content
    return struct.pack(">I", len(content)) + payload + struct.pack(">I", zlib.crc32(payload))


def _tiny_png() -> bytes:
    header = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    pixel = zlib.compress(b"\x00\x10\x20\x30\xff")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", pixel)
        + _png_chunk(b"IEND", b"")
    )


def _upload_asset(
    api: Api,
    occurrence_id: str,
    data: bytes,
    *,
    purpose: str = "PRESENTATION_IMAGE",
    media_type: str = "image/png",
    who: str = "t1",
    complete: bool = True,
) -> str:
    digest = hashlib.sha256(data).hexdigest()
    body: dict[str, Any] = {
        "purpose": purpose,
        "target_ref": occurrence_id,
        "media_type": media_type,
        "expected_size_bytes": len(data),
        "expected_sha256": digest,
    }
    if purpose == "OCCURRENCE_DOCUMENT":
        body["file_name"] = "synthetic-source.pdf"
    created = api.client.post(
        "/v1/upload-sessions",
        json=body,
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    upload_id = str(created.json()["upload_id"])
    asset_ref = f"upl_{upload_id}"
    if not complete:
        return asset_ref
    part = api.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/1",
        content=data,
        headers=headers(
            api.subjects[who],
            **{
                "X-Part-SHA256": digest,
                "Content-Type": "application/octet-stream",
            },
        ),
    )
    assert part.status_code == 200, part.text
    completed = api.client.post(
        f"/v1/upload-sessions/{upload_id}/complete",
        json={"expected_size_bytes": len(data), "expected_sha256": digest},
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert completed.status_code == 202, completed.text
    assert completed.json()["asset_ref"] == asset_ref
    return asset_ref


def _approved_custom_activity(api: Api, occurrence_id: str) -> str:
    registry = ChecklistRegistry(
        (
            ChecklistDefinition(
                "synthetic-v1", (ChecklistItem("synthetic-item", "Synthetic safety item"),)
            ),
        )
    )
    api.app.dependency_overrides[get_checklist_registry] = lambda: registry
    base = f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions"
    draft = api.client.post(
        base,
        json={
            "expected_head_revision_no": 1,
            "objectives": ["Synthetic objective"],
            "teacher_direction": "Synthetic direction",
            "activities": [
                {
                    "kind": "CUSTOM",
                    "title": "Synthetic activity",
                    "description": "Synthetic description",
                }
            ],
        },
        headers=headers(api.subjects["t1"], "presentation-custom-plan-create"),
    )
    assert draft.status_code == 201, draft.text
    confirmed = api.client.post(
        f"{base}/{draft.json()['revision_no']}/confirm",
        json={
            "expected_plan_hash": draft.json()["content_hash"],
            "checklist": [
                {
                    "activity_order": 1,
                    "checklist_version": "synthetic-v1",
                    "items": [{"item_id": "synthetic-item", "checked": True}],
                }
            ],
        },
        headers=headers(api.subjects["t1"], "presentation-custom-plan-confirm"),
    )
    assert confirmed.status_code == 200, confirmed.text
    return str(confirmed.json()["activities"][0]["plan_activity_id"])


def _create_presentation(api: Api, occurrence_id: str, key: str) -> Any:
    response = api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/presentation",
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], key),
    )
    assert response.status_code == 201, response.text
    return response


def _set_media(
    api: Api,
    occurrence_id: str,
    slide_id: str,
    media: dict[str, Any],
    *,
    expected_revision: int,
    key: str,
    repin_to_current_plan: bool = False,
) -> Any:
    return api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/presentation/revisions",
        json={
            "repin_to_current_plan": repin_to_current_plan,
            "operations": [
                {
                    "op": "SET_MEDIA",
                    "slide_id": slide_id,
                    "placement": "FULL",
                    "media": media,
                }
            ],
        },
        headers=headers(
            api.subjects["t1"], key, **{"If-Match": f'"{expected_revision}"'}
        ),
    )


def _create_svg_draft(
    api: Api, occurrence_id: str, plan_activity_id: str, key: str
) -> Any:
    return api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/presentation/svg-drafts",
        json={"plan_activity_id": plan_activity_id, "subject_text": "butterfly"},
        headers=headers(api.subjects["t1"], key),
    )


def _insert_catalog_entry(
    api: Api,
    *,
    organization_id: str,
    catalog_state: str = "ACTIVE",
) -> str:
    asset_ref = f"synthetic-svg-{uuid4()}"
    catalog_entry_id = str(uuid4())
    digest = hashlib.sha256(asset_ref.encode("ascii")).hexdigest()
    with api.sessions().begin() as db:
        db.add(
            CoreAssetMetadataModel(
                asset_ref=asset_ref,
                asset_version=1,
                organization_id=organization_id,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=organization_id,
                content_sha256=digest,
                media_type="image/svg+xml",
                source_refs=[],
                derived_from_ref=None,
            )
        )
        db.flush()
        db.execute(
            SVG_CATALOG_ASSETS.insert().values(
                asset_ref=asset_ref,
                asset_version=1,
                catalog_entry_id=catalog_entry_id,
                visibility_scope="ORGANIZATION",
                organization_id=organization_id,
                canonical_asset_ref=asset_ref,
                canonical_asset_version=1,
                topic_key="synthetic",
                title_vi="Synthetic SVG",
                alt_text_vi="Synthetic lesson image",
                source_uri="https://example.invalid/synthetic.svg",
                license_id="CC0-1.0",
                license_uri="https://creativecommons.org/publicdomain/zero/1.0/",
                source_sha256=digest,
                canonical_sha256=digest,
                sanitizer_version="synthetic-1",
                readiness_class="STROKE_READY",
                structural_facts={"path_count": 1},
                catalog_state=catalog_state,
                created_by=api.accounts["t1"],
            )
        )
    return catalog_entry_id


class _BarrierDrafter:
    def __init__(self, barrier: Barrier) -> None:
        self.barrier = barrier
        self.delegate = DeterministicPresentationSvgDrafter()

    def draft(self, request: PresentationSvgDraftInput) -> PresentationSvgDraftOutput:
        self.barrier.wait(timeout=30)
        return self.delegate.draft(request)


class _UnavailableDrafter:
    def draft(self, _request: PresentationSvgDraftInput) -> PresentationSvgDraftOutput:
        raise PresentationSvgDrafterUnavailable


def test_create_receipt_replays_mismatches_and_conflicts(presentation_api: Api) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    url = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    key = "presentation-create-replay"
    first = api.client.post(
        url, json={"seed": "BLANK"}, headers=headers(api.subjects["t1"], key)
    )
    replay = api.client.post(
        url, json={"seed": "BLANK"}, headers=headers(api.subjects["t1"], key)
    )
    assert (first.status_code, replay.status_code) == (201, 201)
    assert replay.json() == first.json()

    mismatch = api.client.post(
        url,
        json={"seed": "PLAN_ACTIVITIES"},
        headers=headers(api.subjects["t1"], key),
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    other_key = api.client.post(
        url,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-create-other"),
    )
    assert other_key.status_code == 409
    assert other_key.json()["code"] == "RESOURCE_CONFLICT"


def test_concurrent_same_key_create_is_one_presentation_and_two_replays(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    url = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    barrier = Barrier(2)

    def call(_: int) -> Any:
        barrier.wait()
        return api.client.post(
            url,
            json={"seed": "BLANK"},
            headers=headers(api.subjects["t1"], "presentation-concurrent-create"),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(call, range(2)))
    assert [result.status_code for result in results] == [201, 201]
    assert results[0].json() == results[1].json()


def test_concurrent_edits_on_one_if_match_have_one_winner(presentation_api: Api) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = api.client.post(
        base,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-concurrent-base"),
    )
    assert created.status_code == 201, created.text
    slide_id = created.json()["head"]["slides"][0]["slide_id"]
    barrier = Barrier(2)

    def edit(title: str) -> Any:
        barrier.wait()
        return api.client.post(
            f"{base}/revisions",
            json={"operations": [{"op": "UPDATE_SLIDE", "slide_id": slide_id, "title": title}]},
            headers=headers(
                api.subjects["t1"],
                f"presentation-edit-{title.lower().replace(' ', '-')}",
                **{"If-Match": '"1"'},
            ),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, ("Edit A", "Edit B")))
    assert sorted(result.status_code for result in results) == [201, 409]
    stale = next(result for result in results if result.status_code == 409)
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2


def test_occurrence_scope_keeps_uniform_404_and_in_class_non_owner_403(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    url = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    hidden = [
        api.client.get(url, headers=headers(api.subjects[key]))
        for key in ("stranger", "tother", "manager", "parent")
    ]
    assert all(response.status_code == 404 for response in hidden)
    assert len({response.json()["code"] for response in hidden}) == 1
    assert hidden[0].json()["code"] == "RESOURCE_NOT_FOUND"

    forbidden = api.client.post(
        url,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t4"], "presentation-non-owner"),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ACTION_NOT_ALLOWED"


def test_blank_deck_edit_ready_stale_plan_and_database_immutability(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"

    created = api.client.post(
        base,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-create-1"),
    )
    assert created.status_code == 201, created.text
    slide_id = created.json()["head"]["slides"][0]["slide_id"]
    assert created.headers["etag"] == '"1"'

    edited = api.client.post(
        f"{base}/revisions",
        json={
            "repin_to_current_plan": False,
            "operations": [
                {"op": "UPDATE_SLIDE", "slide_id": slide_id, "title": "Synthetic lesson"}
            ],
        },
        headers=headers(api.subjects["t1"], "presentation-edit-1", **{"If-Match": '"1"'}),
    )
    assert edited.status_code == 201, edited.text
    assert edited.json()["head_revision_no"] == 2
    assert edited.headers["content-location"].endswith("/revisions/2")

    ready = api.client.post(
        f"{base}/revisions/2/ready",
        headers=headers(api.subjects["t1"], "presentation-ready-1", **{"If-Match": '"2"'}),
    )
    assert ready.status_code == 200, ready.text
    assert ready.json()["ready_revision_no"] == 2
    assert ready.json()["presentable"] is True

    engine = api.engine
    assert engine is not None
    with engine.begin() as connection, pytest.raises(DBAPIError) as update_error:
        connection.execute(
            update(PRESENTATION_REVISIONS)
            .where(
                PRESENTATION_REVISIONS.c.presentation_id == created.json()["presentation_id"],
                PRESENTATION_REVISIONS.c.revision_no == 1,
            )
            .values(slides=[])
        )
    assert "PRESENTATION_REVISION_IMMUTABLE" in str(update_error.value.orig)

    with engine.begin() as connection, pytest.raises(DBAPIError) as delete_error:
        connection.execute(
            delete(PRESENTATION_REVISIONS).where(
                PRESENTATION_REVISIONS.c.presentation_id == created.json()["presentation_id"],
                PRESENTATION_REVISIONS.c.revision_no == 1,
            )
        )
    assert "PRESENTATION_REVISION_DELETE_FORBIDDEN" in str(delete_error.value.orig)

    aggregate_before_change = api.client.get(base, headers=headers(api.subjects["t1"]))
    revision_before_change = api.client.get(
        f"{base}/revisions/2", headers=headers(api.subjects["t1"])
    )
    reapprove(api, occurrence)
    stale = api.client.get(
        base,
        headers=headers(
            api.subjects["t1"], **{"If-None-Match": aggregate_before_change.headers["etag"]}
        ),
    )
    assert stale.status_code == 200, stale.text
    assert stale.json()["source_state"] == "STALE"
    assert stale.json()["stale_reasons"] == ["PLAN_REVISION_CHANGED"]
    assert stale.json()["presentable"] is False
    assert stale.headers["etag"] != aggregate_before_change.headers["etag"]

    stale_revision = api.client.get(
        f"{base}/revisions/2",
        headers=headers(
            api.subjects["t1"], **{"If-None-Match": revision_before_change.headers["etag"]}
        ),
    )
    assert stale_revision.status_code == 200, stale_revision.text
    assert stale_revision.json()["source_state"] == "STALE"
    assert stale_revision.json()["stale_reasons"] == ["PLAN_REVISION_CHANGED"]
    assert stale_revision.headers["etag"] != revision_before_change.headers["etag"]


def test_stale_ready_is_blocked_until_revision_is_repinned_to_current_plan(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = api.client.post(
        base,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-stale-ready-create"),
    )
    assert created.status_code == 201, created.text
    reapprove(api, occurrence)

    blocked = api.client.post(
        f"{base}/revisions/1/ready",
        headers=headers(
            api.subjects["t1"],
            "presentation-stale-ready-blocked",
            **{"If-Match": '"1"'},
        ),
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "STALE_SOURCE_VERSION"

    repinned = api.client.post(
        f"{base}/revisions",
        json={
            "repin_to_current_plan": True,
            "operations": [
                {
                    "op": "UPDATE_SLIDE",
                    "slide_id": created.json()["head"]["slides"][0]["slide_id"],
                    "title": "Repinned synthetic slide",
                }
            ],
        },
        headers=headers(
            api.subjects["t1"],
            "presentation-stale-ready-repin",
            **{"If-Match": '"1"'},
        ),
    )
    assert repinned.status_code == 201, repinned.text
    assert repinned.json()["head"]["revision_no"] == 2
    assert repinned.json()["head"]["plan_revision_no"] == 2

    ready = api.client.post(
        f"{base}/revisions/2/ready",
        headers=headers(
            api.subjects["t1"],
            "presentation-stale-ready-after-repin",
            **{"If-Match": '"2"'},
        ),
    )
    assert ready.status_code == 200, ready.text
    assert ready.json()["presentable"] is True


def test_second_ready_supersedes_the_previous_ready_revision(presentation_api: Api) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = api.client.post(
        base,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-ready-supersede-create"),
    )
    assert created.status_code == 201, created.text
    slide_id = created.json()["head"]["slides"][0]["slide_id"]

    second = api.client.post(
        f"{base}/revisions",
        json={"operations": [{"op": "UPDATE_SLIDE", "slide_id": slide_id, "title": "Two"}]},
        headers=headers(
            api.subjects["t1"],
            "presentation-ready-supersede-edit-two",
            **{"If-Match": '"1"'},
        ),
    )
    assert second.status_code == 201, second.text
    ready_two = api.client.post(
        f"{base}/revisions/2/ready",
        headers=headers(
            api.subjects["t1"],
            "presentation-ready-supersede-ready-two",
            **{"If-Match": '"2"'},
        ),
    )
    assert ready_two.status_code == 200, ready_two.text

    third = api.client.post(
        f"{base}/revisions",
        json={"operations": [{"op": "UPDATE_SLIDE", "slide_id": slide_id, "title": "Three"}]},
        headers=headers(
            api.subjects["t1"],
            "presentation-ready-supersede-edit-three",
            **{"If-Match": '"3"'},
        ),
    )
    assert third.status_code == 201, third.text
    ready_three = api.client.post(
        f"{base}/revisions/3/ready",
        headers=headers(
            api.subjects["t1"],
            "presentation-ready-supersede-ready-three",
            **{"If-Match": '"4"'},
        ),
    )
    assert ready_three.status_code == 200, ready_three.text

    with api.sessions()() as db:
        states = db.execute(
            select(PRESENTATION_REVISIONS.c.revision_no, PRESENTATION_REVISIONS.c.state).where(
                PRESENTATION_REVISIONS.c.presentation_id == created.json()["presentation_id"]
            )
        ).all()
    assert dict(states) == {1: "DRAFT", 2: "SUPERSEDED", 3: "READY"}


@pytest.mark.parametrize("blocker", ["ARCHIVED_OCCURRENCE", "SUSPENDED_CLASS"])
def test_archived_occurrence_or_suspended_class_refuses_presentation_commands(
    presentation_api: Api, blocker: str
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = api.client.post(
        base,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-archive-create"),
    )
    assert created.status_code == 201, created.text
    with api.sessions().begin() as db:
        if blocker == "ARCHIVED_OCCURRENCE":
            db.execute(
                update(OCCURRENCES)
                .where(OCCURRENCES.c.occurrence_id == occurrence.occurrence_id)
                .values(state="ARCHIVED")
            )
        else:
            db.execute(
                update(ClassroomModel)
                .where(ClassroomModel.class_id == api.classes[occurrence.class_key])
                .values(state="suspended")
            )

    response = api.client.post(
        f"{base}/revisions",
        json={
            "operations": [
                {
                    "op": "UPDATE_SLIDE",
                    "slide_id": created.json()["head"]["slides"][0]["slide_id"],
                    "title": "Not writable",
                }
            ]
        },
        headers=headers(
            api.subjects["t1"],
            "presentation-archive-edit",
            **{"If-Match": '"1"'},
        ),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"


def test_receipt_pk_race_replays_winner_and_rolls_back_loser_counts(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = api.client.post(
        base,
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "presentation-race-base"),
    )
    assert created.status_code == 201, created.text

    principal = VerifiedPrincipal(
        subject=api.subjects["t1"], issuer=ISSUER, roles=frozenset({"teacher"})
    )
    scope = CREATE_SCOPE.replace("{occurrence_id}", occurrence.occurrence_id)
    key = "presentation-forced-pk-race"
    fingerprint = command_fingerprint(
        method="POST",
        route=CREATE_SCOPE,
        ids={"occurrence_id": occurrence.occurrence_id},
        if_match=None,
        body={"seed": "BLANK"},
    )
    race_resource_id = f"presentation-forced-pk-race-audit-{uuid4()}"
    with api.sessions().begin() as db:
        db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=api.organization,
                request_fingerprint=fingerprint,
                response_json={"body": created.json(), "etag": created.headers["etag"]},
            )
        )
        db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=api.organization,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=None,
                actor_ref=api.accounts["t1"],
                action="lesson.presentation.create",
                resource_type="lesson_presentation",
                resource_id=race_resource_id,
                decision="allowed",
            )
        )

    with api.sessions()() as db:
        service = LessonPresentationService(db, storage=None, svg_drafter=None)
        replay = service._finish(
            principal=principal,
            account_ref=api.accounts["t1"],
            organization_id=api.organization,
            occurrence_id=occurrence.occurrence_id,
            presentation_id=created.json()["presentation_id"],
            draft_id=None,
            scope=scope,
            key=key,
            fingerprint=fingerprint,
            body=created.json(),
            status_code=201,
            etag_value=created.headers["etag"],
            action="lesson.presentation.create",
            resource_type="lesson_presentation",
            resource_id=race_resource_id,
        )
    assert replay.replayed is True
    assert replay.body == created.json()

    with api.sessions()() as db:
        presentation_count = db.scalar(
            select(func.count())
            .select_from(PRESENTATIONS)
            .where(PRESENTATIONS.c.occurrence_id == occurrence.occurrence_id)
        )
        receipt_count = db.scalar(
            select(func.count()).select_from(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == principal.subject,
                Be1CommandReceiptModel.operation_scope == scope,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )
        audit_count = db.scalar(
            select(func.count()).select_from(CoreAuditEntryModel).where(
                CoreAuditEntryModel.action == "lesson.presentation.create",
                CoreAuditEntryModel.resource_id == race_resource_id,
            )
        )
        receipt_body = db.scalar(
            select(Be1CommandReceiptModel.response_json).where(
                Be1CommandReceiptModel.principal_ref == principal.subject,
                Be1CommandReceiptModel.operation_scope == scope,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )
    assert (presentation_count, receipt_count, audit_count) == (1, 1, 1)
    assert "child" not in str(receipt_body).lower()


def test_image_upload_purpose_target_checksum_deduplication_and_image_route(
    presentation_api: Api,
) -> None:
    api = presentation_api
    storage = _install_upload_adapters(api)
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = _create_presentation(api, occurrence.occurrence_id, "presentation-image-create")
    slide_id = created.json()["head"]["slides"][0]["slide_id"]
    png = _tiny_png()

    image_ref = _upload_asset(api, occurrence.occurrence_id, png)
    with api.sessions()() as db:
        upload_row = db.execute(
            select(
                UPLOAD_SESSIONS.c.purpose,
                UPLOAD_SESSIONS.c.scan_verdict,
                UPLOAD_SESSIONS.c.final_asset_ref,
            ).where(UPLOAD_SESSIONS.c.upload_session_id == image_ref[4:])
        ).one()
    assert upload_row.purpose == "PRESENTATION_IMAGE"
    assert upload_row.scan_verdict == "CLEAN"

    same_org_target = make_occurrence(api)
    other_target_ref = _upload_asset(api, same_org_target.occurrence_id, png)
    foreign_occurrence = make_occurrence(api, who="tother", class_key="b1")
    foreign_ref = _upload_asset(api, foreign_occurrence.occurrence_id, png, who="tother")
    document_ref = _upload_asset(
        api,
        occurrence.occurrence_id,
        b"%PDF-1.4\nsynthetic document",
        purpose="OCCURRENCE_DOCUMENT",
        media_type="application/pdf",
    )
    unscanned_ref = _upload_asset(api, occurrence.occurrence_id, png, complete=False)

    for index, asset_ref in enumerate(
        (other_target_ref, foreign_ref, document_ref, unscanned_ref), start=1
    ):
        rejected = _set_media(
            api,
            occurrence.occurrence_id,
            slide_id,
            {"kind": "IMAGE", "asset_ref": asset_ref},
            expected_revision=1,
            key=f"presentation-image-reject-{index}",
        )
        assert rejected.status_code == 404, rejected.text
        assert rejected.json()["code"] == "RESOURCE_NOT_FOUND"

    drift_ref = _upload_asset(api, occurrence.occurrence_id, png)
    with api.sessions()() as db:
        drift_upload_key = str(
            db.scalar(
                select(UPLOAD_SESSIONS.c.final_asset_ref).where(
                    UPLOAD_SESSIONS.c.upload_session_id == drift_ref[4:]
                )
            )
        )
    storage.objects[drift_upload_key] = (
        png[:-1] + bytes((png[-1] ^ 0x01,)),
        "image/png",
    )
    checksum_mismatch = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "IMAGE", "asset_ref": drift_ref},
        expected_revision=1,
        key="presentation-image-checksum-drift",
    )
    assert checksum_mismatch.status_code == 422
    assert checksum_mismatch.json()["code"] == "UPLOAD_CHECKSUM_MISMATCH"

    added = api.client.post(
        f"{base}/revisions",
        json={
            "operations": [
                {
                    "op": "ADD_SLIDE",
                    "after_slide_id": None,
                    "title": "Second slide",
                    "body_text": "Synthetic image reuse",
                }
            ]
        },
        headers=headers(
            api.subjects["t1"],
            "presentation-image-add-slide",
            **{"If-Match": '"1"'},
        ),
    )
    assert added.status_code == 201, added.text
    slide_ids = [slide["slide_id"] for slide in added.json()["head"]["slides"]]
    image_key = str(upload_row.final_asset_ref)
    before_reads = storage.reads.count(image_key)
    attached = api.client.post(
        f"{base}/revisions",
        json={
            "operations": [
                {
                    "op": "SET_MEDIA",
                    "slide_id": item_slide_id,
                    "placement": "FULL",
                    "media": {"kind": "IMAGE", "asset_ref": image_ref},
                }
                for item_slide_id in slide_ids
            ]
        },
        headers=headers(
            api.subjects["t1"],
            "presentation-image-attach-twice",
            **{"If-Match": '"2"'},
        ),
    )
    assert attached.status_code == 201, attached.text
    assert storage.reads.count(image_key) - before_reads == 1
    image = api.client.get(f"{base}/images/{image_ref}", headers=headers(api.subjects["t1"]))
    assert image.status_code == 200, image.text
    assert image.content == png
    assert image.headers["x-content-type-options"] == "nosniff"
    assert image.headers["cache-control"] == "private, no-store"


def test_catalog_visibility_archive_and_derived_media_staleness(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = _create_presentation(api, occurrence.occurrence_id, "presentation-catalog-create")
    slide_id = created.json()["head"]["slides"][0]["slide_id"]
    active_entry = _insert_catalog_entry(api, organization_id=api.organization)
    archived_entry = _insert_catalog_entry(
        api, organization_id=api.organization, catalog_state="ARCHIVED"
    )
    foreign_entry = _insert_catalog_entry(api, organization_id=api.other_organization)

    foreign = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_CATALOG", "catalog_entry_id": foreign_entry},
        expected_revision=1,
        key="presentation-catalog-foreign",
    )
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "RESOURCE_NOT_FOUND"
    archived = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_CATALOG", "catalog_entry_id": archived_entry},
        expected_revision=1,
        key="presentation-catalog-archived",
    )
    assert archived.status_code == 409
    assert archived.json()["code"] == "INVALID_STATE_TRANSITION"

    attached = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_CATALOG", "catalog_entry_id": active_entry},
        expected_revision=1,
        key="presentation-catalog-attach",
    )
    assert attached.status_code == 201, attached.text
    ready = api.client.post(
        f"{base}/revisions/2/ready",
        headers=headers(
            api.subjects["t1"],
            "presentation-catalog-ready",
            **{"If-Match": '"2"'},
        ),
    )
    assert ready.status_code == 200, ready.text

    old_aggregate = api.client.get(base, headers=headers(api.subjects["t1"]))
    old_revision = api.client.get(f"{base}/revisions/2", headers=headers(api.subjects["t1"]))
    with api.sessions().begin() as db:
        db.execute(
            update(SVG_CATALOG_ASSETS)
            .where(SVG_CATALOG_ASSETS.c.catalog_entry_id == active_entry)
            .values(catalog_state="ARCHIVED")
        )

    stale_aggregate = api.client.get(
        base,
        headers=headers(
            api.subjects["t1"], **{"If-None-Match": old_aggregate.headers["etag"]}
        ),
    )
    assert stale_aggregate.status_code == 200, stale_aggregate.text
    assert stale_aggregate.json()["presentable"] is False
    assert "MEDIA_SOURCE_CHANGED" in stale_aggregate.json()["stale_reasons"]
    stale_revision = api.client.get(
        f"{base}/revisions/2",
        headers=headers(api.subjects["t1"], **{"If-None-Match": old_revision.headers["etag"]}),
    )
    assert stale_revision.status_code == 200, stale_revision.text
    assert "MEDIA_SOURCE_CHANGED" in stale_revision.json()["stale_reasons"]
    assert stale_revision.json()["slides"][0]["media_state"] == "STALE"


def test_ai_draft_accept_discard_attach_rules_and_second_decision(
    presentation_api: Api,
) -> None:
    api = presentation_api
    api.app.state.presentation_svg_drafter = DeterministicPresentationSvgDrafter()
    occurrence = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occurrence.occurrence_id}/presentation"
    created = _create_presentation(api, occurrence.occurrence_id, "presentation-svg-create")
    slide_id = created.json()["head"]["slides"][0]["slide_id"]
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)

    accepted_draft = _create_svg_draft(
        api, occurrence.occurrence_id, activity_id, "presentation-svg-draft-accept"
    )
    assert accepted_draft.status_code == 201, accepted_draft.text
    accepted_id = accepted_draft.json()["svg_draft_id"]
    pending_attach = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_AI", "svg_draft_id": accepted_id},
        expected_revision=1,
        key="presentation-svg-attach-pending",
        repin_to_current_plan=True,
    )
    assert pending_attach.status_code == 409
    assert pending_attach.json()["code"] == "INVALID_STATE_TRANSITION"

    accepted = api.client.post(
        f"{base}/svg-drafts/{accepted_id}/decision",
        json={"decision": "ACCEPT"},
        headers=headers(
            api.subjects["t1"],
            "presentation-svg-accept",
            **{"If-Match": '"1"'},
        ),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["state"] == "ACCEPTED"
    attached = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_AI", "svg_draft_id": accepted_id},
        expected_revision=1,
        key="presentation-svg-attach-accepted",
        repin_to_current_plan=True,
    )
    assert attached.status_code == 201, attached.text
    assert attached.json()["head"]["slides"][0]["media"]["svg_draft_id"] == accepted_id

    discarded_draft = _create_svg_draft(
        api, occurrence.occurrence_id, activity_id, "presentation-svg-draft-discard"
    )
    assert discarded_draft.status_code == 201, discarded_draft.text
    discarded_id = discarded_draft.json()["svg_draft_id"]
    pending_attach_after_head_advance = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_AI", "svg_draft_id": discarded_id},
        expected_revision=2,
        key="presentation-svg-attach-pending-after-head",
        repin_to_current_plan=True,
    )
    assert pending_attach_after_head_advance.status_code == 409
    assert pending_attach_after_head_advance.json()["code"] == "INVALID_STATE_TRANSITION"

    discarded = api.client.post(
        f"{base}/svg-drafts/{discarded_id}/decision",
        json={"decision": "DISCARD"},
        headers=headers(
            api.subjects["t1"],
            "presentation-svg-discard",
            **{"If-Match": '"1"'},
        ),
    )
    assert discarded.status_code == 200, discarded.text
    assert discarded.json()["state"] == "DISCARDED"
    discarded_attach = _set_media(
        api,
        occurrence.occurrence_id,
        slide_id,
        {"kind": "SVG_AI", "svg_draft_id": discarded_id},
        expected_revision=2,
        key="presentation-svg-attach-discarded",
        repin_to_current_plan=True,
    )
    assert discarded_attach.status_code == 409
    assert discarded_attach.json()["code"] == "INVALID_STATE_TRANSITION"
    second_decision = api.client.post(
        f"{base}/svg-drafts/{accepted_id}/decision",
        json={"decision": "DISCARD"},
        headers=headers(
            api.subjects["t1"],
            "presentation-svg-second-decision",
            **{"If-Match": '"2"'},
        ),
    )
    assert second_decision.status_code == 409
    assert second_decision.json()["code"] == "INVALID_STATE_TRANSITION"


def test_ai_draft_local_cap_race_loser_and_retry_after(presentation_api: Api) -> None:
    api = presentation_api
    api.app.state.presentation_svg_drafter = DeterministicPresentationSvgDrafter()
    occurrence = make_occurrence(api)
    cap_presentation = _create_presentation(
        api, occurrence.occurrence_id, "presentation-svg-cap-create"
    )
    cap_presentation_id = cap_presentation.json()["presentation_id"]
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    for index in range(19):
        seeded = _create_svg_draft(
            api,
            occurrence.occurrence_id,
            activity_id,
            f"presentation-svg-cap-seed-{index}",
        )
        assert seeded.status_code == 201, seeded.text

    api.app.state.presentation_svg_drafter = _BarrierDrafter(Barrier(2))

    def create_racing_draft(index: int) -> Any:
        return _create_svg_draft(
            api,
            occurrence.occurrence_id,
            activity_id,
            f"presentation-svg-cap-race-{index}",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        racing = list(pool.map(create_racing_draft, (1, 2)))
    assert sorted(response.status_code for response in racing) == [201, 429]
    loser = next(response for response in racing if response.status_code == 429)
    assert loser.json()["code"] == "RATE_LIMITED"
    assert loser.headers["retry-after"] == "3600"

    with api.sessions()() as db:
        draft_count = db.scalar(
            select(func.count())
            .select_from(PRESENTATION_SVG_DRAFTS)
            .where(PRESENTATION_SVG_DRAFTS.c.presentation_id == cap_presentation_id)
        )
        race_receipt_count = db.scalar(
            select(func.count()).select_from(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.operation_scope
                == SVG_CREATE_SCOPE.replace("{occurrence_id}", occurrence.occurrence_id),
                Be1CommandReceiptModel.idempotency_key.in_(
                    ("presentation-svg-cap-race-1", "presentation-svg-cap-race-2")
                ),
            )
        )
    assert draft_count == 20
    assert race_receipt_count == 1

    api.app.state.presentation_svg_drafter = DeterministicPresentationSvgDrafter()
    capped = _create_svg_draft(
        api, occurrence.occurrence_id, activity_id, "presentation-svg-cap-twenty-one"
    )
    assert capped.status_code == 429
    assert capped.json()["code"] == "RATE_LIMITED"
    assert capped.headers["retry-after"] == "3600"


def test_ai_provider_unavailability_is_retryable_503_without_a_receipt(
    presentation_api: Api,
) -> None:
    api = presentation_api
    api.app.state.presentation_svg_drafter = _UnavailableDrafter()
    occurrence = make_occurrence(api)
    unavailable_presentation = _create_presentation(
        api, occurrence.occurrence_id, "presentation-svg-unavailable-create"
    )
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    key = "presentation-svg-unavailable"
    unavailable = _create_svg_draft(api, occurrence.occurrence_id, activity_id, key)
    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert unavailable.json()["retryable"] is True

    scope = SVG_CREATE_SCOPE.replace("{occurrence_id}", occurrence.occurrence_id)
    with api.sessions()() as db:
        receipt_count = db.scalar(
            select(func.count()).select_from(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.operation_scope == scope,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )
        draft_count = db.scalar(
            select(func.count())
            .select_from(PRESENTATION_SVG_DRAFTS)
            .where(
                PRESENTATION_SVG_DRAFTS.c.presentation_id
                == unavailable_presentation.json()["presentation_id"]
            )
        )
    assert (receipt_count, draft_count) == (0, 0)


def test_presentation_and_svg_draft_immutability_triggers(presentation_api: Api) -> None:
    api = presentation_api
    api.app.state.presentation_svg_drafter = DeterministicPresentationSvgDrafter()
    occurrence = make_occurrence(api)
    created = _create_presentation(api, occurrence.occurrence_id, "presentation-trigger-create")
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    draft = _create_svg_draft(
        api, occurrence.occurrence_id, activity_id, "presentation-trigger-svg-draft"
    )
    assert draft.status_code == 201, draft.text
    engine = api.engine
    assert engine is not None

    with engine.begin() as connection, pytest.raises(DBAPIError) as presentation_error:
        connection.execute(
            update(PRESENTATIONS)
            .where(PRESENTATIONS.c.presentation_id == created.json()["presentation_id"])
            .values(organization_ref=api.other_organization)
        )
    assert "PRESENTATION_IMMUTABLE" in str(presentation_error.value.orig)

    with engine.begin() as connection, pytest.raises(DBAPIError) as draft_update_error:
        connection.execute(
            update(PRESENTATION_SVG_DRAFTS)
            .where(
                PRESENTATION_SVG_DRAFTS.c.svg_draft_id == draft.json()["svg_draft_id"]
            )
            .values(document={"changed": True})
        )
    assert "PRESENTATION_SVG_DRAFT_IMMUTABLE" in str(draft_update_error.value.orig)

    with engine.begin() as connection, pytest.raises(DBAPIError) as draft_delete_error:
        connection.execute(
            delete(PRESENTATION_SVG_DRAFTS).where(
                PRESENTATION_SVG_DRAFTS.c.svg_draft_id == draft.json()["svg_draft_id"]
            )
        )
    assert "PRESENTATION_SVG_DRAFT_DELETE_FORBIDDEN" in str(draft_delete_error.value.orig)


def test_downgrade_refuses_existing_presentation_rows(presentation_api: Api) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    _create_presentation(api, occurrence.occurrence_id, "presentation-downgrade-guard-create")
    backend_root = Path(__file__).resolve().parents[3]
    migration_path = (
        backend_root / "alembic" / "versions" / "20261126_sl_0001_teacher_presentations.py"
    )
    spec = importlib.util.spec_from_file_location(
        "teacher_presentations_migration_test", migration_path
    )
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = api.engine
    assert engine is not None
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        with (
            Operations.context(context),
            pytest.raises(RuntimeError, match="Refusing to downgrade teacher presentations"),
        ):
            migration.downgrade()
