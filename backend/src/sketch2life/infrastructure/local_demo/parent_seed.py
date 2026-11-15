"""Idempotent, insert-only synthetic Parent demo seed for local Compose."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.domain.lesson_library.model import canonical_content_hash, validate_content
from sketch2life.domain.parent_profiles import (
    ParentProfileRevisionInput,
    profile_revision_sha256,
)
from sketch2life.infrastructure.config.settings import Settings, get_settings
from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentDataAuthorizationModel,
    ParentProfileRevisionModel,
)

_SEED_ACTOR = "system.local-seed.parent-catalog"
_SEED_ORGANIZATION = "local-demo-organization"
_LESSON_TITLE = "Khám phá bướm trong vườn · Bài học mẫu"
_AGE_BAND_REF = "age-72-107-months-v1"
_LESSON_NAMESPACE = "sketch2life:local-demo:parent-butterfly-lesson:v1"


def _stable_id(name: str) -> str:
    return str(uuid5(NAMESPACE_URL, name))


def _lesson_content() -> dict[str, object]:
    return {
        "locale": "vi-VN",
        "title": _LESSON_TITLE,
        "topic": "Bướm và khu vườn",
        "target_age_band_ref": _AGE_BAND_REF,
        "target_age_band_version": 1,
        "objectives": [
            "Quan sát đặc điểm của bướm và môi trường sống quanh khu vườn",
            "So sánh màu sắc, hình dạng và cách di chuyển qua hoạt động ngoài trời",
        ],
        "drawing_subject": "Con bướm",
        "drawing_steps_text": (
            "Vẽ phần thân ở giữa, thêm hai cánh lớn hai bên, rồi quan sát và bổ sung "
            "các đường nét hoặc màu sắc theo ý tưởng của trẻ."
        ),
        "subject_learning_notes": (
            "Bướm là côn trùng có sáu chân và hai cặp cánh. Trẻ có thể quan sát hình ảnh "
            "hoặc bướm ở xa mà không bắt hay chạm vào chúng."
        ),
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            {
                "title": "Tìm màu trong khu vườn",
                "objective": "Trẻ quan sát và so sánh màu sắc quanh khu vườn",
                "materials_text": "Thẻ màu do người lớn chuẩn bị",
                "preparation_text": "Người lớn đặt thẻ màu ở khu vực sân vườn an toàn",
                "instructions_text": (
                    "Ở ngoài trời, trẻ tự chọn một thẻ màu, quan sát cây và hoa từ lối đi, "
                    "rồi chỉ ra màu gần giống mà không hái hoặc chạm vào cây."
                ),
                "observation_notes": "Ghi nhận màu trẻ tự chọn và cách trẻ so sánh",
                "safety_notes": "Người lớn ở cạnh; không hái cây hoặc chạm côn trùng",
                "activity_kind": "outdoor",
            },
            {
                "title": "Bướm giấy bay theo gió",
                "objective": "Trẻ khám phá chuyển động nhẹ của cánh bướm",
                "materials_text": "Hình bướm giấy lớn do người lớn chuẩn bị",
                "preparation_text": "Người lớn chọn khoảng sân thoáng, tránh lối xe",
                "instructions_text": (
                    "Ở sân ngoài trời, trẻ tự chọn cách nâng hoặc nghiêng hình bướm giấy, "
                    "quan sát chuyển động trong gió nhẹ và mô tả điều mình nhận thấy."
                ),
                "observation_notes": "Quan sát cách trẻ thử nghiệm chuyển động của giấy",
                "safety_notes": "Người lớn giám sát; không chạy ra lối xe hoặc gần nước",
                "activity_kind": "outdoor",
            },
            {
                "title": "Bước đi như cánh bướm",
                "objective": "Trẻ liên hệ chuyển động với hình ảnh bướm",
                "materials_text": "Không cần vật liệu",
                "preparation_text": "Người lớn chọn một khoảng sân bằng phẳng",
                "instructions_text": (
                    "Trong sân ngoài trời, trẻ tự chọn một chuyển động chậm của đôi cánh, "
                    "thử nghiệm bằng tay tại chỗ rồi quan sát sự khác nhau giữa các cách làm."
                ),
                "observation_notes": "Ghi nhận chuyển động trẻ tự chọn và mô tả",
                "safety_notes": "Người lớn ở gần; trẻ di chuyển chậm trên nền bằng phẳng",
                "activity_kind": "outdoor",
            },
        ],
    }


def _seed_firebase_parent(settings: Settings) -> str | None:
    email = settings.local_seed_parent_email.strip().lower()
    password = (
        settings.local_seed_parent_password.get_secret_value()
        if settings.local_seed_parent_password
        else ""
    )
    if not email or not password:
        print("local_parent_seed_auth=skipped reason=credentials_not_configured", flush=True)
        return None
    if len(password) < 6:
        raise RuntimeError("LOCAL_PARENT_SEED_CREDENTIALS_INCOMPLETE")
    if settings.env != "local" or not os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
        raise RuntimeError("LOCAL_PARENT_SEED_REQUIRES_FIREBASE_AUTH_EMULATOR")
    if settings.auth_provider != "firebase" or not settings.firebase_project_id:
        raise RuntimeError("LOCAL_PARENT_SEED_REQUIRES_FIREBASE_AUTH_CONFIGURATION")

    from firebase_admin import auth

    app = get_firebase_admin_app(settings)
    stable_uid = _stable_id(f"firebase-parent:{settings.firebase_project_id}:{email}")
    try:
        user = auth.get_user(stable_uid, app=app)
        if (user.email or "").strip().lower() != email:
            raise RuntimeError("LOCAL_PARENT_SEED_AUTH_ID_CONFLICT")
        auth.update_user(user.uid, password=password, app=app)
        print("local_parent_seed_auth=existing_password_synced", flush=True)
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
            display_name="Tài khoản phụ huynh thử nghiệm",
            app=app,
        )
        print("local_parent_seed_auth=created", flush=True)
        return user.uid
    auth.update_user(existing.uid, password=password, app=app)
    print("local_parent_seed_auth=reused_existing_email_password_synced", flush=True)
    return existing.uid


def _ensure_parent_identity_and_profile(
    session: Session, *, subject: str, settings: Settings
) -> None:
    issuer = f"https://securetoken.google.com/{settings.firebase_project_id}"
    identity = session.get(AdultIdentityModel, subject)
    if identity is None:
        session.add(
            AdultIdentityModel(
                subject=subject,
                issuer=issuer,
                state="active",
                account_role="parent",
                role_revision=1,
            )
        )
        session.flush()
        print("local_parent_seed_identity=created", flush=True)
    elif identity.issuer != issuer or identity.account_role != "parent" or identity.state != "active":
        raise RuntimeError("LOCAL_PARENT_SEED_IDENTITY_CONFLICT")
    else:
        print("local_parent_seed_identity=existing", flush=True)

    policy_version = settings.parent_consent_policy_version.strip()
    policy_text = settings.parent_consent_policy_text.strip()
    if not policy_version or not policy_text:
        print("local_parent_seed_profile=skipped reason=local_demo_policy_missing", flush=True)
        return

    profile_id = _stable_id(f"sketch2life:local-demo:parent-profile:{settings.firebase_project_id}:{subject}")
    if session.get(ParentChildProfileModel, profile_id) is not None:
        print("local_parent_seed_profile=existing", flush=True)
        return

    existing_profile = session.scalar(
        select(ParentChildProfileModel.parent_profile_id)
        .where(
            ParentChildProfileModel.owner_subject == subject,
            ParentChildProfileModel.state != "DELETED",
        )
        .limit(1)
    )
    if existing_profile is not None:
        print("local_parent_seed_profile=skipped reason=parent_already_has_profile", flush=True)
        return

    revision_id = _stable_id(f"{profile_id}:revision:1")
    authorization_id = _stable_id(f"{profile_id}:authorization:{policy_version}")
    revision_input = ParentProfileRevisionInput(
        age_months=84,
        display_name="Trẻ thử nghiệm",
        interests_summary="Thiên nhiên, côn trùng, màu sắc",
    )
    revision_hash = profile_revision_sha256(revision_input)
    evidence_hash = hashlib.sha256(
        b"Synthetic local demo authorization only; not legal consent."
    ).hexdigest()
    now = datetime.now(UTC)
    profile = ParentChildProfileModel(
        parent_profile_id=profile_id,
        owner_subject=subject,
        state="ACTIVE",
        current_revision_ref=None,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.flush()
    session.add(
        ParentProfileRevisionModel(
            profile_revision_id=revision_id,
            parent_profile_id=profile_id,
            revision_no=1,
            age_months=revision_input.age_months,
            age_band_ref="age-72-107-months-v1",
            age_band_version="1",
            display_name=revision_input.display_name,
            interests_summary=revision_input.interests_summary,
            authored_by=subject,
            revision_hash=revision_hash,
            created_at=now,
        )
    )
    session.flush()
    profile.current_revision_ref = revision_id
    session.add(
        ParentDataAuthorizationModel(
            authorization_id=authorization_id,
            parent_profile_id=profile_id,
            actor_subject=subject,
            purpose_code="PARENT_STORY_PERSONALIZATION",
            policy_version=policy_version,
            state="GRANTED",
            source_kind="SYNTHETIC_DEV",
            recorded_at=now,
            evidence_ref=evidence_hash,
            synthetic_demo_flag=True,
        )
    )
    session.flush()
    print("local_parent_seed_profile=created synthetic_authorization=true", flush=True)


def _ensure_public_lesson(session: Session) -> None:
    content = _lesson_content()
    validate_content(content)
    lesson_id = _stable_id(_LESSON_NAMESPACE)
    version_id = _stable_id(f"{_LESSON_NAMESPACE}:version:1")
    grant_id = _stable_id(f"{_LESSON_NAMESPACE}:public-view-grant:v1")
    now = datetime.now(UTC)

    existing_seed = session.execute(
        select(LIBRARY_ITEMS.c.lesson_id).where(
            LIBRARY_ITEMS.c.created_by == _SEED_ACTOR,
            LIBRARY_ITEMS.c.lesson_id != lesson_id,
        )
    ).first()
    if existing_seed is not None:
        raise RuntimeError("LOCAL_PARENT_SEED_LESSON_DUPLICATE_KEY_CONFLICT")

    item = session.execute(
        select(LIBRARY_ITEMS).where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
    ).mappings().one_or_none()
    expected_hash = canonical_content_hash(content)
    if item is None:
        session.execute(
            LIBRARY_ITEMS.insert().values(
                lesson_id=lesson_id,
                organization_id=_SEED_ORGANIZATION,
                owner_kind="ORGANIZATION",
                created_by=_SEED_ACTOR,
                state="ACTIVE",
                visibility="PUBLIC",
                internal_visibility="SCHOOL",
                moderation_state="VISIBLE",
                current_version_id=version_id,
                revision=1,
                created_at=now,
                updated_at=now,
            )
        )
        print("local_parent_seed_lesson=created", flush=True)
    elif (
        item["created_by"] != _SEED_ACTOR
        or item["current_version_id"] != version_id
        or item["state"] != "ACTIVE"
        or item["visibility"] != "PUBLIC"
    ):
        raise RuntimeError("LOCAL_PARENT_SEED_LESSON_CONFLICT")
    else:
        print("local_parent_seed_lesson=existing", flush=True)

    version = session.execute(
        select(LIBRARY_VERSIONS).where(LIBRARY_VERSIONS.c.version_id == version_id)
    ).mappings().one_or_none()
    if version is None:
        session.execute(
            LIBRARY_VERSIONS.insert().values(
                version_id=version_id,
                lesson_id=lesson_id,
                version_no=1,
                content_json={key: value for key, value in content.items() if key != "activities"},
                structured_content_hash=expected_hash,
                review_state="APPROVED",
                source_document_revision_id=None,
                authored_by=_SEED_ACTOR,
                created_at=now,
                approved_at=now,
            )
        )
    elif (
        version["lesson_id"] != lesson_id
        or version["structured_content_hash"] != expected_hash
        or version["review_state"] != "APPROVED"
    ):
        raise RuntimeError("LOCAL_PARENT_SEED_LESSON_VERSION_CONFLICT")

    for order, activity in enumerate(content["activities"], start=1):
        activity_id = _stable_id(f"{_LESSON_NAMESPACE}:activity:{order}")
        existing_activity = session.execute(
            select(VERSION_ACTIVITIES).where(
                (VERSION_ACTIVITIES.c.activity_id == activity_id)
                | (
                    (VERSION_ACTIVITIES.c.version_id == version_id)
                    & (VERSION_ACTIVITIES.c.activity_order == order)
                )
            )
        ).mappings().one_or_none()
        if existing_activity is None:
            session.execute(
                VERSION_ACTIVITIES.insert().values(
                    activity_id=activity_id,
                    version_id=version_id,
                    activity_order=order,
                    activity_json=activity,
                )
            )
        elif (
            existing_activity["version_id"] != version_id
            or existing_activity["activity_order"] != order
            or existing_activity["activity_json"] != activity
        ):
            raise RuntimeError("LOCAL_PARENT_SEED_ACTIVITY_CONFLICT")

    grant = session.execute(
        select(ACCESS_GRANTS).where(ACCESS_GRANTS.c.access_grant_id == grant_id)
    ).mappings().one_or_none()
    if grant is None:
        grant = session.execute(
            select(ACCESS_GRANTS).where(
                ACCESS_GRANTS.c.lesson_id == lesson_id,
                ACCESS_GRANTS.c.version_id == version_id,
                ACCESS_GRANTS.c.audience_kind == "PUBLIC",
                ACCESS_GRANTS.c.audience_ref.is_(None),
                ACCESS_GRANTS.c.capability == "VIEW",
                ACCESS_GRANTS.c.state == "ACTIVE",
            )
        ).mappings().one_or_none()
    if grant is None:
        session.execute(
            ACCESS_GRANTS.insert().values(
                access_grant_id=grant_id,
                lesson_id=lesson_id,
                version_id=version_id,
                organization_id=_SEED_ORGANIZATION,
                audience_kind="PUBLIC",
                audience_ref=None,
                capability="VIEW",
                state="ACTIVE",
                granted_by=_SEED_ACTOR,
                approved_by=_SEED_ACTOR,
                approved_at=now,
                decision_reason="Approved synthetic local development catalog record",
                expires_at=None,
                revoked_at=None,
                revision=1,
                created_at=now,
            )
        )
    elif (
        grant["lesson_id"] != lesson_id
        or grant["version_id"] != version_id
        or grant["audience_kind"] != "PUBLIC"
        or grant["capability"] != "VIEW"
        or grant["state"] != "ACTIVE"
    ):
        raise RuntimeError("LOCAL_PARENT_SEED_PUBLIC_GRANT_CONFLICT")


def seed_parent_demo(settings: Settings | None = None) -> None:
    configured = settings or get_settings()
    if configured.env != "local":
        raise RuntimeError("LOCAL_PARENT_SEED_IS_LOCAL_ONLY")

    subject = _seed_firebase_parent(configured)
    engine = create_core_engine()
    sessions = create_core_session_factory(engine)
    try:
        with sessions.begin() as session:
            if subject:
                _ensure_parent_identity_and_profile(
                    session, subject=subject, settings=configured
                )
            _ensure_public_lesson(session)
        print("local_parent_seed=complete", flush=True)
    finally:
        engine.dispose()


def main() -> None:
    seed_parent_demo()


if __name__ == "__main__":
    main()


__all__ = ["main", "seed_parent_demo"]
