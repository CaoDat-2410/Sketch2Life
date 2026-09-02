import unittest
from pathlib import Path

from learning_video.generator_client import MockGenerator
from learning_video.provider_factory import create_generation_provider
from learning_video.settings import AppSettings
from learning_video.wan_generator import Wan2Generator


def settings(provider: str) -> AppSettings:
    return AppSettings.model_validate(
        {
            "wan": {
                "provider": provider,
                "model_name": "mock" if provider == "mock" else "Wan2.2-TI2V-5B",
                "python_binary": "python",
                "inference_script": "/opt/Wan2.2/generate.py",
                "checkpoint_dir": "/models/Wan2.2-TI2V-5B",
                "output_dir": "/tmp/learning-video-output",
                "offload_model": True,
                "convert_model_dtype": True,
                "t5_cpu": True,
            },
            "video": {
                "min_duration_sec": 5,
                "max_duration_sec": 10,
                "width": 1280,
                "height": 704,
                "fps": 24,
            },
            "runtime": {"max_retries": 1},
        }
    )


class ProviderFactoryTest(unittest.TestCase):
    def test_test_profile_selects_mock(self) -> None:
        provider = create_generation_provider(settings("mock"))
        self.assertIsInstance(provider, MockGenerator)

    def test_wan_profile_selects_wan_adapter(self) -> None:
        provider = create_generation_provider(settings("wan2.2"))
        self.assertIsInstance(provider, Wan2Generator)
        self.assertEqual(provider.config.width, 1280)
        self.assertEqual(provider.config.height, 704)
        self.assertEqual(provider.config.output_dir, Path("/tmp/learning-video-output"))


if __name__ == "__main__":
    unittest.main()
