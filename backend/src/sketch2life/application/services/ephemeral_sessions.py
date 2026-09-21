"""Process-local session bootstrap/read use cases for the Android demo."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import RLock
from uuid import UUID

from sketch2life.application.ports.demo_workflow_storage import (
    DemoWorkflowRecord,
    DemoWorkflowStore,
)
from sketch2life.application.ports.session_storage import (
    ArtifactStore,
    DuplicateSessionError,
    IdempotencyConflict,
    IdempotencyReceipt,
    IdempotencyStore,
    SessionRecord,
    SessionRepository,
)
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
    WorkflowFailureV1,
    WorkflowResultProvenanceV1,
)
from sketch2life.contracts.schemas.workflow_records import SessionSnapshotV1

DEMO_ACTOR_REF = "demo:local"
SESSION_CREATE_OPERATION = "CREATE_SESSION"


class SessionWorkflowError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        safe_message: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code
        self.safe_message = safe_message
        self.retryable = retryable


class EphemeralSessionService:
    """Owns session creation and reads; storage stays replaceable behind ports."""

    def __init__(
        self,
        *,
        sessions: SessionRepository[SessionSnapshotV1],
        idempotency: IdempotencyStore,
        artifacts: ArtifactStore,
        workflow_data: DemoWorkflowStore | None = None,
        idle_ttl_seconds: int = 1800,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if not 60 <= idle_ttl_seconds <= 86_400:
            raise ValueError("session idle TTL must be between 60 and 86400 seconds")
        self._sessions = sessions
        self._idempotency = idempotency
        self._artifacts = artifacts
        self._workflow_data = workflow_data
        self._idle_ttl_seconds = idle_ttl_seconds
        self._now = now
        self._lock = RLock()

    def create(self, command: MobileWorkflowCommandV1) -> tuple[MobileWorkflowResultV1, bool]:
        self._validate_create(command)
        session_id = command.session_id
        scope = f"{session_id}:{SESSION_CREATE_OPERATION}"
        fingerprint = _request_fingerprint(command)

        with self._lock:
            self._purge_expired(_aware_now(self._now()))
            existing_receipt = self._idempotency.get(scope=scope, key=command.idempotency_key)
            if existing_receipt is not None:
                if existing_receipt.request_sha256 != fingerprint:
                    raise SessionWorkflowError(
                        code="IDEMPOTENCY_KEY_CONFLICT",
                        status_code=409,
                        safe_message="This retry key was already used for a different request.",
                    )
                replay = MobileWorkflowResultV1.model_validate_json(existing_receipt.response_body)
                snapshot = SessionSnapshotV1.model_validate(replay.payload)
                if snapshot.expires_at <= _aware_now(self._now()):
                    self._expire(session_id)
                    raise _expired_error()
                return replay, True

            now = _aware_now(self._now())
            expires_at = now + timedelta(seconds=self._idle_ttl_seconds)
            snapshot = SessionSnapshotV1(
                session_id=session_id,
                version=0,
                state="CREATED",
                status="ACTIVE",
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
            )
            result = _success(command, snapshot)
            record = SessionRecord(
                session_id=session_id,
                version=0,
                expires_at=expires_at,
                snapshot=snapshot,
                owner_principal_key=None,
            )
            try:
                self._sessions.create(record)
            except DuplicateSessionError as exc:
                raise SessionWorkflowError(
                    code="SESSION_ALREADY_EXISTS",
                    status_code=409,
                    safe_message="A session with this identifier already exists.",
                ) from exc

            if self._workflow_data is not None:
                try:
                    self._workflow_data.create(session_id)
                except ValueError as exc:
                    self._sessions.delete(session_id)
                    raise SessionWorkflowError(
                        code="SESSION_ALREADY_EXISTS",
                        status_code=409,
                        safe_message="A session with this identifier already exists.",
                    ) from exc

            receipt = IdempotencyReceipt(
                scope=scope,
                key=command.idempotency_key,
                request_sha256=fingerprint,
                response_body=result.model_dump_json().encode("utf-8"),
            )
            try:
                self._idempotency.record(receipt)
            except IdempotencyConflict as exc:
                self._sessions.delete(session_id)
                if self._workflow_data is not None:
                    self._workflow_data.delete(session_id)
                raise SessionWorkflowError(
                    code="IDEMPOTENCY_KEY_CONFLICT",
                    status_code=409,
                    safe_message="This retry key was already used for a different request.",
                ) from exc
            return result, False

    def snapshot(self, session_id: str) -> SessionSnapshotV1:
        """Return the current active snapshot after applying the standard expiry cleanup."""
        now = _aware_now(self._now())
        with self._lock:
            record = self._sessions.get(session_id)
            if record is not None and record.expires_at <= now:
                self._expire(session_id)
                raise _expired_error()
            self._purge_expired(now)
            record = self._sessions.get(session_id)
            if record is None:
                raise SessionWorkflowError(
                    code="SESSION_NOT_FOUND",
                    status_code=404,
                    safe_message="This temporary session is unavailable. Start a new session.",
                )
            return SessionSnapshotV1.model_validate(record.snapshot)

    def workflow_record(self, session_id: str) -> DemoWorkflowRecord:
        if self._workflow_data is None:
            raise SessionWorkflowError(
                code="WORKFLOW_STORAGE_UNAVAILABLE",
                status_code=503,
                safe_message="The temporary workflow store is not configured.",
            )
        record = self._workflow_data.get(session_id)
        if record is None:
            raise SessionWorkflowError(
                code="SESSION_NOT_FOUND",
                status_code=404,
                safe_message="This temporary session is unavailable. Start a new session.",
            )
        return record

    def advance(
        self,
        *,
        session_id: str,
        expected_version: int,
        allowed_states: tuple[str, ...],
        next_state: str,
        workflow_updates: dict[str, object],
    ) -> SessionSnapshotV1:
        """Atomically advance the ephemeral aggregate and its session-only workflow data."""
        if self._workflow_data is None:
            raise SessionWorkflowError(
                code="WORKFLOW_STORAGE_UNAVAILABLE",
                status_code=503,
                safe_message="The temporary workflow store is not configured.",
            )
        now = _aware_now(self._now())
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                raise SessionWorkflowError(
                    code="SESSION_NOT_FOUND",
                    status_code=404,
                    safe_message="This temporary session is unavailable. Start a new session.",
                )
            if record.expires_at <= now:
                self._expire(session_id)
                raise _expired_error()
            snapshot = SessionSnapshotV1.model_validate(record.snapshot)
            if snapshot.version != expected_version:
                raise SessionWorkflowError(
                    code="STALE_SESSION_VERSION",
                    status_code=409,
                    safe_message="The session changed. Refresh it before continuing.",
                )
            if snapshot.state not in allowed_states:
                raise SessionWorkflowError(
                    code="WORKFLOW_STEP_NOT_ALLOWED",
                    status_code=409,
                    safe_message=(
                        "This workflow step is not available in the current session state."
                    ),
                )
            workflow = self._workflow_data.get(session_id)
            if workflow is None or workflow.version != expected_version:
                raise SessionWorkflowError(
                    code="STALE_SESSION_VERSION",
                    status_code=409,
                    safe_message="The session changed. Refresh it before continuing.",
                )
            updated_values = {**workflow.values, **workflow_updates}
            updated_workflow = DemoWorkflowRecord(
                session_id=session_id,
                version=expected_version + 1,
                values=updated_values,
            )
            updated_snapshot = SessionSnapshotV1.model_validate(
                {
                    **snapshot.model_dump(mode="python"),
                    "version": expected_version + 1,
                    "state": next_state,
                    "updated_at": now,
                    "expires_at": now + timedelta(seconds=self._idle_ttl_seconds),
                }
            )
            updated_record = SessionRecord(
                session_id=session_id,
                version=expected_version + 1,
                expires_at=updated_snapshot.expires_at,
                snapshot=updated_snapshot,
                owner_principal_key=record.owner_principal_key,
            )
            try:
                self._sessions.compare_and_swap(
                    session_id=session_id,
                    expected_version=expected_version,
                    record=updated_record,
                )
                self._workflow_data.replace(
                    session_id,
                    expected_version=expected_version,
                    record=updated_workflow,
                )
            except ValueError as exc:
                raise SessionWorkflowError(
                    code="STALE_SESSION_VERSION",
                    status_code=409,
                    safe_message="The session changed. Refresh it before continuing.",
                ) from exc
            return updated_snapshot

    def read(
        self,
        *,
        session_id: str,
        request_id: str,
        expected_session_version: int,
    ) -> MobileWorkflowResultV1:
        now = _aware_now(self._now())
        with self._lock:
            candidate = self._sessions.get(session_id)
            if candidate is not None and candidate.expires_at <= now:
                self._expire(session_id)
                raise _expired_error()
            self._purge_expired(now)
            record = self._sessions.get(session_id)
        if record is None:
            raise SessionWorkflowError(
                code="SESSION_NOT_FOUND",
                status_code=404,
                safe_message="This temporary session is unavailable. Start a new session.",
            )
        if record.expires_at <= now:
            self._expire(session_id)
            raise _expired_error()
        snapshot = SessionSnapshotV1.model_validate(record.snapshot)
        return MobileWorkflowResultV1(
            status="SUCCEEDED",
            request_id=request_id,
            session_id=session_id,
            expected_session_version=expected_session_version,
            observed_session_version=record.version,
            provenance=_provenance(),
            payload=snapshot.model_dump(mode="json"),
        )

    def _validate_create(self, command: MobileWorkflowCommandV1) -> None:
        try:
            parsed_id = UUID(command.session_id)
        except ValueError as exc:
            raise SessionWorkflowError(
                code="INVALID_SESSION_ID",
                status_code=422,
                safe_message="Create the session with a client-generated UUIDv4.",
            ) from exc
        if parsed_id.version != 4 or str(parsed_id) != command.session_id.lower():
            raise SessionWorkflowError(
                code="INVALID_SESSION_ID",
                status_code=422,
                safe_message="Create the session with a client-generated UUIDv4.",
            )
        if command.expected_session_version != 0:
            raise SessionWorkflowError(
                code="BOOTSTRAP_VERSION_MUST_BE_ZERO",
                status_code=409,
                safe_message="A new session must start at version zero.",
            )
        if command.actor_ref != DEMO_ACTOR_REF:
            raise SessionWorkflowError(
                code="DEMO_ACTOR_INVALID",
                status_code=422,
                safe_message="The local demo actor marker is invalid.",
            )
        if command.payload != {"operation": SESSION_CREATE_OPERATION}:
            raise SessionWorkflowError(
                code="INVALID_CREATE_OPERATION",
                status_code=422,
                safe_message="The session creation operation is not supported.",
            )

    def _expire(self, session_id: str) -> None:
        self._sessions.delete(session_id)
        self._artifacts.delete_session(session_id)
        if self._workflow_data is not None:
            self._workflow_data.delete(session_id)
        self._idempotency.delete_scope(f"{session_id}:{SESSION_CREATE_OPERATION}")

    def _purge_expired(self, now: datetime) -> None:
        for session_id in self._sessions.expired_before(now):
            self._expire(session_id)


def failure_result(
    *,
    request_id: str,
    session_id: str,
    expected_session_version: int,
    observed_session_version: int | None,
    error: SessionWorkflowError,
) -> MobileWorkflowResultV1:
    return MobileWorkflowResultV1(
        status="FAILED",
        request_id=request_id,
        session_id=session_id,
        expected_session_version=expected_session_version,
        observed_session_version=(
            expected_session_version
            if observed_session_version is None
            else observed_session_version
        ),
        provenance=_provenance(),
        failure=WorkflowFailureV1(
            domain="SESSION",
            code=error.code,
            retryable=error.retryable,
            safe_message=error.safe_message,
        ),
    )


def _success(
    command: MobileWorkflowCommandV1, snapshot: SessionSnapshotV1
) -> MobileWorkflowResultV1:
    return MobileWorkflowResultV1(
        status="SUCCEEDED",
        request_id=command.request_id,
        session_id=command.session_id,
        expected_session_version=command.expected_session_version,
        observed_session_version=snapshot.version,
        provenance=_provenance(),
        payload=snapshot.model_dump(mode="json"),
    )


def _provenance() -> WorkflowResultProvenanceV1:
    return WorkflowResultProvenanceV1(
        producer="APPLICATION",
        component="ephemeral-session-service",
        component_version="1.0",
        source_contracts=("MobileWorkflowCommandV1", "SessionSnapshotV1"),
    )


def _request_fingerprint(command: MobileWorkflowCommandV1) -> str:
    data = command.model_dump(mode="json", exclude={"created_at"})
    normalized = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(normalized.encode("utf-8")).hexdigest()


def _aware_now(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("session clock must return timezone-aware timestamps")
    return value.astimezone(UTC)


def _expired_error() -> SessionWorkflowError:
    return SessionWorkflowError(
        code="SESSION_EXPIRED",
        status_code=410,
        safe_message="This temporary session expired. Start a new session.",
    )


__all__ = [
    "DEMO_ACTOR_REF",
    "EphemeralSessionService",
    "SESSION_CREATE_OPERATION",
    "SessionWorkflowError",
    "failure_result",
]
