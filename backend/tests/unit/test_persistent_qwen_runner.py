from __future__ import annotations

import os
import time
from multiprocessing.connection import Connection
from pathlib import Path

from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision import (
    PersistentSubprocessQwenGenerationRunner,
    QwenTimeoutError,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig


def _fake_persistent_worker(connection: Connection) -> None:
    generation_count = 0
    try:
        while True:
            message = connection.recv()
            if message == ("stop",):
                return
            generation_count += 1
            _profile, _runtime, _image_path, prompt = message
            connection.send(("success", f"{os.getpid()}:{generation_count}:{prompt}"))
    finally:
        connection.close()


def _slow_persistent_worker(connection: Connection) -> None:
    try:
        connection.recv()
        time.sleep(2)
        connection.send(("success", "late result"))
    finally:
        connection.close()


def test_persistent_runner_reuses_one_worker_for_multiple_generations() -> None:
    profile = vision_profile_catalog_v2().resolve(
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1
    )
    runtime = QwenVisionRuntimeConfig(model_cache_dir=Path("cache"))
    runner = PersistentSubprocessQwenGenerationRunner(
        worker_target=_fake_persistent_worker
    )

    try:
        first = runner.generate(profile, runtime, None, "first")
        second = runner.generate(profile, runtime, None, "second")
        first_pid, first_count, first_prompt = first.split(":", maxsplit=2)
        second_pid, second_count, second_prompt = second.split(":", maxsplit=2)

        assert first_pid == second_pid
        assert first_count == "1"
        assert second_count == "2"
        assert first_prompt == "first"
        assert second_prompt == "second"
    finally:
        runner.close()

    assert runner._process is None
    assert runner._connection is None


def test_persistent_runner_terminates_worker_after_generation_deadline() -> None:
    profile = vision_profile_catalog_v2().resolve(
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1
    ).model_copy(update={"timeout_seconds": 0.25})
    runtime = QwenVisionRuntimeConfig(model_cache_dir=Path("cache"))
    runner = PersistentSubprocessQwenGenerationRunner(
        worker_target=_slow_persistent_worker
    )

    try:
        try:
            runner.generate(profile, runtime, None, "slow")
        except QwenTimeoutError:
            pass
        else:
            raise AssertionError("runner must enforce the model generation deadline")
    finally:
        runner.close()

    assert runner._process is None
    assert runner._connection is None
