"""Phase C notification-inbox seed (FEAT-066 SEED-2, design §11.7 S10)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Connection, Engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.notifications import (
    EnqueueResult,
    NotificationCommandV1,
    NotificationProducerPort,
)
from sketch2life.application.services.notifications import READ_ONE_SCOPE
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES as OCCURRENCE_TABLE
from sketch2life.infrastructure.notifications.inbox_repository import (
    NotificationError,
    NotificationInboxService,
    SqlNotificationProducer,
)
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.story_run_lite.tables import story_runs
from tools.seed import data
from tools.seed.s8_lessons_data import OCCURRENCES
from tools.seed.s10_inbox_data import EXPECTED, ITEMS, REF, InboxItemSpec
from tools.seed.stage_common import (
    StageError,
    StageResult,
    run_stage_main,
    seed_principal,
    stage_key,
)

Clock = Callable[[], datetime]
ProducerFactory = Callable[[Session, Clock], NotificationProducerPort]
ParameterResolver = Callable[[Any, InboxItemSpec], dict[str, str | int | bool]]
InboxFactory = Callable[[Session, Clock], NotificationInboxService]


class FixedClock:
    """A deterministic UTC clock supplied to one notification or read command."""

    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


def _dedupe_key(spec: InboxItemSpec) -> str:
    return stage_key("s10", f"item-{spec.key}")


def _read_key(spec: InboxItemSpec) -> str:
    return stage_key("s10", f"read-{spec.key}")


def _command(
    spec: InboxItemSpec, parameters: dict[str, str | int | bool] | None = None
) -> NotificationCommandV1:
    return NotificationCommandV1(
        recipient_account_id=data.seed_uuid_text(f"adult:{spec.recipient_subject}"),
        recipient_role=spec.recipient_role,
        organization_ref=spec.organization_ref,
        notification_type=spec.notification_type,
        template_version=1,
        trigger_id=f"{spec.trigger_id}:{spec.key}",
        dedupe_key=_dedupe_key(spec),
        safe_parameters=dict(spec.safe_parameters if parameters is None else parameters),
        expires_at=spec.expires_at,
    )


def _lookup_run(session: Session, parent_key: str, state: str) -> str:
    scope_ref = data.principal_scope_ref(data.SEED_ISSUER, data.PARENT_SUBJECTS[parent_key])
    found = session.scalars(
        select(story_runs.c.run_id)
        .where(
            story_runs.c.actor_scope_kind == "PARENT_ACCOUNT",
            story_runs.c.actor_scope_ref == scope_ref,
            story_runs.c.run_state == state,
        )
        .order_by(story_runs.c.created_at, story_runs.c.run_id)
    ).first()
    if found is None:
        raise StageError("S10_REFERENCE_MISSING")
    return str(found)


def _lookup_occurrence(session: Session, occurrence_key: str) -> str:
    spec = next((row for row in OCCURRENCES if row.key == occurrence_key), None)
    if spec is None:
        raise StageError("S10_REFERENCE_MISSING")
    found = session.scalars(
        select(OCCURRENCE_TABLE.c.occurrence_id).where(
            OCCURRENCE_TABLE.c.class_ref == data.class_id("a", spec.class_number),
            OCCURRENCE_TABLE.c.title == spec.title,
        )
    ).first()
    if found is None:
        raise StageError("S10_REFERENCE_MISSING")
    return str(found)


def resolve_parameters(session_factory: Any, spec: InboxItemSpec) -> dict[str, str | int | bool]:
    """Replace ``ref:`` values by the ids of the runs and occurrences that earlier stages made."""

    resolved: dict[str, str | int | bool] = {}
    for key, value in spec.safe_parameters.items():
        if isinstance(value, str) and value.startswith(REF):
            kind, *rest = value[len(REF) :].split(":")
            with session_factory() as session:
                if kind == "run" and len(rest) == 2:
                    resolved[key] = _lookup_run(session, rest[0], rest[1])
                elif kind == "occ" and len(rest) == 1:
                    resolved[key] = _lookup_occurrence(session, rest[0])
                else:
                    raise StageError("S10_REFERENCE_MISSING")
        else:
            resolved[key] = value
    return resolved


def seed_inbox(
    session_factory: Any,
    *,
    producer_factory: ProducerFactory = SqlNotificationProducer,
    inbox_factory: InboxFactory = NotificationInboxService,
    resolver: ParameterResolver = resolve_parameters,
) -> None:
    """Enqueue every fixed item, then mark the selected subset read as its recipient."""

    for spec in ITEMS:
        command = _command(spec, resolver(session_factory, spec))
        with session_factory.begin() as session:
            result: EnqueueResult = producer_factory(session, FixedClock(spec.created_at)).enqueue(
                command
            )
        if not spec.read:
            continue
        # A read is always later than its item. The command's receipt freezes the first read_at
        # and turns this same key on a rerun into a replay without a second receipt.
        read_clock = FixedClock(spec.created_at + timedelta(hours=1))
        with session_factory() as session:
            inbox_factory(session, read_clock).mark_read(
                principal=seed_principal(spec.recipient_subject),
                inbox_item_id=result.inbox_item_id,
                idempotency_key=_read_key(spec),
            )


def _read_receipt_keys() -> tuple[str, ...]:
    return tuple(_read_key(spec) for spec in ITEMS if spec.read)


def _dedupe_keys() -> tuple[str, ...]:
    return tuple(_dedupe_key(spec) for spec in ITEMS)


def count_stage_rows(connection: Connection) -> dict[str, int]:
    """Count only inbox entries and mark-read receipts owned by this stage."""

    receipts = Be1CommandReceiptModel.__table__
    item_count = connection.execute(
        select(func.count())
        .select_from(INBOX_ITEMS)
        .where(INBOX_ITEMS.c.trigger_dedupe_key.in_(_dedupe_keys()))
    ).scalar_one()
    receipt_count = connection.execute(
        select(func.count())
        .select_from(receipts)
        .where(
            receipts.c.operation_scope == READ_ONE_SCOPE,
            receipts.c.idempotency_key.in_(_read_receipt_keys()),
            receipts.c.principal_ref.in_({spec.recipient_subject for spec in ITEMS if spec.read}),
        )
    ).scalar_one()
    return {
        "notifications_inbox_items": int(item_count),
        "be1_command_receipts_s10": int(receipt_count),
    }


def run_s10(engine: Engine) -> StageResult:
    """Seed notification items and return the before/after counts for S10."""

    with engine.connect() as connection:
        before = count_stage_rows(connection)
    try:
        seed_inbox(create_core_session_factory(engine))
    except SQLAlchemyError:
        raise StageError("S10_DATABASE_ERROR") from None
    except NotificationError:
        raise StageError("S10_MARK_READ_FAILED") from None
    except Exception:
        # Service validation errors are converted to one fixed code so display data or parameters
        # can never leak through a traceback in the seed runner.
        raise StageError("S10_NOTIFICATION_COMMAND_FAILED") from None
    with engine.connect() as connection:
        after = count_stage_rows(connection)
    return StageResult(name="s10_inbox", before=before, after=after, expected=EXPECTED)


def main() -> int:
    return run_stage_main(run_s10, stage="s10")


if __name__ == "__main__":
    raise SystemExit(main())
