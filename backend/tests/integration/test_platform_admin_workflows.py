"""PostgreSQL-backed Admin workflows in an explicitly disposable acceptance database."""

import os
from types import SimpleNamespace
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountProfile,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.platform_models import PermissionGrantModel
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_feedback import router as feedback_router
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.routers.platform_admin import router
from sketch2life.interfaces.http.routers.platform_admin_accounts import router as accounts_router


@pytest.fixture
def admin_api(monkeypatch):
    url = os.environ.get("ADMIN_TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("ADMIN_TEST_DATABASE_URL is required")
    if "admin_acceptance" not in url.rsplit("/", 1)[-1]:
        pytest.fail("Admin acceptance tests require a disposable admin_acceptance database")
    engine = create_engine(url)
    author, reviewer = "author-" + uuid4().hex, "reviewer-" + uuid4().hex
    issuer = "acceptance-issuer"
    with Session(engine) as db:
        for subject in (author, reviewer):
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    account_id=str(uuid4()),
                    issuer=issuer,
                    account_role="platform_admin",
                    state="active",
                    role_revision=1,
                )
            )
        db.add(
            PermissionGrantModel(
                subject=reviewer,
                permission="content_admin",
                active=True,
                revision=1,
                granted_by=author,
            )
        )
        db.commit()
    current = SimpleNamespace(subject=author)
    app = FastAPI()
    from sketch2life.interfaces.http.routers import platform_admin as admin_routes

    monkeypatch.setattr(
        admin_routes,
        "get_settings",
        lambda: SimpleNamespace(env="test", billing_sandbox_enabled=True, redis_url=None),
    )
    app.include_router(router)
    app.include_router(accounts_router)
    app.state.identity_account_provisioner = SimpleNamespace(
        get_account_profiles=lambda subjects: {
            subject: IdentityAccountProfile(subject, "synthetic@example.test", "Test account")
            for subject in subjects
        }
    )
    app.include_router(feedback_router)

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database

    def lesson_reader(db: Annotated[Session, Depends(get_db)]):
        return LessonLibraryService(db, storage=None, parser=None, scanner=None)

    app.dependency_overrides[get_lesson_library_service] = lesson_reader

    def test_principal(request: Request):
        return VerifiedPrincipal(
            request.headers.get("X-Acceptance-Actor", current.subject), issuer, frozenset()
        )

    app.dependency_overrides[get_verified_adult] = test_principal
    with TestClient(app) as client:
        yield client, current, author, reviewer, engine
    engine.dispose()


BASE = "/api/platform-admin/v1"
ACTIVITY = {
    "title": "Quan sát lá",
    "objective": "Nhận biết hình dạng",
    "instructions_text": "Quan sát và mô tả lá.",
    "safety_notes": "Không đưa lá vào miệng.",
}
LESSON = {
    "title": "Bài học chiếc lá",
    "topic": "Thiên nhiên",
    "target_age_band_ref": "36-71",
    "target_age_band_version": 1,
    "objectives": ["Nhận biết lá"],
    "drawing_subject": "Chiếc lá",
    "drawing_steps_text": "Vẽ hình lá và gân lá.",
    "subject_learning_notes": "Lá có nhiều hình dạng.",
    "activities": [ACTIVITY],
}


def command(client, path, payload, revision=None, method="POST", key=None):
    headers = {"Idempotency-Key": key or str(uuid4())}
    if revision is not None:
        headers["If-Match"] = f'"{revision}"'
    return client.request(method, BASE + path, json=payload, headers=headers)


def lesson_action(client, item, action, **extra):
    return command(
        client,
        "/lessons/" + item["lesson_id"] + "/actions",
        {
            "action": action,
            "version_id": item["version_id"],
            "content_hash": item["content_hash"],
            **extra,
        },
        item["revision"],
    )


