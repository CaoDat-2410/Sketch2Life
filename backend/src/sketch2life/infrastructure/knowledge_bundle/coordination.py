"""One-process guard publication boundary, shared exclusively by the own07 fixtures."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from threading import RLock


class KnowledgeCommitCoordinator:
    """Order external facts after the outer unit, including its rollback path.

    An external publication requested by this thread is queued, not acknowledged as
    applied. Other threads wait on the same lock. This is not a distributed fence.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._depth = 0
        self._pending: deque[Callable[[], None]] = deque()

    @contextmanager
    def read(self) -> Iterator[None]:
        with self._lock:
            yield

    @contextmanager
    def unit(self) -> Iterator[None]:
        with self._lock:
            self._depth += 1
            primary: BaseException | None = None
            try:
                yield
            except BaseException as exc:
                primary = exc
                raise
            finally:
                self._depth -= 1
                if self._depth == 0:
                    failure: BaseException | None = None
                    while self._pending:
                        try:
                            self._pending.popleft()()
                        except BaseException as exc:
                            if failure is None:
                                failure = exc
                    if failure is not None:
                        if primary is None:
                            raise failure
                        primary.add_note(
                            f"Deferred publication also failed: {type(failure).__name__}"
                        )

    def publish(self, publication: Callable[[], None]) -> bool:
        """Return True only when applied; queued requests return False."""
        with self._lock:
            if self._depth:
                self._pending.append(publication)
                return False
            publication()
            return True
