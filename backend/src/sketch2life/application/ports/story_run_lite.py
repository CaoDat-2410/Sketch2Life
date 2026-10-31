"""Ports owned by the StoryRun-lite application slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sketch2life.domain.story_run_lite import OwnerScopeKind


@dataclass(frozen=True, slots=True)
class ScanVerdict:
    decision: str
    sha256: str
    scanner_version: str | None
    scanned_at: datetime | None
    detail_code: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedImage:
    original_media_type: str
    original_sha256: str
    original_size_bytes: int
    width: int
    height: int
    derived_media_type: str
    derived_sha256: str
    derived_size_bytes: int
    derived_bytes: bytes
    worker_memory_limit_bytes: int
    worker_cpu_percent: int
    worker_deadline_seconds: int
    worker_peak_memory_bytes: int = 0
    worker_cpu_user_time_100ns: int = 0
    worker_cpu_kernel_time_100ns: int = 0
    worker_cpu_hard_cap_percent: int = 0
    worker_elapsed_ms: int = 0


@dataclass(frozen=True, slots=True)
class AssetBinding:
    asset_ref: str
    asset_version: int
    media_type: str
    sha256: str
    byte_size: int
    owner_scope_kind: OwnerScopeKind
    owner_scope_ref: str


@dataclass(frozen=True, slots=True)
class AdmittedAssetPair:
    original: AssetBinding
    derived: AssetBinding
    upload_session_id: str
    target_run_id: str


@dataclass(frozen=True, slots=True)
class CommandResult:
    status_code: int
    body: dict[str, object]
    resource_version: int | None = None
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class UploadReservation:
    command_result: CommandResult
    upload_id: str | None = None
    claim_version: int | None = None
    snapshot: bytes | None = None
    expected_sha256: str | None = None
    original_media_type: str | None = None
    actor_scope_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ValidatedVisionResult:
    result_snapshot: dict[str, object]
    subject_label: str
    confidence: float
    canonical_result_sha256: str
    raw_body_sha256: str | None


@dataclass(frozen=True, slots=True)
class VisionAttemptResult:
    state: str
    error_code: str | None = None
    provider_invoked: bool = False
    result_committed: bool = False


class ImageSafetyScannerPort(Protocol):
    def scan(self, snapshot: bytes, sha256: str) -> ScanVerdict: ...


class ImageNormalizerPort(Protocol):
    def normalize(
        self, snapshot: bytes, *, original_media_type: str, sha256: str
    ) -> NormalizedImage: ...


class StoryRunLiteVisionPort(Protocol):
    def analyze(
        self,
        *,
        run_id: str,
        binding: AssetBinding,
        persist_success: Callable[[ValidatedVisionResult], bool],
    ) -> VisionAttemptResult: ...


class StoryRunReferencePort(Protocol):
    def authorize_upload_target(
        self, *, actor_scope_kind: OwnerScopeKind, actor_scope_ref: str, run_id: str
    ) -> bool: ...


class CoreAssetAdmissionPort(Protocol):
    def resolve_story_artwork(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        asset_ref: str,
        run_id: str,
    ) -> AdmittedAssetPair: ...


class StoryRunLiteRepositoryPort(Protocol):
    def create_run(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        profile_ref: str,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult: ...

    def create_upload(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        media_type: str,
        expected_size_bytes: int,
        expected_sha256: str,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult: ...

    def put_part(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        part_number: int,
        payload: bytes,
        declared_length: int,
        declared_sha256: str,
    ) -> CommandResult: ...

    def get_upload(
        self, *, actor_scope_kind: OwnerScopeKind, actor_scope_ref: str, upload_id: str
    ) -> CommandResult: ...

    def abort_upload(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult: ...

    def attach_asset(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        pair: AdmittedAssetPair,
        expected_revision: int,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> tuple[CommandResult, str | None, int | None]: ...

    def get_run(
        self, *, actor_scope_kind: OwnerScopeKind, actor_scope_ref: str, run_id: str
    ) -> CommandResult: ...

    def confirm_subject(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        expected_version: int,
        expected_understanding_revision: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult: ...

    def cancel_run(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        expected_revision: int,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult: ...

    def finalize_attach_command(
        self, *, run_id: str, key_sha256: str, claimed_version: int
    ) -> CommandResult: ...

    def open_story_dispatch_gate(self, *, run_id: str, claimed_version: int) -> bool: ...

    def get_dispatch_context(self, *, run_id: str) -> dict[str, object]: ...

    def commit_vision_success(
        self,
        *,
        run_id: str,
        claimed_version: int,
        result_snapshot: dict[str, object],
        subject_label: str,
        confidence: float,
        canonical_result_sha256: str,
        raw_body_sha256: str | None,
    ) -> bool: ...

    def mark_vision_unknown(
        self, *, run_id: str, claimed_version: int, error_code: str
    ) -> bool: ...

    def mark_vision_failed_before_send(
        self, *, run_id: str, claimed_version: int, error_code: str
    ) -> bool: ...

    def pending_vision_ledger_reconciliation(self) -> list[dict[str, object]]: ...
    def read_asset(self, asset_ref: str) -> bytes: ...

    def reserve_complete_upload(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        expected_size_bytes: int,
        expected_sha256: str,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> UploadReservation: ...

    def finalize_complete_upload(
        self, reservation: UploadReservation, *, key_sha256: str
    ) -> CommandResult: ...

    def open_upload_gate(self, *, upload_id: str, claim_version: int) -> bool: ...

    def finish_upload_admission(
        self,
        *,
        upload_id: str,
        claim_version: int,
        original_asset_ref: str,
        derived_asset_ref: str,
        normalized: NormalizedImage,
        scanner: ScanVerdict,
        actor_scope_ref: str,
    ) -> bool: ...

    def fail_upload_admission(
        self, *, upload_id: str, claim_version: int, error_code: str
    ) -> bool: ...

    def store_asset(self, asset_ref: str, payload: bytes) -> str: ...
    def delete_asset(self, asset_ref: str) -> None: ...
    def remove_upload_quarantine(self, upload_id: str) -> bool:
        """Return whether cleanup succeeded, including when staging is already absent."""
        ...
