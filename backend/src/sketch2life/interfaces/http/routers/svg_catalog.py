"""Authenticated SVG catalog, immutable guide revisions, and exact-hash review API."""

# ruff: noqa: B008

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.svg_catalog import SvgCatalogApplicationService, SvgCatalogError
from sketch2life.contracts.schemas.svg_engine import (
    CreateSvgGuideRevisionRequestV1,
    SvgCatalogAssetCreateRequestV1,
    SvgCatalogAssetResponseV1,
    SvgCatalogPageV1,
    SvgCurationRequestV1,
    SvgGuideCatalogPageV1,
    SvgGuideRevisionPageV1,
    SvgGuideRevisionReceiptV1,
    SvgGuideReviewRequestV1,
    SvgReviewReceiptV1,
    SvgSourceReviewRequestV1,
)
from sketch2life.infrastructure.catalog.svg_assets import (
    SqlSvgCatalogRepository,
    SqlSvgSanitizer,
    SvgCatalogPersistenceError,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import require_assignment

router = APIRouter(prefix="/api/svg-catalog/v1", tags=["SVG catalog v1"])


def get_svg_catalog_service(
    request: Request,
    db: Session = Depends(get_db),
) -> SvgCatalogApplicationService:
    storage = getattr(request.app.state, "lesson_library_storage", None)
    if storage is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "DEPENDENCY_UNAVAILABLE", "message": "SVG object storage is not configured"},
        )
    repository = SqlSvgCatalogRepository(db, storage)
    return SvgCatalogApplicationService(catalog=repository, sanitizer=SqlSvgSanitizer())


def _call(function):
    try:
        return function()
    except (SvgCatalogError, SvgCatalogPersistenceError) as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from None


def _identity(db: Session, principal: VerifiedPrincipal, role: str) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != role
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": f"{role} role is required"})
    return identity


def _teacher(db: Session, principal: VerifiedPrincipal, organization_id: str) -> None:
    require_assignment(db, principal, organization_id, roles={"teacher"})


def _active_teacher_anywhere(db: Session, principal: VerifiedPrincipal) -> None:
    _identity(db, principal, "teacher")
    assigned = db.scalar(
        select(OrganizationAssignmentModel.assignment_id).where(
            OrganizationAssignmentModel.subject == principal.subject,
            OrganizationAssignmentModel.active.is_(True),
            OrganizationAssignmentModel.role == "teacher",
        ).limit(1)
    )
    if assigned is None:
        raise HTTPException(status_code=403, detail={"code": "TEACHER_ASSIGNMENT_REQUIRED"})


def _platform_admin(db: Session, principal: VerifiedPrincipal) -> None:
    _identity(db, principal, "platform_admin")


