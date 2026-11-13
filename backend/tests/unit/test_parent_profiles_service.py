"""Parent service gating and repository boundary tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import (
    ParentCommandResult,
    ParentProfileListResult,
)
from sketch2life.application.services.parent_profiles import ParentProfileService
from sketch2life.domain.parent_profiles import ParentProfileError, ProfileSnapshot
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)


class RecordingRepository:
    def __init__(self) -> None:
        self.create_calls = 0

    def create_profile(self, **kwargs: object) -> ParentCommandResult:
        self.create_calls += 1
        return ParentCommandResult(201, {"profile_id": "generated"})

    def assert_profile_owned(self, **kwargs: object) -> None:
        del kwargs

    def get_profile(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        return {"profile_id": "generated"}

    def list_profiles(self, **kwargs: object) -> ParentProfileListResult:
        del kwargs
        return ParentProfileListResult(items=[], next_cursor=None)

    def patch_profile(self, **kwargs: object) -> ParentCommandResult:
        return ParentCommandResult(200, {"profile_id": "generated"})

    def delete_profile(self, **kwargs: object) -> ParentCommandResult:
        del kwargs
        return ParentCommandResult(202, {"profile_id": "generated"})


def test_disabled_synthetic_creation_fails_before_repository_write() -> None:
    repository = RecordingRepository()
    service = ParentProfileService(repository, synthetic_enabled=False)

    try:
        service.create_profile(
            principal=VerifiedPrincipal("parent-1", "issuer-1", frozenset()),
            snapshot=ProfileSnapshot("Mina", 72, None),
            idempotency_key="synthetic-key",
            request_id="request-1",
        )
    except ParentProfileError as error:
        assert error.status_code == 409
        assert error.code == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"
    else:
        raise AssertionError("disabled synthetic creation unexpectedly succeeded")

    assert repository.create_calls == 0


def test_enabled_synthetic_creation_validates_then_delegates_once() -> None:
    repository = RecordingRepository()
    service = ParentProfileService(repository, synthetic_enabled=True)

    result = service.create_profile(
        principal=VerifiedPrincipal("parent-1", "issuer-1", frozenset()),
        snapshot=ProfileSnapshot("Mina", 72, None),
        idempotency_key="synthetic-key",
        request_id="request-1",
    )

    assert result.status_code == 201
    assert repository.create_calls == 1


@dataclass
class _DeleteProfile:
    parent_profile_id: UUID
    state: str = "ACTIVE"
    updated_at: datetime | None = None


@dataclass
class _DeleteReceipt:
    request_fingerprint: bytes
    response_status: int
    response_body: dict[str, object]


class _TransactionOnlySession:
    def begin(self) -> AbstractContextManager[None]:
        return nullcontext()


class _AutobeginSessionDouble:
    def __init__(self, scalar_results: list[object]) -> None:
        self.scalar_results = scalar_results
        self.scalar_index = 0
        self.transaction_active = False
        self.added: list[object] = []

    def begin(self) -> AbstractContextManager[None]:
        if self.transaction_active:
            raise InvalidRequestError("A transaction is already begun on this Session.")
        return self._transaction()

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self.transaction_active = True
        try:
            yield
        finally:
            self.transaction_active = False

    def scalar(self, _statement: object) -> object:
        self.transaction_active = True
        if self.scalar_index >= len(self.scalar_results):
            raise AssertionError("unexpected scalar query")
        result = self.scalar_results[self.scalar_index]
        self.scalar_index += 1
        return result

    def execute(self, _statement: object, _parameters: object = None) -> None:
        assert self.transaction_active

    def add(self, instance: object) -> None:
        assert self.transaction_active
        self.added.append(instance)

    def flush(self) -> None:
        assert self.transaction_active


@dataclass
class _AutobeginProfile:
    parent_profile_id: UUID
    owner_issuer: str
    owner_subject: str
    current_revision_no: int = 1
    state: str = "ACTIVE"
    deleted_at: datetime | None = None
    data_origin: str = "SYNTHETIC_DEV"
    updated_at: datetime | None = None


def test_read_only_ownership_checks_leave_session_ready_for_patch_and_delete() -> None:
    principal = VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    profile_id = uuid4()
    profile = _AutobeginProfile(
        parent_profile_id=profile_id,
        owner_issuer=principal.issuer,
        owner_subject=principal.subject,
    )
    session = _AutobeginSessionDouble(
        [profile, profile, None, profile, None, profile]
    )
    repository = SqlParentProfileRepository(cast(Session, session))

    repository.assert_profile_owned(principal=principal, profile_id=profile_id)
    patched = repository.patch_profile(
        principal=principal,
        profile_id=profile_id,
        expected_revision=1,
        snapshot=ProfileSnapshot("Mina updated", 73, None),
        idempotency_key="patch-key",
        request_id="patch-request",
    )
    repository.assert_profile_owned(principal=principal, profile_id=profile_id)
    deleted = repository.delete_profile(
        principal=principal,
        profile_id=profile_id,
        idempotency_key="delete-key",
        request_id="delete-request",
    )

    assert patched.status_code == 200
    assert patched.body["revision_no"] == 2
    assert deleted.status_code == 202
    assert deleted.body["state"] == "DELETE_PENDING"
    assert profile.current_revision_no == 2
    assert profile.state == "DELETE_PENDING"
    assert session.scalar_index == 6
    assert len(session.added) == 3
    assert not session.transaction_active


def test_real_sqlalchemy_session_select_then_begin_rejects_active_transaction() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        with Session(engine) as session:
            assert session.scalar(text("SELECT 1")) == 1
            assert session.in_transaction()
            with pytest.raises(
                InvalidRequestError, match="A transaction is already begun"
            ):
                session.begin()
    finally:
        engine.dispose()


def test_same_delete_key_is_independent_between_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = VerifiedPrincipal("parent-1", "issuer-1", frozenset())
    first_id = uuid4()
    second_id = uuid4()
    profiles = {
        first_id: _DeleteProfile(first_id),
        second_id: _DeleteProfile(second_id),
    }
    receipts: dict[tuple[str, str, str, str, bytes], _DeleteReceipt] = {}
    locked_scopes: list[tuple[str, str, bytes]] = []
    repository = SqlParentProfileRepository(_TransactionOnlySession())  # type: ignore[arg-type]

    def lock_scope(
        _principal: VerifiedPrincipal,
        operation: str,
        resource_scope: str,
        key_hash: bytes,
    ) -> None:
        locked_scopes.append((operation, resource_scope, key_hash))

    def find_receipt(
        current_principal: VerifiedPrincipal,
        operation: str,
        resource_scope: str,
        key_hash: bytes,
    ) -> _DeleteReceipt | None:
        key = (
            current_principal.issuer,
            current_principal.subject,
            operation,
            resource_scope,
            key_hash,
        )
        return receipts.get(key)

    def owned_profile(
        _principal: VerifiedPrincipal,
        profile_id: UUID,
        *,
        lock: bool,
        include_pending: bool = False,
    ) -> _DeleteProfile:
        del lock, include_pending
        return profiles[profile_id]

    def store_receipt(
        current_principal: VerifiedPrincipal,
        operation: str,
        resource_scope: str,
        key_hash: bytes,
        fingerprint: bytes,
        _status_code: int,
        body: dict[str, object],
    ) -> None:
        key = (
            current_principal.issuer,
            current_principal.subject,
            operation,
            resource_scope,
            key_hash,
        )
        receipts[key] = _DeleteReceipt(fingerprint, 202, dict(body))

    monkeypatch.setattr(repository, "_lock_scope", lock_scope)
    monkeypatch.setattr(repository, "_find_receipt", find_receipt)
    monkeypatch.setattr(repository, "_owned_profile", owned_profile)
    monkeypatch.setattr(repository, "_store_receipt", store_receipt)

    first = repository.delete_profile(
        principal=principal,
        profile_id=first_id,
        idempotency_key="shared-delete-key",
        request_id="first-request",
    )
    second = repository.delete_profile(
        principal=principal,
        profile_id=second_id,
        idempotency_key="shared-delete-key",
        request_id="second-request",
    )

    assert first.status_code == second.status_code == 202
    assert profiles[first_id].state == profiles[second_id].state == "DELETE_PENDING"
    assert len(receipts) == 2
    assert locked_scopes[0][1] == str(first_id)
    assert locked_scopes[1][1] == str(second_id)
    assert first.body["profile_id"] == str(first_id)
    assert second.body["profile_id"] == str(second_id)

    replay = repository.delete_profile(
        principal=principal,
        profile_id=first_id,
        idempotency_key="shared-delete-key",
        request_id="replay-request",
    )
    assert replay == first
    assert len(receipts) == 2
