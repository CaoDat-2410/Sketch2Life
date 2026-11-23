"""FEAT-066 T-7c-fix: keyed receipt fingerprint and rate-limited real-data gate on PostgreSQL.

SRS l.1697 (keyed commands), l.502 and l.279 (FR-C-10, BR-35: what may outlive a profile), l.278
(BR-34: no child name in audit or logs), l.637 (NFR-12: 429 with Retry-After by account, IP and
operation, never by child id or content). Runs only against a disposable database whose name
contains ``be1_acceptance``. Principals come from the ``X-Test-Principal`` header; every identity,
class and text is synthetic.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.exc import OperationalError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    ConsentRecordModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.be1_receipts import purge_child_receipts
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.rate_limit import SlidingWindowLimiter

ISSUER = "synthetic-t7cf-issuer"
PURPOSE = "classroom-learning-v1"
KEY = "synthetic-t7cf-receipt-key-" + "k" * 32
OTHER_KEY = "synthetic-t7cf-rotated-key-" + "o" * 32
NAME = "Synthetic Fingerprint Learner"


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    token: str
    organization: str
    foreign_organization: str
    subjects: dict[str, str] = field(default_factory=dict)

    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def settings(self) -> Any:
        return self.app.state.be1_runtime.settings

    def limiter(self, **kwargs: Any) -> SlidingWindowLimiter:
        limiter = SlidingWindowLimiter(**kwargs)
        self.app.state.be1_runtime.profile_gate_limiter = limiter
        return limiter


def _identity(db: Any, subject: str, role: str) -> None:
    db.add(AdultIdentityModel(subject=subject, issuer=ISSUER, state="active", account_role=role))
    db.flush()


def _assign(db: Any, organization: str, subject: str, role: str, class_id: str | None) -> None:
    db.add(
        OrganizationAssignmentModel(
            assignment_id=str(uuid4()),
            organization_id=organization,
            subject=subject,
            class_id=class_id,
            role=role,
            active=True,
        )
    )


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_PROFILE_RECEIPT_HMAC_KEY", KEY)
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization, foreign = f"synthetic-t7cf-org-{token}", f"synthetic-t7cf-foreign-{token}"
    d = Api(app, TestClient(app), token, organization, foreign)

    def label(value: str) -> str:
        return f"synthetic-t7cf-{value}-{token}"

    with runtime.session_factory.begin() as db:
        for org in (organization, foreign):
            db.add(OrganizationModel(organization_id=org, display_name=org, state="active"))
        db.flush()
        people: tuple[tuple[str, str, str, str], ...] = (
            ("manager", "school_manager", organization, "school_admin"),
            ("fteacher", "teacher", foreign, "teacher"),
        )
        for key, role, home, assignment_role in people:
            d.subjects[key] = label(key)
            _identity(db, label(key), role)
            _assign(db, home, label(key), assignment_role, None)

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with d.client:
            yield d
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def new_class(d: Api, *, organization: str | None = None) -> str:
    class_id = f"synthetic-t7cf-class-{uuid4().hex[:12]}"
    with d.factory().begin() as db:
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization or d.organization,
                display_name=f"Synthetic {class_id}"[:200],
                state="active",
                created_by="synthetic-t7cf-seed",
            )
        )
    return class_id


def add_teacher(d: Api, key: str, class_id: str) -> None:
    subject = f"synthetic-t7cf-{key}-{d.token}"
    d.subjects[key] = subject
    with d.factory().begin() as db:
        _identity(db, subject, "teacher")
        _assign(db, d.organization, subject, "teacher", class_id)


def url(d: Api, class_id: str) -> str:
    return f"/api/be1/v1/organizations/{d.organization}/classes/{class_id}/profiles"


def post(
    d: Api,
    who: str,
    class_id: str,
    *,
    key: str | None = None,
    if_match: str | None = '"1"',
    body: dict[str, Any] | None = None,
) -> Any:
    headers = {
        "X-Test-Principal": d.subjects[who],
        "Idempotency-Key": uuid4().hex if key is None else key,
    }
    if if_match is not None:
        headers["If-Match"] = if_match
    return d.client.post(
        url(d, class_id),
        json={"display_name": NAME, "age_months": 60} if body is None else body,
        headers=headers,
    )


def move(d: Api, who: str, source: str, child_id: str, target: str) -> Any:
    return d.client.post(
        f"/api/be1/v1/classes/{source}/profiles/{child_id}/move",
        json={"target_class_id": target, "target_class_revision": 1},
        headers={
            "X-Test-Principal": d.subjects[who],
            "Idempotency-Key": uuid4().hex,
            "If-Match": '"1"',
        },
    )


def count(d: Api, model: Any, *where: Any) -> int:
    with d.factory()() as db:
        return int(db.scalar(select(func.count()).select_from(model).where(*where)) or 0)


def receipts(d: Api, key: str | None = None) -> list[Be1CommandReceiptModel]:
    clauses = [Be1CommandReceiptModel.organization_id == d.organization]
    if key is not None:
        clauses.append(Be1CommandReceiptModel.idempotency_key == key)
    with d.factory()() as db:
        rows = list(db.scalars(select(Be1CommandReceiptModel).where(*clauses)).all())
        db.expunge_all()
        return rows


def gate_audits(d: Api) -> int:
    return count(
        d,
        CoreAuditEntryModel,
        CoreAuditEntryModel.organization_id == d.organization,
        CoreAuditEntryModel.action == "profile.enroll",
        CoreAuditEntryModel.decision == "denied_consent_pending",
    )


def pending_consent(d: Api, class_id: str) -> str:
    consent_id = str(uuid4())
    with d.factory().begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=d.organization,
                class_id=class_id,
                child_id=f"synthetic-client-chosen-{uuid4().hex[:8]}",
                purpose_ref=PURPOSE,
                state="pending",
                recorded_by="synthetic-t7cf-seed",
            )
        )
    return consent_id


def gate_body(consent_id: str) -> dict[str, Any]:
    return {"display_name": NAME, "age_months": 60, "consent_id": consent_id}


def v1_fingerprint(principal: str, scope: str, name: str, age: int, revision: int) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "v": 1,
                "principal": principal,
                "scope": scope,
                "display_name": name,
                "age_months": age,
                "consent_id": None,
                "if_match": revision,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


# ----------------------------------------------------------------------------- the fingerprint
def test_create_then_replay_returns_the_same_body_and_the_receipt_is_keyed(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    key = f"t7cf-{uuid4().hex}"
    first = post(d, "t1", class_id, key=key)
    assert first.status_code == 201, first.text
    replay = post(d, "t1", class_id, key=key)
    assert replay.status_code == 201 and replay.content == first.content
    (receipt,) = receipts(d, key)
    fingerprint = receipt.request_fingerprint
    assert re.fullmatch(r"[0-9a-f]{64}", fingerprint)
    scope = f"POST /organizations/{d.organization}/classes/{class_id}/profiles"
    plain = {
        v1_fingerprint(d.subjects["t1"], scope, NAME, 60, 1),
        hashlib.sha256(NAME.encode()).hexdigest(),
        hashlib.sha256(f"{NAME}60".encode()).hexdigest(),
    }
    assert fingerprint not in plain
    assert receipt.response_json["fp_v"] == 2
    assert re.fullmatch(r"[0-9a-f]{8}", str(receipt.response_json["fp_kid"]))


def test_no_receipt_audit_or_outbox_row_holds_the_name_or_the_key(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    assert post(d, "t1", class_id).status_code == 201
    with d.factory()() as db:
        dumps = [
            str(row)
            for row in db.execute(text("SELECT * FROM be1_command_receipts")).all()
            if d.organization in str(row)
        ]
        dumps += [
            str(row)
            for row in db.execute(
                text("SELECT * FROM core_audit_entries WHERE organization_id = :o"),
                {"o": d.organization},
            ).all()
        ]
        dumps += [
            str(row)
            for row in db.execute(
                text("SELECT * FROM core_outbox_events WHERE organization_id = :o"),
                {"o": d.organization},
            ).all()
        ]
    assert dumps
    joined = "\n".join(dumps)
    assert NAME not in joined and KEY not in joined and "Fingerprint Learner" not in joined


def test_the_same_key_with_another_name_age_or_revision_is_400(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    key = f"t7cf-{uuid4().hex}"
    assert post(d, "t1", class_id, key=key).status_code == 201
    for kwargs in (
        {"body": {"display_name": "Synthetic Other", "age_months": 60}},
        {"body": {"display_name": NAME, "age_months": 61}},
        {"if_match": '"2"'},
    ):
        other = post(d, "t1", class_id, key=key, **kwargs)
        assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert count(d, ManagedProfileModel, ManagedProfileModel.class_id == class_id) == 1


def test_a_v1_receipt_and_a_rotated_key_are_non_matching_and_never_make_a_second_profile(
    api: Api,
) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    scope = f"POST /organizations/{d.organization}/classes/{class_id}/profiles"
    legacy_key = f"t7cf-legacy-{uuid4().hex}"
    with d.factory().begin() as db:  # a row of the pre-fix format: plain SHA-256, no fp_v
        db.add(
            Be1CommandReceiptModel(
                principal_ref=d.subjects["t1"],
                operation_scope=scope,
                idempotency_key=legacy_key,
                organization_id=d.organization,
                request_fingerprint=v1_fingerprint(d.subjects["t1"], scope, NAME, 60, 1),
                response_json={
                    "child_id": "synthetic-" + "a" * 24,
                    "enrollment_id": str(uuid4()),
                    "class_revision": 1,
                    "data_origin": "SYNTHETIC_DEV",
                },
            )
        )
    legacy = post(d, "t1", class_id, key=legacy_key)
    assert legacy.status_code == 400 and legacy.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert count(d, ManagedProfileModel, ManagedProfileModel.class_id == class_id) == 0
    # A rotated key: the stored key id and MAC no longer match, so the replay is refused.
    key = f"t7cf-{uuid4().hex}"
    assert post(d, "t1", class_id, key=key).status_code == 201
    d.settings().profile_receipt_hmac_key = SecretStr(OTHER_KEY)
    rotated = post(d, "t1", class_id, key=key)
    assert rotated.status_code == 400 and rotated.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert count(d, ManagedProfileModel, ManagedProfileModel.class_id == class_id) == 1


def test_a_missing_key_is_503_and_writes_nothing_while_a_stranger_still_gets_404(
    api: Api,
) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    key = f"t7cf-{uuid4().hex}"
    first = post(d, "t1", class_id, key=key)
    assert first.status_code == 201
    d.settings().profile_receipt_hmac_key = None
    unavailable = post(d, "t1", class_id)
    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert NAME not in unavailable.text and KEY not in unavailable.text
    assert post(d, "t1", class_id, key=key).status_code == 503  # a stored receipt, no key
    assert post(d, "fteacher", class_id).status_code == 404
    assert post(d, "manager", class_id).status_code == 403
    assert count(d, ManagedProfileModel, ManagedProfileModel.class_id == class_id) == 1


def test_the_purge_helper_removes_the_create_and_move_receipts_of_one_child_only(api: Api) -> None:
    d = api
    source, target = new_class(d), new_class(d)
    add_teacher(d, "t1", source)
    with d.factory().begin() as db:
        _assign(db, d.organization, d.subjects["t1"], "teacher", target)
    first = post(d, "t1", source)
    second = post(d, "t1", source)
    assert first.status_code == second.status_code == 201
    child, other_child = first.json()["child_id"], second.json()["child_id"]
    assert move(d, "t1", source, child, target).status_code == 200
    with d.factory().begin() as db:  # a receipt of another organization that names the same id
        db.add(
            Be1CommandReceiptModel(
                principal_ref="synthetic-t7cf-foreign-principal",
                operation_scope="POST /synthetic/foreign",
                idempotency_key=f"foreign-{uuid4().hex}",
                organization_id=d.foreign_organization,
                request_fingerprint="f" * 64,
                response_json={"child_id": child},
            )
        )
    before = receipts(d)
    assert len(before) == 3  # two creates and one move
    with d.factory().begin() as db:
        removed = purge_child_receipts(db, d.organization, child)
    assert removed == 2
    remaining = receipts(d)
    assert [row.response_json["child_id"] for row in remaining] == [other_child]
    foreign = Be1CommandReceiptModel.organization_id == d.foreign_organization
    assert count(d, Be1CommandReceiptModel, foreign) == 1
    with d.factory().begin() as db:
        assert purge_child_receipts(db, d.organization, child) == 0


def test_a_hashed_move_scope_receipt_is_still_found_through_the_response(api: Api) -> None:
    d = api
    source, target = new_class(d), new_class(d)
    add_teacher(d, "t1", source)
    with d.factory().begin() as db:
        _assign(db, d.organization, d.subjects["t1"], "teacher", target)
    child = post(d, "t1", source).json()["child_id"]
    assert move(d, "t1", source, child, target).status_code == 200
    with d.factory().begin() as db:  # force the "hashed scope" shape: the scope names no child
        db.execute(
            text(
                "UPDATE be1_command_receipts SET operation_scope = 'POST /classes/profiles/move#'"
                " || repeat('a', 64) WHERE organization_id = :o AND operation_scope LIKE '%/move'"
            ),
            {"o": d.organization},
        )
    with d.factory().begin() as db:
        assert purge_child_receipts(db, d.organization, child) == 2


# ----------------------------------------------------------------------------- the gate limit
def test_the_gate_answers_429_after_the_account_limit_and_writes_nothing_more(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    add_teacher(d, "t2", class_id)
    d.limiter(account_limit=3, ip_limit=100, window_seconds=60)
    d.settings().real_profile_data_enabled = True
    consent_id = pending_consent(d, class_id)
    for attempt in range(3):
        refused = post(d, "t1", class_id, body=gate_body(consent_id))
        assert refused.status_code == 409, (attempt, refused.text)
        assert refused.json()["code"] == "CONSENT_NOT_EFFECTIVE"
    assert gate_audits(d) == 3
    limited = post(d, "t1", class_id, body=gate_body(consent_id))
    assert limited.status_code == 429, limited.text
    body = limited.json()
    assert body["code"] == "RATE_LIMITED" and body["retryable"] is True
    retry_after = int(limited.headers["Retry-After"])
    assert 1 <= retry_after <= 60 and body["retry_after_seconds"] == retry_after
    assert NAME not in limited.text and consent_id not in limited.text
    for _ in range(3):
        assert post(d, "t1", class_id, body=gate_body(consent_id)).status_code == 429
    assert gate_audits(d) == 3  # the 429 writes no audit row
    assert receipts(d) == []
    assert count(d, ManagedProfileModel, ManagedProfileModel.organization_id == d.organization) == 0
    # The class lock was released by the rollback: another session can take it at once.
    with d.factory()() as db:
        db.execute(text("SET LOCAL lock_timeout = '1s'"))
        try:
            db.execute(
                text("SELECT class_id FROM be1_classrooms WHERE class_id = :c FOR UPDATE NOWAIT"),
                {"c": class_id},
            )
        except OperationalError as exc:  # pragma: no cover - the failure being tested
            pytest.fail(f"class row still locked after the 429: {exc}")
        db.rollback()
    # Another Teacher account has its own bucket.
    other = post(d, "t2", class_id, body=gate_body(consent_id))
    assert other.status_code == 409 and other.json()["code"] == "CONSENT_NOT_EFFECTIVE"


def test_unknown_consent_ids_are_charged_too_so_probing_is_limited(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    d.limiter(account_limit=2, ip_limit=100, window_seconds=60)
    d.settings().real_profile_data_enabled = True
    for _ in range(2):
        missing = post(d, "t1", class_id, body=gate_body(str(uuid4())))
        assert missing.status_code == 404 and missing.json()["code"] == "RESOURCE_NOT_FOUND"
    assert post(d, "t1", class_id, body=gate_body(str(uuid4()))).status_code == 429
    assert gate_audits(d) == 0


def test_the_address_bucket_limits_all_accounts_together(api: Api) -> None:
    d = api
    class_id = new_class(d)
    for index in range(3):
        add_teacher(d, f"t{index}", class_id)
    d.limiter(account_limit=100, ip_limit=2, window_seconds=60)
    d.settings().real_profile_data_enabled = True
    consent_id = pending_consent(d, class_id)
    statuses = [
        post(d, f"t{index}", class_id, body=gate_body(consent_id)).status_code for index in range(3)
    ]
    assert statuses == [409, 409, 429]


def test_a_stranger_a_manager_and_a_wrong_class_teacher_never_see_429_or_use_the_budget(
    api: Api,
) -> None:
    d = api
    class_id = new_class(d)
    other_class = new_class(d)
    add_teacher(d, "t1", class_id)
    add_teacher(d, "other", other_class)
    d.limiter(account_limit=1, ip_limit=1, window_seconds=60)
    d.settings().real_profile_data_enabled = True
    consent_id = pending_consent(d, class_id)
    for _ in range(4):
        assert post(d, "fteacher", class_id, body=gate_body(consent_id)).status_code == 404
        assert post(d, "other", class_id, body=gate_body(consent_id)).status_code == 404
        assert post(d, "manager", class_id, body=gate_body(consent_id)).status_code == 403
    # None of those used the budget: the Teacher's first attempt still reaches the gate.
    assert post(d, "t1", class_id, body=gate_body(consent_id)).status_code == 409
    assert post(d, "t1", class_id, body=gate_body(consent_id)).status_code == 429


def test_stale_read_only_and_mode_refusals_are_not_charged(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    d.limiter(account_limit=1, ip_limit=1, window_seconds=60)
    d.settings().real_profile_data_enabled = True
    consent_id = pending_consent(d, class_id)
    for _ in range(4):
        stale = post(d, "t1", class_id, body=gate_body(consent_id), if_match='"9"')
        assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    with d.factory().begin() as db:
        row = db.get(ClassroomModel, class_id)
        assert row is not None
        row.state = "suspended"
    for _ in range(4):
        read_only = post(d, "t1", class_id, body=gate_body(consent_id))
        assert read_only.json()["code"] == "INVALID_STATE_TRANSITION"
    with d.factory().begin() as db:
        row = db.get(ClassroomModel, class_id)
        assert row is not None
        row.state = "active"
    d.settings().real_profile_data_enabled = False
    for _ in range(4):  # consent_id while real data is off: 400 UNKNOWN_FIELD, not charged
        assert post(d, "t1", class_id, body=gate_body(consent_id)).status_code == 400
    d.settings().real_profile_data_enabled = True
    assert post(d, "t1", class_id, body=gate_body(consent_id)).status_code == 409
    assert post(d, "t1", class_id, body=gate_body(consent_id)).status_code == 429
    assert gate_audits(d) == 1


def test_the_synthetic_create_is_not_limited(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    d.limiter(account_limit=1, ip_limit=1, window_seconds=60)
    statuses = [post(d, "t1", class_id).status_code for _ in range(12)]
    assert statuses == [201] * 12


def test_concurrent_gate_attempts_admit_exactly_the_limit(api: Api) -> None:
    d = api
    class_id = new_class(d)
    for index in range(8):
        add_teacher(d, f"c{index}", class_id)
    add_teacher(d, "solo", class_id)
    d.limiter(account_limit=3, ip_limit=1000, window_seconds=60)
    d.settings().real_profile_data_enabled = True
    consent_id = pending_consent(d, class_id)
    barrier = Barrier(8)

    def attempt(_: int) -> int:
        barrier.wait(timeout=30)
        return int(post(d, "solo", class_id, body=gate_body(consent_id)).status_code)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(attempt, index) for index in range(8)]
        statuses = sorted(future.result(timeout=90) for future in futures)
    assert statuses == [409, 409, 409, 429, 429, 429, 429, 429]
    assert gate_audits(d) == 3
