"""Exercise the Teacher handlers through qwen-worker and its VllmTextModel adapter."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import qwen_vllm


def _load_worker() -> Any:
    spec = importlib.util.spec_from_file_location(
        "sketch2life_modal_teacher_vllm_test", MODAL_DIR / "language_audio_app.py"
    )
    assert spec is not None and spec.loader is not None
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    return worker


class _FakeVector(list[int]):
    def tolist(self) -> list[int]:
        return list(self)


class _FakeScalar:
    def __init__(self, value: int) -> None:
        self.value = value

    def item(self) -> int:
        return self.value


class _FakeTensor:
    def __init__(self, rows: list[list[int]]) -> None:
        self.rows = rows

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.rows), len(self.rows[0]) if self.rows else 0)

    def tolist(self) -> list[list[int]]:
        return [list(row) for row in self.rows]

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, tuple):
            row_index, column_index = index
            value = self.rows[row_index][column_index]
            return _FakeScalar(value) if isinstance(column_index, int) else _FakeVector(value)
        return _FakeVector(self.rows[index])


class _Encoded(dict[str, Any]):
    def to(self, _device: str) -> _Encoded:
        return self


class _FakeTokenizer:
    eos_token_id = 99
    all_special_ids: ClassVar[list[int]] = []

    def __init__(self, output_by_token: dict[int, str]) -> None:
        self.output_by_token = output_by_token

    def decode(self, token_ids: Any, *, skip_special_tokens: bool) -> str:
        assert skip_special_tokens
        values = token_ids.tolist() if hasattr(token_ids, "tolist") else list(token_ids)
        return self.output_by_token[values[-1]]


class _FakeProcessor:
    def __init__(self, tokenizer: _FakeTokenizer) -> None:
        self.tokenizer = tokenizer

    def apply_chat_template(self, *_args: Any, **_kwargs: Any) -> _Encoded:
        return _Encoded(
            input_ids=_FakeTensor([[11, 12]]),
            attention_mask=_FakeTensor([[1, 1]]),
        )


class _FakeLlm:
    def __init__(self, output_token_ids: list[int]) -> None:
        self.output_token_ids = list(output_token_ids)
        self.calls: list[tuple[list[dict[str, Any]], dict[str, Any]]] = []

    def generate(
        self,
        prompts: list[dict[str, Any]],
        params: dict[str, Any],
        *,
        use_tqdm: bool,
    ) -> list[Any]:
        assert not use_tqdm
        self.calls.append((prompts, dict(params)))
        token_id = self.output_token_ids.pop(0)
        return [SimpleNamespace(outputs=[SimpleNamespace(token_ids=[token_id])])]


def _lesson_request() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": "Bướm",
        "target_age_band_ref": "band-3-5",
        "target_age_band_version": 1,
        "target_age_months": 54,
        "objectives": ["Quan sát cánh bướm"],
        "drawing_subject": "Con bướm",
        "activity_count": 1,
        "activity_kind": "indoor",
        "script_following_allowed": False,
        "script_direction": None,
    }


def _lesson_output() -> dict[str, Any]:
    return {
        "title": "Quan sát bướm",
        "drawing_steps_text": "Vẽ thân bướm.\nThêm cánh lớn.\nVẽ râu.\nThêm chi tiết.",
        "subject_learning_notes": "Bướm có hai cánh đối xứng.",
        "script_direction": None,
        "activities": [
            {
                "title": "Tìm cánh đối xứng",
                "objective": "Nhận ra hai cánh bướm.",
                "materials_text": "Giấy và bút màu",
                "preparation_text": "Đặt giấy trên bàn.",
                "instructions_text": "Quan sát rồi vẽ hai cánh.",
                "observation_notes": "Quan sát cách trẻ so sánh.",
                "safety_notes": "Người lớn kiểm tra vật liệu.",
                "activity_kind": "indoor",
            }
        ],
    }


def _teacher_deck_request() -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "sketch2life.teacher-deck-input.v1",
        "plan_revision_ref": "plan-1",
        "topic": "Bướm",
        "drawing_subject": "Con bướm",
        "target_age_months": 54,
        "objectives": ["Quan sát"],
        "drawing_steps": [
            {"step_index": index, "action": "Vẽ một nét", "placement": "Giữa trang"}
            for index in range(1, 5)
        ],
        "subject_knowledge": ["Bướm có hai cánh"],
        "activities": [
            {"activity_ref": "activity-1", "title": "Quan sát", "description": "Cùng quan sát"}
        ],
    }
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {**data, "content_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


def _teacher_deck_output() -> dict[str, Any]:
    return {
        "steps": [
            {"step_index": index, "instruction": "Quan sát một cánh.", "placement": "Giữa trang."}
            for index in range(1, 5)
        ]
    }


def _presentation_svg_request() -> dict[str, Any]:
    data = {
        "schema_version": "sketch2life.presentation-svg-input.v1",
        "activity_title": "Vẽ một con bướm",
        "subject_text": "Con buom",
    }
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {**data, "content_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


def _presentation_svg_output() -> dict[str, Any]:
    style = {"stroke": "#1f2937", "stroke_width": 2}
    return {
        "schema_version": "sketch2life.presentation-svg-draft.v1",
        "shapes": [
            {"kind": "circle", **style, "cx": 25, "cy": 25, "r": 10},
            {"kind": "rect", **style, "x": 40, "y": 10, "w": 20, "h": 15},
            {"kind": "line", **style, "x1": 10, "y1": 60, "x2": 30, "y2": 60},
            {"kind": "ellipse", **style, "cx": 70, "cy": 70, "rx": 10, "ry": 8},
        ],
    }


def _request_and_output(workload: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if workload == "lesson.plan.suggest":
        return _lesson_request(), _lesson_output()
    if workload == "teacher.sketch-deck.generate":
        return _teacher_deck_request(), _teacher_deck_output()
    return _presentation_svg_request(), _presentation_svg_output()


def _worker_input(
    worker: Any, tmp_path: Path, workload: str, request_data: dict[str, Any]
) -> dict[str, Any]:
    worker.SCRATCH_MOUNT = str(tmp_path / "scratch")
    job_id, generation_id, attempt_id = "job-fixture", "generation-fixture", "attempt-fixture"
    attempt_prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"
    attempt_dir = Path(worker.SCRATCH_MOUNT) / attempt_prefix
    input_dir = attempt_dir / "input"
    input_dir.mkdir(parents=True)
    request_bytes = json.dumps(request_data, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    (input_dir / "request.json").write_bytes(request_bytes)
    manifest_bytes = json.dumps(
        {
            "schema_version": worker.INPUT_SCHEMA,
            "asset": {
                "path": "input/request.json",
                "content_type": "application/json",
                "size_bytes": len(request_bytes),
                "sha256": hashlib.sha256(request_bytes).hexdigest(),
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    (input_dir / "manifest.json").write_bytes(manifest_bytes)
    return {
        "schema_version": worker.WORKER_OUTPUT_SCHEMA.replace("worker-output", "worker-input"),
        "environment": "dev",
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "input_bytes": len(request_bytes) + len(manifest_bytes),
    }


def _run_through_qwen_worker(
    worker: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    workload: str,
    request_data: dict[str, Any],
    outputs: list[tuple[int, str]],
) -> tuple[dict[str, Any], _FakeLlm, Any]:
    monkeypatch.setenv("SKETCH2LIFE_QWEN_ENGINE", "vllm")
    monkeypatch.setattr(worker, "refresh_worker_volume", lambda _volume: None)
    marker_path = tmp_path / "model-marker.json"
    marker_path.write_text(
        json.dumps({"model_id": worker.TEXT_MODEL_ID, "revision": worker.TEXT_MODEL_REVISION}),
        encoding="utf-8",
    )
    monkeypatch.setattr(worker, "TEXT_MODEL_MARKER", str(marker_path))
    output_by_token = {token_id: text for token_id, text in outputs}
    tokenizer = _FakeTokenizer(output_by_token)
    processor = _FakeProcessor(tokenizer)
    llm = _FakeLlm([token_id for token_id, _text in outputs])
    model = qwen_vllm.VllmTextModel(
        llm,
        SimpleNamespace(eos_token_id=99, do_sample=False, temperature=0.0, top_p=None, top_k=None),
        make_params=lambda **params: params,
        to_tensor=_FakeTensor,
        on_engine_dead=lambda: None,
    )
    monkeypatch.setattr(worker, "_load_text_model", lambda: (processor, model))
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(inference_mode=_null_context),
    )
    payload = _worker_input(worker, tmp_path, workload, request_data)
    assert callable(worker._shared_qwen_routes()[workload])
    return worker.qwen_worker.local(payload), llm, worker


def _null_context() -> Any:
    from contextlib import nullcontext

    return nullcontext()


@pytest.mark.parametrize(
    "workload",
    [
        "lesson.plan.suggest",
        "teacher.sketch-deck.generate",
        "presentation.svg-draft.generate",
    ],
)
def test_teacher_handlers_run_through_qwen_worker_with_vllm_text_model(
    workload: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker, "_presentation_svg_draft_enabled", lambda: False)
    request_data, valid_output = _request_and_output(workload)
    output, llm, worker = _run_through_qwen_worker(
        worker,
        monkeypatch,
        tmp_path,
        workload,
        request_data,
        [(41, json.dumps(valid_output, ensure_ascii=False, separators=(",", ":")))],
    )
    if workload == "lesson.plan.suggest":
        expected_schema = worker._lesson_suggestion_json_schema(request_data)
    elif workload == "teacher.sketch-deck.generate":
        expected_schema = worker._teacher_deck_json_schema(len(request_data["drawing_steps"]))
    else:
        expected_schema = worker._presentation_svg_draft_json_schema()

    assert len(llm.calls) == 1
    assert llm.calls[0][1]["json_schema"] == expected_schema
    assert set(output) == {
        "schema_version",
        "workload",
        "job_id",
        "generation_id",
        "attempt_id",
        "model",
        "result",
    }
    assert output["schema_version"] == worker.WORKER_OUTPUT_SCHEMA
    assert output["workload"] == workload
    assert output["model"] == {"id": worker.TEXT_MODEL_ID, "revision": worker.TEXT_MODEL_REVISION}

    if workload == "lesson.plan.suggest":
        assert set(output["result"]) == {"draft_only", "content"}
        assert output["result"]["draft_only"] is True
        assert set(output["result"]["content"]) == {
            "locale",
            "title",
            "topic",
            "target_age_band_ref",
            "target_age_band_version",
            "objectives",
            "drawing_subject",
            "drawing_steps_text",
            "subject_learning_notes",
            "script_direction",
            "script_following_allowed",
            "activities",
        }
    elif workload == "teacher.sketch-deck.generate":
        assert set(output["result"]) == {
            "schema_version",
            "status",
            "plan_revision_ref",
            "content_hash",
            "aspect_ratio",
            "language",
            "topic",
            "target_age_months",
            "subject_knowledge",
            "slides",
            "approved_activity_refs",
            "review_required",
        }
    else:
        assert set(output["result"]) == {"schema_version", "review_required", "viewbox", "shapes"}


def test_occurrence_sketch_deck_adds_one_optional_svg_draft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker, "_presentation_svg_draft_enabled", lambda: True)
    output, llm, _worker = _run_through_qwen_worker(
        worker,
        monkeypatch,
        tmp_path,
        "teacher.sketch-deck.generate",
        _teacher_deck_request(),
        [
            (41, json.dumps(_teacher_deck_output(), ensure_ascii=False, separators=(",", ":"))),
            (42, json.dumps(_presentation_svg_output(), ensure_ascii=False, separators=(",", ":"))),
        ],
    )

    assert len(llm.calls) == 2
    assert llm.calls[0][1]["json_schema"] == worker._teacher_deck_json_schema(4)
    assert llm.calls[1][1]["json_schema"] == worker._presentation_svg_draft_json_schema()
    assert output["result"]["drawing"]["schema_version"] == "sketch2life.presentation-svg-draft.v1"


def test_optional_svg_draft_failure_keeps_the_text_deck_without_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker, "_presentation_svg_draft_enabled", lambda: True)
    output, llm, _worker = _run_through_qwen_worker(
        worker,
        monkeypatch,
        tmp_path,
        "teacher.sketch-deck.generate",
        _teacher_deck_request(),
        [
            (41, json.dumps(_teacher_deck_output(), ensure_ascii=False, separators=(",", ":"))),
            (42, "not-json"),
        ],
    )

    assert len(llm.calls) == 2
    assert "drawing" not in output["result"]
    assert len(output["result"]["slides"][1]["steps"]) == 4


def test_disabled_svg_capability_makes_no_extra_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker, "_presentation_svg_draft_enabled", lambda: False)
    output, llm, _worker = _run_through_qwen_worker(
        worker,
        monkeypatch,
        tmp_path,
        "teacher.sketch-deck.generate",
        _teacher_deck_request(),
        [(41, json.dumps(_teacher_deck_output(), ensure_ascii=False, separators=(",", ":")))],
    )

    assert len(llm.calls) == 1
    assert "drawing" not in output["result"]


def test_existing_local_source_skips_optional_ai_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker, "_presentation_svg_draft_enabled", lambda: True)
    request = _teacher_deck_request()
    request["drawing_source_available"] = True
    canonical = json.dumps(
        {key: value for key, value in request.items() if key != "content_hash"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    request["content_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    output, llm, _worker = _run_through_qwen_worker(
        worker,
        monkeypatch,
        tmp_path,
        "teacher.sketch-deck.generate",
        request,
        [(41, json.dumps(_teacher_deck_output(), ensure_ascii=False, separators=(",", ":")))],
    )

    assert len(llm.calls) == 1
    assert "drawing" not in output["result"]


def test_retryable_teacher_output_is_regenerated_inside_qwen_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    request_data = _lesson_request()
    valid_text = json.dumps(_lesson_output(), ensure_ascii=False, separators=(",", ":"))
    output, llm, _worker = _run_through_qwen_worker(
        worker,
        monkeypatch,
        tmp_path,
        "lesson.plan.suggest",
        request_data,
        [(40, "not-json"), (41, valid_text)],
    )

    assert output["workload"] == "lesson.plan.suggest"
    assert len(llm.calls) == 2
    assert llm.calls[0][1]["temperature"] == 0.0
    assert llm.calls[1][1]["temperature"] == qwen_vllm.SAMPLED_TEMPERATURE
    assert llm.calls[1][1]["json_schema"] == worker._lesson_suggestion_json_schema(request_data)


# Keywords that vLLM's structured-output backends (xgrammar, lm-format-enforcer) refuse.
_UNSUPPORTED_KEYWORDS = {"multipleOf", "uniqueItems", "contains", "patternProperties", "propertyNames", "format"}


def _unsupported_schema_nodes(node: Any, path: str = "$") -> list[str]:
    if isinstance(node, list):
        return [found for i, item in enumerate(node) for found in _unsupported_schema_nodes(item, f"{path}[{i}]")]
    if not isinstance(node, dict):
        return []
    found = [f"{path}.{key}" for key in _UNSUPPORTED_KEYWORDS if key in node]
    if "pattern" in node and ({"minLength", "maxLength"} & set(node)):
        found.append(f"{path}: pattern with length bounds")
    for key, child in node.items():
        if key == "properties":  # property names are data, not keywords
            for name, schema in child.items():
                found += _unsupported_schema_nodes(schema, f"{path}.{name}")
        else:
            found += _unsupported_schema_nodes(child, f"{path}.{key}")
    return found


def test_no_teacher_schema_uses_what_vllm_structured_output_refuses() -> None:
    worker = _load_worker()
    schemas = [worker._presentation_svg_draft_json_schema()]
    schemas += [worker._teacher_deck_json_schema(steps) for steps in range(4, 9)]
    for count in range(1, 7):
        for script in (False, True):
            request = {**_lesson_request(), "activity_count": count, "script_following_allowed": script}
            schemas.append(worker._lesson_suggestion_json_schema(request))

    assert [found for schema in schemas for found in _unsupported_schema_nodes(schema)] == []
    assert _unsupported_schema_nodes({"type": "string", "pattern": "a", "maxLength": 1})


@pytest.mark.parametrize(
    "workload",
    ["lesson.plan.suggest", "teacher.sketch-deck.generate", "presentation.svg-draft.generate"],
)
def test_every_schema_sent_by_qwen_worker_is_accepted_shape_including_retries(
    workload: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _load_worker()
    monkeypatch.setattr(worker, "_presentation_svg_draft_enabled", lambda: False)
    request_data, valid_output = _request_and_output(workload)
    text = json.dumps(valid_output, ensure_ascii=False, separators=(",", ":"))
    outputs = [(40, "not-json"), (41, text)]
    if workload == "presentation.svg-draft.generate":
        outputs = [(41, text)]  # its rejection is not retried
    _output, llm, _worker = _run_through_qwen_worker(
        worker, monkeypatch, tmp_path, workload, request_data, outputs
    )

    assert len(llm.calls) == len(outputs)
    for _prompts, params in llm.calls:
        assert _unsupported_schema_nodes(params["json_schema"]) == []


def test_the_shipped_registry_enables_the_optional_svg_draft() -> None:
    assert _load_worker()._presentation_svg_draft_enabled() is True
