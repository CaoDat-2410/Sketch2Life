"""Unit tests of the SEED-2 umbrella: stage order, counts-only output and failure handling."""

from __future__ import annotations

import pytest

from tools.seed import seed2_abc
from tools.seed.stage_common import StageError, StageResult


def _result(name: str, *, ok: bool = True) -> StageResult:
    return StageResult(name=name, before={"t": 0}, after={"t": 1}, expected={"t": 1 if ok else 2})


def test_the_stages_run_in_the_documented_order() -> None:
    assert [name for name, _run in seed2_abc.STAGES] == [
        "s8_lessons",
        "s9_classes",
        "s7b_story_states",
        "s10_inbox",
        "s11_org_run_shares",
        "s12_story_v4a",
    ]


class _Engine:
    disposed = False

    def dispose(self) -> None:
        self.disposed = True


def _patch(
    monkeypatch: pytest.MonkeyPatch, runners: list[tuple[str, object]], engine: _Engine
) -> None:
    monkeypatch.setattr(seed2_abc, "open_guarded_engine", lambda: engine)
    monkeypatch.setattr(seed2_abc, "STAGES", tuple(runners))


def test_main_prints_each_stage_table_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = _Engine()
    _patch(
        monkeypatch,
        [("a", lambda _e: _result("a")), ("b", lambda _e: _result("b"))],
        engine,
    )
    assert seed2_abc.main() == 0
    assert capsys.readouterr().out.count("table") == 2
    assert engine.disposed


def test_a_count_mismatch_exits_one_and_a_stage_error_keeps_earlier_tables(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing(_engine: object) -> StageResult:
        raise StageError("S_TEST_FAILED")

    engine = _Engine()
    _patch(monkeypatch, [("a", lambda _e: _result("a", ok=False))], engine)
    assert seed2_abc.main() == 1
    capsys.readouterr()
    _patch(monkeypatch, [("a", lambda _e: _result("a")), ("b", failing)], engine)
    assert seed2_abc.main() == 3
    captured = capsys.readouterr()
    assert captured.out.count("table") == 1
    assert captured.err.strip() == "b: S_TEST_FAILED"
