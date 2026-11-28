"""Focused checks for catalog SVG approval and hash validation on presentation writes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from sketch2life.infrastructure.lesson_occurrences.presentations import LessonPresentationService
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.persistence.svg_catalog_tables import (
    SVG_CATALOG_ASSETS,
    SVG_CATALOG_REVIEWS,
)

ORG_ID = "org-1"
OTHER_ORG_ID = "org-2"
SOURCE_HASH = "b" * 64
CANONICAL_HASH = "a" * 64


@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
    return "JSON"


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE core_svg_catalog_assets (
                asset_ref TEXT NOT NULL, asset_version INTEGER NOT NULL,
                catalog_entry_id TEXT NOT NULL UNIQUE, visibility_scope TEXT NOT NULL,
                organization_id TEXT, canonical_asset_ref TEXT NOT NULL,
                canonical_asset_version INTEGER NOT NULL, topic_key TEXT NOT NULL,
                title_vi TEXT NOT NULL, alt_text_vi TEXT NOT NULL, source_uri TEXT NOT NULL,
                license_id TEXT NOT NULL, license_uri TEXT NOT NULL, source_sha256 TEXT NOT NULL,
                canonical_sha256 TEXT NOT NULL, sanitizer_version TEXT NOT NULL,
                readiness_class TEXT NOT NULL, structural_facts JSON NOT NULL,
                catalog_state TEXT NOT NULL, created_by TEXT NOT NULL, created_at TIMESTAMP NOT NULL,
                PRIMARY KEY (asset_ref, asset_version)
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE core_svg_catalog_reviews (
                review_id TEXT PRIMARY KEY, asset_ref TEXT NOT NULL, asset_version INTEGER NOT NULL,
                guide_revision_id TEXT, review_subject_kind TEXT NOT NULL,
                review_kind TEXT NOT NULL, source_sha256 TEXT NOT NULL, guide_sha256 TEXT,
                reviewer_ref TEXT NOT NULL, decision TEXT NOT NULL, grouping_allowed BOOLEAN NOT NULL,
                reason TEXT, created_at TIMESTAMP NOT NULL
            )
            """
        )
    with Session(engine) as session:
        yield session
    engine.dispose()


def _insert_asset(
    db: Session,
    *,
    scope: str = "ORGANIZATION",
    organization_id: str | None = ORG_ID,
    state: str = "ACTIVE",
    canonical_hash: str = CANONICAL_HASH,
    entry_id: str = "catalog-1",
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "asset_ref": f"asset-{entry_id}",
        "asset_version": 1,
        "catalog_entry_id": entry_id,
        "visibility_scope": scope,
        "organization_id": organization_id,
        "canonical_asset_ref": f"canonical-{entry_id}",
        "canonical_asset_version": 1,
        "topic_key": "shapes",
        "title_vi": "Hình đơn giản",
        "alt_text_vi": "Hình minh họa",
        "source_uri": "https://example.test/source.svg",
        "license_id": "CC0-1.0",
        "license_uri": "https://example.test/license",
        "source_sha256": SOURCE_HASH,
        "canonical_sha256": canonical_hash,
        "sanitizer_version": "test",
        "readiness_class": "REQUIRES_MANUAL_AUTHORING",
        "structural_facts": {"filled_shape_count": 0},
        "catalog_state": state,
        "created_by": "author",
        "created_at": datetime.now(UTC),
    }
    db.execute(insert(SVG_CATALOG_ASSETS).values(**values))
    db.flush()
    return values


def _insert_review(
    db: Session,
    entry: dict[str, Any],
    *,
    review_kind: str,
    decision: str = "APPROVE",
    review_id: str | None = None,
    created_at: datetime | None = None,
) -> None:
    db.execute(
        insert(SVG_CATALOG_REVIEWS).values(
            review_id=review_id or f"{entry['asset_ref']}-{review_kind.lower()}-{decision.lower()}",
            asset_ref=entry["asset_ref"],
            asset_version=entry["asset_version"],
            guide_revision_id=None,
            review_subject_kind="SOURCE_ASSET",
            review_kind=review_kind,
            source_sha256=entry["source_sha256"],
            guide_sha256=None,
            reviewer_ref="reviewer",
            decision=decision,
            grouping_allowed=False,
            reason=None,
            created_at=created_at or datetime.now(UTC),
        )
    )
    db.flush()


def _validate(
    db: Session,
    *,
    entry_id: str = "catalog-1",
    organization_id: str = ORG_ID,
    canonical_hash: str = CANONICAL_HASH,
) -> None:
    service = LessonPresentationService(db, storage=None, svg_drafter=None)
    service._validate_catalog_svg_media(
        {
            "kind": "SVG_CATALOG",
            "catalog_entry_id": entry_id,
            "canonical_sha256": canonical_hash,
        },
        organization_id,
    )


def _assert_error(db: Session, code: str, *, status: int = 409, **kwargs: Any) -> None:
    with pytest.raises(LessonOccurrenceError) as raised:
        _validate(db, **kwargs)
    assert (raised.value.status_code, raised.value.code) == (status, code)


def test_approved_organization_and_platform_catalog_svgs_are_accepted(db: Session) -> None:
    organization_asset = _insert_asset(db)
    _insert_review(db, organization_asset, review_kind="EDUCATOR")
    _validate(db)

    platform_asset = _insert_asset(
        db, entry_id="platform-1", scope="PLATFORM", organization_id=None
    )
    _insert_review(db, platform_asset, review_kind="EDUCATOR")
    _insert_review(db, platform_asset, review_kind="CURATOR")
    _validate(db, entry_id="platform-1")


def test_pending_catalog_svg_is_rejected(db: Session) -> None:
    _insert_asset(db)
    _assert_error(db, "SVG_CATALOG_NOT_APPROVED")


def test_rejected_catalog_svg_is_rejected(db: Session) -> None:
    rejected_asset = _insert_asset(db, state="REJECTED")
    _insert_review(db, rejected_asset, review_kind="EDUCATOR", decision="REJECT")
    _assert_error(db, "SVG_CATALOG_REJECTED")


def test_latest_rejection_supersedes_an_earlier_approval(db: Session) -> None:
    entry = _insert_asset(db)
    now = datetime.now(UTC)
    _insert_review(db, entry, review_kind="EDUCATOR", created_at=now)
    _insert_review(
        db,
        entry,
        review_kind="EDUCATOR",
        decision="REJECT",
        review_id="educator-z-reject",
        created_at=now + timedelta(seconds=1),
    )
    _assert_error(db, "SVG_CATALOG_REJECTED")


def test_catalog_svg_from_another_organization_is_hidden_as_404(db: Session) -> None:
    _insert_asset(db)
    _assert_error(db, "SVG_CATALOG_NOT_AVAILABLE", status=404, organization_id=OTHER_ORG_ID)


def test_changed_catalog_canonical_hash_is_rejected(db: Session) -> None:
    entry = _insert_asset(db)
    _insert_review(db, entry, review_kind="EDUCATOR")
    _assert_error(db, "SVG_CATALOG_HASH_MISMATCH", canonical_hash="f" * 64)
