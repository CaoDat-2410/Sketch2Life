# ruff: noqa: E501, F811, SIM117, B023
"""Missing PostgreSQL acceptance tests named in IMPL_REVIEW_E_E1_R1_20261125.md."""

from __future__ import annotations

import hashlib
import io
import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from PIL import Image
from sqlalchemy import create_engine, delete, select, text, update
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool
from test_child_selection_postgres import Api, _build, headers, make_occurrence

from alembic import command
from sketch2life.application.ports.lesson_documents import MalwareDetected, MalwareScanResult
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.lesson_occurrences.presentation_svg_fake import (
    DeterministicPresentationSvgDrafter,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
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

pytestmark = pytest.mark.integration

_FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}
_ALLOWED_TEST_PORTS = {55440, 55441} | {
    int(port) for port in (os.environ.get("FRC08_ALLOWED_PORT", ""),) if port.isdigit()
}


class _InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put_object(
        self, key: str, body: Any, *, content_type: str, content_length: int, metadata: Any
    ) -> None:
        content = body.read()
        assert len(content) == content_length
        self.objects[key] = (content, content_type)

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type = item
        return StoredObject(io.BytesIO(content), len(content), content_type, {})

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


class _AllowlistScanner:
    def __init__(self) -> None:
        self.clean: set[str] = set()

    def scan(self, file_obj: Any) -> MalwareScanResult:
        file_obj.seek(0)
        digest = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        if digest not in self.clean:
            raise MalwareDetected("synthetic")
        return MalwareScanResult("e1-allowlist", "1", "CLEAN")


def _png_bytes(color: tuple[int, int, int] = (12, 34, 56)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def presentation_gap_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    for api in _build(monkeypatch, real_service=True, pilot=True):
        storage = _InMemoryStorage()
        scanner = _AllowlistScanner()
        api.app.state.lesson_library_storage = storage
        api.app.state.lesson_document_scanner = scanner
        api.app.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
        api.app.state.presentation_svg_drafter = DeterministicPresentationSvgDrafter()
        yield api


def _make_occurrence_with_activity(
    api: Api,
    *,
    who: str = "t1",
    class_key: str = "a1",
    activity_title: str = "Draw a star",
) -> tuple[str, str]:
    created = api.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": api.classes[class_key], "title": "Synthetic lesson"},
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    occurrence_id = str(created.json()["occurrence_id"])
    plan_res = api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions",
        json={
            "expected_head_revision_no": 0,
            "objectives": ["Draw a star"],
            "teacher_direction": "Trace five lines.",
        },
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert plan_res.status_code == 201, plan_res.text
    plan = plan_res.json()
    plan_activity_id = str(uuid4())
    with api.sessions().begin() as db:
        plan_rev_id = db.execute(
            select(PLAN_REVISIONS.c.plan_revision_id).where(
                PLAN_REVISIONS.c.occurrence_id == occurrence_id,
                PLAN_REVISIONS.c.revision_no == plan["revision_no"],
            )
        ).scalar_one()
        db.execute(
            PLAN_ACTIVITIES.insert().values(
                plan_activity_id=plan_activity_id,
                plan_revision_id=plan_rev_id,
                activity_order=1,
                activity_kind="LESSON",
                catalog_activity_ref="cat-act-1",
                activity_version=1,
                custom_title=None,
                custom_description=None,
                activity_snapshot={
                    "title": activity_title,
                    "instructions_text": "Draw carefully.",
                },
                activity_snapshot_hash="b" * 64,
            )
        )
    confirm = api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{plan['revision_no']}/confirm",
        json={"expected_plan_hash": plan["content_hash"]},
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert confirm.status_code == 200, confirm.text
    return occurrence_id, plan_activity_id


def _upload_presentation_image(
    api: Api,
    *,
    who: str = "t1",
    target_ref: str,
    purpose: str = "PRESENTATION_IMAGE",
    data: bytes | None = None,
    clean: bool = True,
) -> tuple[str, bytes, str]:
    payload = data if data is not None else _png_bytes()
    digest = _sha256(payload)
    if clean:
        api.app.state.lesson_document_scanner.clean.add(digest)
    created = api.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": purpose,
            "target_ref": target_ref,
            "media_type": "image/png",
            "expected_size_bytes": len(payload),
            "expected_sha256": digest,
        },
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    upload_id = created.json()["upload_id"]
    put = api.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/1",
        content=payload,
        headers=headers(
            api.subjects[who],
            **{"X-Part-SHA256": digest, "Content-Type": "application/octet-stream"},
        ),
    )
    assert put.status_code == 200, put.text
    complete = api.client.post(
        f"/v1/upload-sessions/{upload_id}/complete",
        json={"expected_size_bytes": len(payload), "expected_sha256": digest},
        headers=headers(api.subjects[who], uuid4().hex),
    )
    assert complete.status_code == 202, complete.text
    return str(complete.json()["asset_ref"]), payload, digest


