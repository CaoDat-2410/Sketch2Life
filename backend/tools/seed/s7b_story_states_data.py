"""Synthetic Vietnamese data for the Phase B Parent StoryRun states seed."""

from __future__ import annotations

import hashlib
import io
import wave
from datetime import UTC, datetime, timedelta
from typing import Any

from PIL import Image, ImageDraw

from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisResult,
    StoryGenerationResult,
)
from sketch2life.domain.parent_profiles import ProfileSnapshot
from tools.seed import data as s1_data

PROFILE_KEY = "k6"
PROFILE_SNAPSHOT = ProfileSnapshot(
    display_name="Mây",
    age_months=66,
    interests_summary="Mây thích xếp hình, chăm cây ở ban công và nghe kể chuyện về các con vật.",
)

P3_RUN_A = (
    "Hạt đậu thức giấc",
    "Bé muốn kể chuyện một hạt đậu được gieo trong chậu nhỏ rồi vươn lên đón nắng.",
)
P3_RUN_B = (
    "Chiếc thuyền giấy trên vũng nước",
    "Bé muốn vẽ một chiếc thuyền giấy chở chiếc lá đi quanh sân sau cơn mưa.",
)
P3A_TRANSCRIPT = "Con muốn hạt đậu lớn lên thành cây có hai chiếc lá xanh."
P4_SUBJECT = "Chim sẻ trên cành"
P5_SUBJECT = "Ngôi nhà có khu vườn nhỏ"
P3_ACTIVITY_LESSON_KEY = "l2"
P3_ACTIVITY_LESSON_VERSION_NO = 1

P5_ACTIVITY_LESSON_CONTENT: dict[str, Any] = {
    "locale": "vi-VN",
    "title": "Ngôi nhà bên khu vườn",
    "topic": "Thiết kế ngôi nhà có khu vườn nhỏ",
    "target_age_band_ref": "age-72-107-months-v1",
    "target_age_band_version": 1,
    "objectives": ["Nhận biết hình khối và sắp xếp chi tiết cho một ngôi nhà."],
    "drawing_subject": "Ngôi nhà có mái đỏ và khu vườn nhỏ",
    "drawing_steps_text": "Vẽ mái nhà, thân nhà, cửa ra vào rồi thêm các chi tiết của khu vườn.",
    "subject_learning_notes": "Khuyến khích trẻ mô tả cách các hình khối tạo thành ngôi nhà.",
    "script_direction": "Kể một câu chuyện nhẹ nhàng về việc cùng gia đình chăm sóc khu vườn.",
    "script_following_allowed": True,
    "activities": [
        {
            "title": "Khám phá ngôi nhà bên khu vườn",
            "objective": (
                "Trẻ quan sát mái nhà, cửa ra vào và cây trong khu vườn rồi chọn "
                "chi tiết để phác họa."
            ),
            "materials_text": "Bảng kẹp giấy, giấy vẽ và bút sáp màu cỡ lớn.",
            "preparation_text": (
                "Chọn góc sân bằng phẳng, có lối đi an toàn để trẻ quan sát "
                "khu vườn cùng người lớn."
            ),
            "instructions_text": (
                "1. Cùng người lớn quan sát mái nhà, cửa ra vào và cây từ lối đi an toàn.\n"
                "2. Mời trẻ tự chọn hình cơ bản để phác họa mặt tiền ngôi nhà.\n"
                "3. Thêm cửa sổ, lối đi và một chi tiết nhỏ trong khu vườn."
            ),
            "observation_notes": "Lắng nghe trẻ mô tả vị trí các phần của ngôi nhà và khu vườn.",
            "safety_notes": "Người lớn quan sát trẻ và giữ lối đi khô ráo, thông thoáng.",
            "activity_kind": "outdoor",
        }
    ],
}

