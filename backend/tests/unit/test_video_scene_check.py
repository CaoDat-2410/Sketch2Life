"""FEAT-094 phase 5: rendered scenes are looked at (report first; regeneration only when enforced)."""

from __future__ import annotations

import hashlib
import threading
from typing import Any

import pytest

import sketch2life.infrastructure.story_video.modal_scene_check as module
from sketch2life.application.video_pipeline.orchestrator import VideoPipeline
from sketch2life.application.video_pipeline.ports import PreparedScene, SceneClip, VideoPipelineError

from test_modal_scene_preparation import _Volume
from test_video_pipeline_orchestrator import (
    _Assembler,
    _draft,
    _Generator,
    _Narration,
    _Prep,
    _Render,
    _source,
    _Validator,
)


class _SeedRender(_Render):
    def __init__(self) -> None:
        super().__init__()
        self.seeds: list[tuple[int, int]] = []

    def render(self, job):
        self.seeds.append((job.scene.index, job.scene.seed))
        return super().render(job)


class _Check:
    def __init__(self, bad: dict[int, int] | None = None, error: Exception | None = None) -> None:
        self.bad = dict(bad or {})  # scene index -> how many times it is reported bad
        self.error = error
        self.calls: list[int] = []

    def check(self, clip: SceneClip, keyframe_png: bytes) -> tuple[str, ...]:
        self.calls.append(clip.scene_index)
        if self.error:
            raise self.error
        if self.bad.get(clip.scene_index, 0):
            self.bad[clip.scene_index] -= 1
            return ("NEW_CHARACTER",)
        return ()


def _run(check: Any, mode: str, render: Any = None, **options: Any) -> Any:
    pipeline = VideoPipeline(
        timeline_generator=_Generator(_draft()), preparation=_Prep(), renderer=render or _SeedRender(),
        narration=_Narration(), assembler=_Assembler(), validator=_Validator(),
        scene_check=check, check_mode=mode, **options,
    )
    return pipeline.run(_source())


def test_report_mode_records_the_findings_and_changes_nothing() -> None:
    render = _SeedRender()
    result = _run(_Check({2: 9}), "report", render)

    assert result.findings == {2: ("NEW_CHARACTER",)}
    assert [index for index, _seed in render.seeds] == [1, 2, 3, 4, 5]


@pytest.mark.parametrize("mode, check", [("off", _Check({1: 1})), ("report", None)])
def test_no_check_runs_when_switched_off_or_missing(mode: str, check: Any) -> None:
    result = _run(check, mode)

    assert result.findings == {} and (check is None or check.calls == [])


def test_a_check_that_cannot_run_never_fails_the_video() -> None:
    result = _run(_Check(error=VideoPipelineError("VIDEO_SCENE_CHECK_FAILED")), "report")

    assert result.findings == {} and result.video == b"MP4-5"


def test_report_mode_does_not_wait_long_for_a_slow_check() -> None:
    release = threading.Event()

    class _Slow(_Check):
        def check(self, clip, keyframe_png):
            release.wait(5)
            return ("NEW_CHARACTER",)

    try:
        result = _run(_Slow(), "report", report_wait_seconds=0.05)
    finally:
        release.set()

    assert result.findings == {}


def test_enforce_mode_renders_a_bad_scene_again_with_a_new_seed() -> None:
    render = _SeedRender()
    result = _run(_Check({2: 1}), "enforce", render)

    seeds = [seed for index, seed in render.seeds if index == 2]
    assert len(seeds) == 2 and seeds[0] != seeds[1]
    assert result.findings == {} and result.video == b"MP4-5"


def test_enforce_mode_gives_up_after_two_new_renders() -> None:
    render = _SeedRender()
    with pytest.raises(VideoPipelineError) as error:
        _run(_Check({3: 9}), "enforce", render)

    assert error.value.code == "VIDEO_SCENE_VISUAL_CHECK_FAILED"
    assert [index for index, _seed in render.seeds].count(3) == 3


# ------------------------------------------------------------------ adapter
class _Call:
    def __init__(self, payload: dict[str, Any], problems: Any, error: Exception | None) -> None:
        self.payload, self.problems, self.error = payload, problems, error

    def get(self, timeout: float) -> dict[str, Any]:
        if self.error:
            raise self.error
        return {
            "schema_version": "sketch2life.modal.worker-output.v1",
            "job_id": self.payload["job_id"],
            "attempt_id": self.payload["attempt_id"],
            "check": {"problems": self.problems},
        }


class _Function:
    def __init__(self, problems: Any = (), error: Exception | None = None) -> None:
        self.problems, self.error, self.inputs = list(problems), error, []

    def spawn(self, payload):
        self.inputs.append(payload)
        return _Call(payload, self.problems, self.error)


