"""Closed v1 candidate schemas for the BE1-01 core handoff fixtures.

These are fixture/domain-boundary contracts only. They do not freeze REST,
database, queue, or generated mobile interfaces from SRS B21–B22.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CORE_COMMAND_IDENTITY = "Sketch2Life.ResolvedCoreCommandV1@1.0"
CORE_FIXTURE_IDENTITY = "Sketch2Life.CoreFoundationFixtureV1@1.0"
CORE_MANIFEST_IDENTITY = "Sketch2Life.CoreFoundationManifestV1@1.0"

OpaqueId = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
Fingerprint = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


SourceStatusV1 = Literal[
    "OWNER_CONFIRMED",
    "CONFIRMED",
    "PROPOSED",
    "PROPOSED_UNADOPTED",
    "TBD",
    "REPO_CONSTRAINT",
]


class AdultRoleV1(StrEnum):
    TEACHER = "teacher"
    SCHOOL_ADMIN = "school_admin"
    SUPER_ADMIN = "super_admin"


class PrincipalKindV1(StrEnum):
    ADULT = "adult"
    ADMITTED_DEVICE = "admitted_device"
    PENDING_DEVICE = "pending_device"
    BACKEND_WORKER = "backend_worker"


class CoreFailureCodeV1(StrEnum):
    FORGED_PRINCIPAL = "FORGED_PRINCIPAL"
    FORBIDDEN_ROLE = "FORBIDDEN_ROLE"
    PENDING_PRINCIPAL_RESTRICTED = "PENDING_PRINCIPAL_RESTRICTED"
    SCOPE_DENIED = "SCOPE_DENIED"
    CONSENT_NOT_EFFECTIVE = "CONSENT_NOT_EFFECTIVE"
    AGE_OUT_OF_RANGE = "AGE_OUT_OF_RANGE"
    ADMISSION_REQUIRED = "ADMISSION_REQUIRED"
    INVALID_TURN = "INVALID_TURN"
    STALE_AGGREGATE = "STALE_AGGREGATE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    GALLERY_AUDIENCE_DENIED = "GALLERY_AUDIENCE_DENIED"
    DATA_REQUEST_INCOMPLETE = "DATA_REQUEST_INCOMPLETE"


class CoreScopeV1(StrictFrozenModel):
    organization_id: OpaqueId
    class_id: OpaqueId | None = None
    session_id: OpaqueId | None = None
    group_id: OpaqueId | None = None
    child_id: OpaqueId | None = None
    canvas_id: OpaqueId | None = None
    artifact_id: OpaqueId | None = None


class PrincipalContextV1(StrictFrozenModel):
    """Server-resolved context; never a public client command body."""

    principal_id: OpaqueId
    kind: PrincipalKindV1
    role: AdultRoleV1 | None = None
    role_source: Literal["identity_port", "caller_payload"]
    verified: bool
    authorized_scope: CoreScopeV1
    capabilities: tuple[str, ...] = ()
    device_id: OpaqueId | None = None

    @model_validator(mode="after")
    def _unique_capabilities(self) -> PrincipalContextV1:
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("capabilities must be unique")
        return self


class AuthorizationPayloadV1(StrictFrozenModel):
    kind: Literal["authorization"]
    required_capability: str = Field(min_length=1, max_length=96)
    allowed_roles: tuple[AdultRoleV1, ...] = ()


class ProfileConsentPayloadV1(StrictFrozenModel):
    kind: Literal["profile_consent"]
    child_id: OpaqueId
    purpose: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")


class SessionAdmissionPayloadV1(StrictFrozenModel):
    kind: Literal["session_admission"]
    child_id: OpaqueId
    purpose: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    target_group_id: OpaqueId | None = None


class TurnCanvasPayloadV1(StrictFrozenModel):
    kind: Literal["turn_canvas"]
    operation_id: OpaqueId
    turn_id: OpaqueId
    participant_id: OpaqueId
    document_epoch: int = Field(ge=1)
    expected_document_revision: int = Field(ge=1)
    request_fingerprint: Fingerprint


class GalleryPortfolioPayloadV1(StrictFrozenModel):
    kind: Literal["gallery_portfolio"]
    view_kind: Literal["gallery", "portfolio"] = "gallery"
    requested_scope: CoreScopeV1
    child_id: OpaqueId | None = None


class DataLifecyclePayloadV1(StrictFrozenModel):
    kind: Literal["data_lifecycle"]
    action: Literal["complete"]
    request_id: OpaqueId
    request_kind: Literal["export", "delete"]


CorePayloadV1 = Annotated[
    AuthorizationPayloadV1
    | ProfileConsentPayloadV1
    | SessionAdmissionPayloadV1
    | TurnCanvasPayloadV1
    | GalleryPortfolioPayloadV1
    | DataLifecyclePayloadV1,
    Field(discriminator="kind"),
]


class CoreCommandEnvelopeV1(StrictFrozenModel):
    contract_name: Literal["ResolvedCoreCommandV1"] = "ResolvedCoreCommandV1"
    contract_version: Literal["1.0"] = "1.0"
    command_id: OpaqueId
    action: str = Field(min_length=1, max_length=96, pattern=r"^[a-z][a-z0-9_.]*$")
    actor: PrincipalContextV1
    scope: CoreScopeV1
    expected_revision: int | None = Field(default=None, ge=1)
    idempotency_key: OpaqueId | None = None
    payload: CorePayloadV1


class AuthorizationStateV1(StrictFrozenModel):
    kind: Literal["authorization"]
    resource_scope: CoreScopeV1
    resource_revision: int = Field(ge=1)


class ProfileConsentStateV1(StrictFrozenModel):
    kind: Literal["profile_consent"]
    profile_child_id: OpaqueId
    profile_organization_id: OpaqueId
    profile_class_id: OpaqueId
    age_months: int = Field(ge=0)
    consent_state: Literal["pending_verification", "effective", "revoked", "expired", "rejected"]
    verification_state: Literal["pending", "verified", "rejected"]
    effective_purposes: tuple[str, ...] = ()


class SessionAdmissionStateV1(StrictFrozenModel):
    kind: Literal["session_admission"]
    profile_child_id: OpaqueId
    profile_organization_id: OpaqueId
    profile_class_id: OpaqueId
    age_months: int = Field(ge=0)
    consent_state: Literal["pending_verification", "effective", "revoked", "expired", "rejected"]
    verification_state: Literal["pending", "verified", "rejected"]
    effective_purposes: tuple[str, ...] = ()
    participant_id: OpaqueId
    membership_state: Literal["pending", "admitted", "denied", "left", "removed", "expired"]
    membership_session_id: OpaqueId
    membership_class_id: OpaqueId
    membership_group_id: OpaqueId | None = None
    session_open: bool


class TurnCanvasStateV1(StrictFrozenModel):
    kind: Literal["turn_canvas"]
    membership_state: Literal["pending", "admitted", "denied", "left", "removed", "expired"]
    membership_participant_id: OpaqueId
    membership_child_id: OpaqueId
    membership_session_id: OpaqueId
    allowed_canvas_ids: tuple[OpaqueId, ...]
    active_turn_id: OpaqueId
    active_turn_state: Literal["active", "closed", "revoked"]
    turn_device_id: OpaqueId
    turn_session_id: OpaqueId
    turn_canvas_id: OpaqueId
    turn_participant_id: OpaqueId
    turn_revision: int = Field(ge=1)
    current_document_revision: int = Field(ge=1)
    stored_request_fingerprint: Fingerprint | None = None
    stored_resulting_revision: int | None = Field(default=None, ge=1)
    stored_operation_id: OpaqueId | None = None


class GalleryPortfolioStateV1(StrictFrozenModel):
    kind: Literal["gallery_portfolio"]
    artifact_id: OpaqueId
    artifact_organization_id: OpaqueId
    published: bool
    audience_scope: CoreScopeV1
    contributor_ids: tuple[OpaqueId, ...] = ()
    portfolio_entry_id: OpaqueId | None = None
    portfolio_child_id: OpaqueId | None = None
    portfolio_source_refs: tuple[OpaqueId, ...] = ()
    portfolio_contribution_child_ids: tuple[OpaqueId, ...] = ()


class DataLifecycleStateV1(StrictFrozenModel):
    kind: Literal["data_lifecycle"]
    request_state: Literal[
        "received",
        "identity_check",
        "scope_review",
        "approved",
        "running",
        "awaiting_external_purge",
        "completed",
        "partially_completed",
        "rejected",
        "failed",
        "cancelled",
    ]
    unresolved_items: int = Field(ge=0)


CoreStateV1 = Annotated[
    AuthorizationStateV1
    | ProfileConsentStateV1
    | SessionAdmissionStateV1
    | TurnCanvasStateV1
    | GalleryPortfolioStateV1
    | DataLifecycleStateV1,
    Field(discriminator="kind"),
]


class CoreExpectedResultV1(StrictFrozenModel):
    status: Literal["accepted", "replayed", "rejected"]
    failure_code: CoreFailureCodeV1 | None = None
    resulting_revision: int | None = Field(default=None, ge=1)
    contributor_ids: tuple[OpaqueId, ...] = ()
    source_refs: tuple[OpaqueId, ...] = ()
    mutates_state: bool

    @model_validator(mode="after")
    def _result_is_coherent(self) -> CoreExpectedResultV1:
        if self.status == "rejected" and self.failure_code is None:
            raise ValueError("rejected fixture requires a typed failure code")
        if self.status != "rejected" and self.failure_code is not None:
            raise ValueError("accepted/replayed fixture cannot carry a failure code")
        if self.status == "rejected" and self.mutates_state:
            raise ValueError("rejected fixture must not mutate state")
        return self


class CoreFoundationFixtureV1(StrictFrozenModel):
    contract_name: Literal["CoreFoundationFixtureV1"] = "CoreFoundationFixtureV1"
    contract_version: Literal["1.0"] = "1.0"
    contract_status: Literal["PROPOSED_UNADOPTED"]
    fixture_id: OpaqueId
    owner: Literal["P2/BE1"] = "P2/BE1"
    source_refs: tuple[str, ...] = Field(min_length=1)
    source_status_labels: tuple[SourceStatusV1, ...] = Field(min_length=1)
    synthetic_only: Literal[True] = True
    command: CoreCommandEnvelopeV1
    state: CoreStateV1
    expected_result: CoreExpectedResultV1

    @model_validator(mode="after")
    def _handoff_types_match(self) -> CoreFoundationFixtureV1:
        if self.command.payload.kind != self.state.kind:
            raise ValueError("command payload and state handoff kinds must match")
        return self


class FixtureManifestEntryV1(StrictFrozenModel):
    fixture_id: OpaqueId
    path: str = Field(min_length=1, pattern=r"^[a-z0-9-]+\.json$")
    index: int = Field(ge=0)
    contract_status: Literal["PROPOSED_UNADOPTED"]
    source_status_labels: tuple[SourceStatusV1, ...] = Field(min_length=1)
    kind: Literal[
        "authorization",
        "profile_consent",
        "session_admission",
        "turn_canvas",
        "gallery_portfolio",
        "data_lifecycle",
    ]
    expected_status: Literal["accepted", "replayed", "rejected"]
    expected_failure_code: CoreFailureCodeV1 | None = None


class InvalidContractProbeV1(StrictFrozenModel):
    probe_id: OpaqueId
    source_fixture_id: OpaqueId
    mutation: Literal["undeclared_command_field"]
    expected_failure_code: Literal["FIELD_NOT_ALLOWED"]


class CoreFoundationManifestV1(StrictFrozenModel):
    contract_name: Literal["CoreFoundationManifestV1"] = "CoreFoundationManifestV1"
    contract_version: Literal["1.0"] = "1.0"
    contract_status: Literal["PROPOSED_UNADOPTED"]
    manifest_id: OpaqueId
    owner: Literal["P2/BE1"] = "P2/BE1"
    source_refs: tuple[str, ...] = Field(min_length=1)
    source_status_labels: tuple[SourceStatusV1, ...] = Field(min_length=1)
    data_policy: Literal["SYNTHETIC_ONLY"] = "SYNTHETIC_ONLY"
    entries: tuple[FixtureManifestEntryV1, ...] = Field(min_length=1)
    invalid_contract_probes: tuple[InvalidContractProbeV1, ...] = ()

    @model_validator(mode="after")
    def _unique_fixture_ids(self) -> CoreFoundationManifestV1:
        ids = [entry.fixture_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("fixture IDs must be unique")
        positions = [(entry.path, entry.index) for entry in self.entries]
        if len(positions) != len(set(positions)):
            raise ValueError("manifest fixture positions must be unique")
        probe_ids = [probe.probe_id for probe in self.invalid_contract_probes]
        if len(probe_ids) != len(set(probe_ids)):
            raise ValueError("probe IDs must be unique")
        entry_statuses = {status for entry in self.entries for status in entry.source_status_labels}
        if entry_statuses != set(self.source_status_labels):
            raise ValueError("manifest source-status labels must match its fixture entries")
        return self


class CoreFixturePackV1(StrictFrozenModel):
    contract_name: Literal["CoreFixturePackV1"] = "CoreFixturePackV1"
    contract_version: Literal["1.0"] = "1.0"
    synthetic_only: Literal[True] = True
    cases: tuple[CoreFoundationFixtureV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_case_ids(self) -> CoreFixturePackV1:
        ids = [case.fixture_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("fixture case IDs must be unique")
        return self


__all__ = [
    "CORE_COMMAND_IDENTITY",
    "CORE_FIXTURE_IDENTITY",
    "CORE_MANIFEST_IDENTITY",
    "CoreCommandEnvelopeV1",
    "CoreFailureCodeV1",
    "CoreFixturePackV1",
    "CoreFoundationFixtureV1",
    "CoreFoundationManifestV1",
]
