from __future__ import annotations

from pathlib import Path

from sketch2life.infrastructure.ai.sam21_runtime import Sam21RuntimeConfig


def test_sam21_config_resolves_checkpoint_and_config_from_model_dir(tmp_path: Path) -> None:
    model_dir = tmp_path / "sam2.1-hiera-small"
    config_path = model_dir / "configs" / "sam2.1" / "sam2.1_hiera_s.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("model: test\n", encoding="utf-8")
    checkpoint_path = model_dir / "sam2.1_hiera_small.pt"
    checkpoint_path.write_bytes(b"fixture")

    config = Sam21RuntimeConfig.from_env(
        {
            "SAM2_MODEL_DIR": str(model_dir),
            "SKETCH2LIFE_SAM21_CHECKPOINT": str(model_dir / "renamed.pt"),
            "SKETCH2LIFE_SAM21_MODEL_CONFIG": "configs/sam2.1/sam2.1_hiera_s.yaml",
            "SKETCH2LIFE_SAM21_DEVICE": "cuda",
        }
    )

    assert config.checkpoint == checkpoint_path.resolve()
    assert config.model_config == str(config_path.resolve())
    assert config.device == "cuda"


def test_sam21_config_keeps_installed_package_config_name_when_not_local(tmp_path: Path) -> None:
    missing_checkpoint = tmp_path / "missing" / "sam2.1_hiera_small.pt"
    config = Sam21RuntimeConfig.from_env(
        {
            "SKETCH2LIFE_SAM21_CHECKPOINT": str(missing_checkpoint),
            "SKETCH2LIFE_SAM21_MODEL_CONFIG": "configs/sam2.1/sam2.1_hiera_s.yaml",
        }
    )

    assert config.checkpoint == missing_checkpoint.resolve()
    assert config.model_config == "configs/sam2.1/sam2.1_hiera_s.yaml"
