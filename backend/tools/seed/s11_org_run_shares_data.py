"""Pure fixtures for Teacher-run cancellation and private lesson-share seeds."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from tools.seed import data

ORG_A = data.org_id("a")
TEACHER_A1 = data.ORG_A_TEACHERS[0]
TEACHER_A2 = data.ORG_A_TEACHERS[1]
MANAGER_A = data.manager_subject("a")
PARENT_P1 = data.PARENT_SUBJECTS["p1"]
PARENT_GROUP_A1 = data.PARENT_GROUP_IDS[0]

TEACHER_RUN_ID = data.seed_uuid_text("story-run:s11-org-a-teacher-cancel")
TEACHER_RUN_INPUT_ID = data.seed_uuid_text("story-run-input:s11-org-a-teacher-cancel:1")
TEACHER_RUN_PROFILE_REF = "seed-ch-a-1-1"
TEACHER_RUN_CREATED_AT = datetime(2026, 11, 21, 8, 0, tzinfo=UTC)
TEACHER_RUN_STATE = "PREPARATION_REVIEW"
TEACHER_RUN_CANCEL_KEY = "teacher-run-cancel"
TEACHER_RUN_REVISION = 1
TEACHER_RUN_TOPIC = "Khu vườn sau cơn mưa"
TEACHER_RUN_IDEA = "Em muốn vẽ những luống rau xanh bên chiếc bình tưới nhỏ."
TEACHER_PROFILE_REVISION_REF = data.seed_uuid_text("managed-profile-revision:seed-ch-a-1-1:1")
TEACHER_CONTEXT_SNAPSHOT: dict[str, Any] = {
    "schema_version": data.PARENT_CONTEXT_SCHEMA,
    "profile_revision_ref": TEACHER_PROFILE_REVISION_REF,
    "age_months": 36,
    "interests_summary": "",
    "topic": TEACHER_RUN_TOPIC,
    "adult_confirmed_idea": TEACHER_RUN_IDEA,
}


def _activity(
    title: str,
    objective: str,
    instructions: str,
    *,
    materials: str = "Giấy vẽ A4, bút chì và bút sáp màu.",
    preparation: str = (
        "Đặt giấy và màu trong tầm với; người lớn kiểm tra đầu bút trước khi bắt đầu."
    ),
    observation: str = (
        "Khuyến khích trẻ kể về hình mình đang vẽ, không yêu cầu tô theo một mẫu duy nhất."
    ),
    safety: str = "Dùng bút màu phù hợp với trẻ và giữ bàn vẽ khô, thoáng.",
) -> dict[str, str]:
    return {
        "title": title,
        "objective": objective,
        "materials_text": materials,
        "preparation_text": preparation,
        "instructions_text": instructions,
        "observation_notes": observation,
        "safety_notes": safety,
        "activity_kind": "indoor",
    }


LESSON_CONTENTS: dict[str, dict[str, Any]] = {
    "chicken": {
        "locale": "vi-VN",
        "title": "Vẽ chú gà con",
        "topic": "Những hình tròn trong sân nhỏ",
        "target_age_band_ref": data.SUPPORTED_AGE_BAND_REF,
        "target_age_band_version": 1,
        "objectives": [
            (
                "Ghép hình tròn và hình bầu dục thành chú gà con, rồi chọn màu để thể hiện "
                "ý tưởng riêng."
            )
        ],
        "drawing_subject": "chú gà con",
        "drawing_steps_text": (
            "Bắt đầu bằng một hình tròn nhỏ làm đầu và một hình bầu dục lớn hơn làm thân. "
            "Nối hai hình bằng nét cong nhẹ, thêm chiếc mỏ tam giác, mắt tròn và hai chân ngắn. "
            "Vẽ vài chiếc lông ở đuôi, sau đó tô lông vàng hoặc màu trẻ thích; để lại giấy trắng "
            "ở mắt để chú gà trông sáng hơn."
        ),
        "subject_learning_notes": (
            "Gà con có thân phủ lông mềm, mỏ nhỏ và hai chân giúp đứng, bước đi. Có thể quan sát "
            "hình dáng qua tranh minh họa của bài học hoặc qua cách trẻ tưởng tượng."
        ),
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            _activity(
                "Tìm hình trong dáng gà con",
                "Nhận ra những hình cơ bản có thể ghép thành đầu, thân và mỏ.",
                "Mời trẻ dùng ngón tay vẽ một vòng tròn trong không khí. Cùng trẻ đặt hình tròn "
                "làm đầu và hình bầu dục làm thân trên giấy. Hỏi trẻ muốn chú gà nhìn về phía nào, "
                "rồi thử thêm mỏ ở hướng đó.",
                observation=(
                    "Quan sát trẻ có nối được các hình thành một dáng liền mạch hay muốn thử "
                    "cách ghép khác."
                ),
            ),
            _activity(
                "Vẽ gà con bên ổ rơm",
                "Hoàn thiện một bức tranh có chú gà con và một chi tiết nền đơn giản.",
                "Trẻ thêm mắt, mỏ, chân và vài nét lông. Gợi ý vẽ những nét cong ngắn làm ổ rơm "
                "hoặc thêm một hạt thóc bên cạnh. Trẻ tự chọn màu cho gà và nền, rồi kể một câu "
                "ngắn về nơi chú gà đang đứng.",
                safety="Không dùng hạt nhỏ rời làm đồ trang trí; chỉ vẽ hạt thóc bằng bút màu.",
            ),
        ],
    },
    "sailing": {
        "locale": "vi-VN",
        "title": "Vẽ chiếc thuyền buồm",
        "topic": "Gió đưa thuyền trên mặt nước",
        "target_age_band_ref": data.SUPPORTED_AGE_BAND_REF,
        "target_age_band_version": 1,
        "objectives": [
            "Sắp xếp thân thuyền, cột buồm và cánh buồm thành một hình cân đối trên mặt nước."
        ],
        "drawing_subject": "chiếc thuyền buồm",
        "drawing_steps_text": (
            "Kẻ một đường ngang nhẹ để đánh dấu mặt nước. Vẽ thân thuyền bằng một nét cong dài "
            "khép lại ở hai đầu, dựng cột buồm ở giữa và thêm một hoặc hai cánh buồm bằng các "
            "đường xiên. Cuối cùng, tô thân thuyền, buồm và mặt nước bằng những màu khác nhau; "
            "có thể thêm mây hoặc gợn sóng nhỏ."
        ),
        "subject_learning_notes": (
            "Thuyền buồm có phần thân nổi trên mặt nước và cánh buồm đón gió. Cánh buồm có thể "
            "được tạo bằng những hình tam giác đơn giản; trẻ được tự chọn số lượng và màu sắc."
        ),
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            _activity(
                "Quan sát thân thuyền và cánh buồm",
                "Phân biệt phần thân thuyền với những mảng buồm phía trên cột buồm.",
                "Cùng trẻ nhìn vào sơ đồ nét đơn của bài học và chỉ lần lượt thân thuyền, "
                "cột buồm, "
                "cánh buồm. Trẻ dùng tay mô tả đường cong của thân thuyền rồi dùng hai ngón tay "
                "tạo thành hình tam giác cho cánh buồm.",
                materials="Giấy vẽ A4, bút chì và bút sáp màu; không cần vật sắc nhọn.",
                safety=(
                    "Chỉ dùng vật liệu vẽ an toàn; người lớn không cần chuẩn bị thuyền thật "
                    "hoặc chậu nước."
                ),
            ),
            _activity(
                "Vẽ thuyền đón gió",
                "Thể hiện chiếc thuyền đang đi trên mặt nước bằng nét cong và mảng màu riêng.",
                "Trẻ vẽ thân thuyền trước, đặt cột buồm lên trên rồi chọn hình cho cánh buồm. "
                "Thêm vài đường lượn dưới thân thuyền làm gợn sóng. Mời trẻ chọn màu buồm khác "
                "màu thân thuyền và nói xem gió đang đưa thuyền đi đâu.",
                observation=(
                    "Gợi ý thêm đường sóng khi trẻ đã hoàn thành thuyền, không sửa thay nét "
                    "vẽ của trẻ."
                ),
            ),
        ],
    },
    "sunflower": {
        "locale": "vi-VN",
        "title": "Vẽ bông hoa hướng dương",
        "topic": "Bông hoa đón nắng",
        "target_age_band_ref": data.SUPPORTED_AGE_BAND_REF,
        "target_age_band_version": 1,
        "objectives": [
            "Quan sát cấu tạo đơn giản của hoa và dùng các nét lặp lại để vẽ cánh, nhụy, thân, lá."
        ],
        "drawing_subject": "bông hoa hướng dương",
        "drawing_steps_text": (
            "Vẽ một vòng tròn ở giữa làm nhụy, sau đó thêm các cánh dài xung quanh. Kéo một nét "
            "thẳng hơi cong xuống dưới để tạo thân và gắn hai chiếc lá ở hai bên. Tô nhụy nâu, "
            "cánh vàng và thân xanh nếu trẻ thích; để trẻ đổi màu theo ý tưởng của mình."
        ),
        "subject_learning_notes": (
            "Hoa hướng dương có nhụy lớn ở giữa, nhiều cánh xung quanh và thân xanh có lá. Khi vẽ, "
            "trẻ có thể nhận ra các cánh lặp lại theo vòng tròn mà không cần đếm chính xác."
        ),
        "script_direction": None,
        "script_following_allowed": False,
        "activities": [
            _activity(
                "Nhìn cấu tạo của bông hoa",
                "Gọi tên được nhụy, cánh, thân và lá bằng quan sát trực quan.",
                "Mời trẻ chạm nhẹ vào các phần trên sơ đồ: nhụy ở giữa, cánh ở xung quanh, thân "
                "ở phía dưới và lá mọc hai bên. Cùng trẻ thử tạo hình bông hoa bằng bàn tay mở "
                "rồi thu các ngón tay lại làm nhụy.",
                materials="Sơ đồ nét đơn của bài học, giấy vẽ và bút sáp màu.",
                observation=(
                    "Đón nhận cách trẻ mô tả cánh hoa bằng lời của mình, kể cả khi trẻ chọn "
                    "số cánh khác nhau."
                ),
            ),
            _activity(
                "Vẽ hoa trong chiếc bình",
                "Sắp xếp một bông hoa và chiếc bình thành bố cục có khoảng trống rõ ràng.",
                "Trẻ vẽ hoa ở phía trên tờ giấy, kéo thân xuống dưới rồi thêm chiếc bình bằng hai "
                "nét thẳng và một nét cong ở đáy. Gợi ý tô cánh trước, nhụy sau; cuối cùng trẻ có "
                "thể thêm một chiếc lá hoặc đặt bình trên bàn.",
                preparation="Đặt giấy theo chiều dọc và để trẻ chọn một bộ màu vừa tay.",
                safety="Nhắc trẻ tô từng mảng vừa sức, không ấn mạnh đầu bút xuống giấy.",
            ),
        ],
    },
}

LESSON_TITLES: tuple[str, ...] = tuple(
    str(LESSON_CONTENTS[key]["title"]) for key in ("chicken", "sailing", "sunflower")
)

# Each lesson starts PRIVATE. The service's real grant flow sets the final visibility. A named
# Parent grant is an invitation (INVITED), so the sailing lesson also receives an active grant to
# the existing Parent group whose only active member is that same Parent; this preserves the
# requested SELECTED_AUDIENCE visibility without bypassing the service.
PRIVATE_SHARE_SPECS: tuple[dict[str, str], ...] = (
    {
        "lesson_key": "chicken",
        "author": TEACHER_A1,
        "audience_kind": "ORGANIZATION",
        "audience_ref": ORG_A,
        "capability": "VIEW",
        "expected_visibility": "SCHOOL",
        "expected_review_state": "DRAFT",
    },
    {
        "lesson_key": "sailing",
        "author": TEACHER_A2,
        "audience_kind": "PRINCIPAL",
        "audience_ref": PARENT_P1,
        "capability": "VIEW",
        "expected_visibility": "SELECTED_AUDIENCE",
        "expected_review_state": "PENDING_REVIEW",
    },
    {
        "lesson_key": "sunflower",
        "author": TEACHER_A1,
        "audience_kind": "PARENT_GROUP",
        "audience_ref": PARENT_GROUP_A1,
        "capability": "VIEW",
        "expected_visibility": "SELECTED_AUDIENCE",
        "expected_review_state": "CHANGES_REQUESTED",
    },
)

REVIEW_REQUEST_LESSONS = ("sailing", "sunflower")
REVIEW_CHANGE_REASON = (
    "Phần tâm hoa chưa được tách rõ khỏi cánh. Vui lòng thêm bước chấm các hạt nhỏ và nhắc "
    "trẻ tô nhẹ tay để giấy không bị rách."
)

LESSON_RECEIPT_KEYS: tuple[str, ...] = (
    "lesson-chicken-create",
    "lesson-chicken-school-grant",
    "lesson-sailing-create",
    "lesson-sailing-submit-review",
    "lesson-sailing-parent-invite",
    "lesson-sailing-parent-group-grant",
    "lesson-sunflower-create",
    "lesson-sunflower-submit-review",
    "lesson-sunflower-request-changes",
    "lesson-sunflower-parent-group-grant",
)

EXPECTED: dict[str, int] = {
    "lesson_library_items_s11": 3,
    "lesson_library_versions_s11": 3,
    "lesson_version_activities_s11": 6,
    "lesson_access_grants_s11": 6,
    "lesson_command_receipts_s11": len(LESSON_RECEIPT_KEYS),
    "story_runs_s11": 1,
    "story_run_inputs_s11": 1,
    "story_command_receipts_s11": 1,
}
