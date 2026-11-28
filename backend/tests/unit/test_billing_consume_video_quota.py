from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.billing_models import (
    BillingOfferModel,
    BillingQuotaAllocationEventModel,
    BillingQuotaAllocationModel,
    BillingQuotaProductModel,
    BillingReceiptModel,
    VideoQuotaGrantModel,
    VideoQuotaUsageModel,
)


class SqliteQuotaCommerceService(QuotaCommerceService):
    """Unit-test service using SQLite while leaving PostgreSQL locking to integration tests."""

    def lock(self, key: str) -> None:
        del key


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"billing": None}},
    )
    for model in (
        AdultIdentityModel,
        BillingOfferModel,
        BillingQuotaProductModel,
        BillingQuotaAllocationModel,
        BillingQuotaAllocationEventModel,
        BillingReceiptModel,
        VideoQuotaGrantModel,
        VideoQuotaUsageModel,
    ):
        model.__table__.create(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


def commerce(
    db: Session,
    *,
    clock=lambda: datetime(2026, 11, 20, tzinfo=UTC),
    parent_units: int = 0,
    organization_units: int = 0,
):
    settings = SimpleNamespace(
        video_quota_included_units_parent=parent_units,
        video_quota_included_units_organization=organization_units,
    )
    return SqliteQuotaCommerceService(db, "story-video-admission", settings, clock)


def add_grant(
    db: Session,
    *,
    owner_kind: str = "PARENT_ACCOUNT",
    owner_ref: str = "parent-1",
    kind: str = "TOP_UP",
    units: int = 1,
    period: str | None = None,
    expires_at: datetime | None = None,
) -> VideoQuotaGrantModel:
    grant = VideoQuotaGrantModel(
        grant_id=str(uuid4()),
        owner_kind=owner_kind,
        owner_ref=owner_ref,
        kind=kind,
        units=units,
        period=period,
        expires_at=expires_at,
    )
    db.add(grant)
    db.commit()
    return grant


def consume(
    service: QuotaCommerceService,
    *,
    owner_scope: tuple[str, str] = ("PARENT_ACCOUNT", "parent-1"),
    request_ref: str = "generation-1",
    idempotency_key: str = "key-1",
    fingerprint: str = "fingerprint-1",
):
    return service.consume_video_quota(
        owner_scope,
        request_ref,
        idempotency_key,
        fingerprint,
        "video-quota-port-v1",
    )


def add_teacher_identity(
    db: Session,
    *,
    account_id: str = "teacher-account-1",
    subject: str = "teacher-subject-1",
) -> AdultIdentityModel:
    teacher = AdultIdentityModel(
        subject=subject,
        account_id=account_id,
        issuer="test-issuer",
        account_role="teacher",
        state="active",
    )
    db.add(teacher)
    db.commit()
    return teacher


def add_teacher_allocation(
    db: Session,
    *,
    organization_ref: str = "org-1",
    teacher_ref: str = "teacher-subject-1",
    units: int = 1,
    reclaimed_units: int = 0,
) -> BillingQuotaAllocationModel:
    allocation = BillingQuotaAllocationModel(
        allocation_id=str(uuid4()),
        organization_ref=organization_ref,
        teacher_ref=teacher_ref,
        active=True,
        revision=1,
    )
    db.add(allocation)
    db.add(
        BillingQuotaAllocationEventModel(
            event_id=str(uuid4()),
            allocation_id=allocation.allocation_id,
            organization_ref=organization_ref,
            teacher_ref=teacher_ref,
            event_kind="ALLOCATED",
            units=units,
            actor_ref="manager-subject",
            operation_key="allocate-1",
        )
    )
    if reclaimed_units:
        db.add(
            BillingQuotaAllocationEventModel(
                event_id=str(uuid4()),
                allocation_id=allocation.allocation_id,
                organization_ref=organization_ref,
                teacher_ref=teacher_ref,
                event_kind="RECLAIMED",
                units=reclaimed_units,
                actor_ref="manager-subject",
                operation_key="reclaim-1",
            )
        )
    db.commit()
    return allocation


def consume_teacher(
    service: QuotaCommerceService,
    *,
    organization_ref: str = "org-1",
    teacher_account_id: str = "teacher-account-1",
    request_ref: str = "teacher-generation-1",
    idempotency_key: str = "teacher-key-1",
    fingerprint: str = "teacher-fingerprint-1",
):
    return service.consume_teacher_quota(
        organization_ref,
        teacher_account_id,
        request_ref,
        idempotency_key,
        fingerprint,
        "video-quota-port-v1",
    )


def test_consume_video_quota_writes_one_receipt_and_replays_the_same_usage(db: Session) -> None:
    grant = add_grant(db)
    service = commerce(db)

    first = consume(service)
    retry = consume(service)

    assert first["status"] == "ACCEPTED"
    assert first["usage_ref"]
    assert first["grant_ref"] == grant.grant_id
    assert first["duplicate"] is False
    assert retry["status"] == "ACCEPTED"
    assert retry["usage_ref"] == first["usage_ref"]
    assert retry["grant_ref"] == first["grant_ref"]
    assert retry["duplicate"] is True
    assert db.scalar(select(func.count()).select_from(VideoQuotaUsageModel)) == 1
    assert db.scalar(select(func.count()).select_from(BillingReceiptModel)) == 1


def test_teacher_admission_requires_an_allocation(db: Session) -> None:
    add_teacher_identity(db)

    result = consume_teacher(commerce(db))

    assert result["status"] == "QUOTA_ALLOCATION_NOT_FOUND"
    assert result["usage_ref"] is None
    assert db.scalar(select(func.count()).select_from(VideoQuotaUsageModel)) == 0


def test_teacher_allocation_is_a_hard_cap_before_school_balance(db: Session) -> None:
    add_teacher_identity(db)
    add_teacher_allocation(db, units=1, reclaimed_units=1)

    result = consume_teacher(commerce(db))

    assert result["status"] == "TEACHER_QUOTA_INSUFFICIENT"
    assert result["usage_ref"] is None
    assert db.scalar(select(func.count()).select_from(VideoQuotaUsageModel)) == 0


def test_teacher_admission_reports_exhausted_school_balance(db: Session) -> None:
    add_teacher_identity(db)
    allocation = add_teacher_allocation(db)
    grant = add_grant(
        db,
        owner_kind="ORGANIZATION",
        owner_ref="org-1",
        units=1,
    )
    db.add(
        VideoQuotaUsageModel(
            usage_id=str(uuid4()),
            grant_id=grant.grant_id,
            owner_kind="ORGANIZATION",
            owner_ref="org-1",
            admission_ref="other-teacher-generation",
            allocation_id=None,
            teacher_ref=None,
        )
    )
    db.commit()
    assert allocation.active is True

    result = consume_teacher(commerce(db))

    assert result["status"] == "SCHOOL_QUOTA_INSUFFICIENT"
    assert result["usage_ref"] is None
    assert db.scalar(
        select(func.count()).select_from(VideoQuotaUsageModel).where(
            VideoQuotaUsageModel.admission_ref == "teacher-generation-1"
        )
    ) == 0


def test_teacher_admission_consumes_allocation_and_replays_the_same_receipt(
    db: Session,
) -> None:
    add_teacher_identity(db)
    allocation = add_teacher_allocation(db)
    grant = add_grant(db, owner_kind="ORGANIZATION", owner_ref="org-1", units=2)
    service = commerce(db)

    first = consume_teacher(service)
    allocation.active = False
    db.commit()
    replay = consume_teacher(service)

    assert first["status"] == "ACCEPTED"
    assert first["teacher_ref"] == "teacher-subject-1"
    assert first["grant_ref"] == grant.grant_id
    assert first["allocation_id"] == allocation.allocation_id
    assert first["duplicate"] is False
    assert replay["status"] == "ACCEPTED"
    assert replay["usage_ref"] == first["usage_ref"]
    assert replay["grant_ref"] == first["grant_ref"]
    assert replay["allocation_id"] == first["allocation_id"]
    assert replay["duplicate"] is True
    assert db.scalar(
        select(func.count()).select_from(VideoQuotaUsageModel).where(
            VideoQuotaUsageModel.admission_ref == "teacher-generation-1"
        )
    ) == 1
    assert db.scalar(
        select(func.count()).select_from(BillingQuotaAllocationEventModel).where(
            BillingQuotaAllocationEventModel.allocation_id == allocation.allocation_id,
            BillingQuotaAllocationEventModel.event_kind == "CONSUMED",
        )
    ) == 1
    assert db.scalar(select(func.count()).select_from(BillingReceiptModel)) == 1


def test_same_idempotency_key_with_another_fingerprint_is_a_mismatch(db: Session) -> None:
    add_grant(db)
    service = commerce(db)
    accepted = consume(service)

    mismatch = consume(service, fingerprint="different-fingerprint")

    assert accepted["status"] == "ACCEPTED"
    assert mismatch["status"] == "IDEMPOTENCY_MISMATCH"
    assert mismatch["usage_ref"] is None
    assert db.scalar(select(func.count()).select_from(VideoQuotaUsageModel)) == 1


def test_exhausted_quota_stores_nothing_and_a_retry_after_top_up_is_accepted(db: Session) -> None:
    service = commerce(db)

    first = consume(service)
    retry = consume(service)

    assert first["status"] == "QUOTA_EXCEEDED"
    assert first["usage_ref"] is None
    assert first["included_grant_state"] == "NOT_CONFIGURED"
    assert retry["status"] == "QUOTA_EXCEEDED"
    assert db.scalar(select(func.count()).select_from(VideoQuotaUsageModel)) == 0
    assert db.scalar(select(func.count()).select_from(BillingReceiptModel)) == 0

    top_up = add_grant(db, kind="TOP_UP", units=1)
    after_top_up = consume(service)

    assert after_top_up["status"] == "ACCEPTED"
    assert after_top_up["grant_ref"] == top_up.grant_id
    assert after_top_up["duplicate"] is False


def test_included_grant_uses_the_configured_setting_units_and_precedes_top_up(db: Session) -> None:
    top_up = add_grant(db, kind="TOP_UP", units=9)
    service = commerce(db, parent_units=3)

    result = consume(service)

    included = db.scalar(
        select(VideoQuotaGrantModel).where(VideoQuotaGrantModel.kind == "INCLUDED")
    )
    assert included is not None
    assert included.units == 3
    assert included.period == "2026-11"
    assert included.expires_at is not None
    assert included.expires_at.replace(tzinfo=UTC) == datetime(2026, 11, 30, 17, tzinfo=UTC)
    assert result["included_grant_state"] == "CREATED"
    assert result["grant_ref"] == included.grant_id
    assert result["grant_ref"] != top_up.grant_id


def test_available_video_grants_are_consumed_in_included_monthly_top_up_order(db: Session) -> None:
    monthly = add_grant(
        db,
        kind="MONTHLY",
        units=1,
        period="2026-11",
        expires_at=datetime(2026, 12, 1, tzinfo=UTC),
    )
    top_up = add_grant(db, kind="TOP_UP", units=1)
    service = commerce(db, parent_units=1)

    included_use = consume(service)
    monthly_use = consume(
        service,
        request_ref="generation-2",
        idempotency_key="key-2",
    )
    top_up_use = consume(
        service,
        request_ref="generation-3",
        idempotency_key="key-3",
    )

    included = db.scalar(
        select(VideoQuotaGrantModel).where(VideoQuotaGrantModel.kind == "INCLUDED")
    )
    assert included is not None
    assert included_use["grant_ref"] == included.grant_id
    assert monthly_use["grant_ref"] == monthly.grant_id
    assert top_up_use["grant_ref"] == top_up.grant_id


def test_parent_default_admission_grants_two_full_midmonth_units(db: Session) -> None:
    settings = Settings(_env_file=None, env="test")  # type: ignore[call-arg]
    service = SqliteQuotaCommerceService(
        db,
        "story-video-admission",
        settings,
        lambda: datetime(2026, 11, 15, 0, tzinfo=UTC),
    )

    first = consume(service, request_ref="generation-1", idempotency_key="key-1")
    second = consume(service, request_ref="generation-2", idempotency_key="key-2")
    third = consume(service, request_ref="generation-3", idempotency_key="key-3")

    included = db.scalar(
        select(VideoQuotaGrantModel).where(
            VideoQuotaGrantModel.owner_kind == "PARENT_ACCOUNT",
            VideoQuotaGrantModel.owner_ref == "parent-1",
            VideoQuotaGrantModel.kind == "INCLUDED",
            VideoQuotaGrantModel.period == "2026-11",
        )
    )
    assert included is not None
    assert included.units == 2
    assert first["status"] == "ACCEPTED"
    assert first["included_grant_state"] == "CREATED"
    assert second["status"] == "ACCEPTED"
    assert second["grant_ref"] == included.grant_id
    assert third["status"] == "QUOTA_EXCEEDED"
    assert third["usage_ref"] is None
    assert db.scalar(
        select(func.count()).select_from(VideoQuotaUsageModel).where(
            VideoQuotaUsageModel.owner_kind == "PARENT_ACCOUNT",
            VideoQuotaUsageModel.owner_ref == "parent-1",
        )
    ) == 2
    assert db.scalar(
        select(func.count()).select_from(VideoQuotaUsageModel).where(
            VideoQuotaUsageModel.admission_ref == "generation-3",
        )
    ) == 0


def test_parent_default_admission_grants_fresh_units_at_hcm_month_rollover(
    db: Session,
) -> None:
    settings = Settings(_env_file=None, env="test")  # type: ignore[call-arg]
    now = [datetime(2026, 11, 30, 16, 59, tzinfo=UTC)]
    service = SqliteQuotaCommerceService(
        db, "story-video-admission", settings, lambda: now[0]
    )

    november = consume(service, request_ref="generation-nov", idempotency_key="key-nov")
    now[0] = datetime(2026, 11, 30, 17, 0, tzinfo=UTC)
    december_first = consume(
        service, request_ref="generation-dec-1", idempotency_key="key-dec-1"
    )
    december_second = consume(
        service, request_ref="generation-dec-2", idempotency_key="key-dec-2"
    )
    december_third = consume(
        service, request_ref="generation-dec-3", idempotency_key="key-dec-3"
    )

    grants = list(
        db.scalars(
            select(VideoQuotaGrantModel)
            .where(
                VideoQuotaGrantModel.owner_kind == "PARENT_ACCOUNT",
                VideoQuotaGrantModel.owner_ref == "parent-1",
                VideoQuotaGrantModel.kind == "INCLUDED",
            )
            .order_by(VideoQuotaGrantModel.period)
        )
    )
    assert november["status"] == "ACCEPTED"
    assert december_first["status"] == "ACCEPTED"
    assert december_second["status"] == "ACCEPTED"
    assert december_third["status"] == "QUOTA_EXCEEDED"
    assert [(grant.period, grant.units) for grant in grants] == [
        ("2026-11", 2),
        ("2026-12", 2),
    ]
    assert december_first["grant_ref"] == december_second["grant_ref"]
    assert december_first["grant_ref"] != november["grant_ref"]
    assert db.scalar(
        select(func.count()).select_from(VideoQuotaUsageModel).where(
            VideoQuotaUsageModel.admission_ref == "generation-dec-3",
        )
    ) == 0


def test_monthly_included_grant_is_idempotent_per_owner_and_month(db: Session) -> None:
    service = commerce(db, parent_units=4)

    first = service.ensure_monthly_included_grant(
        ("PARENT_ACCOUNT", "parent-1"), "2026-11"
    )
    second = service.ensure_monthly_included_grant(
        ("PARENT_ACCOUNT", "parent-1"), "2026-11"
    )

    assert first["status"] == "CREATED"
    assert second["status"] == "EXISTS"
    assert second["grant_ref"] == first["grant_ref"]
    assert second["units"] == 4
    assert db.scalar(select(func.count()).select_from(VideoQuotaGrantModel)) == 1


def test_monthly_included_grant_is_per_scope_setting_and_never_from_a_sellable_product(
    db: Session,
) -> None:
    db.add(
        BillingOfferModel(
            offer_id="o",
            product_id="p",
            version=1,
            display_name="Sellable monthly",
            offer_kind="MONTHLY",
            cycle_months=1,
            owner_kind="PARENT_ACCOUNT",
            units=7,
            amount_vnd=1000,
            created_by="platform-admin",
        )
    )
    db.add(
        BillingQuotaProductModel(
            product_id="p",
            owner_kind="PARENT_ACCOUNT",
            display_name="Sellable monthly",
            offer_kind="MONTHLY",
            cycle_months=1,
            current_offer_id="o",
            active=True,
            revision=1,
            created_by="platform-admin",
        )
    )
    db.commit()

    parent = commerce(db, organization_units=5).ensure_monthly_included_grant(
        ("PARENT_ACCOUNT", "parent-1"), "2026-11"
    )
    organization = commerce(db, organization_units=5).ensure_monthly_included_grant(
        ("ORGANIZATION", "org-1"), "2026-11"
    )

    assert parent["status"] == "NOT_CONFIGURED"
    assert organization["status"] == "CREATED"
    assert organization["units"] == 5
    assert db.scalar(select(func.count()).select_from(VideoQuotaGrantModel)) == 1


def test_parent_setting_zero_still_returns_not_configured(db: Session) -> None:
    settings = Settings(
        _env_file=None,
        env="test",
        video_quota_included_units_parent=0,
    )  # type: ignore[call-arg]
    service = SqliteQuotaCommerceService(
        db,
        "story-video-admission",
        settings,
        lambda: datetime(2026, 11, 20, tzinfo=UTC),
    )

    result = service.ensure_monthly_included_grant(
        ("PARENT_ACCOUNT", "parent-1"), "2026-11"
    )

    assert result == {
        "status": "NOT_CONFIGURED",
        "grant_ref": None,
        "period": "2026-11",
    }
    assert db.scalar(select(func.count()).select_from(VideoQuotaGrantModel)) == 0


def test_monthly_included_grant_returns_clear_state_when_unconfigured(db: Session) -> None:
    result = commerce(db).ensure_monthly_included_grant(
        ("PARENT_ACCOUNT", "parent-1"), "2026-11"
    )

    assert result == {
        "status": "NOT_CONFIGURED",
        "grant_ref": None,
        "period": "2026-11",
    }
    assert db.scalar(select(func.count()).select_from(VideoQuotaGrantModel)) == 0


@pytest.mark.parametrize(
    ("error", "status"),
    [
        ("TEACHER_QUOTA_INSUFFICIENT", "TEACHER_QUOTA_INSUFFICIENT"),
        ("QUOTA_ALLOCATION_NOT_FOUND", "QUOTA_ALLOCATION_NOT_FOUND"),
        ("SCHOOL_QUOTA_INSUFFICIENT", "SCHOOL_QUOTA_INSUFFICIENT"),
        ("SUBSCRIPTION_RESTRICTED", "SUBSCRIPTION_RESTRICTED"),
        ("IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_MISMATCH"),
        ("BILLING_DEPENDENCY_UNAVAILABLE", "UNAVAILABLE"),
    ],
)
def test_billing_errors_map_to_one_story_status(error: str, status: str) -> None:
    assert QuotaCommerceService._video_admission_error_status(AdminError(error, 409)) == status


def test_included_units_settings_default_to_parent_demo_quota_only() -> None:
    settings = Settings(_env_file=None, env="test")  # type: ignore[call-arg]

    assert settings.video_quota_included_units_parent == 2
    assert settings.video_quota_included_units_organization == 0
