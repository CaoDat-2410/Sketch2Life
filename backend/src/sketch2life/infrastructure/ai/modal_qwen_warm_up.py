"""Start the shared Qwen worker before the first AI step needs it (FEAT-093 Amendment D).

A cold engine takes minutes to load. The Parent spends that long choosing a topic and a drawing, so the API asks Modal
to start the container then. The call carries no data and its failure only means the first step is slower.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any, Final

from structlog import get_logger

from sketch2life.infrastructure.ai.modal_function_client import APP_NAME, ENVIRONMENT_NAME, FUNCTION_NAME

WINDOW_SECONDS: Final = 300.0
_LOGGER = get_logger(__name__)


class QwenWarmUp:
    def __init__(
        self,
        *,
        function: Any | None = None,
        clock: Callable[[], float] = time.monotonic,
        window_seconds: float = WINDOW_SECONDS,
    ) -> None:
        self._function = function
        self._clock = clock
        self._window = window_seconds
        self._requested_at: float | None = None
        self._lock = threading.Lock()

    def request(self) -> bool:
        """True when a warm-up was dispatched; at most one per window."""

        with self._lock:
            now = self._clock()
            if self._requested_at is not None and now - self._requested_at < self._window:
                return False
            try:
                self._resolve_function().spawn({"warmup": True})
            except Exception as error:  # noqa: BLE001 - optional speed-up, never a user-facing failure
                _LOGGER.warning("qwen_warm_up_not_dispatched", error_type=type(error).__name__)
                return False
            self._requested_at = now
            return True

    def _resolve_function(self) -> Any:
        if self._function is None:
            import modal

            self._function = modal.Function.from_name(APP_NAME, FUNCTION_NAME, environment_name=ENVIRONMENT_NAME)
        return self._function


__all__ = ["QwenWarmUp"]
