"""Authenticated Parent/Teacher APIs for sharing, inbox, quota and lesson history."""

# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_platform import ParentPlatformError
from sketch2life.application.services.parent_platform import ParentPlatformService
from sketch2life.contracts.schemas.parent_platform import (
    AcceptProfileShareRequestV1,
    CreateProfileShareRequestV1,
    LessonDeliveryCreateRequestV1,
    LessonDeliveryOccurrenceV1,
    LessonDeliveryFeedbackReplyRequestV1,
    LessonDeliveryFeedbackReplyResponseV1,
    LessonDeliveryFeedbackRequestV1,
    LessonDeliveryFeedbackResponseV1,
    NotificationInboxItemV1,
    NotificationInboxPageV1,
    ParentLessonDeliveryPageV1,
    ParentVideoQuotaSummaryV1,
    ProfileShareEnvelopeV1,
    ProfileShareGrantV1,
    ProfileSharePageV1,
    TeacherProfileShareInvitationPageV1,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.parent_platform_repository import (
    SqlParentPlatformRepository,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.parent_consent_policy import require_active_parent_consent_policy

parent_router = APIRouter(prefix="/api/parent/v1", tags=["Parent platform v1"])
teacher_router = APIRouter(prefix="/api/teacher/v1", tags=["Teacher profile sharing v1"])
lesson_router = APIRouter(prefix="/api/lesson-library/v1", tags=["Lesson delivery v1"])
notification_router = APIRouter(prefix="/api/notifications/v1", tags=["Notification inbox v1"])
billing_router = APIRouter(prefix="/api/billing/v1", tags=["Billing read v1"])


def _service(db: Session) -> ParentPlatformService:
    return ParentPlatformService(SqlParentPlatformRepository(db))


def _parent_policy_version(db: Session) -> str:
    return require_active_parent_consent_policy(db).version


def _require_role(
    db: Session, principal: VerifiedPrincipal, role: str
) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != role
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": f"{role.upper()}_ROLE_REQUIRED"})
    return identity


def _invoke(callable_, **kwargs):
    try:
        return callable_(**kwargs)
    except ParentPlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None


@parent_router.post(
    "/child-profiles/{parent_profile_id}/shares",
    response_model=ProfileShareEnvelopeV1,
    status_code=status.HTTP_201_CREATED,
    summary="Invite one named Teacher to link a Parent-owned profile",
)
def create_profile_share(
    parent_profile_id: UUID,
    payload: CreateProfileShareRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
) -> ProfileShareEnvelopeV1:
    _require_role(db, principal, "parent")
    grant = _invoke(
        _service(db).create_profile_share,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
        teacher_subject=payload.teacher_subject,
        policy_version=_parent_policy_version(db),
        idempotency_key=idempotency_key,
    )
    return ProfileShareEnvelopeV1(request_id=uuid4(), grant=ProfileShareGrantV1(**grant))


@parent_router.get(
    "/child-profiles/{parent_profile_id}/shares",
    response_model=ProfileSharePageV1,
    summary="List invitations and active/revoked grants for an owned profile",
)
def list_profile_shares(
    parent_profile_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ProfileSharePageV1:
    _require_role(db, principal, "parent")
    items = _invoke(
        _service(db).list_profile_shares,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
    )
    return ProfileSharePageV1(items=[ProfileShareGrantV1(**item) for item in items])


@parent_router.delete(
    "/child-profiles/{parent_profile_id}/shares/{grant_id}",
    response_model=ProfileShareEnvelopeV1,
    summary="Revoke one profile-share grant immediately",
)
def revoke_profile_share(
    parent_profile_id: UUID,
    grant_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ProfileShareEnvelopeV1:
    _require_role(db, principal, "parent")
    grant = _invoke(
        _service(db).revoke_profile_share,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
        grant_id=str(grant_id),
    )
    return ProfileShareEnvelopeV1(request_id=uuid4(), grant=ProfileShareGrantV1(**grant))


@teacher_router.get(
    "/profile-share-invitations",
    response_model=TeacherProfileShareInvitationPageV1,
    summary="List profile-share invitations addressed to the authenticated Teacher",
)
def list_teacher_profile_share_invitations(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> TeacherProfileShareInvitationPageV1:
    _require_role(db, principal, "teacher")
    items = _invoke(
        _service(db).list_teacher_share_invitations, teacher_subject=principal.subject
    )
    return TeacherProfileShareInvitationPageV1(items=items)


@teacher_router.post(
    "/profile-share-invitations/{grant_id}/accept",
    response_model=ProfileShareEnvelopeV1,
    summary="Accept an addressed invitation and link one managed profile",
)
def accept_teacher_profile_share_invitation(
    grant_id: UUID,
    payload: AcceptProfileShareRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ProfileShareEnvelopeV1:
    _require_role(db, principal, "teacher")
    grant = _invoke(
        _service(db).accept_profile_share,
        teacher_subject=principal.subject,
        grant_id=str(grant_id),
        managed_profile_ref=payload.managed_profile_ref,
    )
    return ProfileShareEnvelopeV1(request_id=uuid4(), grant=ProfileShareGrantV1(**grant))


@teacher_router.post(
    "/profile-share-invitations/{grant_id}/decline",
    response_model=ProfileShareEnvelopeV1,
    summary="Decline an addressed profile-share invitation",
)
def decline_teacher_profile_share_invitation(
    grant_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ProfileShareEnvelopeV1:
    _require_role(db, principal, "teacher")
    grant = _invoke(
        _service(db).decline_profile_share,
        teacher_subject=principal.subject,
        grant_id=str(grant_id),
    )
    return ProfileShareEnvelopeV1(request_id=uuid4(), grant=ProfileShareGrantV1(**grant))


@lesson_router.post(
    "/organizations/{organization_id}/lessons/{lesson_id}/occurrences",
    response_model=LessonDeliveryOccurrenceV1,
    status_code=status.HTTP_201_CREATED,
    summary="Record one approved lesson delivery to an authorized managed profile",
)
def create_lesson_delivery_occurrence(
    organization_id: str,
    lesson_id: UUID,
    payload: LessonDeliveryCreateRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
) -> LessonDeliveryOccurrenceV1:
    _require_role(db, principal, "teacher")
    _require_teacher_organization(db, principal.subject, organization_id)
    result = _invoke(
        _service(db).record_lesson_delivery,
        organization_id=organization_id,
        lesson_id=str(lesson_id),
        version_id=str(payload.lesson_version_id),
        managed_profile_ref=payload.managed_profile_ref,
        teacher_subject=principal.subject,
        idempotency_key=idempotency_key,
    )
    return LessonDeliveryOccurrenceV1(
        contract="LessonDeliveryOccurrenceV1",
        occurrence_id=result["occurrence_id"],
        lesson_id=result["lesson_id"],
        version_id=result["version_id"],
        title=result["lesson_title_snapshot"],
        topic=result["lesson_topic_snapshot"],
        delivered_at=result["delivered_at"],
    )


@lesson_router.get(
    "/me/deliveries",
    response_model=ParentLessonDeliveryPageV1,
    summary="List lessons delivered to one shared Parent profile in the SRS history window",
)
def list_parent_lesson_deliveries(
    profile_id: UUID = Query(),
    cursor: str | None = Query(default=None, min_length=1, max_length=256),
    limit: int = Query(default=20, ge=1, le=50),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentLessonDeliveryPageV1:
    _require_role(db, principal, "parent")
    items, next_cursor = _invoke(
        _service(db).list_parent_deliveries,
        owner_subject=principal.subject,
        parent_profile_id=str(profile_id),
        policy_version=_parent_policy_version(db),
        limit=limit,
        cursor=cursor,
    )
    return ParentLessonDeliveryPageV1(items=items, next_cursor=next_cursor)


@lesson_router.post(
    "/me/deliveries/{occurrence_id}/feedback",
    response_model=LessonDeliveryFeedbackResponseV1,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback for a lesson delivered to an actively shared profile",
)
def submit_parent_lesson_feedback(
    occurrence_id: UUID,
    payload: LessonDeliveryFeedbackRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> LessonDeliveryFeedbackResponseV1:
    _require_role(db, principal, "parent")
    result = _invoke(
        _service(db).submit_delivery_feedback,
        owner_subject=principal.subject,
        parent_profile_id=str(payload.parent_profile_id),
        occurrence_id=str(occurrence_id),
        policy_version=_parent_policy_version(db),
        feedback_text=payload.feedback_text,
    )
    return LessonDeliveryFeedbackResponseV1(**result)


@lesson_router.post(
    "/organizations/{organization_id}/deliveries/{occurrence_id}/feedback-replies",
    response_model=LessonDeliveryFeedbackReplyResponseV1,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to a Parent's lesson feedback inside the owning organization",
)
def reply_to_parent_lesson_feedback(
    organization_id: str,
    occurrence_id: UUID,
    payload: LessonDeliveryFeedbackReplyRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> LessonDeliveryFeedbackReplyResponseV1:
    _require_role(db, principal, "teacher")
    _require_teacher_organization(db, principal.subject, organization_id)
    result = _invoke(
        _service(db).reply_to_delivery_feedback,
        organization_id=organization_id,
        teacher_subject=principal.subject,
        occurrence_id=str(occurrence_id),
        reply_text=payload.reply_text,
    )
    return LessonDeliveryFeedbackReplyResponseV1(**result)


@notification_router.get(
    "/inbox",
    response_model=NotificationInboxPageV1,
    summary="List the authenticated adult's in-app inbox",
)
def list_inbox(
    cursor: str | None = Query(default=None, min_length=1, max_length=256),
    limit: int = Query(default=20, ge=1, le=50),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> NotificationInboxPageV1:
    _require_adult_identity(db, principal)
    items, next_cursor = _invoke(
        _service(db).list_notifications,
        recipient_subject=principal.subject,
        limit=limit,
        cursor=cursor,
    )
    return NotificationInboxPageV1(
        items=[NotificationInboxItemV1(**item) for item in items], next_cursor=next_cursor
    )


@notification_router.post(
    "/inbox/{notification_id}/read",
    response_model=NotificationInboxItemV1,
    summary="Mark one owned in-app notification as read",
)
def mark_inbox_item_read(
    notification_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> NotificationInboxItemV1:
    _require_adult_identity(db, principal)
    item = _invoke(
        _service(db).mark_notification_read,
        recipient_subject=principal.subject,
        notification_id=str(notification_id),
    )
    return NotificationInboxItemV1(**item)


@billing_router.get(
    "/video-quota",
    response_model=ParentVideoQuotaSummaryV1,
    summary="Read the authenticated Parent account's server-derived video quota",
)
def get_parent_video_quota(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentVideoQuotaSummaryV1:
    identity = _require_role(db, principal, "parent")
    result = _invoke(_service(db).get_parent_quota, account_id=identity.account_id)
    return ParentVideoQuotaSummaryV1(**result)


def _require_adult_identity(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if identity is None or identity.state != "active" or identity.issuer != principal.issuer:
        raise HTTPException(status_code=403, detail={"code": "ACTIVE_ADULT_REQUIRED"})
    return identity


def _require_teacher_organization(db: Session, subject: str, organization_id: str) -> None:
    assignment = db.scalar(
        select(OrganizationAssignmentModel.assignment_id).where(
            OrganizationAssignmentModel.subject == subject,
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.role == "teacher",
            OrganizationAssignmentModel.active.is_(True),
        ).limit(1)
    )
    if assignment is None:
        raise HTTPException(status_code=403, detail={"code": "TEACHER_ORGANIZATION_SCOPE_REQUIRED"})


__all__ = [
    "billing_router",
    "lesson_router",
    "notification_router",
    "parent_router",
    "teacher_router",
]
