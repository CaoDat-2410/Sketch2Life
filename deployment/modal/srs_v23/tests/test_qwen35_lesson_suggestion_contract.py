from __future__ import annotations

import importlib.util
import importlib.metadata
import ast
import json
import sys
import types
import unicodedata
from contextlib import nullcontext
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


def test_qwen35_image_pins_official_causal_conv1d_wheel_and_digest() -> None:
    requirement = worker.QWEN_CAUSAL_CONV1D_WHEEL

    assert requirement.startswith(
        "causal-conv1d @ https://github.com/Dao-AILab/causal-conv1d/releases/"
    )
    assert "%2Bcu12torch2.8cxx11abiTRUE-cp311-cp311-linux_x86_64.whl" in requirement
    assert requirement.endswith(
        "#sha256=b28c3657a9d6855e1f95bc912ab94f893434276b437dec8008c92c9f38b6a1f4"
    )


def test_qwen38_text_runtime_pins_tensor_descriptor_compatible_cuda_stack() -> None:
    assert worker.QWEN_TRITON_VERSION == "3.4.0"
    source = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
    assert '"torch==2.8.0"' in source
    assert '"torchvision==0.23.0"' in source

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


def test_qwen38_checkpoint_and_model_pin_are_explicit() -> None:
    assert worker.TEXT_MODEL_ID == "Qwen/Qwen3.8-27B-FP8"
    assert worker.TEXT_MODEL_REVISION == "c3a462cc3d38cf351f3b26cbd763469eeb74ef81"
    assert worker.STORY_GENERATION_BUDGET == 4_096


