"""FEAT-093 Amendment C: the vLLM engine behind the generate interface the Qwen handlers already use (offline)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import qwen_vllm  # noqa: E402

SCHEMA = {"type": "object", "properties": {"value": {"type": "string"}}}


class _Llm:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, Any]] = []

    def generate(self, prompts: Any, params: Any, use_tqdm: bool = True) -> list[Any]:
        self.calls.append((prompts, params))
        return [SimpleNamespace(prompt_token_ids=[5, 6, 7], outputs=[SimpleNamespace(token_ids=[8, 9])])]


def _model(llm: _Llm) -> qwen_vllm.VllmTextModel:
    config = SimpleNamespace(
        eos_token_id=[9, 10], do_sample=True, temperature=1.0, top_p=0.95, top_k=20, max_new_tokens=32, min_new_tokens=None
    )
    return qwen_vllm.VllmTextModel(
        llm, config, make_params=lambda **options: options, to_tensor=lambda rows: rows
    )


def _config(model: Any, **changes: Any) -> Any:
    config = SimpleNamespace(**vars(model.generation_config))
    for name, value in changes.items():
        setattr(config, name, value)
    return config


def test_a_greedy_handler_call_becomes_a_constrained_vllm_request() -> None:
    llm = _Llm()
    model = _model(llm)

    progress: list[Any] = []

    output = model.generate(
        input_ids=[[1, 2, 3]],
        attention_mask=[[1, 1, 1]],
        generation_config=_config(model, do_sample=False, max_new_tokens=64),
        prefix_allowed_tokens_fn=qwen_vllm.JsonSchemaConstraint(SCHEMA),
        stopping_criteria=[lambda ids, scores: progress.append(ids)],
    )

    prompts, params = llm.calls[0]
    assert prompts == [{"prompt_token_ids": [1, 2, 3]}]
    assert params == {"max_tokens": 64, "temperature": 0.0, "json_schema": SCHEMA}
    assert output == [[1, 2, 3, 8, 9]]
    assert progress == [output]  # the progress record learns the final token count


def test_keyword_arguments_win_over_the_model_defaults() -> None:
    llm = _Llm()
    _model(llm).generate(
        input_ids=[[1]], do_sample=True, temperature=0.75, top_p=0.9, max_new_tokens=420, pad_token_id=9
    )

    params = llm.calls[0][1]
    assert (params["temperature"], params["top_p"], params["max_tokens"]) == (0.75, 0.9, 420)
    assert params["json_schema"] is None


@pytest.mark.parametrize(("attempt", "creative"), [(2, False), (3, False), (1, True)])
def test_a_retry_or_a_creative_workload_samples_instead_of_repeating_greedy(attempt: int, creative: bool) -> None:
    llm = _Llm()
    model = _model(llm)

    with qwen_vllm.generation_attempt(attempt, creative=creative):
        model.generate(input_ids=[[1]], do_sample=False, max_new_tokens=8)

    params = llm.calls[0][1]
    assert params["temperature"] == qwen_vllm.SAMPLED_TEMPERATURE
    assert (params["top_p"], params["top_k"]) == (0.8, 20)
    assert "seed" not in params  # a second call for the same request must be able to differ


def test_an_image_tensor_or_a_foreign_constraint_is_refused() -> None:
    model = _model(_Llm())
    with pytest.raises(RuntimeError, match="MODAL_QWEN_ENGINE_IMAGE_INPUT_UNSUPPORTED"):
        model.generate(input_ids=[[1]], pixel_values=object())
    with pytest.raises(RuntimeError, match="MODAL_QWEN_ENGINE_CONSTRAINT_UNSUPPORTED"):
        model.generate(input_ids=[[1]], prefix_allowed_tokens_fn=lambda *_: [1])


def test_a_drawing_is_sent_as_prompt_text_plus_the_image() -> None:
    llm = _Llm()
    image = object()

    input_ids, output_ids = _model(llm).generate_from_image(
        "<prompt>", image, schema=SCHEMA, max_new_tokens=256, min_new_tokens=16
    )

    prompts, params = llm.calls[0]
    assert prompts == [{"prompt": "<prompt>", "multi_modal_data": {"image": image}}]
    assert params == {"max_tokens": 256, "temperature": 0.0, "min_tokens": 16, "json_schema": SCHEMA}
    assert input_ids == [[5, 6, 7]] and output_ids == [[5, 6, 7, 8, 9]]


class _Handler:
    def __init__(self, *errors: Exception) -> None:
        self.errors = list(errors)
        self.attempts: list[tuple[int, bool]] = []

    def __call__(self, payload: dict[str, Any]) -> str:
        self.attempts.append((qwen_vllm.current_attempt().number, qwen_vllm.current_attempt().creative))
        if self.errors:
            raise self.errors.pop(0)
        return "ok"


class _StoryOutputValidationError(RuntimeError):
    reason_code = "STORY_TEXT_INCOMPLETE"


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("MODAL_MODEL_OUTPUT_INVALID"),
        RuntimeError("MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT"),
        RuntimeError("MODAL_MODEL_OUTPUT_TRUNCATED"),
        RuntimeError("TIMELINE_DRAFT_SCENE_COUNT"),
        _StoryOutputValidationError("MODAL_MODEL_OUTPUT_INVALID"),
    ],
)
def test_a_rejected_output_is_generated_again(error: Exception) -> None:
    handler = _Handler(error)

    assert qwen_vllm.run_with_quality_retries(handler, {}, creative=False) == "ok"
    assert handler.attempts == [(1, False), (2, False)]


def test_the_third_rejection_is_final_and_keeps_its_error() -> None:
    handler = _Handler(*[RuntimeError("MODAL_MODEL_OUTPUT_INVALID")] * 3)

    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        qwen_vllm.run_with_quality_retries(handler, {}, creative=True)
    assert [number for number, _ in handler.attempts] == [1, 2, 3]
    assert qwen_vllm.current_attempt().number == 1


@pytest.mark.parametrize(
    "error", [RuntimeError("MODAL_INPUT_NOT_ALLOWED"), RuntimeError("CUDA out of memory"), ValueError("x")]
)
def test_other_failures_are_not_repeated(error: Exception) -> None:
    handler = _Handler(error)

    with pytest.raises(type(error)):
        qwen_vllm.run_with_quality_retries(handler, {}, creative=False)
    assert len(handler.attempts) == 1


def test_engine_options_bound_the_context_and_enable_mtp_without_fp8_kv_cache() -> None:
    options = qwen_vllm.engine_options(min_pixels=10, max_pixels=20)

    assert options["max_model_len"] == 32_768
    # Without this the grammar allows endless line breaks, and one run wrote them until its token budget.
    # vLLM 0.34.0 refuses the flag unless the backend is named, which only showed up when the engine started.
    assert options["structured_outputs_config"] == {"backend": "xgrammar", "disable_any_whitespace": True}
    assert options["speculative_config"] == {"method": "mtp", "num_speculative_tokens": 3}
    assert "kv_cache_dtype" not in options  # crashes the hybrid (mamba) layers in vLLM 0.34.0, see evidence M12
    assert options["mm_processor_kwargs"] == {"min_pixels": 10, "max_pixels": 20}


def _worker_module() -> Any:
    import importlib.util

    spec = importlib.util.spec_from_file_location("sketch2life_worker_for_retries", MODAL_DIR / "language_audio_app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_real_quality_gate_error_of_the_worker_is_retried() -> None:
    worker = _worker_module()
    errors = [
        worker.StoryOutputValidationError("STORY_TEXT_INCOMPLETE", field_path="scenes[1].action"),
        worker._ParentActivityLanguageGateError("title", 1),
        worker._ParentActivityTextCompletenessError("title", character_count=3, reason_code="dangling_word"),
        *[
            RuntimeError(code)
            for code in (
                "MODAL_MODEL_OUTPUT_INVALID_ACTIVITY_FIELD",
                "MODAL_MODEL_OUTPUT_INVALID_JSON",
                "MODAL_MODEL_OUTPUT_DUPLICATE_ACTIVITY_TITLE",
                "MODAL_MODEL_OUTPUT_ACTIVITY_STEPS_REPEATED",
                "MODAL_MODEL_OUTPUT_EMPTY",
            )
        ],
    ]

    for error in errors:
        assert qwen_vllm.is_quality_rejection(error), error


class EngineDeadError(Exception):
    pass


def test_a_dead_engine_stops_the_container_and_reports_a_stable_code() -> None:
    class _Dead(_Llm):
        def generate(self, prompts: Any, params: Any, use_tqdm: bool = True) -> list[Any]:
            raise EngineDeadError("boom with private text")

    stopped: list[bool] = []
    model = qwen_vllm.VllmTextModel(
        _Dead(), _model(_Llm()).generation_config, make_params=lambda **options: options,
        to_tensor=lambda rows: rows, on_engine_dead=lambda: stopped.append(True),
    )

    with pytest.raises(RuntimeError, match="^MODAL_QWEN_ENGINE_FAILED$"):
        model.generate(input_ids=[[1]], do_sample=False, max_new_tokens=4)
    assert stopped == [True]
    assert not qwen_vllm.is_quality_rejection(RuntimeError("MODAL_QWEN_ENGINE_FAILED"))


def test_the_story_and_the_activity_list_sample_on_the_first_attempt() -> None:
    assert qwen_vllm.CREATIVE_WORKLOADS == {"story.generate", "parent.activity.suggest"}


def test_a_warm_up_payload_loads_the_engine_without_a_job(monkeypatch: pytest.MonkeyPatch) -> None:
    worker = _worker_module()
    loaded: list[bool] = []
    monkeypatch.setattr(worker, "_load_text_model", lambda: loaded.append(True) or (None, None))

    assert worker.qwen_worker.local({"warmup": True}) == {"warmed": True}
    assert loaded == [True]