S7B_COMMAND_CASES: dict[str, str] = {
    "profile_create": "p3-profile-create-1",
    "p3a_create": "p3-a-create-1",
    "p3a_confirm_context": "p3-a-confirm-context-1",
    "p3a_attach": "p3-a-attach-drawing-1",
    "p3a_submit_idea": "p3-a-submit-idea-1",
    "p3a_confirm_transcript": "p3-a-confirm-transcript-1",
    "p3a_confirm_subject": "p3-a-confirm-subject-1",
    "p3a_select_activity": "p3-a-select-activity-1",
    "p3a_reserve_story": "p3-a-reserve-story-1",
    "p3a_confirm_story": "p3-a-confirm-story-1",
    "p3a_request_video": "p3-a-request-video-1",
    "p3a_complete": "p3-a-complete-1",
    "p3b_create": "p3-b-create-1",
    "p3b_confirm_context": "p3-b-confirm-context-1",
    "p3b_attach": "p3-b-attach-drawing-1",
    "p4_attach": "p4-attach-drawing-1",
    "p5_attach": "p5-attach-drawing-1",
    "p5_confirm_subject": "p5-confirm-subject-1",
    "p5_select_activity": "p5-select-activity-1",
    "p5_reserve_story": "p5-reserve-story-1",
    "p5_confirm_story": "p5-confirm-story-1",
    "p5_request_video": "p5-request-video-1",
}

STORY_CREATE_CASES = {
    "p3-a": S7B_COMMAND_CASES["p3a_create"],
    "p3-b": S7B_COMMAND_CASES["p3b_create"],
}

STORY_RECEIPT_CASES = tuple(
    name
    for name in S7B_COMMAND_CASES
    if name not in {"profile_create", "p3a_reserve_story", "p5_reserve_story"}
)
STORY_CATALOG_RECEIPT_CASES = (
    "p3-outdoor-lesson-grant",
    "p5-lesson",
    "p5-grant",
    "p5-approve",
)

ABANDONED_RUN_ID = s1_data.seed_uuid_text("story-run:s7b:p1-abandoned")
ABANDONED_AT = datetime(2026, 11, 22, 0, 0, tzinfo=UTC)
SEED_TIME = datetime(2026, 11, 18, 0, 0, tzinfo=UTC)


def drawing_bytes(case: str) -> bytes:
    """Create a small, legible synthetic drawing entirely in memory."""

    image = Image.new("RGB", (96, 72), (250, 248, 238))
    draw = ImageDraw.Draw(image)
    ink = (57, 61, 54)
    if case == "p3-a":
        draw.rectangle((33, 42, 62, 65), outline=ink, width=3)
        draw.line((48, 42, 48, 22), fill=(61, 126, 70), width=3)
        draw.ellipse((34, 21, 48, 31), fill=(112, 171, 93), outline=ink)
        draw.ellipse((48, 26, 63, 36), fill=(142, 190, 113), outline=ink)
        draw.line((16, 66, 80, 66), fill=(167, 123, 74), width=2)
    elif case == "p3-b":
        for center_x in (31, 64):
            draw.ellipse((center_x - 5, 17, center_x + 5, 27), outline=ink, width=2)
            draw.line((center_x, 27, center_x, 48), fill=ink, width=2)
            draw.line((center_x, 34, center_x - 8, 41), fill=ink, width=2)
            draw.line((center_x, 34, center_x + 8, 41), fill=ink, width=2)
            draw.line((center_x, 48, center_x - 7, 58), fill=ink, width=2)
            draw.line((center_x, 48, center_x + 7, 58), fill=ink, width=2)
        draw.line((13, 63, 83, 63), fill=(100, 145, 190), width=3)
    elif case == "p4":
        draw.line((14, 55, 82, 48), fill=(119, 91, 60), width=4)
        draw.ellipse((37, 25, 63, 48), fill=(196, 162, 105), outline=ink, width=2)
        draw.ellipse((54, 21, 67, 34), fill=(196, 162, 105), outline=ink, width=2)
        draw.polygon(((66, 27), (77, 31), (66, 34)), fill=(214, 132, 69), outline=ink)
        draw.ellipse((62, 25, 64, 27), fill=ink)
        draw.arc((39, 28, 59, 45), 190, 345, fill=ink, width=2)
        draw.line((48, 47, 46, 53), fill=ink, width=2)
        draw.line((56, 46, 58, 52), fill=ink, width=2)
    elif case == "p5":
        draw.polygon(((22, 36), (48, 16), (75, 36)), outline=ink, fill=(197, 126, 99))
        draw.rectangle((28, 35, 69, 64), outline=ink, width=3, fill=(241, 218, 171))
        draw.rectangle((35, 42, 45, 51), outline=ink, width=2, fill=(168, 208, 215))
        draw.rectangle((53, 43, 62, 64), outline=ink, width=2, fill=(122, 157, 112))
        draw.ellipse((10, 58, 22, 69), fill=(112, 162, 91))
        draw.ellipse((72, 57, 84, 69), fill=(112, 162, 91))
    else:
        raise ValueError("unknown synthetic drawing case")
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


