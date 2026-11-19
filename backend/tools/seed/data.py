"""Pure S1 seed data (FEAT-066 SEED-1, package §3.2 to §3.5; design §4.1).

Synthetic data only. Nothing here touches a database or reads settings. Stable text IDs
start with ``seed-`` and stay within 36 characters; display names start with ``[SEED]``;
UUID columns use UUIDv5 from one fixed namespace.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sketch2life.domain.lesson_library.model import canonical_content_hash
from sketch2life.domain.parent_profiles import ProfileSnapshot

SEED_NAMESPACE = uuid.UUID("6f1c3c2e-6a51-5d0e-9a43-2b6c1f0e5a17")
SEED_ISSUER = "urn:sketch2life:seed:issuer"
SEED_TIME = datetime(2026, 11, 18, 0, 0, tzinfo=UTC)
MEMBERSHIP_EXPIRES_AT = datetime(2030, 1, 1, 0, 0, tzinfo=UTC)
PLACEHOLDER_AGE_BAND_REF = "seed-age-band-placeholder"
PARENT_CONTEXT_SCHEMA = "sketch2life.parent-context.v1"
FAILED_RUN_ERROR_CODE = "SEED_SYNTHETIC_FAILURE"
CLASS_PROFILE_AGES = (36, 54, 78, 96, 120)

ORGANIZATION_KEYS = ("a", "b", "c", "d", "e", "f", "g", "h")
CLASS_COUNTS = {"a": 4, "b": 1, "c": 10, "d": 10, "e": 10, "f": 2, "g": 2, "h": 2}
ORG_A_PROFILES_PER_CLASS = (5, 4, 3, 3)


def seed_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


def seed_uuid_text(key: str) -> str:
    return str(seed_uuid(key))


def canonical_json(value: Any) -> str:
    """Same encoding as the Parent StoryRun repository's canonical JSON."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def principal_scope_ref(issuer: str, subject: str) -> str:
    """Re-derivation of ``_principal_scope_ref`` (parent_story_repository.py)."""

    return sha256_json({"issuer": issuer, "subject": subject})


def derive_visibility(internal_visibility: str, grants: list[dict[str, Any]], now: datetime) -> str:
    """Pure re-derivation of ``LessonLibraryService._recalculate_visibility``."""

    kinds = {
        grant["audience_kind"]
        for grant in grants
        if grant["state"] == "ACTIVE" and (grant["expires_at"] is None or grant["expires_at"] > now)
    }
    if "PUBLIC" in kinds:
        return "PUBLIC"
    if kinds.intersection({"PRINCIPAL", "PARENT_GROUP"}):
        return "SELECTED_AUDIENCE"
    if "ORGANIZATION" in kinds:
        return "SCHOOL"
    return internal_visibility


# --- Adults -----------------------------------------------------------------------------


def org_id(key: str) -> str:
    return f"seed-org-{key}"


def manager_subject(key: str) -> str:
    return f"seed-mgr-{key}"


def class_id(key: str, number: int) -> str:
    return f"seed-org-{key}-class-{number}"


PLATFORM_ADMIN_SUBJECT = "seed-admin"
ORG_A_TEACHERS = ("seed-tch-a1", "seed-tch-a2", "seed-tch-a3")
NO_ORG_TEACHER_SUBJECT = "seed-tch-noorg"
PARENT_SUBJECTS = {
    "p1": "seed-parent-p1",
    "p2": "seed-parent-p2",
    "p3": "seed-parent-p3",
    "p4": "seed-parent-p4",
    "p5": "seed-parent-p5",
}


def teacher_subject(key: str) -> str:
    return f"seed-tch-{key}"


def _adult(subject: str, role: str) -> dict[str, Any]:
    return {
        "subject": subject,
        "account_id": seed_uuid_text(f"adult:{subject}"),
        "issuer": SEED_ISSUER,
        "state": "active",
        "account_role": role,
        "role_revision": 1,
    }


