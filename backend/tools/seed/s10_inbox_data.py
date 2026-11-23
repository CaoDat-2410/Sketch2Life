"""Pure fixtures for the Phase C notification inbox seed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from tools.seed import data


@dataclass(frozen=True, slots=True)
class InboxItemSpec:
    key: str
    recipient_subject: str
    recipient_role: str
    notification_type: str
    trigger_id: str
    created_at: datetime
    safe_parameters: dict[str, str | int | bool]
    read: bool
    organization_ref: str | None = None
    expires_at: datetime | None = None


def _at(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 11, day, hour, 0, tzinfo=UTC)


_EXPIRES = datetime(2026, 12, 31, 0, 0, tzinfo=UTC)
_ORG_A = data.org_id("a")

# A parameter value that starts with this prefix names a row made by an earlier stage; the stage
# replaces it with that row's id before the command is built (``ref:run:<parent>:<state>``,
# ``ref:occ:<occurrence key>``).
REF = "ref:"

# No billing item is included: the SRS routes billing notices to the configured billing admin,
# and it does not establish that every School Manager is that recipient. The Manager's fourth
# sample is the second class-state change (suspended and archived are distinct events).
ITEMS: tuple[InboxItemSpec, ...] = (
    InboxItemSpec(
        "parent-p1-video-ready",
        data.PARENT_SUBJECTS["p1"],
        "parent",
        "VIDEO_READY",
        "story.video.ready",
        _at(21, 12),
        {"run_id": data.run_id("r1"), "state_code": "VIDEO_READY"},
        True,
    ),
    InboxItemSpec(
        "parent-p1-lesson-shared",
        data.PARENT_SUBJECTS["p1"],
        "parent",
        "LESSON_SHARED",
        "lesson.shared.parent-group",
        _at(17, 9),
        {"lesson_id": data.lesson_id("l1"), "capability": "VIEW"},
        False,
    ),
    InboxItemSpec(
        "parent-p3-run-completed",
        data.PARENT_SUBJECTS["p3"],
        "parent",
        "RUN_COMPLETED",
        "story.run.completed",
        _at(18, 15),
        {"run_id": f"{REF}run:p3:COMPLETED", "state_code": "COMPLETED"},
        True,
    ),
    InboxItemSpec(
        "parent-p3-review-required",
        data.PARENT_SUBJECTS["p3"],
        "parent",
        "RUN_REVIEW_REQUIRED",
        "story.review.required",
        _at(21, 8),
        {"run_id": f"{REF}run:p3:INPUT_REVIEW", "review_code": "INPUT"},
        False,
    ),
    InboxItemSpec(
        "parent-p4-review-required",
        data.PARENT_SUBJECTS["p4"],
        "parent",
        "RUN_REVIEW_REQUIRED",
        "story.review.required",
        _at(20, 9),
        {"run_id": f"{REF}run:p4:SUBJECT_REVIEW", "review_code": "SUBJECT"},
        False,
    ),
    InboxItemSpec(
        "parent-p5-video-ready",
        data.PARENT_SUBJECTS["p5"],
        "parent",
        "VIDEO_READY",
        "story.video.ready",
        _at(21, 11),
        {"run_id": f"{REF}run:p5:VIDEO_READY", "state_code": "VIDEO_READY"},
        False,
    ),
    InboxItemSpec(
        "parent-p5-adult-wait",
        data.PARENT_SUBJECTS["p5"],
        "parent",
        "ADULT_WAIT_REMINDER",
        "story.adult-wait.144h",
        _at(20, 9),
        {"run_id": f"{REF}run:p5:VIDEO_READY", "hours": 144},
        False,
        expires_at=_EXPIRES,
    ),
    InboxItemSpec(
        "teacher-a1-class-assigned",
        data.ORG_A_TEACHERS[0],
        "teacher",
        "CLASS_ASSIGNED",
        "class.teacher.assigned",
        _at(21, 10),
        {"class_id": data.class_id("a", 1)},
        False,
        organization_ref=_ORG_A,
    ),
    InboxItemSpec(
        "teacher-a1-lesson-share-reviewed",
        data.ORG_A_TEACHERS[0],
        "teacher",
        "LESSON_SHARE_REVIEWED",
        "lesson.share.reviewed",
        _at(20, 10),
        {"lesson_id": data.lesson_id("l1"), "review_code": "APPROVED"},
        True,
        organization_ref=_ORG_A,
    ),
    InboxItemSpec(
        "teacher-a1-profile-moved",
        data.ORG_A_TEACHERS[0],
        "teacher",
        "PROFILE_MOVED",
        "class.profile.moved",
        _at(19, 10),
        {"class_id": data.class_id("a", 3)},
        False,
        organization_ref=_ORG_A,
    ),
    InboxItemSpec(
        "teacher-a1-occurrence-reminder",
        data.ORG_A_TEACHERS[0],
        "teacher",
        "OCCURRENCE_REMINDER",
        "lesson.occurrence.reminder",
        _at(17, 10),
        {"occurrence_id": f"{REF}occ:o2", "days": 1},
        False,
        organization_ref=_ORG_A,
        expires_at=_EXPIRES,
    ),
    InboxItemSpec(
        "manager-a-share-awaiting-review",
        data.manager_subject("a"),
        "school_manager",
        "LESSON_SHARE_AWAITING_REVIEW",
        "lesson.share.awaiting-review",
        _at(21, 14),
        {"lesson_id": data.lesson_id("l3"), "review_state": "PENDING_REVIEW"},
        False,
        organization_ref=_ORG_A,
        expires_at=_EXPIRES,
    ),
    InboxItemSpec(
        "manager-a-class-suspended",
        data.manager_subject("a"),
        "school_manager",
        "CLASS_SUSPENDED",
        "class.state.suspended",
        _at(20, 14),
        {"class_id": data.class_id("a", 6), "state_code": "SUSPENDED"},
        True,
        organization_ref=_ORG_A,
    ),
    InboxItemSpec(
        "manager-a-class-archived",
        data.manager_subject("a"),
        "school_manager",
        "CLASS_ARCHIVED",
        "class.state.archived",
        _at(19, 14),
        {"class_id": data.class_id("a", 5), "state_code": "ARCHIVED"},
        True,
        organization_ref=_ORG_A,
    ),
    InboxItemSpec(
        "manager-a-teacher-cancelled-run",
        data.manager_subject("a"),
        "school_manager",
        "TEACHER_CANCELLED_RUN",
        "story.teacher.cancelled",
        _at(18, 14),
        {
            "run_id": data.seed_uuid_text("story-run:s11-org-a-teacher-cancel"),
            "state_code": "DELETE_PENDING",
        },
        False,
        organization_ref=_ORG_A,
    ),
)

EXPECTED: dict[str, int] = {
    "notifications_inbox_items": len(ITEMS),
    "be1_command_receipts_s10": sum(item.read for item in ITEMS),
}
