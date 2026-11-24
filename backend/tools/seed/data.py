"""Pure S1 seed data (FEAT-066 SEED-1, package §3.2 to §3.5; design §4.1).

Synthetic data only. Nothing here touches a database or reads settings. Stable text IDs
keep the ``seed-`` prefix and stay within 36 characters; UUID columns use UUIDv5 from one
fixed namespace.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sketch2life.domain.be1_profile_revisions import (
    BAND_VERSION,
    HASH_VERSION,
    age_band,
    baseline_revision_id,
    revision_hash,
)
from sketch2life.domain.lesson_library.model import canonical_content_hash
from sketch2life.domain.parent_profiles import ProfileSnapshot

SEED_NAMESPACE = uuid.UUID("6f1c3c2e-6a51-5d0e-9a43-2b6c1f0e5a17")
SEED_ISSUER = "urn:sketch2life:seed:issuer"
SEED_TIME = datetime(2026, 11, 18, 0, 0, tzinfo=UTC)
MEMBERSHIP_EXPIRES_AT = datetime(2030, 1, 1, 0, 0, tzinfo=UTC)
PLACEHOLDER_AGE_BAND_REF = "seed-age-band-placeholder"
PARENT_CONTEXT_SCHEMA = "sketch2life.parent-context.v1"
FAILED_RUN_ERROR_CODE = "SEED_SYNTHETIC_FAILURE"
CLASS_PROFILE_AGE_RANGES = {"mam": (36, 47), "choi": (48, 59), "la": (60, 71)}
_CLASS_AGE_LABELS = {"mam": "Mầm", "choi": "Chồi", "la": "Lá"}
_CLASS_AGE_GROUPS = ("mam", "choi", "la")
_FAMILY_NAMES = (
    "Nguyễn",
    "Trần",
    "Lê",
    "Phạm",
    "Hoàng",
    "Huỳnh",
    "Phan",
    "Vũ",
    "Võ",
    "Đặng",
    "Bùi",
    "Đỗ",
    "Hồ",
    "Ngô",
    "Dương",
    "Lý",
    "Đinh",
    "Trịnh",
    "Lâm",
    "Mai",
)
_FEMALE_MIDDLE_NAMES = ("Ngọc", "Bảo", "Minh", "Khánh", "Gia", "Thùy", "Phương", "Diệu")
_MALE_MIDDLE_NAMES = ("Minh", "Gia", "Bảo", "Đức", "Hữu", "Quang", "Anh", "Tuấn")
_FEMALE_GIVEN_NAMES = (
    "An",
    "Chi",
    "Hà",
    "Hân",
    "Khuê",
    "Lan",
    "Mai",
    "Vy",
    "Linh",
    "Nhi",
    "Trang",
    "Thảo",
    "Uyên",
    "Anh",
    "My",
    "Ngân",
)
_MALE_GIVEN_NAMES = (
    "Bảo",
    "Duy",
    "Khang",
    "Long",
    "Nam",
    "Phúc",
    "Quân",
    "Huy",
    "Khôi",
    "Kiệt",
    "Hiếu",
    "Đạt",
    "Thịnh",
    "Nghĩa",
    "Sơn",
    "Tín",
)

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


def class_age_group(key: str, number: int) -> str:
    """Return the seed age group for one class number."""
    if key not in ORGANIZATION_KEYS or number < 1:
        raise ValueError("unknown organization or class number")
    if key == "a" and number <= 4:
        return ("mam", "choi", "la", "la")[number - 1]
    offset = number - 5 if key == "a" else number - 1
    return _CLASS_AGE_GROUPS[offset % len(_CLASS_AGE_GROUPS)]


def class_display_name(key: str, number: int) -> str:
    """Name a class by age group, with its ordinal inside that group."""
    group = class_age_group(key, number)
    ordinal = sum(class_age_group(key, n) == group for n in range(1, number + 1))
    return f"Lớp {_CLASS_AGE_LABELS[group]} {ordinal}"


def managed_child_display_name(child_id: str) -> str:
    """Generate a stable fictional full name from a seed managed-profile id."""
    parts = child_id.split("-")
    try:
        org_index = ORGANIZATION_KEYS.index(parts[2])
        class_number = int(parts[3])
        child_number = int(parts[4])
    except (IndexError, ValueError):
        slot = int.from_bytes(hashlib.sha256(child_id.encode("utf-8")).digest()[:2], "big") % 640
    else:
        if parts[:2] != ["seed", "ch"] or not 1 <= class_number <= 10 or not 1 <= child_number <= 8:
            raise ValueError("managed child id is outside the seed name space")
        slot = org_index * 80 + (class_number - 1) * 8 + child_number - 1
    gender = slot % 2
    ordinal = slot // 2
    # (family, block) is recoverable from (family, given), so every slot gets a distinct name.
    block, family_index = divmod(ordinal, len(_FAMILY_NAMES))
    family = _FAMILY_NAMES[family_index]
    middle_names = _FEMALE_MIDDLE_NAMES if gender == 0 else _MALE_MIDDLE_NAMES
    given_names = _FEMALE_GIVEN_NAMES if gender == 0 else _MALE_GIVEN_NAMES
    given = given_names[(5 * family_index + 3 * block) % len(given_names)]
    middle = middle_names[(family_index + block) % len(middle_names)]
    if middle == given:
        middle = middle_names[(family_index + block + 1) % len(middle_names)]
    return f"{family} {middle} {given}"


def managed_profile_age(child_number: int, age_group: str, profiles_in_class: int) -> int:
    """Spread a class's synthetic ages evenly across its age-group range."""
    if age_group not in CLASS_PROFILE_AGE_RANGES or profiles_in_class < 1:
        raise ValueError("unknown age group or empty class")
    if not 1 <= child_number <= profiles_in_class:
        raise ValueError("child number is outside the class profile count")
    minimum, maximum = CLASS_PROFILE_AGE_RANGES[age_group]
    if profiles_in_class == 1:
        return minimum
    return round(minimum + (child_number - 1) * (maximum - minimum) / (profiles_in_class - 1))


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
    names = {
        "a": "Hoa Sen",
        "b": "Sao Mai",
        "c": "Hướng Dương",
        "d": "Họa Mi",
        "e": "Tuổi Thơ",
        "f": "Ánh Dương",
        "g": "Bình Minh",
        "h": "Vàng Anh",
    }
    return [
        {
            "organization_id": org_id(key),
            "display_name": f"Trường Mầm non {names[key]}",
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
                    "display_name": class_display_name(key, number),
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


def managed_profile_row(
    child_id: str,
    key: str,
    class_number: int,
    child_number: int,
    profiles_in_class: int,
    *,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Build one synthetic managed profile, also used for later stage-owned children."""
    group = class_age_group(key, class_number)
    return {
        "child_id": child_id,
        "organization_id": org_id(key),
        "class_id": class_id(key, class_number),
        "display_name": managed_child_display_name(child_id),
        "age_months": managed_profile_age(child_number, group, profiles_in_class),
        "age_revision": 1,
        "age_source": "SYNTHETIC_FIXTURE",
        "consent_id": None,
        "consent_purpose_ref": None,
        "data_origin": "SYNTHETIC_DEV",
        "state": "active",
        "created_by": created_by or manager_subject(key),
        # T-12b: the head of the baseline revision written by `baseline_revision_row`.
        "current_profile_revision_id": baseline_revision_id(child_id),
        "profile_revision_no": 1,
    }


def baseline_revision_row(profile: dict[str, Any]) -> dict[str, Any]:
    """Revision 1 of a seeded profile (T-12b): the profile's own name and age, no interests."""
    band = age_band(int(profile["age_months"]))
    return {
        "profile_revision_id": baseline_revision_id(str(profile["child_id"])),
        "child_id": profile["child_id"],
        "revision_no": 1,
        "display_name": profile["display_name"],
        "age_months": profile["age_months"],
        "age_band_version": None if band is None else BAND_VERSION,
        "age_band_code": None if band is None else band[1],
        "structured_interests": [],
        "authored_by": profile["created_by"],
        "revision_hash_version": HASH_VERSION,
        "revision_hash": revision_hash(
            child_id=str(profile["child_id"]),
            revision_no=1,
            display_name=str(profile["display_name"]),
            age_months=int(profile["age_months"]),
            structured_interests=[],
        ),
    }


def be1_profile_revision_rows() -> list[dict[str, Any]]:
    return [baseline_revision_row(profile) for profile in managed_profile_rows()]


def managed_profile_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ORGANIZATION_KEYS:
        for number in range(1, CLASS_COUNTS[key] + 1):
            count = ORG_A_PROFILES_PER_CLASS[number - 1] if key == "a" else 1
            rows.extend(
                managed_profile_row(f"seed-ch-{key}-{number}-{index}", key, number, index, count)
                for index in range(1, count + 1)
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
            "display_name": f"Phụ huynh lớp {'Mầm' if number == 1 else 'Chồi'} 1",
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
        (
            ("Mít", 60, "Mít thích vẽ những con vật bé gặp ở công viên."),
            ("Mít", 61, "Mít thích vẽ con vật và thêm cây cối để kể lại buổi đi chơi."),
        ),
    ),
    ("k2", "p1", "DELETE_PENDING", (("Bông", 48, None),)),
    (
        "k3",
        "p2",
        "ACTIVE",
        (
            ("Tí", 84, "Tí thích vẽ xe buýt nhiều màu."),
            ("Tí", 85, "Tí thích vẽ xe buýt và những chuyến tàu chạy xa."),
        ),
    ),
    ("k4", "p4", "ACTIVE", (("Na", 72, "Na thường chọn vẽ chim nhỏ đang đậu trên cành cây."),)),
    ("k5", "p5", "ACTIVE", (("Sóc", 96, "Sóc thích vẽ ngôi nhà có mái đỏ và một khu vườn nhỏ."),)),
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


def _activity(
    title: str,
    *,
    objective: str | None = None,
    materials_text: str | None = None,
    preparation_text: str | None = None,
    instructions_text: str | None = None,
    observation_notes: str | None = None,
    safety_notes: str | None = None,
    activity_kind: str = "indoor",
) -> dict[str, Any]:
    return {
        "title": title,
        "objective": objective or f"Trẻ quan sát {title.lower()} và chia sẻ điều mình nhận thấy.",
        "materials_text": materials_text or "Giấy, bút sáp màu cỡ lớn và tranh minh hoạ.",
        "preparation_text": preparation_text
        or "Chuẩn bị giấy, đặt màu trên bàn thấp và kiểm tra đồ dùng trước giờ học.",
        "instructions_text": instructions_text
        or (
            "1. Mời trẻ cùng quan sát tranh gợi ý.\n"
            "2. Hỏi trẻ muốn bắt đầu bằng hình dạng hoặc màu sắc nào.\n"
            "3. Khuyến khích trẻ tự hoàn thiện bức vẽ rồi kể một câu về ý tưởng của mình."
        ),
        "observation_notes": observation_notes
        or "Lắng nghe lời kể của trẻ và ghi nhận cách trẻ chọn hình, nét vẽ và màu sắc.",
        "safety_notes": safety_notes
        or "Dùng bút sáp cỡ lớn, nhắc trẻ không đưa đồ dùng lên miệng và cùng cất màu sau giờ học.",
        "activity_kind": activity_kind,
    }


def lesson_content(
    title: str,
    topic: str,
    drawing_subject: str,
    *,
    objectives: list[str] | None = None,
    drawing_steps_text: str | None = None,
    subject_learning_notes: str | None = None,
    activities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a complete Vietnamese lesson while preserving the original three arguments."""
    lesson_objectives = objectives or [
        f"Trẻ nhận ra những hình dạng chính tạo nên {drawing_subject}.",
        "Trẻ phối hợp nét vẽ và màu sắc để kể một ý tưởng của riêng mình.",
    ]
    steps = drawing_steps_text or (
        f"1. Cùng trẻ nhìn kỹ {drawing_subject} và gọi tên những phần dễ nhận ra.\n"
        "2. Mời trẻ vẽ hình lớn nhất bằng nét nhẹ.\n"
        "3. Thêm các chi tiết bằng nét đơn giản, không cần vẽ giống hệt mẫu.\n"
        "4. Chọn màu trẻ yêu thích và tô từng khoảng rộng.\n"
        "5. Mời trẻ kể một câu về bức tranh của mình."
    )
    notes = subject_learning_notes or (
        f"Hãy để trẻ quan sát {drawing_subject} bằng mắt và kể điều trẻ nhận thấy. "
        "Mỗi bức tranh có thể khác nhau vì trẻ được tự chọn chi tiết và màu sắc."
    )
    lesson_activities = activities or [
        _activity(
            f"Cùng quan sát {drawing_subject}",
            objective=f"Trẻ nhận ra một vài nét và hình dạng đặc trưng của {drawing_subject}.",
            materials_text="Tranh minh hoạ khổ lớn, giấy trắng và bút chì sáp màu.",
            preparation_text="Đặt tranh ở tầm mắt trẻ và chuẩn bị giấy, sáp màu trên bàn thấp.",
            instructions_text=(
                "1. Mời trẻ quan sát tranh trong yên lặng một lúc.\n"
                "2. Hỏi trẻ nhìn thấy bộ phận nào trước và bộ phận nào ở bên cạnh.\n"
                "3. Cho trẻ dùng ngón tay vẽ thử một đường trong không khí."
            ),
            observation_notes="Lắng nghe trẻ gọi tên hình dạng và mô tả vị trí các chi tiết.",
            safety_notes="Dùng tranh giấy có góc tù; nhắc trẻ không đưa bút màu lên miệng.",
            activity_kind="indoor",
        ),
        _activity(
            f"Vẽ {drawing_subject} theo cách của bé",
            objective=f"Trẻ sắp xếp các hình đơn giản thành một bức vẽ về {drawing_subject}.",
            materials_text="Giấy vẽ, bút chì sáp màu cỡ lớn và bảng kê giấy.",
            preparation_text=(
                "Chia giấy cho từng trẻ, kiểm tra sáp màu nguyên vẹn và đủ màu cơ bản."
            ),
            instructions_text=(
                "1. Cùng trẻ chọn một hình lớn để bắt đầu.\n"
                "2. Gợi ý trẻ thêm hai hoặc ba chi tiết mình nhớ được.\n"
                "3. Mời trẻ tô màu và đặt tên cho bức tranh."
            ),
            observation_notes="Ghi nhận cách trẻ chọn hình, thử màu và nói về ý tưởng của mình.",
            safety_notes=(
                "Nhắc trẻ ngồi vững, chia sẻ màu nhẹ nhàng và thu sáp vào hộp sau giờ học."
            ),
            activity_kind="indoor",
        ),
    ]
    return {
        "locale": "vi-VN",
        "title": title,
        "topic": topic,
        "target_age_band_ref": PLACEHOLDER_AGE_BAND_REF,
        "target_age_band_version": 1,
        "objectives": lesson_objectives,
        "drawing_subject": drawing_subject,
        "drawing_steps_text": steps,
        "subject_learning_notes": notes,
        "script_direction": None,
        "script_following_allowed": False,
        "activities": lesson_activities,
    }


# (lesson key, internal visibility, item revision, versions as (version no, review state, content))
LESSON_SPECS: tuple[tuple[str, str, int, tuple[tuple[int, str, dict[str, Any]], ...]], ...] = (
    (
        "l1",
        "PRIVATE",
        2,
        (
            (
                1,
                "APPROVED",
                lesson_content(
                    "Vẽ chú mèo con",
                    "Nhận biết dáng chú mèo đang ngồi",
                    "chú mèo đang ngồi",
                    objectives=[
                        "Trẻ nhận ra thân mèo có thể vẽ bằng một hình bầu dục lớn.",
                        "Trẻ thêm đầu, tai, mắt và đuôi bằng những nét đơn giản.",
                        "Trẻ chọn màu để thể hiện chú mèo theo trí tưởng tượng của mình.",
                    ],
                    drawing_steps_text=(
                        "1. Mời trẻ nhìn tranh mèo đang ngồi và nhận xét đầu, thân, chân.\n"
                        "2. Vẽ một hình bầu dục đứng làm thân mèo.\n"
                        "3. Thêm hình tròn nhỏ hơn phía trên để làm đầu.\n"
                        "4. Vẽ hai tai tam giác, mắt tròn, mũi nhỏ và ria ngắn.\n"
                        "5. Thêm bốn chân gấp gọn và một chiếc đuôi cong bên cạnh thân.\n"
                        "6. Tô màu lông và mời trẻ kể chú mèo đang làm gì."
                    ),
                    subject_learning_notes=(
                        "Mèo thường ngồi thu chân dưới thân để nghỉ ngơi. "
                        "Mèo dùng ria mép để cảm nhận khoảng trống xung quanh, "
                        "còn đôi tai giúp mèo nghe âm thanh nhỏ."
                    ),
                    activities=[
                        _activity(
                            "Nhìn dáng mèo đang ngồi",
                            objective=(
                                "Trẻ tìm được các hình tròn, bầu dục và nét cong trong dáng mèo."
                            ),
                            materials_text=(
                                "Tranh mèo đang ngồi, thẻ hình tròn và thẻ hình bầu dục."
                            ),
                            preparation_text=(
                                "Treo tranh ngang tầm mắt và xếp thẻ hình trên một chiếc bàn thấp."
                            ),
                            instructions_text=(
                                "1. Cho trẻ quan sát tranh rồi nói điều mình nhận ra trước tiên.\n"
                                "2. Đặt thẻ bầu dục cạnh thân mèo và thẻ tròn cạnh đầu mèo.\n"
                                "3. Mời trẻ dùng tay vẽ thử chiếc đuôi cong trong không khí."
                            ),
                            observation_notes=(
                                "Chú ý trẻ có ghép hình với đúng bộ phận "
                                "và mô tả được dáng ngồi không."
                            ),
                            safety_notes="Dùng thẻ giấy lớn, không có ghim hoặc chi tiết nhỏ rời.",
                            activity_kind="indoor",
                        ),
                        _activity(
                            "Vẽ chú mèo ngồi",
                            objective="Trẻ nối các hình cơ bản thành chú mèo và tự chọn màu lông.",
                            materials_text=(
                                "Giấy vẽ, bút chì sáp màu cỡ lớn và tranh mèo làm gợi ý."
                            ),
                            preparation_text=(
                                "Đặt giấy trên mặt bàn phẳng và chia mỗi trẻ một hộp sáp màu."
                            ),
                            instructions_text=(
                                "1. Cùng trẻ vẽ thân bầu dục rồi đặt đầu tròn lên phía trên.\n"
                                "2. Thêm tai, mắt, ria, chân và đuôi bằng nét ngắn.\n"
                                "3. Mời trẻ chọn màu, tô tranh rồi đặt tên cho chú mèo."
                            ),
                            observation_notes=(
                                "Ghi nhận cách trẻ giữ các bộ phận gần nhau "
                                "để mèo trông như đang ngồi."
                            ),
                            safety_notes=(
                                "Nhắc trẻ không vẽ lên bạn và cất bút màu vào hộp sau hoạt động."
                            ),
                            activity_kind="indoor",
                        ),
                    ],
                ),
            ),
            (
                2,
                "APPROVED",
                lesson_content(
                    "Vẽ chú mèo con bên cửa sổ",
                    "Chú mèo ngồi nhìn ra cửa sổ",
                    "chú mèo đang ngồi bên cửa sổ",
                    objectives=[
                        "Trẻ dùng hình bầu dục và hình tròn để vẽ chú mèo đang ngồi.",
                        "Trẻ sắp xếp chú mèo và khung cửa sổ trong cùng một bức tranh.",
                        "Trẻ chọn thêm cảnh vật bên ngoài theo điều mình tưởng tượng.",
                    ],
                    drawing_steps_text=(
                        "1. Hỏi trẻ cửa sổ thường có những đường thẳng nào.\n"
                        "2. Vẽ khung cửa sổ bằng một hình chữ nhật lớn.\n"
                        "3. Vẽ thân bầu dục và đầu tròn của chú mèo ở cạnh khung cửa.\n"
                        "4. Thêm tai, mắt, ria, chân gấp và đuôi cong.\n"
                        "5. Vẽ vài đám mây, tán cây hoặc cánh chim ngoài cửa sổ.\n"
                        "6. Tô màu trong khung cửa rồi kể chú mèo đang ngắm gì."
                    ),
                    subject_learning_notes=(
                        "Khung cửa giúp ánh sáng ban ngày vào phòng. Khi ngồi yên nhìn ra ngoài, "
                        "mèo có thể quan sát chim, lá cây và những chuyển động quanh nhà."
                    ),
                    activities=[
                        _activity(
                            "Tìm đường thẳng quanh cửa sổ",
                            objective=(
                                "Trẻ nhận biết hình chữ nhật và cách các đường tạo thành khung cửa."
                            ),
                            materials_text=(
                                "Tranh căn phòng có cửa sổ, que tính bản to và giấy khổ lớn."
                            ),
                            preparation_text=(
                                "Đặt tranh trên giá thấp và để que tính trên bàn, cách xa lối đi."
                            ),
                            instructions_text=(
                                "1. Cùng trẻ đếm các cạnh của khung cửa trong tranh.\n"
                                "2. Xếp bốn que thành hình chữ nhật trên mặt bàn.\n"
                                "3. Mời trẻ chỉ vị trí chú mèo và cảnh vật ở ngoài cửa."
                            ),
                            observation_notes=(
                                "Lắng nghe trẻ nói về cạnh dài, cạnh ngắn "
                                "và vị trí bên trong khung."
                            ),
                            safety_notes=(
                                "Chỉ dùng que giấy lớn, đầu tù; thu que ngay sau khi quan sát."
                            ),
                            activity_kind="indoor",
                        ),
                        _activity(
                            "Vẽ mèo ngắm cảnh ngoài cửa sổ",
                            objective=(
                                "Trẻ đặt chú mèo cạnh cửa sổ và thêm một chi tiết ở ngoài trời."
                            ),
                            materials_text=(
                                "Giấy vẽ, bút chì sáp màu và một tranh gợi ý căn phòng sáng."
                            ),
                            preparation_text=(
                                "Phát giấy, đặt tranh gợi ý ở giữa bàn và kiểm tra sáp màu cỡ lớn."
                            ),
                            instructions_text=(
                                "1. Mời trẻ vẽ khung cửa sổ trước để chọn vị trí cho bức tranh.\n"
                                "2. Vẽ chú mèo ngồi cạnh cửa, thêm mắt nhìn ra ngoài.\n"
                                "3. Thêm cây, mây hoặc chim theo ý trẻ rồi tô màu.\n"
                                "4. Mời trẻ kể điều chú mèo đang quan sát."
                            ),
                            observation_notes=(
                                "Ghi nhận trẻ có thể kể mối liên hệ giữa chú mèo và cảnh ngoài cửa."
                            ),
                            safety_notes=(
                                "Giữ lối đi thông thoáng và nhắc trẻ dùng sáp màu trên giấy."
                            ),
                            activity_kind="indoor",
                        ),
                    ],
                ),
            ),
        ),
    ),
    (
        "l2",
        "PRIVATE",
        1,
        (
            (
                1,
                "APPROVED",
                lesson_content(
                    "Vẽ cái cây xanh",
                    "Một cây xanh trong sân trường",
                    "cây xanh trong sân trường",
                    objectives=[
                        "Trẻ nhận ra thân cây, cành cây và tán lá có hình dáng khác nhau.",
                        "Trẻ dùng nét thẳng, nét cong và mảng màu để vẽ một cây xanh.",
                        "Trẻ kể được một điều cây cần để lớn lên.",
                    ],
                    drawing_steps_text=(
                        "1. Cùng trẻ quan sát thân cây và tán lá từ vị trí an toàn.\n"
                        "2. Vẽ hai nét dài làm thân cây, hơi rộng ở phía dưới.\n"
                        "3. Thêm vài cành nhỏ hướng lên hai bên.\n"
                        "4. Vẽ tán lá bằng những vòng cong hoặc các cụm hình tròn.\n"
                        "5. Thêm cỏ, nắng hoặc chiếc ghế ở sân trường.\n"
                        "6. Tô thân cây màu nâu, lá xanh và kể cây giúp sân trường thế nào."
                    ),
                    subject_learning_notes=(
                        "Rễ giữ cây đứng vững và hút nước trong đất. "
                        "Thân cây nâng cành lá lên cao, "
                        "còn lá đón ánh sáng để cây phát triển."
                    ),
                    activities=[
                        _activity(
                            "Quan sát cây trong sân trường",
                            objective=(
                                "Trẻ mô tả được thân cây, cành và tán lá bằng những từ đơn giản."
                            ),
                            materials_text=(
                                "Thẻ quan sát có hình chiếc lá và một bảng kẹp giấy nhẹ."
                            ),
                            preparation_text=(
                                "Chọn cây gần lối đi, báo trước ranh giới quan sát "
                                "và đi cùng cả lớp."
                            ),
                            instructions_text=(
                                "1. Đưa trẻ đến điểm đứng đã chọn, "
                                "cách gốc cây một khoảng an toàn.\n"
                                "2. Mời trẻ nhìn thân, cành và tán lá mà không cần chạm vào cây.\n"
                                "3. Hỏi trẻ cây cao hơn hay thấp hơn mình và lá nằm ở đâu.\n"
                                "4. Cùng trẻ trở vào lớp rồi kể lại điều vừa quan sát."
                            ),
                            observation_notes=(
                                "Chú ý trẻ có dùng từ chỉ vị trí và nhận ra lá mọc trên cành không."
                            ),
                            safety_notes=(
                                "Giáo viên đi đầu và cuối hàng; trẻ không trèo, "
                                "bẻ lá hoặc chạm côn trùng."
                            ),
                            activity_kind="outdoor",
                        ),
                        _activity(
                            "Vẽ cây cho sân trường",
                            objective="Trẻ thể hiện thân cây và tán lá bằng ít nhất hai loại nét.",
                            materials_text="Giấy vẽ, bút chì sáp màu xanh và nâu, bảng kê giấy.",
                            preparation_text=(
                                "Cho trẻ ngồi thành nhóm nhỏ và đặt màu ở giữa mỗi bàn."
                            ),
                            instructions_text=(
                                "1. Mời trẻ vẽ thân cây bằng hai nét dài.\n"
                                "2. Thêm cành và tán bằng những vòng tròn hoặc nét cong.\n"
                                "3. Vẽ thêm điều trẻ muốn thấy trong sân trường.\n"
                                "4. Cho trẻ kể cây cần gì để tiếp tục lớn lên."
                            ),
                            observation_notes="Ghi nhận trẻ nối thân với cành và chọn màu cho lá.",
                            safety_notes=(
                                "Nhắc trẻ không ngậm sáp màu, không đứng trên ghế "
                                "và rửa tay sau giờ học."
                            ),
                            activity_kind="indoor",
                        ),
                    ],
                ),
            ),
        ),
    ),
    (
        "l3",
        "SCHOOL",
        1,
        (
            (
                1,
                "PENDING_REVIEW",
                lesson_content(
                    "Vẽ ngôi nhà của bé",
                    "Ngôi nhà nhỏ nơi gia đình cùng quây quần",
                    "ngôi nhà của bé",
                    objectives=[
                        "Trẻ nhận ra mái nhà, thân nhà, cửa ra vào và cửa sổ.",
                        "Trẻ ghép hình tam giác và hình chữ nhật để vẽ ngôi nhà.",
                        "Trẻ thêm một chi tiết thể hiện nơi mình yêu quý.",
                    ],
                    drawing_steps_text=(
                        "1. Hỏi trẻ nhà thường có mái và những ô cửa nào.\n"
                        "2. Vẽ hình chữ nhật làm thân nhà.\n"
                        "3. Thêm mái tam giác ở phía trên.\n"
                        "4. Vẽ cửa ra vào và một hoặc hai cửa sổ.\n"
                        "5. Thêm cây, hoa hoặc người thân ở cạnh nhà.\n"
                        "6. Tô màu và mời trẻ kể một việc gia đình thường làm cùng nhau."
                    ),
                    subject_learning_notes=(
                        "Mái nhà che nắng mưa, còn cửa giúp mọi người đi vào và ra ngoài. "
                        "Những ngôi nhà có thể khác nhau về màu sắc, hình dáng "
                        "và nơi chúng được xây."
                    ),
                    activities=[
                        _activity(
                            "Ghép hình mái và thân nhà",
                            objective="Trẻ ghép được mái tam giác với thân nhà hình chữ nhật.",
                            materials_text=(
                                "Bộ hình giấy lớn gồm tam giác, chữ nhật, cửa và cửa sổ."
                            ),
                            preparation_text=(
                                "Xếp các hình theo khay riêng và dành chỗ rộng trên bàn nhóm."
                            ),
                            instructions_text=(
                                "1. Cho trẻ chọn một hình làm thân ngôi nhà.\n"
                                "2. Mời trẻ đặt mái lên phía trên rồi thử đổi màu mái.\n"
                                "3. Thêm cửa ra vào và cửa sổ vào vị trí trẻ muốn.\n"
                                "4. Cùng trẻ nói mỗi phần giúp ngôi nhà như thế nào."
                            ),
                            observation_notes=(
                                "Quan sát trẻ đặt mái trên thân và dùng từ trên, dưới, bên cạnh."
                            ),
                            safety_notes=(
                                "Dùng hình giấy khổ lớn đã cắt sẵn; "
                                "không dùng kéo trong hoạt động này."
                            ),
                            activity_kind="indoor",
                        ),
                        _activity(
                            "Vẽ ngôi nhà bé yêu quý",
                            objective=(
                                "Trẻ vẽ ngôi nhà bằng hình cơ bản "
                                "và thêm một chi tiết của riêng mình."
                            ),
                            materials_text="Giấy vẽ, bút sáp màu cỡ lớn và bảng kê chống trượt.",
                            preparation_text=(
                                "Đặt giấy ngay ngắn trước mỗi trẻ "
                                "và chia sẻ màu trong từng nhóm nhỏ."
                            ),
                            instructions_text=(
                                "1. Mời trẻ vẽ thân nhà trước rồi chọn kiểu mái.\n"
                                "2. Thêm cửa, cửa sổ và một chi tiết trẻ nhớ về gia đình.\n"
                                "3. Tô màu và đặt tên cho ngôi nhà trong tranh.\n"
                                "4. Mời từng trẻ kể một câu về nơi mình thích ở cùng người thân."
                            ),
                            observation_notes=(
                                "Lắng nghe trẻ giải thích lựa chọn "
                                "và ghi nhận cách trẻ sắp xếp các hình."
                            ),
                            safety_notes=(
                                "Nhắc trẻ ngồi vững, chuyền màu bằng tay "
                                "và cất đồ dùng khi hoàn tất."
                            ),
                            activity_kind="indoor",
                        ),
                    ],
                ),
            ),
        ),
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
    (
        "r1",
        "p1",
        "k1",
        "COMPLETED",
        False,
        "Chú mèo đi dạo trong vườn",
        "Bé nhà tôi muốn vẽ chú mèo đang đi dạo bên luống hoa.",
    ),
    ("r2", "p1", "k1", "FAILED", False, "Cây khế trước sân", None),
    ("r3", "p1", "k1", "DELETE_PENDING", False, "Ngôi nhà nhỏ của bé", None),
    (
        "r4",
        "p1",
        "k1",
        "INPUT_PROCESSING",
        True,
        "Đàn cá trong bể nước",
        "Con muốn vẽ đàn cá nhỏ bơi cạnh những bụi rong xanh.",
    ),
    ("r5", "p2", "k3", "COMPLETED", False, "Chiếc xe cứu hoả", None),
    (
        "r6",
        "p2",
        "k3",
        "PREPARATION_REVIEW",
        True,
        "Đoàn tàu qua cánh đồng",
        "Bé muốn vẽ đoàn tàu đang chạy qua cánh đồng xanh.",
    ),
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
        "be1_profile_revisions": len(be1_profile_revision_rows()),
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
    "be1_profile_revisions": 52,
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
    (
        "p4",
        "k4",
        "Chim sẻ đậu trên cành ổi",
        "Con muốn vẽ chú chim sẻ đang nghỉ trên cành ổi sau cơn mưa.",
    ),
    (
        "p5",
        "k5",
        "Ngôi nhà có khu vườn nhỏ",
        "Bé muốn vẽ mái nhà màu đỏ, bên cạnh có luống rau bà chăm sóc.",
    ),
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