DRAWING_BYTES = {case: drawing_bytes(case) for case in ("p3-a", "p3-b", "p4", "p5")}
DRAWING_SHA256 = {
    case: hashlib.sha256(content).hexdigest() for case, content in DRAWING_BYTES.items()
}

DRAWING_RESULTS = {
    "p3-a": DrawingAnalysisResult(
        subject="Chậu đậu mới nhú mầm",
        visible_features=("mầm cây xanh", "hai chiếc lá non", "chậu nhỏ", "đường đất trong chậu"),
        confidence=0.96,
        topic_compatible=True,
    ),
    "p3-b": DrawingAnalysisResult(
        subject="Hai bạn nhỏ",
        visible_features=("hai hình người", "mặt trời", "vũng nước"),
        confidence=0.94,
        child_count=2,
        topic_compatible=True,
    ),
    "p4": DrawingAnalysisResult(
        subject=P4_SUBJECT,
        visible_features=("chim nâu", "mỏ cam", "cành cây", "mắt tròn"),
        confidence=0.93,
        topic_compatible=True,
    ),
    "p5": DrawingAnalysisResult(
        subject=P5_SUBJECT,
        visible_features=("mái nhà đỏ", "cửa xanh", "hai ô cửa sổ", "bụi cây nhỏ"),
        confidence=0.95,
        topic_compatible=True,
    ),
}


def synthetic_audio_bytes() -> bytes:
    """Return a deterministic, silent WAV stand-in; no audio file is written."""

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(1)
        writer.setframerate(8_000)
        writer.writeframes(bytes(8_000))
    return buffer.getvalue()


AUDIO_BYTES = synthetic_audio_bytes()
AUDIO_SHA256 = hashlib.sha256(AUDIO_BYTES).hexdigest()


def _scenes(items: tuple[tuple[str, str, str, str, tuple[str, ...]], ...]) -> list[dict[str, Any]]:
    return [
        {
            "scene_index": index,
            "title": title,
            "action": action,
            "visual_prompt": visual,
            "narration": narration,
            "start_ms": (index - 1) * 6_000,
            "duration_ms": 6_000,
            "character_anchors": list(anchors),
        }
        for index, (title, action, visual, narration, anchors) in enumerate(items, start=1)
    ]


P3A_STORY: dict[str, Any] = {
    "schema_version": "sketch2life.story-revision.v1",
    "language": "vi",
    "title": "Mầm đậu đón nắng",
    "story": {
        "opening": "Mây gieo một hạt đậu vào chiếc chậu nhỏ bên cửa sổ.",
        "middle": "Mỗi sáng, Mây tưới một ít nước và chờ chiếc mầm tìm thấy ánh nắng.",
        "ending": "Hai chiếc lá non mở ra, còn Mây nhớ rằng cây lớn lên nhờ được chăm sóc đều đặn.",
    },
    "duration_ms": 30_000,
    "scenes": _scenes(
        (
            (
                "Chiếc chậu bên cửa sổ",
                "Mây đặt hạt đậu vào lớp đất mềm trong chậu.",
                "Góc ban công sáng dịu, chiếc chậu đất nhỏ cạnh cửa sổ.",
                "Mây chọn một hạt đậu tròn và đặt nhẹ vào lòng đất.",
                ("Mây tóc ngắn", "chậu đất nâu"),
            ),
            (
                "Một ngụm nước",
                "Mây dùng chiếc bình nhỏ tưới quanh hạt đậu.",
                "Tia nước mảnh rơi xuống đất, nắng sớm trên bậu cửa.",
                "Mây tưới vừa đủ rồi đặt bình xuống để đất nghỉ.",
                ("Mây tóc ngắn", "bình tưới xanh"),
            ),
            (
                "Mầm cây thức giấc",
                "Một chiếc mầm xanh nhú lên sau vài ngày.",
                "Mầm cong nhỏ đội đất lên, hai lá mầm còn khép.",
                "Sáng hôm ấy, Mây nhìn thấy một chấm xanh vừa thức dậy.",
                ("Mây tóc ngắn", "mầm đậu xanh"),
            ),
            (
                "Lá tìm ánh sáng",
                "Hai chiếc lá mở rộng về phía cửa sổ.",
                "Lá non đón nắng, chiếc chậu đứng trên kệ gỗ.",
                "Mây xoay chậu một chút để cả hai chiếc lá đều gặp nắng.",
                ("Mây tóc ngắn", "hai lá non"),
            ),
            (
                "Ngày mai lại chăm cây",
                "Mây ghi dấu ngày cây lớn thêm trên tờ lịch nhỏ.",
                "Mây ngồi cạnh chậu cây, ban công có nắng ấm.",
                "Mây vui vì biết cây cần nước, ánh sáng và sự kiên nhẫn.",
                ("Mây tóc ngắn", "cây đậu nhỏ"),
            ),
        )
    ),
}

