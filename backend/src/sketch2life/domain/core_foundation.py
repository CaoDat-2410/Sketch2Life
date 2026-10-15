"""Framework-independent rules for the collaborative classroom foundation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CoreErrorCode(StrEnum):
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


class PrincipalKind(StrEnum):
    ADULT = "adult"
    ADMITTED_DEVICE = "admitted_device"
    PENDING_DEVICE = "pending_device"
    BACKEND_WORKER = "backend_worker"


class AdultRole(StrEnum):
    TEACHER = "teacher"
    SCHOOL_ADMIN = "school_admin"
    SUPER_ADMIN = "super_admin"


class PrincipalSource(StrEnum):
    IDENTITY_PORT = "identity_port"
    CALLER_PAYLOAD = "caller_payload"


class ConsentState(StrEnum):
    PENDING_VERIFICATION = "pending_verification"
    EFFECTIVE = "effective"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REJECTED = "rejected"


class MembershipState(StrEnum):
    PENDING = "pending"
    ADMITTED = "admitted"
    DENIED = "denied"
    LEFT = "left"
    REMOVED = "removed"
    EXPIRED = "expired"


class DataRequestState(StrEnum):
    RECEIVED = "received"
    IDENTITY_CHECK = "identity_check"
    SCOPE_REVIEW = "scope_review"
    APPROVED = "approved"
    RUNNING = "running"
    AWAITING_EXTERNAL_PURGE = "awaiting_external_purge"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CoreRuleViolation(ValueError):
    """A domain rejection with a stable, transport-independent error code."""

    def __init__(self, code: CoreErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class CoreScope:
    organization_id: str
    class_id: str | None = None
    session_id: str | None = None
    group_id: str | None = None
    child_id: str | None = None
    canvas_id: str | None = None
    artifact_id: str | None = None

    def is_within(self, allowed: CoreScope) -> bool:
        """Return whether this requested scope is no broader than ``allowed``."""

        if self.organization_id != allowed.organization_id:
            return False
        for name in ("class_id", "session_id", "group_id", "child_id", "canvas_id", "artifact_id"):
            requested_value = getattr(self, name)
            allowed_value = getattr(allowed, name)
            if allowed_value is not None and requested_value != allowed_value:
                return False
            if allowed_value is not None and requested_value is None:
                return False
        return True


@dataclass(frozen=True, slots=True)
class VerifiedPrincipal:
    principal_id: str
    kind: PrincipalKind
    organization_id: str
    source: PrincipalSource
    verified: bool
    role: AdultRole | None
    capabilities: frozenset[str]
    authorized_scope: CoreScope
    device_id: str | None = None


def authorize_action(
    principal: VerifiedPrincipal,
    target: CoreScope,
    capability: str,
    allowed_roles: frozenset[AdultRole] = frozenset(),
) -> None:
    """Require an identity-port principal with capability and matching resource scope."""

    if not principal.verified or principal.source is not PrincipalSource.IDENTITY_PORT:
        raise CoreRuleViolation(
            CoreErrorCode.FORGED_PRINCIPAL,
            "principal must come from the verified identity port",
        )
    if principal.kind is PrincipalKind.PENDING_DEVICE and capability not in {
        "join.status",
        "join.submit_pending",
    }:
        raise CoreRuleViolation(
            CoreErrorCode.PENDING_PRINCIPAL_RESTRICTED,
            "pending devices may only access their own pending join flow",
        )
    if principal.organization_id != target.organization_id:
        raise CoreRuleViolation(CoreErrorCode.SCOPE_DENIED, "organization scope does not match")
    if not target.is_within(principal.authorized_scope):
        raise CoreRuleViolation(CoreErrorCode.SCOPE_DENIED, "resource is outside the granted scope")
    if allowed_roles and principal.role not in allowed_roles:
        raise CoreRuleViolation(
            CoreErrorCode.FORBIDDEN_ROLE, "principal role cannot perform this action"
        )
    if capability not in principal.capabilities:
        raise CoreRuleViolation(CoreErrorCode.FORBIDDEN_ROLE, "required capability is not granted")


def validate_age_months(age_months: int) -> None:
    """Validate the owner-confirmed 36–155 completed-month product boundary."""

    if isinstance(age_months, bool) or not isinstance(age_months, int):
        raise CoreRuleViolation(CoreErrorCode.AGE_OUT_OF_RANGE, "age must be completed months")
    if not 36 <= age_months <= 155:
        raise CoreRuleViolation(CoreErrorCode.AGE_OUT_OF_RANGE, "age is outside 36–155 months")


@dataclass(frozen=True, slots=True)
class ManagedChildProfile:
    child_id: str
    organization_id: str
    class_id: str
    age_months: int

    def __post_init__(self) -> None:
        validate_age_months(self.age_months)


@dataclass(frozen=True, slots=True)
class ConsentGrant:
    child_id: str
    organization_id: str
    state: ConsentState
    verification_state: str
    effective_purposes: frozenset[str]


def require_effective_consent(
    profile: ManagedChildProfile,
    grant: ConsentGrant,
    purpose: str,
    organization_id: str,
) -> None:
    if grant.child_id != profile.child_id or grant.organization_id != organization_id:
        raise CoreRuleViolation(
            CoreErrorCode.SCOPE_DENIED, "consent does not match child or organization"
        )
    if (
        grant.state is not ConsentState.EFFECTIVE
        or grant.verification_state != "verified"
        or purpose not in grant.effective_purposes
    ):
        raise CoreRuleViolation(
            CoreErrorCode.CONSENT_NOT_EFFECTIVE,
            "the requested purpose has no verified effective consent",
        )


@dataclass(frozen=True, slots=True)
class SessionMembership:
    participant_id: str
    child_id: str
    organization_id: str
    class_id: str
    session_id: str
    state: MembershipState
    group_id: str | None = None
    allowed_canvas_ids: frozenset[str] = frozenset()


def require_admitted_membership(
    membership: SessionMembership,
    *,
    child_id: str,
    organization_id: str,
    session_id: str,
) -> None:
    if (
        membership.state is not MembershipState.ADMITTED
        or membership.child_id != child_id
        or membership.organization_id != organization_id
        or membership.session_id != session_id
    ):
        raise CoreRuleViolation(
            CoreErrorCode.ADMISSION_REQUIRED,
            "an admitted membership in this session is required",
        )


def require_admission_eligible(membership: SessionMembership, *, session_open: bool) -> None:
    if not session_open or membership.state is not MembershipState.PENDING:
        raise CoreRuleViolation(
            CoreErrorCode.ADMISSION_REQUIRED,
            "only a pending participant in an open session can be admitted",
        )


def require_group_binding(membership: SessionMembership, target: CoreScope) -> None:
    if target.group_id is not None and membership.group_id != target.group_id:
        raise CoreRuleViolation(
            CoreErrorCode.SCOPE_DENIED,
            "participant group binding does not match the command scope",
        )


@dataclass(frozen=True, slots=True)
class ActiveChildTurn:
    turn_id: str
    device_id: str
    organization_id: str
    session_id: str
    canvas_id: str
    participant_id: str
    state: str
    revision: int
    document_epoch: int = 1


@dataclass(frozen=True, slots=True)
class CanvasOperation:
    operation_id: str
    turn_id: str
    participant_id: str
    session_id: str
    canvas_id: str
    document_epoch: int


def validate_canvas_operation(
    principal: VerifiedPrincipal,
    target: CoreScope,
    membership: SessionMembership,
    turn: ActiveChildTurn,
    operation: CanvasOperation,
) -> None:
    if principal.kind is not PrincipalKind.ADMITTED_DEVICE or not principal.device_id:
        raise CoreRuleViolation(
            CoreErrorCode.FORBIDDEN_ROLE, "canvas writes require an admitted device"
        )
    if (
        target.organization_id != turn.organization_id
        or target.session_id != turn.session_id
        or target.canvas_id != turn.canvas_id
        or (target.class_id is not None and target.class_id != membership.class_id)
        or (target.group_id is not None and target.group_id != membership.group_id)
        or (target.child_id is not None and target.child_id != membership.child_id)
    ):
        raise CoreRuleViolation(
            CoreErrorCode.SCOPE_DENIED,
            "canvas command scope does not match the loaded turn and membership",
        )
    if turn.state != "active" or turn.device_id != principal.device_id:
        raise CoreRuleViolation(
            CoreErrorCode.INVALID_TURN, "active turn is not bound to this device"
        )
    if (
        operation.turn_id != turn.turn_id
        or operation.participant_id != turn.participant_id
        or operation.session_id != turn.session_id
        or operation.canvas_id != turn.canvas_id
        or operation.document_epoch != turn.document_epoch
        or principal.organization_id != turn.organization_id
        or membership.organization_id != turn.organization_id
        or operation.session_id != membership.session_id
        or operation.participant_id != membership.participant_id
        or operation.canvas_id not in membership.allowed_canvas_ids
        or membership.state is not MembershipState.ADMITTED
    ):
        raise CoreRuleViolation(
            CoreErrorCode.INVALID_TURN,
            "operation does not match the admitted participant's active turn and canvas grant",
        )


def require_expected_revision(expected_revision: int, current_revision: int) -> None:
    if expected_revision < 1 or current_revision < 1 or expected_revision != current_revision:
        raise CoreRuleViolation(
            CoreErrorCode.STALE_AGGREGATE,
            "expected aggregate revision is stale",
        )


@dataclass(frozen=True, slots=True)
class IdempotencyReceipt:
    scope: str
    key: str
    request_fingerprint: str
    resulting_revision: int
    operation_id: str


def is_idempotent_replay(
    receipt: IdempotencyReceipt | None,
    *,
    key: str,
    request_fingerprint: str,
) -> bool:
    if receipt is None:
        return False
    if receipt.key != key or receipt.request_fingerprint != request_fingerprint:
        raise CoreRuleViolation(
            CoreErrorCode.IDEMPOTENCY_CONFLICT,
            "idempotency key is already bound to a different request",
        )
    return True


@dataclass(frozen=True, slots=True)
class GalleryResource:
    artifact_id: str
    organization_id: str
    published: bool
    audience_scope: CoreScope
    contributor_ids: tuple[str, ...]


def require_gallery_access(
    principal: VerifiedPrincipal,
    requested_scope: CoreScope,
    resource: GalleryResource,
) -> None:
    authorize_action(principal, requested_scope, "gallery.read")
    if (
        not resource.published
        or resource.organization_id != requested_scope.organization_id
        or requested_scope.artifact_id != resource.artifact_id
        or not requested_scope.is_within(resource.audience_scope)
    ):
        raise CoreRuleViolation(
            CoreErrorCode.GALLERY_AUDIENCE_DENIED,
            "gallery item is not available to the requested audience",
        )


def visible_contributor_ids(resource: GalleryResource) -> tuple[str, ...]:
    """Return only explicit contribution references; never infer all group members."""

    return tuple(dict.fromkeys(resource.contributor_ids))


@dataclass(frozen=True, slots=True)
class PortfolioEntry:
    entry_id: str
    organization_id: str
    child_id: str
    source_refs: tuple[str, ...]
    contribution_child_ids: tuple[str, ...]


def require_portfolio_access(
    principal: VerifiedPrincipal,
    target: CoreScope,
    entry: PortfolioEntry,
) -> tuple[str, ...]:
    """Return source links for this child's entry without copying shared source media."""

    authorize_action(principal, target, "portfolio.read")
    if (
        target.organization_id != entry.organization_id
        or target.child_id != entry.child_id
        or entry.child_id not in entry.contribution_child_ids
    ):
        raise CoreRuleViolation(
            CoreErrorCode.GALLERY_AUDIENCE_DENIED,
            "portfolio entry is outside the child's authorized contribution scope",
        )
    return tuple(dict.fromkeys(entry.source_refs))


