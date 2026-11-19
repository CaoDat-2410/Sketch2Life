"""S7 item 2a writer: one command-made Parent run for P4 and for P5 (FEAT-066 SEED-7a).

Run from ``backend/`` as ``python -m tools.seed.s7a_runs``, after S1. The runs are made
by the product's own service methods (``create_run`` then ``confirm_context``), so they
are valid starting points for the later seed stages. Guard order: the process
environment first, then the S1 database guard, then the resolved settings. A second run
creates nothing. The output is a table of counts and the two run states: no ID, URL or
content.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import Connection, Engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRunError,
    ParentStoryRunRecord,
    ParentStoryRunView,
)
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tools.seed import data
from tools.seed.guard import (
    SeedGuardError,
    check_no_provider,
    check_s7a_environment,
    guarded_engine,
)

_RUN_STATE = "INPUT_PROCESSING"


class S7aError(RuntimeError):
    """A fixed-message failure. It carries a code and never a URL, an ID or content."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class RunService(Protocol):
    """The three service methods S7a uses (the real service and the unit-test fake)."""

    def get_active_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunView | None: ...

    def create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        parent_profile_id: UUID,
        idempotency_key: str,
        topic: str,
        adult_confirmed_idea: str,
    ) -> ParentStoryRunView: ...

    def confirm_context(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_context_revision: int,
        expected_context_snapshot_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunView: ...


def _expect_record(view: ParentStoryRunView | None) -> ParentStoryRunRecord:
    """A seed run must be a full record in INPUT_PROCESSING (a lifecycle record is not)."""

    if not isinstance(view, ParentStoryRunRecord) or view.run_state != _RUN_STATE:
        raise S7aError("S7A_UNEXPECTED_RUN_STATE")
    return view


def _is_seed_run(record: ParentStoryRunRecord, profile_id: UUID, topic: str, idea: str) -> bool:
    snapshot = record.context_snapshot
    return (
        str(record.parent_profile_id) == str(profile_id)
        and snapshot.get("topic") == topic
        and snapshot.get("adult_confirmed_idea") == idea
        and data.sha256_json(snapshot) == record.context_snapshot_sha256
    )


def ensure_parent_run(
    service: RunService,
    *,
    principal: VerifiedPrincipal,
    account_id: str,
    profile_id: UUID,
    parent_key: str,
    topic: str,
    idea: str,
) -> str:
    """Apply the decision table of package section 3.3 and return the action taken."""

    try:
        active = service.get_active_run(principal=principal, account_id=account_id)
        action = "kept"
        if active is None:
            created = service.create_run(
                principal=principal,
                account_id=account_id,
                parent_profile_id=profile_id,
                idempotency_key=data.s7a_create_key(parent_key),
                topic=topic,
                adult_confirmed_idea=idea,
            )
            record = _expect_record(created)
            action = "created"
        else:
            if isinstance(active, ParentStoryRunRecord) and not _is_seed_run(
                active, profile_id, topic, idea
            ):
                raise S7aError("S7A_FOREIGN_ACTIVE_RUN")
            record = _expect_record(active)
        if not record.context_confirmed:
            confirmed = service.confirm_context(
                principal=principal,
                run_id=record.run_id,
                expected_context_revision=record.context_revision,
                expected_context_snapshot_sha256=record.context_snapshot_sha256,
                idempotency_key=data.s7a_confirm_key(parent_key),
            )
            record = _expect_record(confirmed)
            action = "created" if action == "created" else "confirmed"
        if not record.context_confirmed:
            raise S7aError("S7A_UNEXPECTED_RUN_STATE")
    except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
        raise S7aError(f"S7A_COMMAND_FAILED_{exc.code}") from None
    return action


def _require_parent(session: Session, principal: VerifiedPrincipal) -> None:
    """The same three conditions as the route's ``_require_parent``."""

    identity = session.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise S7aError("S7A_PARENT_IDENTITY_MISSING")


def _build_service(session: Session) -> ParentStoryRunService:
    return ParentStoryRunService(
        SqlParentStoryRunRepository(session), SqlParentStoryProfileLookup(session)
    )


def run_s7a(
    engine: Engine,
    service_factory: Callable[[Session], RunService] = _build_service,
) -> dict[str, str]:
    """Run item 2a for every spec and return the action taken per Parent key."""

    factory = create_core_session_factory(engine)
    actions: dict[str, str] = {}
    for parent_key, profile_key, topic, idea in data.S7A_RUN_SPECS:
        principal = VerifiedPrincipal(
            subject=data.PARENT_SUBJECTS[parent_key],
            issuer=data.SEED_ISSUER,
            roles=frozenset(),
        )
        session = factory()
        try:
            _require_parent(session, principal)
            actions[parent_key] = ensure_parent_run(
                service_factory(session),
                principal=principal,
                account_id=data.parent_account_id(parent_key),
                profile_id=data.parent_profile_id(profile_key),
                parent_key=parent_key,
                topic=topic,
                idea=idea,
            )
        except SQLAlchemyError:
            raise S7aError("S7A_DATABASE_ERROR") from None
        finally:
            session.close()
    return actions


def _s7a_scope_refs() -> list[str]:
    return [
        data.principal_scope_ref(data.SEED_ISSUER, data.PARENT_SUBJECTS[parent_key])
        for parent_key, _profile, _topic, _idea in data.S7A_RUN_SPECS
    ]


def count_s7a_rows(connection: Connection) -> dict[str, int]:
    """Count the S7a-owned rows through the seeded Parent principals and the run FK."""

    runs = story_tables.story_runs
    run_ids = select(runs.c.run_id).where(
        runs.c.actor_scope_kind == "PARENT_ACCOUNT",
        runs.c.actor_scope_ref.in_(_s7a_scope_refs()),
    )
    receipts = story_tables.story_command_receipts
    return {
        "story.runs": int(
            connection.execute(
                select(func.count()).select_from(runs).where(runs.c.run_id.in_(run_ids))
            ).scalar_one()
        ),
        "story.run_inputs": int(
            connection.execute(
                select(func.count())
                .select_from(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_id.in_(run_ids))
            ).scalar_one()
        ),
        "story.command_receipts": int(
            connection.execute(
                select(func.count())
                .select_from(receipts)
                .where(receipts.c.resource_ref.in_(run_ids))
            ).scalar_one()
        ),
    }


def format_s7a(
    before: dict[str, int], after: dict[str, int], expected: dict[str, int], states: dict[str, str]
) -> str:
    width = max(len(name) for name in after)
    lines = [f"{'table'.ljust(width)}  new  total  expected  ok"]
    for name, total in after.items():
        ok = "yes" if total == expected.get(name) else "NO"
        lines.append(
            f"{name.ljust(width)}  {total - before.get(name, 0):>3}  {total:>5}"
            f"  {expected.get(name, 0):>8}  {ok}"
        )
    lines.append("runs: " + ", ".join(f"{key}={states[key]}" for key in sorted(states)))
    return "\n".join(lines)


def main() -> int:
    try:
        check_s7a_environment()
        engine, _target = guarded_engine()
    except SeedGuardError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        try:
            check_no_provider()
        except SeedGuardError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        try:
            with engine.connect() as connection:
                before = count_s7a_rows(connection)
            actions = run_s7a(engine)
            with engine.connect() as connection:
                after = count_s7a_rows(connection)
        except S7aError as exc:
            print(exc.code, file=sys.stderr)
            return 3
        except SQLAlchemyError:
            print("S7A_DATABASE_ERROR", file=sys.stderr)
            return 3
    finally:
        engine.dispose()
    states: dict[str, Any] = {key: f"{_RUN_STATE}/{action}" for key, action in actions.items()}
    print(format_s7a(before, after, data.EXPECTED_S7A_COUNTS, states))
    return 0 if after == data.EXPECTED_S7A_COUNTS else 1


if __name__ == "__main__":
    raise SystemExit(main())
