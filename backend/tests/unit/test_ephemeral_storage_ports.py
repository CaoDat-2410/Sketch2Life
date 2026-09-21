from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from sketch2life.application.ports.session_storage import IdempotencyReceipt, SessionRecord
from sketch2life.infrastructure.storage.in_memory import (
    IdempotencyConflict,
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemoryJobStore,
    InMemorySessionRepository,
    SessionVersionConflict,
)


@dataclass(frozen=True)
class Snapshot:
    value: str


def test_session_repository_supports_ephemeral_create_cas_expiry_and_delete() -> None:
    now = datetime.now(UTC)
    repository = InMemorySessionRepository[Snapshot]()
    initial = SessionRecord("session-1", 0, now + timedelta(minutes=30), Snapshot("created"))
    repository.create(initial)
    assert repository.get("session-1") == initial
    assert repository.get("session-1").owner_principal_key is None
    assert repository.expired_before(now) == ()

    updated = SessionRecord("session-1", 1, now + timedelta(minutes=30), Snapshot("ready"))
    repository.compare_and_swap(session_id="session-1", expected_version=0, record=updated)
    assert repository.get("session-1") == updated
    with pytest.raises(SessionVersionConflict):
        repository.compare_and_swap(session_id="session-1", expected_version=0, record=updated)
    assert repository.expired_before(now + timedelta(minutes=31)) == ("session-1",)
    assert repository.delete("session-1") is True
    assert repository.get("session-1") is None


def test_repository_owner_link_is_private_metadata_separate_from_snapshot() -> None:
    now = datetime.now(UTC)
    repository = InMemorySessionRepository[Snapshot]()
    linked = SessionRecord(
        "session-linked",
        0,
        now + timedelta(minutes=30),
        Snapshot("created"),
        owner_principal_key="firebase:verified-subject",
    )
    repository.create(linked)

    assert repository.get("session-linked") == linked
    assert "owner_principal_key" not in vars(linked.snapshot)


def test_artifact_store_keeps_opaque_refs_and_deletes_all_session_bytes() -> None:
    store = InMemoryArtifactStore()
    original = b"synthetic-test-image"
    stored = store.put(session_id="session-1", content_type="image/png", body=original)
    read_back = store.get(stored.artifact_ref)

    assert stored.artifact_ref.startswith("artifact:")
    assert stored.sha256 == sha256(original).hexdigest()
    assert read_back == (stored, original)
    assert store.delete_session("another-session") == 0
    assert store.delete_session("session-1") == 1
    assert store.get(stored.artifact_ref) is None


def test_job_store_is_replaceable_and_uses_compare_before_replace() -> None:
    store = InMemoryJobStore[str]()
    store.create("job-1", "QUEUED")
    store.replace("job-1", expected="QUEUED", updated="RUNNING")
    assert store.get("job-1") == "RUNNING"
    with pytest.raises(ValueError, match="changed"):
        store.replace("job-1", expected="QUEUED", updated="SUCCEEDED")


def test_idempotency_store_replays_same_fingerprint_and_rejects_key_conflict() -> None:
    store = InMemoryIdempotencyStore()
    receipt = IdempotencyReceipt(
        scope="session-1",
        key="retry-1",
        request_sha256="a" * 64,
        response_body=b'{"status":"ACCEPTED"}',
    )
    store.record(receipt)
    store.record(receipt)
    assert store.get(scope="session-1", key="retry-1") == receipt
    with pytest.raises(IdempotencyConflict):
        store.record(
            IdempotencyReceipt(
                scope="session-1",
                key="retry-1",
                request_sha256="b" * 64,
                response_body=b"{}",
            )
        )