P5_STORY: dict[str, Any] = {
    "schema_version": "sketch2life.story-revision.v1",
    "language": "vi",
    "title": "Ngôi nhà chào buổi sáng",
    "story": {
        "opening": "Bé nhìn ngôi nhà mái đỏ và chiếc cửa xanh trong bức vẽ của mình.",
        "middle": "Một luống hoa nhỏ mọc bên lối đi, còn những ô cửa sổ đón nắng đầu ngày.",
        "ending": "Bé thêm một chiếc ghế trước hiên để cả nhà cùng ngồi ngắm khu vườn.",
    },
    "duration_ms": 30_000,
    "scenes": _scenes(
        (
            (
                "Mái nhà màu đỏ",
                "Bé tô mái nhà bằng màu đỏ ấm.",
                "Ngôi nhà nhỏ hiện ra trên tờ giấy đặt cạnh hộp màu.",
                "Bé chọn màu đỏ cho mái nhà để căn nhà trông thật ấm áp.",
                ("Bé áo vàng", "mái nhà đỏ"),
            ),
            (
                "Chiếc cửa xanh",
                "Bé vẽ cánh cửa và tay nắm tròn.",
                "Cửa xanh ở giữa căn nhà, hai ô cửa sổ sáng trong.",
                "Một chiếc cửa xanh mở ra lối vào ngôi nhà.",
                ("Bé áo vàng", "cửa xanh"),
            ),
            (
                "Luống hoa bên hiên",
                "Bé thêm vài bông hoa dọc theo lối đi.",
                "Những bông hoa vàng và tím mọc cạnh bậc thềm.",
                "Bé để lại khoảng đất nhỏ cho khu vườn của gia đình.",
                ("Bé áo vàng", "hoa tím"),
            ),
            (
                "Nắng qua ô cửa",
                "Ánh nắng chiếu lên bàn ăn phía trong nhà.",
                "Hai ô cửa sổ hắt nắng vào căn phòng gọn gàng.",
                "Buổi sáng, cả nhà có thể cùng ăn sáng bên cửa sổ.",
                ("Bé áo vàng", "ô cửa sổ"),
            ),
            (
                "Chiếc ghế trước hiên",
                "Bé đặt thêm một chiếc ghế cạnh chậu cây.",
                "Hiên nhà có ghế gỗ, chậu cây và lối đi sạch sẽ.",
                "Bé tưởng tượng mọi người cùng ngồi nghỉ sau khi chăm vườn.",
                ("Bé áo vàng", "ghế gỗ"),
            ),
        )
    ),
}

STORY_RESULTS = {
    "p3-a": StoryGenerationResult(P3A_STORY, "fixture-s7b-p3a", "sketch2life-story-v1", "1"),
    "p5": StoryGenerationResult(P5_STORY, "fixture-s7b-p5", "sketch2life-story-v1", "1"),
}