def adult_rows() -> list[dict[str, Any]]:
    rows = [_adult(PLATFORM_ADMIN_SUBJECT, "platform_admin")]
    rows += [_adult(manager_subject(key), "school_manager") for key in ORGANIZATION_KEYS]
    rows += [_adult(subject, "teacher") for subject in ORG_A_TEACHERS]
    rows += [_adult(teacher_subject(key), "teacher") for key in ORGANIZATION_KEYS[1:]]
    rows.append(_adult(NO_ORG_TEACHER_SUBJECT, "teacher"))
    rows += [_adult(subject, "parent") for subject in PARENT_SUBJECTS.values()]
    return rows


def parent_account_id(parent_key: str) -> str:
    return seed_uuid_text(f"adult:{PARENT_SUBJECTS[parent_key]}")


# --- Organizations, classes, assignments ----------------------------------------------


def organization_rows() -> list[dict[str, Any]]:
    return [
        {
            "organization_id": org_id(key),
            "display_name": f"[SEED] Trường {key.upper()}",
            "state": "active",
        }
        for key in ORGANIZATION_KEYS
    ]


def classroom_rows() -> list[dict[str, Any]]:
    rows = []
    for key in ORGANIZATION_KEYS:
        for number in range(1, CLASS_COUNTS[key] + 1):
            rows.append(
                {
                    "class_id": class_id(key, number),
                    "organization_id": org_id(key),
                    "display_name": f"[SEED] Lớp {key.upper()}{number}",
                    "state": "active",
                    "created_by": manager_subject(key),
                }
            )
    return rows


def _assignment(key: str, subject: str, role: str, klass: str | None) -> dict[str, Any]:
    return {
        "assignment_id": seed_uuid_text(f"assignment:{key}:{subject}:{klass}:{role}"),
        "organization_id": org_id(key),
        "subject": subject,
        "class_id": klass,
        "role": role,
        "active": True,
    }


def assignment_rows() -> list[dict[str, Any]]:
    rows = [
        _assignment(key, manager_subject(key), "school_admin", None) for key in ORGANIZATION_KEYS
    ]
    # Org A: two class-scoped Teachers; class 4 has no Teacher; the third Teacher is an
    # organization member with no class (the MGR-3 candidate case).
    rows.append(_assignment("a", ORG_A_TEACHERS[0], "teacher", class_id("a", 1)))
    rows.append(_assignment("a", ORG_A_TEACHERS[1], "teacher", class_id("a", 2)))
    rows.append(_assignment("a", ORG_A_TEACHERS[0], "teacher", class_id("a", 3)))
    rows.append(_assignment("a", ORG_A_TEACHERS[2], "teacher", None))
    rows += [
        _assignment(key, teacher_subject(key), "teacher", class_id(key, 1))
        for key in ORGANIZATION_KEYS[1:]
    ]
    return rows


# --- Class profiles and enrollments ---------------------------------------------------


def managed_profile_rows() -> list[dict[str, Any]]:
    rows = []
    for key in ORGANIZATION_KEYS:
        for number in range(1, CLASS_COUNTS[key] + 1):
            count = ORG_A_PROFILES_PER_CLASS[number - 1] if key == "a" else 1
            for index in range(1, count + 1):
                rows.append(
                    {
                        "child_id": f"seed-ch-{key}-{number}-{index}",
                        "organization_id": org_id(key),
                        "class_id": class_id(key, number),
                        "display_name": f"[SEED] Bé {key.upper()}{number}-{index}",
                        "age_months": CLASS_PROFILE_AGES[(index - 1) % len(CLASS_PROFILE_AGES)],
                        "age_revision": 1,
                        "age_source": "SYNTHETIC_FIXTURE",
                        "consent_id": None,
                        "consent_purpose_ref": None,
                        "data_origin": "SYNTHETIC_DEV",
                        "state": "active",
                        "created_by": manager_subject(key),
                    }
                )
    return rows


def enrollment_rows() -> list[dict[str, Any]]:
    return [
        {
            "enrollment_id": seed_uuid_text(f"enrollment:{profile['child_id']}"),
            "organization_id": profile["organization_id"],
            "class_id": profile["class_id"],
            "child_id": profile["child_id"],
            "state": "active",
            "created_by": profile["created_by"],
        }
        for profile in managed_profile_rows()
    ]


# --- Parent groups ---------------------------------------------------------------------