@dataclass(frozen=True, slots=True)
class DataLifecycleRequest:
    request_id: str
    organization_id: str
    state: DataRequestState
    unresolved_items: int


def require_data_request_completion(request: DataLifecycleRequest) -> None:
    if request.state not in {DataRequestState.RUNNING, DataRequestState.AWAITING_EXTERNAL_PURGE}:
        raise CoreRuleViolation(
            CoreErrorCode.DATA_REQUEST_INCOMPLETE,
            "data request is not in a completion-eligible state",
        )
    if request.unresolved_items != 0:
        raise CoreRuleViolation(
            CoreErrorCode.DATA_REQUEST_INCOMPLETE,
            "unresolved copies or exceptions prevent a completed disposition",
        )


__all__ = [
    "ActiveChildTurn",
    "AdultRole",
    "CanvasOperation",
    "ConsentGrant",
    "ConsentState",
    "CoreErrorCode",
    "CoreRuleViolation",
    "CoreScope",
    "DataLifecycleRequest",
    "DataRequestState",
    "GalleryResource",
    "IdempotencyReceipt",
    "ManagedChildProfile",
    "MembershipState",
    "PortfolioEntry",
    "PrincipalKind",
    "PrincipalSource",
    "SessionMembership",
    "VerifiedPrincipal",
    "authorize_action",
    "is_idempotent_replay",
    "require_admission_eligible",
    "require_admitted_membership",
    "require_data_request_completion",
    "require_effective_consent",
    "require_expected_revision",
    "require_gallery_access",
    "require_group_binding",
    "require_portfolio_access",
    "validate_age_months",
    "validate_canvas_operation",
    "visible_contributor_ids",
]
