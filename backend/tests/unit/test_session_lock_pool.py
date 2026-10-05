from __future__ import annotations

from threading import Event, Thread

from sketch2life.application.services.session_lock_pool import SessionLockPool


def test_session_lock_pool_serializes_same_session_but_not_other_sessions() -> None:
    pool = SessionLockPool()
    same_session_first = pool.for_session("session-a")
    same_session_second = pool.for_session("session-a")
    other_session = pool.for_session("session-b")

    assert same_session_first is same_session_second
    assert same_session_first is not other_session

    other_session_acquired = Event()

    def acquire_other_session() -> None:
        with pool.for_session("session-b"):
            other_session_acquired.set()

    with same_session_first:
        thread = Thread(target=acquire_other_session)
        thread.start()
        try:
            assert other_session_acquired.wait(timeout=1)
        finally:
            thread.join(timeout=1)
    assert not thread.is_alive()