PARENT_GROUP_IDS = ("seed-pg-a-1", "seed-pg-a-2")


def parent_group_rows() -> list[dict[str, Any]]:
    return [
        {
            "parent_group_id": group_id,
            "organization_id": org_id("a"),
            "display_name": f"[SEED] Nhóm phụ huynh {number}",
            "state": "active",
            "created_by": manager_subject("a"),
        }
        for number, group_id in enumerate(PARENT_GROUP_IDS, start=1)
    ]


def parent_group_member_rows() -> list[dict[str, Any]]:
    specs = (
        (PARENT_GROUP_IDS[0], "p1", "active"),
        (PARENT_GROUP_IDS[0], "p2", "revoked"),
        (PARENT_GROUP_IDS[1], "p3", "active"),
    )
    return [
        {
            "membership_id": f"seed-pgm-{group_id[-1]}-{parent_key}",
            "parent_group_id": group_id,
            "parent_principal_ref": PARENT_SUBJECTS[parent_key],
            "state": state,
            "invited_by": manager_subject("a"),
            "invited_at": SEED_TIME,
            "expires_at": MEMBERSHIP_EXPIRES_AT,
            "accepted_at": SEED_TIME,
            "revision": 1 if state == "active" else 2,
        }
        for group_id, parent_key, state in specs
    ]


# --- Parent profiles -------------------------------------------------------------------

# (profile key, parent key, state, revisions as (display name, age, interests))
PARENT_PROFILE_SPECS: tuple[tuple[str, str, str, tuple[tuple[str, int, str | None], ...]], ...] = (
    (
        "k1",
        "p1",
        "ACTIVE",
        (("[SEED] K1", 60, "Thích vẽ con vật"), ("[SEED] K1", 61, "Thích vẽ con vật và cây")),
    ),
    ("k2", "p1", "DELETE_PENDING", (("[SEED] K2", 48, None),)),
    (
        "k3",
        "p2",
        "ACTIVE",
        (("[SEED] K3", 84, "Thích vẽ xe"), ("[SEED] K3", 85, "Thích vẽ xe và tàu")),
    ),
    ("k4", "p4", "ACTIVE", (("[SEED] K4", 72, "Thích vẽ chim"),)),
    ("k5", "p5", "ACTIVE", (("[SEED] K5", 96, "Thích vẽ nhà"),)),
)


def parent_profile_id(profile_key: str) -> uuid.UUID:
    return seed_uuid(f"parent-profile:{profile_key}")


def profile_revision_id(profile_key: str, revision_no: int) -> uuid.UUID:
    return seed_uuid(f"parent-profile-revision:{profile_key}:{revision_no}")


def child_profile_rows() -> list[dict[str, Any]]:
    return [
        {
            "parent_profile_id": parent_profile_id(profile_key),
            "owner_issuer": SEED_ISSUER,
            "owner_subject": PARENT_SUBJECTS[parent_key],
            "state": state,
            "current_revision_no": len(revisions),
            "data_origin": "SYNTHETIC_DEV",
        }
        for profile_key, parent_key, state, revisions in PARENT_PROFILE_SPECS
    ]


def profile_revision_rows() -> list[dict[str, Any]]:
    rows = []
    for profile_key, parent_key, _state, revisions in PARENT_PROFILE_SPECS:
        for revision_no, (display_name, age_months, interests) in enumerate(revisions, start=1):
            snapshot = ProfileSnapshot(
                display_name=display_name, age_months=age_months, interests_summary=interests
            )
            rows.append(
                {
                    "profile_revision_id": profile_revision_id(profile_key, revision_no),
                    "parent_profile_id": parent_profile_id(profile_key),
                    "revision_no": revision_no,
                    "age_months": age_months,
                    "age_band_ref": None,
                    "age_band_version": None,
                    "display_name": display_name,
                    "interests_summary": interests,
                    "authored_by_issuer": SEED_ISSUER,
                    "authored_by_subject": PARENT_SUBJECTS[parent_key],
                    "revision_hash": snapshot.revision_hash(),
                }
            )
    return rows


