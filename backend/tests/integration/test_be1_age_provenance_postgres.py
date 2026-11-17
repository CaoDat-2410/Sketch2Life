"""PostgreSQL acceptance for persisted synthetic age provenance."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomModel,
    ConsentRecordModel,
    ManagedProfileModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_store import PostgresCoreStore
from sketch2life.interfaces.http import app as http_app
from sketch2life.interfaces.http import be1_runtime as be1_runtime_module
from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def postgres_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[object]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL for the isolated PostgreSQL age-provenance test")

    parsed = make_url(database_url)
    if "be1_acceptance" not in (parsed.database or ""):
        pytest.fail("the PostgreSQL age-provenance test requires a disposable be1_acceptance DB")
    if parsed.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("the PostgreSQL age-provenance test only permits loopback hosts")
    for key in ("host", "hostaddr"):
        values = parsed.query.get(key, ())
        if isinstance(values, str):
            values = (values,)
        if any(value not in {"localhost", "127.0.0.1", "::1"} for value in values):
            pytest.fail("the PostgreSQL age-provenance test rejects non-loopback query hosts")

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("SKETCH2LIFE_S3_ACCESS_KEY", "synthetic-test-key")
    monkeypatch.setenv("SKETCH2LIFE_S3_SECRET_KEY", "synthetic-test-secret")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "synthetic-test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "synthetic-test-secret")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    settings_factory = cast(Callable[..., Settings], Settings)
    core_settings_factory = cast(Callable[..., CoreDatabaseSettings], CoreDatabaseSettings)
    monkeypatch.setattr(http_app, "get_settings", lambda: settings_factory(_env_file=None))
    monkeypatch.setattr(
        be1_runtime_module,
        "get_core_database_settings",
        lambda: core_settings_factory(_env_file=None),
    )
    app = http_app.create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("the BE1 PostgreSQL runtime did not initialize")

    try:
        yield runtime
    finally:
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_operator_created_synthetic_profile_persists_age_provenance_and_no_consent(
    postgres_runtime: object,
) -> None:
    runtime = postgres_runtime
    sessions = runtime.session_factory  # type: ignore[attr-defined]
    store = PostgresCoreStore(sessions)
    organization_id = f"synthetic-org-{uuid4()}"
    class_id = f"synthetic-class-{uuid4()}"
    child_id = f"synthetic-{uuid4()}"
    operator_id = f"synthetic-operator-{uuid4()}"

    try:
        with sessions.begin() as db:
            db.add(
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic age-provenance acceptance",
                    state="active",
                )
            )
            db.flush()
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=organization_id,
                    display_name="Synthetic class",
                    state="active",
                    created_by=operator_id,
                )
            )

        assert store.create_synthetic_profile(
            organization_id=organization_id,
            class_id=class_id,
            child_id=child_id,
            display_name="Synthetic profile",
            age_months=60,
            created_by=operator_id,
        )

        with sessions() as db:
            profile = db.get(ManagedProfileModel, child_id)
            assert profile is not None
            assert profile.age_revision == 1
            assert profile.age_source == "SYNTHETIC_FIXTURE"
            assert profile.data_origin == "SYNTHETIC_DEV"
            assert profile.consent_id is None
            assert profile.consent_purpose_ref is None
            consent_count = db.scalar(
                select(func.count())
                .select_from(ConsentRecordModel)
                .where(
                    ConsentRecordModel.organization_id == organization_id,
                    ConsentRecordModel.child_id == child_id,
                )
            )
            assert consent_count == 0

        with pytest.raises(IntegrityError), sessions.begin() as db:
            db.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == child_id)
                .values(age_revision=0)
            )

        with pytest.raises(IntegrityError), sessions.begin() as db:
            db.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == child_id)
                .values(age_source="UNRECOGNIZED")
            )
    finally:
        with sessions.begin() as db:
            db.execute(delete(ManagedProfileModel).where(ManagedProfileModel.child_id == child_id))
            db.execute(delete(ClassroomModel).where(ClassroomModel.class_id == class_id))
            db.execute(
                delete(OrganizationModel).where(
                    OrganizationModel.organization_id == organization_id
                )
            )