def test_independent_lesson_review_publish_hide_and_immutable_edit(admin_api):
    from sketch2life.infrastructure.lesson_library.service import LessonLibraryError

    client, current, author, reviewer, engine = admin_api
    created = command(client, "/lessons", {"content": LESSON}, key="lesson-once")
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["is_published_version"] is False
    assert command(client, "/lessons", {"content": LESSON}, key="lesson-once").json() == item
    assert lesson_action(client, item, "publish").status_code == 403
    item = lesson_action(client, item, "submit").json()
    assert item["review_state"] == "PENDING_REVIEW"
    current.subject = reviewer
    reviewed = lesson_action(client, item, "approve")
    assert reviewed.status_code == 200, reviewed.text
    item = reviewed.json()
    reloaded = client.get(BASE + "/lessons/" + item["lesson_id"]).json()
    assert reloaded["is_author"] is False
    assert reloaded["reviews"][0]["review_id"] == item["review_id"]
    published = lesson_action(
        client, reloaded, "publish", review_id=reloaded["reviews"][0]["review_id"]
    )
    assert published.status_code == 200, published.text
    item = published.json()
    assert item["visibility"] == "PUBLIC"
    assert item["is_published_version"] is True
    with Session(engine) as db:
        reader = LessonLibraryService(db, storage=None, parser=None, scanner=None)
        assert (
            reader.get_parent_lesson(
                parent_principal_ref="synthetic-parent", lesson_id=item["lesson_id"]
            )["version_id"]
            == item["version_id"]
        )

    # Editing a published lesson keeps the existing version live until the new
    # immutable version has gone through independent review and publication.
    old_public_version = item["version_id"]
    current.subject = author
    revised = command(
        client,
        "/lessons/" + item["lesson_id"],
        {"content": {**LESSON, "title": "Bản cập nhật"}},
        item["revision"],
        method="PATCH",
    )
    assert revised.status_code == 200, revised.text
    item = revised.json()
    assert item["visibility"] == "PUBLIC"
    assert item["is_published_version"] is False
    with Session(engine) as db:
        reader = LessonLibraryService(db, storage=None, parser=None, scanner=None)
        assert (
            reader.get_parent_lesson(
                parent_principal_ref="synthetic-parent", lesson_id=item["lesson_id"]
            )["version_id"]
            == old_public_version
        )
    item = lesson_action(client, item, "submit").json()
    current.subject = reviewer
    item = lesson_action(client, item, "approve").json()
    reviewed = client.get(BASE + "/lessons/" + item["lesson_id"]).json()
    republished = lesson_action(
        client, reviewed, "publish", review_id=reviewed["reviews"][0]["review_id"]
    )
    assert republished.status_code == 200, republished.text
    item = republished.json()
    assert item["is_published_version"] is True
    with Session(engine) as db:
        reader = LessonLibraryService(db, storage=None, parser=None, scanner=None)
        assert (
            reader.get_parent_lesson(
                parent_principal_ref="synthetic-parent", lesson_id=item["lesson_id"]
            )["version_id"]
            == item["version_id"]
        )

    hidden = lesson_action(client, item, "hide", reason="Review correction")
    assert hidden.status_code == 200 and hidden.json()["moderation_state"] == "HIDDEN"
    assert hidden.json()["is_published_version"] is False
    with Session(engine) as db, pytest.raises(LessonLibraryError):
        LessonLibraryService(db, storage=None, parser=None, scanner=None).get_parent_lesson(
            parent_principal_ref="synthetic-parent", lesson_id=item["lesson_id"]
        )
    old = item
    item = hidden.json()
    current.subject = author
    revised = command(
        client,
        "/lessons/" + item["lesson_id"],
        {"content": {**LESSON, "title": "Bản sửa"}},
        item["revision"],
        method="PATCH",
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["version_id"] != old["version_id"]
    assert revised.json()["review_state"] == "DRAFT"
    assert (
        command(
            client,
            "/lessons/" + item["lesson_id"],
            {"content": LESSON},
            old["revision"],
            method="PATCH",
        ).status_code
        == 409
    )


def test_review_revocation_blocks_publication(admin_api):
    client, current, author, reviewer, engine = admin_api
    item = command(client, "/lessons", {"content": LESSON}).json()
    item = lesson_action(client, item, "submit").json()
    current.subject = reviewer
    item = lesson_action(client, item, "approve").json()
    with Session(engine) as db:
        grant = db.get(PermissionGrantModel, (reviewer, "content_admin"))
        grant.revision += 1
        grant.active = False
        db.commit()
    assert lesson_action(client, item, "publish", review_id=item["review_id"]).status_code == 403


def test_catalog_reuses_existing_review_and_publication_rules(admin_api):
    client, current, author, reviewer, _ = admin_api
    item = command(
        client, "/catalog", {"activity": ACTIVITY, "age_band": "36-71", "age_band_version": 1}
    ).json()
    path = "/catalog/" + item["record_id"] + "/actions"

    def act(action, **extra):
        return command(
            client,
            path,
            {
                "action": action,
                "version": item["version"],
                "content_hash": item["content_hash"],
                **extra,
            },
            item["revision"],
        )

    item = act("submit").json()
    current.subject = reviewer
    assert act("publish").status_code == 409
    for dimension in ("safety", "pedagogical"):
        response = act("review", dimension=dimension, decision="approve")
        assert response.status_code == 200, response.text
        item = response.json()
    response = act("publish")
    assert response.status_code == 200, response.text
    item = response.json()
    assert item["state"] == "published"
    current.subject = author
    draft = command(
        client,
        "/catalog/" + item["record_id"],
        {"activity": ACTIVITY, "age_band": "36-71", "age_band_version": 1},
        item["revision"],
        method="PATCH",
    )
    assert draft.status_code == 200, draft.text
    assert draft.json()["version"] == item["version"] + 1
    item["revision"] = draft.json()["revision"]
    current.subject = reviewer
    item = act("hide", reason="Correction needed").json()
    assert item["state"] == "recalled"


def test_sandbox_payment_grant_idempotency_and_quota_priority(admin_api):
    client, _, _, _, _ = admin_api
    scope = {
        "owner_kind": "ORGANIZATION",
        "owner_ref": command(
            client, "/organizations", {"display_name": "Quota test school"}
        ).json()["organization_id"],
    }
    offer = command(
        client,
        "/billing/sandbox/offers",
        {"owner_kind": "ORGANIZATION", "units": 2, "amount_vnd": 1000},
    ).json()
    invoice = command(
        client, "/billing/sandbox/invoices", {**scope, "offer_id": offer["offer_id"]}
    ).json()
    assert client.get(BASE + "/billing/sandbox/quota", params=scope).json()["available_units"] == 0
    settlement = {"event_id": str(uuid4()), "paid": True, "amount_vnd": 999}
    path = "/billing/sandbox/invoices/" + invoice["invoice_id"] + "/settle"
    assert command(client, path, settlement, invoice["revision"]).status_code == 409
    settlement["amount_vnd"] = 1000
    assert command(client, path, settlement, invoice["revision"]).json()["state"] == "PAID"
    assert command(client, path, settlement, invoice["revision"]).json()["state"] == "PAID"
    assert client.get(BASE + "/billing/sandbox/quota", params=scope).json()["available_units"] == 2
    included = command(client, "/billing/sandbox/included-grants", {**scope, "units": 1}).json()
    assert (
        command(client, "/billing/sandbox/included-grants", {**scope, "units": 1}).json()[
            "grant_id"
        ]
        == included["grant_id"]
    )
    first = command(client, "/billing/sandbox/consume", {**scope, "admission_ref": "first"}).json()
    assert first["grant_id"] == included["grant_id"]
    assert (
        command(client, "/billing/sandbox/consume", {**scope, "admission_ref": "first"}).json()
        == first
    )
    assert (
        command(
            client, "/billing/sandbox/consume", {**scope, "admission_ref": "second"}
        ).status_code
        == 200
    )
    assert (
        command(client, "/billing/sandbox/consume", {**scope, "admission_ref": "third"}).status_code
        == 200
    )
    assert (
        command(
            client, "/billing/sandbox/consume", {**scope, "admission_ref": "fourth"}
        ).status_code
        == 409
    )
    assert client.get(BASE + "/billing/sandbox/quota", params=scope).json()["available_units"] == 0
    assert (
        client.get(
            BASE + "/billing/sandbox/quota",
            params={"owner_kind": "PARENT_ACCOUNT", "owner_ref": scope["owner_ref"]},
        ).status_code
        == 404
    )


def test_payment_sandbox_is_closed_in_production_even_if_flag_is_on(admin_api, monkeypatch):
    client, _, _, _, _ = admin_api
    from sketch2life.interfaces.http.routers import platform_admin as admin_routes

    monkeypatch.setattr(
        admin_routes,
        "get_settings",
        lambda: SimpleNamespace(env="production", billing_sandbox_enabled=True),
    )
    assert client.get(BASE + "/billing/sandbox/offers").status_code == 403


def test_feedback_is_lesson_bound_school_scoped_and_text_only(admin_api):
    from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
    from sketch2life.infrastructure.lesson_library.tables import ACCESS_GRANTS, LIBRARY_VERSIONS
    from sketch2life.infrastructure.persistence.be1_models import OrganizationAssignmentModel

    client, current, author, _, engine = admin_api
    org = command(client, "/organizations", {"display_name": "Feedback School"}).json()[
        "organization_id"
    ]
    other_org = command(client, "/organizations", {"display_name": "Other School"}).json()[
        "organization_id"
    ]
    parent, other_parent, teacher = [str(uuid4()) for _ in range(3)]
    with Session(engine) as db:
        for subject, role in [(parent, "parent"), (other_parent, "parent"), (teacher, "teacher")]:
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    account_id=str(uuid4()),
                    issuer="acceptance-issuer",
                    account_role=role,
                    state="active",
                    role_revision=1,
                )
            )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=other_org,
                subject=teacher,
                role="teacher",
                active=True,
            )
        )
        db.commit()
        lesson = LessonLibraryService(db, storage=None, parser=None, scanner=None).create_lesson(
            organization_id=org,
            actor=author,
            content=LessonContentInputV1(**LESSON),
            visibility="SCHOOL",
            idempotency_key=str(uuid4()),
        )
        version_id = lesson["current_version"]["version_id"]
        db.execute(
            LIBRARY_VERSIONS.update()
            .where(LIBRARY_VERSIONS.c.version_id == version_id)
            .values(review_state="APPROVED")
        )
        db.execute(
            ACCESS_GRANTS.insert().values(
                access_grant_id=str(uuid4()),
                lesson_id=lesson["lesson_id"],
                version_id=version_id,
                organization_id=org,
                audience_kind="PUBLIC",
                capability="VIEW",
                state="ACTIVE",
                granted_by=author,
                revision=1,
            )
        )
        db.commit()
    current.subject = parent
    path = (
        "/api/lesson-library/v1/organizations/"
        + org
        + "/lessons/"
        + lesson["lesson_id"]
        + "/feedback"
    )
    response = client.post(
        path, json={"body": "Hoạt động phù hợp."}, headers={"Idempotency-Key": str(uuid4())}
    )
    assert response.status_code == 201, response.text
    thread = response.json()
    assert (
        client.post(
            path,
            json={"body": "Feedback", "media_url": "forbidden"},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 422
    )
    parent_path = "/api/lesson-library/v1/organizations/" + org + "/feedback/" + thread["thread_id"]
    assert client.get(parent_path).status_code == 200
    current.subject = other_parent
    assert client.get(parent_path).status_code == 404
    current.subject = teacher
    assert client.get(parent_path).status_code == 404
    current.subject = author
    assert (
        client.get(
            BASE + "/organizations/" + other_org + "/feedback/" + thread["thread_id"]
        ).status_code
        == 404
    )
    response = command(
        client,
        "/organizations/" + org + "/feedback/" + thread["thread_id"] + "/replies",
        {"body": "Cảm ơn phản hồi."},
        thread["revision"],
    )
    assert response.status_code == 200, response.text
    assert (
        command(
            client,
            "/organizations/" + org + "/feedback/" + thread["thread_id"] + "/replies",
            {"body": "Old update"},
            thread["revision"],
        ).status_code
        == 409
    )


def test_operations_and_lifecycle_expose_only_metadata(admin_api):
    from sketch2life.infrastructure.persistence.be1_models import DataLifecycleRequestModel

    client, _, author, _, engine = admin_api
    with Session(engine) as db:
        db.add(
            DataLifecycleRequestModel(
                request_id=str(uuid4()),
                organization_id="synthetic-school",
                request_type="profile_delete",
                target_ref="sensitive-child-marker",
                state="requested",
                unresolved_items=1,
                requested_by=author,
            )
        )
        db.commit()
    for path in ("/operations", "/lifecycle", "/email-deliveries"):
        response = client.get(BASE + path)
        assert response.status_code == 200, response.text
        assert "sensitive-child-marker" not in response.text
        assert "target_ref" not in response.text
    assert client.get(BASE + "/session").json()["role"] == "platform_admin"


def test_concurrent_cross_demotion_preserves_an_active_admin(admin_api):
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy import func, select

    client, _, author, reviewer, engine = admin_api
    with Session(engine) as db:
        # Earlier tests of this module leave other active admins in the disposable database;
        # the last-admin rule only bites when these two are the only ones.
        for other in db.scalars(
            select(AdultIdentityModel).where(
                AdultIdentityModel.account_role == "platform_admin",
                AdultIdentityModel.state == "active",
                AdultIdentityModel.subject.not_in((author, reviewer)),
            )
        ):
            other.state = "disabled"
        db.commit()
    with Session(engine) as db:
        refs = {
            r.subject: (r.account_id, r.role_revision)
            for r in db.scalars(
                select(AdultIdentityModel).where(AdultIdentityModel.subject.in_((author, reviewer)))
            )
        }

    def demote(pair):
        actor, target = pair
        account_id, revision = refs[target]
        return client.patch(
            BASE + "/accounts/" + account_id,
            json={"role": "teacher"},
            headers={
                "X-Acceptance-Actor": actor,
                "Idempotency-Key": str(uuid4()),
                "If-Match": f'"{revision}"',
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(demote, [(author, reviewer), (reviewer, author)]))
    # The loser is refused either at authorization (403) or by the last-admin rule (409),
    # depending on which request locks the admin rows second (FEAT-066 C5 locking order).
    assert sorted(statuses) in ([200, 403], [200, 409])
    with Session(engine) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(AdultIdentityModel)
                .where(
                    AdultIdentityModel.subject.in_((author, reviewer)),
                    AdultIdentityModel.account_role == "platform_admin",
                    AdultIdentityModel.state == "active",
                )
            )
            == 1
        )


