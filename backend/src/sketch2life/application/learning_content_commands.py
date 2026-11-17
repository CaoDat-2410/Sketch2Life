"""BE2-12 command orchestration; identity/source/review owner adapters are injected.

One transaction covers state, exact proof, history/outbox and scoped receipt.
The external owner guard is retained through commit, including duplicate recovery.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from pydantic import ValidationError

from sketch2life.application.learning_content_eligibility import (
    audience_hash,
    eligible_body,
    published_body,
    stored_body,
)
from sketch2life.application.ports.learning_content import (
    ContentAccess,
    ContentBoundary,
    ContentEvent,
    ContentReceipt,
    ContentStore,
    ContentTransaction,
)
from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewRecordV1,
    GenericLibraryContextV1,
    LibraryAudienceV1,
)
from sketch2life.contracts.schemas.learning_content import (
    ContentCommand,
    ContentCommandResult,
    ContentRecord,
    CreateContent,
    EditContent,
    PublicationReviewSet,
    PublishContent,
    RecordContentReview,
    RequestContentChanges,
    RetireContent,
    SubmitContent,
)
from sketch2life.domain.learning_content import model as domain
from sketch2life.domain.learning_content.model import (
    Capability,
    ContentError,
    ContentState,
    ContentVersion,
    ReviewProof,
    authorize,
    canonical_json,
    content_hash,
)


def command_capability(command: ContentCommand) -> Capability:
    if isinstance(command, (CreateContent, EditContent, SubmitContent)):
        return Capability.AUTHOR
    if isinstance(command, (RecordContentReview, RequestContentChanges)):
        if command.review.review_dimension == "safety":
            return Capability.REVIEW_SAFETY
        if command.review.review_dimension == "pedagogical":
            return Capability.REVIEW_PEDAGOGICAL
        raise ContentError("CONTENT_INVALID_REVIEW")
    if isinstance(command, PublishContent):
        return Capability.PUBLISH
    return Capability.RECALL


def record_view(content: ContentVersion) -> ContentRecord:
    publication = None
    if content.publication_policy_version is not None:
        if len(content.publication_review_ids) != 2:
            raise ContentError("CONTENT_REVIEW_REQUIRED")
        publication = PublicationReviewSet(
            safety_review_id=content.publication_review_ids[0],
            pedagogical_review_id=content.publication_review_ids[1],
            review_policy_version=content.publication_policy_version)
    return ContentRecord(
        record_id=content.record_id, organization_id=content.organization_id,
        version=content.version, revision=content.revision, hash=content.hash,
        state=content.state.value, authored_by=content.authored_by,
        created_at=content.created_at, context_revision=content.context_revision,
        review_revision=content.review_revision, publication_review_ref=publication,
        recalled_at=content.recalled_at, recall_reason=content.recall_reason)


def _scope(content: ContentVersion, organization_id: str, record_id: str,
           version: int | None = None) -> None:
    if (content.organization_id != organization_id or content.record_id != record_id
            or (version is not None and content.version != version)):
        raise ContentError("CONTENT_STORAGE_SCOPE_MISMATCH")


class ContentCommands:
    def __init__(self, store: ContentStore, boundary: ContentBoundary, *,
                 clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self.store = store
        self.boundary = boundary
        self.clock = clock

    def execute(self, principal_id: str, organization_id: str, command: ContentCommand, *,
                expected_revision: int | None = None) -> ContentCommandResult:
        if isinstance(command, CreateContent):
            if expected_revision is not None:
                raise ContentError("CONTENT_UNEXPECTED_PRECONDITION")
        elif type(expected_revision) is not int or expected_revision < 1:
            raise ContentError("CONTENT_PRECONDITION_REQUIRED")
        fingerprint = content_hash(canonical_json({
            "organization_id": organization_id, "principal_id": principal_id,
            "command": command.model_dump(mode="json"), "if_match": expected_revision,
        }))
        with self.boundary.guard(principal_id, organization_id) as access:
            if (access.authority.principal_id, access.authority.organization_id) != (
                principal_id, organization_id
            ):
                raise ContentError("CONTENT_INVALID_AUTHORITY")
            authorize(access.authority, organization_id, command_capability(command))
            try:
                with self.store.transaction() as tx:
                    return self._once(tx, access, command, expected_revision, fingerprint)
            except ContentError as error:
                if str(error) != "CONTENT_WRITE_CONFLICT":
                    raise
                # A concurrent identical create may lose the unique insert.
                # Rollback is complete before reading the winner. Never retry
                # arbitrary writes, or treat a different integrity error as success.
                with self.store.transaction() as tx:
                    receipt = tx.receipt(organization_id, principal_id, command.client_request_id)
                    if receipt is None:
                        raise error
                    return self._replay(tx, access, command, receipt, fingerprint)

    def _once(self, tx: ContentTransaction, access: ContentAccess, command: ContentCommand,
              expected: int | None, fingerprint: str) -> ContentCommandResult:
        actor = access.authority
        receipt = tx.receipt(actor.organization_id, actor.principal_id, command.client_request_id)
        if receipt is not None:
            return self._replay(tx, access, command, receipt, fingerprint)
        # Stable server IDs are scoped to principal/org/request, never caller IDs
        # and never an unscoped request key. All unique conflicts roll back.
        key = content_hash(canonical_json([
            actor.organization_id, actor.principal_id, command.client_request_id]))
        target: ContentVersion | None = None
        if not isinstance(command, CreateContent):
            head = tx.load(actor.organization_id, command.record_id, for_update=True)
            if head is None:
                raise ContentError("CONTENT_NOT_FOUND")
            _scope(head, actor.organization_id, command.record_id)
            # Recheck after the parent lock: a duplicate may have committed while
            # this request waited. Its original If-Match must not be reapplied.
            receipt = tx.receipt(actor.organization_id, actor.principal_id,
                                 command.client_request_id)
            if receipt is not None:
                return self._replay(tx, access, command, receipt, fingerprint)
            target = (head if command.target_version == head.version else tx.load(
                actor.organization_id, command.record_id, version=command.target_version,
                for_update=True))
            if target is None:
                raise ContentError("CONTENT_NOT_FOUND")
            _scope(target, actor.organization_id, command.record_id, command.target_version)
            authorize(actor, target.organization_id, command_capability(command),
                      authored_by=target.authored_by)
            if target.hash != command.target_hash:
                raise ContentError("CONTENT_HASH_MISMATCH")
            domain.check_revision(target, cast(int, expected))
            if target.version != head.version and not isinstance(command, RetireContent):
                raise ContentError("CONTENT_SUPERSEDED_VERSION")
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ContentError("CONTENT_INVALID_TIME")
        review_record = None
        if isinstance(command, CreateContent):
            updated = domain.create(
                "lc_" + key, actor, command.content.model_dump(mode="json"), now)
            eligible_body(updated, access, require_moderation=False)
        else:
            assert target is not None and expected is not None
            if isinstance(command, EditContent):
                updated = domain.edit(target, actor, command.content.model_dump(mode="json"), now,
                                      expected_revision=expected, next_version=target.version + 1)
                eligible_body(updated, access, require_moderation=False)
            elif isinstance(command, SubmitContent):
                eligible_body(target, access, require_moderation=False)
                updated = domain.submit(target, actor, expected_revision=expected)
            elif isinstance(command, (RecordContentReview, RequestContentChanges)):
                updated, review_record = self._review(target, access, command, expected, key, now)
            elif isinstance(command, PublishContent):
                body = stored_body(target)
                if command.review_ref.review_policy_version != access.policy.version:
                    raise ContentError("CONTENT_POLICY_DENIED")
                updated = domain.publish(
                    target, actor, expected_revision=expected,
                    safety_review_id=command.review_ref.safety_review_id,
                    pedagogical_review_id=command.review_ref.pedagogical_review_id,
                    policy_version=access.policy.version, audience_hash=audience_hash(body))
                published_body(updated, access)
            else:
                # Removal is allowed with current recall authority even when the
                # original source/policy is no longer eligible for publication.
                updated = domain.retire(target, actor, now, expected_revision=expected,
                                        reason=command.reason, archive=command.action == "archive")
        result = ContentCommandResult(
            record=record_view(updated), review_record=review_record,
            current_revision=updated.revision, current_state=updated.state.value)
        tx.save(updated, expected_revision=expected,
                event=ContentEvent("lce_" + key, "content." + command.action,
                                   actor.principal_id, now))
        tx.add_receipt(ContentReceipt(
            actor.organization_id, actor.principal_id, command.client_request_id,
            fingerprint, result.model_dump_json()))
        return result

    def _review(self, target: ContentVersion, access: ContentAccess,
                command: RecordContentReview | RequestContentChanges, expected: int,
                key: str, now: datetime) -> tuple[ContentVersion, ExactContentReviewRecordV1]:
        review = command.review
        body = (eligible_body(target, access) if review.decision == "approve"
                else stored_body(target))
        context, audience = review.review_context, review.audience_scope
        if (not isinstance(context, GenericLibraryContextV1)
                or not isinstance(audience, LibraryAudienceV1)
                or review.source_context_revision != target.context_revision
                or (context.content_kind, context.age_policy_ref, context.content_policy_ref) != (
                    body.content_kind, body.age_eligibility.age_policy_ref, body.content_policy_ref)
                or audience.age_policy_ref != body.age_eligibility.age_policy_ref
                or len(set(audience.purpose_codes)) != len(audience.purpose_codes)
                or set(audience.purpose_codes) != set(body.purpose_codes)):
            raise ContentError("CONTENT_REVIEW_MISMATCH")
        if not access.policy.version:
            raise ContentError("CONTENT_POLICY_DENIED")
        proof = ReviewProof(
            "lcr_" + key, cast(str, review.review_dimension), review.decision,
            target.record_id, target.version, target.hash, target.context_revision,
            audience_hash(body), access.authority.principal_id, access.policy.version,
            target.review_revision + 1, reason=review.reason)
        updated = domain.record_review(
            target, access.authority, proof, expected_revision=expected,
            expected_review_revision=cast(int, review.expected_review_revision))
        if access.review_effective(updated, proof) is not True:
            raise ContentError("CONTENT_REVIEW_INEFFECTIVE")
        record = ExactContentReviewRecordV1(
            review_id=proof.review_id, review_revision=proof.review_revision,
            reviewer_principal_id=proof.reviewer_id, reviewed_at=now,
            policy_version=proof.policy_version, state="effective")
        return updated, record

    def _replay(self, tx: ContentTransaction, access: ContentAccess, command: ContentCommand,
                receipt: ContentReceipt, fingerprint: str) -> ContentCommandResult:
        actor = access.authority
        if (receipt.organization_id, receipt.principal_id, receipt.request_id) != (
            actor.organization_id, actor.principal_id, command.client_request_id
        ):
            raise ContentError("CONTENT_RECEIPT_SCOPE_MISMATCH")
        if receipt.fingerprint != fingerprint:
            raise ContentError("CONTENT_COMMAND_CONFLICT")
        try:
            result = ContentCommandResult.model_validate_json(receipt.result_json)
        except ValidationError:
            raise ContentError("CONTENT_INVALID_RECEIPT") from None
        if not isinstance(command, CreateContent):
            result_version = command.target_version + int(isinstance(command, EditContent))
            if (result.record.record_id != command.record_id
                    or result.record.version != result_version):
                raise ContentError("CONTENT_INVALID_RECEIPT")
        if isinstance(command, (CreateContent, EditContent)):
            if result.record.hash != content_hash(canonical_json(
                command.content.model_dump(mode="json")
            )):
                raise ContentError("CONTENT_INVALID_RECEIPT")
        elif result.record.hash != command.target_hash:
            raise ContentError("CONTENT_INVALID_RECEIPT")
        head = tx.load(actor.organization_id, result.record.record_id)
        current = tx.load(actor.organization_id, result.record.record_id,
                          version=result.record.version)
        if current is None or head is None:
            raise ContentError("CONTENT_INVALID_RECEIPT")
        _scope(head, actor.organization_id, result.record.record_id)
        _scope(current, actor.organization_id, result.record.record_id, result.record.version)
        if (result.record.organization_id != actor.organization_id
                or result.record.hash != current.hash):
            raise ContentError("CONTENT_INVALID_RECEIPT")
        authorize(actor, current.organization_id, command_capability(command),
                  authored_by=current.authored_by)
        if isinstance(command, RetireContent):
            if current.state.value != result.record.state:
                raise ContentError("CONTENT_RECEIPT_INEFFECTIVE")
        else:
            if current.state in {ContentState.RECALLED, ContentState.ARCHIVED}:
                raise ContentError("CONTENT_RECEIPT_INEFFECTIVE")
            if current.version != head.version and current.state != ContentState.PUBLISHED:
                raise ContentError("CONTENT_SUPERSEDED_VERSION")
            if isinstance(command, PublishContent) or current.state == ContentState.PUBLISHED:
                published_body(current, access)
            elif isinstance(command, (RecordContentReview, RequestContentChanges)):
                if command.review.decision == "approve":
                    eligible_body(current, access)
            else:
                eligible_body(current, access, require_moderation=False)
            if isinstance(command, SubmitContent) and (
                current.context_revision != result.record.context_revision
            ):
                raise ContentError("CONTENT_RECEIPT_INEFFECTIVE")
            if isinstance(command, (RecordContentReview, RequestContentChanges)):
                record = result.review_record
                proofs = [p for p in current.reviews if record and p.review_id == record.review_id]
                if (len(proofs) != 1 or proofs[0].policy_version != access.policy.version
                        or proofs[0].context_revision != current.context_revision
                        or access.review_effective(current, proofs[0]) is not True):
                    raise ContentError("CONTENT_REVIEW_INEFFECTIVE")
                proof = proofs[0]
                assert record is not None
                if (proof.target_id, proof.target_version, proof.target_hash,
                    proof.context_revision, proof.reviewer_id, proof.review_revision,
                    proof.policy_version, proof.dimension, proof.decision, proof.reason,
                    proof.audience_hash, proof.state) != (
                        current.record_id, current.version, current.hash,
                        command.review.source_context_revision, record.reviewer_principal_id,
                        record.review_revision, record.policy_version,
                        command.review.review_dimension, command.review.decision,
                        command.review.reason, audience_hash(stored_body(current)), "effective"):
                    raise ContentError("CONTENT_REVIEW_MISMATCH")
        return result.model_copy(update={
            "replayed": True, "current_revision": current.revision,
            "current_state": current.state.value})
