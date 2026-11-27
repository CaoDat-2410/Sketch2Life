"""FEAT-098: start the video work while the adult reviews the learning script.

The scene pictures are asked for (the worker keeps them for a short while) and the renderer is then loaded. A rewritten
script is a new revision; only the pictures that differ are painted again. Everything here is best effort: a failure
costs time later and is never shown to the adult.
"""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from typing import Any

from sketch2life.application.ports.story_video import VideoRenderRequest
from sketch2life.application.video_pipeline.orchestrator import prepare_ahead
from sketch2life.application.video_pipeline.ports import VideoPipelineError

_LOG = logging.getLogger(__name__)
_REMEMBERED = 256


class VideoPrepareAhead:
    def __init__(self, reader: Any, preparation: Any, renderer: Any) -> None:
        self._reader = reader
        self._preparation = preparation
        self._renderer = renderer
        self._lock = threading.Lock()
        self._asked: OrderedDict[str, None] = OrderedDict()

    def request(self, run_id: str, story_revision_id: str) -> bool:
        """Ask once per story revision; ``True`` when the work was sent."""

        with self._lock:
            if story_revision_id in self._asked:
                return False
            self._asked[story_revision_id] = None
            while len(self._asked) > _REMEMBERED:
                self._asked.popitem(last=False)
        sent = False
        try:
            sent = self._send(run_id, story_revision_id) > 0
        except VideoPipelineError as error:
            _LOG.warning("video_prepare_ahead_failed code=%s", error.code)
        except Exception as error:  # noqa: BLE001 - only a speed-up
            _LOG.warning("video_prepare_ahead_failed error_type=%s", type(error).__name__)
        if not sent:
            with self._lock:
                self._asked.pop(story_revision_id, None)
        return sent

    def _send(self, run_id: str, story_revision_id: str) -> int:
        source = self._reader.read(
            VideoRenderRequest(
                generation_id="",
                run_id=run_id,
                story_revision_id=story_revision_id,
                script_hash="",  # not confirmed yet: whatever this revision holds
                scene_count=0,
                job_ref="",
            )
        )
        if source is None:
            return 0
        return prepare_ahead(source, self._preparation, self._renderer)


__all__ = ["VideoPrepareAhead"]
