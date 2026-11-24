from __future__ import annotations

import ast
from pathlib import Path

MODAL_DIR = Path(__file__).resolve().parents[1]
VIDEO_APP_PATH = MODAL_DIR / "video_app.py"
VIDEO_SOURCE = VIDEO_APP_PATH.read_text(encoding="utf-8")
VIDEO_TREE = ast.parse(VIDEO_SOURCE)


def _assignment(name: str) -> ast.AST:
    for node in VIDEO_TREE.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    raise AssertionError(f"missing module assignment: {name}")


def _function(name: str) -> ast.FunctionDef:
    for node in VIDEO_TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing worker function: {name}")


def _call_decorator(function: ast.FunctionDef, name: str) -> ast.Call:
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == name:
            return decorator
    raise AssertionError(f"missing {name} decorator on {function.name}")


def _keyword_values(call: ast.Call) -> dict[str, ast.AST]:
    return {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg}


def test_silent_story_worker_is_pinned_and_runs_only_on_l40s() -> None:
    assert ast.literal_eval(_assignment("APP_NAME")) == "sketch2life-srs23-dev-video"
    assert ast.literal_eval(_assignment("MODEL_ID")) == "Lightricks/LTX-2.5"
    assert ast.literal_eval(_assignment("MODEL_REVISION")) == (
        "49b093a39c19169a8a81721dcc541e07e945232f"
    )

    worker = _function("generate_silent_story_video")
    modal_config = _keyword_values(_call_decorator(worker, "app.function"))
    assert ast.literal_eval(modal_config["name"]) == "generate-silent-story-video"
    assert ast.literal_eval(modal_config["gpu"]) == "L40S"
    assert ast.literal_eval(modal_config["min_containers"]) == 0
    assert ast.literal_eval(modal_config["max_containers"]) == 1
    assert ast.literal_eval(modal_config["timeout"]) == 1_800
    assert ast.literal_eval(modal_config["retries"]) == 0

    observer = _keyword_values(_call_decorator(worker, "observed_worker"))
    assert ast.literal_eval(observer["workload"]) == "video.story.generate"
    assert "model_volume.with_mount_options(read_only=True)" in ast.unparse(
        modal_config["volumes"]
    )
    assert "scratch_volume" in ast.unparse(modal_config["volumes"])


def test_ltx_start_conditioning_is_always_a_hard_replace_at_frame_zero() -> None:
    run_ltx = _function("_run_ltx")
    calls = [
        ast.unparse(node)
        for node in ast.walk(run_ltx)
        if isinstance(node, ast.Call)
    ]
    replace_call = next(
        call for call in calls if call.startswith("ImageConditioningInput.replace(")
    )
    assert "frame_idx=0" in replace_call
    assert "strength=1.0" in replace_call
    # FEAT-087: an end keyframe is a soft guide, built only by the dedicated helper.
    assert not any(call.startswith("ImageConditioningInput.guide(") for call in calls)
    helper = ast.unparse(_function("_end_frame_conditioning"))
    assert "ImageConditioningInput.guide(" in helper and "num_frames - 1" in helper
    assert "images=[conditioning, *end_conditioning]" in VIDEO_SOURCE
    assert "story_image_guides" not in VIDEO_SOURCE


def test_silent_story_worker_never_enables_warm_gpu_or_retries() -> None:
    worker = _function("generate_silent_story_video")
    config = _keyword_values(_call_decorator(worker, "app.function"))
    assert ast.literal_eval(config["min_containers"]) == 0
    assert ast.literal_eval(config["retries"]) == 0
    assert '"product_playable": False' in VIDEO_SOURCE
    assert '"safety_validation": "NOT_RUN"' in VIDEO_SOURCE


def test_silent_story_result_returns_all_validated_media_metadata() -> None:
    output_builder = _function("_build_silent_story_output_payload")
    returned_payload = next(
        node.value
        for node in ast.walk(output_builder)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
    )
    result_fields = {
        ast.literal_eval(key): ast.unparse(value)
        for key, value in zip(returned_payload.keys, returned_payload.values)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }

    for field in ("width", "height", "fps", "video_codec"):
        assert result_fields[field] == f"final_details[{field!r}]"

