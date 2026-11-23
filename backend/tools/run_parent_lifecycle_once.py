"""Run the approved, exact Parent lifecycle event once against the task-local Docker stack.

This deliberately narrow operator tool exists for the approved Rev55 cleanup only. It refuses
any run other than the pinned synthetic run and any database/storage target other than the
current local Compose services. All lifecycle work is performed by ``Be1LifecycleConsumer``;
this tool never edits business rows directly.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.core_foundation import PARENT_SCOPE_KIND
from sketch2life.application.ports.story_run_lifecycle import (
    CANCEL_EVENT_TYPE,
    LIFECYCLE_EVENT_TYPES,
    lifecycle_request_id,
)
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlParentLifecycleNoticeStore
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
    Be1LifecycleConsumer,
    ConsumerConfig,
    SqlLifecycleAuditWriter,
    SqlLifecycleReceiptStore,
)
from sketch2life.infrastructure.persistence.be1_models import DataLifecycleRequestModel
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    SqlCoreRunUploadClose,
)
from sketch2life.infrastructure.persistence.core_models import CoreOutboxEventModel
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.persistence.outbox import PostgresOutbox
from sketch2life.infrastructure.persistence.story_lifecycle_store import SqlStoryLifecycleStore
from sketch2life.infrastructure.storage.s3_compatible import Boto3S3CompatibleObjectStorage
from sketch2life.infrastructure.story_run_lite import tables as story_tables

APPROVED_RUN_REF = "08657e31-ebd7-4a07-8f9b-5929b4dff23b"
EXPECTED_DATABASE = ("postgres", 5432, "sketch2life")
EXPECTED_OBJECT_STORE = ("http://minio:9000", "sketch2life-private")


class _Refused(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _preflight(
    sessions: sessionmaker[Session], run_ref: str
) -> tuple[str, str]:
    with sessions() as session:
        run = session.execute(
            select(
                story_tables.story_runs.c.run_state,
                story_tables.story_runs.c.actor_scope_kind,
                story_tables.story_runs.c.actor_scope_ref,
                story_tables.story_runs.c.active_owner_parent_account_id,
            ).where(story_tables.story_runs.c.run_id == run_ref)
        ).mappings().one_or_none()
        if run is None:
            raise _Refused("TARGET_RUN_NOT_FOUND")
        if (
            run["run_state"] != "DELETE_PENDING"
            or run["actor_scope_kind"] != PARENT_SCOPE_KIND
            or not run["actor_scope_ref"]
            or run["active_owner_parent_account_id"] is not None
        ):
            raise _Refused("TARGET_RUN_STATE_OR_SCOPE_MISMATCH")

        events = list(
            session.scalars(
                select(CoreOutboxEventModel).where(
                    CoreOutboxEventModel.aggregate_id == run_ref,
                    CoreOutboxEventModel.event_type.in_(LIFECYCLE_EVENT_TYPES),
                )
            )
        )
        if len(events) != 1:
            raise _Refused("TARGET_EVENT_COUNT_MISMATCH")
        event = events[0]
        if (
            event.event_type != CANCEL_EVENT_TYPE
            or event.status != "pending"
            or event.available_at > datetime.now(UTC)
            or event.owner_scope_kind != PARENT_SCOPE_KIND
            or event.owner_scope_ref != run["actor_scope_ref"]
            or event.payload.get("run_ref") != run_ref
            or event.payload.get("lifecycle_request_ref") != lifecycle_request_id(run_ref)
        ):
            raise _Refused("TARGET_EVENT_STATE_OR_SCOPE_MISMATCH")
        return str(event.event_id), str(run["actor_scope_ref"])


def _verify(
    sessions: sessionmaker[Session], run_ref: str, event_id: str
) -> None:
    request_id = lifecycle_request_id(run_ref)
    with sessions() as session:
        run_state, active_owner = session.execute(
            select(
                story_tables.story_runs.c.run_state,
                story_tables.story_runs.c.active_owner_parent_account_id,
            ).where(story_tables.story_runs.c.run_id == run_ref)
        ).one()
        event = session.get(CoreOutboxEventModel, event_id)
        receipt = session.get(DataLifecycleRequestModel, request_id)
    if run_state != "DELETED" or active_owner is not None:
        raise _Refused("TARGET_RUN_FINAL_STATE_INVALID")
    if event is None or event.status != "delivered" or event.delivered_at is None:
        raise _Refused("TARGET_EVENT_NOT_DELIVERED")
    if (
        receipt is None
        or receipt.state != "completed"
        or receipt.unresolved_items != 0
        or receipt.completed_at is None
    ):
        raise _Refused("TARGET_LIFECYCLE_RECEIPT_NOT_COMPLETE")


def _make_consumer(
    sessions: sessionmaker[Session], engine: object, settings: Settings, worker_id: str
) -> Be1LifecycleConsumer:
    access_key = settings.s3_access_key.get_secret_value() if settings.s3_access_key else ""
    secret_key = settings.s3_secret_key.get_secret_value() if settings.s3_secret_key else ""
    if not access_key or not secret_key:
        raise _Refused("OBJECT_STORE_CREDENTIALS_MISSING")
    storage = Boto3S3CompatibleObjectStorage(
        bucket=settings.s3_bucket,
        endpoint_url=settings.s3_endpoint,
        region_name=settings.s3_region,
        access_key=access_key,
        secret_key=secret_key,
    )
    story = SqlStoryLifecycleStore(sessions)
    return Be1LifecycleConsumer(
        outbox=PostgresOutbox(sessions),
        receipts=SqlLifecycleReceiptStore(sessions),
        audit=SqlLifecycleAuditWriter(),
        uploads=SqlCoreRunUploadClose(sessions),
        notices=SqlParentLifecycleNoticeStore(engine, clock=lambda: datetime.now(UTC)),
        assets=SqlCoreRunAssetPurge(sessions, storage),
        story=story,
        story_refs=story,
        config=ConsumerConfig(worker_id=worker_id),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    if args.run_id != APPROVED_RUN_REF:
        print("LIFECYCLE_REFUSED code=RUN_NOT_APPROVED", file=sys.stderr)
        return 2

    settings = Settings()
    if settings.env != "local" or not settings.database_url:
        print("LIFECYCLE_REFUSED code=NON_LOCAL_OR_DATABASE_UNCONFIGURED", file=sys.stderr)
        return 2
    if (settings.s3_endpoint, settings.s3_bucket) != EXPECTED_OBJECT_STORE:
        print("LIFECYCLE_REFUSED code=OBJECT_STORE_TARGET_MISMATCH", file=sys.stderr)
        return 2

    database_url = settings.database_url.get_secret_value()
    try:
        database = make_url(database_url)
    except Exception:
        print("LIFECYCLE_REFUSED code=DATABASE_URL_INVALID", file=sys.stderr)
        return 2
    if (database.host, database.port, database.database) != EXPECTED_DATABASE:
        print("LIFECYCLE_REFUSED code=DATABASE_TARGET_MISMATCH", file=sys.stderr)
        return 2

    engine = create_core_engine(database_url)
    sessions = create_core_session_factory(engine)
    try:
        with engine.connect() as connection:
            database_name = connection.exec_driver_sql("SELECT current_database()").scalar_one()
        if database_name != EXPECTED_DATABASE[2]:
            raise _Refused("CONNECTED_DATABASE_MISMATCH")
        event_id, _scope_ref = _preflight(sessions, args.run_id)
        consumer = _make_consumer(
            sessions,
            engine,
            settings,
            worker_id="parent-lifecycle-once-" + uuid4().hex[:12],
        )
        outcome = consumer.run_once(target_run_ref=args.run_id)
        if outcome != "completed":
            raise _Refused("LIFECYCLE_CONSUMER_NOT_COMPLETED")
        _verify(sessions, args.run_id, event_id)
    except _Refused as refused:
        print(f"LIFECYCLE_STOP code={refused.code}", file=sys.stderr)
        return 1
    except Exception as exc:
        logging.getLogger("sketch2life.parent_lifecycle_once").error(
            "lifecycle_one_shot_failed error_type=%s", type(exc).__name__
        )
        print("LIFECYCLE_STOP code=UNEXPECTED_ERROR", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print("LIFECYCLE_COMPLETED run_state=DELETED event=delivered receipt=completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
