"""Owner-run composition root for the FR-C-08 BE1 lifecycle consumer (Allowlist Draft 13 §7).

The tool wires the BE1 lifecycle consumer to PostgreSQL and a local S3-compatible store and
processes lifecycle events one at a time. It is owner-run only and refuses to start unless the
database and the object store match an explicit allow-list (fail closed):

* the database URL host is loopback, its port is not 5432 or 5433, its database name contains
  ``frc08`` and is not ``sketch2life_m2_s1a``, ``be1_acceptance`` or a seed database, and the
  name and port equal ``FRC08_ALLOWED_DATABASE`` and ``FRC08_ALLOWED_PORT``;
* the S3 endpoint is a loopback URL equal to ``FRC08_ALLOWED_ENDPOINT`` and the bucket contains
  ``frc08`` and equals ``FRC08_ALLOWED_BUCKET``.

Inputs come only from ``FRC08_*`` environment variables set by the owner's command file; the
application settings and ``.env`` values are never read. Nothing secret is printed.

    python tools/run_be1_lifecycle_consumer.py --max-events 20
"""

from __future__ import annotations

import argparse
import ipaddress
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

FORBIDDEN_DATABASES = frozenset({"sketch2life_m2_s1a", "be1_acceptance"})
FORBIDDEN_PORTS = frozenset({5432, 5433})
REQUIRED_MARKER = "frc08"


