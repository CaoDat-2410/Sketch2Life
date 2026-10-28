"""Authenticated, deterministic Lesson Library API v1."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import re
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_library import (
    CreateLessonAccessGrantRequestV1,
    CreateLessonRequestV1,
    CreateLessonUploadSessionRequestV1,
    CreateLessonVersionRequestV1,
    CreateParentGroupRequestV1,
    DecideLessonAccessGrantRequestV1,
    InviteParentToGroupRequestV1,
    LessonAccessGrantDecisionResponseV1,
    LessonAccessGrantV1,
    LessonAccessGrantPageV1,
    LessonDetailV1,
    LessonDocumentRevisionPreviewV1,
    LessonExportV1,
    LessonInvitationPageV1,
    LessonModerationV1,
    LessonPageV1,
    LessonSourceDocumentStatusV1,
    LessonVersionV1,
    ModerateLessonRequestV1,
    ParentGroupInvitationPageV1,
    ParentGroupInvitationV1,
    ParentGroupMembershipV1,
    ParentGroupPageV1,
    ParentGroupV1,
    ParentLessonDetailV1,
    ParentLessonPageV1,
    UpdateLessonRequestV1,
    UploadPartReceiptV1,
    UploadSessionV1,
)
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import OrganizationAssignmentModel
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import require_assignment
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError, LessonLibraryService

router = APIRouter(prefix="/api/lesson-library/v1", tags=["Lesson Library v1"])
_ETAG = re.compile(r'^"([1-9][0-9]*)"$')
_CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def get_lesson_library_service(
    request: Request,
    db: Session = Depends(get_db),
) -> LessonLibraryService:
    storage = getattr(request.app.state, "lesson_library_storage", None)
    parser = getattr(request.app.state, "lesson_document_parser", None)
    scanner = getattr(request.app.state, "lesson_document_scanner", None)
    if storage is None or parser is None or scanner is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "DEPENDENCY_UNAVAILABLE", "message": "Lesson Library is not configured"},
        )
    return LessonLibraryService(db, storage=storage, parser=parser, scanner=scanner)


def _call(function):
    try:
        return function()
    except LessonLibraryError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from None


def _strong_revision(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(
            status_code=428,
            detail={"code": "PRECONDITION_REQUIRED", "message": "If-Match is required"},
        )
    match = _ETAG.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_REQUEST", "message": "If-Match must contain a strong numeric ETag"},
        )
    return int(match.group(1))


def _etag(response: Response, revision: int) -> None:
    response.headers["ETag"] = f'"{revision}"'


def _staff(
    db: Session, principal: VerifiedPrincipal, organization_id: str,
) -> bool:
    assignments = require_assignment(
        db, principal, organization_id, roles={"teacher", "school_admin"}
    )
    return any(row.role == "school_admin" for row in assignments)


def _manager(db: Session, principal: VerifiedPrincipal, organization_id: str) -> None:
    require_assignment(db, principal, organization_id, roles={"school_admin"})


def _teacher(db: Session, principal: VerifiedPrincipal, organization_id: str) -> None:
    require_assignment(db, principal, organization_id, roles={"teacher"})


def _parent_actor(db: Session, principal: VerifiedPrincipal) -> None:
    staff_assignment = db.scalar(
        select(OrganizationAssignmentModel.assignment_id)
        .where(
            OrganizationAssignmentModel.subject == principal.subject,
            OrganizationAssignmentModel.active.is_(True),
        )
        .limit(1)
    )
    if staff_assignment is not None:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Use a separate Parent account for Parent endpoints"},
        )


def _platform_admin(principal: VerifiedPrincipal) -> None:
    subjects = {
        item.strip()
        for item in get_settings().platform_admin_subjects.split(",")
        if item.strip()
    }
    if principal.subject not in subjects:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Platform Admin authority is required"},
        )


def _limit_cursor(
    limit: int,
    cursor: str | None,
) -> tuple[int, str | None]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST", "message": "limit must be 1–100"})
    return limit, cursor


@router.post(
    "/organizations/{organization_id}/lessons",
    response_model=LessonDetailV1,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    organization_id: str,
    payload: CreateLessonRequestV1,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    result = _call(lambda: service.create_lesson(
        organization_id=organization_id,
        actor=principal.subject,
        content=payload.content,
        visibility=payload.visibility,
        idempotency_key=idempotency_key,
    ))
    _etag(response, result["revision"])
    return result


@router.get("/organizations/{organization_id}/lessons", response_model=LessonPageV1)
def list_lessons(
    organization_id: str,
    state: Literal["ACTIVE", "ARCHIVED"] | None = None,
    visibility: Literal["PRIVATE", "SCHOOL", "PUBLIC"] | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    manager = _staff(db, principal, organization_id)
    limit, cursor = _limit_cursor(limit, cursor)
    return _call(lambda: service.list_lessons(
        organization_id=organization_id, actor=principal.subject,
        manager=manager, state=state, visibility=visibility, limit=limit, cursor=cursor,
    ))


@router.get("/organizations/{organization_id}/lessons/{lesson_id}", response_model=LessonDetailV1)
def get_lesson(
    organization_id: str,
    lesson_id: str,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    manager = _staff(db, principal, organization_id)
    result = _call(lambda: service.get_lesson(
        organization_id=organization_id, lesson_id=lesson_id,
        actor=principal.subject, manager=manager,
    ))
    _etag(response, result["revision"])
    return result


@router.patch("/organizations/{organization_id}/lessons/{lesson_id}", response_model=LessonDetailV1)
def update_lesson(
    organization_id: str,
    lesson_id: str,
    payload: UpdateLessonRequestV1,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    result = _call(lambda: service.update_lesson(
        organization_id=organization_id, lesson_id=lesson_id, actor=principal.subject,
        expected_revision=_strong_revision(if_match), content=payload.content,
    ))
    _etag(response, result["revision"])
    return result


@router.delete("/organizations/{organization_id}/lessons/{lesson_id}", response_model=LessonDetailV1)
def archive_lesson(
    organization_id: str,
    lesson_id: str,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    manager = _staff(db, principal, organization_id)
    result = _call(lambda: service.archive_lesson(
        organization_id=organization_id, lesson_id=lesson_id, actor=principal.subject,
        manager=manager, expected_revision=_strong_revision(if_match),
    ))
    _etag(response, result["revision"])
    return result


@router.post(
    "/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions",
    response_model=UploadSessionV1,
    status_code=status.HTTP_201_CREATED,
)
def create_upload_session(
    organization_id: str,
    lesson_id: str,
    payload: CreateLessonUploadSessionRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.create_upload_session(
        organization_id=organization_id, lesson_id=lesson_id, actor=principal.subject,
        file_name=payload.file_name, media_type=payload.media_type,
        byte_length=payload.byte_length, sha256=payload.sha256,
        idempotency_key=idempotency_key,
    ))


@router.get("/upload-sessions/{upload_session_id}", response_model=UploadSessionV1)
def get_upload_session(
    upload_session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    return _call(lambda: service.get_upload_session_status(
        upload_session_id=upload_session_id, actor=principal.subject
    ))


@router.delete("/upload-sessions/{upload_session_id}", response_model=UploadSessionV1)
def abort_upload_session(
    upload_session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    return _call(lambda: service.abort_upload_session(
        upload_session_id=upload_session_id, actor=principal.subject
    ))


@router.put("/upload-sessions/{upload_session_id}/parts/{part_number}", response_model=UploadPartReceiptV1)
async def upload_part(
    upload_session_id: str,
    part_number: int,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    x_part_sha256: Annotated[str, Header(alias="X-Part-SHA256", pattern=r"^[0-9a-f]{64}$")] = ...,
    content_range: Annotated[str, Header(alias="Content-Range")] = ...,
) -> dict[str, object]:
    match = _CONTENT_RANGE.fullmatch(content_range)
    if match is None:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST", "message": "Content-Range is invalid"})
    body = await request.body()
    return _call(lambda: service.put_upload_part(
        upload_session_id=upload_session_id,
        actor=principal.subject,
        part_number=part_number,
        body=body,
        part_sha256=x_part_sha256,
        range_start=int(match.group(1)),
        range_end=int(match.group(2)),
        range_total=int(match.group(3)),
    ))


@router.post(
    "/upload-sessions/{upload_session_id}/complete",
    response_model=LessonSourceDocumentStatusV1,
)
def complete_upload(
    upload_session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    return _call(lambda: service.complete_upload(
        upload_session_id=upload_session_id,
        actor=principal.subject,
        idempotency_key=idempotency_key,
    ))


@router.get(
    "/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}",
    response_model=LessonSourceDocumentStatusV1,
)
def get_source_document(
    organization_id: str,
    lesson_id: str,
    source_document_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.get_source_document(
        organization_id=organization_id, lesson_id=lesson_id,
        source_document_id=source_document_id, actor=principal.subject,
    ))


@router.get(
    "/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}",
    response_model=LessonDocumentRevisionPreviewV1,
)
def get_document_revision(
    organization_id: str,
    lesson_id: str,
    source_document_id: str,
    revision_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.get_document_revision(
        organization_id=organization_id, lesson_id=lesson_id,
        source_document_id=source_document_id, revision_id=revision_id,
        actor=principal.subject,
    ))


@router.post(
    "/organizations/{organization_id}/lessons/{lesson_id}/versions",
    response_model=LessonVersionV1,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson_version(
    organization_id: str,
    lesson_id: str,
    payload: CreateLessonVersionRequestV1,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    current_revision = _strong_revision(if_match)
    result = _call(lambda: service.create_lesson_version(
        organization_id=organization_id, lesson_id=lesson_id, actor=principal.subject,
        expected_revision=current_revision,
        source_revision_id=payload.source_document_revision_id,
        content=payload.content,
    ))
    _etag(response, current_revision + 1)
    return result


@router.post(
    "/organizations/{organization_id}/lessons/{lesson_id}/access-grants",
    response_model=LessonAccessGrantV1,
    status_code=status.HTTP_201_CREATED,
)
def create_access_grant(
    organization_id: str,
    lesson_id: str,
    payload: CreateLessonAccessGrantRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _teacher(db, principal, organization_id)
    return _call(lambda: service.create_access_grant(
        organization_id=organization_id, lesson_id=lesson_id, actor=principal.subject,
        version_id=payload.version_id, audience_kind=payload.audience_kind,
        audience_ref=payload.audience_ref, capability=payload.capability,
        expires_at=payload.expires_at, idempotency_key=idempotency_key,
    ))


@router.get("/organizations/{organization_id}/access-grants", response_model=LessonAccessGrantPageV1)
def list_access_grants(
    organization_id: str,
    audience_kind: str | None = None,
    state: str | None = None,
    lesson_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _manager(db, principal, organization_id)
    limit, cursor = _limit_cursor(limit, cursor)
    return _call(lambda: service.list_access_grants(
        organization_id=organization_id, audience_kind=audience_kind,
        state=state, lesson_id=lesson_id, limit=limit, cursor=cursor,
    ))


@router.post(
    "/organizations/{organization_id}/access-grants/{access_grant_id}/decision",
    response_model=LessonAccessGrantDecisionResponseV1,
)
def decide_access_grant(
    organization_id: str,
    access_grant_id: str,
    payload: DecideLessonAccessGrantRequestV1,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _manager(db, principal, organization_id)
    result = _call(lambda: service.decide_access_grant(
        organization_id=organization_id, grant_id=access_grant_id,
        actor=principal.subject, expected_revision=_strong_revision(if_match),
        decision=payload.decision, reason=payload.reason,
        idempotency_key=idempotency_key,
    ))
    _etag(response, result["revision"])
    return result


@router.delete(
    "/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}",
    response_model=dict[str, object],
)
def revoke_access_grant(
    organization_id: str,
    lesson_id: str,
    access_grant_id: str,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    manager = _staff(db, principal, organization_id)
    result = _call(lambda: service.revoke_access_grant(
        organization_id=organization_id, lesson_id=lesson_id,
        grant_id=access_grant_id, actor=principal.subject,
        manager=manager, expected_revision=_strong_revision(if_match),
    ))
    _etag(response, result["revision"])
    return result


@router.post(
    "/organizations/{organization_id}/parent-groups",
    response_model=ParentGroupV1,
    status_code=status.HTTP_201_CREATED,
)
def create_parent_group(
    organization_id: str,
    payload: CreateParentGroupRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _manager(db, principal, organization_id)
    return _call(lambda: service.create_parent_group(
        organization_id=organization_id, actor=principal.subject,
        display_name=payload.display_name, idempotency_key=idempotency_key,
    ))


@router.get("/organizations/{organization_id}/parent-groups", response_model=ParentGroupPageV1)
def list_parent_groups(
    organization_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _manager(db, principal, organization_id)
    limit, cursor = _limit_cursor(limit, cursor)
    return _call(lambda: service.list_parent_groups(
        organization_id=organization_id, limit=limit, cursor=cursor
    ))


@router.post(
    "/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations",
    response_model=ParentGroupInvitationV1,
    status_code=status.HTTP_201_CREATED,
)
def invite_parent_to_group(
    organization_id: str,
    parent_group_id: str,
    payload: InviteParentToGroupRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _manager(db, principal, organization_id)
    return _call(lambda: service.invite_parent_to_group(
        organization_id=organization_id, group_id=parent_group_id,
        actor=principal.subject, parent_principal_ref=payload.parent_principal_ref,
        idempotency_key=idempotency_key,
    ))


@router.get("/me/parent-group-invitations", response_model=ParentGroupInvitationPageV1)
def list_parent_group_invitations(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _parent_actor(db, principal)
    limit, cursor = _limit_cursor(limit, cursor)
    return _call(lambda: service.list_parent_group_invitations(
        parent_principal_ref=principal.subject, limit=limit, cursor=cursor
    ))


@router.post(
    "/me/parent-group-invitations/{membership_id}/accept",
    response_model=ParentGroupMembershipV1,
)
def accept_parent_group_invitation(
    membership_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _parent_actor(db, principal)
    return _call(lambda: service.accept_parent_group_invitation(
        membership_id=membership_id, actor=principal.subject,
        idempotency_key=idempotency_key,
    ))


@router.delete(
    "/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}",
    response_model=ParentGroupMembershipV1,
)
def revoke_parent_group_membership(
    organization_id: str,
    parent_group_id: str,
    membership_id: str,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    manager = False
    try:
        _manager(db, principal, organization_id)
        manager = True
    except HTTPException as exc:
        if exc.status_code != 403:
            raise
    result = _call(lambda: service.revoke_parent_group_membership(
        organization_id=organization_id, group_id=parent_group_id,
        membership_id=membership_id, actor=principal.subject, manager=manager,
        expected_revision=_strong_revision(if_match),
    ))
    _etag(response, result["revision"])
    return result


@router.get("/me/lesson-invitations", response_model=LessonInvitationPageV1)
def list_lesson_invitations(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _parent_actor(db, principal)
    limit, cursor = _limit_cursor(limit, cursor)
    return _call(lambda: service.list_lesson_invitations(
        parent_principal_ref=principal.subject, limit=limit, cursor=cursor
    ))


@router.post(
    "/me/lesson-invitations/{access_grant_id}/accept",
    response_model=dict[str, object],
)
def accept_lesson_invitation(
    access_grant_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _parent_actor(db, principal)
    return _call(lambda: service.respond_to_lesson_invitation(
        access_grant_id=access_grant_id, actor=principal.subject, accept=True,
        idempotency_key=idempotency_key,
    ))


@router.post(
    "/me/lesson-invitations/{access_grant_id}/decline",
    response_model=dict[str, object],
)
def decline_lesson_invitation(
    access_grant_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _parent_actor(db, principal)
    return _call(lambda: service.respond_to_lesson_invitation(
        access_grant_id=access_grant_id, actor=principal.subject, accept=False,
        idempotency_key=idempotency_key,
    ))


@router.get("/me/lessons", response_model=ParentLessonPageV1)
def list_parent_lessons(
    source: Literal["ALL", "PUBLIC", "SHARED"] = "ALL",
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _parent_actor(db, principal)
    limit, cursor = _limit_cursor(limit, cursor)
    return _call(lambda: service.list_parent_lessons(
        parent_principal_ref=principal.subject, source=source,
        limit=limit, cursor=cursor,
    ))


@router.get("/me/lessons/{lesson_id}", response_model=ParentLessonDetailV1)
def get_parent_lesson(
    lesson_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> dict[str, object]:
    _parent_actor(db, principal)
    return _call(lambda: service.get_parent_lesson(
        parent_principal_ref=principal.subject, lesson_id=lesson_id
    ))


@router.get("/me/lessons/{lesson_id}/download", response_model=LessonExportV1)
def download_parent_lesson(
    lesson_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    service: LessonLibraryService = Depends(get_lesson_library_service),
) -> JSONResponse:
    _parent_actor(db, principal)
    result = _call(lambda: service.get_parent_lesson_export(
        parent_principal_ref=principal.subject, lesson_id=lesson_id
    ))
    return JSONResponse(
        content=result,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="lesson-{lesson_id}.json"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/platform/lessons/{lesson_id}/moderation", response_model=LessonModerationV1)
def moderate_lesson(
    lesson_id: str,
    payload: ModerateLessonRequestV1,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonLibraryService = Depends(get_lesson_library_service),
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...,
) -> dict[str, object]:
    _platform_admin(principal)
    result = _call(lambda: service.moderate_lesson(
        lesson_id=lesson_id, actor=principal.subject,
        expected_revision=_strong_revision(if_match),
        moderation_state=payload.state, reason=payload.reason,
        idempotency_key=idempotency_key,
    ))
    _etag(response, result["revision"])
    return result


__all__ = ["router"]
