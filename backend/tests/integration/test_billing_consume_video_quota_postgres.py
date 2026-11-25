"""PostgreSQL locking and receipt tests for the Billing-owned Story video quota admission."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.domain.billing_capacity import quota_month
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.persistence.billing_models import (
    VideoQuotaGrantModel,
    VideoQuotaUsageModel,
)

_SETTINGS = SimpleNamespace(
    video_quota_included_units_parent=2,
    video_quota_included_units_organization=2,
)
_FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}
_FORBIDDEN_DATABASES = {"sketch2life", "sketch2life_m2_s1a"}


@pytest.fixture(scope="module")
def billing_engine():
    url = os.environ.get("T_QC1_TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("T_QC1_TEST_DATABASE_URL is required for the disposable PostgreSQL test DB")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        pytest.fail("T_QC1_TEST_DATABASE_URL must point to PostgreSQL")
    if parsed.database in _FORBIDDEN_DATABASES:
        pytest.fail("T-QC1 integration tests refuse the protected Sketch2Life databases")
    if parsed.port in _FORBIDDEN_PORTS or parsed.port is None:
        pytest.fail("T-QC1 integration tests refuse protected or implicit database ports")
    if not (
        parsed.database.startswith("frc08_")
        and parsed.database.endswith("t_qc1_acceptance")
    ):
        pytest.fail("T-QC1 integration tests require a disposable frc08_*t_qc1_acceptance database")

    from sqlalchemy import create_engine

    engine = create_engine(url, pool_size=4, max_overflow=0, pool_timeout=15)
    yield engine
    engine.dispose()


def _session_factory(billing_engine):
    return sessionmaker(bind=billing_engine, autoflush=False, expire_on_commit=False)


def _prepare_last_unit(
    billing_engine, owner_kind: str
) -> tuple[str, str, sessionmaker[Session]]:
    sessions = _session_factory(billing_engine)
    owner_ref = "tqc1-" + uuid4().hex
    month, _ = quota_month(datetime.now(UTC))
    with sessions() as db:
        service = QuotaCommerceService(db, "story-video-admission", _SETTINGS)
        service.ensure_monthly_included_grant((owner_kind, owner_ref), month)
        included_grants = list(
            db.scalars(
                select(VideoQuotaGrantModel).where(
                    VideoQuotaGrantModel.owner_kind == owner_kind,
                    VideoQuotaGrantModel.owner_ref == owner_ref,
                    VideoQuotaGrantModel.kind == "INCLUDED",
                    VideoQuotaGrantModel.period == month,
                )
            )
        )
        for grant in included_grants:
            used = service._usage_count(db, grant.grant_id)
            for index in range(max(0, grant.units - used)):
                db.add(
                    VideoQuotaUsageModel(
                        usage_id=str(uuid4()),
                        grant_id=grant.grant_id,
                        owner_kind=owner_kind,
                        owner_ref=owner_ref,
                        admission_ref=f"seed-{index}-{uuid4().hex}",
                    )
                )
        top_up = VideoQuotaGrantModel(
            grant_id=str(uuid4()),
            owner_kind=owner_kind,
            owner_ref=owner_ref,
            kind="TOP_UP",
            units=1,
            period=None,
            expires_at=None,
        )
        db.add(top_up)
        db.commit()
    return owner_ref, top_up.grant_id, sessions


def _consume(
    sessions: sessionmaker[Session],
    owner_kind: str,
    owner_ref: str,
    request_ref: str,
    idempotency_key: str,
    fingerprint: str = "fingerprint-1",
) -> dict:
    with sessions() as db:
        return QuotaCommerceService(
            db, "story-video-admission", _SETTINGS
        ).consume_video_quota(
            (owner_kind, owner_ref),
            request_ref,
            idempotency_key,
            fingerprint,
            "video-quota-port-v1",
        )


def test_postgres_retry_mismatch_and_exhausted_quota(billing_engine) -> None:
    owner_ref, top_up_ref, sessions = _prepare_last_unit(billing_engine, "PARENT_ACCOUNT")
    accepted_ref = "request-" + uuid4().hex
    accepted = _consume(sessions, "PARENT_ACCOUNT", owner_ref, accepted_ref, "key-1")
    replay = _consume(sessions, "PARENT_ACCOUNT", owner_ref, accepted_ref, "key-1")
    mismatch = _consume(
        sessions,
        "PARENT_ACCOUNT",
        owner_ref,
        accepted_ref,
        "key-1",
        fingerprint="different-fingerprint",
    )
    denied_ref = "request-" + uuid4().hex
    exhausted = _consume(sessions, "PARENT_ACCOUNT", owner_ref, denied_ref, "key-2")

    assert accepted["status"] == "ACCEPTED"
    assert accepted["grant_ref"] == top_up_ref
    assert replay["status"] == "ACCEPTED"
    assert replay["usage_ref"] == accepted["usage_ref"]
    assert replay["duplicate"] is True
    assert mismatch["status"] == "IDEMPOTENCY_MISMATCH"
    assert exhausted["status"] == "QUOTA_EXCEEDED"
    with sessions() as db:
        assert db.scalar(
            select(func.count()).select_from(VideoQuotaUsageModel).where(
                VideoQuotaUsageModel.owner_kind == "PARENT_ACCOUNT",
                VideoQuotaUsageModel.owner_ref == owner_ref,
                VideoQuotaUsageModel.admission_ref == denied_ref,
            )
        ) == 0


def test_postgres_competing_requests_for_last_parent_and_organization_units(billing_engine) -> None:
    for owner_kind in ("PARENT_ACCOUNT", "ORGANIZATION"):
        owner_ref, top_up_ref, sessions = _prepare_last_unit(billing_engine, owner_kind)
        barrier = Barrier(2)
        requests = (
            ("request-" + uuid4().hex, "key-" + uuid4().hex),
            ("request-" + uuid4().hex, "key-" + uuid4().hex),
        )

        def attempt(
            request: tuple[str, str],
            *,
            barrier: Barrier = barrier,
            sessions: sessionmaker[Session] = sessions,
            owner_kind: str = owner_kind,
            owner_ref: str = owner_ref,
        ) -> dict:
            barrier.wait(timeout=10)
            return _consume(sessions, owner_kind, owner_ref, request[0], request[1])

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, requests))

        assert sorted(result["status"] for result in results) == [
            "ACCEPTED",
            "QUOTA_EXCEEDED",
        ]
        assert sum(result["grant_ref"] == top_up_ref for result in results) == 1
        with sessions() as db:
            assert db.scalar(
                select(func.count()).select_from(VideoQuotaUsageModel).where(
                    VideoQuotaUsageModel.owner_kind == owner_kind,
                    VideoQuotaUsageModel.owner_ref == owner_ref,
                    VideoQuotaUsageModel.grant_id == top_up_ref,
                )
            ) == 1


def test_postgres_monthly_included_grant_is_idempotent(billing_engine) -> None:
    owner_kind = "PARENT_ACCOUNT"
    owner_ref = "tqc1-" + uuid4().hex
    month, expiry = quota_month(datetime.now(UTC))
    sessions = _session_factory(billing_engine)

    first = _consume_monthly_grant(sessions, owner_kind, owner_ref, month)
    second = _consume_monthly_grant(sessions, owner_kind, owner_ref, month)
    assert first["status"] == "CREATED"
    assert first["units"] == 2
    assert second["status"] == "EXISTS"
    assert second["grant_ref"] == first["grant_ref"]
    with sessions() as db:
        grant = db.get(VideoQuotaGrantModel, first["grant_ref"])
        assert grant is not None
        assert grant.expires_at == expiry
        assert db.scalar(
            select(func.count()).select_from(VideoQuotaGrantModel).where(
                VideoQuotaGrantModel.owner_kind == owner_kind,
                VideoQuotaGrantModel.owner_ref == owner_ref,
                VideoQuotaGrantModel.kind == "INCLUDED",
                VideoQuotaGrantModel.period == month,
            )
        ) == 1


def test_postgres_parent_admission_uses_two_units_and_resets_at_hcm_month_boundary(
    billing_engine,
) -> None:
    owner_kind = "PARENT_ACCOUNT"
    owner_ref = "tqc1-" + uuid4().hex
    sessions = _session_factory(billing_engine)
    now = [datetime(2026, 11, 15, 0, tzinfo=UTC)]

    def consume_at(request_ref: str) -> dict:
        with sessions() as db:
            return QuotaCommerceService(
                db,
                "story-video-admission",
                _SETTINGS,
                clock=lambda: now[0],
            ).consume_video_quota(
                (owner_kind, owner_ref),
                request_ref,
                "key-" + request_ref,
                "fingerprint-1",
                "video-quota-port-v1",
            )

    november_first = consume_at("request-nov-1-" + uuid4().hex)
    november_second = consume_at("request-nov-2-" + uuid4().hex)
    november_third_ref = "request-nov-3-" + uuid4().hex
    november_third = consume_at(november_third_ref)
    now[0] = datetime(2026, 11, 30, 17, 0, tzinfo=UTC)
    december_first = consume_at("request-dec-1-" + uuid4().hex)
    december_second = consume_at("request-dec-2-" + uuid4().hex)
    december_third_ref = "request-dec-3-" + uuid4().hex
    december_third = consume_at(december_third_ref)

    assert november_first["status"] == "ACCEPTED"
    assert november_second["status"] == "ACCEPTED"
    assert november_second["grant_ref"] == november_first["grant_ref"]
    assert november_third["status"] == "QUOTA_EXCEEDED"
    assert december_first["status"] == "ACCEPTED"
    assert december_second["status"] == "ACCEPTED"
    assert december_second["grant_ref"] == december_first["grant_ref"]
    assert december_first["grant_ref"] != november_first["grant_ref"]
    assert december_third["status"] == "QUOTA_EXCEEDED"

    with sessions() as db:
        grants = list(
            db.scalars(
                select(VideoQuotaGrantModel)
                .where(
                    VideoQuotaGrantModel.owner_kind == owner_kind,
                    VideoQuotaGrantModel.owner_ref == owner_ref,
                    VideoQuotaGrantModel.kind == "INCLUDED",
                )
                .order_by(VideoQuotaGrantModel.period)
            )
        )
        assert [(grant.period, grant.units) for grant in grants] == [
            ("2026-11", 2),
            ("2026-12", 2),
        ]
        assert db.scalar(
            select(func.count()).select_from(VideoQuotaUsageModel).where(
                VideoQuotaUsageModel.owner_kind == owner_kind,
                VideoQuotaUsageModel.owner_ref == owner_ref,
            )
        ) == 4
        for denied_ref in (november_third_ref, december_third_ref):
            assert db.scalar(
                select(func.count()).select_from(VideoQuotaUsageModel).where(
                    VideoQuotaUsageModel.owner_kind == owner_kind,
                    VideoQuotaUsageModel.owner_ref == owner_ref,
                    VideoQuotaUsageModel.admission_ref == denied_ref,
                )
            ) == 0


def _consume_monthly_grant(
    sessions: sessionmaker[Session], owner_kind: str, owner_ref: str, month: str
) -> dict:
    with sessions() as db:
        return QuotaCommerceService(
            db, "story-video-admission", _SETTINGS
        ).ensure_monthly_included_grant((owner_kind, owner_ref), month)
