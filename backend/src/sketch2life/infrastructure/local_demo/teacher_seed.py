"""Idempotent local Teacher/Auth Emulator and organization/class seed."""

from __future__ import annotations

import os
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)

_SEED_NAMESPACE = "sketch2life:rev82:local-teacher-demo:v1"
_ORGANIZATION_ID = "local-rev82-teacher-organization"
_CLASS_ID = "local-rev82-teacher-class"
_ORGANIZATION_NAME = "Trường thử nghiệm Sketch2Life"
_CLASS_NAME = "Lớp thử nghiệm"


def _stable_uid(project_id: str, email: str) -> str:
    return uuid5(NAMESPACE_URL, f"{_SEED_NAMESPACE}:auth:{project_id}:{email}").hex


def _require_local_emulator() -> None:
    settings = get_settings()
    emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "").strip()
    if settings.env != "local" or settings.auth_provider != "firebase":
        raise RuntimeError("LOCAL_TEACHER_SEED_IS_LOCAL_FIREBASE_ONLY")
    if not settings.firebase_project_id or not emulator_host:
        raise RuntimeError("LOCAL_TEACHER_SEED_REQUIRES_AUTH_EMULATOR")
    if emulator_host not in {"firebase-auth:9099", "127.0.0.1:9099", "localhost:9099"}:
        raise RuntimeError("LOCAL_TEACHER_SEED_EMULATOR_HOST_NOT_ALLOWED")


def _seed_auth_user(*, email: str, password: str, project_id: str) -> str:
    if len(password) < 12:
        raise RuntimeError("LOCAL_TEACHER_SEED_PASSWORD_TOO_SHORT")
    from firebase_admin import auth

    app = get_firebase_admin_app(get_settings())
    stable_uid = _stable_uid(project_id, email)
    try:
        user = auth.get_user(stable_uid, app=app)
        if (user.email or "").strip().lower() != email:
            raise RuntimeError("LOCAL_TEACHER_SEED_AUTH_ID_CONFLICT")
        auth.update_user(user.uid, password=password, app=app)
        print("local_teacher_seed_auth=existing_password_synced", flush=True)
        return user.uid
    except auth.UserNotFoundError:
        pass

    try:
        existing = auth.get_user_by_email(email, app=app)
    except auth.UserNotFoundError:
        user = auth.create_user(
            uid=stable_uid,
            email=email,
            password=password,
            display_name="Giáo viên thử nghiệm",
            app=app,
        )
        print("local_teacher_seed_auth=created", flush=True)
        return user.uid

    if existing.uid != stable_uid:
        raise RuntimeError("LOCAL_TEACHER_SEED_AUTH_EMAIL_UID_CONFLICT")
    auth.update_user(existing.uid, password=password, app=app)
    print("local_teacher_seed_auth=existing_password_synced", flush=True)
    return stable_uid


def _ensure_organization(session: Session) -> None:
    organization = session.get(OrganizationModel, _ORGANIZATION_ID)
    if organization is None:
        session.add(
            OrganizationModel(
                organization_id=_ORGANIZATION_ID,
                display_name=_ORGANIZATION_NAME,
                state="active",
            )
        )
        session.flush()
        print("local_teacher_seed_organization=created", flush=True)
    elif (
        organization.display_name != _ORGANIZATION_NAME
        or organization.state != "active"
    ):
        raise RuntimeError("LOCAL_TEACHER_SEED_ORGANIZATION_CONFLICT")
    else:
        print("local_teacher_seed_organization=existing", flush=True)


def _ensure_classroom(session: Session, *, subject: str) -> None:
    classroom = session.get(ClassroomModel, _CLASS_ID)
    if classroom is None:
        session.add(
            ClassroomModel(
                class_id=_CLASS_ID,
                organization_id=_ORGANIZATION_ID,
                display_name=_CLASS_NAME,
                state="active",
                created_by=subject,
            )
        )
        session.flush()
        print("local_teacher_seed_classroom=created", flush=True)
    elif (
        classroom.organization_id != _ORGANIZATION_ID
        or classroom.display_name != _CLASS_NAME
        or classroom.state != "active"
    ):
        raise RuntimeError("LOCAL_TEACHER_SEED_CLASSROOM_CONFLICT")
    else:
        print("local_teacher_seed_classroom=existing", flush=True)


