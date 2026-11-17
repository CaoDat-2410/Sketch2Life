"""BE1 gallery, reflection/assessment, portfolio and data-request endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import (
    DataRequestCreate,
    GalleryAnnotationRequest,
    GalleryCreateRequest,
    ObservationCreateRequest,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomSessionModel,
    DataLifecycleRequestModel,
    GallerySnapshotModel,
    ManagedProfileModel,
    ObservationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    audit,
    commit,
    consent_is_effective,
    deny_pending_consent,
    event,
    failure,
    get_class,
    get_session,
    require_assignment,
    session_event,
)

router = APIRouter(
    prefix="/api/be1/v1", tags=["BE1 records and lifecycle"], responses=BE1_ERROR_RESPONSES
)


def _require_contributors_consent(
    db: Session,
    *,
    organization_id: str,
    session: ClassroomSessionModel,
    child_ids: list[str],
    actor: str,
    resource_type: str,
    resource_id: str,
    action: str,
) -> None:
    purpose_ref = str(session.configuration.get("purpose_ref", ""))
    for child_id in set(child_ids):
        if not consent_is_effective(
            db,
            organization_id=organization_id,
            class_id=session.class_id,
            child_id=child_id,
            purpose_ref=purpose_ref,
        ):
            deny_pending_consent(
                db,
                organization_id=organization_id,
                actor=actor,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
            )


@router.post("/organizations/{organization_id}/gallery", status_code=status.HTTP_201_CREATED)
def create_gallery_snapshot(
    organization_id: str,
    payload: GalleryCreateRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = get_session(db, organization_id, payload.session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=session.class_id
    )
    metadata = db.scalar(
        select(CoreAssetMetadataModel)
        .where(
            CoreAssetMetadataModel.organization_id == organization_id,
            CoreAssetMetadataModel.asset_ref == payload.artifact_ref,
        )
        .order_by(CoreAssetMetadataModel.asset_version.desc())
    )
    if metadata is None or f"be1-session:{session.session_id}" not in metadata.source_refs:
        raise failure(404, "ARTIFACT_NOT_FOUND", "Artifact is not available in this session")
    contributors = sorted(set(payload.contributor_ids))
    _require_contributors_consent(
        db,
        organization_id=organization_id,
        session=session,
        child_ids=contributors,
        actor=principal.subject,
        resource_type="gallery",
        resource_id=payload.session_id,
        action="gallery.create",
    )
    gallery_id = str(uuid4())
    row = GallerySnapshotModel(
        gallery_id=gallery_id,
        organization_id=organization_id,
        session_id=session.session_id,
        artifact_ref=payload.artifact_ref,
        audience=payload.audience,
        contributor_refs=contributors,
        caption=payload.caption,
        annotations=[],
        state="draft",
        created_by=principal.subject,
    )
    db.add(row)
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="gallery.snapshot.create",
        resource_type="gallery",
        resource_id=gallery_id,
    )
    session_event(
        db,
        session=session,
        event_type="be1.gallery.snapshot_created.v1",
        payload={"gallery_id": gallery_id, "session_id": session.session_id},
    )
    commit(db)
    return {
        "contract": "Be1GallerySnapshotV1",
        "gallery_id": gallery_id,
        "state": row.state,
        "audience": row.audience,
        "artifact_ref": row.artifact_ref,
    }


@router.get("/organizations/{organization_id}/gallery")
def list_gallery(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = get_session(db, organization_id, session_id)
    require_assignment(db, principal, organization_id, class_id=session.class_id)
    rows = db.scalars(
        select(GallerySnapshotModel)
        .where(
            GallerySnapshotModel.organization_id == organization_id,
            GallerySnapshotModel.session_id == session_id,
            GallerySnapshotModel.state == "published",
        )
        .order_by(GallerySnapshotModel.created_at)
    ).all()
    for row in rows:
        _require_contributors_consent(
            db,
            organization_id=organization_id,
            session=session,
            child_ids=row.contributor_refs,
            actor=principal.subject,
            resource_type="gallery",
            resource_id=row.gallery_id,
            action="gallery.read",
        )
    return {
        "contract": "Be1GalleryListV1",
        "items": [
            {
                "gallery_id": row.gallery_id,
                "artifact_ref": row.artifact_ref,
                "audience": row.audience,
                "contributors": row.contributor_refs,
                "caption": row.caption,
                "annotations": row.annotations,
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }


@router.post("/organizations/{organization_id}/gallery/{gallery_id}/publish")
def publish_gallery(
    organization_id: str,
    gallery_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    row = db.scalar(
        select(GallerySnapshotModel).where(
            GallerySnapshotModel.organization_id == organization_id,
            GallerySnapshotModel.gallery_id == gallery_id,
        )
    )
    if row is None:
        raise failure(404, "GALLERY_NOT_FOUND", "Gallery item was not found")
    session = get_session(db, organization_id, row.session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=session.class_id
    )
    _require_contributors_consent(
        db,
        organization_id=organization_id,
        session=session,
        child_ids=row.contributor_refs,
        actor=principal.subject,
        resource_type="gallery",
        resource_id=gallery_id,
        action="gallery.publish",
    )
    if row.state != "draft":
        raise failure(
            409, "INVALID_GALLERY_TRANSITION", "Only a draft gallery item can be published"
        )
    row.state = "published"
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="gallery.publish",
        resource_type="gallery",
        resource_id=gallery_id,
    )
    session_event(
        db,
        session=session,
        event_type="be1.gallery.published.v1",
        payload={"gallery_id": gallery_id},
    )
    commit(db)
    return {"contract": "Be1GallerySnapshotV1", "gallery_id": gallery_id, "state": row.state}


@router.post("/organizations/{organization_id}/gallery/{gallery_id}/annotations")
def annotate_gallery(
    organization_id: str,
    gallery_id: str,
    payload: GalleryAnnotationRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    row = db.scalar(
        select(GallerySnapshotModel).where(
            GallerySnapshotModel.organization_id == organization_id,
            GallerySnapshotModel.gallery_id == gallery_id,
        )
    )
    if row is None:
        raise failure(404, "GALLERY_NOT_FOUND", "Gallery item was not found")
    session = get_session(db, organization_id, row.session_id)
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin", "teacher", "guide"},
        class_id=session.class_id,
    )
    _require_contributors_consent(
        db,
        organization_id=organization_id,
        session=session,
        child_ids=row.contributor_refs,
        actor=principal.subject,
        resource_type="gallery",
        resource_id=gallery_id,
        action="gallery.annotate",
    )
    if row.state != "published":
        raise failure(
            409, "GALLERY_NOT_PUBLISHED", "Only published gallery items accept annotations"
        )
    annotations = list(row.annotations)
    annotation_id = str(uuid4())
    annotations.append(
        {
            "annotation_id": annotation_id,
            "author_ref": principal.subject,
            "text": payload.text,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    row.annotations = annotations
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="gallery.annotate",
        resource_type="gallery",
        resource_id=gallery_id,
    )
    session_event(
        db,
        session=session,
        event_type="be1.gallery.annotated.v1",
        payload={"annotation_id": annotation_id, "gallery_id": gallery_id},
    )
    commit(db)
    return {
        "contract": "Be1GalleryAnnotationV1",
        "annotation_id": annotation_id,
        "gallery_id": gallery_id,
    }


@router.post(
    "/organizations/{organization_id}/classes/{class_id}/observations",
    status_code=status.HTTP_201_CREATED,
)
def create_observation(
    organization_id: str,
    class_id: str,
    payload: ObservationCreateRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin", "teacher", "guide"},
        class_id=class_id,
    )
    get_class(db, organization_id, class_id)
    session = get_session(db, organization_id, payload.session_id)
    if session.class_id != class_id:
        raise failure(422, "CLASS_SCOPE_MISMATCH", "Session does not belong to this class")
    profile = db.scalar(
        select(ManagedProfileModel).where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.child_id == payload.child_id,
            ManagedProfileModel.state == "active",
        )
    )
    if profile is None:
        raise failure(404, "PROFILE_NOT_FOUND", "Profile was not found in this class")
    content_json = json.dumps(payload.content, ensure_ascii=False, separators=(",", ":"))
    if len(content_json.encode("utf-8")) > 8192:
        raise failure(
            413, "OBSERVATION_TOO_LARGE", "Observation content exceeds the supported size"
        )
    _require_contributors_consent(
        db,
        organization_id=organization_id,
        session=session,
        child_ids=[payload.child_id],
        actor=principal.subject,
        resource_type="observation",
        resource_id=payload.child_id,
        action=f"portfolio.{payload.kind}.record",
    )
    observation_id = str(uuid4())
    row = ObservationModel(
        organization_id=organization_id,
        observation_id=observation_id,
        session_id=session.session_id,
        child_id=payload.child_id,
        kind=payload.kind,
        content=payload.content,
        source_refs=payload.source_refs,
        created_by=principal.subject,
    )
    db.add(row)
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action=f"portfolio.{payload.kind}.record",
        resource_type="observation",
        resource_id=observation_id,
    )
    session_event(
        db,
        session=session,
        event_type=f"be1.portfolio.{payload.kind}_recorded.v1",
        payload={"child_id": payload.child_id, "observation_id": observation_id},
    )
    commit(db)
    return {
        "contract": "Be1ObservationV1",
        "observation_id": observation_id,
        "child_id": payload.child_id,
        "kind": payload.kind,
    }


@router.get("/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio")
def read_portfolio(
    organization_id: str,
    class_id: str,
    child_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, class_id=class_id)
    get_class(db, organization_id, class_id)
    profile = db.scalar(
        select(ManagedProfileModel).where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.child_id == child_id,
            ManagedProfileModel.state == "active",
        )
    )
    if profile is None:
        raise failure(404, "PROFILE_NOT_FOUND", "Profile was not found in this class")
    # Portfolio records aggregate multiple session purposes. Require a future approved
    # portfolio-purpose verifier before returning any child-owned observation/artifact.
    raise failure(
        409,
        "CONSENT_NOT_EFFECTIVE",
        "Portfolio purpose verification is pending; child data is blocked",
    )


@router.post("/organizations/{organization_id}/data-requests", status_code=status.HTTP_202_ACCEPTED)
def create_data_request(
    organization_id: str,
    payload: DataRequestCreate,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"school_admin"})
    request_id = str(uuid4())
    row = DataLifecycleRequestModel(
        organization_id=organization_id,
        request_id=request_id,
        request_type=payload.request_type,
        target_ref=payload.target_ref,
        state="requested",
        unresolved_items=0,
        requested_by=principal.subject,
    )
    db.add(row)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action=f"data_request.{payload.request_type}",
        resource_type="data_request",
        resource_id=request_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=request_id,
        event_type="be1.data_request.created.v1",
        payload={"request_id": request_id, "request_type": payload.request_type},
    )
    commit(db)
    return {
        "contract": "Be1DataRequestV1",
        "request_id": request_id,
        "state": "requested",
        "completion_claimed": False,
    }


@router.get("/organizations/{organization_id}/data-requests/{request_id}")
def read_data_request(
    organization_id: str,
    request_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"school_admin"})
    row = db.scalar(
        select(DataLifecycleRequestModel).where(
            DataLifecycleRequestModel.organization_id == organization_id,
            DataLifecycleRequestModel.request_id == request_id,
        )
    )
    if row is None:
        raise failure(404, "DATA_REQUEST_NOT_FOUND", "Data request was not found")
    return {
        "contract": "Be1DataRequestV1",
        "request_id": row.request_id,
        "request_type": row.request_type,
        "target_ref": row.target_ref,
        "state": row.state,
        "unresolved_items": row.unresolved_items,
        "completion_claimed": row.state == "completed" and row.unresolved_items == 0,
    }


__all__ = ["router"]
