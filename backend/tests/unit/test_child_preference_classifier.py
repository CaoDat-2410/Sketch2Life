from __future__ import annotations

from pathlib import Path

import pytest

from sketch2life.contracts.schemas.child_preference_classification import (
    ChildPreferenceClassificationRequestV1,
)
from sketch2life.infrastructure.ai.qwen_child_preference_classifier import (
    QwenChildPreferenceClassifier,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig


class _FakeRunner:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls = 0
        self.prompt = ""

    def generate(self, profile, runtime_config, image_path, prompt):
        del profile, runtime_config
        assert image_path is None
        self.calls += 1
        self.prompt = prompt
        return self.output


def _request() -> ChildPreferenceClassificationRequestV1:
    return ChildPreferenceClassificationRequestV1(
        request_id="synthetic-preference-1",
        interest_text="thích ngắm chim và nghe tiếng chim",
        avoid_text="không thích hoạt động có côn trùng thật",
    )


def test_classifier_returns_only_adult_reviewable_allowlisted_tags() -> None:
    runner = _FakeRunner(
        '{"interest_tags":[{"concept_id":"ANIMAL_GENERIC","confidence":0.87},'
        '{"concept_id":"INVENTED_TAG","confidence":0.99}],"avoid_tags":[]}'
    )
    classifier = QwenChildPreferenceClassifier(
        QwenVisionRuntimeConfig(model_dir=None, model_cache_dir=Path("cache")),
        generation_runner=runner,
    )

    result = classifier.classify(_request())

    assert runner.calls == 1
    assert result.interest_tags[0].concept_id == "ANIMAL_GENERIC"
    assert result.interest_tags[0].label_vi == "Động vật"
    assert result.interest_tags[0].confidence == 0.87
    assert result.avoid_tags == ()
    assert result.interest_unmapped is True
    assert "INVENTED_TAG" not in result.model_dump_json()
    assert "diagnosis" in runner.prompt


def test_classifier_rejects_non_json_or_extra_output_without_retry() -> None:
    runner = _FakeRunner('{"interest_tags":[],"avoid_tags":[],"activity":"invented"}')
    classifier = QwenChildPreferenceClassifier(
        QwenVisionRuntimeConfig(model_cache_dir=Path("cache")),
        generation_runner=runner,
    )

    with pytest.raises(ValueError, match="shape"):
        classifier.classify(_request())
    assert runner.calls == 1
