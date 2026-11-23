"""Synthetic Vietnamese fixtures for the SEED-2 S12 Phase A story stage."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Final

from tools.seed import data

S12_NAMESPACE: Final[uuid.UUID] = data.seed_uuid("s12-story-v4a-namespace")

REUSED_ORG_ID: Final[str] = data.org_id("a")
REUSED_TEACHER_SUBJECT: Final[str] = data.ORG_A_TEACHERS[0]
REUSED_MANAGER_SUBJECT: Final[str] = data.manager_subject("a")
REUSED_PARENT_KEY: Final[str] = "p1"
REUSED_CHILD_KEY: Final[str] = "k1"

OUTDOOR_AGE_BAND_REF: Final[str] = "age-36-71-months-v1"
OUTDOOR_AGE_BAND_VERSION: Final[int] = 1
QUALITY_REASON_CODE: Final[str] = "QUALITY_LOW"


def s12_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(S12_NAMESPACE, name)


def s12_uuid_text(name: str) -> str:
    return str(s12_uuid(name))


def sha256_text(text: str) -> str:
    return data.sha256_json({"text": text})


@dataclass(frozen=True)
class S12ParentSpec:
    key: str
    subject: str
    account_id: str
    profile_key: str
    profile_id: uuid.UUID
    profile_revision_id: uuid.UUID
    child_name: str
    age_months: int
    interests_summary: str

    @property
    def scope_ref(self) -> str:
        return data.principal_scope_ref(data.SEED_ISSUER, self.subject)


PARENT_SPECS: Final[tuple[S12ParentSpec, ...]] = (
    S12ParentSpec(
        key="p6",
        subject="seed-parent-s12-p6",
        account_id=s12_uuid_text("adult:p6"),
        profile_key="k6",
        profile_id=s12_uuid("profile:k6"),
        profile_revision_id=s12_uuid("profile-rev:k6:1"),
        child_name="Na",
        age_months=54,
        interests_summary="Na thích vẽ cây xanh và quan sát lá rụng ở sân trường.",
    ),
    S12ParentSpec(
        key="p7",
        subject="seed-parent-s12-p7",
        account_id=s12_uuid_text("adult:p7"),
        profile_key="k7",
        profile_id=s12_uuid("profile:k7"),
        profile_revision_id=s12_uuid("profile-rev:k7:1"),
        child_name="Su",
        age_months=48,
        interests_summary="Su thích vẽ bông hoa nắng sớm và bạn nhỏ ngoài công viên.",
    ),
)

PARENTS_BY_KEY: Final[dict[str, S12ParentSpec]] = {spec.key: spec for spec in PARENT_SPECS}

LESSON_ID: Final[str] = s12_uuid_text("lesson:outdoor:1")
LESSON_VERSION_ID: Final[str] = s12_uuid_text("lesson-version:outdoor:1:v1")
LESSON_GRANT_ID: Final[str] = s12_uuid_text("lesson-grant:public:1")
LESSON_ACTIVITY_IDS: Final[tuple[str, str]] = (
    s12_uuid_text("lesson-activity:outdoor:1"),
    s12_uuid_text("lesson-activity:outdoor:2"),
)

LESSON_CONTENT: Final[dict[str, Any]] = {
    "locale": "vi-VN",
    "title": "Khám phá cây xanh sân trường",
    "topic": "Thiên nhiên quanh bé",
    "target_age_band_ref": OUTDOOR_AGE_BAND_REF,
    "target_age_band_version": OUTDOOR_AGE_BAND_VERSION,
    "objectives": [
        "Quan sát màu sắc của lá cây và ánh nắng ngoài sân trường.",
        "Kể lại điều bé nhìn thấy qua bức vẽ cùng người thân.",
    ],
    "drawing_subject": "Cây xanh sân trường",
    "drawing_steps_text": "1. Vẽ thân cây thẳng. 2. Vẽ tán lá xanh và tia nắng nhẹ.",
    "subject_learning_notes": "Khuyến khích bé gọi tên lá cây, thân cây và nắng sớm.",
    "script_direction": "Giữ giọng kể ấm áp, gần gũi với trải nghiệm sân trường của bé.",
    "script_following_allowed": False,
}

LESSON_ACTIVITIES: Final[tuple[dict[str, Any], ...]] = (
    {
        "title": "Nhặt lá rụng vẽ tranh cây xanh",
        "objective": "Giúp bé nhận biết hình dáng lá cây ngoài sân trường.",
        "materials_text": "Lá cây rụng sạch, giấy vẽ khổ A4 và bút sáp màu.",
        "preparation_text": "Chọn góc sân trường thoáng mát, an toàn cho bé đi dạo.",
        "instructions_text": "Cùng bé nhặt ba chiếc lá khác nhau, đặt cạnh tranh cây xanh.",
        "observation_notes": "Ghi lại màu lá bé chọn để đưa vào câu chuyện.",
        "safety_notes": "Tránh lá có gai hoặc khu vực ẩm ướt trơn trượt.",
        "activity_kind": "outdoor",
    },
    {
        "title": "Tìm bóng nắng và bông hoa ngoài vườn",
        "objective": "Giúp bé quan sát ánh nắng chiếu qua tán cây xanh.",
        "materials_text": "Bình nước cá nhân và phấn màu vẽ trên sân khô.",
        "preparation_text": "Đi dạo buổi sáng khi nắng dịu ở sân trường hoặc công viên.",
        "instructions_text": "Bé chỉ bóng nắng dưới tán cây xanh và kể màu bông hoa nhìn thấy.",
        "observation_notes": "Khuyến khích bé đặt một câu ngắn về bông hoa và nắng sớm.",
        "safety_notes": "Đội mũ cho bé và nhắc uống nước sau hoạt động ngoài trời.",
        "activity_kind": "outdoor",
    },
)

LESSON_CONTENT_HASH: Final[str] = data.sha256_json(
    {**LESSON_CONTENT, "activities": list(LESSON_ACTIVITIES)}
)

RUN_STARTED_ID: Final[str] = s12_uuid_text("run:started")
RUN_SAFETY_BLOCKED_ID: Final[str] = s12_uuid_text("run:safety-blocked")
RUN_COMPLETED_ID: Final[str] = s12_uuid_text("run:completed")

SELECT_STARTED_KEY_1: Final[str] = "seed:s12:started:select-1"
SELECT_STARTED_KEY_2: Final[str] = "seed:s12:started:select-2"
CONFIRM_CONTEXT_STARTED_KEY: Final[str] = "seed:s12:started:confirm-context"

SAFETY_STORY_REV_ID: Final[str] = s12_uuid_text("story-rev:safety-blocked:1")
SAFETY_REVIEW_ID: Final[str] = s12_uuid_text("story-review:safety-blocked:1")
SAFETY_VIDEO_GEN_ID: Final[str] = s12_uuid_text("video-gen:safety-blocked:1")

COMPLETED_STORY_REV_ID: Final[str] = s12_uuid_text("story-rev:completed:1")
COMPLETED_REVIEW_EPOCH_1_ID: Final[str] = s12_uuid_text("story-review:completed:epoch-1")
COMPLETED_REVIEW_EPOCH_2_ID: Final[str] = s12_uuid_text("story-review:completed:epoch-2")
COMPLETED_VIDEO_SPENT_ID: Final[str] = s12_uuid_text("video-gen:completed:1")
COMPLETED_VIDEO_READY_ID: Final[str] = s12_uuid_text("video-gen:completed:2")
COMPLETED_VIDEO_ASSET_REF: Final[str] = "seed/s12/run-completed/video-v2.mp4"


def activity_ref(activity_index: int) -> dict[str, Any]:
    return {
        "lesson_id": LESSON_ID,
        "version_id": LESSON_VERSION_ID,
        "content_sha256": LESSON_CONTENT_HASH,
        "activity_index": activity_index,
    }


def adult_identity_rows() -> list[dict[str, Any]]:
    return [
        {
            "subject": spec.subject,
            "account_id": spec.account_id,
            "issuer": data.SEED_ISSUER,
            "state": "active",
            "account_role": "parent",
            "email_verification_required": False,
            "role_revision": 1,
            "created_at": data.SEED_TIME,
        }
        for spec in PARENT_SPECS
    ]


def parent_profile_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles: list[dict[str, Any]] = []
    revisions: list[dict[str, Any]] = []
    for spec in PARENT_SPECS:
        snapshot = data.ProfileSnapshot(
            display_name=spec.child_name,
            age_months=spec.age_months,
            interests_summary=spec.interests_summary,
        )
        profiles.append(
            {
                "parent_profile_id": spec.profile_id,
                "owner_issuer": data.SEED_ISSUER,
                "owner_subject": spec.subject,
                "state": "ACTIVE",
                "deleted_at": None,
                "created_at": data.SEED_TIME,
                "updated_at": data.SEED_TIME,
                "current_revision_no": 1,
                "data_origin": "SYNTHETIC_DEV",
            }
        )
        revisions.append(
            {
                "profile_revision_id": spec.profile_revision_id,
                "parent_profile_id": spec.profile_id,
                "revision_no": 1,
                "age_months": spec.age_months,
                "age_band_ref": OUTDOOR_AGE_BAND_REF,
                "age_band_version": "v1",
                "display_name": spec.child_name,
                "interests_summary": spec.interests_summary,
                "authored_by_issuer": data.SEED_ISSUER,
                "authored_by_subject": spec.subject,
                "created_at": data.SEED_TIME,
                "revision_hash": snapshot.revision_hash(),
            }
        )
    return profiles, revisions


def _run_context(
    *,
    child_name: str,
    age_months: int,
    profile_revision_ref: str,
    interests_summary: str,
) -> dict[str, Any]:
    return {
        "schema_version": data.PARENT_CONTEXT_SCHEMA,
        "profile_revision_ref": profile_revision_ref,
        "display_name": child_name,
        "age_months": age_months,
        "age_band_ref": OUTDOOR_AGE_BAND_REF,
        "age_band_version": "v1",
        "interests_summary": interests_summary,
    }


def _story_bundle(
    *,
    tag: str,
    run_id: str,
    story_revision_id: str,
    title: str,
    subject_label: str,
    opening: str,
    middle: str,
    ending: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    story_content = {"opening": opening, "middle": middle, "ending": ending}
    scenes_spec = (
        ("Sân trường buổi sáng", f"Bé ngắm {subject_label} dưới ánh nắng nhẹ.", opening, 0),
        ("Tìm sắc màu quanh cây", "Bé chạm tay vào từng chiếc lá xanh mát.", middle, 12000),
        ("Cùng bạn chia sẻ niềm vui", "Bé kể lại điều mới khám phá ngoài trời.", middle, 24000),
        ("Khép lại bức tranh", f"Cả lớp nâng niu bức tranh {subject_label}.", ending, 36000),
    )
    scenes: list[dict[str, Any]] = []
    for index, (scene_title, action, narration, start_ms) in enumerate(scenes_spec, start=1):
        scenes.append(
            {
                "scene_id": s12_uuid_text(f"scene:{tag}:{index}"),
                "story_revision_id": story_revision_id,
                "scene_index": index,
                "title": scene_title,
                "action": action,
                "visual_prompt": f"Tranh màu nước thiếu nhi ấm áp: {action}",
                "narration": narration,
                "start_ms": start_ms,
                "duration_ms": 12000,
                "character_anchors": {"subject": subject_label},
            }
        )
    story_sha256 = data.sha256_json(
        {
            "title": title,
            "story": story_content,
            "scenes": [
                {
                    "scene_index": row["scene_index"],
                    "title": row["title"],
                    "action": row["action"],
                    "narration": row["narration"],
                    "start_ms": row["start_ms"],
                    "duration_ms": row["duration_ms"],
                }
                for row in scenes
            ],
        }
    )
    revision = {
        "story_revision_id": story_revision_id,
        "run_id": run_id,
        "revision_no": 1,
        "status": "CONFIRMED",
        "source_asset_sha256": sha256_text(f"{tag}:source-asset"),
        "understanding_revision": 1,
        "context_revision": 1,
        "story_sha256": story_sha256,
        "language": "vi",
        "title": title,
        "duration_ms": 48000,
        "story_content": story_content,
        "schema_version": "sketch2life.story-script.v1",
        "prompt_version": "s12-v1",
        "model_id": "seed-story-model",
        "model_revision": "2026-11",
        "request_sha256": sha256_text(f"{tag}:story-request"),
        "provider_call_id": None,
        "created_at": data.SEED_TIME,
    }
    return revision, scenes, story_sha256


def _receipt_row(
    *,
    tag: str,
    actor_scope_ref: str,
    operation: str,
    run_id: str,
    resource_version: int,
    response_body: dict[str, Any],
) -> dict[str, Any]:
    return {
        "receipt_id": s12_uuid_text(f"receipt:{tag}"),
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": actor_scope_ref,
        "operation": operation,
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": run_id,
        "idempotency_key_sha256": sha256_text(f"seed:s12:idem:{tag}"),
        "request_fingerprint_sha256": sha256_text(f"seed:s12:fp:{tag}"),
        "state": "FINAL",
        "response_status": 200,
        "response_resource_version": resource_version,
        "response_body": response_body,
        "resource_ref": run_id,
        "resource_version": resource_version,
        "state_version": 1,
        "created_at": data.SEED_TIME,
        "finalized_at": data.SEED_TIME,
    }


def _selection_row(
    *,
    tag: str,
    run_id: str,
    receipt_id: str,
    actor_scope_ref: str,
    selection_no: int,
    activity_index: int,
) -> dict[str, Any]:
    item = LESSON_ACTIVITIES[activity_index]
    ref = activity_ref(activity_index)
    snapshot = {
        "schema": "sketch2life.parent-activity-pin.v1",
        "activity_ref": ref,
        "title": item["title"],
        "objective": item["objective"],
        "materials_text": item["materials_text"],
        "preparation_text": item["preparation_text"],
        "instructions_text": item["instructions_text"],
        "observation_notes": item["observation_notes"],
        "safety_notes": item["safety_notes"],
        "activity_kind": item["activity_kind"],
        "source": "LIBRARY_CATALOG",
        "lesson_title": LESSON_CONTENT["title"],
        "lesson_topic": LESSON_CONTENT["topic"],
        "selected_at": data.SEED_TIME.isoformat(),
    }
    return {
        "selection_id": s12_uuid_text(f"selection:{tag}"),
        "run_id": run_id,
        "command_receipt_id": receipt_id,
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": actor_scope_ref,
        "selection_no": selection_no,
        "target_understanding_revision": 1,
        "source_kind": "LIBRARY_CATALOG",
        "activity_ref": ref,
        "activity_snapshot": snapshot,
        "activity_snapshot_sha256": data.sha256_json(snapshot),
        "created_at": data.SEED_TIME,
    }


def build_static_fixture_bundle() -> dict[str, list[dict[str, Any]]]:
    """Return deterministic S12 rows excluding runtime command outputs on RUN_STARTED."""

    p6 = PARENTS_BY_KEY["p6"]
    p7 = PARENTS_BY_KEY["p7"]
    k1_rev = data.current_profile_revision(REUSED_CHILD_KEY)
    p1_subject = data.PARENT_SUBJECTS[REUSED_PARENT_KEY]
    p1_scope = data.principal_scope_ref(data.SEED_ISSUER, p1_subject)

    sb_revision, sb_scenes, sb_sha = _story_bundle(
        tag="safety-blocked",
        run_id=RUN_SAFETY_BLOCKED_ID,
        story_revision_id=SAFETY_STORY_REV_ID,
        title="Bông hoa nhỏ đón nắng sớm",
        subject_label="Bông hoa nắng sớm",
        opening="Buổi sáng trong vườn, Su nhìn thấy bông hoa vàng khẽ rung trong gió.",
        middle="Ánh nắng dịu chiếu lên cánh hoa khiến bức vẽ của Su thêm rạng rỡ.",
        ending="Su mỉm cười mang bức tranh hoa tặng cô giáo và cả nhà.",
    )
    comp_revision, comp_scenes, comp_sha = _story_bundle(
        tag="completed",
        run_id=RUN_COMPLETED_ID,
        story_revision_id=COMPLETED_STORY_REV_ID,
        title="Mít khám phá tán lá xanh",
        subject_label="Tán lá xanh công viên",
        opening="Mít chạy quanh tán cây xanh mát và nhặt chiếc lá hình trái tim.",
        middle="Ánh nắng xuyên qua kẽ lá tạo nên những đốm sáng nhảy múa trên sân.",
        ending="Mít vẽ lại tán lá xanh để giữ kỷ niệm buổi dạo chơi thật vui.",
    )

    started_ctx = _run_context(
        child_name=p6.child_name,
        age_months=p6.age_months,
        profile_revision_ref=str(p6.profile_revision_id),
        interests_summary=p6.interests_summary,
    )
    sb_ctx = _run_context(
        child_name=p7.child_name,
        age_months=p7.age_months,
        profile_revision_ref=str(p7.profile_revision_id),
        interests_summary=p7.interests_summary,
    )
    comp_ctx = _run_context(
        child_name=str(k1_rev["display_name"]),
        age_months=int(k1_rev["age_months"]),
        profile_revision_ref=str(k1_rev["profile_revision_id"]),
        interests_summary=str(k1_rev["interests_summary"] or ""),
    )

    runs = [
        {
            "run_id": RUN_STARTED_ID,
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": p6.scope_ref,
            "profile_ref": str(p6.profile_id),
            "child_age_months": p6.age_months,
            "run_state": "PREPARATION_REVIEW",
            "revision": 1,
            "version": 1,
            "retryable": False,
            "active_owner_parent_account_id": p6.account_id,
            "current_input_revision": 1,
            "understanding_revision": 1,
            "subject_label": "Cây xanh sân trường",
            "job_state": "SUCCEEDED",
            "adult_wait_started_at": data.SEED_TIME,
            "created_at": data.SEED_TIME,
            "updated_at": data.SEED_TIME,
        },
        {
            "run_id": RUN_SAFETY_BLOCKED_ID,
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": p7.scope_ref,
            "profile_ref": str(p7.profile_id),
            "child_age_months": p7.age_months,
            "run_state": "SCRIPT_REVIEW",
            "revision": 4,
            "version": 4,
            "retryable": False,
            "active_owner_parent_account_id": p7.account_id,
            "current_input_revision": 1,
            "understanding_revision": 1,
            "subject_label": "Bông hoa nắng sớm",
            "current_video_generation_id": SAFETY_VIDEO_GEN_ID,
            "job_state": "SUCCEEDED",
            "error_code": "SAFETY_BLOCKED",
            "adult_wait_started_at": data.SEED_TIME,
            "created_at": data.SEED_TIME,
            "updated_at": data.SEED_TIME,
        },
        {
            "run_id": RUN_COMPLETED_ID,
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": p1_scope,
            "profile_ref": str(data.parent_profile_id(REUSED_CHILD_KEY)),
            "child_age_months": int(k1_rev["age_months"]),
            "run_state": "COMPLETED",
            "revision": 7,
            "version": 7,
            "retryable": False,
            "active_owner_parent_account_id": None,
            "current_input_revision": 1,
            "understanding_revision": 1,
            "subject_label": "Tán lá xanh công viên",
            "current_video_generation_id": COMPLETED_VIDEO_READY_ID,
            "job_state": "SUCCEEDED",
            "error_code": None,
            "created_at": data.SEED_TIME,
            "updated_at": data.SEED_TIME,
            "finished_at": data.SEED_TIME,
        },
    ]

    run_inputs = [
        {
            "run_input_id": s12_uuid_text("run-input:started"),
            "run_id": RUN_STARTED_ID,
            "input_revision": 1,
            "topic": "Thiên nhiên sân trường",
            "adult_confirmed_idea": "Bé vẽ cây xanh sân trường đón nắng mai",
            "typed_idea": "Bé vẽ cây xanh sân trường đón nắng mai",
            "idea_source": "TEXT",
            "original_asset_ref": "seed/s12/run-started/drawing-orig.png",
            "original_asset_version": 1,
            "original_sha256": sha256_text("started:orig"),
            "original_media_type": "image/png",
            "original_size_bytes": 2048,
            "derived_asset_ref": "seed/s12/run-started/drawing-derived.png",
            "derived_asset_version": 1,
            "derived_sha256": sha256_text("started:derived"),
            "derived_media_type": "image/png",
            "derived_size_bytes": 1024,
            "source_profile_revision_ref": str(p6.profile_revision_id),
            "context_revision": 1,
            "context_snapshot": started_ctx,
            "context_snapshot_sha256": data.sha256_json(started_ctx),
            "context_confirmed_by": None,
            "context_confirmed_at": None,
            "created_at": data.SEED_TIME,
        },
        {
            "run_input_id": s12_uuid_text("run-input:safety-blocked"),
            "run_id": RUN_SAFETY_BLOCKED_ID,
            "input_revision": 1,
            "topic": "Vườn hoa buổi sáng",
            "adult_confirmed_idea": "Bé kể chuyện bông hoa nắng sớm trong vườn",
            "typed_idea": "Bé kể chuyện bông hoa nắng sớm trong vườn",
            "idea_source": "TEXT",
            "original_asset_ref": "seed/s12/run-safety-blocked/drawing-orig.png",
            "original_asset_version": 1,
            "original_sha256": sha256_text("safety-blocked:orig"),
            "original_media_type": "image/png",
            "original_size_bytes": 2048,
            "derived_asset_ref": "seed/s12/run-safety-blocked/drawing-derived.png",
            "derived_asset_version": 1,
            "derived_sha256": sha256_text("safety-blocked:derived"),
            "derived_media_type": "image/png",
            "derived_size_bytes": 1024,
            "source_profile_revision_ref": str(p7.profile_revision_id),
            "context_revision": 1,
            "context_snapshot": sb_ctx,
            "context_snapshot_sha256": data.sha256_json(sb_ctx),
            "context_confirmed_by": p7.scope_ref,
            "context_confirmed_at": data.SEED_TIME,
            "created_at": data.SEED_TIME,
        },
        {
            "run_input_id": s12_uuid_text("run-input:completed"),
            "run_id": RUN_COMPLETED_ID,
            "input_revision": 1,
            "topic": "Công viên cây xanh",
            "adult_confirmed_idea": "Mít vẽ tán lá xanh sau buổi dạo công viên",
            "typed_idea": "Mít vẽ tán lá xanh sau buổi dạo công viên",
            "idea_source": "TEXT",
            "original_asset_ref": "seed/s12/run-completed/drawing-orig.png",
            "original_asset_version": 1,
            "original_sha256": sha256_text("completed:orig"),
            "original_media_type": "image/png",
            "original_size_bytes": 2048,
            "derived_asset_ref": "seed/s12/run-completed/drawing-derived.png",
            "derived_asset_version": 1,
            "derived_sha256": sha256_text("completed:derived"),
            "derived_media_type": "image/png",
            "derived_size_bytes": 1024,
            "source_profile_revision_ref": str(k1_rev["profile_revision_id"]),
            "context_revision": 1,
            "context_snapshot": comp_ctx,
            "context_snapshot_sha256": data.sha256_json(comp_ctx),
            "context_confirmed_by": p1_scope,
            "context_confirmed_at": data.SEED_TIME,
            "created_at": data.SEED_TIME,
        },
    ]

    understanding_specs = (
        ("started", RUN_STARTED_ID, run_inputs[0]["run_input_id"], "Cây xanh sân trường", ["cây xanh", "lá rụng", "sân trường"]),
        ("safety-blocked", RUN_SAFETY_BLOCKED_ID, run_inputs[1]["run_input_id"], "Bông hoa nắng sớm", ["bông hoa", "nắng sớm", "vườn cây"]),
        ("completed", RUN_COMPLETED_ID, run_inputs[2]["run_input_id"], "Tán lá xanh công viên", ["tán lá xanh", "công viên", "cây cối"]),
    )
    understandings: list[dict[str, Any]] = []
    for tag, run_id, run_input_id, label, features in understanding_specs:
        snapshot = {"result": {"subject_label": label, "visible_features": features}}
        understandings.append(
            {
                "understanding_revision_id": s12_uuid_text(f"understanding:{tag}"),
                "run_id": run_id,
                "run_input_id": run_input_id,
                "revision_no": 1,
                "subject_label": label,
                "confidence": 0.96,
                "canonical_result_sha256": data.sha256_json(snapshot),
                "raw_body_sha256": data.sha256_json(snapshot),
                "result_snapshot": snapshot,
                "created_at": data.SEED_TIME,
            }
        )

    subject_receipt_specs = (
        ("started:subj", p6.scope_ref, RUN_STARTED_ID),
        ("safety-blocked:subj", p7.scope_ref, RUN_SAFETY_BLOCKED_ID),
        ("completed:subj", p1_scope, RUN_COMPLETED_ID),
    )
    receipts: list[dict[str, Any]] = [
        _receipt_row(
            tag=tag,
            actor_scope_ref=scope_ref,
            operation="CONFIRM_SUBJECT",
            run_id=run_id,
            resource_version=1,
            response_body={"decision": "CONFIRM", "understanding_revision": 1},
        )
        for tag, scope_ref, run_id in subject_receipt_specs
    ]
    review_decisions = [
        {
            "decision_id": s12_uuid_text(f"review-decision:{tag}"),
            "run_id": run_id,
            "command_receipt_id": s12_uuid_text(f"receipt:{tag}"),
            "stage": "SUBJECT",
            "decision": "CONFIRM",
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": scope_ref,
            "target_understanding_revision": 1,
            "created_at": data.SEED_TIME,
        }
        for tag, scope_ref, run_id in subject_receipt_specs
    ]

    sb_select_receipt = _receipt_row(
        tag="safety-blocked:select",
        actor_scope_ref=p7.scope_ref,
        operation="SELECT_ACTIVITY",
        run_id=RUN_SAFETY_BLOCKED_ID,
        resource_version=2,
        response_body={"selection_no": 1},
    )
    sb_confirm_receipt = _receipt_row(
        tag="safety-blocked:confirm-1",
        actor_scope_ref=p7.scope_ref,
        operation="CONFIRM_STORY_REVISION",
        run_id=RUN_SAFETY_BLOCKED_ID,
        resource_version=3,
        response_body={"decision": "CONFIRMED", "revision": 1},
    )
    comp_select_receipt = _receipt_row(
        tag="completed:select",
        actor_scope_ref=p1_scope,
        operation="SELECT_ACTIVITY",
        run_id=RUN_COMPLETED_ID,
        resource_version=2,
        response_body={"selection_no": 1},
    )
    comp_confirm_receipt_1 = _receipt_row(
        tag="completed:confirm-1",
        actor_scope_ref=p1_scope,
        operation="CONFIRM_STORY_REVISION",
        run_id=RUN_COMPLETED_ID,
        resource_version=3,
        response_body={"decision": "CONFIRMED", "revision": 1},
    )
    comp_confirm_receipt_2 = _receipt_row(
        tag="completed:confirm-2",
        actor_scope_ref=p1_scope,
        operation="CONFIRM_STORY_REVISION",
        run_id=RUN_COMPLETED_ID,
        resource_version=5,
        response_body={"decision": "CONFIRMED", "revision": 1},
    )
    receipts.extend(
        [
            sb_select_receipt,
            sb_confirm_receipt,
            comp_select_receipt,
            comp_confirm_receipt_1,
            comp_confirm_receipt_2,
        ]
    )

    activity_selections = [
        _selection_row(
            tag="safety-blocked:1",
            run_id=RUN_SAFETY_BLOCKED_ID,
            receipt_id=sb_select_receipt["receipt_id"],
            actor_scope_ref=p7.scope_ref,
            selection_no=1,
            activity_index=0,
        ),
        _selection_row(
            tag="completed:1",
            run_id=RUN_COMPLETED_ID,
            receipt_id=comp_select_receipt["receipt_id"],
            actor_scope_ref=p1_scope,
            selection_no=1,
            activity_index=1,
        ),
    ]

    story_revision_reviews = [
        {
            "review_id": SAFETY_REVIEW_ID,
            "run_id": RUN_SAFETY_BLOCKED_ID,
            "story_revision_id": SAFETY_STORY_REV_ID,
            "command_receipt_id": sb_confirm_receipt["receipt_id"],
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": p7.scope_ref,
            "decision": "CONFIRM",
            "target_story_sha256": sb_sha,
            "review_epoch": 1,
            "created_at": data.SEED_TIME,
        },
        {
            "review_id": COMPLETED_REVIEW_EPOCH_1_ID,
            "run_id": RUN_COMPLETED_ID,
            "story_revision_id": COMPLETED_STORY_REV_ID,
            "command_receipt_id": comp_confirm_receipt_1["receipt_id"],
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": p1_scope,
            "decision": "CONFIRM",
            "target_story_sha256": comp_sha,
            "review_epoch": 1,
            "created_at": data.SEED_TIME,
        },
        {
            "review_id": COMPLETED_REVIEW_EPOCH_2_ID,
            "run_id": RUN_COMPLETED_ID,
            "story_revision_id": COMPLETED_STORY_REV_ID,
            "command_receipt_id": comp_confirm_receipt_2["receipt_id"],
            "actor_scope_kind": "PARENT_ACCOUNT",
            "actor_scope_ref": p1_scope,
            "decision": "CONFIRM",
            "target_story_sha256": comp_sha,
            "review_epoch": 2,
            "created_at": data.SEED_TIME,
        },
    ]

    video_generations = [
        {
            "video_generation_id": SAFETY_VIDEO_GEN_ID,
            "story_run_id": RUN_SAFETY_BLOCKED_ID,
            "story_revision_id": SAFETY_STORY_REV_ID,
            "story_review_id": SAFETY_REVIEW_ID,
            "generation_no": 1,
            "generation_kind": "INITIAL",
            "state": "SAFETY_BLOCKED",
            "request_idempotency_key_hash": sha256_text("vg:safety-blocked:key"),
            "request_fingerprint_sha256": sha256_text("vg:safety-blocked:fp"),
            "target_script_hash": sb_sha,
            "quality_reason_code": None,
            "technical_validation_state": "PASSED",
            "consistency_validation_state": "PASSED",
            "safety_validation_state": "FAILED",
            "safety_finding_codes": ["CHILD_SAFETY_REVIEW"],
            "safe_failure_code": "SAFETY_BLOCKED",
            "admission_started_at": data.SEED_TIME,
            "accepted_at": data.SEED_TIME,
            "started_at": data.SEED_TIME,
            "completed_at": data.SEED_TIME,
            "generation_revision": 5,
            "created_at": data.SEED_TIME,
            "updated_at": data.SEED_TIME,
        },
        {
            "video_generation_id": COMPLETED_VIDEO_SPENT_ID,
            "story_run_id": RUN_COMPLETED_ID,
            "story_revision_id": COMPLETED_STORY_REV_ID,
            "story_review_id": COMPLETED_REVIEW_EPOCH_1_ID,
            "generation_no": 1,
            "generation_kind": "INITIAL",
            "state": "FAILED",
            "request_idempotency_key_hash": sha256_text("vg:completed-spent:key"),
            "request_fingerprint_sha256": sha256_text("vg:completed-spent:fp"),
            "target_script_hash": comp_sha,
            "quality_reason_code": None,
            "technical_validation_state": "FAILED",
            "safe_failure_code": "VIDEO_TECHNICAL_FAILURE",
            "admission_started_at": data.SEED_TIME,
            "accepted_at": data.SEED_TIME,
            "started_at": data.SEED_TIME,
            "completed_at": data.SEED_TIME,
            "generation_revision": 4,
            "created_at": data.SEED_TIME,
            "updated_at": data.SEED_TIME,
        },
        {
            "video_generation_id": COMPLETED_VIDEO_READY_ID,
            "story_run_id": RUN_COMPLETED_ID,
            "story_revision_id": COMPLETED_STORY_REV_ID,
            "story_review_id": COMPLETED_REVIEW_EPOCH_2_ID,
            "generation_no": 2,
            "generation_kind": "QUALITY_REGEN",
            "state": "READY",
            "request_idempotency_key_hash": sha256_text("vg:completed-ready:key"),
            "request_fingerprint_sha256": sha256_text("vg:completed-ready:fp"),
            "target_script_hash": comp_sha,
            "quality_reason_code": QUALITY_REASON_CODE,
            "technical_validation_state": "PASSED",
            "consistency_validation_state": "PASSED",
            "safety_validation_state": "PASSED",
            "output_asset_ref": COMPLETED_VIDEO_ASSET_REF,
            "output_asset_version": 1,
            "admission_started_at": data.SEED_TIME,
            "accepted_at": data.SEED_TIME,
            "started_at": data.SEED_TIME,
            "completed_at": data.SEED_TIME,
            "generation_revision": 6,
            "created_at": data.SEED_TIME,
            "updated_at": data.SEED_TIME,
        },
    ]

    video_generation_scenes = [
        {
            "generation_scene_id": s12_uuid_text(f"vg-scene:sb:{row['scene_index']}"),
            "video_generation_id": SAFETY_VIDEO_GEN_ID,
            "story_revision_id": SAFETY_STORY_REV_ID,
            "story_scene_id": row["scene_id"],
            "state": "READY",
            "created_at": data.SEED_TIME,
            "started_at": data.SEED_TIME,
            "completed_at": data.SEED_TIME,
        }
        for row in sb_scenes
    ] + [
        {
            "generation_scene_id": s12_uuid_text(f"vg-scene:comp:{row['scene_index']}"),
            "video_generation_id": COMPLETED_VIDEO_READY_ID,
            "story_revision_id": COMPLETED_STORY_REV_ID,
            "story_scene_id": row["scene_id"],
            "state": "READY",
            "created_at": data.SEED_TIME,
            "started_at": data.SEED_TIME,
            "completed_at": data.SEED_TIME,
        }
        for row in comp_scenes
    ]

    return {
        "runs": runs,
        "run_inputs": run_inputs,
        "understandings": understandings,
        "receipts": receipts,
        "review_decisions": review_decisions,
        "activity_selections": activity_selections,
        "story_revisions": [sb_revision, comp_revision],
        "story_scenes": sb_scenes + comp_scenes,
        "story_revision_reviews": story_revision_reviews,
        "video_generations": video_generations,
        "video_generation_scenes": video_generation_scenes,
    }


RUN_IDS: Final[tuple[str, str, str]] = (
    RUN_STARTED_ID,
    RUN_SAFETY_BLOCKED_ID,
    RUN_COMPLETED_ID,
)

# Exact S12-owned totals: 3 static receipts on S12 runs plus 3 runtime command receipts
# (2 activity selections + 1 confirm_context) and 1 started story revision on RUN_STARTED.
EXPECTED: Final[dict[str, int]] = {
    "be1_adult_identities": 2,
    "parent_child_profiles": 2,
    "parent_profile_revisions": 2,
    "lesson_library_items": 1,
    "lesson_library_versions": 1,
    "lesson_version_activities": 2,
    "lesson_access_grants": 1,
    "story_runs": 3,
    "story_run_inputs": 3,
    "story_understanding_revisions": 3,
    "story_review_decisions": 3,
    "story_activity_selections": 4,
    "story_revisions": 3,
    "story_scenes": 8,
    "story_revision_reviews": 3,
    "story_video_generations": 3,
    "story_video_generation_scenes": 8,
    "story_command_receipts": 11,
}
