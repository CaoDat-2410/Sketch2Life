"""Create a generation provider from validated application settings."""

from __future__ import annotations

from .generator_client import GenerationProvider, MockGenerator
from .settings import AppSettings
from .wan_generator import Wan2Generator, Wan2GeneratorConfig


def create_generation_provider(settings: AppSettings) -> GenerationProvider:
    """Return the configured generator without changing pipeline code."""

    if settings.wan.provider == "mock":
        return MockGenerator()
    if settings.wan.provider == "wan2.2":
        return Wan2Generator(
            Wan2GeneratorConfig(
                python_binary=settings.wan.python_binary,
                inference_script=settings.wan.inference_script,
                checkpoint_dir=settings.wan.checkpoint_dir,
                output_dir=settings.wan.output_dir,
                width=settings.video.width,
                height=settings.video.height,
                offload_model=settings.wan.offload_model,
                convert_model_dtype=settings.wan.convert_model_dtype,
                t5_cpu=settings.wan.t5_cpu,
            )
        )
    raise ValueError(f"unsupported generation provider: {settings.wan.provider}")