def _ensure_teacher_identity_and_assignment(session: Session, *, subject: str) -> None:
    settings = get_settings()
    issuer = f"https://securetoken.google.com/{settings.firebase_project_id}"
    identity = session.get(AdultIdentityModel, subject)
    if identity is None:
        session.add(
            AdultIdentityModel(
                subject=subject,
                issuer=issuer,
                state="active",
                account_role="teacher",
                role_revision=1,
            )
        )
        session.flush()
        print("local_teacher_seed_identity=created", flush=True)
    elif (
        identity.issuer != issuer
        or identity.account_role != "teacher"
        or identity.state != "active"
    ):
        raise RuntimeError("LOCAL_TEACHER_SEED_IDENTITY_CONFLICT")
    else:
        print("local_teacher_seed_identity=existing", flush=True)

    assignment_id = uuid5(
        NAMESPACE_URL,
        f"{_SEED_NAMESPACE}:assignment:{_ORGANIZATION_ID}:{_CLASS_ID}:{subject}",
    ).hex
    assignment = session.get(OrganizationAssignmentModel, assignment_id)
    if assignment is None:
        existing = session.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == _ORGANIZATION_ID,
                OrganizationAssignmentModel.subject == subject,
                OrganizationAssignmentModel.class_id == _CLASS_ID,
                OrganizationAssignmentModel.role == "teacher",
            )
        )
        if existing is not None:
            if existing.active:
                print("local_teacher_seed_assignment=existing", flush=True)
                return
            raise RuntimeError("LOCAL_TEACHER_SEED_ASSIGNMENT_INACTIVE")
        session.add(
            OrganizationAssignmentModel(
                assignment_id=str(assignment_id),
                organization_id=_ORGANIZATION_ID,
                subject=subject,
                class_id=_CLASS_ID,
                role="teacher",
                active=True,
            )
        )
        session.flush()
        print("local_teacher_seed_assignment=created", flush=True)
    elif (
        assignment.organization_id != _ORGANIZATION_ID
        or assignment.subject != subject
        or assignment.class_id != _CLASS_ID
        or assignment.role != "teacher"
        or not assignment.active
    ):
        raise RuntimeError("LOCAL_TEACHER_SEED_ASSIGNMENT_CONFLICT")
    else:
        print("local_teacher_seed_assignment=existing", flush=True)


def seed_teacher_demo() -> None:
    _require_local_emulator()
    settings = get_settings()
    email = os.getenv("SKETCH2LIFE_LOCAL_SEED_TEACHER_EMAIL", "").strip().lower()
    password = os.getenv("SKETCH2LIFE_LOCAL_SEED_TEACHER_PASSWORD", "")
    if not email or not password:
        print("local_teacher_seed=skipped reason=credentials_not_configured", flush=True)
        return
    if "@" not in email or len(email) > 254:
        raise RuntimeError("LOCAL_TEACHER_SEED_EMAIL_INVALID")

    subject = _seed_auth_user(
        email=email,
        password=password,
        project_id=settings.firebase_project_id,
    )
    engine = create_core_engine()
    sessions = create_core_session_factory(engine)
    try:
        with sessions.begin() as session:
            _ensure_organization(session)
            _ensure_classroom(session, subject=subject)
            _ensure_teacher_identity_and_assignment(session, subject=subject)
        print("local_teacher_seed=complete", flush=True)
    finally:
        engine.dispose()


def main() -> None:
    seed_teacher_demo()


if __name__ == "__main__":
    main()


__all__ = ["main", "seed_teacher_demo"]
