import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from learning_video.frame_sampler import FrameSampler
from learning_video.schemas import ValidationStatus


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "ffmpeg and ffprobe are required for media integration tests",
)
class FrameSamplerIntegrationTest(unittest.TestCase):
    def test_real_video_produces_five_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "valid.mp4"
            frames = root / "frames"
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=blue:s=320x176:r=8",
                    "-t", "8", "-pix_fmt", "yuv420p", str(video),
                ],
                check=True,
            )

            result = FrameSampler().sample(video, frames)

            self.assertIs(result.status, ValidationStatus.PASS)
            self.assertEqual(len(result.sampled_frame_paths), 5)
            self.assertTrue(all(Path(path).is_file() for path in result.sampled_frame_paths))


if __name__ == "__main__":
    unittest.main()
