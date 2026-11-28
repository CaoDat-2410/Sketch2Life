"""Vietnamese S14 content for synthetic web-screen examples."""

from __future__ import annotations

from typing import Final

from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from tools.seed import data

CONSENT_ORGANIZATION_ID: Final[str] = data.org_id("a")
CONSENT_CLASS_ID: Final[str] = data.class_id("a", 3)
CONSENT_ACTOR_SUBJECT: Final[str] = data.manager_subject("a")
CONSENT_PURPOSE_REF: Final[str] = "seed:s14:pending-school-activity"

NOTIFICATION_OPERATION: Final[str] = "s14.notification.create"
NOTIFICATION_KEY: Final[str] = "seed:s14:notification:admin"
NOTIFICATION_KIND: Final[str] = "S14_DEMO_READY"
NOTIFICATION_RESOURCE: Final[str] = "seed:s14:web-demo"

PLATFORM_LESSON_CONTENT: Final[LessonContentInputV1] = LessonContentInputV1(
    locale="vi-VN",
    title="Khu vườn nhỏ sau giờ học",
    topic="Quan sát cây và kể chuyện bằng hình vẽ",
    target_age_band_ref="age-72-107-months-v1",
    target_age_band_version=1,
    objectives=[
        "Nhận ra thân, lá và bông hoa qua hình dáng đơn giản.",
        "Chọn màu sắc để kể một điều em quan sát được trong vườn.",
    ],
    drawing_subject="Một góc vườn có cây, hoa và lối đi",
    drawing_steps_text=(
        "1. Cùng quan sát một góc vườn và gọi tên những phần dễ nhận ra.\n"
        "2. Vẽ lối đi hoặc luống cây bằng những nét lớn trước.\n"
        "3. Thêm lá, hoa và một chi tiết em muốn kể với cả lớp.\n"
        "4. Chọn màu theo ý tưởng của mình rồi giới thiệu bức tranh."
    ),
    subject_learning_notes=(
        "Cây thường có thân nâng đỡ lá và hoa. Hình dáng mỗi cây có thể khác nhau; "
        "khuyến khích trẻ quan sát, mô tả điều mình thấy và không cần vẽ giống hệt mẫu."
    ),
    script_direction=None,
    script_following_allowed=False,
    activities=[
        {
            "title": "Tìm hình trong khu vườn",
            "objective": "Gọi tên hai hình dáng hoặc màu sắc trẻ quan sát được.",
            "materials_text": "Tranh khu vườn, giấy vẽ và bút sáp màu cỡ lớn.",
            "preparation_text": "Đặt tranh ở tầm mắt trẻ và chia giấy trên bàn thấp.",
            "instructions_text": (
                "Mời trẻ quan sát tranh trong một phút. Hỏi trẻ nhận ra chiếc lá, "
                "bông hoa hay lối đi trước, rồi cùng tìm các hình tròn và nét cong."
            ),
            "observation_notes": "Lắng nghe cách trẻ mô tả màu sắc và vị trí các chi tiết.",
            "safety_notes": "Dùng bút sáp cỡ lớn; nhắc trẻ không đưa đồ dùng lên miệng.",
            "activity_kind": "indoor",
        }
    ],
)

EXPECTED: Final[dict[str, int]] = {
    "be1_consent_records_s14": 0,
    "core_audit_entries_s14": 4,
    "core_outbox_events_s14": 0,
    "learning_content_records_s14": 1,
    "learning_content_versions_s14": 1,
    "learning_content_events_s14": 2,
    "learning_content_outbox_s14": 2,
    "platform_command_receipts_s14": 5,
    "platform_lesson_items_s14": 1,
    "platform_lesson_versions_s14": 1,
    "platform_lesson_activities_s14": 1,
    "notification_inbox_items_s14": 1,
}


def consent_child_id() -> str:
    """Select the oldest existing synthetic child in the assigned Lá class."""
    candidates = [
        row for row in data.managed_profile_rows() if row["class_id"] == CONSENT_CLASS_ID
    ]
    if not candidates:
        raise ValueError("S14 consent class has no seeded synthetic profile")
    return str(max(candidates, key=lambda row: int(row["age_months"]))["child_id"])


__all__ = [
    "CONSENT_ACTOR_SUBJECT",
    "CONSENT_CLASS_ID",
    "CONSENT_ORGANIZATION_ID",
    "CONSENT_PURPOSE_REF",
    "EXPECTED",
    "NOTIFICATION_KEY",
    "NOTIFICATION_KIND",
    "NOTIFICATION_OPERATION",
    "NOTIFICATION_RESOURCE",
    "PLATFORM_LESSON_CONTENT",
    "consent_child_id",
]
