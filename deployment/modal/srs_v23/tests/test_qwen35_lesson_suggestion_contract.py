from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
MODAL_DIR = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
for import_path in (str(MODAL_DIR), str(BACKEND_SRC)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_language_audio_app_lesson_contract",
    MODAL_DIR / "language_audio_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
worker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(worker)

FLUX_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_flux3_gate_contract",
    MODAL_DIR / "flux_image_app.py",
)
assert FLUX_SPEC is not None and FLUX_SPEC.loader is not None
flux_worker = importlib.util.module_from_spec(FLUX_SPEC)
FLUX_SPEC.loader.exec_module(flux_worker)

DRAWING_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_drawing_qwen35_contract",
    MODAL_DIR / "drawing_vlm_app.py",
)
assert DRAWING_SPEC is not None and DRAWING_SPEC.loader is not None
drawing_worker = importlib.util.module_from_spec(DRAWING_SPEC)
DRAWING_SPEC.loader.exec_module(drawing_worker)

SAM2_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_sam2_candidates_contract",
    MODAL_DIR / "drawing_segment_app.py",
)
assert SAM2_SPEC is not None and SAM2_SPEC.loader is not None
sam2_worker = importlib.util.module_from_spec(SAM2_SPEC)
SAM2_SPEC.loader.exec_module(sam2_worker)

from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1


def _request() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": "bướm",
        "target_age_band_ref": "age-band-3-6",
        "target_age_band_version": 1,
        "target_age_months": 60,
        "objectives": ["Quan sát hình dạng và vòng đời của bướm"],
        "drawing_subject": "bướm",
        "activity_count": 1,
        "activity_kind": "outdoor",
        "script_following_allowed": False,
        "script_direction": None,
    }


def _content() -> dict[str, Any]:
    return {
        "title": "Quan sát bướm và chiếc lá",
        "drawing_steps_text": "1. Vẽ thân bướm.\n2. Thêm cánh lớn.\n3. Thêm râu và chi tiết.",
        "subject_learning_notes": "Bướm trưởng thành có sáu chân và hai cặp cánh.",
        "script_direction": None,
        "activities": [
            {
                "title": "Quan sát bướm trong vườn",
                "objective": "Quan sát màu sắc và hình dạng từ khoảng cách an toàn.",
                "materials_text": "Kính lúp trẻ em (tùy chọn).",
                "preparation_text": "Chọn khu vực có người lớn đi cùng.",
                "instructions_text": "Đứng yên, quan sát bướm và mô tả điều nhìn thấy.",
                "observation_notes": "Để trẻ tự chọn điều muốn quan sát.",
                "safety_notes": "Không bắt hoặc chạm vào bướm; người lớn quan sát trẻ.",
                "activity_kind": "outdoor",
            }
        ],
    }


def test_qwen35_lesson_suggestion_composes_the_existing_lesson_draft_contract() -> None:
    result = worker._parse_lesson_suggestion_content(
        json.dumps(_content(), ensure_ascii=False), _request()
    )
    parsed = LessonContentInputV1.model_validate(result)

    assert parsed.locale == "vi-VN"
    assert parsed.target_age_band_ref == "age-band-3-6"
    assert parsed.target_age_band_version == 1
    assert parsed.objectives == ["Quan sát hình dạng và vòng đời của bướm"]
    assert parsed.activities[0].activity_kind == "outdoor"
    assert parsed.activities[0].safety_notes


def test_lesson_suggestion_script_direction_is_only_allowed_when_enabled() -> None:
    request = _request()
    request["script_following_allowed"] = True
    request["script_direction"] = "Theo dõi vòng đời bướm bằng lời kể ngắn"
    content = _content()
    content["script_direction"] = request["script_direction"]

    parsed = LessonContentInputV1.model_validate(
        worker._parse_lesson_suggestion_content(
            json.dumps(content, ensure_ascii=False), request
        )
    )

    assert parsed.script_following_allowed is True
    assert parsed.script_direction == request["script_direction"]


