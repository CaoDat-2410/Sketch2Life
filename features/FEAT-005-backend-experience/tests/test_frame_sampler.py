import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from learning_video.frame_sampler import FrameSampler
from learning_video.schemas import ValidationStatus


class FrameSamplerTest(unittest.TestCase):
    def test_samples_all_five_percentages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "video.mp4"
            video.write_bytes(b"synthetic video placeholder")

            def fake_run(command, **kwargs):
                if command[0] == "ffprobe":
                    return type("Result", (), {"stdout": "8.0\n"})()
                Path(command[-1]).write_bytes(b"synthetic frame")
                return type("Result", (), {})()

            with patch("learning_video.frame_sampler.subprocess.run", side_effect=fake_run):
                result = FrameSampler().sample(video, root / "frames")

            self.assertIs(result.status, ValidationStatus.PASS)
            self.assertEqual(result.sample_percentages, [0, 25, 50, 75, 100])
            self.assertEqual(len(result.sampled_frame_paths), 5)

    def test_blocks_video_outside_duration_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "video.mp4"
            video.write_bytes(b"synthetic video placeholder")

            def fake_run(command, **kwargs):
                return type("Result", (), {"stdout": "11.0\n"})()

            with patch("learning_video.frame_sampler.subprocess.run", side_effect=fake_run):
                result = FrameSampler().sample(video, root / "frames")

            self.assertIs(result.status, ValidationStatus.BLOCK)
            self.assertEqual(result.reason_codes, ["DURATION_OUT_OF_BOUNDS"])


if __name__ == "__main__":
    unittest.main()
