"""Local/test-only operator command for the FEAT-064 synthetic eligibility pilot.

Creates a SYNTHETIC_DEV profile, issues a scoped proof and revokes it. There is no HTTP route
for any of this. Every command defaults to a dry run that never opens a database connection;
a write needs ``--apply``. The command refuses unless the runtime environment is ``local`` or
``test``, the pilot setting is on, ``--pilot`` is given, and the database is loopback or a
disposable ``be1_acceptance`` database. It never prints settings or connection strings.

Run from ``backend/`` with ``PYTHONPATH=src``:
    python ../tools/synthetic_eligibility.py issue --pilot --organization-id ... --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

POLICY_VERSION = "feat064-synthetic-pilot-v1"
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_ALLOWED_ENVIRONMENTS = frozenset({"local", "test"})
_DISPOSABLE_DATABASE_MARKER = "be1_acceptance"
_MAX_TTL_MINUTES = 24 * 60


class SafetyError(Exception):
    """Raised for any refusal; messages never include settings or connection strings."""


class SettingsLike(Protocol):
    @property
    def env(self) -> str: ...

    @property
    def synthetic_pilot_enabled(self) -> bool: ...


class ProofStore(Protocol):
    def create_synthetic_profile(
        self,
        *,
        organization_id: str,
        class_id: str,
        child_id: str,
        display_name: str,
        age_months: int,
        created_by: str,
    ) -> bool: ...

    def issue_synthetic_proof(
        self,
        *,
        evidence_id: str,
        organization_id: str,
        class_id: str,
        child_id: str,
        purpose_ref: str,
        run_ref: str,
        session_id: str | None,
        issued_by: str,
        issued_at: datetime,
        expires_at: datetime,
        policy_version: str,
    ) -> bool: ...

    def revoke_synthetic_proof(
        self, *, evidence_id: str, organization_id: str, revoked_at: datetime
    ) -> bool: ...


def _query_hosts(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (tuple, list)):
        return [str(item) for item in value]
    return [str(value)]


def check_database_url(url: str | None) -> None:
    """Refuse unless every effective host is loopback or the database is a disposable one."""
    if not url:
        raise SafetyError("a database URL is not configured")
    try:
        parsed = make_url(url)
    except ArgumentError:
        raise SafetyError("the database URL is not valid") from None
    # `host` and `hostaddr` in the query string override the URL host, so inspect them too.
    # No DNS lookup is performed: a name that is not literally loopback is not loopback.
    hosts = [parsed.host or "", *_query_hosts(parsed.query.get("host"))]
    hosts.extend(_query_hosts(parsed.query.get("hostaddr")))
    loopback = all(host in _LOOPBACK_HOSTS for host in hosts)
    disposable = _DISPOSABLE_DATABASE_MARKER in (parsed.database or "")
    if not (loopback or disposable):
        raise SafetyError(
            "refused: the database host is not loopback and the database name does not"
            f" contain {_DISPOSABLE_DATABASE_MARKER}"
        )


def check_runtime(settings: SettingsLike, *, pilot_flag: bool) -> None:
    if settings.env not in _ALLOWED_ENVIRONMENTS:
        raise SafetyError("refused: the environment must be local or test")
    if settings.synthetic_pilot_enabled is not True:
        raise SafetyError("refused: the synthetic pilot setting is off")
    if not pilot_flag:
        raise SafetyError("refused: pass --pilot to confirm the synthetic pilot")


def _text(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 128:
        raise SafetyError(f"{label} must be 1-128 characters")
    return cleaned


_SYNTHETIC_CHILD_ID = re.compile(r"^synthetic-[a-z0-9][a-z0-9-]{0,99}$")


def _synthetic_child_id(value: str) -> str:
    """Only a clearly artificial id is accepted, so a real child's identifier cannot be stored."""
    cleaned = value.strip()
    if not _SYNTHETIC_CHILD_ID.fullmatch(cleaned):
        raise SafetyError("refused: the child id must match synthetic-[a-z0-9-]{1,100}")
    return cleaned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pilot", action="store_true", help="confirm the synthetic pilot")
    common.add_argument("--apply", action="store_true", help="write; the default is a dry run")
    common.add_argument("--operator", default="local-operator", help="recorded as issued_by")
    sub = parser.add_subparsers(dest="command", required=True)
    profile = sub.add_parser(
        "create-profile", parents=[common], help="create a SYNTHETIC_DEV profile"
    )
    profile.add_argument("--organization-id", required=True)
    profile.add_argument("--class-id", required=True)
    profile.add_argument("--child-id", required=True, help="must start with 'synthetic-'")
    # No display-name option: the name is derived from the id so no real name can be stored.
    profile.add_argument("--age-months", type=int, required=True)
    issue = sub.add_parser(
        "issue", parents=[common], help="issue a scoped proof for a SYNTHETIC_DEV profile"
    )
    issue.add_argument("--organization-id", required=True)
    issue.add_argument("--class-id", required=True)
    issue.add_argument("--child-id", required=True, help="must start with 'synthetic-'")
    issue.add_argument("--purpose-ref", required=True)
    issue.add_argument("--run-ref", required=True)
    # Required: the run reference lives in teacher-writable session configuration, so a proof
    # is only honored when it names the exact session the operator intends.
    issue.add_argument("--session-id", required=True)
    issue.add_argument("--ttl-minutes", type=int, default=60)
    issue.add_argument("--evidence-id")
    revoke = sub.add_parser("revoke", parents=[common], help="revoke a proof once")
    revoke.add_argument("--organization-id", required=True)
    revoke.add_argument("--evidence-id", required=True)
    return parser


