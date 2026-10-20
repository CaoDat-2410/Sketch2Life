"""BE2-14 commands: lifecycle, exact reviews, scoped receipt and atomic effective pin."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import cast

from pydantic import ValidationError

from sketch2life.application.ai_policy_compatibility import bind_definitions
from sketch2life.application.ports.ai_policy import (
    PolicyEvent,
    PolicyReceipt,
    PolicyStore,
    PolicyTransaction,
    ScopeTransition,
)
from sketch2life.application.ports.ai_policy_registry import (
    PolicyCommandAccess,
    PolicyCommandBoundary,
)
from sketch2life.contracts.schemas.ai_policy import AiPolicyCommand, AiPolicyWrite
from sketch2life.contracts.schemas.governance import DelegateRecord, DelegateResult
from sketch2life.contracts.schemas.learning_content import PublicationReviewSet
from sketch2life.domain.ai_policy import model as domain
from sketch2life.domain.ai_policy.model import Capability, PolicyError, PolicyVersion


def _digest(value: object) -> str:
    return hashlib.sha256(domain.canonical_json(value).encode("utf-8")).hexdigest()


def _body(record: PolicyVersion) -> AiPolicyWrite:
    if hashlib.sha256(record.body_json.encode("utf-8")).hexdigest() != record.hash:
        raise PolicyError("AI_POLICY_HASH_MISMATCH")
    try:
        return AiPolicyWrite.model_validate_json(record.body_json)
    except ValidationError:
        raise PolicyError("AI_POLICY_INVALID_BODY") from None


def _capability(command: AiPolicyCommand) -> Capability:
    if command.action in {"create", "edit", "submit_review"}:
        return Capability.AUTHOR
    if command.review is not None:
        return (
            Capability.REVIEW_SAFETY
            if command.review.dimension == "safety"
            else Capability.REVIEW_PEDAGOGICAL
        )
    return Capability.PUBLISH if command.action == "publish" else Capability.DISABLE


def _requires_definitions(command: AiPolicyCommand) -> bool:
    return command.action in {"create", "edit", "submit_review", "publish"} or (
        command.review is not None and command.review.decision == "approve"
    )


def _view(record: PolicyVersion) -> DelegateResult:
    publication = None
    if record.publication_policy_version is not None:
        if len(record.publication_review_ids) != 2:
            raise PolicyError("AI_POLICY_REVIEW_REQUIRED")
        publication = PublicationReviewSet(
            safety_review_id=record.publication_review_ids[0],
            pedagogical_review_id=record.publication_review_ids[1],
            review_policy_version=record.publication_policy_version,
        )
    return DelegateResult(
        record=DelegateRecord(
            record_kind="policy",
            policy_kind="ai",
            record_id=record.record_id,
            organization_id=record.organization_id,
            version=record.version,
            revision=record.revision,
            hash=record.hash,
            state=record.state.value,
            authored_by=record.authored_by,
            created_at=record.created_at,
            publication_review_ref=publication,
            recalled_at=record.recalled_at,
            recall_reason=record.recall_reason,
        ),
        current_revision=record.revision,
        current_state=record.state.value,
    )


def _proofs_current(record: PolicyVersion, access: PolicyCommandAccess) -> None:
    if (
        not access.review_policy_version
        or len(record.reviews) != 2
        or any(
            proof.policy_version != access.review_policy_version
            or access.review_effective(record, proof) is not True
            for proof in record.reviews
        )
    ):
        raise PolicyError("AI_POLICY_REVIEW_INEFFECTIVE")


class AiPolicyCommands:
    def __init__(
        self,
        store: PolicyStore,
        boundary: PolicyCommandBoundary,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary = store, boundary
        self.clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self,
        principal_id: str,
        organization_id: str,
        command: AiPolicyCommand,
        *,
        expected_revision: int | None = None,
    ) -> DelegateResult:
        try:
            command = AiPolicyCommand.model_validate(command.model_dump(mode="python"), strict=True)
        except (ValidationError, ValueError, TypeError):
            raise PolicyError("AI_POLICY_INVALID_COMMAND") from None
        if command.action == "create":
            if expected_revision is not None:
                raise PolicyError("AI_POLICY_UNEXPECTED_PRECONDITION")
        elif type(expected_revision) is not int or expected_revision < 1:
            raise PolicyError("AI_POLICY_PRECONDITION_REQUIRED")
        fingerprint = _digest(
            dict(
                principal_id=principal_id,
                organization_id=organization_id,
                command=command.model_dump(mode="json"),
                expected_revision=expected_revision,
            )
        )
        identity = _digest([organization_id, principal_id, command.client_request_id])
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                if access.authority.principal_id != principal_id:
                    raise PolicyError("AI_POLICY_FORBIDDEN")
                domain.authorize(access.authority, organization_id, _capability(command))
                try:
                    with self.store.transaction() as tx:
                        result = self._execute(
                            tx,
                            access,
                            command,
                            organization_id,
                            expected_revision,
                            fingerprint,
                            identity,
                        )
                except PolicyError as error:
                    if str(error) != "AI_POLICY_WRITE_CONFLICT":
                        raise
                    # Unique conflict rolls back first; only a fresh receipt read,
                    # never repeat the write against a changed snapshot.
                    with self.store.transaction() as tx:
                        receipt = tx.receipt(
                            organization_id, principal_id, command.client_request_id
                        )
                        if receipt is None:
                            raise error
                        result = self._replay(tx, access, command, receipt, fingerprint, identity)
            return result  # Both SQL commit and outer guard exit completed.
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_DEPENDENCY_UNAVAILABLE") from None

    def _execute(
        self,
        tx: PolicyTransaction,
        access: PolicyCommandAccess,
        command: AiPolicyCommand,
        organization_id: str,
        expected: int | None,
        fingerprint: str,
        identity: str,
    ) -> DelegateResult:
        actor = access.authority
        receipt = tx.receipt(organization_id, actor.principal_id, command.client_request_id)
        if receipt is not None:
            return self._replay(tx, access, command, receipt, fingerprint, identity)
        feature = (
            command.policy.feature_scope
            if command.policy is not None
            else tx.feature_scope(organization_id, cast(str, command.record_id))
        )
        if feature is None:
            raise PolicyError("AI_POLICY_NOT_FOUND")
        scope = tx.effective_scope(organization_id, feature, for_update=True)
        if scope is None or (scope.organization_id, scope.feature_scope) != (
            organization_id,
            feature,
        ):
            raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
        # Same org/feature contenders serialized; receipt may now exist.
        receipt = tx.receipt(organization_id, actor.principal_id, command.client_request_id)
        if receipt is not None:
            return self._replay(tx, access, command, receipt, fingerprint, identity)
        now = self.clock()
        if now.utcoffset() is None:
            raise PolicyError("AI_POLICY_INVALID_TIME")
        original = None
        if command.action != "create":
            original = tx.load(
                organization_id,
                cast(str, command.record_id),
                version=command.target_version,
                for_update=True,
            )
            if original is None:
                raise PolicyError("AI_POLICY_NOT_FOUND")
            if (original.organization_id, original.record_id, original.version, original.hash) != (
                organization_id,
                command.record_id,
                command.target_version,
                command.target_hash,
            ):
                raise PolicyError("AI_POLICY_HASH_MISMATCH")
            domain.check_revision(original, cast(int, expected))
            head = tx.load(organization_id, original.record_id, for_update=True)
            if head is None:
                raise PolicyError("AI_POLICY_NOT_FOUND")
            if command.action not in {"recall", "archive"} and head.version != original.version:
                raise PolicyError("AI_POLICY_SUPERSEDED_VERSION")
            if _body(original).feature_scope != feature:
                raise PolicyError("AI_POLICY_FEATURE_CHANGE_DENIED")
            domain.authorize(actor, organization_id, _capability(command), original.authored_by)
        body = (
            command.policy if command.policy is not None else _body(cast(PolicyVersion, original))
        )
        if _requires_definitions(command):
            bind_definitions(body, organization_id, access)
        if command.action == "create":
            updated = domain.create("ap-" + identity, actor, body.model_dump(mode="json"), now)
        elif command.action == "edit":
            record = cast(PolicyVersion, original)
            updated = domain.edit(
                record,
                actor,
                body.model_dump(mode="json"),
                now,
                expected_revision=cast(int, expected),
                next_version=record.version + 1,
            )
        elif command.action == "submit_review":
            updated = domain.submit(
                cast(PolicyVersion, original), actor, expected_revision=cast(int, expected)
            )
        elif command.action in {"record_review", "request_changes"}:
            record = cast(PolicyVersion, original)
            review = command.review
            if review is None or review.review_policy_version != access.review_policy_version:
                raise PolicyError("AI_POLICY_REVIEW_MISMATCH")
            proposed = domain.Review(
                "review-" + identity,
                record.record_id,
                record.version,
                record.hash,
                review.context_revision,
                review.expected_review_revision + 1,
                review.dimension,
                review.decision,
                actor.principal_id,
                review.review_policy_version,
                review.reason,
            )
            updated = domain.record_review(
                record,
                actor,
                proposed,
                expected_revision=cast(int, expected),
                expected_review_revision=review.expected_review_revision,
            )
            if (
                review.decision == "approve"
                and access.review_effective(updated, proposed) is not True
            ):
                raise PolicyError("AI_POLICY_REVIEW_INEFFECTIVE")
        elif command.action == "publish":
            record = cast(PolicyVersion, original)
            refs = command.review_ref
            if refs is None or refs.review_policy_version != access.review_policy_version:
                raise PolicyError("AI_POLICY_REVIEW_MISMATCH")
            _proofs_current(record, access)
            updated = domain.publish(
                record,
                actor,
                expected_revision=cast(int, expected),
                safety_review_id=refs.safety_review_id,
                pedagogical_review_id=refs.pedagogical_review_id,
                current_review_policy=access.review_policy_version,
            )
        else:
            updated = domain.retire(
                cast(PolicyVersion, original),
                actor,
                now,
                expected_revision=cast(int, expected),
                archive=command.action == "archive",
                reason=cast(str, command.reason),
            )
        tx.save(
            updated,
            expected_revision=expected,
            event=PolicyEvent(
                "event-" + identity, "ai_policy." + command.action, actor.principal_id, now
            ),
        )
        if command.action == "publish":
            tx.save_scope(
                replace(
                    scope,
                    epoch=scope.epoch + 1,
                    record_id=updated.record_id,
                    version=updated.version,
                    hash=updated.hash,
                    disabled=False,
                ),
                expected_epoch=scope.epoch,
                event=ScopeTransition("scope-" + identity, actor.principal_id, now, None),
            )
        elif command.action in {"recall", "archive"} and (
            scope.record_id,
            scope.version,
            scope.hash,
        ) == (updated.record_id, updated.version, updated.hash):
            tx.save_scope(
                replace(scope, epoch=scope.epoch + 1, disabled=True),
                expected_epoch=scope.epoch,
                event=ScopeTransition("scope-" + identity, actor.principal_id, now, command.reason),
            )
        result = _view(updated)
        tx.add_receipt(
            PolicyReceipt(
                organization_id,
                actor.principal_id,
                command.client_request_id,
                fingerprint,
                result.model_dump_json(),
            )
        )
        return result

    def _replay(
        self,
        tx: PolicyTransaction,
        access: PolicyCommandAccess,
        command: AiPolicyCommand,
        receipt: PolicyReceipt,
        fingerprint: str,
        identity: str,
    ) -> DelegateResult:
        if receipt.fingerprint != fingerprint:
            raise PolicyError("AI_POLICY_COMMAND_CONFLICT")
        if (receipt.organization_id, receipt.principal_id, receipt.request_id) != (
            access.authority.organization_id,
            access.authority.principal_id,
            command.client_request_id,
        ):
            raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
        result = DelegateResult.model_validate_json(receipt.result_json)
        organization_id = access.authority.organization_id
        if result.record.organization_id != organization_id or result.record.policy_kind != "ai":
            raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
        feature = tx.feature_scope(organization_id, result.record.record_id)
        if feature is None:
            raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
        scope = tx.effective_scope(organization_id, feature, for_update=True)
        current = tx.load(
            organization_id, result.record.record_id, version=result.record.version, for_update=True
        )
        if current is None or current.hash != result.record.hash or scope is None:
            raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
        if (current.organization_id, current.record_id, current.version) != (
            organization_id,
            result.record.record_id,
            result.record.version,
        ) or (scope.organization_id, scope.feature_scope) != (organization_id, feature):
            raise PolicyError("AI_POLICY_SCOPE_MISMATCH")
        domain.authorize(
            access.authority, organization_id, _capability(command), current.authored_by
        )
        if command.action not in {"recall", "archive"} and current.state in {
            domain.State.RECALLED,
            domain.State.ARCHIVED,
        }:
            raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
        if _requires_definitions(command):
            bind_definitions(_body(current), organization_id, access)
        if command.review is not None:
            proof = next((p for p in current.reviews if p.review_id == "review-" + identity), None)
            if proof is None or proof.policy_version != access.review_policy_version:
                raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
            if proof.decision == "approve" and access.review_effective(current, proof) is not True:
                raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
        if command.action == "publish":
            if current.state != domain.State.PUBLISHED or scope.disabled:
                raise PolicyError("AI_POLICY_RECEIPT_INEFFECTIVE")
            _proofs_current(current, access)
        return result.model_copy(
            update=dict(
                replayed=True, current_revision=current.revision, current_state=current.state.value
            )
        )