def current_profile_revision(profile_key: str) -> dict[str, Any]:
    revisions = [
        row
        for row in profile_revision_rows()
        if row["parent_profile_id"] == parent_profile_id(profile_key)
    ]
    return max(revisions, key=lambda row: row["revision_no"])


# --- Lessons and grants ----------------------------------------------------------------


def _activity(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "objective": f"Mục tiêu: {title}",
        "materials_text": "Giấy, bút sáp màu",
        "preparation_text": "",
        "instructions_text": f"Hướng dẫn trẻ thực hiện: {title}",
        "observation_notes": "",
        "safety_notes": "",
        "activity_kind": "indoor",
    }


def lesson_content(title: str, topic: str, drawing_subject: str) -> dict[str, Any]:
    return {
        "locale": "vi-VN",
        "title": title,
        "topic": topic,
        "target_age_band_ref": PLACEHOLDER_AGE_BAND_REF,
        "target_age_band_version": 1,
        "objectives": [f"Trẻ vẽ được {drawing_subject}"],
        "drawing_subject": drawing_subject,
        "drawing_steps_text": f"Bước 1: vẽ hình dạng chính của {drawing_subject}. Bước 2: tô màu.",
        "subject_learning_notes": f"Ghi chú tổng hợp về {drawing_subject} (dữ liệu tổng hợp).",
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            _activity(f"Quan sát {drawing_subject}"),
            _activity(f"Vẽ {drawing_subject}"),
        ],
    }


# (lesson key, internal visibility, item revision, versions as (version no, review state, content))
LESSON_SPECS: tuple[tuple[str, str, int, tuple[tuple[int, str, dict[str, Any]], ...]], ...] = (
    (
        "l1",
        "PRIVATE",
        2,
        (
            (1, "APPROVED", lesson_content("[SEED] Bài 1 (bản 1)", "Con mèo", "con mèo")),
            (2, "APPROVED", lesson_content("[SEED] Bài 1 (bản 2)", "Con mèo", "con mèo ngồi")),
        ),
    ),
    ("l2", "PRIVATE", 1, ((1, "APPROVED", lesson_content("[SEED] Bài 2", "Cái cây", "cái cây")),)),
    (
        "l3",
        "SCHOOL",
        1,
        ((1, "PENDING_REVIEW", lesson_content("[SEED] Bài 3", "Ngôi nhà", "ngôi nhà")),),
    ),
)
LESSON_AUTHOR = ORG_A_TEACHERS[0]


def lesson_id(key: str) -> str:
    return f"seed-lesson-{key}"


def version_id(key: str, number: int) -> str:
    return f"seed-lv-{key}-{number}"


def access_grant_rows() -> list[dict[str, Any]]:
    manager = manager_subject("a")
    base = {"organization_id": org_id("a"), "granted_by": LESSON_AUTHOR, "expires_at": None}
    return [
        {
            **base,
            "access_grant_id": "seed-gr-1",
            "lesson_id": lesson_id("l1"),
            "version_id": version_id("l1", 2),
            "audience_kind": "ORGANIZATION",
            "audience_ref": org_id("a"),
            "capability": "VIEW",
            "state": "ACTIVE",
            "approved_by": manager,
            "approved_at": SEED_TIME,
            "revoked_at": None,
            "revision": 2,
        },
        {
            **base,
            "access_grant_id": "seed-gr-2",
            "lesson_id": lesson_id("l1"),
            "version_id": version_id("l1", 1),
            "audience_kind": "PARENT_GROUP",
            "audience_ref": PARENT_GROUP_IDS[0],
            "capability": "VIEW",
            "state": "PENDING_REVIEW",
            "approved_by": None,
            "approved_at": None,
            "revoked_at": None,
            "revision": 1,
        },
        {
            **base,
            "access_grant_id": "seed-gr-3",
            "lesson_id": lesson_id("l2"),
            "version_id": version_id("l2", 1),
            "audience_kind": "PRINCIPAL",
            "audience_ref": PARENT_SUBJECTS["p1"],
            "capability": "DOWNLOAD",
            "state": "REVOKED",
            "approved_by": manager,
            "approved_at": SEED_TIME,
            "revoked_at": SEED_TIME,
            "revision": 2,
        },
        {
            **base,
            "access_grant_id": "seed-gr-4",
            "lesson_id": lesson_id("l3"),
            "version_id": version_id("l3", 1),
            "audience_kind": "PUBLIC",
            "audience_ref": None,
            "capability": "VIEW",
            "state": "PENDING_REVIEW",
            "approved_by": None,
            "approved_at": None,
            "revoked_at": None,
            "revision": 1,
        },
    ]


