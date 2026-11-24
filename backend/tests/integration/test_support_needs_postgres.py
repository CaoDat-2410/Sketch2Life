"""T-12c PostgreSQL acceptance: encrypted profile support needs (Parent and Teacher families).

SRS l.264 BR-20, l.499 FR-C-07, l.932, l.1922, l.2338. Set ``BE1_TEST_DATABASE_URL`` to a
disposable database whose name contains ``frc08_v4_t12c`` and ``be1_acceptance``; every test builds
its own organization and profiles. The cipher is the real AES-256-GCM adapter with fixed synthetic
keys (owner decision of 2026-11-23). The Teacher consent and the narrow permission are injected
fakes of the two ports (the real consent can never be effective today and the permission store
does not exist); the default, denying guard is exercised on the real stack too. Only the external
token boundary is substituted: a test header names the acting adult, and every route, scope query
and transaction is real. The migration round trips need their own empty database in
``T12C_ROUNDTRIP_DATABASE_URL`` naming a ``frc08_v4_t12c*roundtrip*be1_acceptance`` database.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, select, text
from sqlalchemy.exc import DataError, DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.parent_profiles import ProfileSnapshot
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    Be1ProfileSupportNeedsModel,
    ClassroomModel,
    ConsentRecordModel,
    DataLifecycleRequestModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentCommandReceiptModel,
    ParentProfileSupportNeedsModel,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)
from sketch2life.infrastructure.security.support_needs_crypto import (
    AesGcmSupportNeedsCrypto,
    StaticSupportNeedsKeyring,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.parent_runtime import get_parent_principal
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.support_needs_runtime import SupportNeedsRuntime

BACKEND = Path(__file__).resolve().parents[2]
ISSUER = "synthetic-t12c-issuer"
ACTOR_HEADER = "X-T12c-Actor"
BASE_TIME = datetime(2026, 3, 1, 8, 0, 0, tzinfo=UTC)
SENTINEL = "SENTINEL-support-note-c91e4f20"
CATEGORY = "sensory-SENTINEL-cat-3b7d"
OTHER_NOTE = "SENTINEL-second-note-aa12"
ENC_1, ENC_2 = bytes(range(32)), bytes(range(100, 132))
FP_1, FP_2 = bytes(range(200, 232)), bytes(reversed(range(200, 232)))
# (actor name, account role, assignment role, scope)
ACTORS = (
    ("manager", "school_manager", "school_admin", "org"),
    ("teacher", "teacher", "teacher", "class"),
    ("other_teacher", "teacher", "teacher", "other"),
    ("suspended_teacher", "teacher", "teacher", "suspended"),
    ("archived_teacher", "teacher", "teacher", "archived"),
    ("orgwide_teacher", "teacher", "teacher", "orgwide"),
    ("foreign_teacher", "teacher", "teacher", "foreign"),
    ("parent", "parent", None, None),
    ("other_parent", "parent", None, None),
)


def make_crypto(nonce_source: Any = None) -> AesGcmSupportNeedsCrypto:
    keyring = StaticSupportNeedsKeyring(
        encryption_keys={"enc-1": ENC_1, "enc-2": ENC_2},
        current_key_id="enc-1",
        fingerprint_keys={"fp-1": FP_1, "fp-2": FP_2},
        current_fingerprint_key_id="fp-1",
    )
    return (
        AesGcmSupportNeedsCrypto(keyring)
        if nonce_source is None
        else AesGcmSupportNeedsCrypto(keyring, nonce_source)
    )


class FakeGuard:
    """The two Teacher proofs as injected ports: sets of children and (subject, child) pairs."""

    def __init__(self) -> None:
        self.consent: set[str] = set()
        self.permission: set[tuple[str, str]] = set()

    def consent_effective(self, db: Any, profile: ManagedProfileModel) -> bool:
        return profile.child_id in self.consent

    def permission_granted(self, db: Any, principal: Any, profile: ManagedProfileModel) -> bool:
        return (principal.subject, profile.child_id) in self.permission


@dataclass
class Sn:
    app: FastAPI
    client: TestClient
    run: str
    organization_id: str
    class_id: str
    other_class_id: str
    suspended_class_id: str
    archived_class_id: str
    foreign_organization_id: str
    guard: FakeGuard
    subjects: dict[str, str] = field(default_factory=dict)

    @property
    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def runtime(self, **changes: Any) -> None:
        values: dict[str, Any] = {"crypto": make_crypto(), "teacher_guard": self.guard}
        values.update(changes)
        self.app.state.support_needs_runtime = SupportNeedsRuntime(**values)

    # -- Parent family
    def parent_path(self, profile_id: str) -> str:
        return f"/v1/parent/profiles/{profile_id}/support-needs"

    def parent_get(self, actor: str, profile_id: str) -> Any:
        return self.client.get(self.parent_path(profile_id), headers={ACTOR_HEADER: actor})

    def parent_put(
        self, actor: str, profile_id: str, body: dict[str, Any], *, key: str | None = None
    ) -> Any:
        return self.client.put(
            self.parent_path(profile_id),
            json=body,
            headers={ACTOR_HEADER: actor, "Idempotency-Key": key or f"k-{uuid4().hex[:12]}"},
        )

    # -- Teacher family
    def be1_path(self, child_id: str, class_id: str | None = None, org: str | None = None) -> str:
        return (
            f"/api/be1/v1/organizations/{org or self.organization_id}"
            f"/classes/{class_id or self.class_id}/profiles/{child_id}/support-needs"
        )

    def be1_get(self, actor: str, child_id: str, class_id: str | None = None) -> Any:
        return self.client.get(self.be1_path(child_id, class_id), headers={ACTOR_HEADER: actor})

    def be1_put(
        self,
        actor: str,
        child_id: str,
        body: dict[str, Any],
        *,
        key: str | None = None,
        class_id: str | None = None,
    ) -> Any:
        return self.client.put(
            self.be1_path(child_id, class_id),
            json=body,
            headers={ACTOR_HEADER: actor, "Idempotency-Key": key or f"k-{uuid4().hex[:12]}"},
        )


def body(expected: int = 0, category: str | None = CATEGORY, note: str | None = SENTINEL) -> dict:
    return {"expected_revision": expected, "category": category, "note": note}


def _class(class_id: str, organization_id: str, state: str) -> ClassroomModel:
    return ClassroomModel(
        class_id=class_id,
        organization_id=organization_id,
        display_name=f"Synthetic {class_id}"[:200],
        state=state,
        created_by="synthetic-t12c-seed",
        created_at=BASE_TIME,
    )


@pytest.fixture
def sn(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[Sn]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed T-12c acceptance tests")
    name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in name or "frc08_v4_t12c" not in name:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable frc08_v4_t12c*be1_acceptance")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("BE1 PostgreSQL runtime did not initialize")

    run = uuid4().hex[:10]
    organization_id = f"synthetic-t12c-{run}-org"
    foreign_organization_id = f"synthetic-t12c-{run}-foreign"
    class_id = f"synthetic-t12c-{run}-class-a"
    other_class_id = f"synthetic-t12c-{run}-class-b"
    suspended_class_id = f"synthetic-t12c-{run}-class-s"
    archived_class_id = f"synthetic-t12c-{run}-class-x"
    foreign_class_id = f"synthetic-t12c-{run}-foreign-1"
    subjects = {actor: f"synthetic-t12c-{run}-{actor}" for actor, *_rest in ACTORS}
    principals = {
        subject: VerifiedPrincipal(
            subject=subject, issuer=ISSUER, roles=frozenset(), token_id=f"synthetic-t12c-{n}"
        )
        for n, subject in enumerate(subjects.values())
    }
    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic T12c org",
                    state="active",
                ),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name="Synthetic T12c foreign org",
                    state="active",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                _class(class_id, organization_id, "active"),
                _class(other_class_id, organization_id, "active"),
                _class(suspended_class_id, organization_id, "suspended"),
                _class(archived_class_id, organization_id, "archived"),
                _class(foreign_class_id, foreign_organization_id, "active"),
            ]
        )
        db.add_all(
            [
                AdultIdentityModel(
                    subject=subjects[actor], issuer=ISSUER, state="active", account_role=account
                )
                for actor, account, _role, _scope in ACTORS
            ]
        )
        db.flush()
        scope_to_row = {
            "org": (organization_id, None),
            "class": (organization_id, class_id),
            "other": (organization_id, other_class_id),
            "suspended": (organization_id, suspended_class_id),
            "archived": (organization_id, archived_class_id),
            "orgwide": (organization_id, None),
            "foreign": (foreign_organization_id, None),
        }
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=scope_to_row[scope][0],
                    subject=subjects[actor],
                    class_id=scope_to_row[scope][1],
                    role=role,
                    active=True,
                )
                for actor, _account, role, scope in ACTORS
                if role is not None and scope is not None
            ]
        )

    async def verified_actor(request: Request) -> VerifiedPrincipal:
        return principals[subjects[request.headers[ACTOR_HEADER]]]

    app.dependency_overrides[get_verified_adult] = verified_actor
    app.dependency_overrides[get_parent_principal] = verified_actor
    guard = FakeGuard()
    with TestClient(app, client=("10.7.7.8", 12345), raise_server_exceptions=False) as client:
        state = Sn(
            app=app,
            client=client,
            run=run,
            organization_id=organization_id,
            class_id=class_id,
            other_class_id=other_class_id,
            suspended_class_id=suspended_class_id,
            archived_class_id=archived_class_id,
            foreign_organization_id=foreign_organization_id,
            guard=guard,
            subjects=subjects,
        )
        state.runtime()
        yield state
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


# --- fixtures of data --------------------------------------------------------------------------
def make_parent_profile(sn: Sn, owner: str = "parent") -> str:
    principal = VerifiedPrincipal(subject=sn.subjects[owner], issuer=ISSUER, roles=frozenset())
    with sn.factory() as db:
        result = SqlParentProfileRepository(db).create_profile(
            principal=principal,
            snapshot=ProfileSnapshot("Mina", 60, "thich ve ca"),
            idempotency_key=uuid4().hex,
            request_id="t12c",
        )
    return str(result.body["profile_id"])


def make_be1_profile(
    sn: Sn, suffix: str, *, class_id: str | None = None, state: str = "active"
) -> str:
    child_id = f"synthetic-t12c-{sn.run}-{suffix}"
    with sn.factory.begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=sn.organization_id,
                class_id=class_id or sn.class_id,
                display_name="Synthetic Mina Pham",
                age_months=60,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE",
                consent_id=None,
                consent_purpose_ref=None,
                data_origin="SYNTHETIC_DEV",
                state=state,
                created_by=sn.subjects["manager"],
                created_at=BASE_TIME,
            )
        )
    return child_id


def open_child(sn: Sn, suffix: str, *, class_id: str | None = None) -> str:
    """A profile the fake guard releases to the class Teacher (consent and permission)."""
    child = make_be1_profile(sn, suffix, class_id=class_id)
    sn.guard.consent.add(child)
    sn.guard.permission.add((sn.subjects["teacher"], child))
    return child


def parent_row(sn: Sn, profile_id: str) -> ParentProfileSupportNeedsModel | None:
    with sn.factory() as db:
        row = db.get(ParentProfileSupportNeedsModel, UUID(profile_id))
        if row is not None:
            db.expunge(row)
        return row


def be1_row(sn: Sn, child_id: str) -> Be1ProfileSupportNeedsModel | None:
    with sn.factory() as db:
        row = db.get(Be1ProfileSupportNeedsModel, child_id)
        if row is not None:
            db.expunge(row)
        return row


def parent_receipts(sn: Sn, profile_id: str) -> list[ParentCommandReceiptModel]:
    with sn.factory() as db:
        return list(
            db.scalars(
                select(ParentCommandReceiptModel).where(
                    ParentCommandReceiptModel.operation_scope == "put_support_needs",
                    ParentCommandReceiptModel.resource_scope == profile_id,
                )
            )
        )


def be1_receipts(sn: Sn) -> list[Be1CommandReceiptModel]:
    with sn.factory() as db:
        return [
            receipt
            for receipt in db.scalars(
                select(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.organization_id == sn.organization_id
                )
            )
            if "support-needs" in receipt.operation_scope
        ]


def audits(sn: Sn, action: str) -> list[CoreAuditEntryModel]:
    with sn.factory() as db:
        return list(
            db.scalars(
                select(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.organization_id == sn.organization_id,
                    CoreAuditEntryModel.action == action,
                )
            )
        )


def code_of(response: Any) -> str:
    return str(response.json().get("code"))


def assert_no_value(response: Any) -> None:
    assert SENTINEL not in response.text and CATEGORY not in response.text
    assert OTHER_NOTE not in response.text


# ==================== the Parent family ====================
def test_parent_reads_empty_writes_reads_and_the_row_holds_only_ciphertext(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    empty = sn.parent_get("parent", profile)
    assert empty.status_code == 200
    assert empty.json() == {
        "contract": "ParentSupportNeedsV1",
        "profile_id": profile,
        "revision": 0,
        "category": None,
        "note": None,
    }
    assert empty.headers["Cache-Control"] == "private, no-store"
    written = sn.parent_put("parent", profile, body(0), key="parent-1")
    assert written.status_code == 200
    assert written.json() == {
        "contract": "ParentSupportNeedsWriteV1",
        "profile_id": profile,
        "revision": 1,
    }
    assert_no_value(written) and written.headers["Cache-Control"] == "private, no-store"
    read = sn.parent_get("parent", profile)
    assert read.json() == {
        "contract": "ParentSupportNeedsV1",
        "profile_id": profile,
        "revision": 1,
        "category": CATEGORY,
        "note": SENTINEL,
    }
    row = parent_row(sn, profile)
    assert row is not None and row.revision == 1 and row.key_id == "enc-1"
    assert row.algorithm_version == 1 and len(row.nonce) == 12 and len(bytes(row.ciphertext)) >= 16
    for fragment in (SENTINEL, CATEGORY, "sensory", "note"):
        assert fragment.encode() not in bytes(row.ciphertext)
    with sn.factory() as db:  # the whole row, as text, holds nothing readable
        dumped = db.scalar(text("SELECT row_to_json(t)::text FROM parent.profile_support_needs t"))
    assert dumped is not None and SENTINEL not in dumped and "sensory" not in dumped
    (receipt,) = parent_receipts(sn, profile)
    assert set(receipt.response_body) == {"revision", "fp_v", "fp_kid"}
    assert receipt.response_body["revision"] == 1 and receipt.response_status == 200
    assert len(bytes(receipt.request_fingerprint)) == 32
    assert SENTINEL not in repr(receipt.response_body) + repr(bytes(receipt.request_fingerprint))


def test_parent_replay_returns_the_first_answer_without_touching_the_row(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    first = sn.parent_put("parent", profile, body(0), key="replay-1")
    before = parent_row(sn, profile)
    again = sn.parent_put("parent", profile, body(0), key="replay-1")
    assert again.status_code == 200 and again.json() == first.json()
    after = parent_row(sn, profile)
    assert before is not None and after is not None
    assert (before.ciphertext, before.nonce, before.revision, before.updated_at) == (
        after.ciphertext,
        after.nonce,
        after.revision,
        after.updated_at,
    )
    assert len(parent_receipts(sn, profile)) == 1
    # even after a second write, the old key still answers the first revision
    assert sn.parent_put("parent", profile, body(1, note=OTHER_NOTE)).status_code == 200
    replay = sn.parent_put("parent", profile, body(0), key="replay-1")
    assert replay.status_code == 200 and replay.json()["revision"] == 1


def test_parent_same_key_with_another_body_is_400_and_changes_nothing(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    assert sn.parent_put("parent", profile, body(0), key="mismatch-1").status_code == 200
    before = parent_row(sn, profile)
    for other in (
        body(0, note=OTHER_NOTE),
        body(0, category=None),
        body(1),
        body(0, category="Different"),
    ):
        response = sn.parent_put("parent", profile, other, key="mismatch-1")
        assert response.status_code == 400 and code_of(response) == "INVALID_IDEMPOTENCY_KEY"
        assert_no_value(response)
    after = parent_row(sn, profile)
    assert before is not None and after is not None and before.ciphertext == after.ciphertext
    assert after.revision == 1 and len(parent_receipts(sn, profile)) == 1


def test_parent_stale_is_409_with_the_current_version_and_is_not_receipted(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    assert sn.parent_put("parent", profile, body(0)).status_code == 200
    for expected in (0, 5):
        stale = sn.parent_put("parent", profile, body(expected, note=OTHER_NOTE))
        assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
        assert stale.json()["current_version"] == 1
        assert_no_value(stale)
    row = parent_row(sn, profile)
    assert row is not None and row.revision == 1
    assert len(parent_receipts(sn, profile)) == 1  # the stale answers are not receipted
    assert sn.parent_get("parent", profile).json()["note"] == SENTINEL


def test_parent_a_second_write_replaces_ciphertext_and_nonce_and_raises_the_revision(
    sn: Sn,
) -> None:
    profile = make_parent_profile(sn)
    sn.parent_put("parent", profile, body(0))
    first = parent_row(sn, profile)
    second_response = sn.parent_put("parent", profile, body(1, category=None, note=OTHER_NOTE))
    assert second_response.status_code == 200 and second_response.json()["revision"] == 2
    second = parent_row(sn, profile)
    assert first is not None and second is not None
    assert second.revision == 2 and second.created_at == first.created_at
    assert second.nonce != first.nonce and second.ciphertext != first.ciphertext
    assert second.updated_at >= first.updated_at
    read = sn.parent_get("parent", profile).json()
    assert (read["revision"], read["category"], read["note"]) == (2, None, OTHER_NOTE)
    assert len(parent_receipts(sn, profile)) == 2


def test_parent_foreign_and_non_parent_callers_get_the_uniform_404(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    sn.parent_put("parent", profile, body(0))
    for actor in ("other_parent", "teacher", "manager"):
        for response in (
            sn.parent_get(actor, profile),
            sn.parent_put(actor, profile, body(0, note=OTHER_NOTE)),
            sn.parent_put(actor, profile, {"extra": 1}),
        ):
            assert response.status_code == 404 and code_of(response) == "PROFILE_NOT_FOUND"
            assert_no_value(response)
    unknown = sn.parent_get("parent", str(uuid4()))
    assert unknown.status_code == 404 and code_of(unknown) == "PROFILE_NOT_FOUND"
    assert len(parent_receipts(sn, profile)) == 1
    row = parent_row(sn, profile)
    assert row is not None and row.revision == 1


def test_parent_a_profile_with_a_pending_deletion_refuses_both_routes(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    sn.parent_put("parent", profile, body(0), key="before-delete")
    deleted = sn.client.request(
        "DELETE",
        f"/v1/parent/profiles/{profile}",
        headers={ACTOR_HEADER: "parent", "Idempotency-Key": "delete-1"},
    )
    assert deleted.status_code == 202
    for response in (
        sn.parent_get("parent", profile),
        sn.parent_put("parent", profile, body(1, note=OTHER_NOTE)),
        sn.parent_put("parent", profile, body(0), key="before-delete"),  # a replay is refused too
    ):
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"
        assert_no_value(response)
    row = parent_row(sn, profile)
    assert row is not None and row.revision == 1


def test_parent_two_keys_at_one_revision_one_wins_and_one_is_stale(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    barrier = Barrier(2)

    def call(n: int) -> Any:
        barrier.wait()
        return sn.parent_put("parent", profile, body(0, note=f"{SENTINEL}-{n}"), key=f"race-{n}")

    with ThreadPoolExecutor(2) as pool:
        statuses = sorted(r.status_code for r in pool.map(call, range(2)))
    assert statuses == [200, 409]
    row = parent_row(sn, profile)
    assert row is not None and row.revision == 1 and len(parent_receipts(sn, profile)) == 1


def test_parent_the_same_key_concurrent_commits_one_write_and_every_caller_gets_it(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    barrier = Barrier(4)

    def call(_: int) -> Any:
        barrier.wait()
        return sn.parent_put("parent", profile, body(0), key="same-1")

    with ThreadPoolExecutor(4) as pool:
        responses = list(pool.map(call, range(4)))
    assert [r.status_code for r in responses] == [200] * 4
    assert {r.json()["revision"] for r in responses} == {1}
    row = parent_row(sn, profile)
    assert row is not None and row.revision == 1 and len(parent_receipts(sn, profile)) == 1


def test_parent_a_failure_in_the_transaction_rolls_back_the_row_and_the_receipt(sn: Sn) -> None:
    profile = make_parent_profile(sn)

    class ShortMac(AesGcmSupportNeedsCrypto):
        def fingerprint(self, **kwargs: Any) -> bytes:
            return super().fingerprint(**kwargs)[:31]  # the receipt CHECK (32 bytes) refuses it

    healthy = make_crypto()
    sn.runtime(crypto=ShortMac(healthy._keyring))  # noqa: SLF001
    response = sn.parent_put("parent", profile, body(0))
    assert response.status_code >= 500 or response.status_code == 503
    assert_no_value(response)
    assert parent_row(sn, profile) is None and parent_receipts(sn, profile) == []
    sn.runtime()
    assert sn.parent_put("parent", profile, body(0)).status_code == 200


def test_parent_a_tampered_ciphertext_is_a_generic_503(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    sn.parent_put("parent", profile, body(0))
    with sn.factory.begin() as db:  # the guard trigger is lifted inside this transaction only
        db.execute(text("ALTER TABLE parent.profile_support_needs DISABLE TRIGGER USER"))
        db.execute(
            text(
                "UPDATE parent.profile_support_needs SET ciphertext = "
                "set_byte(ciphertext, 0, get_byte(ciphertext, 0) # 1) WHERE parent_profile_id = :p"
            ),
            {"p": profile},
        )
        db.execute(text("ALTER TABLE parent.profile_support_needs ENABLE TRIGGER USER"))
    for response in (sn.parent_get("parent", profile),):
        assert response.status_code == 503 and code_of(response) == "SUPPORT_NEEDS_UNAVAILABLE"
        assert_no_value(response)
        assert "enc-1" not in response.text and "key" not in response.json()["message"].lower()


def test_without_a_key_source_both_families_answer_503_after_authorization(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    child = open_child(sn, "nokey")
    sn.runtime(crypto=None)
    parent = (
        sn.parent_get("parent", profile),
        sn.parent_put("parent", profile, body(0)),
        sn.parent_put("parent", profile, {"junk": 1}),  # before the body is read
    )
    teacher = (sn.be1_get("teacher", child), sn.be1_put("teacher", child, body(0)))
    for response in (*parent, *teacher):
        assert response.status_code == 503 and code_of(response) == "SUPPORT_NEEDS_UNAVAILABLE"
        assert_no_value(response)
    # a stranger is denied first, never told about the configuration
    assert sn.parent_get("other_parent", profile).status_code == 404
    assert sn.be1_get("other_teacher", child).status_code == 404
    assert parent_row(sn, profile) is None and be1_row(sn, child) is None


def test_the_production_default_has_no_runtime_so_both_families_are_unavailable(sn: Sn) -> None:
    profile = make_parent_profile(sn)
    child = make_be1_profile(sn, "default")
    del sn.app.state.support_needs_runtime  # what production composes today: nothing
    assert sn.parent_get("parent", profile).status_code == 503
    # the default Teacher guard denies first: no permission exists, so the uniform 404 before 503
    assert sn.be1_get("teacher", child).status_code == 404


def test_parent_projections_and_the_logs_never_carry_the_note(
    sn: Sn, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    profile = make_parent_profile(sn)
    sn.parent_put("parent", profile, body(0))
    sn.parent_get("parent", profile)
    sn.parent_put("parent", profile, body(9))  # stale
    sn.parent_put("parent", profile, {"expected_revision": 0, "category": None, "note": ""})
    for response in (
        sn.client.get(f"/v1/parent/profiles/{profile}", headers={ACTOR_HEADER: "parent"}),
        sn.client.get("/v1/parent/profiles", headers={ACTOR_HEADER: "parent"}),
        sn.client.get(
            f"/v1/parent/profiles/{profile}/context-entries", headers={ACTOR_HEADER: "parent"}
        ),
    ):
        assert response.status_code == 200
        assert_no_value(response)
        assert "support" not in response.text.lower()
    assert SENTINEL not in caplog.text and CATEGORY not in caplog.text


# ==================== the Teacher family ====================
def test_the_default_guard_denies_every_profile_with_the_uniform_404_and_no_audit(sn: Sn) -> None:
    sn.runtime(teacher_guard=None)  # the production default guard over the real consent lookup
    child = make_be1_profile(sn, "default-guard")  # synthetic, no consent, no permission
    # V4-B T-12b-fix (owner decision Q3, T-12c review P3-3): the permission is asked before the
    # consent, so a Teacher without it learns nothing about the consent state and no audit row
    # is written.
    unknown = sn.be1_get("teacher", f"{child}-missing")
    for response in (sn.be1_get("teacher", child), sn.be1_put("teacher", child, body(0))):
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
        assert response.json()["message"] == unknown.json()["message"]
        assert_no_value(response)
    assert audits(sn, "profile.support_needs.read") == []
    assert audits(sn, "profile.support_needs.write") == []
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_a_permission_without_an_effective_consent_is_the_audited_409(sn: Sn) -> None:
    child = make_be1_profile(sn, "perm-no-consent")
    sn.guard.permission.add((sn.subjects["teacher"], child))  # permission, no consent
    for response in (sn.be1_get("teacher", child), sn.be1_put("teacher", child, body(0))):
        assert response.status_code == 409 and code_of(response) == "CONSENT_NOT_EFFECTIVE"
        assert_no_value(response)
    denied = audits(sn, "profile.support_needs.read") + audits(sn, "profile.support_needs.write")
    assert len(denied) == 2 and {a.decision for a in denied} == {"denied_consent_pending"}
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_a_pending_deletion_request_is_the_uniform_404_with_no_audit_row(sn: Sn) -> None:
    child = open_child(sn, "deleting")
    assert sn.be1_put("teacher", child, body(0), key="del-1").status_code == 200
    with sn.factory() as db:
        db.add(
            DataLifecycleRequestModel(
                request_id=str(uuid4()),
                organization_id=sn.organization_id,
                request_type="delete",
                target_ref=child,
                state="requested",
                requested_by="test",
            )
        )
        db.commit()
    unknown = sn.be1_get("teacher", f"{child}-missing")
    for response in (
        sn.be1_get("teacher", child),
        sn.be1_put("teacher", child, body(1, note=OTHER_NOTE)),
        sn.be1_put("teacher", child, body(0), key="del-1"),  # a replay is denied too
    ):
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
        assert response.json()["message"] == unknown.json()["message"]
        assert_no_value(response)
    assert audits(sn, "profile.support_needs.read") == []
    row = be1_row(sn, child)
    assert row is not None and row.revision == 1


def test_a_revoked_consent_of_a_real_profile_is_the_uniform_404_with_no_audit_row(sn: Sn) -> None:
    """Q3: a withdrawn grant hides the profile before the permission and consent are asked."""
    child = f"synthetic-t12c-{sn.run}-revoked"
    with sn.factory.begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child,
                organization_id=sn.organization_id,
                class_id=sn.class_id,
                display_name="Synthetic Mina Pham",
                age_months=60,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=str(uuid4()),
                consent_purpose_ref="synthetic-purpose-revoked",
                data_origin="REAL",
                state="active",
                created_by=sn.subjects["manager"],
                created_at=BASE_TIME,
            )
        )
        db.add(
            ConsentRecordModel(
                consent_id=str(uuid4()),
                organization_id=sn.organization_id,
                class_id=sn.class_id,
                child_id=child,
                purpose_ref="synthetic-purpose-revoked",
                state="revoked",
                recorded_by=sn.subjects["manager"],
            )
        )
    sn.guard.consent.add(child)
    sn.guard.permission.add((sn.subjects["teacher"], child))
    unknown = sn.be1_get("teacher", f"{child}-missing")
    for response in (sn.be1_get("teacher", child), sn.be1_put("teacher", child, body(0))):
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
        assert response.json()["message"] == unknown.json()["message"]
        assert_no_value(response)
    assert audits(sn, "profile.support_needs.read") == []
    assert audits(sn, "profile.support_needs.write") == []
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_a_diagnosis_in_the_category_or_the_note_is_400_and_writes_nothing(sn: Sn) -> None:
    """BR-20 (T-12b-fix): the Teacher route refuses it with a field code and no echo."""
    child = open_child(sn, "br20")
    for payload, field_name in (
        (body(0, category="chẩn đoán tự kỷ", note=None), "category"),
        (body(0, category=None, note=f"ADHD {SENTINEL}"), "note"),
    ):
        response = sn.be1_put("teacher", child, payload)
        assert response.status_code == 400, response.text
        assert {"field": field_name, "code": "DIAGNOSIS_LIKE"} in response.json()["field_errors"]
        assert SENTINEL not in response.text
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_a_consent_without_the_permission_is_the_uniform_404(sn: Sn) -> None:
    child = make_be1_profile(sn, "no-permission")
    sn.guard.consent.add(child)  # effective consent, no narrow permission
    unknown = sn.be1_get("teacher", f"{child}-missing")
    for response in (sn.be1_get("teacher", child), sn.be1_put("teacher", child, body(0))):
        assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
        assert response.json()["message"] == unknown.json()["message"]
    assert be1_row(sn, child) is None


def test_the_role_and_scope_matrix_is_closed(sn: Sn) -> None:
    child = open_child(sn, "matrix")
    for actor in ("other_teacher", "orgwide_teacher", "foreign_teacher", "parent"):
        for response in (sn.be1_get(actor, child), sn.be1_put(actor, child, body(0))):
            assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND", actor
            assert_no_value(response)
    # a School Manager never reads support needs: 403 (a count of roster is not a permission)
    for response in (sn.be1_get("manager", child), sn.be1_put("manager", child, body(0))):
        assert response.status_code == 403, response.text
        assert_no_value(response)
    # the wrong organization and the wrong class are the same 404
    assert sn.be1_get("teacher", child, class_id=sn.other_class_id).status_code == 404
    assert (
        sn.client.get(
            sn.be1_path(child, org=sn.foreign_organization_id), headers={ACTOR_HEADER: "teacher"}
        ).status_code
        == 404
    )
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_an_unknown_or_inactive_profile_is_the_uniform_404(sn: Sn) -> None:
    gone = make_be1_profile(sn, "inactive", state="archived")
    sn.guard.consent.add(gone)
    sn.guard.permission.add((sn.subjects["teacher"], gone))
    for child in (gone, "synthetic-no-such-child"):
        assert sn.be1_get("teacher", child).status_code == 404
        assert sn.be1_put("teacher", child, body(0)).status_code == 404


def test_the_teacher_cycle_read_write_replay_stale_mismatch_and_update(sn: Sn) -> None:
    child = open_child(sn, "cycle")
    empty = sn.be1_get("teacher", child)
    assert empty.status_code == 200 and empty.headers["Cache-Control"] == "private, no-store"
    assert empty.json() == {
        "contract": "Be1SupportNeedsV1",
        "child_id": child,
        "revision": 0,
        "category": None,
        "note": None,
    }
    first = sn.be1_put("teacher", child, body(0), key="cycle-1")
    assert first.status_code == 200
    assert first.json() == {"contract": "Be1SupportNeedsWriteV1", "child_id": child, "revision": 1}
    assert_no_value(first)
    read = sn.be1_get("teacher", child)
    assert read.json()["revision"] == 1 and read.json()["note"] == SENTINEL
    assert read.json()["category"] == CATEGORY
    row = be1_row(sn, child)
    assert row is not None and row.key_id == "enc-1" and len(row.nonce) == 12
    for fragment in (SENTINEL, CATEGORY, "sensory"):
        assert fragment.encode() not in bytes(row.ciphertext)
    # replay: the stored answer, nothing re-encrypted
    replay = sn.be1_put("teacher", child, body(0), key="cycle-1")
    assert replay.status_code == 200 and replay.json() == first.json()
    same = be1_row(sn, child)
    assert same is not None and same.ciphertext == row.ciphertext and same.nonce == row.nonce
    # the same key with another request: 400, nothing changes
    mismatch = sn.be1_put("teacher", child, body(0, note=OTHER_NOTE), key="cycle-1")
    assert mismatch.status_code == 400 and code_of(mismatch) == "INVALID_IDEMPOTENCY_KEY"
    assert_no_value(mismatch)
    # a stale revision: 409 with the current version, not receipted
    stale = sn.be1_put("teacher", child, body(0, note=OTHER_NOTE))
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == 1
    assert_no_value(stale)
    assert len(be1_receipts(sn)) == 1
    # an update raises the revision and replaces the nonce and the ciphertext
    second = sn.be1_put("teacher", child, body(1, category=None, note=OTHER_NOTE))
    assert second.status_code == 200 and second.json()["revision"] == 2
    updated = be1_row(sn, child)
    assert updated is not None and updated.revision == 2 and updated.nonce != row.nonce
    assert updated.ciphertext != row.ciphertext
    after = sn.be1_get("teacher", child).json()
    assert (after["revision"], after["category"], after["note"]) == (2, None, OTHER_NOTE)
    # the receipts hold references only
    receipts = be1_receipts(sn)
    assert len(receipts) == 2
    for receipt in receipts:
        assert set(receipt.response_json) == {"revision", "fp_v", "fp_kid"}
        assert len(receipt.request_fingerprint) == 64 and receipt.request_fingerprint.isalnum()
        dump = repr(receipt.__dict__) + repr(receipt.response_json)
        assert SENTINEL not in dump and OTHER_NOTE not in dump and CATEGORY not in dump
    for audit in audits(sn, "profile.support_needs.write"):
        dump = repr(audit.__dict__)
        assert SENTINEL not in dump and OTHER_NOTE not in dump and CATEGORY not in dump
    assert len(audits(sn, "profile.support_needs.write")) == 2


def test_the_stale_version_is_shown_only_after_every_proof(sn: Sn) -> None:
    child = open_child(sn, "stale-proof")
    sn.be1_put("teacher", child, body(0))
    for actor in ("other_teacher", "orgwide_teacher", "parent"):
        probe = sn.be1_put(actor, child, body(7))
        assert probe.status_code == 404 and "current_version" not in probe.text
    sn.guard.permission.discard((sn.subjects["teacher"], child))
    probe = sn.be1_put("teacher", child, body(7))
    assert probe.status_code == 404 and "current_version" not in probe.text
    sn.guard.permission.add((sn.subjects["teacher"], child))
    assert sn.be1_put("teacher", child, body(7)).status_code == 409


def test_a_revoked_consent_or_permission_denies_reads_writes_and_replays(sn: Sn) -> None:
    child = open_child(sn, "revoked")
    assert sn.be1_put("teacher", child, body(0), key="rev-1").status_code == 200
    sn.guard.consent.discard(child)  # the consent is revoked
    for response in (
        sn.be1_get("teacher", child),
        sn.be1_put("teacher", child, body(1, note=OTHER_NOTE)),
        sn.be1_put("teacher", child, body(0), key="rev-1"),  # a replay is denied too
    ):
        assert response.status_code == 409 and code_of(response) == "CONSENT_NOT_EFFECTIVE"
        assert_no_value(response)
    sn.guard.consent.add(child)
    sn.guard.permission.discard((sn.subjects["teacher"], child))  # the permission is withdrawn
    for response in (
        sn.be1_get("teacher", child),
        sn.be1_put("teacher", child, body(0), key="rev-1"),
    ):
        assert response.status_code == 404
        assert_no_value(response)
    row = be1_row(sn, child)
    assert row is not None and row.revision == 1


def test_the_class_state_gates_the_two_routes(sn: Sn) -> None:
    suspended = open_child(sn, "susp", class_id=sn.suspended_class_id)
    archived = open_child(sn, "arch", class_id=sn.archived_class_id)
    for child, actor, cls in (
        (suspended, "suspended_teacher", sn.suspended_class_id),
        (archived, "archived_teacher", sn.archived_class_id),
    ):
        sn.guard.permission.add((sn.subjects[actor], child))
        assert cls
    read = sn.be1_get("suspended_teacher", suspended, class_id=sn.suspended_class_id)
    assert read.status_code == 200 and read.json()["revision"] == 0  # a suspended class is readable
    write = sn.be1_put("suspended_teacher", suspended, body(0), class_id=sn.suspended_class_id)
    assert write.status_code == 409 and be1_row(sn, suspended) is None
    hidden = sn.be1_get("archived_teacher", archived, class_id=sn.archived_class_id)
    assert hidden.status_code == 404  # an archived class is gone for a Teacher
    assert sn.be1_put(
        "archived_teacher", archived, body(0), class_id=sn.archived_class_id
    ).status_code in {404, 409}


def test_the_teacher_key_and_body_are_validated_without_echo_or_write(sn: Sn) -> None:
    child = open_child(sn, "validate")
    for payload in (
        {"expected_revision": 0, "category": None, "note": None},
        {"expected_revision": 0, "category": "x" * 81, "note": SENTINEL},
        {"expected_revision": 0, "category": None, "note": SENTINEL + "\x00"},
        {"expected_revision": 0, "category": None, "note": SENTINEL, "extra": SENTINEL},
        {"expected_revision": -1, "category": None, "note": SENTINEL},
        {"category": None, "note": SENTINEL},
        {"expected_revision": 0, "note": SENTINEL},
    ):
        response = sn.be1_put("teacher", child, payload)
        assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST", payload
        assert_no_value(response)
    missing_key = sn.client.put(sn.be1_path(child), json=body(0), headers={ACTOR_HEADER: "teacher"})
    assert missing_key.status_code == 400
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_the_teacher_two_keys_at_one_revision_one_wins_and_one_is_stale(sn: Sn) -> None:
    child = open_child(sn, "race")
    barrier = Barrier(2)

    def call(n: int) -> Any:
        barrier.wait()
        return sn.be1_put("teacher", child, body(0, note=f"{SENTINEL}-{n}"), key=f"race-{n}")

    with ThreadPoolExecutor(2) as pool:
        statuses = sorted(r.status_code for r in pool.map(call, range(2)))
    assert statuses == [200, 409]
    row = be1_row(sn, child)
    assert row is not None and row.revision == 1 and len(be1_receipts(sn)) == 1


def test_the_teacher_same_key_concurrent_commits_one_write_and_every_caller_gets_it(sn: Sn) -> None:
    child = open_child(sn, "same")
    barrier = Barrier(4)

    def call(_: int) -> Any:
        barrier.wait()
        return sn.be1_put("teacher", child, body(0), key="same-1")

    with ThreadPoolExecutor(4) as pool:
        responses = list(pool.map(call, range(4)))
    assert [r.status_code for r in responses] == [200] * 4
    assert {r.json()["revision"] for r in responses} == {1}
    row = be1_row(sn, child)
    assert row is not None and row.revision == 1 and len(be1_receipts(sn)) == 1


def test_the_teacher_failure_in_the_transaction_rolls_back_row_receipt_and_audit(
    sn: Sn, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = open_child(sn, "rollback")

    def boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("synthetic failure after the row was staged")

    original = be1_registry.audit
    monkeypatch.setattr(be1_registry, "audit", boom)
    failed = sn.be1_put("teacher", child, body(0))
    assert failed.status_code == 500
    assert_no_value(failed)
    monkeypatch.setattr(be1_registry, "audit", original)
    assert be1_row(sn, child) is None and be1_receipts(sn) == []
    assert audits(sn, "profile.support_needs.write") == []
    assert sn.be1_put("teacher", child, body(0)).status_code == 200


def test_the_teacher_receipt_check_failure_rolls_the_row_back(sn: Sn) -> None:
    child = open_child(sn, "short-mac")

    class ShortMac(AesGcmSupportNeedsCrypto):
        def fingerprint(self, **kwargs: Any) -> bytes:
            return super().fingerprint(**kwargs)[:30]  # 60 hex characters: the CHECK says 64

    sn.runtime(crypto=ShortMac(make_crypto()._keyring))  # noqa: SLF001
    response = sn.be1_put("teacher", child, body(0))
    assert response.status_code in {409, 500, 503}
    assert_no_value(response)
    assert be1_row(sn, child) is None and be1_receipts(sn) == []


def test_the_teacher_tampered_ciphertext_is_a_generic_503(sn: Sn) -> None:
    child = open_child(sn, "tamper")
    sn.be1_put("teacher", child, body(0))
    with sn.factory.begin() as db:
        db.execute(text("ALTER TABLE be1_profile_support_needs DISABLE TRIGGER USER"))
        db.execute(
            text("UPDATE be1_profile_support_needs SET revision = 5 WHERE child_id = :c"),
            {"c": child},
        )  # a ciphertext moved to another revision no longer authenticates
        db.execute(text("ALTER TABLE be1_profile_support_needs ENABLE TRIGGER USER"))
    response = sn.be1_get("teacher", child)
    assert response.status_code == 503 and code_of(response) == "SUPPORT_NEEDS_UNAVAILABLE"
    assert_no_value(response)


def test_a_ciphertext_copied_to_another_profile_does_not_open(sn: Sn) -> None:
    first, second = open_child(sn, "copy-a"), open_child(sn, "copy-b")
    sn.be1_put("teacher", first, body(0))
    sn.be1_put("teacher", second, body(0, note=OTHER_NOTE))
    row = be1_row(sn, first)
    assert row is not None
    with sn.factory.begin() as db:
        db.execute(text("ALTER TABLE be1_profile_support_needs DISABLE TRIGGER USER"))
        # (key_id, nonce) is unique, so the first record gives up its nonce before the copy
        db.execute(
            text("UPDATE be1_profile_support_needs SET nonce = :t WHERE child_id = :c"),
            {"t": bytes([10]) * 12, "c": first},
        )
        db.execute(
            text(
                "UPDATE be1_profile_support_needs SET ciphertext = :c, nonce = :n, key_id = :k "
                "WHERE child_id = :child"
            ),
            {"c": bytes(row.ciphertext), "n": bytes(row.nonce), "k": row.key_id, "child": second},
        )
        db.execute(text("ALTER TABLE be1_profile_support_needs ENABLE TRIGGER USER"))
    response = sn.be1_get("teacher", second)
    assert response.status_code == 503 and code_of(response) == "SUPPORT_NEEDS_UNAVAILABLE"
    assert_no_value(response)


def test_a_long_scope_is_hashed_to_fit_the_receipt_column(sn: Sn) -> None:
    long_org, long_class = f"synthetic-t12c-{sn.run}-" + "o" * 100, "c" * 100
    child = "k" * 128
    with sn.factory.begin() as db:
        db.add(OrganizationModel(organization_id=long_org, display_name="Long", state="active"))
        db.flush()
        db.add(_class(long_class, long_org, "active"))
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=long_org,
                subject=sn.subjects["teacher"],
                class_id=long_class,
                role="teacher",
                active=True,
            )
        )
        db.add(
            ManagedProfileModel(
                child_id=child,
                organization_id=long_org,
                class_id=long_class,
                display_name="Synthetic Long",
                age_months=60,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE",
                data_origin="SYNTHETIC_DEV",
                state="active",
                created_by="x",
                created_at=BASE_TIME,
            )
        )
    sn.guard.consent.add(child)
    sn.guard.permission.add((sn.subjects["teacher"], child))
    path = (
        f"/api/be1/v1/organizations/{long_org}/classes/{long_class}/profiles/{child}/support-needs"
    )
    scope = be1_registry._support_receipt_scope(long_org, long_class, child)  # noqa: SLF001
    assert len(scope) <= 256 and scope.startswith(
        "PUT /organizations/classes/profiles/support-needs#"
    )
    short = be1_registry._support_receipt_scope("o", "c", "k")  # noqa: SLF001
    assert short == "PUT /organizations/o/classes/c/profiles/k/support-needs"
    headers = {ACTOR_HEADER: "teacher", "Idempotency-Key": "long-1"}
    first = sn.client.put(path, json=body(0), headers=headers)
    assert first.status_code == 200, first.text
    assert sn.client.put(path, json=body(0), headers=headers).json() == first.json()
    with sn.factory() as db:
        stored = db.scalar(
            select(Be1CommandReceiptModel.operation_scope).where(
                Be1CommandReceiptModel.organization_id == long_org
            )
        )
    assert stored == scope


def test_the_roster_and_the_revision_history_never_carry_the_note(sn: Sn) -> None:
    child = open_child(sn, "projection")
    sn.be1_put("teacher", child, body(0))
    base = f"/api/be1/v1/organizations/{sn.organization_id}/classes/{sn.class_id}/profiles"
    for url in (base, f"{base}/{child}/revisions"):
        response = sn.client.get(url, headers={ACTOR_HEADER: "teacher"})
        assert response.status_code in {200, 409}
        assert_no_value(response)
        assert "support" not in response.text.lower()


def test_teacher_logs_and_errors_never_carry_the_note(
    sn: Sn, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    child = open_child(sn, "logs")
    responses = [
        sn.be1_put("teacher", child, body(0), key="logs-1"),
        sn.be1_get("teacher", child),
        sn.be1_put("teacher", child, body(0, note=OTHER_NOTE), key="logs-1"),
        sn.be1_put("teacher", child, body(5)),
        sn.be1_put("teacher", child, {"expected_revision": 0, "category": None, "note": ""}),
    ]
    assert [r.status_code for r in responses] == [200, 200, 400, 409, 400]
    for response in responses[2:]:
        assert_no_value(response)
    assert SENTINEL not in caplog.text and CATEGORY not in caplog.text
    assert OTHER_NOTE not in caplog.text


# ==================== the database guarantees ====================
_TABLES = {
    "parent": ("parent.profile_support_needs", "parent_profile_id"),
    "be1": ("be1_profile_support_needs", "child_id"),
}


def _insert_profile(sn: Sn, family: str) -> str:
    if family == "parent":
        return make_parent_profile(sn)
    return make_be1_profile(sn, f"db-{uuid4().hex[:8]}")


def _raw_row(family: str, key: str, **changes: Any) -> dict[str, Any]:
    nonce = uuid4().bytes[:12]
    values: dict[str, Any] = {
        "k": key,
        "rev": 1,
        "c": b"\x01" * 24,
        "n": nonce,
        "kid": "enc-1",
        "alg": 1,
    }
    values.update(changes)
    return values


def _insert_sql(family: str) -> str:
    table, key = _TABLES[family]
    cast = "CAST(:k AS uuid)" if family == "parent" else ":k"
    return (
        f"INSERT INTO {table} ({key}, revision, ciphertext, nonce, key_id, algorithm_version) "
        f"VALUES ({cast}, :rev, :c, :n, :kid, :alg)"
    )


@pytest.mark.parametrize("family", ["parent", "be1"])
@pytest.mark.parametrize(
    "bad",
    [
        {"rev": 0},
        {"rev": -3},
        {"c": b"\x01" * 15},
        {"c": b"\x01" * 16385},
        {"n": b"\x02" * 11},
        {"n": b"\x02" * 13},
        {"kid": ""},
        {"kid": "k" * 129},
        {"alg": 2},
        {"alg": 0},
    ],
)
def test_the_database_checks_refuse_a_malformed_row(
    sn: Sn, family: str, bad: dict[str, Any]
) -> None:
    key = _insert_profile(sn, family)
    with pytest.raises((IntegrityError, DataError)), sn.factory.begin() as db:
        db.execute(text(_insert_sql(family)), _raw_row(family, key, **bad))
    with sn.factory.begin() as db:  # the unmodified row is accepted
        db.execute(text(_insert_sql(family)), _raw_row(family, key))


@pytest.mark.parametrize("family", ["parent", "be1"])
def test_the_update_guard_and_the_delete_refusal(sn: Sn, family: str) -> None:
    table, key_column = _TABLES[family]
    key = _insert_profile(sn, family)
    other = _insert_profile(sn, family)
    cast = "CAST(:k AS uuid)" if family == "parent" else ":k"
    with sn.factory.begin() as db:
        db.execute(text(_insert_sql(family)), _raw_row(family, key))

    def attempt(statement: str, **values: Any) -> None:
        with pytest.raises((IntegrityError, DBAPIError)), sn.factory.begin() as db:
            db.execute(text(statement), {"k": key, "o": other, "n": uuid4().bytes[:12], **values})

    where = f"WHERE {key_column} = {cast}"
    attempt(f"UPDATE {table} SET revision = 3 {where}")  # not +1
    attempt(f"UPDATE {table} SET revision = 1, nonce = :n {where}")  # not +1
    attempt(f"UPDATE {table} SET revision = 2 {where}")  # the nonce did not change
    attempt(
        f"UPDATE {table} SET revision = 2, nonce = :n, {key_column} = "
        f"{'CAST(:o AS uuid)' if family == 'parent' else ':o'} {where}"
    )  # the profile key is immutable
    attempt(f"UPDATE {table} SET revision = 2, nonce = :n, created_at = now() {where}")
    attempt(f"DELETE FROM {table} {where}")  # no ordinary delete
    attempt(f"DELETE FROM {table}")
    with sn.factory.begin() as db:  # the legal step: revision + 1 and a new nonce
        db.execute(
            text(f"UPDATE {table} SET revision = 2, nonce = :n {where}"),
            {"k": key, "n": uuid4().bytes[:12]},
        )


@pytest.mark.parametrize("family", ["parent", "be1"])
def test_a_nonce_is_unique_per_key_label_and_a_profile_is_required(sn: Sn, family: str) -> None:
    first, second = _insert_profile(sn, family), _insert_profile(sn, family)
    shared = b"\x07" * 12
    with sn.factory.begin() as db:
        db.execute(text(_insert_sql(family)), _raw_row(family, first, n=shared))
        db.execute(text(_insert_sql(family)), _raw_row(family, second, n=shared, kid="enc-2"))
    third = _insert_profile(sn, family)
    with pytest.raises(IntegrityError), sn.factory.begin() as db:
        db.execute(text(_insert_sql(family)), _raw_row(family, third, n=shared))  # same label
    missing = str(uuid4()) if family == "parent" else "synthetic-no-such-profile"
    with pytest.raises(IntegrityError), sn.factory.begin() as db:
        db.execute(text(_insert_sql(family)), _raw_row(family, missing))


def test_a_profile_with_a_support_record_cannot_be_deleted(sn: Sn) -> None:
    child = _insert_profile(sn, "be1")
    with sn.factory.begin() as db:
        db.execute(text(_insert_sql("be1")), _raw_row("be1", child))
    with pytest.raises(IntegrityError), sn.factory.begin() as db:
        db.execute(text("DELETE FROM be1_managed_profiles WHERE child_id = :c"), {"c": child})
    profile = _insert_profile(sn, "parent")
    with sn.factory.begin() as db:
        db.execute(text(_insert_sql("parent")), _raw_row("parent", profile))
    with pytest.raises(IntegrityError), sn.factory.begin() as db:
        db.execute(
            text("DELETE FROM parent.child_profiles WHERE parent_profile_id = CAST(:p AS uuid)"),
            {"p": profile},
        )


def test_the_unique_nonce_refuses_a_repeated_nonce_through_the_route(sn: Sn) -> None:
    profiles = [make_parent_profile(sn), make_parent_profile(sn)]
    sn.runtime(crypto=make_crypto(nonce_source=lambda: b"\x09" * 12))  # a broken nonce source
    assert sn.parent_put("parent", profiles[0], body(0)).status_code == 200
    again = sn.parent_put("parent", profiles[1], body(0))
    assert again.status_code == 503 and code_of(again) == "SUPPORT_NEEDS_UNAVAILABLE"
    assert parent_row(sn, profiles[1]) is None and parent_receipts(sn, profiles[1]) == []


# ==================== migration round trips ====================
@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T12C_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip(
            "set T12C_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database"
        )
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v4_t12c", "roundtrip")):
        pytest.fail(
            "T12C_ROUNDTRIP_DATABASE_URL must name a frc08_v4_t12c*roundtrip*be1_acceptance db"
        )
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _versions(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {str(v) for v in connection.scalars(text("SELECT version_num FROM alembic_version"))}


def _exists(engine: Engine, regclass: str) -> bool:
    with engine.connect() as connection:
        return bool(connection.scalar(text("SELECT to_regclass(:r)"), {"r": regclass}))


def test_the_parent_migration_round_trips_and_refuses_data(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    head, parent = "20261121_psn_0001", "20261121_pce_0001"
    command.upgrade(config, "heads")
    assert head in _versions(engine) and parent not in _versions(engine)
    assert _exists(engine, "parent.profile_support_needs")
    command.downgrade(config, parent)  # an empty table: the guard passes (explicit target)
    assert not _exists(engine, "parent.profile_support_needs") and parent in _versions(engine)
    with engine.connect() as connection:  # the trigger functions went with the table
        assert not connection.scalar(
            text(
                "SELECT count(*) FROM pg_proc WHERE proname = 'guard_profile_support_needs_update'"
            )
        )
    command.upgrade(config, "heads")
    assert head in _versions(engine) and _exists(engine, "parent.profile_support_needs")
    with Session(engine) as db:  # a real profile and its first revision, through the repository
        created = SqlParentProfileRepository(db).create_profile(
            principal=VerifiedPrincipal(subject="rt-subject", issuer=ISSUER, roles=frozenset()),
            snapshot=ProfileSnapshot("Mina", 60, None),
            idempotency_key="rt-1",
            request_id="t12c-rt",
        )
    with engine.begin() as connection:
        connection.execute(
            text(_insert_sql("parent")), _raw_row("parent", str(created.body["profile_id"]))
        )
    with pytest.raises(Exception, match="downgrade refused"):
        command.downgrade(config, parent)
    assert _exists(engine, "parent.profile_support_needs") and head in _versions(engine)


def test_the_be1_migration_round_trips_and_refuses_data(roundtrip: tuple[Config, Engine]) -> None:
    config, engine = roundtrip
    head, parent = "20261123_ppg_0001", "20261121_bpr_0001"  # the purge revision sits on psn_0002
    command.upgrade(config, "heads")
    assert head in _versions(engine) and parent not in _versions(engine)
    assert _exists(engine, "public.be1_profile_support_needs")
    command.downgrade(config, parent)
    assert not _exists(engine, "public.be1_profile_support_needs") and parent in _versions(engine)
    assert _exists(engine, "public.be1_profile_revisions")  # T-12b stays
    command.upgrade(config, "heads")
    assert head in _versions(engine) and _exists(engine, "public.be1_profile_support_needs")
    org, cls, child = "synthetic-t12c-rt-org", "synthetic-t12c-rt-class", "synthetic-t12c-rt-1"
    revision_id = str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO be1_organizations (organization_id, display_name, state) "
                "VALUES (:o, 'Synthetic RT', 'active')"
            ),
            {"o": org},
        )
        connection.execute(
            text(
                "INSERT INTO be1_classrooms (class_id, organization_id, display_name, state, "
                "created_by) VALUES (:c, :o, 'Synthetic RT class', 'active', 'x')"
            ),
            {"c": cls, "o": org},
        )
        connection.execute(
            text(
                "INSERT INTO be1_managed_profiles (child_id, organization_id, class_id, "
                "display_name, age_months, age_revision, age_source, data_origin, state, "
                "created_by, current_profile_revision_id, profile_revision_no) VALUES "
                "(:i, :o, :c, 'Synthetic Rt', 60, 1, 'SYNTHETIC_FIXTURE', 'SYNTHETIC_DEV', "
                "'active', 'x', :r, 1)"
            ),
            {"i": child, "o": org, "c": cls, "r": revision_id},
        )
        connection.execute(
            text(
                "INSERT INTO be1_profile_revisions (profile_revision_id, child_id, revision_no, "
                "display_name, age_months, age_band_version, age_band_code, authored_by, "
                "revision_hash_version, revision_hash) VALUES (:r, :i, 1, 'Synthetic Rt', 60, 1, "
                "'AGE_36_71', 'x', 1, repeat('c', 64))"
            ),
            {"r": revision_id, "i": child},
        )
        connection.execute(text(_insert_sql("be1")), _raw_row("be1", child))
    with pytest.raises(Exception, match="downgrade refused"):
        command.downgrade(config, parent)
    assert _exists(engine, "public.be1_profile_support_needs") and head in _versions(engine)


def _function_exists(engine: Engine) -> bool:
    with engine.connect() as connection:
        return bool(
            connection.scalar(
                text("SELECT to_regprocedure('public.be1_purge_profile(varchar,varchar)')")
            )
        )


def test_the_purge_revision_round_trips_and_the_original_guards_come_back(
    roundtrip: tuple[Config, Engine],
) -> None:
    """V4-B T-12b-fix (``20261123_ppg_0001``): the downgrade restores both original functions."""
    config, engine = roundtrip
    head, parent = "20261123_ppg_0001", "20261121_psn_0002"
    command.upgrade(config, "heads")
    assert head in _versions(engine) and parent not in _versions(engine)
    assert _function_exists(engine)
    command.downgrade(config, parent)  # explicit target; no row is touched
    assert parent in _versions(engine) and head not in _versions(engine)
    assert not _function_exists(engine)
    with engine.connect() as connection:
        bodies = list(
            connection.scalars(
                text(
                    "SELECT pg_get_functiondef(p.oid) FROM pg_proc p WHERE p.proname IN "
                    "('reject_be1_profile_revision_change', "
                    "'refuse_be1_profile_support_needs_delete')"
                )
            )
        )
    assert len(bodies) == 2 and not any("profile_purge" in body for body in bodies)
    command.upgrade(config, "heads")
    assert head in _versions(engine)
    assert _function_exists(engine)