def test_concurrent_quota_consumption_cannot_overspend(admin_api):
    from concurrent.futures import ThreadPoolExecutor

    client, _, _, _, _ = admin_api
    ref = command(client, "/organizations", {"display_name": "Concurrent quota"}).json()[
        "organization_id"
    ]
    scope = {"owner_kind": "ORGANIZATION", "owner_ref": ref}
    assert (
        command(client, "/billing/sandbox/included-grants", {**scope, "units": 1}).status_code
        == 201
    )

    def consume(index):
        return command(
            client, "/billing/sandbox/consume", {**scope, "admission_ref": "request-" + str(index)}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(consume, [1, 2])) == [200, 409]
    assert client.get(BASE + "/billing/sandbox/quota", params=scope).json()["available_units"] == 0


def test_capacity_quotes_payments_proration_downgrade_and_grace(admin_api):
    from datetime import timedelta

    from sketch2life.infrastructure.persistence.be1_models import ClassroomModel
    from sketch2life.infrastructure.platform_admin.sandbox_billing import SandboxBillingService
    from sketch2life.infrastructure.platform_admin.sandbox_capacity import SandboxCapacityService

    client, _, author, _, engine = admin_api
    org = command(client, "/organizations", {"display_name": "Capacity School"}).json()[
        "organization_id"
    ]
    price = command(
        client,
        "/billing/sandbox/capacity-prices",
        {"cycle_months": 1, "base_amount_vnd": 1000, "slot_amount_vnd": 100},
    ).json()
    quote = command(
        client,
        "/billing/sandbox/subscriptions/quote",
        {"mode": "START", "organization_ref": org, "price_id": price["price_id"], "addon_slots": 2},
    )
    assert quote.status_code == 201, quote.text
    quote = quote.json()
    assert quote["amount_vnd"] == 1200

    def settle(invoice):
        response = command(
            client,
            "/billing/sandbox/invoices/" + invoice["invoice_id"] + "/settle",
            {"event_id": str(uuid4()), "paid": True, "amount_vnd": invoice["amount_vnd"]},
            1,
        )
        assert response.status_code == 200, response.text

    settle(quote)
    ref = quote["subscription_id"]
    subscription = next(
        r
        for r in client.get(BASE + "/billing/sandbox/subscriptions").json()["items"]
        if r["subscription_id"] == ref
    )
    assert subscription["capacity"] == 12
    upgraded = command(
        client,
        "/billing/sandbox/subscriptions/" + ref + "/quote",
        {"mode": "ADDON", "addon_slots": 3},
        subscription["revision"],
    )
    assert upgraded.status_code == 201, upgraded.text
    assert 1 <= upgraded.json()["amount_vnd"] <= 100
    settle(upgraded.json())
    with Session(engine) as db:
        for index in range(13):
            db.add(
                ClassroomModel(
                    class_id=ref + ":" + str(index),
                    organization_id=org,
                    display_name="Test Class",
                    state="active",
                    created_by=author,
                )
            )
        db.commit()
    subscription = next(
        r
        for r in client.get(BASE + "/billing/sandbox/subscriptions").json()["items"]
        if r["subscription_id"] == ref
    )
    assert subscription["capacity"] == 13
    assert (
        command(
            client,
            "/billing/sandbox/subscriptions/" + ref,
            {"action": "downgrade", "addon_slots": 0, "suspend_class_refs": ["outside-school"]},
            subscription["revision"],
            method="PATCH",
        ).status_code
        == 422
    )
    selected = [ref + ":" + str(i) for i in range(3)]
    response = command(
        client,
        "/billing/sandbox/subscriptions/" + ref,
        {"action": "downgrade", "addon_slots": 0, "suspend_class_refs": selected},
        subscription["revision"],
        method="PATCH",
    )
    assert response.status_code == 200, response.text
    assert response.json()["capacity"] == 13 and response.json()["scheduled_addon_slots"] == 0
    with Session(engine) as db:
        settings = SimpleNamespace(env="test", billing_sandbox_enabled=True)
        billing = SandboxBillingService(db, author, settings)
        capacity = SandboxCapacityService(billing)
        row = capacity.load(ref)
        end = row.period_end
        billing.clock = lambda: end + timedelta(days=6)
        view = capacity.view(row)
        assert view["capacity"] == 10 and view["state"] == "GRACE"
        assert set(view["suspended_class_refs"]) == set(selected)
        billing.clock = lambda: end + timedelta(days=7)
        assert capacity.view(row)["state"] == "RESTRICTED"
        renewed = capacity.quote(
            {"mode": "RENEW", "addon_slots": 0}, str(uuid4()), ref, row.revision
        )
        billing.settle(
            renewed["invoice_id"],
            {"event_id": str(uuid4()), "paid": True, "amount_vnd": renewed["amount_vnd"]},
            1,
            str(uuid4()),
        )
        assert capacity.view(capacity.load(ref))["state"] == "ACTIVE"
        assert capacity.view(capacity.load(ref))["capacity"] == 10


