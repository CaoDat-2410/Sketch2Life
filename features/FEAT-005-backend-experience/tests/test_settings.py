import importlib.util
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from learning_video.settings import load_settings


CONFIG = Path(__file__).parents[1] / "config"


@unittest.skipUnless(importlib.util.find_spec("yaml"), "PyYAML is not installed")
class SettingsTest(unittest.TestCase):
    def test_loads_test_profile(self) -> None:
        settings = load_settings(CONFIG / "test.yaml")

        self.assertEqual(settings.wan.model_name, "mock")
        self.assertEqual(settings.video.width, 320)
        self.assertEqual(settings.video.height, 176)
        self.assertEqual(settings.runtime.max_retries, 1)

    def test_rejects_invalid_duration_range(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "invalid-test.yaml"
            settings_path.write_text(
                (CONFIG / "test.yaml")
                .read_text(encoding="utf-8")
                .replace("min_duration_sec: 5", "min_duration_sec: 11"),
                encoding="utf-8",
            )
            with self.assertRaises((ValidationError, ValueError)):
                load_settings(settings_path)

    def test_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "invalid-test.yaml"
            settings_path.write_text(
                (CONFIG / "test.yaml")
                .read_text(encoding="utf-8")
                .replace("wan:\n", "wan:\n  unexpected: true\n"),
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                load_settings(settings_path)


if __name__ == "__main__":
    unittest.main()
