"""SVG review routes persist approved decisions through an isolated SQLite catalog."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from io import BytesIO
from typing import Any, BinaryIO

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.infrastructure.catalog.svg_assets import SqlSvgCatalogRepository
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.svg_catalog_tables import (
    CORE_ASSET_LINEAGE,
    SVG_CATALOG_ASSETS,
    SVG_CATALOG_GUIDE_REVISIONS,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.svg_catalog import router

ORG_ID = "review-org"
OTHER_ORG_ID = "other-org"
TEACHER = "teacher-reviewer"
AUTHOR = "teacher-author"
ADMIN = "platform-admin"
ISSUER = "test-issuer"
SOURCE_HASH = "a" * 64
GUIDE_HASH = "b" * 64


class _MemoryObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}

    def put_object(
        self,
        key: str,
        body: BinaryIO,
        *,
        content_type: str,
        content_length: int,
        metadata: Mapping[str, str],
    ) -> None:
        content = body.read()
        if len(content) != content_length:
            raise ValueError("stored object length did not match")
        self.objects[key] = (content, content_type, dict(metadata))

    def get_object(self, key: str) -> StoredObject | None:
        value = self.objects.get(key)
        if value is None:
            return None
        content, content_type, metadata = value
        return StoredObject(BytesIO(content), len(content), content_type, metadata)

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
    return "JSON"


def _create_svg_sqlite_tables(engine: Any) -> None:
    statements = (
        """
        CREATE TABLE core_asset_metadata (
            asset_ref VARCHAR(256) NOT NULL,
            asset_version INTEGER NOT NULL,
            organization_id VARCHAR(128),
            owner_scope_kind VARCHAR(32) NOT NULL,
            owner_scope_ref VARCHAR(128),
            content_sha256 VARCHAR(64) NOT NULL,
            media_type VARCHAR(128) NOT NULL,
            source_refs JSON NOT NULL,
            derived_from_ref VARCHAR(256),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (asset_ref, asset_version),
            CHECK (asset_version > 0),
            CHECK (length(content_sha256) = 64),
            CHECK (
                (owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL
                    AND length(owner_scope_ref) > 0 AND organization_id IS NULL) OR
                (owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL AND
                    (owner_scope_ref IS NULL OR
                        (length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id))) OR
                (owner_scope_kind = 'PLATFORM' AND organization_id IS NULL
                    AND owner_scope_ref IS NOT NULL AND owner_scope_ref = 'PLATFORM')
            )
        )
        """,
        """
        CREATE TABLE core_svg_catalog_assets (
            asset_ref TEXT NOT NULL,
            asset_version INTEGER NOT NULL,
            catalog_entry_id TEXT NOT NULL UNIQUE,
            visibility_scope TEXT NOT NULL,
            organization_id TEXT,
            canonical_asset_ref TEXT NOT NULL,
            canonical_asset_version INTEGER NOT NULL,
            topic_key TEXT NOT NULL,
            title_vi TEXT NOT NULL,
            alt_text_vi TEXT NOT NULL,
            source_uri TEXT NOT NULL,
            license_id TEXT NOT NULL,
            license_uri TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            canonical_sha256 TEXT NOT NULL,
            sanitizer_version TEXT NOT NULL,
            readiness_class TEXT NOT NULL,
            structural_facts JSON NOT NULL,
            catalog_state TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            PRIMARY KEY (asset_ref, asset_version)
        )
        """,
        """
        CREATE TABLE core_svg_catalog_guide_revisions (
            guide_revision_id TEXT PRIMARY KEY,
            guide_ref TEXT NOT NULL,
            guide_revision INTEGER NOT NULL,
            asset_ref TEXT NOT NULL,
            asset_version INTEGER NOT NULL,
            visibility_scope TEXT NOT NULL,
            organization_id TEXT,
            source_sha256 TEXT NOT NULL,
            guide_sha256 TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            guide_json JSON NOT NULL,
            authored_by TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE core_svg_catalog_reviews (
            review_id TEXT PRIMARY KEY,
            asset_ref TEXT NOT NULL,
            asset_version INTEGER NOT NULL,
            guide_revision_id TEXT,
            review_subject_kind TEXT NOT NULL,
            review_kind TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            guide_sha256 TEXT,
            reviewer_ref TEXT NOT NULL,
            decision TEXT NOT NULL,
            grouping_allowed BOOLEAN NOT NULL,
            reason TEXT,
            created_at TIMESTAMP NOT NULL
        )
        """,
    )
    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)
    CORE_ASSET_LINEAGE.create(engine)


def _asset_values(
    *, entry_id: str, asset_ref: str, scope: str, organization_id: str | None, author: str
) -> dict[str, Any]:
    return {
        "asset_ref": asset_ref,
        "asset_version": 1,
        "catalog_entry_id": entry_id,
        "visibility_scope": scope,
        "organization_id": organization_id,
        "canonical_asset_ref": f"canonical-{asset_ref}",
        "canonical_asset_version": 1,
        "topic_key": "shapes",
        "title_vi": "Shapes",
        "alt_text_vi": "A simple shape",
        "source_uri": "https://example.test/source.svg",
        "license_id": "CC0",
        "license_uri": "https://example.test/license",
        "source_sha256": SOURCE_HASH,
        "canonical_sha256": SOURCE_HASH,
        "sanitizer_version": "test-sanitizer",
        "readiness_class": "REQUIRES_MANUAL_AUTHORING",
        "structural_facts": {"filled_shape_count": 0},
        "catalog_state": "ACTIVE",
        "created_by": author,
        "created_at": datetime.now(UTC),
    }


@pytest.fixture
def svg_review_api():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    _create_svg_sqlite_tables(engine)
    for model in (OrganizationModel, AdultIdentityModel, OrganizationAssignmentModel):
        model.__table__.create(engine)

    with Session(engine) as db:
        db.add_all(
            [
                OrganizationModel(organization_id=ORG_ID, display_name="Review School"),
                OrganizationModel(organization_id=OTHER_ORG_ID, display_name="Other School"),
                AdultIdentityModel(
                    subject=TEACHER,
                    account_id="teacher-account",
                    issuer=ISSUER,
                    state="active",
                    account_role="teacher",
                ),
                AdultIdentityModel(
                    subject=AUTHOR,
                    account_id="author-account",
                    issuer=ISSUER,
                    state="active",
                    account_role="teacher",
                ),
                AdultIdentityModel(
                    subject=ADMIN,
                    account_id="admin-account",
                    issuer=ISSUER,
                    state="active",
                    account_role="platform_admin",
                ),
                OrganizationAssignmentModel(
                    assignment_id="reviewer-assignment",
                    organization_id=ORG_ID,
                    subject=TEACHER,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id="reviewer-other-org-assignment",
                    organization_id=OTHER_ORG_ID,
                    subject=TEACHER,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id="author-assignment",
                    organization_id=ORG_ID,
                    subject=AUTHOR,
                    role="teacher",
                    active=True,
                ),
            ]
        )
        for values in (
            _asset_values(
                entry_id="org-source-entry",
                asset_ref="org-source-asset",
                scope="ORGANIZATION",
                organization_id=ORG_ID,
                author=AUTHOR,
            ),
            _asset_values(
                entry_id="platform-source-entry",
                asset_ref="platform-source-asset",
                scope="PLATFORM",
                organization_id=None,
                author=AUTHOR,
            ),
            _asset_values(
                entry_id="org-guide-entry",
                asset_ref="org-guide-asset",
                scope="ORGANIZATION",
                organization_id=ORG_ID,
                author=AUTHOR,
            ),
            _asset_values(
                entry_id="platform-guide-entry",
                asset_ref="platform-guide-asset",
                scope="PLATFORM",
                organization_id=None,
                author=AUTHOR,
            ),
            _asset_values(
                entry_id="curation-entry",
                asset_ref="curation-asset",
                scope="PLATFORM",
                organization_id=None,
                author=AUTHOR,
            ),
        ):
            db.execute(insert(SVG_CATALOG_ASSETS).values(**values))
        for asset_ref, scope, organization_id, revision_id in (
            ("org-guide-asset", "ORGANIZATION", ORG_ID, "org-guide-revision"),
            (
                "platform-guide-asset",
                "PLATFORM",
                None,
                "platform-guide-revision",
            ),
        ):
            db.execute(
                insert(SVG_CATALOG_GUIDE_REVISIONS).values(
                    guide_revision_id=revision_id,
                    guide_ref=f"guide-{revision_id}",
                    guide_revision=1,
                    asset_ref=asset_ref,
                    asset_version=1,
                    visibility_scope=scope,
                    organization_id=organization_id,
                    source_sha256=SOURCE_HASH,
                    guide_sha256=GUIDE_HASH,
                    schema_version="SketchStrokeGuideV3",
                    guide_json={"schema_version": "SketchStrokeGuideV3", "stages": []},
                    authored_by=AUTHOR,
                    created_at=datetime.now(UTC),
                )
            )
        db.commit()

    current_principal = {"value": VerifiedPrincipal(TEACHER, ISSUER, frozenset())}
    app = FastAPI()
    app.state.lesson_library_storage = _MemoryObjectStorage()
    app.include_router(router)

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_verified_adult] = lambda: current_principal["value"]
    with TestClient(app) as client:
        yield client, engine, current_principal
    engine.dispose()


@pytest.mark.parametrize("scope", ["ORGANIZATION", "PLATFORM"])
def test_guide_revision_lifecycle_uses_real_repository(
    svg_review_api: Any, scope: str
) -> None:
    client, _engine, current_principal = svg_review_api
    author = AUTHOR if scope == "ORGANIZATION" else ADMIN
    current_principal["value"] = VerifiedPrincipal(author, ISSUER, frozenset())
    source_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path id="path-a" d="M0 0 L10 10"/>'
        '<path id="path-b" d="M10 0 L20 10"/>'
        '<path id="path-c" d="M20 0 L30 10"/>'
        '<path id="path-d" d="M30 0 L40 10"/>'
        "</svg>"
    )
    asset_request = {
        "contract": "SvgCatalogAssetCreateRequestV1",
        "title_vi": "Four paths",
        "topic_key": "shapes",
        "alt_text_vi": "Four independent paths",
        "source_uri": "https://example.test/source.svg",
        "license_id": "CC0",
        "license_uri": "https://example.test/license",
        "source_svg": source_svg,
    }
    create_asset_path = (
        f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets"
        if scope == "ORGANIZATION"
        else "/api/svg-catalog/v1/platform/assets"
    )
    created_asset = client.post(create_asset_path, json=asset_request)
    assert created_asset.status_code == 201, created_asset.text
    asset = created_asset.json()
    catalog_entry_id = asset["catalog_entry_id"]

    current_principal["value"] = VerifiedPrincipal(TEACHER, ISSUER, frozenset())
    detail_path = f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/{catalog_entry_id}"
    detail = client.get(detail_path)
    assert detail.status_code == 200, detail.text
    assert detail.json()["catalog_entry_id"] == catalog_entry_id
    assert detail.json()["document"] == asset["document"]
    assert detail.json()["review_state"] == "PENDING_EDUCATOR_REVIEW"
    if scope == "ORGANIZATION":
        outside_org = client.get(
            f"/api/svg-catalog/v1/organizations/{OTHER_ORG_ID}/assets/{catalog_entry_id}"
        )
        missing = client.get(
            f"/api/svg-catalog/v1/organizations/{OTHER_ORG_ID}/assets/not-an-entry"
        )
        assert outside_org.status_code == missing.status_code == 404
        assert outside_org.json()["detail"]["code"] == missing.json()["detail"]["code"]

    source_review_path = (
        f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/{catalog_entry_id}/source-reviews"
        if scope == "ORGANIZATION"
        else f"/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/source-reviews"
    )
    source_review = client.post(
        source_review_path,
        json={
            "contract": "SvgSourceReviewRequestV1",
            "source_sha256": asset["source_sha256"],
            "decision": "APPROVE",
        },
    )
    assert source_review.status_code == 200, source_review.text
    assert source_review.json()["reviewer_ref"] == TEACHER

    path_ids = [path["path_id"] for path in asset["document"]["paths"]]
    assert path_ids == ["path-a", "path-b", "path-c", "path-d"]
    assert asset["source_sha256"] != asset["canonical_sha256"]
    guide = {
        "schema_version": "SketchStrokeGuideV3",
        "guide_id": f"{scope.lower()}-guide",
        "title_vi": "Draw four paths",
        "source_asset_ref": asset["source_asset_ref"],
        "source_asset_version": asset["source_asset_version"],
        "source_sha256": asset["source_sha256"],
        "parts": [
            {
                "part_id": "main-part",
                "label_vi": "Net ve",
                "path_ids": path_ids,
                "depends_on": [],
            }
        ],
        "stages": [
            {
                "step_index": index,
                "instruction_vi": f"Ve net {index}",
                "part_ids": ["main-part"],
                "new_path_ids": [path_id],
                "animation_order": [path_id],
            }
            for index, path_id in enumerate(path_ids, start=1)
        ],
    }
    current_principal["value"] = VerifiedPrincipal(author, ISSUER, frozenset())
    create_guide_path = (
        f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/{catalog_entry_id}/guide-revisions"
        if scope == "ORGANIZATION"
        else f"/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/guide-revisions"
    )
    created_guide = client.post(
        create_guide_path,
        json={"contract": "CreateSvgGuideRevisionRequestV1", "guide": guide},
    )
    assert created_guide.status_code == 201, created_guide.text
    guide_receipt = created_guide.json()
    assert guide_receipt["source_sha256"] == asset["source_sha256"]
    assert guide_receipt["guide"]["source_sha256"] == asset["source_sha256"]

    current_principal["value"] = VerifiedPrincipal(TEACHER, ISSUER, frozenset())
    list_path = (
        f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/{catalog_entry_id}/guide-revisions"
    )
    listed = client.get(list_path)
    assert listed.status_code == 200, listed.text
    assert [item["guide_revision_id"] for item in listed.json()["items"]] == [
        guide_receipt["guide_revision_id"]
    ]
    assert listed.json()["items"][0]["review_state"] == "PENDING"

    review_path = (
        f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/{catalog_entry_id}/guide-revisions/"
        f"{guide_receipt['guide_revision_id']}/educator-reviews"
        if scope == "ORGANIZATION"
        else f"/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/guide-revisions/"
        f"{guide_receipt['guide_revision_id']}/educator-reviews"
    )
    reviewed = client.post(
        review_path,
        json={
            "contract": "SvgGuideReviewRequestV1",
            "source_sha256": asset["source_sha256"],
            "guide_sha256": guide_receipt["guide_sha256"],
            "decision": "APPROVE",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["reviewer_ref"] == TEACHER

    approved = client.get(list_path)
    assert approved.status_code == 200, approved.text
    assert approved.json()["items"][0]["review_state"] == "APPROVED"
    if scope == "ORGANIZATION":
        with Session(_engine) as db:
            db.execute(
                update(SVG_CATALOG_ASSETS)
                .where(SVG_CATALOG_ASSETS.c.catalog_entry_id == catalog_entry_id)
                .values(catalog_state="REJECTED")
            )
            db.commit()
        rejected = client.get(detail_path)
        assert rejected.status_code == 404
        assert rejected.json()["detail"]["code"] == outside_org.json()["detail"]["code"]


def test_all_svg_review_routes_persist_with_raw_asset_rows(svg_review_api: Any) -> None:
    client, engine, current_principal = svg_review_api
    source_review = {"source_sha256": SOURCE_HASH, "decision": "APPROVE"}
    guide_review = {
        "source_sha256": SOURCE_HASH,
        "guide_sha256": GUIDE_HASH,
        "decision": "APPROVE",
    }

    responses = (
        client.post(
            f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/org-source-entry/source-reviews",
            json=source_review,
        ),
        client.post(
            "/api/svg-catalog/v1/platform/assets/platform-source-entry/source-reviews",
            json=source_review,
        ),
        client.post(
            f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/org-guide-entry/"
            "guide-revisions/org-guide-revision/educator-reviews",
            json=guide_review,
        ),
        client.post(
            "/api/svg-catalog/v1/platform/assets/platform-guide-entry/"
            "guide-revisions/platform-guide-revision/educator-reviews",
            json=guide_review,
        ),
    )
    assert [response.status_code for response in responses] == [200, 200, 200, 200]
    assert all(response.json()["decision"] == "APPROVE" for response in responses)

    current_principal["value"] = VerifiedPrincipal(ADMIN, ISSUER, frozenset())
    curation = client.post(
        "/api/svg-catalog/v1/platform/assets/curation-entry/curation",
        json={"source_sha256": SOURCE_HASH, "decision": "APPROVE", "grouping_allowed": True},
    )
    assert curation.status_code == 200
    assert curation.json()["review_kind"] == "CURATOR"

    with Session(engine) as db:
        repository = SqlSvgCatalogRepository(db, storage=object())
        source_asset = dict(repository._load_asset("org-source-entry"))
        source_asset["structural_facts"] = {"filled_shape_count": 0}
        assert repository._asset_response(source_asset, include_document=False)["review_state"] == (
            "APPROVED"
        )


def test_svg_review_routes_keep_scope_and_independent_review_guards(svg_review_api: Any) -> None:
    client, _engine, current_principal = svg_review_api
    body = {"source_sha256": SOURCE_HASH, "decision": "APPROVE"}
    outside_org = client.post(
        f"/api/svg-catalog/v1/organizations/{OTHER_ORG_ID}/assets/org-source-entry/source-reviews",
        json=body,
    )
    assert outside_org.status_code == 404

    current_principal["value"] = VerifiedPrincipal(AUTHOR, ISSUER, frozenset())
    author_review = client.post(
        f"/api/svg-catalog/v1/organizations/{ORG_ID}/assets/org-source-entry/source-reviews",
        json=body,
    )
    assert author_review.status_code == 403
    assert author_review.json()["detail"]["code"] == "INDEPENDENT_REVIEW_REQUIRED"