def test_ui_capacity_metadata_reads_are_authorized_and_bounded(admin_api):
    from sketch2life.infrastructure.persistence.be1_models import ClassroomModel

    client, current, author, _, engine = admin_api
    org = command(client, "/organizations", {"display_name": "Metadata test school"}).json()[
        "organization_id"
    ]
    with Session(engine) as db:
        db.add(
            ClassroomModel(
                class_id="ui-class-" + uuid4().hex,
                organization_id=org,
                display_name="Test classroom",
                created_by=author,
                state="active",
            )
        )
        db.commit()
    response = client.get(BASE + "/organizations/" + org + "/capacity-classes")
    assert response.status_code == 200
    assert set(response.json()["items"][0]) == {"class_id", "display_name"}
    price = command(
        client,
        "/billing/sandbox/capacity-prices",
        {"cycle_months": 1, "base_amount_vnd": 200000, "slot_amount_vnd": 20000},
    ).json()
    rows = client.get(BASE + "/billing/sandbox/capacity-prices?limit=1").json()["items"]
    assert len(rows) == 1 and rows[0]["price_id"] == price["price_id"]
    assert client.get(BASE + "/billing/sandbox/capacity-prices?limit=101").status_code == 422
    current.subject = "no-valid-admin-assignment"
    assert client.get(BASE + "/organizations/" + org + "/capacity-classes").status_code == 403
    assert client.get(BASE + "/billing/sandbox/capacity-prices").status_code == 403