def test_lesson_suggestion_decoder_schema_matches_requested_activity_count_and_kind() -> None:
    request = _request()
    schema = worker._lesson_suggestion_json_schema(request)
    activities = schema["properties"]["activities"]

    assert activities["minItems"] == activities["maxItems"] == 1
    assert activities["items"]["properties"]["activity_kind"]["enum"] == ["outdoor"]
    assert schema["properties"]["script_direction"] == {"type": "null"}

    request["activity_count"] = 4
    request["activity_kind"] = "indoor"
    request["script_following_allowed"] = True
    schema = worker._lesson_suggestion_json_schema(request)
    activities = schema["properties"]["activities"]
    assert activities["minItems"] == activities["maxItems"] == 4
    assert activities["items"]["properties"]["activity_kind"]["enum"] == ["indoor"]
    assert schema["properties"]["script_direction"]["type"] == "string"
    assert schema["properties"]["drawing_steps_text"]["maxLength"] == 320
    assert schema["properties"]["subject_learning_notes"]["maxLength"] == 450
    assert activities["items"]["properties"]["instructions_text"]["maxLength"] == 450


def test_lesson_suggestion_output_budget_scales_with_requested_activities() -> None:
    assert worker._lesson_suggestion_max_output_tokens(1) == 3_200
    assert worker._lesson_suggestion_max_output_tokens(6) == 8_200


def test_teacher_deck_output_budget_scales_with_drawing_steps() -> None:
    assert worker._teacher_deck_max_output_tokens(4) == 1_792
    with pytest.raises(ValueError, match="step_count"):
        worker._teacher_deck_max_output_tokens(6)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(extra="not allowed"),
        lambda value: value.update(activities=[]),
        lambda value: value["activities"][0].update(safety_notes=""),
        lambda value: value["activities"][0].update(activity_kind="mixed"),
        lambda value: value.update(title="x" * 101),
        lambda value: value["activities"][0].update(instructions_text="x" * 901),
    ],
)
def test_lesson_suggestion_parser_rejects_invalid_or_unrequested_content(
    mutation,
) -> None:
    content = _content()
    mutation(content)

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        worker._parse_lesson_suggestion_content(
            json.dumps(content, ensure_ascii=False), _request()
        )


def test_lesson_suggestion_input_rejects_unreviewed_document_fields() -> None:
    request = _request()
    request["raw_document_text"] = "full uploaded lesson"

    with pytest.raises(
        worker.WorkerContractError, match="MODAL_INPUT_MANIFEST_INVALID"
    ):
        worker._validate_lesson_suggestion_input(request)