def _adapter(function: _Function, volume: _Volume, edges: Any = lambda clip: False) -> Any:
    return module.ModalSceneCheck(
        volume=volume, function=function, sheet=lambda clip, key, frames: b"\x89PNG-sheet", edges=edges,
        sleep=lambda _s: None,
    )


def test_the_adapter_sends_one_picture_sheet_and_returns_known_problems() -> None:
    volume, function = _Volume(), _Function(["NEW_CHARACTER", "SOMETHING_ELSE"])

    problems = _adapter(function, volume).check(SceneClip(1, b"clip", 145), b"key")

    assert problems == ("NEW_CHARACTER",)
    payload = function.inputs[0]
    assert payload["workload"] == "video.scene.validate"
    request = volume.files[f"/{payload['attempt_prefix']}input/request.json"]
    assert hashlib.sha256(b"\x89PNG-sheet").hexdigest().encode() in request


def test_an_unusable_answer_is_a_safe_code() -> None:
    with pytest.raises(VideoPipelineError) as error:
        _adapter(_Function(error=RuntimeError("provider text")), _Volume()).check(SceneClip(1, b"clip", 145), b"key")

    assert error.value.code == "VIDEO_SCENE_CHECK_FAILED"


def _grid(**changed: int) -> bytes:
    """One frame of block differences; ``changed`` maps "bX_Y" block names to their level."""

    cells = bytearray(module.GRID_WIDTH * module.GRID_HEIGHT)
    for name, level in changed.items():
        x, y = (int(part) for part in name.removeprefix("b").split("_"))
        cells[y * module.GRID_WIDTH + x] = level
    return bytes(cells)


def test_something_coming_in_from_an_edge_is_seen() -> None:
    hand = [_grid()] * 100 + [_grid(b11_8=98)] * 12 + [_grid()] * 128

    assert module.edge_changed(b"".join(hand)) is True


@pytest.mark.parametrize(
    "frames",
    [
        [_grid(b7_4=200)] * 240,  # the subject moves in the middle of the picture
        [_grid(b0_4=23)] * 240,  # the painting at the edge shimmers a little (measured on a clean scene)
        [_grid(b2_8=45)] * 240,  # a slight camera sway (measured in live run 3)
        [_grid(b0_0=98)] * 5 + [_grid()] * 235,  # a flash shorter than a quarter second
    ],
)
def test_normal_movement_is_not_an_edge_change(frames: list[bytes]) -> None:
    assert module.edge_changed(b"".join(frames)) is False


def test_an_edge_change_is_reported_beside_the_model_findings() -> None:
    adapter = _adapter(_Function(["SUBJECT_CHANGED"]), _Volume(), edges=lambda clip: True)

    assert adapter.check(SceneClip(1, b"clip", 145), b"key") == ("EDGE_CHANGED", "SUBJECT_CHANGED")


def test_an_edge_change_is_kept_when_the_model_cannot_answer() -> None:
    adapter = _adapter(_Function(error=RuntimeError("provider text")), _Volume(), edges=lambda clip: True)

    assert adapter.check(SceneClip(1, b"clip", 145), b"key") == ("EDGE_CHANGED",)


def test_a_failing_edge_measure_leaves_the_model_check() -> None:
    def broken(_clip: bytes) -> bool:
        raise OSError("no ffmpeg")

    adapter = _adapter(_Function(["TEXT_OR_LOGO"]), _Volume(), edges=broken)

    assert adapter.check(SceneClip(1, b"clip", 145), b"key") == ("TEXT_OR_LOGO",)