def test_admin_lists_use_filter_bound_keyset_cursors(admin_api):
    client, *_ = admin_api
    for name, key in (("Cursor School One", "cursor-school-one"), ("Cursor School Two", "cursor-school-two")):
        created = command(client, "/organizations", {"display_name": name}, key=key)
        assert created.status_code == 201, created.text

    first = client.get(BASE + "/organizations", params={"limit": 1}).json()
    assert first["limit"] == 1
    assert first["next_cursor"]
    second = client.get(
        BASE + "/organizations",
        params={"limit": 1, "cursor": first["next_cursor"]},
    ).json()
    assert second["items"][0]["organization_id"] != first["items"][0]["organization_id"]
    seen = {first["items"][0]["organization_id"], second["items"][0]["organization_id"]}
    cursor = second["next_cursor"]
    while cursor:
        page = client.get(
            BASE + "/organizations", params={"limit": 1, "cursor": cursor}
        ).json()
        organization_id = page["items"][0]["organization_id"]
        assert organization_id not in seen
        seen.add(organization_id)
        cursor = page["next_cursor"]
    assert len(seen) == first["total"]
    assert client.get(
        BASE + "/organizations",
        params={"state": "active", "cursor": first["next_cursor"]},
    ).status_code == 422

    audit_first = client.get(BASE + "/audit", params={"limit": 1}).json()
    audit_second = client.get(
        BASE + "/audit",
        params={"limit": 1, "cursor": audit_first["next_cursor"]},
    ).json()
    assert audit_second["items"][0]["audit_id"] != audit_first["items"][0]["audit_id"]