def _default_store(url: str) -> ProofStore:
    from sketch2life.infrastructure.persistence.core_store import PostgresCoreStore
    from sketch2life.infrastructure.persistence.database import (
        create_core_engine,
        create_core_session_factory,
    )

    return PostgresCoreStore(create_core_session_factory(create_core_engine(url)))


def _default_settings() -> SettingsLike:
    from sketch2life.infrastructure.config.settings import get_settings

    return get_settings()


def _default_database_url() -> str | None:
    from sketch2life.infrastructure.config.settings import get_core_database_settings

    secret = get_core_database_settings().database_url
    return secret.get_secret_value() if secret else None


def run(
    argv: Sequence[str],
    *,
    settings_loader: Callable[[], SettingsLike] = _default_settings,
    database_url_loader: Callable[[], str | None] = _default_database_url,
    store_factory: Callable[[str], ProofStore] = _default_store,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    emit: Callable[[str], None] = print,
) -> int:
    args = build_parser().parse_args(list(argv))
    try:
        check_runtime(settings_loader(), pilot_flag=args.pilot)
        url = database_url_loader()
        check_database_url(url)
        assert url is not None
        plan = _plan(args, clock())
    except SafetyError as exc:
        emit(str(exc))
        return 2
    if not args.apply:
        emit(f"DRY-RUN (no database connection opened): {plan.description}")
        return 0
    store = store_factory(url)
    try:
        done = plan.execute(store)
    except ValueError as exc:
        emit(f"refused: {exc}")
        return 1
    emit(f"APPLIED: {plan.description}" if done else f"NOT APPLIED (conflict): {plan.description}")
    return 0 if done else 1


class _Plan:
    def __init__(self, description: str, execute: Callable[[ProofStore], bool]) -> None:
        self.description = description
        self.execute = execute


def _plan(args: argparse.Namespace, now: datetime) -> _Plan:
    organization_id = _text(args.organization_id, "organization id")
    if args.command == "create-profile":
        class_id = _text(args.class_id, "class id")
        child_id = _synthetic_child_id(args.child_id)
        display_name = f"Synthetic {child_id}"
        if not 36 <= args.age_months <= 155:
            raise SafetyError("age months must be between 36 and 155")
        return _Plan(
            f"create SYNTHETIC_DEV profile {child_id} in {organization_id}/{class_id}",
            lambda store: store.create_synthetic_profile(
                organization_id=organization_id,
                class_id=class_id,
                child_id=child_id,
                display_name=display_name,
                age_months=args.age_months,
                created_by=args.operator,
            ),
        )
    if args.command == "revoke":
        evidence_id = _text(args.evidence_id, "evidence id")
        return _Plan(
            f"revoke proof {evidence_id} in {organization_id}",
            lambda store: store.revoke_synthetic_proof(
                evidence_id=evidence_id, organization_id=organization_id, revoked_at=now
            ),
        )
    class_id = _text(args.class_id, "class id")
    child_id = _synthetic_child_id(args.child_id)
    purpose_ref = _text(args.purpose_ref, "purpose ref")
    run_ref = _text(args.run_ref, "run ref")
    if not 1 <= args.ttl_minutes <= _MAX_TTL_MINUTES:
        raise SafetyError(f"ttl minutes must be between 1 and {_MAX_TTL_MINUTES}")
    session_id = _text(args.session_id, "session id")
    evidence_id = _text(args.evidence_id, "evidence id") if args.evidence_id else str(uuid4())
    expires_at = now + timedelta(minutes=args.ttl_minutes)
    return _Plan(
        f"issue proof {evidence_id} for {child_id} in {organization_id}/{class_id}"
        f" (purpose {purpose_ref}, run {run_ref}, expires {expires_at.isoformat()})",
        lambda store: store.issue_synthetic_proof(
            evidence_id=evidence_id,
            organization_id=organization_id,
            class_id=class_id,
            child_id=child_id,
            purpose_ref=purpose_ref,
            run_ref=run_ref,
            session_id=session_id,
            issued_by=args.operator,
            issued_at=now,
            expires_at=expires_at,
            policy_version=POLICY_VERSION,
        ),
    )


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