def _install_fp8_kernel_preload_modules(
    monkeypatch: pytest.MonkeyPatch,
    get_kernel: Any,
) -> types.SimpleNamespace:
    hub_constants = types.SimpleNamespace(HF_HUB_DISABLE_TELEMETRY=True)
    hub_package = types.ModuleType("huggingface_hub")
    hub_package.constants = hub_constants  # type: ignore[attr-defined]
    kernels_package = types.ModuleType("kernels")
    kernels_package.get_kernel = get_kernel  # type: ignore[attr-defined]
    integrations_package = types.ModuleType("transformers.integrations")
    integrations_package.__path__ = []  # type: ignore[attr-defined]
    hub_kernels = types.ModuleType("transformers.integrations.hub_kernels")
    hub_kernels._KERNEL_MODULE_MAPPING = {}
    integrations_package.hub_kernels = hub_kernels  # type: ignore[attr-defined]
    transformers_package = types.ModuleType("transformers")
    transformers_package.__path__ = []  # type: ignore[attr-defined]
    transformers_package.integrations = integrations_package  # type: ignore[attr-defined]
    for name, module in {
        "huggingface_hub": hub_package,
        "kernels": kernels_package,
        "transformers": transformers_package,
        "transformers.integrations": integrations_package,
        "transformers.integrations.hub_kernels": hub_kernels,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(worker, "worker_phase", lambda _name: nullcontext())
    return hub_constants


def test_fp8_kernel_preload_uses_pinned_allowlist_and_restores_telemetry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kernel = types.ModuleType("finegrained_fp8")
    kernel.matmul_2d = lambda: None  # type: ignore[attr-defined]
    kernel.matmul_batched = lambda: None  # type: ignore[attr-defined]
    kernel.matmul_grouped = lambda: None  # type: ignore[attr-defined]
    observed: dict[str, Any] = {}

    def get_kernel(repo_id: str, **kwargs: Any) -> types.ModuleType:
        observed.update(repo_id=repo_id, **kwargs)
        observed["telemetry_disabled_during_load"] = hub_constants.HF_HUB_DISABLE_TELEMETRY
        return kernel

    hub_constants = _install_fp8_kernel_preload_modules(monkeypatch, get_kernel)
    _install_triton_runtime_modules(monkeypatch)

    worker._preload_allowlisted_fp8_kernel()

    assert observed == {
        "repo_id": worker.FP8_KERNEL_REPO_ID,
        "version": worker.FP8_KERNEL_VERSION,
        "trust_remote_code": [worker.FP8_KERNEL_REPO_ID],
        "user_agent": {"component": "sketch2life-fp8-bootstrap"},
        "telemetry_disabled_during_load": False,
    }
    assert hub_constants.HF_HUB_DISABLE_TELEMETRY is True


def test_fp8_kernel_preload_restores_telemetry_after_loader_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def get_kernel(*_args: Any, **_kwargs: Any) -> None:
        raise ValueError("simulated kernel resolution error")

    hub_constants = _install_fp8_kernel_preload_modules(monkeypatch, get_kernel)
    _install_triton_runtime_modules(monkeypatch)

    with pytest.raises(ValueError, match="simulated kernel resolution error"):
        worker._preload_allowlisted_fp8_kernel()

    assert hub_constants.HF_HUB_DISABLE_TELEMETRY is True


def test_drawing_fp8_kernel_preload_uses_exact_repo_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kernel = types.ModuleType("finegrained_fp8")
    kernel.matmul_2d = lambda: None  # type: ignore[attr-defined]
    kernel.matmul_batched = lambda: None  # type: ignore[attr-defined]
    kernel.matmul_grouped = lambda: None  # type: ignore[attr-defined]
    observed: dict[str, Any] = {}

    hub_constants = types.SimpleNamespace(HF_HUB_DISABLE_TELEMETRY=True)
    hub_package = types.ModuleType("huggingface_hub")
    hub_package.constants = hub_constants  # type: ignore[attr-defined]

    def get_kernel(repo_id: str, **kwargs: Any) -> types.ModuleType:
        observed.update(repo_id=repo_id, **kwargs)
        observed["telemetry_disabled_during_load"] = hub_constants.HF_HUB_DISABLE_TELEMETRY
        return kernel

    kernels_package = types.ModuleType("kernels")
    kernels_package.get_kernel = get_kernel  # type: ignore[attr-defined]
    integrations_package = types.ModuleType("transformers.integrations")
    integrations_package.__path__ = []  # type: ignore[attr-defined]
    hub_kernels = types.ModuleType("transformers.integrations.hub_kernels")
    hub_kernels._KERNEL_MODULE_MAPPING = {}
    integrations_package.hub_kernels = hub_kernels  # type: ignore[attr-defined]
    transformers_package = types.ModuleType("transformers")
    transformers_package.__path__ = []  # type: ignore[attr-defined]
    transformers_package.integrations = integrations_package  # type: ignore[attr-defined]
    for name, module in {
        "huggingface_hub": hub_package,
        "kernels": kernels_package,
        "transformers": transformers_package,
        "transformers.integrations": integrations_package,
        "transformers.integrations.hub_kernels": hub_kernels,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(drawing_worker, "worker_phase", lambda _name: nullcontext())
    monkeypatch.setattr(
        drawing_worker, "_ensure_fp8_triton_import_compatibility", lambda: None
    )

    drawing_worker._preload_allowlisted_fp8_kernel()
    drawing_worker._preload_allowlisted_fp8_kernel()

    assert observed == {
        "repo_id": drawing_worker.FP8_KERNEL_REPO_ID,
        "version": drawing_worker.FP8_KERNEL_VERSION,
        "trust_remote_code": [drawing_worker.FP8_KERNEL_REPO_ID],
        "user_agent": {"component": "sketch2life-fp8-bootstrap"},
        "telemetry_disabled_during_load": False,
    }
    assert hub_constants.HF_HUB_DISABLE_TELEMETRY is True
    assert hub_kernels._KERNEL_MODULE_MAPPING["finegrained-fp8"] is kernel


def test_drawing_fp8_triton_compatibility_exposes_pinned_kernel_imports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    autotuner, jit = _install_triton_runtime_modules(monkeypatch)

    drawing_worker._ensure_fp8_triton_import_compatibility()

    assert autotuner.JITFunction is jit.JITFunction
    assert callable(autotuner.triton_key)
    assert autotuner.driver is sys.modules["triton.runtime.driver"].driver


def test_drawing_fp8_triton_compatibility_fails_closed_without_tensor_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_triton_runtime_modules(monkeypatch)
    monkeypatch.delitem(sys.modules, "triton.tools.tensor_descriptor")

    with pytest.raises(
        RuntimeError, match="MODAL_FP8_TRITON_TENSOR_DESCRIPTOR_UNSUPPORTED"
    ):
        drawing_worker._ensure_fp8_triton_import_compatibility()


def _install_triton_runtime_modules(
    monkeypatch: pytest.MonkeyPatch,
    *,
    autotuner_jit_function: Any = None,
) -> tuple[types.ModuleType, types.ModuleType]:
    triton_package = types.ModuleType("triton")
    triton_package.__path__ = []  # type: ignore[attr-defined]
    runtime_package = types.ModuleType("triton.runtime")
    runtime_package.__path__ = []  # type: ignore[attr-defined]
    autotuner_module = types.ModuleType("triton.runtime.autotuner")

    class FakeAutotuner:
        def __init__(self, *_args: Any, **kwargs: Any) -> None:
            if "cache_results" in kwargs:
                raise TypeError("unexpected keyword argument 'cache_results'")
            self.forwarded_kwargs = kwargs

    autotuner_module.Autotuner = FakeAutotuner  # type: ignore[attr-defined]
    cache_module = types.ModuleType("triton.runtime.cache")
    cache_module.get_cache_manager = lambda *_args, **_kwargs: None  # type: ignore[attr-defined]
    driver_module = types.ModuleType("triton.runtime.driver")
    driver_module.driver = object()  # type: ignore[attr-defined]
    jit_module = types.ModuleType("triton.runtime.jit")
    jit_function = type("JITFunction", (), {})
    jit_module.JITFunction = jit_function  # type: ignore[attr-defined]
    compiler_package = types.ModuleType("triton.compiler")
    compiler_package.__path__ = []  # type: ignore[attr-defined]
    compiler_module = types.ModuleType("triton.compiler.compiler")
    compiler_module.triton_key = lambda: "test-triton-key"  # type: ignore[attr-defined]
    compiler_package.compiler = compiler_module  # type: ignore[attr-defined]
    c_package = types.ModuleType("triton._C")
    c_package.__path__ = []  # type: ignore[attr-defined]
    libtriton_module = types.ModuleType("triton._C.libtriton")
    libtriton_module.get_cache_invalidating_env_vars = lambda: []  # type: ignore[attr-defined]
    c_package.libtriton = libtriton_module  # type: ignore[attr-defined]
    if autotuner_jit_function is not None:
        autotuner_module.JITFunction = autotuner_jit_function  # type: ignore[attr-defined]
    runtime_package.autotuner = autotuner_module  # type: ignore[attr-defined]
    runtime_package.cache = cache_module  # type: ignore[attr-defined]
    runtime_package.driver = driver_module  # type: ignore[attr-defined]
    runtime_package.jit = jit_module  # type: ignore[attr-defined]
    tools_package = types.ModuleType("triton.tools")
    tools_package.__path__ = []  # type: ignore[attr-defined]
    descriptor_module = types.ModuleType("triton.tools.tensor_descriptor")
    descriptor_module.TensorDescriptor = type("TensorDescriptor", (), {})  # type: ignore[attr-defined]
    tools_package.tensor_descriptor = descriptor_module  # type: ignore[attr-defined]
    triton_package.runtime = runtime_package  # type: ignore[attr-defined]
    triton_package._C = c_package  # type: ignore[attr-defined]
    for name, module in {
        "triton": triton_package,
        "triton._C": c_package,
        "triton._C.libtriton": libtriton_module,
        "triton.compiler": compiler_package,
        "triton.compiler.compiler": compiler_module,
        "triton.runtime": runtime_package,
        "triton.runtime.autotuner": autotuner_module,
        "triton.runtime.cache": cache_module,
        "triton.runtime.driver": driver_module,
        "triton.runtime.jit": jit_module,
        "triton.tools": tools_package,
        "triton.tools.tensor_descriptor": descriptor_module,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    triton_package.tools = tools_package  # type: ignore[attr-defined]
    return autotuner_module, jit_module


def test_fp8_kernel_compatibility_exports_jit_function_for_triton_331(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    autotuner, jit = _install_triton_runtime_modules(monkeypatch)

    worker._ensure_fp8_triton_import_compatibility()

    assert autotuner.JITFunction is jit.JITFunction
    assert callable(autotuner.get_cache_invalidating_env_vars)
    assert callable(autotuner.get_cache_manager)
    assert callable(autotuner.triton_key)
    assert autotuner.triton_key is sys.modules["triton.compiler.compiler"].triton_key
    assert autotuner.driver is sys.modules["triton.runtime.driver"].driver
    assert autotuner.knobs.autotuning.print is False


def test_fp8_kernel_compatibility_preserves_existing_triton_export(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = type("ExistingJITFunction", (), {})
    autotuner, _jit = _install_triton_runtime_modules(
        monkeypatch,
        autotuner_jit_function=existing,
    )

    worker._ensure_fp8_triton_import_compatibility()

    assert autotuner.JITFunction is existing


def test_fp8_kernel_compatibility_requires_triton_tensor_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    autotuner, _jit = _install_triton_runtime_modules(monkeypatch)
    monkeypatch.delitem(sys.modules, "triton.tools.tensor_descriptor")

    with pytest.raises(
        RuntimeError,
        match="MODAL_FP8_TRITON_TENSOR_DESCRIPTOR_UNSUPPORTED",
    ):
        worker._ensure_fp8_triton_import_compatibility()

    assert autotuner is sys.modules["triton.runtime.autotuner"]


def test_parent_activity_inference_binds_stopping_criteria_and_progress() -> None:
    source = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "suggest_parent_activities"
    )
    imports_stopping_criteria = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "transformers"
        and any(alias.name == "StoppingCriteriaList" for alias in node.names)
        for node in ast.walk(function)
    )
    binds_progress_context = any(
        isinstance(node, ast.withitem)
        and isinstance(node.optional_vars, ast.Name)
        and node.optional_vars.id == "progress"
        for node in ast.walk(function)
    )

    assert imports_stopping_criteria
    assert binds_progress_context


def test_language_audio_uses_qwen_multimodal_class_and_cpu_readiness_does_not_load_weights() -> None:
    source = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    def function_named(name: str) -> ast.FunctionDef:
        return next(
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )

    loader = ast.get_source_segment(source, function_named("_load_text_model"))
    loader_node = function_named("_load_text_model")
    readiness = ast.get_source_segment(
        source, function_named("check_qwen38_decoder_readiness")
    )
    runtime_telemetry_call = next(
        node
        for node in ast.walk(loader_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "worker_runtime_verified"
    )
    qwen_model_load_call = next(
        node
        for node in ast.walk(loader_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "from_pretrained"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "AutoModelForMultimodalLM"
    )

    assert loader is not None and "AutoModelForMultimodalLM.from_pretrained" in loader
    assert loader is not None and "use_cache=True" not in loader
    assert any(
        isinstance(node, ast.Expr) and node.value is runtime_telemetry_call
        for node in ast.walk(loader_node)
    )
    assert not any(
        isinstance(node, ast.withitem)
        and node.context_expr is runtime_telemetry_call
        for node in ast.walk(loader_node)
    )
    assert all(keyword.arg != "use_cache" for keyword in qwen_model_load_call.keywords)
    assert readiness is not None and "AutoModelForMultimodalLM" in readiness
    assert readiness is not None and ".from_pretrained(" not in readiness
    assert readiness is not None and "MODAL_FP8_RUNTIME_STACK_UNSUPPORTED" in readiness
    assert readiness is not None and "triton.tools.tensor_descriptor" in readiness
    assert readiness is not None and "torchvision_version" in readiness


def test_qwen_text_model_inputs_preserve_the_full_multimodal_processor_envelope() -> None:
    input_ids = object()
    attention_mask = object()
    mm_token_type_ids = object()

    result = worker._qwen_text_model_generation_inputs(
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "mm_token_type_ids": mm_token_type_ids,
        }
    )

    assert result == {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "mm_token_type_ids": mm_token_type_ids,
    }


def test_every_text_model_generate_call_uses_validated_processor_inputs() -> None:
    source = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    generate_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "generate"
    ]

    # FEAT-087 M4 added the story staging pass (an 8th call, validated like the rest).
    assert len(generate_calls) == 8
    assert all(
        any(
            keyword.arg is None
            and isinstance(keyword.value, ast.Call)
            and isinstance(keyword.value.func, ast.Name)
            and keyword.value.func.id == "_qwen_text_model_generation_inputs"
            for keyword in call.keywords
        )
        for call in generate_calls
    )


def test_qwen_text_model_placement_diagnostics_are_safe_and_count_offload() -> None:
    gpu_properties = types.SimpleNamespace(
        name="NVIDIA L40S™",
        total_memory=48 * 1024 * 1024 * 1024,
    )
    torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(
            get_device_properties=lambda _device: gpu_properties,
            memory_allocated=lambda _device: 12 * 1024 * 1024 * 1024,
            memory_reserved=lambda _device: 14 * 1024 * 1024 * 1024,
        )
    )
    model = types.SimpleNamespace(
        hf_device_map={
            "private.layer.0": 0,
            "private.layer.1": "cpu",
            "private.layer.2": "cuda:0",
            "private.layer.3": "disk",
        },
        config=types.SimpleNamespace(use_cache=True, _attn_implementation="sdpa"),
    )

    report = worker._qwen_text_model_placement_diagnostics(torch, model)

    assert report["event"] == "qwen_text_model_placement"
    assert report["gpu_name"] == "NVIDIA L40S"
    assert report["device_map_module_counts"] == {
        "cuda": 2,
        "cpu": 1,
        "disk": 1,
        "other": 0,
    }
    assert report["use_cache"] is True
    assert report["attention_implementation"] == "sdpa"
    assert "private.layer" not in repr(report)


def test_qwen_prefix_decoder_measures_callback_latency_without_token_data(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lmfe = types.ModuleType("lmformatenforcer")
    tokenenforcer = types.ModuleType("lmformatenforcer.tokenenforcer")
    captured: dict[str, Any] = {}

    class FakeSchemaParser:
        def __init__(self, _schema: dict[str, Any]) -> None:
            pass

    class FakeTokenizerData:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

    class FakeEnforcer:
        prefix_states: dict[tuple[int, ...], Any] = {}

        def __init__(self, *_args: Any) -> None:
            pass

        def get_allowed_tokens(self, token_ids: list[int]) -> Any:
            captured["token_ids"] = token_ids
            return types.SimpleNamespace(allowed_tokens=[7, 8])

    lmfe.JsonSchemaParser = FakeSchemaParser
    tokenenforcer.TokenEnforcer = FakeEnforcer
    tokenenforcer.TokenEnforcerTokenizerData = FakeTokenizerData
    monkeypatch.setitem(sys.modules, "lmformatenforcer", lmfe)
    monkeypatch.setitem(sys.modules, "lmformatenforcer.tokenenforcer", tokenenforcer)

    class Tokenizer:
        eos_token_id = 0
        all_special_ids = [0]

        def __len__(self) -> int:
            return 3

        def encode(self, _text: str) -> list[int]:
            return [1]

        def decode(self, token_ids: list[int]) -> str:
            return "".join({0: "", 1: "0", 2: "a"}[token_id] for token_id in token_ids)

    worker._CACHED_STORY_VOCAB_DATA = None
    worker._CACHED_STORY_EOS_IDS = None
    prefix_fn = worker._build_json_prefix_allowed_tokens_fn(
        Tokenizer(), {"type": "object"}, eos_token_id=0
    )

    class Input:
        calls = 0

        def tolist(self) -> list[int]:
            self.calls += 1
            return [4, 5]

    input_ids = Input()
    for _ in range(25):
        assert prefix_fn(0, input_ids) == [7, 8]

    diagnostics = prefix_fn.decoder_diagnostics
    output = capsys.readouterr().out
    assert input_ids.calls == 25
    assert diagnostics["callback_calls"] == 25
    assert diagnostics["callback_duration_total_ms"] >= 0
    assert diagnostics["allowed_token_count_last"] == 2
    assert '"event": "qwen_json_decoder_callback_timing"' in output
    assert "token_ids" not in output
    assert "private" not in output


def test_parent_activity_decoder_filters_escapes_and_non_latin_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lmfe = types.ModuleType("lmformatenforcer")
    tokenenforcer = types.ModuleType("lmformatenforcer.tokenenforcer")

    class FakeSchemaParser:
        active_field = "objective"
        active_text = "Nội dung chưa kết thúc"

        def __init__(self, _schema: dict[str, Any]) -> None:
            self.object_stack = [
                types.SimpleNamespace(current_key=self.active_field),
                types.SimpleNamespace(
                    parsed_string=self.active_text,
                    max_length=80,
                    seen_opening_quote=True,
                    seen_closing_quote=False,
                    allowed_strings=[],
                    regex_parser=None,
                ),
            ]

    class FakeTokenizerData:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

    class FakeEnforcer:
        def __init__(self, _data: Any, parser: FakeSchemaParser) -> None:
            self.parser = parser
            self.prefix_states: dict[tuple[int, ...], Any] = {}

        def get_allowed_tokens(self, token_ids: list[int]) -> Any:
            self.prefix_states[tuple(token_ids)] = types.SimpleNamespace(
                parser=self.parser
            )
            return types.SimpleNamespace(allowed_tokens=[7, 3, 9, 4, 5, 6])

    lmfe.JsonSchemaParser = FakeSchemaParser
    tokenenforcer.TokenEnforcer = FakeEnforcer
    tokenenforcer.TokenEnforcerTokenizerData = FakeTokenizerData
    monkeypatch.setitem(sys.modules, "lmformatenforcer", lmfe)
    monkeypatch.setitem(sys.modules, "lmformatenforcer.tokenenforcer", tokenenforcer)

    class Tokenizer:
        eos_token_id = 0
        all_special_ids = [0]
        pieces = {
            0: "",
            1: "0",
            2: "a",
            3: "\\",
            4: "中",
            5: "ế",
            6: "nội dung\"",
        }

        def __len__(self) -> int:
            return len(self.pieces)

        def encode(self, _text: str) -> list[int]:
            return [1]

        def decode(self, token_ids: list[int]) -> str:
            return "".join(self.pieces[token_id] for token_id in token_ids)

    worker._CACHED_STORY_VOCAB_DATA = None
    worker._CACHED_STORY_EOS_IDS = None
    tokenizer = Tokenizer()
    prefix_fn = worker._build_json_prefix_allowed_tokens_fn(
        tokenizer,
        {"type": "object"},
        eos_token_id=0,
        reject_json_backslash_escapes=True,
    )

    class Input:
        def tolist(self) -> list[int]:
            return [10, 11]

    assert prefix_fn(0, Input()) == [7, 9, 5, 6]
    assert prefix_fn.decoder_diagnostics["backslash_escape_candidates_blocked"] == 1
    assert prefix_fn.decoder_diagnostics["non_latin_letter_candidates_blocked"] == 1
    assert prefix_fn.decoder_diagnostics["backslash_escape_filter_enabled"] is True
    assert prefix_fn.decoder_diagnostics["non_latin_letter_filter_enabled"] is True

    FakeSchemaParser.active_text = "Nội dung đã kết thúc.  "
    worker._CACHED_STORY_VOCAB_DATA = None
    worker._CACHED_STORY_EOS_IDS = None
    punctuated_prefix_fn = worker._build_json_prefix_allowed_tokens_fn(
        tokenizer,
        {"type": "object"},
        eos_token_id=0,
        reject_json_backslash_escapes=True,
    )
    assert 6 in punctuated_prefix_fn(0, Input())

    FakeSchemaParser.active_field = "materials_text"
    FakeSchemaParser.active_text = "Nội dung không bắt buộc dấu câu"
    worker._CACHED_STORY_VOCAB_DATA = None
    worker._CACHED_STORY_EOS_IDS = None
    non_required_prefix_fn = worker._build_json_prefix_allowed_tokens_fn(
        tokenizer,
        {"type": "object"},
        eos_token_id=0,
        reject_json_backslash_escapes=True,
    )
    assert 6 in non_required_prefix_fn(0, Input())

    FakeSchemaParser.active_field = "objective"
    worker._CACHED_STORY_VOCAB_DATA = None
    worker._CACHED_STORY_EOS_IDS = None
    unrestricted_prefix_fn = worker._build_json_prefix_allowed_tokens_fn(
        tokenizer, {"type": "object"}, eos_token_id=0
    )
    assert unrestricted_prefix_fn(0, Input()) == [7, 3, 9, 4, 5, 6]
    assert (
        unrestricted_prefix_fn.decoder_diagnostics[
            "non_latin_letter_filter_enabled"
        ]
        is False
    )


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


def test_active_qwen_dev_workloads_use_the_pinned_qwen38_model() -> None:
    registry_path = (
        Path(__file__).resolve().parents[4]
        / "deployment"
        / "modal"
        / "srs_v23"
        / "workloads.json"
    )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    candidates = {workload["id"]: workload["candidate"] for workload in registry["workloads"]}

    assert candidates["drawing.analyze"].startswith("Qwen/Qwen3.8-27B-FP8@")
    for workload_id in (
        "story.generate",
        "storyboard.generate",
        "parent.topic-subjects.validate",
        "parent.activity.suggest",
        "teacher.sketch-deck.generate",
        "lesson.plan.suggest",
    ):
        assert candidates[workload_id].startswith("Qwen/Qwen3.8-27B-FP8@")
    assert "Qwen/Qwen3.8-27B-FP8@" in registry["model_selection_status"]
    assert "Qwen/Qwen3.5-9B@" not in registry["model_selection_status"]
    assert "Retired from dispatch" in candidates["parent.topic-subjects.suggest"]


def test_drawing_vlm_uses_documented_image_message_shape() -> None:
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
            "main_subject": {
                "label": "bướm",
                "visible_features": ["hai cặp cánh", "thân mảnh"],
                "facing": "front",
                "box": [3, 3, 17, 17],
            },
            "secondary_subjects": [],
            "confidence": 0.9,
        },
        ensure_ascii=False,
    )
    assert drawing_worker._parse_candidate(valid)["candidate_subject"] == "bướm"
    assert drawing_worker._parse_candidate(valid)["main_subject"]["label"] == "bướm"

    for invalid in (
        "Dưới đây là JSON: " + valid,
        valid + "\nĐã hoàn thành.",
        valid.replace('"confidence": 0.9', '"confidence": 0.9, "confidence": 0.8'),
    ):
        with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
            drawing_worker._parse_candidate(invalid)


def test_drawing_decoder_uses_model_eos_set_for_constraints_and_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    lmfe = type("LMFE", (), {})()
    tokenenforcer = type("TokenEnforcerModule", (), {})()

    class FakeSchemaParser:
        def __init__(self, schema: dict[str, Any]) -> None:
            captured["schema"] = schema

    class FakeTokenizerData:
        def __init__(
            self,
            regular_tokens: list[tuple[int, str, bool]],
            decode: Any,
            eos_token_id: int | list[int],
            *,
            use_bitmask: bool,
            vocab_size: int,
        ) -> None:
            captured["regular_tokens"] = regular_tokens
            captured["eos_token_id"] = eos_token_id
            captured["use_bitmask"] = use_bitmask
            captured["vocab_size"] = vocab_size

    class FakeEnforcer:
        prefix_states: dict[tuple[int, ...], Any] = {}

        def __init__(self, _data: Any, _parser: Any) -> None:
            pass

        def get_allowed_tokens(self, token_ids: list[int]) -> Any:
            captured["prefix"] = token_ids
            return type("Allowed", (), {"allowed_tokens": [11, 12]})()

    lmfe.JsonSchemaParser = FakeSchemaParser
    tokenenforcer.TokenEnforcer = FakeEnforcer
    tokenenforcer.TokenEnforcerTokenizerData = FakeTokenizerData
    monkeypatch.setitem(sys.modules, "lmformatenforcer", lmfe)
    monkeypatch.setitem(sys.modules, "lmformatenforcer.tokenenforcer", tokenenforcer)

    class Tokenizer:
        eos_token_id = 0
        all_special_ids = [0]
        tokens = ["<tokenizer-eos>", "0", "a", "b", "<model-eos-a>", "<model-eos-b>"]

        def __len__(self) -> int:
            return len(self.tokens)

        def encode(self, text: str) -> list[int]:
            assert text == "0"
            return [1]

        def decode(self, token_ids: list[int]) -> str:
            return "".join(self.tokens[token_id] for token_id in token_ids)

    drawing_worker._CACHED_QWEN_VOCAB_DATA = None
    drawing_worker._CACHED_QWEN_EOS_IDS = None
    prefix_fn = drawing_worker._build_drawing_prefix_allowed_tokens_fn(
        Tokenizer(), eos_token_id=[4, 5]
    )
    assert prefix_fn(0, type("Input", (), {"tolist": lambda _self: [9, 10]})()) == [11, 12]
    assert captured["prefix"] == [9, 10]
    assert captured["eos_token_id"] == [4, 5]
    assert {token[0] for token in captured["regular_tokens"]} == {1, 2, 3}
    assert captured["use_bitmask"] is False
    assert prefix_fn.decoder_diagnostics["callback_calls"] == 1
    assert "ơ" in drawing_worker.LMFE_VIETNAMESE_JSON_ALPHABET


def test_drawing_invalid_json_diagnostics_omit_generated_text() -> None:
    private_text = '{"candidate_subject":"con gà","visible_features":["mào đỏ'
    diagnostics = drawing_worker._drawing_json_diagnostics(private_text)

    assert diagnostics["json_complete"] is False
    assert diagnostics["json_error_type"] == "UnterminatedString"
    assert diagnostics["json_error_position"] >= 0
    assert diagnostics["decoded_character_count"] == len(private_text)
    assert private_text not in repr(diagnostics)


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


def test_qwen38_checkpoint_verification_checks_every_indexed_shard(
    tmp_path: Path,
) -> None:
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_8",
                "quantization_config": {"quant_method": "fp8", "fmt": "e4m3"},
            }
        ),
        encoding="utf-8",
    )
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