EXPECTED_VISIBILITY = {"l1": "SCHOOL", "l2": "PRIVATE", "l3": "SCHOOL"}


def library_item_rows() -> list[dict[str, Any]]:
    grants = access_grant_rows()
    rows = []
    for key, internal_visibility, revision, versions in LESSON_SPECS:
        lesson_grants = [grant for grant in grants if grant["lesson_id"] == lesson_id(key)]
        rows.append(
            {
                "lesson_id": lesson_id(key),
                "organization_id": org_id("a"),
                "owner_kind": "ORGANIZATION",
                "created_by": LESSON_AUTHOR,
                "state": "ACTIVE",
                "visibility": derive_visibility(internal_visibility, lesson_grants, SEED_TIME),
                "internal_visibility": internal_visibility,
                "moderation_state": "VISIBLE",
                "current_version_id": version_id(key, max(number for number, _, _ in versions)),
                "revision": revision,
            }
        )
    return rows


def library_version_rows() -> list[dict[str, Any]]:
    rows = []
    for key, _internal, _revision, versions in LESSON_SPECS:
        for number, review_state, content in versions:
            rows.append(
                {
                    "version_id": version_id(key, number),
                    "lesson_id": lesson_id(key),
                    "version_no": number,
                    # Stored as the product writer stores it (service.py _insert_version).
                    "content_json": {k: v for k, v in content.items() if k != "activities"},
                    "structured_content_hash": canonical_content_hash(content),
                    "review_state": review_state,
                    "source_document_revision_id": None,
                    "authored_by": LESSON_AUTHOR,
                    "approved_at": SEED_TIME if review_state == "APPROVED" else None,
                }
            )
    return rows


def version_activity_rows() -> list[dict[str, Any]]:
    rows = []
    for key, _internal, _revision, versions in LESSON_SPECS:
        for number, _state, content in versions:
            for order, activity in enumerate(content["activities"], start=1):
                rows.append(
                    {
                        "activity_id": f"seed-la-{key}-{number}-{order}",
                        "version_id": version_id(key, number),
                        "activity_order": order,
                        "activity_json": activity,
                    }
                )
    return rows


# --- StoryRuns -------------------------------------------------------------------------

# (run key, parent key, profile key, run state, active?, topic, typed idea)
STORY_RUN_SPECS: tuple[tuple[str, str, str, str, bool, str, str | None], ...] = (
    ("r1", "p1", "k1", "COMPLETED", False, "Con mèo", "Con mèo đi dạo"),
    ("r2", "p1", "k1", "FAILED", False, "Cái cây", None),
    ("r3", "p1", "k1", "DELETE_PENDING", False, "Ngôi nhà", None),
    ("r4", "p1", "k1", "INPUT_PROCESSING", True, "Con cá", "Con cá bơi"),
    ("r5", "p2", "k3", "COMPLETED", False, "Chiếc xe", None),
    ("r6", "p2", "k3", "PREPARATION_REVIEW", True, "Tàu hoả", "Tàu hoả chạy"),
)


def run_id(key: str) -> str:
    return seed_uuid_text(f"story-run:{key}")


def _context(profile_key: str, topic: str, idea: str | None) -> dict[str, Any]:
    revision = current_profile_revision(profile_key)
    return {
        "schema_version": PARENT_CONTEXT_SCHEMA,
        "profile_revision_ref": str(revision["profile_revision_id"]),
        "age_months": revision["age_months"],
        "interests_summary": revision["interests_summary"] or "",
        "topic": topic,
        "adult_confirmed_idea": idea or "",
    }


