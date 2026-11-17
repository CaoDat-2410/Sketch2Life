from __future__ import annotations

from sketch2life.interfaces.http.app import create_app


class Pipeline:
    def run(self, job, update_stage):
        raise AssertionError("pipeline is only being injected in this wiring test")


def test_app_accepts_injected_whiteboard_pipeline() -> None:
    app = create_app(whiteboard_video_pipeline=Pipeline())

    assert app.state.whiteboard_video_job_service._pipeline.__class__ is Pipeline
