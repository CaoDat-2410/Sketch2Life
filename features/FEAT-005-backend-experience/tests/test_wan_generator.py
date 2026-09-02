import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from learning_video.schemas import GenerationBrief
from learning_video.wan_generator import Wan2Generator, Wan2GeneratorConfig, WanGenerationError


BRIEF_PATH = Path(__file__).parents[1] / "fixtures/objectives/butterfly_generation_brief.json"


def load_brief(**overrides: object) -> GenerationBrief:
    data = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))
    data.update(overrides)
    return GenerationBrief.model_validate(data)


class WanGeneratorTest(unittest.TestCase):
    def make_generator(self, output_dir: Path) -> Wan2Generator:
        return Wan2Generator(
            Wan2GeneratorConfig(
                python_binary="python",
                inference_script=Path("/opt/Wan2.2/generate.py"),
                checkpoint_dir=Path("/models/Wan2.2-TI2V-5B"),
                output_dir=output_dir,
            )
        )

    def test_build_command_uses_official_ti2v_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generator = self.make_generator(Path(directory))
            command = generator.build_command(load_brief(profile={"frame_num": 121}), Path(directory) / "out.mp4")

        self.assertEqual(command[:4], ["python", "/opt/Wan2.2/generate.py", "--task", "ti2v-5B"])
        self.assertIn("--offload_model", command)
        self.assertIn("--convert_model_dtype", command)
        self.assertIn("--t5_cpu", command)
        self.assertIn("--frame_num", command)
        self.assertIn("121", command)
        self.assertIn("--save_file", command)

    def test_generate_returns_metadata_when_save_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            generator = self.make_generator(output_dir)

            def fake_run(command: list[str], **_: object) -> object:
                output = Path(command[command.index("--save_file") + 1])
                output.write_bytes(b"synthetic mp4")
                return type("Completed", (), {"stdout": "saved", "stderr": ""})()

            with patch("learning_video.wan_generator.subprocess.run", side_effect=fake_run) as run:
                result = generator.generate(load_brief())
                self.assertTrue(Path(result.output_path).is_file())

        run.assert_called_once()
        self.assertEqual(result.provider, "wan2.2")
        self.assertEqual(result.provenance.model_name, "Wan2.2-TI2V-5B")

    def test_generate_fails_when_process_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generator = self.make_generator(Path(directory))
            with patch("learning_video.wan_generator.subprocess.run"):
                with self.assertRaisesRegex(WanGenerationError, "without creating"):
                    generator.generate(load_brief())

    def test_frame_num_must_follow_wan_constraint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generator = self.make_generator(Path(directory))
            with self.assertRaisesRegex(ValueError, "frame_num"):
                generator.build_command(load_brief(profile={"frame_num": 120}), Path(directory) / "out.mp4")


if __name__ == "__main__":
    unittest.main()