def test_sandbox_configuration_lists_use_filter_bound_keyset_cursors(admin_api):
    from sketch2life.infrastructure.persistence.be1_models import ClassroomModel

    client, _, author, _, engine = admin_api
    org = command(
        client, "/organizations", {"display_name": "Capacity cursor school"}
    ).json()["organization_id"]
    for index in range(3):
        command(
            client,
            "/billing/sandbox/offers",
            {"owner_kind": "ORGANIZATION", "units": index + 1, "amount_vnd": 1000 + index},
            key=f"cursor-offer-{index}",
        )
        command(
            client,
            "/billing/sandbox/capacity-prices",
            {
                "cycle_months": 1,
                "base_amount_vnd": 2000 + index,
                "slot_amount_vnd": 200 + index,
            },
            key=f"cursor-capacity-price-{index}",
        )
    with Session(engine) as db:
        for index in range(3):
            db.add(
                ClassroomModel(
                    class_id=f"cursor-capacity-class-{index}",
                    organization_id=org,
                    display_name=f"Capacity class {index}",
                    created_by=author,
                    state="active",
                )
            )
        db.commit()

    def assert_complete_traversal(path, ref_key):
        first = client.get(BASE + path, params={"limit": 1})
        assert first.status_code == 200, first.text
        data = first.json()
        seen = {data["items"][0][ref_key]}
        cursor = data["next_cursor"]
        while cursor:
            page_response = client.get(BASE + path, params={"limit": 1, "cursor": cursor})
            assert page_response.status_code == 200, page_response.text
            page = page_response.json()
            identifier = page["items"][0][ref_key]
            assert identifier not in seen
            seen.add(identifier)
            cursor = page["next_cursor"]
        assert len(seen) == data["total"]
        return data

    assert_complete_traversal("/billing/sandbox/offers", "offer_id")
    assert_complete_traversal("/billing/sandbox/capacity-prices", "price_id")
    classes = assert_complete_traversal(
        f"/organizations/{org}/capacity-classes", "class_id"
    )
    assert classes["total"] == 3
    other_org = command(
        client, "/organizations", {"display_name": "Other capacity cursor school"}
    ).json()["organization_id"]
    assert client.get(
        BASE + f"/organizations/{other_org}/capacity-classes",
        params={"limit": 1, "cursor": classes["next_cursor"]},
    ).status_code == 422
