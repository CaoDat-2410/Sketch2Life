"""SEED-2 umbrella: every Phase A-C stage in order, one guarded engine, one counts table each.

Run from ``backend/`` as ``python -m tools.seed.seed2_abc``, after S1 and S7a. The stages are
S8 (lesson occurrences), S9 (class lifecycle and enrollment move), S7b (Parent StoryRun states),
S10 (notification inbox), S11 (Teacher-cancelled organization run and private lesson shares) and
S12 (Phase A StoryRun activity selections, review epochs, safety block and replayable video).
Each stage is idempotent and prints a counts-only table; the exit code is 0 only when every
stage's totals match its expected counts. The API test kit runs this one module name.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from tools.seed import (
    s7b_story_states,
    s8_lessons,
    s9_classes,
    s10_inbox,
    s11_org_run_shares,
    s12_story_v4a,
)
from tools.seed.guard import SeedGuardError
from tools.seed.stage_common import (
    StageError,
    StageResult,
    format_result,
    open_guarded_engine,
)

StageRunner = Callable[[Engine], StageResult]

STAGES: tuple[tuple[str, StageRunner], ...] = (
    ("s8_lessons", s8_lessons.run_s8),
    ("s9_classes", s9_classes.run_s9),
    ("s7b_story_states", s7b_story_states.run_s7b),
    ("s10_inbox", s10_inbox.run_s10),
    ("s11_org_run_shares", s11_org_run_shares.run_s11),
    ("s12_story_v4a", s12_story_v4a.run_s12),
)


def run_all(
    engine: Engine, stages: tuple[tuple[str, StageRunner], ...] = STAGES
) -> list[StageResult]:
    """Run the stages in order and stop at the first failure (a later stage may depend on it)."""

    return [run(engine) for _name, run in stages]


def main() -> int:
    try:
        engine = open_guarded_engine()
    except SeedGuardError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    all_ok = True
    try:
        for name, run in STAGES:
            try:
                result = run(engine)
            except StageError as exc:
                print(f"{name}: {exc.code}", file=sys.stderr)
                return 3
            except SQLAlchemyError:
                print(f"{name}: SEED2_DATABASE_ERROR", file=sys.stderr)
                return 3
            # Print each table as its stage ends, so a later failure keeps the earlier counts.
            print(format_result(result), flush=True)
            all_ok = all_ok and result.ok
    finally:
        engine.dispose()
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