def _insert_catalog_entry(
    api: Api,
    *,
    visibility_scope: str,
    organization_id: str | None,
    catalog_state: str = "ACTIVE",
) -> str:
    entry_id = str(uuid4())
    source_ref = f"svg-src-{entry_id}"
    canonical_ref = f"svg-can-{entry_id}"
    owner_scope_kind = "ORGANIZATION" if organization_id else "PARENT_ACCOUNT"
    owner_scope_ref = organization_id or "platform-svg-seed"
    with api.sessions().begin() as db:
        for asset_ref in (source_ref, canonical_ref):
            db.add(
                CoreAssetMetadataModel(
                    asset_ref=asset_ref,
                    asset_version=1,
                    organization_id=organization_id,
                    owner_scope_kind=owner_scope_kind,
                    owner_scope_ref=owner_scope_ref,
                    content_sha256="a" * 64,
                    media_type="image/svg+xml",
                    source_refs=[],
                )
            )
        db.flush()
        db.execute(
            SVG_CATALOG_ASSETS.insert().values(
                asset_ref=source_ref,
                asset_version=1,
                catalog_entry_id=entry_id,
                visibility_scope=visibility_scope,
                organization_id=organization_id,
                canonical_asset_ref=canonical_ref,
                canonical_asset_version=1,
                topic_key="shapes",
                title_vi="Ngôi sao",
                alt_text_vi="Hình ngôi sao",
                source_uri="https://example.test/star.svg",
                license_id="CC0-1.0",
                license_uri="https://creativecommons.org/publicdomain/zero/1.0/",
                source_sha256="a" * 64,
                canonical_sha256="b" * 64,
                sanitizer_version="1",
                readiness_class="STROKE_READY",
                structural_facts={"path_count": 1},
                catalog_state=catalog_state,
                created_by="synthetic-seed",
            )
        )
    return entry_id