def story_run_rows() -> list[dict[str, Any]]:
    rows = []
    for key, parent_key, profile_key, state, active, _topic, _idea in STORY_RUN_SPECS:
        rows.append(
            {
                "run_id": run_id(key),
                "actor_scope_kind": "PARENT_ACCOUNT",
                "actor_scope_ref": principal_scope_ref(SEED_ISSUER, PARENT_SUBJECTS[parent_key]),
                "profile_ref": str(parent_profile_id(profile_key)),
                "child_age_months": current_profile_revision(profile_key)["age_months"],
                "run_state": state,
                "revision": 1,
                "version": 1,
                "retryable": False,
                "job_state": "FAILED" if state == "FAILED" else None,
                "error_code": FAILED_RUN_ERROR_CODE if state == "FAILED" else None,
                "active_owner_parent_account_id": parent_account_id(parent_key) if active else None,
                "current_input_revision": 1,
            }
        )
    return rows


def run_input_rows() -> list[dict[str, Any]]:
    rows = []
    for key, _parent_key, profile_key, _state, _active, topic, idea in STORY_RUN_SPECS:
        context = _context(profile_key, topic, idea)
        rows.append(
            {
                "run_input_id": seed_uuid_text(f"story-run-input:{key}:1"),
                "run_id": run_id(key),
                "input_revision": 1,
                "typed_idea": idea,
                "idea_source": "TEXT" if idea else None,
                "source_profile_revision_ref": context["profile_revision_ref"],
                "context_revision": 1,
                "context_snapshot": context,
                "context_snapshot_sha256": sha256_json(context),
                "context_confirmed_by": None,
                "context_confirmed_at": None,
            }
        )
    return rows


# --- Expected counts -------------------------------------------------------------------


def expected_counts() -> dict[str, int]:
    return {
        "be1_organizations": len(organization_rows()),
        "be1_adult_identities": len(adult_rows()),
        "be1_organization_assignments": len(assignment_rows()),
        "be1_classrooms": len(classroom_rows()),
        "be1_managed_profiles": len(managed_profile_rows()),
        "be1_enrollments": len(enrollment_rows()),
        "be1_parent_groups": len(parent_group_rows()),
        "be1_parent_group_members": len(parent_group_member_rows()),
        "parent.child_profiles": len(child_profile_rows()),
        "parent.profile_revisions": len(profile_revision_rows()),
        "lesson.library_items": len(library_item_rows()),
        "lesson.library_versions": len(library_version_rows()),
        "lesson.version_activities": len(version_activity_rows()),
        "lesson.access_grants": len(access_grant_rows()),
        "story.runs": len(story_run_rows()),
        "story.run_inputs": len(run_input_rows()),
    }


EXPECTED_COUNTS: dict[str, int] = {
    "be1_organizations": 8,
    "be1_adult_identities": 25,
    "be1_organization_assignments": 19,
    "be1_classrooms": 41,
    "be1_managed_profiles": 52,
    "be1_enrollments": 52,
    "be1_parent_groups": 2,
    "be1_parent_group_members": 3,
    "parent.child_profiles": 5,
    "parent.profile_revisions": 7,
    "lesson.library_items": 3,
    "lesson.library_versions": 4,
    "lesson.version_activities": 8,
    "lesson.access_grants": 4,
    "story.runs": 6,
    "story.run_inputs": 6,
}


# --- SEED-7a: command-made Parent runs (S7 item 2a) -------------------------------------

# (parent key, profile key, topic, adult-confirmed idea). The values are synthetic; the
# lengths stay inside the service limits (topic at most 120, idea at most 500 characters).
S7A_RUN_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("p4", "k4", "[SEED] Chim trên cành", "Bé muốn vẽ một chú chim đậu trên cành cây."),
    ("p5", "k5", "[SEED] Ngôi nhà của em", "Bé muốn vẽ ngôi nhà có mái đỏ và một khu vườn nhỏ."),
)

# Rows that S7a run 1 adds, counted through the seeded Parent principals and the run FK.
EXPECTED_S7A_COUNTS: dict[str, int] = {
    "story.runs": 2,
    "story.run_inputs": 2,
    "story.command_receipts": 4,
}


def s7a_create_key(parent_key: str) -> str:
    return f"seed:s7a:{parent_key}:create-1"


def s7a_confirm_key(parent_key: str) -> str:
    return f"seed:s7a:{parent_key}:confirm-1"