def test_the_edge_measure_compares_every_frame_with_the_first_one(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []

    def run(command, **_options):
        commands.append(command)
        return type("Done", (), {"returncode": 0, "stdout": _grid(b0_0=200) * 8})()

    monkeypatch.setattr(module.subprocess, "run", run)

    assert module.clip_edge_changed(b"clip") is True
    graph = commands[0][commands[0].index("-filter_complex") + 1]
    assert "eq(n\\,0)" in graph and "difference" in graph and "scale=16:9:flags=area" in graph


class _FrameCheck(_Check):
    def __init__(self, bad: dict[int, int] | None = None, error: Exception | None = None) -> None:
        super().__init__()
        self.bad_frames, self.frame_error, self.frames = dict(bad or {}), error, []

    def check_keyframe(self, drawing_png: bytes, keyframe_png: bytes) -> tuple[str, ...]:
        self.frames.append(keyframe_png)
        if self.frame_error:
            raise self.frame_error
        index = int(keyframe_png.split(b"-")[1])
        if self.bad_frames.get(index, 0):
            self.bad_frames[index] -= 1
            return ("NEW_CHARACTER",)
        return ()


class _SeededPrep(_Prep):
    def __init__(self, background: str = "AI") -> None:
        super().__init__()
        self.attempts: list[tuple[int, int]] = []
        self.background = background

    def prepare(self, job):
        self.attempts.append((job.scene.index, job.plate_attempt))
        return PreparedScene(f"key-{job.scene.index}-{job.plate_attempt}".encode(), self.background)


class _KeyRender(_Render):
    def __init__(self) -> None:
        super().__init__()
        self.keys: list[bytes] = []

    def render(self, job):
        self.keys.append(job.keyframe_png)
        return super().render(job)


def _run_frames(check: Any, prep: Any, mode: str = "report", **options: Any) -> list[bytes]:
    render = _KeyRender()
    VideoPipeline(
        timeline_generator=_Generator(_draft()), preparation=prep, renderer=render, narration=_Narration(),
        assembler=_Assembler(), validator=_Validator(), scene_check=check, check_mode=mode, **options,
    ).run(_source())
    return render.keys


def test_a_bad_background_is_repainted_once_before_the_scene_is_rendered() -> None:
    check, prep = _FrameCheck({2: 9}), _SeededPrep()

    keys = _run_frames(check, prep)

    assert prep.attempts == [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (2, 1)]
    assert keys == [b"key-1-0", b"key-2-1", b"key-3-0", b"key-4-0", b"key-5-0"]
    assert len(check.frames) == 5


@pytest.mark.parametrize(
    "check, prep, mode",
    [
        (_FrameCheck({1: 1}), _SeededPrep(), "off"),
        (_FrameCheck({1: 1}), _SeededPrep("PAPER"), "report"),  # nothing was painted, so nothing to repaint
        (_FrameCheck(error=VideoPipelineError("VIDEO_SCENE_CHECK_FAILED")), _SeededPrep(), "report"),
    ],
)
def test_no_background_is_repainted_without_a_finding(check: Any, prep: Any, mode: str) -> None:
    keys = _run_frames(check, prep, mode)

    assert [attempt for _index, attempt in prep.attempts] == [0] * 5 and len(keys) == 5


def test_a_slow_frame_check_does_not_hold_the_video_back() -> None:
    release = threading.Event()

    class _Slow(_FrameCheck):
        def check_keyframe(self, drawing_png, keyframe_png):
            release.wait(5)
            return ("NEW_CHARACTER",)

    prep = _SeededPrep()
    try:
        _run_frames(_Slow(), prep, frame_wait_seconds=0.05, report_wait_seconds=0.05)
    finally:
        release.set()

    assert len(prep.attempts) == 5


def test_the_adapter_asks_about_a_first_frame_beside_the_drawing(monkeypatch: pytest.MonkeyPatch) -> None:
    volume, function = _Volume(), _Function(["NEW_CHARACTER"])
    pairs: list[tuple[bytes, bytes]] = []
    monkeypatch.setattr(module, "pair_sheet", lambda drawing, key: pairs.append((drawing, key)) or b"\x89PNG-pair")

    problems = _adapter(function, volume).check_keyframe(b"drawing", b"key")

    assert problems == ("NEW_CHARACTER",) and pairs == [(b"drawing", b"key")]
    request = volume.files[f"/{function.inputs[0]['attempt_prefix']}input/request.json"]
    assert b'"kind":"keyframe"' in request


def test_the_sheet_holds_the_first_frame_and_five_moments_of_the_clip(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []

    def run(command, **_options):
        commands.append(command)
        from pathlib import Path

        Path(command[-1]).write_bytes(b"sheet")
        return type("Done", (), {"returncode": 0})()

    monkeypatch.setattr(module.subprocess, "run", run)

    assert module.picture_sheet(b"clip", b"key", 145) == b"sheet"
    graph = commands[0][commands[0].index("-filter_complex") + 1]
    assert all(f"eq(n\\,{index})" in graph for index in (28, 57, 86, 115, 144)) and "tile=3x2" in graph


def test_first_frames_are_looked_at_while_later_frames_are_still_prepared() -> None:
    first_looked = threading.Event()

    class _Watching(_FrameCheck):
        def check_keyframe(self, drawing_png, keyframe_png):
            first_looked.set()
            return super().check_keyframe(drawing_png, keyframe_png)

    class _Waiting(_SeededPrep):
        looked_before_the_last: bool | None = None

        def prepare(self, job):
            if job.scene.index == 5 and job.plate_attempt == 0:
                self.looked_before_the_last = first_looked.wait(3)
            return super().prepare(job)

    prep = _Waiting()
    _run_frames(_Watching(), prep)

    assert prep.looked_before_the_last is True
