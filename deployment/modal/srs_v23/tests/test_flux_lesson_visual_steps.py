"""The approved-lesson picture generates one cumulative panel per drawing step."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

_MODULE_DIR = Path(__file__).resolve().parents[1]


def _load() -> ModuleType:
    pytest.importorskip("modal")
    sys.path.insert(0, str(_MODULE_DIR))
    spec = importlib.util.spec_from_file_location(
        "sketch2life_flux_lesson_visual_steps", _MODULE_DIR / "flux_image_app.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _data(count: int) -> dict[str, object]:
    return {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": "plan-1",
        "content_hash": "a" * 64,
        "topic": "butterfly",
        "steps": [
            {"step_index": n, "instruction": f"Draw part {n}", "placement": "centre"}
            for n in range(1, count + 1)
        ],
    }


@pytest.mark.parametrize("count", [3, 4, 5, 8])
def test_three_to_eight_steps_are_accepted(count: int) -> None:
    _load()._validate_lesson_visual_input(_data(count))


@pytest.mark.parametrize("count", [2, 9])
def test_other_step_counts_are_refused(count: int) -> None:
    worker = _load()
    with pytest.raises(worker.WorkerContractError):
        worker._validate_lesson_visual_input(_data(count))


def test_a_step_as_long_as_the_backend_allows_is_accepted_and_longer_refused() -> None:
    worker = _load()
    data = _data(4)
    data["steps"][0]["instruction"] = "a" * 240
    worker._validate_lesson_visual_input(data)
    data["steps"][0]["instruction"] = "a" * 241
    with pytest.raises(worker.WorkerContractError):
        worker._validate_lesson_visual_input(data)


@pytest.mark.parametrize(
    ("count", "grid"),
    [
        (3, (1, 3)),
        (5, (2, 3)),
        (8, (2, 4)),
    ],
)
def test_worker_generates_a_cumulative_panel_per_step_and_keeps_its_contract(
    count: int,
    grid: tuple[int, int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PIL import Image

    worker = _load()
    data = _data(count)
    request = SimpleNamespace(
        workload="lesson.visual.generate",
        job_id="job-1",
        generation_id="generation-1",
        attempt_id="attempt-1",
    )
    monkeypatch.setattr(worker, "_require_flux3_enabled", lambda: None)
    monkeypatch.setattr(
        worker,
        "parse_worker_input",
        lambda _payload, execution_group: request,
    )
    monkeypatch.setattr(worker, "refresh_worker_volume", lambda _volume: None)
    monkeypatch.setattr(worker, "_read_json_asset", lambda _request: data)
    monkeypatch.setattr(worker, "_verify_marker", lambda: None)

    runtime_calls: list[dict[str, object]] = []
    generated_panels: list[tuple[str, int, int]] = []
    colors = [
        (220, 30, 30),
        (20, 160, 50),
        (30, 70, 220),
        (210, 130, 20),
        (150, 40, 170),
        (20, 150, 160),
        (120, 100, 30),
        (200, 70, 100),
    ]

    @contextmanager
    def fake_runtime(
        prompts: list[str], *, height: int, width: int, seed: int
    ):
        runtime_calls.append(
            {"prompts": list(prompts), "height": height, "width": width, "seed": seed}
        )

        def generate_panel(prompt: str, index: int) -> tuple[Image.Image, str]:
            generated_panels.append((prompt, index, seed))
            return Image.new("RGB", (120, 80), colors[index]), f"expanded:{index}:{prompt}"

        yield generate_panel

    monkeypatch.setattr(worker, "_load_flux3_panel_runtime", fake_runtime)
    output = worker.generate_approved_lesson_visual_candidate.local({})

    prompts = runtime_calls[0]["prompts"]
    assert len(runtime_calls) == 1
    assert runtime_calls[0]["height"] == 512
    assert runtime_calls[0]["width"] == 512
    assert runtime_calls[0]["seed"] == 20261105
    assert len(generated_panels) == count
    assert [index for _, index, _ in generated_panels] == list(range(count))
    assert {seed for _, _, seed in generated_panels} == {20261105}
    assert [prompt for prompt, _, _ in generated_panels] == prompts

    style_sentences = {prompt.rsplit("\n", maxsplit=1)[-1] for prompt in prompts}
    assert style_sentences == {worker._LESSON_VISUAL_STYLE_SENTENCE}
    for completed_step, prompt in enumerate(prompts, start=1):
        for step_index in range(1, completed_step + 1):
            assert f"Draw part {step_index}" in prompt
        if completed_step < count:
            assert f"Draw part {completed_step + 1}" not in prompt

    expected_expanded_prompts = [
        f"expanded:{index}:{prompt}" for index, prompt in enumerate(prompts)
    ]
    assert output["prompt_sha256"] == hashlib.sha256(
        "\0".join(expected_expanded_prompts).encode("utf-8")
    ).hexdigest()

    assert set(output) == {
        "schema_version",
        "workload",
        "job_id",
        "generation_id",
        "attempt_id",
        "model",
        "prompt_sha256",
        "plan_revision_ref",
        "content_hash",
        "status",
        "review_required",
        "asset",
        "limitations",
    }
    asset = output["asset"]
    assert set(asset) == {
        "content_type",
        "size_bytes",
        "sha256",
        "width",
        "height",
        "bytes",
    }
    assert asset["content_type"] == "image/png"
    assert asset["width"] == 768
    assert asset["height"] == 432
    assert asset["size_bytes"] == len(asset["bytes"])
    assert asset["sha256"] == hashlib.sha256(asset["bytes"]).hexdigest()

    image = Image.open(io.BytesIO(asset["bytes"]))
    assert image.size == (768, 432)
    rows, columns = grid
    assert worker._lesson_visual_grid(count) == grid
    cell_width = image.width // columns
    cell_height = image.height // rows
    for index in range(count):
        row, column = divmod(index, columns)
        left = column * cell_width
        top = row * cell_height
        assert image.getpixel((left + cell_width // 2, top)) == (32, 32, 32)
        assert image.getpixel((left + cell_width // 2, top + 1)) == (255, 255, 255)
        assert image.getpixel((left + cell_width // 2, top + cell_height // 2)) == colors[
            index
        ]
    bottom_right = (255, 255, 255) if count == 5 else (32, 32, 32)
    assert image.getpixel((image.width - 1, image.height - 1)) == bottom_right
