from __future__ import annotations

import hashlib
import inspect
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from PIL import Image
from sketch2life.contracts.schemas.be1_runtime import (
    CanvasSourceExportV1,
    CanvasSourceOperationV1,
)


def _source(
    point_counts: tuple[int, ...] = (2,), *, tuple_points: bool = False
) -> CanvasSourceExportV1:
    operations = []
    for revision, count in enumerate(point_counts, start=2):
        points = [{"x": 0.25, "y": 0.5}] * count
        payload = {
            "canvas_operation_profile_id": "canvas-operation-profile-v1",
            "kind": "stroke",
            "points": tuple(points) if tuple_points else points,
            "color": "#FFD21F",
            "size": 5,
        }
        operations.append(
            CanvasSourceOperationV1(
                operation_id=f"synthetic-stroke-{revision}",
                participant_id="synthetic-child",
                document_epoch=1,
                resulting_revision=revision,
                operation_payload=payload,
                payload_sha256=hashlib.sha256(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            )
        )
    return CanvasSourceExportV1.from_operations(
        organization_id="synthetic-org",
        session_id="synthetic-session",
        canvas_id="synthetic-canvas",
        document_epoch=1,
        document_revision=len(operations) + 1,
        operations=operations,
    )


def test_capacity_constants_fit_reconnect_page() -> None:
    from sketch2life.infrastructure.canvas_render import limits
    from sketch2life.interfaces.http.routers.be1_canvas import sync_canvas_operations

    limit = inspect.signature(sync_canvas_operations).parameters["limit"].default
    reconnect_limit = next(item.le for item in limit.metadata if hasattr(item, "le"))
    assert limits.MAX_STROKES == 500
    assert reconnect_limit >= limits.MAX_STROKES
    assert limits.MAX_POINTS == 60_000
    assert limits.RENDER_DEADLINE_SECONDS == 6


def test_capacity_accepts_exact_stroke_and_point_boundaries() -> None:
    from sketch2life.infrastructure.canvas_render.limits import validate_source_capacity

    validate_source_capacity(_source((120,) * 500))


@pytest.mark.parametrize("point_counts", [(2,) * 501, (500,) * 120 + (1,)])
def test_capacity_rejects_oversized_history_before_drawing(
    point_counts: tuple[int, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    from sketch2life.infrastructure.canvas_render import renderer
    from sketch2life.infrastructure.canvas_render.limits import CanvasSourceTooLarge

    def no_image(*args: Any, **kwargs: Any) -> None:
        pytest.fail("capacity must be checked before allocating an image")

    monkeypatch.setattr(Image, "new", no_image)
    with pytest.raises(CanvasSourceTooLarge):
        renderer.render_canvas_source(_source(point_counts))


def test_serialized_array_points_cannot_bypass_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    from sketch2life.infrastructure.canvas_render import renderer
    from sketch2life.infrastructure.canvas_render.limits import CanvasSourceTooLarge

    def no_image(*args: Any, **kwargs: Any) -> None:
        pytest.fail("serialized array capacity must be checked before image allocation")

    monkeypatch.setattr(Image, "new", no_image)
    with pytest.raises(CanvasSourceTooLarge):
        renderer.render_canvas_source(_source((500,) * 120 + (1,), tuple_points=True))


def test_expired_deadline_refuses_before_render(monkeypatch: pytest.MonkeyPatch) -> None:
    from sketch2life.infrastructure.canvas_render import limits, renderer

    monkeypatch.setattr(limits, "monotonic", lambda: 10.0)
    with pytest.raises(limits.CanvasRenderDeadlineExceeded):
        renderer.render_canvas_source(_source(), deadline=10.0)


def test_semaphore_wait_consumes_remaining_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    from sketch2life.infrastructure.canvas_render import limits, renderer

    class BusySemaphore:
        def acquire(self, *, timeout: float) -> bool:
            assert timeout == 2.0
            return False

        def release(self) -> None:
            pytest.fail("a semaphore that was not acquired cannot be released")

    monkeypatch.setattr(limits, "monotonic", lambda: 10.0)
    monkeypatch.setattr(renderer, "_RENDER_SEMAPHORE", BusySemaphore())
    with pytest.raises(limits.CanvasRenderBusy):
        renderer.render_canvas_source(_source(), deadline=12.0)


def test_deadline_checked_between_strokes_before_png(monkeypatch: pytest.MonkeyPatch) -> None:
    from sketch2life.infrastructure.canvas_render import limits, renderer

    now = [0.0]
    calls = []

    def slow_stroke(*args: Any, **kwargs: Any) -> None:
        calls.append("stroke")
        now[0] = 6.0

    monkeypatch.setattr(limits, "monotonic", lambda: now[0])
    monkeypatch.setattr(renderer, "_draw_stroke", slow_stroke)
    with pytest.raises(limits.CanvasRenderDeadlineExceeded):
        renderer.render_canvas_source(_source((2, 2)), deadline=6.0)
    assert calls == ["stroke"]


def test_deadline_checked_after_png_and_semaphore_released(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.infrastructure.canvas_render import limits, renderer

    now = [0.0]
    save = Image.Image.save

    def slow_save(self: Any, *args: Any, **kwargs: Any) -> None:
        save(self, *args, **kwargs)
        now[0] = 6.0

    monkeypatch.setattr(limits, "monotonic", lambda: now[0])
    monkeypatch.setattr(Image.Image, "save", slow_save)
    with pytest.raises(limits.CanvasRenderDeadlineExceeded):
        renderer.render_canvas_source(_source(), deadline=6.0)
    monkeypatch.setattr(Image.Image, "save", save)
    now[0] = 0.0
    assert renderer.render_canvas_source(_source(), deadline=6.0).png_bytes.startswith(b"\x89PNG")


def test_render_error_releases_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    from sketch2life.infrastructure.canvas_render import renderer

    draw_stroke = renderer._draw_stroke

    def broken_stroke(*args: Any, **kwargs: Any) -> None:
        raise ValueError("synthetic draw failure")

    monkeypatch.setattr(renderer, "_draw_stroke", broken_stroke)
    with pytest.raises(ValueError, match="synthetic draw failure"):
        renderer.render_canvas_source(_source())
    monkeypatch.setattr(renderer, "_draw_stroke", draw_stroke)
    assert renderer.render_canvas_source(_source()).png_bytes.startswith(b"\x89PNG")


def test_two_renders_wait_for_one_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    from sketch2life.infrastructure.canvas_render import renderer

    entered = threading.Event()
    second_waiting = threading.Event()
    release_first = threading.Event()
    lock = threading.Lock()
    actual = threading.BoundedSemaphore(1)
    acquire_calls = 0
    drawing_order: list[str] = []

    class ObservedSemaphore:
        def acquire(self, *, timeout: float) -> bool:
            nonlocal acquire_calls
            with lock:
                acquire_calls += 1
                if acquire_calls == 2:
                    second_waiting.set()
            return actual.acquire(timeout=timeout)

        def release(self) -> None:
            actual.release()

    def tracked_stroke(*args: Any, **kwargs: Any) -> None:
        with lock:
            drawing_order.append(threading.current_thread().name)
            first = len(drawing_order) == 1
        if first:
            entered.set()
            assert release_first.wait(timeout=2.0)

    monkeypatch.setattr(renderer, "_RENDER_SEMAPHORE", ObservedSemaphore())
    monkeypatch.setattr(renderer, "_draw_stroke", tracked_stroke)
    source = _source()
    with ThreadPoolExecutor(max_workers=2) as executor:
        first_render = executor.submit(renderer.render_canvas_source, source)
        assert entered.wait(timeout=2.0)
        second_render = executor.submit(renderer.render_canvas_source, source)
        try:
            assert second_waiting.wait(timeout=2.0)
            assert len(drawing_order) == 1
        finally:
            release_first.set()
        assert first_render.result(timeout=3.0).png_bytes.startswith(b"\x89PNG")
        assert second_render.result(timeout=3.0).png_bytes.startswith(b"\x89PNG")
    assert len(drawing_order) == 2
