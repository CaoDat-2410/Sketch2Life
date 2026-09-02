"""Subprocess adapter for the official Wan2.2 TI2V-5B generator."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .schemas import GeneratedVideo, GenerationBrief, ProvenanceMetadata


class WanGenerationError(RuntimeError):
    """Raised when Wan2.2 cannot produce the requested video artifact."""


@dataclass(frozen=True)
class Wan2GeneratorConfig:
    """Runtime settings needed to invoke Wan2.2 without shell interpolation."""

    python_binary: str
    inference_script: Path
    checkpoint_dir: Path
    output_dir: Path
    width: int = 1280
    height: int = 704
    offload_model: bool = True
    convert_model_dtype: bool = True
    t5_cpu: bool = True
    timeout_sec: int = 1800


class Wan2Generator:
    """GenerationProvider implementation backed by Wan2.2's ``generate.py``."""

    provider_name = "wan2.2"
    model_name = "Wan2.2-TI2V-5B"

    def __init__(self, config: Wan2GeneratorConfig) -> None:
        if config.width <= 0 or config.height <= 0:
            raise ValueError("Wan2.2 output dimensions must be positive")
        if config.timeout_sec <= 0:
            raise ValueError("Wan2.2 timeout_sec must be positive")
        self.config = config

    def build_command(self, brief: GenerationBrief, output_path: Path) -> list[str]:
        """Build the official Wan2.2 CLI command as an argv list."""

        command = [
            self.config.python_binary,
            str(self.config.inference_script),
            "--task",
            "ti2v-5B",
            "--size",
            f"{self.config.width}*{self.config.height}",
            "--ckpt_dir",
            str(self.config.checkpoint_dir),
            "--save_file",
            str(output_path),
            "--prompt",
            brief.prompt,
        ]
        if self.config.offload_model:
            command.extend(["--offload_model", "True"])
        if self.config.convert_model_dtype:
            command.append("--convert_model_dtype")
        if self.config.t5_cpu:
            command.append("--t5_cpu")

        frame_num = brief.profile.get("frame_num")
        if frame_num is not None:
            if not isinstance(frame_num, int) or isinstance(frame_num, bool) or frame_num < 1:
                raise ValueError("frame_num must be a positive integer")
            if frame_num % 4 != 1:
                raise ValueError("Wan2.2 frame_num must satisfy frame_num % 4 == 1")
            command.extend(["--frame_num", str(frame_num)])
        return command

    def generate(self, brief: GenerationBrief) -> GeneratedVideo:
        artifact_id = f"WAN-{brief.objective_id}-{brief.objective_version}"
        output_path = self.config.output_dir / f"{artifact_id}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = self.build_command(brief, output_path)

        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_sec,
            )
        except FileNotFoundError as exc:
            raise WanGenerationError("Wan2.2 Python binary or inference script was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise WanGenerationError("Wan2.2 generation timed out") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "Wan2.2 process failed").strip()
            raise WanGenerationError(detail[-1000:]) from exc

        if not output_path.is_file():
            stdout = (completed.stdout or "").strip()
            raise WanGenerationError(
                "Wan2.2 completed without creating --save_file output"
                + (f": {stdout[-500:]}" if stdout else "")
            )

        return GeneratedVideo(
            artifact_id=artifact_id,
            objective_id=brief.objective_id,
            objective_version=brief.objective_version,
            output_path=output_path.as_posix(),
            duration_sec=float(brief.duration_sec),
            provider=self.provider_name,
            provenance=ProvenanceMetadata(
                source="wan2.2_generator",
                model_name=self.model_name,
                model_version="TI2V-5B",
                config_hash=self._config_hash(),
            ),
        )

    def _config_hash(self) -> str:
        values = {
            "model_name": self.model_name,
            "width": self.config.width,
            "height": self.config.height,
            "offload_model": self.config.offload_model,
            "convert_model_dtype": self.config.convert_model_dtype,
            "t5_cpu": self.config.t5_cpu,
        }
        encoded = json.dumps(values, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]