def _install_qwen_fast_kernel_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    causal = types.ModuleType("causal_conv1d")
    causal.causal_conv1d_fn = lambda: None
    causal.causal_conv1d_update = lambda: None
    fla = types.ModuleType("fla")
    fla.__path__ = []
    ops = types.ModuleType("fla.ops")
    ops.__path__ = []
    gated_delta = types.ModuleType("fla.ops.gated_delta_rule")
    gated_delta.chunk_gated_delta_rule = lambda: None
    gated_delta.fused_recurrent_gated_delta_rule = lambda: None
    monkeypatch.setitem(sys.modules, "causal_conv1d", causal)
    monkeypatch.setitem(sys.modules, "fla", fla)
    monkeypatch.setitem(sys.modules, "fla.ops", ops)
    monkeypatch.setitem(sys.modules, "fla.ops.gated_delta_rule", gated_delta)
    versions = {
        "flash-linear-attention": "0.6.0",
        "causal-conv1d": "1.7.0",
        "triton": "3.3.1",
    }
    monkeypatch.setattr(importlib.metadata, "version", lambda name: versions[name])


def test_qwen35_fast_kernel_readiness_reports_versions_and_gpu_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_qwen_fast_kernel_imports(monkeypatch)
    torch = types.SimpleNamespace(
        __version__="2.7.1",
        version=types.SimpleNamespace(cuda="12.6"),
        cuda=types.SimpleNamespace(
            is_available=lambda: True,
            get_device_capability=lambda _device: (8, 9),
        ),
    )

    report = worker._qwen_fast_kernel_diagnostics(torch, require_cuda=True)

    assert report == {
        "torch_version": "2.7.1",
        "torch_cuda_version": "12.6",
        "fla_version": "0.6.0",
        "causal_conv1d_version": "1.7.0",
        "triton_version": "3.3.1",
        "fla_kernel_import": "verified",
        "gpu_capability": "8.9",
    }


