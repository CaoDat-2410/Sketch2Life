import json
import unittest
from pathlib import Path

from learning_video.generator_client import MockGenerator
from learning_video.prompt_compiler import GenerationBriefCompiler
from learning_video.schemas import GeneratedVideo, GenerationBrief, LearningObjective


BRIEF_PATH = (
    Path(__file__).parents[1] / "fixtures/objectives/butterfly_generation_brief.json"
)


def load_brief() -> GenerationBrief:
    return GenerationBrief.model_validate(json.loads(BRIEF_PATH.read_text(encoding="utf-8")))


class GenerationTest(unittest.TestCase):
    def test_mock_generator_returns_bounded_generated_video_metadata(self) -> None:
        result = MockGenerator().generate(load_brief())

        self.assertIsInstance(result, GeneratedVideo)
        self.assertEqual(result.provider, "mock")
        self.assertEqual(result.artifact_id, "MOCK-butterfly_proboscis-v1")
        self.assertEqual(result.duration_sec, 8)
        self.assertTrue(result.output_path.endswith("MOCK-butterfly_proboscis-v1.mp4"))


    def test_mock_generator_is_deterministic(self) -> None:
        generator = MockGenerator()
        first = generator.generate(load_brief())
        second = generator.generate(load_brief())

        self.assertEqual(first.model_dump(), second.model_dump())


    def test_generation_brief_compiler_preserves_objective_identity(self) -> None:
        objective = LearningObjective(
            objective_id="butterfly_proboscis",
            version="v1",
            locale="vi-VN",
            age_band="3-6",
            concept="Bướm dùng vòi để hút mật từ hoa",
        )

        brief = GenerationBriefCompiler().compile(objective)

        self.assertEqual(brief.objective_id, objective.objective_id)
        self.assertEqual(brief.objective_version, objective.version)
        self.assertEqual(brief.duration_sec, 8)
        self.assertIn("proboscis", brief.show)


if __name__ == "__main__":
    unittest.main()
