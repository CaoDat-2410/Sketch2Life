"""Shared plumbing of the SEED-2 stages (FEAT-066 SEED-2; every stage after S7a).

One stage module has this shape (``tools/seed/s7a_runs.py`` is the model):

* ``run_stage(engine) -> dict[str, int]`` writes the stage and returns the NEW rows per table;
* ``count_stage_rows(connection) -> dict[str, int]`` counts only the rows the stage owns;
* ``EXPECTED`` (in the stage's own data module) is the expected total per table;
* ``main()`` runs the guards, the stage and prints the counts-only table.

The guard order is the S7a order: the process environment first, then the S1 database guard
(loopback host, explicit port, name contains ``seed``), then the resolved settings, plus one
rule that only the SEED-2 stages add: the database name must start with ``frc08_`` (the disposable
databases of the frc08 container). Nothing here prints a URL, an ID or a row content.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.ports.identity import VerifiedPrincipal
from tools.seed import data
from tools.seed.guard import (
    SeedGuardError,
    check_no_provider,
    check_s7a_environment,
    check_target,
    guarded_engine,
)

REQUIRED_DATABASE_PREFIX = "frc08_"


class StageError(RuntimeError):
    """A fixed-message stage failure: a code only, never a URL, an ID or a content string."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def stage_key(stage: str, case: str) -> str:
    """The stable idempotency key of one seed command (design section 4.5)."""

    return f"seed:{stage}:{case}"


def seed_principal(subject: str) -> VerifiedPrincipal:
    """The seeded adult as the verified principal; the issuer is read at call time.

    ``data.SEED_ISSUER`` is replaced by the API test kit (``seed_runner.py --firebase-project``),
    so it must never be imported by value.
    """

    return VerifiedPrincipal(subject=subject, issuer=data.SEED_ISSUER, roles=frozenset())


def check_database_prefix(environ: dict[str, str] | None = None) -> None:
    """Refuse a database whose name does not start with ``frc08_`` (SEED-2 rule)."""

    target = check_target(environ)
    if not target.database.lower().startswith(REQUIRED_DATABASE_PREFIX):
        raise SeedGuardError("seed guard refused: the database name must start with 'frc08_'")


def open_guarded_engine() -> Engine:
    """Run every guard in the S7a order and return the checked engine."""

    check_s7a_environment()
    check_database_prefix()
    engine, _target = guarded_engine()
    try:
        check_no_provider()
    except SeedGuardError:
        engine.dispose()
        raise
    return engine


@dataclass(frozen=True, slots=True)
class StageResult:
    name: str
    before: dict[str, int]
    after: dict[str, int]
    expected: dict[str, int]
    notes: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.after == self.expected


def format_result(result: StageResult) -> str:
    """The counts-only table. Table names use ``[A-Za-z0-9_]`` only, so the API test kit's
    count-line filter (``^[A-Za-z0-9_]+\\s+\\d+\\s+\\d+\\s+\\d+\\s+(yes|NO)$``) keeps every row."""

    width = max(len(name) for name in result.after)
    lines = [f"{'table'.ljust(width)}  new  total  expected  ok"]
    for name, total in result.after.items():
        expected = result.expected.get(name, 0)
        ok = "yes" if total == expected else "NO"
        new = total - result.before.get(name, 0)
        lines.append(f"{name.ljust(width)}  {new:>3}  {total:>5}  {expected:>8}  {ok}")
    lines.extend(result.notes)
    return "\n".join(lines)


def run_stage_main(
    run: Callable[[Engine], StageResult], *, stage: str, stderr_code: str | None = None
) -> int:
    """Open the guarded engine, run one stage, print the table; exit 0 only if counts match."""

    try:
        engine = open_guarded_engine()
    except SeedGuardError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        try:
            result = run(engine)
        except StageError as exc:
            print(exc.code, file=sys.stderr)
            return 3
        except SQLAlchemyError:
            print(stderr_code or f"{stage.upper()}_DATABASE_ERROR", file=sys.stderr)
            return 3
    finally:
        engine.dispose()
    print(format_result(result))
    return 0 if result.ok else 1
