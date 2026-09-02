import json
from pathlib import Path

from learning_video.generator_client import MockGenerator
from learning_video.schemas import GeneratedVideo, GenerationBrief


BRIEF_PATH = (
    Path(__file__).parents[1] / "fixtures/objectives/butterfly_generation_brief.json"
)


def load_brief() -> GenerationBrief:
    return GenerationBrief.model_validate(json.loads(BRIEF_PATH.read_text(encoding="utf-8")))


def test_mock_generator_returns_bounded_generated_video_metadata() -> None:
    result = MockGenerator().generate(load_brief())

    assert isinstance(result, GeneratedVideo)
    assert result.provider == "mock"
    assert result.artifact_id == "MOCK-butterfly_proboscis-v1"
    assert result.duration_sec == 8
    assert result.output_path.endswith("MOCK-butterfly_proboscis-v1.mp4")


def test_mock_generator_is_deterministic() -> None:
    generator = MockGenerator()
    first = generator.generate(load_brief())
    second = generator.generate(load_brief())

    assert first.model_dump() == second.model_dump()
