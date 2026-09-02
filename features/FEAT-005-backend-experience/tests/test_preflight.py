import unittest
from unittest.mock import patch

from learning_video.preflight_support import check_settings
from learning_video.settings import AppSettings


def make_settings(provider: str = "wan2.2") -> AppSettings:
    return AppSettings.model_validate(
        {
            "wan": {
                "provider": provider,
                "model_name": "Wan2.2-TI2V-5B",
                "python_binary": "python",
                "inference_script": "/missing/generate.py",
                "checkpoint_dir": "/missing/checkpoint",
                "output_dir": "/tmp/output",
                "offload_model": True,
                "convert_model_dtype": True,
                "t5_cpu": True,
            },
            "video": {"min_duration_sec": 5, "max_duration_sec": 10, "width": 1280, "height": 704, "fps": 24},
            "runtime": {"max_retries": 1},
        }
    )


class PreflightTest(unittest.TestCase):
    @patch("learning_video.preflight_support.shutil.which", return_value=None)
    def test_reports_missing_runtime_dependencies(self, _: object) -> None:
        problems = check_settings(make_settings())
        self.assertTrue(any("inference script" in problem for problem in problems))
        self.assertTrue(any("checkpoint" in problem for problem in problems))
        self.assertTrue(any("ffmpeg" in problem for problem in problems))

    def test_mock_provider_is_rejected_for_real_preflight(self) -> None:
        problems = check_settings(make_settings("mock"))
        self.assertTrue(any("provider" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
