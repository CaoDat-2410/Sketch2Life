"""Fixture-first application policies for the core classroom handoffs.

These use cases coordinate domain rules and ports. Durable transaction semantics
are a requirement of a future adapter; the fixture runner only proves the port
contract with an in-memory implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from sketch2life.application.ports.core_foundation import (
    AggregateRevisionPort,
    CanvasMutationCommit,
    CoreMutationTransactionPort,
    IdempotencyReceiptPort,
)
from sketch2life.domain.core_foundation import (
    ActiveChildTurn,
    AdultRole,
    CanvasOperation,
    ConsentGrant,
    CoreErrorCode,
    CoreRuleViolation,
    CoreScope,
    DataLifecycleRequest,
    GalleryResource,
    IdempotencyReceipt,
    ManagedChildProfile,
    PortfolioEntry,
    SessionMembership,
    VerifiedPrincipal,
    authorize_action,
    is_idempotent_replay,
    require_admission_eligible,
    require_data_request_completion,
    require_effective_consent,
    require_expected_revision,
    require_gallery_access,
    require_group_binding,
    require_portfolio_access,
    validate_canvas_operation,
    visible_contributor_ids,
)


class CommandStatus(StrEnum):
    ACCEPTED = "accepted"
    REPLAYED = "replayed"


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    status: CommandStatus
    resulting_revision: int | None = None
    contributor_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()


class CoreFoundationApplication:
    """Application boundary for the isolated BE1-01 core rules."""

    @staticmethod
    def authorize(
        principal: VerifiedPrincipal,
        target: CoreScope,
        capability: str,
        allowed_roles: frozenset[AdultRole] = frozenset(),
        authoritative_scope: CoreScope | None = None,
    ) -> None:
        if authoritative_scope is not None and not target.is_within(authoritative_scope):
            raise CoreRuleViolation(
                CoreErrorCode.SCOPE_DENIED, "requested scope exceeds the loaded resource"
            )
        authorize_action(principal, target, capability, allowed_roles)

    @staticmethod
    def validate_profile_purpose(
        profile: ManagedChildProfile,
        consent: ConsentGrant,
        *,
        purpose: str,
        organization_id: str,
    ) -> None:
        if profile.organization_id != organization_id:
            raise CoreRuleViolation(
                CoreErrorCode.SCOPE_DENIED, "profile organization does not match"
            )
        require_effective_consent(profile, consent, purpose, organization_id)

    @staticmethod
    def admit_participant(
        *,
        principal: VerifiedPrincipal,
        target: CoreScope,
        profile: ManagedChildProfile,
        consent: ConsentGrant,
        membership: SessionMembership,
        purpose: str,
        session_open: bool,
    ) -> None:
        authorize_action(principal, target, "session.admit", frozenset({AdultRole.TEACHER}))
        if (
            profile.child_id != membership.child_id
            or profile.class_id != membership.class_id
            or profile.organization_id != membership.organization_id
            or membership.organization_id != target.organization_id
            or membership.session_id != target.session_id
            or (target.class_id is not None and membership.class_id != target.class_id)
        ):
            raise CoreRuleViolation(
                CoreErrorCode.SCOPE_DENIED, "profile and membership scope differ"
            )
        require_group_binding(membership, target)
        require_effective_consent(profile, consent, purpose, target.organization_id)
        require_admission_eligible(membership, session_open=session_open)

    @staticmethod
    def apply_canvas_operation(
        *,
        principal: VerifiedPrincipal,
        target: CoreScope,
        membership: SessionMembership,
        turn: ActiveChildTurn,
        operation: CanvasOperation,
        expected_revision: int,
        idempotency_scope: str,
        idempotency_key: str,
        request_fingerprint: str,
        revision_port: AggregateRevisionPort,
        receipt_port: IdempotencyReceiptPort,
        transaction_port: CoreMutationTransactionPort,
        operation_payload: dict[str, object] | None = None,
    ) -> CommandOutcome:
        authorize_action(principal, target, "canvas.write")
        validate_canvas_operation(principal, target, membership, turn, operation)
        previous = receipt_port.get_receipt(
            organization_id=target.organization_id,
            scope=idempotency_scope,
            key=idempotency_key,
        )
        if is_idempotent_replay(
            previous,
            key=idempotency_key,
            request_fingerprint=request_fingerprint,
        ):
            assert previous is not None
            return CommandOutcome(CommandStatus.REPLAYED, previous.resulting_revision)

        current_revision = revision_port.current_revision(
            operation.canvas_id, organization_id=target.organization_id
        )
        if current_revision is None:
            raise CoreRuleViolation(
                CoreErrorCode.STALE_AGGREGATE, "canvas aggregate is unavailable"
            )
        require_expected_revision(expected_revision, current_revision)
        next_revision = current_revision + 1
        receipt = IdempotencyReceipt(
            scope=idempotency_scope,
            key=idempotency_key,
            request_fingerprint=request_fingerprint,
            resulting_revision=next_revision,
            operation_id=operation.operation_id,
        )
        committed = transaction_port.commit_canvas_mutation(
            CanvasMutationCommit(
                aggregate_id=operation.canvas_id,
                expected_revision=current_revision,
                next_revision=next_revision,
                organization_id=target.organization_id,
                actor_id=principal.principal_id,
                operation=operation,
                receipt=receipt,
                outbox_event_id=str(uuid4()),
                operation_payload=operation_payload or {},
            )
        )
        if not committed:
            raise CoreRuleViolation(
                CoreErrorCode.STALE_AGGREGATE, "canvas revision changed during commit"
            )
        return CommandOutcome(CommandStatus.ACCEPTED, next_revision)

    @staticmethod
    def read_gallery(
        *,
        principal: VerifiedPrincipal,
        requested_scope: CoreScope,
        resource: GalleryResource,
    ) -> CommandOutcome:
        require_gallery_access(principal, requested_scope, resource)
        return CommandOutcome(
            CommandStatus.ACCEPTED,
            contributor_ids=visible_contributor_ids(resource),
        )

    @staticmethod
    def read_portfolio(
        *,
        principal: VerifiedPrincipal,
        target: CoreScope,
        entry: PortfolioEntry,
    ) -> CommandOutcome:
        source_refs = require_portfolio_access(principal, target, entry)
        return CommandOutcome(CommandStatus.ACCEPTED, source_refs=source_refs)

    @staticmethod
    def complete_data_request(
        *, principal: VerifiedPrincipal, target: CoreScope, request: DataLifecycleRequest
    ) -> CommandOutcome:
        authorize_action(principal, target, "data_request.complete")
        if request.organization_id != target.organization_id:
            raise CoreRuleViolation(
                CoreErrorCode.SCOPE_DENIED,
                "data request organization does not match the authorized scope",
            )
        require_data_request_completion(request)
        return CommandOutcome(CommandStatus.ACCEPTED)


__all__ = ["CommandOutcome", "CommandStatus", "CoreFoundationApplication"]