@router.get("/parent/guides", response_model=SvgGuideCatalogPageV1)
def list_parent_guides(
    topic_key: Annotated[str | None, Query(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")] = None,
    limit: int = Query(default=50, ge=1, le=100),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _identity(db, principal, "parent")
    return _call(lambda: service.list_parent_guides(topic_key=topic_key, limit=limit))


@router.get("/organizations/{organization_id}/assets", response_model=SvgCatalogPageV1)
def list_teacher_assets(
    organization_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.list_teacher_assets(organization_id=organization_id, limit=limit))


@router.post(
    "/organizations/{organization_id}/assets",
    response_model=SvgCatalogAssetResponseV1,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_asset(
    organization_id: str,
    payload: SvgCatalogAssetCreateRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.create_asset(
        scope_kind="ORGANIZATION",
        organization_id=organization_id,
        actor=principal.subject,
        request=payload.model_dump(mode="json"),
    ))


@router.post(
    "/platform/assets",
    response_model=SvgCatalogAssetResponseV1,
    status_code=status.HTTP_201_CREATED,
)
def create_platform_asset(
    payload: SvgCatalogAssetCreateRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _platform_admin(db, principal)
    return _call(lambda: service.create_asset(
        scope_kind="PLATFORM",
        organization_id=None,
        actor=principal.subject,
        request=payload.model_dump(mode="json"),
    ))


@router.post(
    "/organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions",
    response_model=SvgGuideRevisionReceiptV1,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_guide_revision(
    organization_id: str,
    catalog_entry_id: str,
    payload: CreateSvgGuideRevisionRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    asset = _call(lambda: service.catalog.get_asset_for_teacher(
        organization_id=organization_id,
        catalog_entry_id=catalog_entry_id,
    ))
    return _call(lambda: service.create_guide_revision(
        asset=asset,
        actor=principal.subject,
        organization_id=organization_id,
        guide=payload.guide.model_dump(mode="json"),
    ))


@router.get(
    "/organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions",
    response_model=SvgGuideRevisionPageV1,
)
def list_organization_guide_revisions(
    organization_id: str,
    catalog_entry_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.list_guide_revisions(
        organization_id=organization_id,
        catalog_entry_id=catalog_entry_id,
        limit=limit,
    ))


@router.post(
    "/platform/assets/{catalog_entry_id}/guide-revisions",
    response_model=SvgGuideRevisionReceiptV1,
    status_code=status.HTTP_201_CREATED,
)
def create_platform_guide_revision(
    catalog_entry_id: str,
    payload: CreateSvgGuideRevisionRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _platform_admin(db, principal)
    asset = _call(lambda: service.catalog.get_asset_for_platform(catalog_entry_id=catalog_entry_id))
    return _call(lambda: service.create_guide_revision(
        asset=asset,
        actor=principal.subject,
        organization_id=None,
        guide=payload.guide.model_dump(mode="json"),
    ))


@router.post(
    "/organizations/{organization_id}/assets/{catalog_entry_id}/source-reviews",
    response_model=SvgReviewReceiptV1,
)
def review_organization_source(
    organization_id: str,
    catalog_entry_id: str,
    payload: SvgSourceReviewRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    asset = _call(lambda: service.catalog.get_asset_for_teacher(organization_id=organization_id, catalog_entry_id=catalog_entry_id))
    if asset["visibility_scope"] != "ORGANIZATION" or asset["created_by"] == principal.subject:
        raise HTTPException(status_code=403, detail={"code": "INDEPENDENT_REVIEW_REQUIRED"})
    return _call(lambda: service.record_review(
        asset=asset,
        actor=principal.subject,
        review_subject_kind="SOURCE_ASSET",
        review_kind="EDUCATOR",
        source_sha256=payload.source_sha256,
        decision=payload.decision,
        reason=payload.reason,
    ))


@router.post("/platform/assets/{catalog_entry_id}/source-reviews", response_model=SvgReviewReceiptV1)
def review_platform_source(
    catalog_entry_id: str,
    payload: SvgSourceReviewRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _active_teacher_anywhere(db, principal)
    asset = _call(lambda: service.catalog.get_asset_for_platform(catalog_entry_id=catalog_entry_id))
    if asset["created_by"] == principal.subject:
        raise HTTPException(status_code=403, detail={"code": "INDEPENDENT_REVIEW_REQUIRED"})
    return _call(lambda: service.record_review(
        asset=asset,
        actor=principal.subject,
        review_subject_kind="SOURCE_ASSET",
        review_kind="EDUCATOR",
        source_sha256=payload.source_sha256,
        decision=payload.decision,
        reason=payload.reason,
    ))


@router.post(
    "/organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions/{guide_revision_id}/educator-reviews",
    response_model=SvgReviewReceiptV1,
)
def review_organization_guide(
    organization_id: str,
    catalog_entry_id: str,
    guide_revision_id: str,
    payload: SvgGuideReviewRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    asset = _call(lambda: service.catalog.get_asset_for_teacher(organization_id=organization_id, catalog_entry_id=catalog_entry_id))
    guide = _call(lambda: service.get_guide_revision(catalog_entry_id=catalog_entry_id, guide_revision_id=guide_revision_id))
    if guide["visibility_scope"] != "ORGANIZATION" or guide["organization_id"] != organization_id or guide["authored_by"] == principal.subject:
        raise HTTPException(status_code=403, detail={"code": "INDEPENDENT_REVIEW_REQUIRED"})
    return _call(lambda: service.record_review(
        asset=asset,
        actor=principal.subject,
        review_subject_kind="GUIDE",
        review_kind="EDUCATOR",
        source_sha256=payload.source_sha256,
        guide_sha256=payload.guide_sha256,
        guide_revision=guide,
        decision=payload.decision,
        reason=payload.reason,
    ))


@router.post(
    "/platform/assets/{catalog_entry_id}/guide-revisions/{guide_revision_id}/educator-reviews",
    response_model=SvgReviewReceiptV1,
)
def review_platform_guide(
    catalog_entry_id: str,
    guide_revision_id: str,
    payload: SvgGuideReviewRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _active_teacher_anywhere(db, principal)
    asset = _call(lambda: service.catalog.get_asset_for_platform(catalog_entry_id=catalog_entry_id))
    guide = _call(lambda: service.get_guide_revision(catalog_entry_id=catalog_entry_id, guide_revision_id=guide_revision_id))
    if guide["visibility_scope"] != "PLATFORM" or guide["authored_by"] == principal.subject:
        raise HTTPException(status_code=403, detail={"code": "INDEPENDENT_REVIEW_REQUIRED"})
    return _call(lambda: service.record_review(
        asset=asset,
        actor=principal.subject,
        review_subject_kind="GUIDE",
        review_kind="EDUCATOR",
        source_sha256=payload.source_sha256,
        guide_sha256=payload.guide_sha256,
        guide_revision=guide,
        decision=payload.decision,
        reason=payload.reason,
    ))


@router.post("/platform/assets/{catalog_entry_id}/curation", response_model=SvgReviewReceiptV1)
def curate_platform_asset(
    catalog_entry_id: str,
    payload: SvgCurationRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: SvgCatalogApplicationService = Depends(get_svg_catalog_service),
) -> dict[str, object]:
    _platform_admin(db, principal)
    asset = _call(lambda: service.catalog.get_asset_for_platform(catalog_entry_id=catalog_entry_id))
    if asset["created_by"] == principal.subject:
        raise HTTPException(status_code=403, detail={"code": "INDEPENDENT_CURATION_REQUIRED"})
    return _call(lambda: service.record_review(
        asset=asset,
        actor=principal.subject,
        review_subject_kind="SOURCE_ASSET",
        review_kind="CURATOR",
        source_sha256=payload.source_sha256,
        decision=payload.decision,
        reason=payload.reason,
        grouping_allowed=payload.grouping_allowed,
    ))


__all__ = ["router"]
