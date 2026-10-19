"""Strict13 delegate into sole12 CMD-48; own transaction/authority only."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from sketch2life.application.governance_dispatcher import StrictDelegateBinding
from sketch2life.application.ports.preset_automation import Authority, LocalReceipt, Store
from sketch2life.contracts.schemas.governance import DelegateRecord, DelegateResult
from sketch2life.contracts.schemas.learning_content import PublicationReviewSet
from sketch2life.contracts.schemas.preset_automation import PresetCommand
from sketch2life.domain.preset_automation.model import (
    Library,
    Review,
    State,
    Version,
    digest,
    fail,
    identifier,
)


def receipt_key(actor: str, key: str) -> str:
    identifier(actor)
    identifier(key)
    return "receipt-" + digest([actor, key])


class PresetGovernance:
    def __init__(
        self,
        store: Store,
        authority: Authority,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_id: Callable[[], str] = lambda: uuid4().hex,
    ) -> None:
        self.store, self.authority, self.clock, self.new_id = store, authority, clock, new_id

    def execute(
        self,
        principal_id: str,
        organization_id: str,
        command: PresetCommand,
        *,
        expected_revision: int | None,
    ) -> DelegateResult:
        command = PresetCommand.model_validate_json(command.model_dump_json())
        if command.action == "create":
            if expected_revision is not None:
                fail("UNEXPECTED_PRECONDITION")
        elif type(expected_revision) is not int or expected_revision < 1:
            fail("PRECONDITION_REQUIRED")
        fingerprint = digest([command.model_dump(mode="json"), expected_revision])
        rkey = receipt_key(principal_id, command.client_request_id)
        with self.authority.hold(organization_id, principal_id) as guard:
            guard.check(command.action)
            with self.store.transaction(organization_id, "library") as rows:
                receipt = rows.get(rkey)
                if receipt is not None:
                    if (
                        type(receipt) is not LocalReceipt
                        or receipt.fingerprint != fingerprint
                        or (receipt.actor, receipt.client_key)
                        != (principal_id, command.client_request_id)
                    ):
                        fail("IDEMPOTENCY_CONFLICT")
                    old_result = rows.history(receipt.object_key, receipt.applied_revision)
                    current = rows.get(receipt.object_key)
                    if type(old_result) is not Library or type(current) is not Library:
                        fail("STORAGE_CORRUPT")
                    guard.check_current()
                    return self._result(old_result, receipt.target_version, current, True)
                before = None
                if command.action == "create":
                    if command.body is None:
                        fail("INVALID_BODY")
                    body = command.body.domain()
                    guard.validate_body(body)
                    now = self.clock()
                    library = Library(
                        self.new_id(),
                        organization_id,
                        1,
                        (Version(1, body, State.DRAFT, principal_id, now),),
                        "create",
                        principal_id,
                        now,
                    )
                    target = 1
                else:
                    if (
                        command.record_id is None
                        or command.target_version is None
                        or command.target_hash is None
                    ):
                        fail("INVALID_TARGET")
                    before = rows.get(command.record_id)
                    if type(before) is not Library:
                        fail("NOT_FOUND")
                    before.target(command.target_version, command.target_hash)
                    edited_body = command.body.domain() if command.body else None
                    if edited_body is not None:
                        guard.validate_body(edited_body)
                    proof = None
                    if command.review is not None:
                        r = command.review
                        proof = Review(
                            r.review_id,
                            before.record_id,
                            command.target_version,
                            command.target_hash,
                            r.dimension,
                            principal_id,
                            r.policy_ref,
                            r.decision,
                            r.reason,
                        )
                        guard.review(before, proof)
                    refs = None
                    if command.review_ref is not None:
                        p = command.review_ref
                        refs = (
                            p.safety_review_id,
                            p.pedagogical_review_id,
                            p.review_policy_version,
                        )
                        guard.publication(before, command.target_version, refs)
                    library = before.change(
                        command.action,
                        cast(int, expected_revision),
                        command.target_version,
                        command.target_hash,
                        principal_id,
                        self.clock(),
                        body=edited_body,
                        review=proof,
                        publication=refs,
                        why=command.reason,
                    )
                    target = command.target_version + (command.action == "edit")
                guard.check_current()
                rows.put(library.record_id, before, library)
                rows.put(
                    rkey,
                    None,
                    LocalReceipt(
                        principal_id,
                        command.client_request_id,
                        fingerprint,
                        library.record_id,
                        library.revision,
                        target,
                    ),
                )
                guard.check_current()
            return self._result(library, target, library, False)

    @staticmethod
    def _result(snapshot: Library, target: int, current: Library, replayed: bool) -> DelegateResult:
        version = snapshot.versions[target - 1]
        refs = version.publication
        return DelegateResult(
            record=DelegateRecord(
                record_kind="preset",
                record_id=snapshot.record_id,
                organization_id=snapshot.organization_id,
                version=target,
                revision=snapshot.revision,
                hash=version.body.hash,
                state=version.state.value,
                authored_by=version.author,
                created_at=version.created_at,
                publication_review_ref=PublicationReviewSet(
                    safety_review_id=refs[0],
                    pedagogical_review_id=refs[1],
                    review_policy_version=refs[2],
                )
                if refs
                else None,
                recalled_at=version.recalled_at,
                recall_reason=version.recall_reason,
            ),
            replayed=replayed,
            current_revision=current.revision,
            current_state=current.versions[target - 1].state.value,
        )


def bind_preset(service: PresetGovernance) -> StrictDelegateBinding[PresetCommand]:
    return StrictDelegateBinding(PresetCommand, service)