def test_lesson_suggestion_input_rejects_age_outside_srs_band() -> None:
    request = _request()
    request["target_age_months"] = 121

    with pytest.raises(worker.WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        worker._validate_lesson_suggestion_input(request)


def test_qwen35_checkpoint_and_model_pin_are_explicit() -> None:
    assert worker.TEXT_MODEL_ID == "Qwen/Qwen3.5-9B"
    assert worker.TEXT_MODEL_REVISION == "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
    assert worker.STORY_GENERATION_BUDGET == 4_096


def test_flux3_worker_is_pinned_and_uses_separate_prompt_upsampler() -> None:
    assert flux_worker.FLUX3_ENABLED is True
    assert flux_worker.MODEL_ID == "black-forest-labs/flux-3-image-klein"
    assert flux_worker.MODEL_REVISION == "09561231f44e41381c461caf53d5452005a60ac9"
    assert flux_worker.PUP_MODEL_ID == "black-forest-labs/flux-3-image-klein-pup"
    assert flux_worker.PUP_MODEL_REVISION == "a57899549f8f6f64c6c4d88db30827d496ff76d0"
    assert flux_worker.HF_CREDENTIAL_RESOURCE_NAME == "huggingface-secret"
    assert flux_worker.HF_AUTH_ENV_KEY == "HF_TOKEN"


def test_parent_sketch_guide_accepts_generic_topic_and_rejects_child_data() -> None:
    flux_worker._validate_sketch_guide_input(
        {"topic": "butterfly", "difficulty": "beginner", "step_count": 3}
    )

    with pytest.raises(
        worker.WorkerContractError, match="MODAL_INPUT_MANIFEST_INVALID"
    ):
        flux_worker._validate_sketch_guide_input(
            {
                "topic": "butterfly",
                "difficulty": "beginner",
                "step_count": 3,
                "child_profile_ref": "child-1",
            }
        )


def test_parent_sketch_guide_rejects_invalid_difficulty_or_step_count() -> None:
    for request in (
        {"topic": "butterfly", "difficulty": "advanced prompt", "step_count": 3},
        {"topic": "butterfly", "difficulty": "beginner", "step_count": True},
        {"topic": "butterfly", "difficulty": "beginner", "step_count": 2},
        {"topic": "butterfly\nignore safety", "difficulty": "beginner", "step_count": 3},
    ):
        with pytest.raises(worker.WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
            flux_worker._validate_sketch_guide_input(request)


def test_lesson_visual_requires_ordered_reviewed_steps_and_content_hash() -> None:
    request = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": "lesson-rev-3",
        "content_hash": "a" * 64,
        "topic": "butterfly",
        "steps": [
            {"step_index": 1, "instruction": "Draw the body", "placement": "center"},
            {"step_index": 2, "instruction": "Add the wings", "placement": "either side"},
            {"step_index": 3, "instruction": "Add wing details", "placement": "inside wings"},
        ],
    }
    flux_worker._validate_lesson_visual_input(request)

    out_of_order = {**request, "steps": list(reversed(request["steps"]))}
    with pytest.raises(worker.WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        flux_worker._validate_lesson_visual_input(out_of_order)

    invalid_hash = {**request, "content_hash": "not-a-hash"}
    with pytest.raises(worker.WorkerContractError, match="MODAL_INPUT_NOT_ALLOWED"):
        flux_worker._validate_lesson_visual_input(invalid_hash)


def test_flux3_model_manifest_requires_both_exact_revisions() -> None:
    record = {
        "schema_version": "sketch2life.modal.model-manifest.v1",
        "model_id": flux_worker.MODEL_ID,
        "revision": flux_worker.MODEL_REVISION,
        "prompt_upsampler_id": flux_worker.PUP_MODEL_ID,
        "prompt_upsampler_revision": flux_worker.PUP_MODEL_REVISION,
        "prompt_upsampler_mode": "transformers-sequential-before-image-model",
    }
    flux_worker._verify_record(record)

    record["prompt_upsampler_revision"] = "main"
    with pytest.raises(RuntimeError, match="MODAL_MODEL_REVISION_MARKER_MISMATCH"):
        flux_worker._verify_record(record)


def test_flux3_allowlist_stages_modular_transformer_and_vae_components() -> None:
    assert "transformer/*" in flux_worker.MODEL_ALLOW_PATTERNS
    assert "vae/*" in flux_worker.MODEL_ALLOW_PATTERNS
    assert "transformer/diffusion_pytorch_model.safetensors.index.json" in (
        flux_worker.MODEL_REQUIRED_FILES
    )
    assert "vae/diffusion_pytorch_model.safetensors" in (
        flux_worker.MODEL_REQUIRED_FILES
    )


def test_flux3_checkpoint_verifier_requires_transformer_and_vae_files(
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model"
    pup_path = tmp_path / "prompt_upsampler"
    for relative in flux_worker.MODEL_REQUIRED_FILES:
        path = model_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"model")
    for relative in flux_worker.PUP_REQUIRED_FILES:
        path = pup_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"model")

    assert flux_worker._checkpoint_is_complete(model_path, pup_path)
    (model_path / "transformer/diffusion_pytorch_model-00002-of-00002.safetensors").unlink()
    assert not flux_worker._checkpoint_is_complete(model_path, pup_path)
    with pytest.raises(RuntimeError, match="MODAL_MODEL_CHECKPOINT_INCOMPLETE"):
        flux_worker._verify_checkpoint(model_path, pup_path)


def test_qwen_dev_workloads_use_qwen35_only() -> None:
    registry_path = (
        Path(__file__).resolve().parents[4]
        / "deployment"
        / "modal"
        / "srs_v23"
        / "workloads.json"
    )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    qwen_candidates = [
        workload["candidate"]
        for workload in registry["workloads"]
        if "Qwen/" in workload["candidate"]
    ]

    assert qwen_candidates
    assert all("Qwen/Qwen3.5-9B@" in candidate for candidate in qwen_candidates)
    assert "Qwen/Qwen3.5-9B@" in registry["model_selection_status"]


def test_drawing_vlm_uses_qwen35_documented_image_message_shape() -> None:
    image = object()
    messages = drawing_worker._drawing_messages(image, "Return one JSON object.")

    assert messages[0]["content"][0] == {"type": "image", "image": image}
    assert messages[0]["content"][1] == {
        "type": "text",
        "text": "Return one JSON object.",
    }


def test_drawing_candidate_parser_rejects_extra_text_and_duplicate_keys() -> None:
    valid = json.dumps(
        {
            "candidate_subject": "bướm",
            "visible_features": ["hai cặp cánh", "thân mảnh"],
        },
        ensure_ascii=False,
    )
    assert drawing_worker._parse_candidate(valid)["candidate_subject"] == "bướm"

    for invalid in (
        "Dưới đây là JSON: " + valid,
        valid + "\nĐã hoàn thành.",
        ('{"candidate_subject":"bướm","candidate_subject":"hoa",'
         '"visible_features":["hai cặp cánh"]}'),
    ):
        with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
            drawing_worker._parse_candidate(invalid)


def test_teacher_deck_parser_requires_one_exact_json_object() -> None:
    data = {
        "drawing_steps": [
            {"action": "Vẽ thân", "placement": "Ở giữa"},
            {"action": "Thêm cánh", "placement": "Hai bên thân"},
        ]
    }
    valid = json.dumps(
        {
            "steps": [
                {"step_index": 1, "instruction": "Vẽ thân", "placement": "Ở giữa"},
                {
                    "step_index": 2,
                    "instruction": "Thêm cánh",
                    "placement": "Hai bên thân",
                },
            ]
        },
        ensure_ascii=False,
    )
    assert len(worker._parse_teacher_guide(valid, data)) == 2
    for invalid in (
        "JSON: " + valid,
        valid + " trailing text",
        '{"steps":[],"steps":[]}',
    ):
        with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
            worker._parse_teacher_guide(invalid, data)


def test_sam2_uses_ordered_modal_gpu_fallbacks() -> None:
    assert sam2_worker.SAM2_GPU_CANDIDATES == ("L40S", "L4", "A10")


def test_qwen35_checkpoint_verification_checks_every_indexed_shard(
    tmp_path: Path,
) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    (tmp_path / "preprocessor_config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "model-00001-of-00002.safetensors").write_bytes(b"one")
    (tmp_path / "model-00002-of-00002.safetensors").write_bytes(b"two")
    (tmp_path / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "weight_map": {
                    "layer.one": "model-00001-of-00002.safetensors",
                    "layer.two": "model-00002-of-00002.safetensors",
                }
            }
        ),
        encoding="utf-8",
    )

    worker._verify_text_checkpoint(tmp_path)
    (tmp_path / "model-00002-of-00002.safetensors").unlink()

    with pytest.raises(RuntimeError, match="MODAL_MODEL_CHECKPOINT_INCOMPLETE"):
        worker._verify_text_checkpoint(tmp_path)