class TargetRefused(RuntimeError):
    """A database or storage target outside the §7 allow-list; nothing was contacted."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Frc08Targets:
    database_url: str
    database_name: str
    database_port: int
    s3_endpoint: str | None
    s3_bucket: str | None


def _loopback(host: str | None) -> bool:
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def check_database_url(url: str, allowed: Mapping[str, str]) -> tuple[str, int]:
    """Return (database name, port) only for an allowed disposable loopback database."""

    parts = urlsplit(url)
    if parts.scheme not in {"postgresql", "postgresql+psycopg"}:
        raise TargetRefused("DATABASE_SCHEME_REFUSED")
    if parts.query or parts.fragment:
        raise TargetRefused("DATABASE_URL_OPTIONS_REFUSED")
    if not _loopback(parts.hostname):
        raise TargetRefused("DATABASE_HOST_NOT_LOOPBACK")
    try:
        port = parts.port
    except ValueError:
        raise TargetRefused("DATABASE_PORT_INVALID") from None
    if port is None or port in FORBIDDEN_PORTS:
        raise TargetRefused("DATABASE_PORT_REFUSED")
    name = parts.path.lstrip("/")
    lowered = name.lower()
    if (
        not name
        or "/" in name
        or REQUIRED_MARKER not in lowered
        or lowered in FORBIDDEN_DATABASES
        or "seed" in lowered
    ):
        raise TargetRefused("DATABASE_NAME_REFUSED")
    if allowed.get("FRC08_ALLOWED_DATABASE") != name:
        raise TargetRefused("DATABASE_NOT_ALLOW_LISTED")
    if allowed.get("FRC08_ALLOWED_PORT") != str(port):
        raise TargetRefused("DATABASE_PORT_NOT_ALLOW_LISTED")
    return name, port


def check_storage_target(endpoint: str, bucket: str, allowed: Mapping[str, str]) -> None:
    parts = urlsplit(endpoint)
    if parts.scheme not in {"http", "https"} or parts.path not in {"", "/"}:
        raise TargetRefused("STORAGE_ENDPOINT_REFUSED")
    if parts.query or parts.fragment or parts.username or parts.password:
        raise TargetRefused("STORAGE_ENDPOINT_REFUSED")
    if not _loopback(parts.hostname):
        raise TargetRefused("STORAGE_ENDPOINT_NOT_LOOPBACK")
    if allowed.get("FRC08_ALLOWED_ENDPOINT") != endpoint:
        raise TargetRefused("STORAGE_ENDPOINT_NOT_ALLOW_LISTED")
    if REQUIRED_MARKER not in bucket.lower() or allowed.get("FRC08_ALLOWED_BUCKET") != bucket:
        raise TargetRefused("STORAGE_BUCKET_REFUSED")


def load_targets(environ: Mapping[str, str], *, require_storage: bool) -> Frc08Targets:
    """Read and check the ``FRC08_*`` targets; raise ``TargetRefused`` before any contact."""

    url = environ.get("FRC08_DATABASE_URL", "")
    if not url:
        raise TargetRefused("DATABASE_URL_MISSING")
    name, port = check_database_url(url, environ)
    endpoint = environ.get("FRC08_S3_ENDPOINT") or None
    bucket = environ.get("FRC08_S3_BUCKET") or None
    if require_storage or endpoint or bucket:
        if not endpoint or not bucket:
            raise TargetRefused("STORAGE_TARGET_MISSING")
        check_storage_target(endpoint, bucket, environ)
        if not environ.get("FRC08_S3_ACCESS_KEY") or not environ.get("FRC08_S3_SECRET_KEY"):
            raise TargetRefused("STORAGE_CREDENTIALS_MISSING")
    return Frc08Targets(url, name, port, endpoint, bucket)


def build_engine(targets: Frc08Targets) -> Any:
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    return create_engine(
        targets.database_url,
        poolclass=NullPool,
        hide_parameters=True,
        # DTR §6.3: every call also has its own statement timeout (30 s per statement).
        connect_args={"connect_timeout": 5, "options": "-c statement_timeout=30000"},
    )


def build_consumer(
    targets: Frc08Targets, environ: Mapping[str, str], *, worker_id: str
) -> tuple[Any, Any]:
    """Compose the consumer from the owner adapters; returns (consumer, engine)."""

    from sqlalchemy.orm import sessionmaker

    from sketch2life.infrastructure.ai_jobs.sql.repository import SqlParentLifecycleNoticeStore
    from sketch2life.infrastructure.persistence.be1_lifecycle_consumer import (
        Be1LifecycleConsumer,
        ConsumerConfig,
        SqlLifecycleAuditWriter,
        SqlLifecycleReceiptStore,
    )
    from sketch2life.infrastructure.persistence.core_lifecycle_store import (
        SqlCoreRunAssetPurge,
        SqlCoreRunUploadClose,
    )
    from sketch2life.infrastructure.persistence.outbox import PostgresOutbox
    from sketch2life.infrastructure.persistence.story_lifecycle_store import (
        SqlStoryLifecycleStore,
    )
    from sketch2life.infrastructure.storage.s3_compatible import (
        Boto3S3CompatibleObjectStorage,
    )

    if targets.s3_endpoint is None or targets.s3_bucket is None:
        raise TargetRefused("STORAGE_TARGET_MISSING")
    engine = build_engine(targets)
    sessions = sessionmaker(engine, expire_on_commit=False, autoflush=False)
    storage = Boto3S3CompatibleObjectStorage(
        bucket=targets.s3_bucket,
        endpoint_url=targets.s3_endpoint,
        region_name=environ.get("FRC08_S3_REGION", "us-east-1"),
        access_key=environ["FRC08_S3_ACCESS_KEY"],
        secret_key=environ["FRC08_S3_SECRET_KEY"],
    )
    story = SqlStoryLifecycleStore(sessions)
    consumer = Be1LifecycleConsumer(
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
    return consumer, engine


def main(argv: list[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-events", type=int, default=20)
    parser.add_argument("--worker-id", default=f"frc08-lifecycle-{uuid4().hex[:12]}")
    args = parser.parse_args(argv)
    env = os.environ if environ is None else environ
    if not 1 <= args.max_events <= 1000:
        print("REFUSED code=MAX_EVENTS_OUT_OF_RANGE", file=sys.stderr)
        return 2
    try:
        targets = load_targets(env, require_storage=True)
    except TargetRefused as refused:
        print(f"REFUSED code={refused.code}", file=sys.stderr)
        return 2
    consumer, engine = build_consumer(targets, env, worker_id=args.worker_id)
    outcomes: dict[str, int] = {}
    try:
        for _ in range(args.max_events):
            outcome = consumer.run_once()
            if outcome is None:
                break
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
    finally:
        engine.dispose()
    summary = " ".join(f"{key}={value}" for key, value in sorted(outcomes.items()))
    print(f"FRC08_CONSUMER_DONE {summary or 'no_events'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