def test_seed_from_approved_plan_and_refuse_unapproved_occurrence(
    presentation_gap_api: Api,
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (seed from plan and unapproved 409)"""
    api = presentation_gap_api
    unapproved = make_occurrence(api, approve=False)
    refused = api.client.post(
        f"/v1/lesson-occurrences/{unapproved.occurrence_id}/presentation",
        json={"seed": "PLAN_ACTIVITIES"},
        headers=headers(api.subjects["t1"], "e1-unapproved-create"),
    )
    assert refused.status_code == 409
    assert refused.json()["code"] == "LESSON_PLAN_NOT_APPROVED"

    occurrence_id, _activity_id = _make_occurrence_with_activity(
        api, activity_title="Draw a star"
    )
    created = api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/presentation",
        json={"seed": "PLAN_ACTIVITIES"},
        headers=headers(api.subjects["t1"], "e1-seeded-create"),
    )
    assert created.status_code == 201, created.text
    slides = created.json()["head"]["slides"]
    assert len(slides) == 1
    assert slides[0]["title"] == "Draw a star"
    assert slides[0]["body_text"] == "Draw carefully."


def test_svg_catalog_attach_org_isolation_and_archiving(presentation_gap_api: Api) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (catalog other org 404, archived 409, STALE)"""
    api = presentation_gap_api
    occ = make_occurrence(api)
    base = f"/v1/lesson-occurrences/{occ.occurrence_id}/presentation"
    created = api.client.post(
        base, json={"seed": "BLANK"}, headers=headers(api.subjects["t1"], "e1-cat-create")
    )
    assert created.status_code == 201
    slide_id = created.json()["head"]["slides"][0]["slide_id"]

    active_id = _insert_catalog_entry(
        api, visibility_scope="ORGANIZATION", organization_id=api.organization, catalog_state="ACTIVE"
    )
    archived_id = _insert_catalog_entry(
        api, visibility_scope="ORGANIZATION", organization_id=api.organization, catalog_state="ARCHIVED"
    )
    other_org_id = _insert_catalog_entry(
        api, visibility_scope="ORGANIZATION", organization_id=api.other_organization, catalog_state="ACTIVE"
    )

    foreign = api.client.post(
        f"{base}/revisions",
        json={
            "operations": [
                {
                    "op": "SET_MEDIA",
                    "slide_id": slide_id,
                    "placement": "FULL",
                    "media": {"kind": "SVG_CATALOG", "catalog_entry_id": other_org_id, "alt_text": "x"},
                }
            ]
        },
        headers=headers(api.subjects["t1"], "e1-cat-foreign", **{"If-Match": '"1"'}),
    )
    assert foreign.status_code == 404

    archived_attach = api.client.post(
        f"{base}/revisions",
        json={
            "operations": [
                {
                    "op": "SET_MEDIA",
                    "slide_id": slide_id,
                    "placement": "FULL",
                    "media": {"kind": "SVG_CATALOG", "catalog_entry_id": archived_id, "alt_text": "x"},
                }
            ]
        },
        headers=headers(api.subjects["t1"], "e1-cat-archived", **{"If-Match": '"1"'}),
    )
    assert archived_attach.status_code == 409
    assert archived_attach.json()["code"] == "INVALID_STATE_TRANSITION"

    attached = api.client.post(
        f"{base}/revisions",
        json={
            "operations": [
                {
                    "op": "SET_MEDIA",
                    "slide_id": slide_id,
                    "placement": "FULL",
                    "media": {"kind": "SVG_CATALOG", "catalog_entry_id": active_id, "alt_text": "Star"},
                }
            ]
        },
        headers=headers(api.subjects["t1"], "e1-cat-attach", **{"If-Match": '"1"'}),
    )
    assert attached.status_code == 201

    with api.sessions().begin() as db:
        db.execute(
            update(SVG_CATALOG_ASSETS)
            .where(SVG_CATALOG_ASSETS.c.catalog_entry_id == active_id)
            .values(catalog_state="ARCHIVED")
        )
    after_archive = api.client.get(base, headers=headers(api.subjects["t1"]))
    assert after_archive.status_code == 200
    assert after_archive.json()["stale_reasons"] == ["MEDIA_SOURCE_CHANGED"]
    assert after_archive.json()["head"]["slides"][0]["media_state"] == "STALE"

    ready_blocked = api.client.post(
        f"{base}/revisions/2/ready",
        headers=headers(api.subjects["t1"], "e1-cat-ready-blocked", **{"If-Match": '"2"'}),
    )
    assert ready_blocked.status_code == 409
    assert ready_blocked.json()["code"] == "STALE_SOURCE_VERSION"


def test_archived_occurrence_and_suspended_class_reject_commands(
    presentation_gap_api: Api,
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (archived occurrence and suspended class 409)"""
    api = presentation_gap_api
    occ_archived = make_occurrence(api)
    occ_suspended = make_occurrence(api)
    with api.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occ_archived.occurrence_id)
            .values(state="ARCHIVED")
        )
    archived_res = api.client.post(
        f"/v1/lesson-occurrences/{occ_archived.occurrence_id}/presentation",
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "e1-archived-occ"),
    )
    assert archived_res.status_code == 409
    assert archived_res.json()["code"] == "INVALID_STATE_TRANSITION"

    with api.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == api.classes["a1"])
            .values(state="suspended")
        )
    suspended_res = api.client.post(
        f"/v1/lesson-occurrences/{occ_suspended.occurrence_id}/presentation",
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], "e1-suspended-class"),
    )
    assert suspended_res.status_code == 409
    assert suspended_res.json()["code"] == "INVALID_STATE_TRANSITION"


def test_presentation_and_svg_draft_triggers_and_privacy(presentation_gap_api: Api) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (triggers and privacy in receipts/audits)"""
    api = presentation_gap_api
    occ_id, act_id = _make_occurrence_with_activity(api, activity_title="Draw a moon")
    base = f"/v1/lesson-occurrences/{occ_id}/presentation"
    created = api.client.post(
        base, json={"seed": "PLAN_ACTIVITIES"}, headers=headers(api.subjects["t1"], "e1-priv-create")
    ).json()
    draft = api.client.post(
        f"{base}/svg-drafts",
        json={"plan_activity_id": act_id, "subject_text": "crescent"},
        headers=headers(api.subjects["t1"], "e1-priv-draft"),
    ).json()

    with api.sessions().begin() as db:
        with pytest.raises(DBAPIError, match="PRESENTATION_DELETE_FORBIDDEN"):
            db.execute(
                delete(PRESENTATIONS).where(
                    PRESENTATIONS.c.presentation_id == created["presentation_id"]
                )
            )
    with api.sessions().begin() as db:
        with pytest.raises(DBAPIError, match="PRESENTATION_IMMUTABLE"):
            db.execute(
                update(PRESENTATIONS)
                .where(PRESENTATIONS.c.presentation_id == created["presentation_id"])
                .values(organization_ref="tampered", revision=2)
            )
    with api.sessions().begin() as db:
        with pytest.raises(DBAPIError, match="PRESENTATION_SVG_DRAFT_DELETE_FORBIDDEN"):
            db.execute(
                delete(PRESENTATION_SVG_DRAFTS).where(
                    PRESENTATION_SVG_DRAFTS.c.svg_draft_id == draft["svg_draft_id"]
                )
            )
    with api.sessions().begin() as db:
        with pytest.raises(DBAPIError, match="PRESENTATION_SVG_DRAFT_IMMUTABLE"):
            db.execute(
                update(PRESENTATION_SVG_DRAFTS)
                .where(PRESENTATION_SVG_DRAFTS.c.svg_draft_id == draft["svg_draft_id"])
                .values(license_id="MIT")
            )
    with api.sessions().begin() as db:
        with pytest.raises(DBAPIError, match="PRESENTATION_SVG_DRAFT_ILLEGAL_TRANSITION"):
            db.execute(
                update(PRESENTATION_SVG_DRAFTS)
                .where(PRESENTATION_SVG_DRAFTS.c.svg_draft_id == draft["svg_draft_id"])
                .values(state="PENDING_REVIEW", revision=2)
            )

    with api.sessions()() as db:
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.idempotency_key.in_(("e1-priv-create", "e1-priv-draft"))
            )
        ).all()
        audits = db.execute(
            select(
                CoreAuditEntryModel.action,
                CoreAuditEntryModel.resource_type,
                CoreAuditEntryModel.resource_id,
            ).where(
                CoreAuditEntryModel.resource_id.in_(
                    (created["presentation_id"], draft["svg_draft_id"])
                )
            )
        ).all()
    audit_dump = json.dumps([tuple(row) for row in audits])
    receipt_dump = json.dumps([r.request_fingerprint for r in receipts])
    assert "Draw a moon" not in audit_dump and "crescent" not in audit_dump
    assert "Draw a moon" not in receipt_dump and "crescent" not in receipt_dump
    assert "child" not in audit_dump.lower()


