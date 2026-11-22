"""Authored Vietnamese fixtures for the SEED-2 lesson occurrence stage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from tools.seed import data


@dataclass(frozen=True, slots=True)
class OccurrenceSpec:
    key: str
    title: str
    class_number: int
    teacher_subject: str
    scheduled_date: date
    lesson_key: str | None = None
    lesson_version_no: int | None = None


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    key: str
    occurrence_key: str
    safe_file_name: str
    extension: str
    page_count: int
    extracted_text: str
    page_coverage: tuple[int, ...]
    warnings: tuple[str, ...] = ()
    parser_name: str = "seed-text-fixture"
    parser_version: str = "1.0"


@dataclass(frozen=True, slots=True)
class PlanSpec:
    occurrence_key: str
    revision_no: int
    expected_head_revision_no: int
    objectives: tuple[str, ...]
    teacher_direction: str
    safety_notes: str
    document_revision_no: int | None
    activity_orders: tuple[int, ...]
    confirm: bool


OCCURRENCES = (
    OccurrenceSpec(
        "o1",
        "Vẽ chú mèo con ngồi bên cửa sổ",
        1,
        data.ORG_A_TEACHERS[0],
        date(2026, 11, 24),
        "l1",
        2,
    ),
    OccurrenceSpec(
        "o2",
        "Vẽ cái cây xanh trong sân trường",
        1,
        data.ORG_A_TEACHERS[0],
        date(2026, 11, 26),
        "l2",
        1,
    ),
    OccurrenceSpec(
        "o3",
        "Ngôi nhà của bé",
        1,
        data.ORG_A_TEACHERS[0],
        date(2026, 12, 2),
    ),
    OccurrenceSpec(
        "o4",
        "Vẽ những chú cá trong bể nước",
        2,
        data.ORG_A_TEACHERS[1],
        date(2026, 12, 4),
    ),
    OccurrenceSpec(
        "o5",
        "Bài giảng con mèo cho lớp Lá",
        3,
        data.ORG_A_TEACHERS[0],
        date(2026, 12, 9),
        "l1",
        1,
    ),
)

DOCUMENTS = (
    DocumentSpec(
        "doc-o1",
        "o1",
        "giao-an-ve-meo-con.docx",
        ".docx",
        3,
        "Cô mời trẻ ngồi thành vòng cung để cùng quan sát tranh chú mèo đang nghỉ bên cửa sổ. "
        "Trẻ gọi tên đầu, thân, tai, chân và chiếc đuôi cong; cô gợi ý các con thử ghép hình tròn "
        "với hình bầu dục trước khi cầm bút. Sau đó mỗi trẻ tự chọn vị trí cho khung cửa, vẽ chú "
        "mèo ngồi bên cạnh và thêm một cảnh vật mình thích ở ngoài trời. Cô làm mẫu bằng nét lớn, "
        "chậm rãi, không yêu cầu trẻ sao chép giống nhau. Khi trẻ hoàn thành, cô mời từng bạn kể "
        "chú mèo đang nhìn gì và vì sao bạn chọn màu ấy. Cô chuẩn bị giấy khổ vừa, bút sáp màu "
        "cỡ lớn và tranh minh hoạ sạch, không có chi tiết gây sợ. Cuối giờ, trẻ cùng cô thu màu, "
        "đặt tranh lên kệ khô rồi rửa tay trước khi chuyển sang hoạt động tiếp theo.",
        (1, 2, 3),
    ),
    DocumentSpec(
        "doc-o2",
        "o2",
        "ke-hoach-cay-xanh.pdf",
        ".pdf",
        2,
        "Trước khi ra sân, cô nhắc trẻ đi thành hàng và dừng tại vạch đã chọn gần cây phượng. "
        "Các con quan sát thân cây, những cành hướng lên cao và tán lá xanh mà không cần chạm "
        "vào cây. Cô hỏi lá nằm ở đâu, thân cây có màu gì và cây cần gì để lớn lên. Trở vào lớp, "
        "trẻ dùng hai nét dài làm thân, thêm cành bằng nét cong và vẽ tán lá theo cách mình nhớ. "
        "Cô chuẩn bị giấy, bút sáp màu xanh và nâu, bảng kê nhẹ; trẻ có thể thêm nắng, cỏ hoặc "
        "chiếc ghế trong sân. Cô quan sát cách trẻ nối cành với thân, khuyến khích trẻ kể một "
        "điều cây mang lại cho sân trường. Không cho trẻ trèo, bẻ lá hay chạm vào côn trùng; "
        "sau giờ học, trẻ cất màu và rửa tay cùng cô.",
        (1,),
        ("OCR_NOT_SUPPORTED_PAGES",),
    ),
    DocumentSpec(
        "doc-o5",
        "o5",
        "bai-giang-meo-lop-la.pptx",
        ".pptx",
        12,
        "Bài giảng gợi ý trẻ quan sát mèo ngồi, nhận ra đầu tròn, thân bầu dục và chiếc đuôi cong. "
        "Cô lần lượt hướng dẫn vẽ thân, thêm đầu và tai, rồi chọn màu lông theo ý thích. Trẻ có "
        "thể kể về một chú mèo mình từng gặp hoặc tưởng tượng thêm chiếc nơ, chiếc ghế hay khung "
        "cửa sổ. Cô dành thời gian cho mỗi bạn giới thiệu tranh và lắng nghe bạn bè nhận xét bằng "
        "lời nhẹ nhàng. Bút sáp màu cỡ lớn được đặt giữa bàn; sau hoạt động, cả lớp cùng cất đồ "
        "dùng và lau sạch mặt bàn.",
        tuple(range(1, 13)),
    ),
)

DOCUMENT_EDIT_TEXT = (
    "Cô bắt đầu giờ học bằng câu hỏi: nếu chú mèo ngồi cạnh cửa sổ thì bên ngoài có thể nhìn "
    "thấy điều gì? Trẻ quan sát khung cửa hình chữ nhật, sau đó chọn hình tròn và bầu dục để "
    "phác thảo đầu cùng thân mèo. Cô làm mẫu từng bước trên giấy lớn, dừng lại để trẻ đoán "
    "nét tiếp theo thay vì vẽ hộ. Mỗi bạn được tự thêm tai, mắt, ria và chiếc đuôi; trẻ muốn "
    "vẽ thêm cây, mây hay chim ngoài cửa đều được khuyến khích. Cô chuẩn bị giấy không trơn, "
    "tranh gợi ý và sáp màu bản to, rồi kiểm tra bàn ghế vừa tầm trẻ. Trong lúc vẽ, cô quan sát "
    "cách trẻ cầm bút, gọi tên hình và kể về màu sắc mình chọn. Khi có bạn cần trợ giúp, cô gợi "
    "ý bằng câu hỏi ngắn để bạn tự hoàn thiện. Cuối giờ, từng trẻ giới thiệu tranh trong một "
    "câu; cả lớp cùng thu dọn sáp màu, cất tranh ở nơi khô ráo và rửa tay. Không dùng kéo hoặc "
    "vật sắc nhọn trong hoạt động, nhắc trẻ không đưa đồ dùng lên miệng và giữ lối đi thông thoáng."
)

PLANS = (
    PlanSpec(
        "o1",
        1,
        0,
        (
            "Trẻ nhận biết đầu, thân và đuôi của chú mèo qua các hình tròn, bầu dục và nét cong.",
            "Trẻ sắp xếp chú mèo bên khung cửa sổ và thêm một chi tiết ở ngoài trời.",
            "Trẻ kể được một câu về điều chú mèo đang ngắm nhìn.",
        ),
        "Cô giới thiệu tranh, làm mẫu bằng nét lớn rồi mời trẻ tự chọn "
        "vị trí cho khung cửa và chú mèo. "
        "Cô đi quanh các bàn, gợi ý bằng câu hỏi ngắn, để trẻ tự hoàn thiện "
        "tranh và chia sẻ ý tưởng.",
        "Dùng giấy và sáp màu cỡ lớn, không dùng vật sắc nhọn; "
        "nhắc trẻ không đưa đồ dùng lên miệng.",
        2,
        (1, 2),
        True,
    ),
    PlanSpec(
        "o2",
        1,
        0,
        (
            "Trẻ gọi tên được thân cây, cành và tán lá sau khi quan sát cùng cô.",
            "Trẻ dùng nét thẳng, nét cong và màu sắc để vẽ cây trong sân trường.",
        ),
        "Cô đưa trẻ đến điểm quan sát đã chọn, cùng các con nhìn thân và tán cây "
        "rồi trở về lớp theo hàng. "
        "Trong giờ vẽ, cô khuyến khích trẻ thêm chi tiết mình nhớ "
        "và kể cây giúp sân trường ra sao.",
        "Trẻ chỉ quan sát từ vị trí an toàn, không trèo cây, bẻ lá "
        "hoặc chạm vào côn trùng; sáp màu được cất sau giờ học.",
        1,
        (1, 2),
        False,
    ),
    PlanSpec(
        "o3",
        1,
        0,
        ("Trẻ ghép mái, thân và cửa thành hình ngôi nhà bằng các nét cơ bản.",),
        "Cô cho trẻ kể những phần dễ nhận ra của một ngôi nhà, sau đó mời "
        "các con vẽ thân nhà trước rồi chọn mái. "
        "Trẻ có thể thêm cửa sổ hoặc một chi tiết gợi nhớ đến gia đình mình.",
        "Dùng giấy và bút sáp màu cỡ lớn; không dùng kéo, và nhắc trẻ giữ màu trên giấy.",
        None,
        (),
        True,
    ),
    PlanSpec(
        "o3",
        2,
        1,
        (
            "Trẻ chọn được hình phù hợp để tạo mái và thân nhà.",
            "Trẻ đặt cửa ra vào ở vị trí hợp lý và kể được một hoạt động gia đình trong nhà.",
        ),
        "Cô khuyến khích trẻ bắt đầu từ hình chữ nhật, thử một kiểu mái "
        "rồi tự điều chỉnh kích thước. "
        "Sau khi thêm cửa và cửa sổ, trẻ chia sẻ điều mình thích nhất về ngôi nhà trong tranh.",
        "Chuẩn bị bàn ghế vững, chia màu theo nhóm và thu dọn sáp màu "
        "sau khi trẻ giới thiệu tranh.",
        None,
        (),
        True,
    ),
    PlanSpec(
        "o3",
        3,
        2,
        (
            "Trẻ phối hợp hình tam giác và hình chữ nhật để vẽ một ngôi nhà.",
            "Trẻ thêm người thân, cây hoặc hoa để thể hiện ý tưởng riêng.",
        ),
        "Cô đặt tranh gợi ý ở giữa bàn nhưng không yêu cầu trẻ chép lại. "
        "Trẻ tự chọn màu và chi tiết, "
        "còn cô ghi nhận lời kể của từng bạn để lần sau nối tiếp hoạt động.",
        "Giữ lối đi thông thoáng, chỉ dùng bút màu nguyên vẹn "
        "và nhắc trẻ chuyền màu cho bạn bằng hai tay thay vì ném qua bàn.",
        None,
        (),
        False,
    ),
)


EXPECTED = {
    "lesson_occurrences": 5,
    "lesson_source_documents": 3,
    "lesson_document_revisions": 4,
    "lesson_plan_revisions": 5,
    "lesson_plan_activities": 4,
}


def occurrence_key(key: str) -> str:
    return f"seed:s8:occ-{key}-create"


def plan_create_key(occurrence_key_value: str, revision_no: int) -> str:
    return f"seed:s8:{occurrence_key_value}:plan-{revision_no}-create"


def plan_confirm_key(occurrence_key_value: str, revision_no: int) -> str:
    return f"seed:s8:{occurrence_key_value}:plan-{revision_no}-confirm"


def source_document_id(key: str) -> str:
    return data.seed_uuid_text(f"s8:source-document:{key}")


def document_revision_id(key: str, revision_no: int) -> str:
    return data.seed_uuid_text(f"s8:document-revision:{key}:{revision_no}")
