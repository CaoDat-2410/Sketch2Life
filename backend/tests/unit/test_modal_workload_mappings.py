"""Every workload name that the backend sends to the Modal JSON client must be mapped."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sketch2life.infrastructure.ai import modal_function_client as client
from sketch2life.infrastructure.config.settings import Settings

_SOURCE = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
# lesson.visual.generate is still called by teacher_ai /lesson-visuals but has no mapping, the
# same as on origin/dev (the lesson-picture feature is removed from the web).
_KNOWN_UNMAPPED = {"lesson.visual.generate"}


def _invoked_workloads() -> set[str]:
    names: set[str] = set()
    for path in _SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        constants = {
            target.id: node.value.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "invoke"
                and node.args
            ):
                continue
            first = node.args[0]
            value = (
                first.value
                if isinstance(first, ast.Constant)
                else constants.get(first.id)
                if isinstance(first, ast.Name)
                else None
            )
            if isinstance(value, str) and "." in value:
                names.add(value)
    return names


def test_every_invoked_workload_has_a_mapping() -> None:
    invoked = _invoked_workloads()

    assert "presentation.svg-draft.generate" in invoked
    assert "teacher.sketch-deck.generate" in invoked
    assert invoked - set(client._JSON_WORKERS) <= _KNOWN_UNMAPPED


def test_teacher_ai_engine_uses_the_central_settings_default() -> None:
    assert Settings.model_fields["teacher_ai_engine"].default == "vllm"


def test_presentation_svg_draft_maps_to_a_deployed_function() -> None:
    app_name, function_name, _timeout = client._JSON_WORKERS["presentation.svg-draft.generate"]
    deployment = _SOURCE.parents[2] / "deployment" / "modal" / "srs_v23" / "language_audio_app.py"

    assert app_name == "sketch2life-srs23-language-audio-dev"
    assert f'name="{function_name}"' in deployment.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("workload", "fallback_name"),
    [
        ("lesson.plan.suggest", "suggest-lesson-plan"),
        ("teacher.sketch-deck.generate", "generate-teacher-sketch-deck"),
        ("presentation.svg-draft.generate", "generate-presentation-svg-draft"),
    ],
)
def test_teacher_workloads_default_to_qwen_and_can_select_transformers(
    workload: str, fallback_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SKETCH2LIFE_TEACHER_AI_ENGINE", raising=False)
    assert client._json_worker_for_invoke(workload) == (
        client.APP_NAME,
        client.FUNCTION_NAME,
        1_800,
    )

    monkeypatch.setenv("SKETCH2LIFE_TEACHER_AI_ENGINE", "transformers")
    assert client._json_worker_for_invoke(workload) == (
        client.APP_NAME,
        fallback_name,
        1_800,
    )


def test_invalid_teacher_engine_fails_closed_with_a_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_TEACHER_AI_ENGINE", "other")

    with pytest.raises(
        ValueError,
        match="SKETCH2LIFE_TEACHER_AI_ENGINE must be 'vllm' or 'transformers'",
    ):
        client._json_worker_for_invoke("lesson.plan.suggest")


def test_parent_workloads_ignore_the_teacher_engine_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent_workers = {
        "parent.topic-subjects.validate": (client.APP_NAME, client.FUNCTION_NAME, 1_800),
        "parent.activity.suggest": (client.APP_NAME, client.FUNCTION_NAME, 1_200),
    }
    monkeypatch.setenv("SKETCH2LIFE_TEACHER_AI_ENGINE", "invalid")

    for workload, expected in parent_workers.items():
        assert client._JSON_WORKERS[workload] == expected
        assert client._json_worker_for_invoke(workload) == expected


def test_teacher_transformers_functions_remain_deployed() -> None:
    deployment = _SOURCE.parents[2] / "deployment" / "modal" / "srs_v23" / "language_audio_app.py"
    source = deployment.read_text(encoding="utf-8")

    for name in (
        "suggest-lesson-plan",
        "generate-teacher-sketch-deck",
        "generate-presentation-svg-draft",
    ):
        assert f'name="{name}"' in source