def abandoned_rows(issuer: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Post-closeout shape for P1's extra inactive history run and its first input."""

    profile_revision = s1_data.current_profile_revision("k1")
    profile_id = s1_data.parent_profile_id("k1")
    principal_scope = s1_data.principal_scope_ref(issuer, s1_data.PARENT_SUBJECTS["p1"])
    topic = "Chiếc lá cuối sân"
    idea = "Bé muốn kể về chiếc lá được gió đưa đến bên bậc cửa."
    snapshot = {
        "schema_version": s1_data.PARENT_CONTEXT_SCHEMA,
        "profile_revision_ref": str(profile_revision["profile_revision_id"]),
        "age_months": profile_revision["age_months"],
        "interests_summary": profile_revision["interests_summary"] or "",
        "topic": topic,
        "adult_confirmed_idea": idea,
    }
    run = {
        "run_id": ABANDONED_RUN_ID,
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": principal_scope,
        "profile_ref": str(profile_id),
        "child_age_months": profile_revision["age_months"],
        "run_state": "ABANDONED",
        "revision": 2,
        "version": 2,
        "retryable": False,
        "active_owner_parent_account_id": None,
        "current_input_revision": 1,
        "adult_wait_started_at": None,
        "last_meaningful_activity_at": ABANDONED_AT - timedelta(hours=169),
        "finished_at": ABANDONED_AT,
        "created_at": ABANDONED_AT - timedelta(hours=170),
        "updated_at": ABANDONED_AT,
    }
    input_row = {
        "run_input_id": s1_data.seed_uuid_text("story-run-input:s7b:p1-abandoned:1"),
        "run_id": ABANDONED_RUN_ID,
        "input_revision": 1,
        "typed_idea": idea,
        "idea_source": "TEXT",
        "source_profile_revision_ref": str(profile_revision["profile_revision_id"]),
        "context_revision": 1,
        "context_snapshot": snapshot,
        "context_snapshot_sha256": s1_data.sha256_json(snapshot),
        "context_confirmed_by": principal_scope,
        "context_confirmed_at": SEED_TIME,
        "created_at": run["created_at"],
    }
    return run, input_row


EXPECTED: dict[str, int] = {
    "story_runs_s7b": 5,
    "story_run_inputs_s7b": 10,
    "story_story_revisions_s7b": 2,
    "story_video_generations_s7b": 2,
    "story_transcript_revisions_s7b": 1,
    "story_activity_selections_s7b": 2,
    "parent_child_profiles_s7b": 1,
    "parent_profile_revisions_s7b": 1,
    "story_understanding_revisions_s7b": 3,
    "story_review_decisions_s7b": 2,
    "story_story_revision_reviews_s7b": 2,
    "story_story_scenes_s7b": 10,
    "story_video_generation_scenes_s7b": 10,
    "story_asset_lineage_s7b": 4,
    "story_command_receipts_s7b": len(STORY_RECEIPT_CASES),
    "parent_command_receipts_s7b": 1,
    "core_asset_metadata_s7b": 11,
    "lesson_library_items_s7b": 1,
    "lesson_library_versions_s7b": 1,
    "lesson_version_activities_s7b": 1,
    "lesson_access_grants_s7b": 2,
    "lesson_command_receipts_s7b": len(STORY_CATALOG_RECEIPT_CASES),
}


__all__ = [
    "ABANDONED_AT",
    "ABANDONED_RUN_ID",
    "AUDIO_BYTES",
    "AUDIO_SHA256",
    "DRAWING_BYTES",
    "DRAWING_RESULTS",
    "DRAWING_SHA256",
    "EXPECTED",
    "P3A_STORY",
    "P3A_TRANSCRIPT",
    "P3_ACTIVITY_LESSON_KEY",
    "P3_ACTIVITY_LESSON_VERSION_NO",
    "P3_RUN_A",
    "P3_RUN_B",
    "P4_SUBJECT",
    "P5_ACTIVITY_LESSON_CONTENT",
    "P5_SUBJECT",
    "PROFILE_KEY",
    "PROFILE_SNAPSHOT",
    "S7B_COMMAND_CASES",
    "STORY_CREATE_CASES",
    "STORY_CATALOG_RECEIPT_CASES",
    "STORY_RECEIPT_CASES",
    "STORY_RESULTS",
    "abandoned_rows",
    "drawing_bytes",
]