@pytest.fixture
def sl_roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    database_url = os.environ.get("T_SLD1_ROUNDTRIP_DATABASE_URL")
    if not database_url:
        pytest.skip("set T_SLD1_ROUNDTRIP_DATABASE_URL to a disposable T-SLD1 round-trip database")
    parsed = make_url(database_url)
    database_name = parsed.database or ""
    if not all(token in database_name for token in ("frc08", "be1_acceptance")):
        pytest.fail("T_SLD1_ROUNDTRIP_DATABASE_URL must name a disposable frc08*be1_acceptance db")
    if parsed.port in _FORBIDDEN_PORTS or parsed.port not in _ALLOWED_TEST_PORTS:
        pytest.fail("T-SLD1 round-trip tests require an isolated database on an allowed local test port")
    if parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("T-SLD1 round-trip tests are restricted to a local disposable database")

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    backend = Path(__file__).resolve().parents[3]
    config = Config(str(backend / "alembic.ini"))
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_downgrade_refuses_with_presentation_image_upload_and_restores_purpose_check(
    sl_roundtrip: tuple[Config, Engine],
) -> None:
    """covers: IMPL_REVIEW_E_E1_R1_20261125.md P2-3 (downgrade refusal and purpose CHECK restore)"""
    config, engine = sl_roundtrip
    command.upgrade(config, "heads")
    parent = str(ScriptDirectory.from_config(config).get_revision("20261126_sl_0001").down_revision)
    upload_id = str(uuid4())
    with engine.begin() as conn:
        conn.execute(
            UPLOAD_SESSIONS.insert().values(
                upload_session_id=upload_id,
                purpose="PRESENTATION_IMAGE",
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref="synthetic-org",
                organization_id="synthetic-org",
                owner_principal_ref="synthetic-teacher",
                target_ref=str(uuid4()),
                safe_file_name="presentation.png",
                expected_media_type="image/png",
                expected_size_bytes=16,
                expected_sha256="a" * 64,
                chunk_size_bytes=4 * 1024 * 1024,
                expected_parts=1,
                state="OPEN",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
    with pytest.raises(RuntimeError, match="Refusing to downgrade teacher presentations"):
        command.downgrade(config, parent)

    with engine.begin() as conn:
        conn.execute(
            delete(UPLOAD_SESSIONS).where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
        )
    command.downgrade(config, parent)
    with engine.connect() as conn:
        definition = conn.execute(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'ck_core_upload_purpose'"
            )
        ).scalar_one()
    assert "PRESENTATION_IMAGE" not in str(definition)
    command.upgrade(config, "heads")