def test_qwen35_fast_kernel_readiness_fails_closed_when_kernels_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broken_causal = types.ModuleType("causal_conv1d")
    monkeypatch.setitem(sys.modules, "causal_conv1d", broken_causal)
    torch = types.SimpleNamespace(
        __version__="2.7.1",
        version=types.SimpleNamespace(cuda="12.6"),
        cuda=types.SimpleNamespace(is_available=lambda: True),
    )

    with pytest.raises(RuntimeError, match="MODAL_CAUSAL_CONV1D_IMPORT_FAILED"):
        worker._qwen_fast_kernel_diagnostics(torch, require_cuda=False)
    assert '"kernel": "causal_conv1d"' in capsys.readouterr().out


def test_qwen35_fast_kernel_readiness_identifies_missing_fla_kernels(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_qwen_fast_kernel_imports(monkeypatch)
    monkeypatch.delitem(sys.modules, "fla.ops.gated_delta_rule")
    torch = types.SimpleNamespace(
        __version__="2.7.1",
        version=types.SimpleNamespace(cuda="12.6"),
        cuda=types.SimpleNamespace(is_available=lambda: True),
    )

    with pytest.raises(RuntimeError, match="MODAL_FLA_KERNEL_IMPORT_FAILED"):
        worker._qwen_fast_kernel_diagnostics(torch, require_cuda=False)
    assert '"kernel": "fla.ops.gated_delta_rule"' in capsys.readouterr().out


def test_qwen35_cpu_readiness_defers_fla_kernel_import_to_gpu_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_qwen_fast_kernel_imports(monkeypatch)
    torch = types.SimpleNamespace(
        __version__="2.7.1",
        version=types.SimpleNamespace(cuda="12.6"),
        cuda=types.SimpleNamespace(is_available=lambda: False),
    )

    report = worker._qwen_fast_kernel_diagnostics(torch, require_cuda=False)

    assert report["fla_kernel_import"] == "deferred_to_gpu_worker"
    assert report["fla_version"] == "0.6.0"


def test_qwen35_fast_kernel_readiness_fails_closed_without_cuda_device() -> None:
    torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: False),
    )

    with pytest.raises(RuntimeError, match="MODAL_GPU_UNAVAILABLE"):
        worker._qwen_fast_kernel_diagnostics(torch, require_cuda=True)
