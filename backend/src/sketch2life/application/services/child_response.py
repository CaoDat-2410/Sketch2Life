"""Offline CMD-36: exact viewer choice, immutable acknowledgement and local atomic commit."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import ValidationError

from sketch2life.application.ports.ai_jobs import ClockPort, IdGeneratorPort, Principal
from sketch2life.application.ports.child_response import (
    AuthorityPort,
    ChildResponseRepository,
    ChildResponseUnitOfWork,
    ReceiptKey,
    ResponseAudit,
    ResponseReceipt,
    ReviewAccessPort,
    RevisionConflict,
    UniqueConflict,
)
from sketch2life.contracts.schemas.child_responses import (
    CONTRACT_NAME,
    ChildResponseCommandV1,
    ChildResponseOutcomeV1,
    ChildResponseProjectionV1,
    ChildResponseReadV1,
    ReviewAccessSnapshotV1,
    TeacherResponseEventV1,
    TurnSnapshotV1,
    command_fingerprint,
)
from sketch2life.contracts.schemas.sketch_proposals import ChildResponseV1
from sketch2life.domain.child_response import (
    ResponseAction,
    ResponseEntry,
    ResponseTerminal,
    ViewerKey,
    ViewerState,
    transition,
    viewer_etag,
)

_OPAQUE = re.compile(r"[A-Za-z0-9_.:-]{1,120}")


class ChildResponseError(Exception):
    """Application reasons only; this checkpoint does not expose an HTTP route."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class ResponseCommand:
    principal: Principal
    proposal_id: str
    idempotency_key: str | None
    if_match: str | None
    body: ChildResponseCommandV1 | str | bytes


@dataclass(frozen=True, slots=True)
class ResponseResult:
    data: ChildResponseOutcomeV1
    replayed: bool


@dataclass(frozen=True, slots=True)
class ChildResponseDependencies:
    access: ReviewAccessPort
    authority: AuthorityPort
    repository: ChildResponseRepository
    clock: ClockPort
    ids: IdGeneratorPort


def _key(access: ReviewAccessSnapshotV1) -> ViewerKey:
    return ViewerKey(access.organization_id, access.participant_id,
                     access.proposal_id, access.proposal_version)


def _etag(access: ReviewAccessSnapshotV1, state: ViewerState) -> str:
    return viewer_etag(state.key, access.content_sha256, access.review_ref, state.revision)


def _response(entry: ResponseEntry) -> ChildResponseV1:
    return ChildResponseV1(action=entry.action.value, participant_id=entry.key.participant_id,
                           turn_id=entry.turn_id, responded_at=entry.responded_at)


class ChildResponseService:
    def __init__(self, deps: ChildResponseDependencies) -> None:
        self._d = deps

    def record_response(self, command: ResponseCommand) -> ResponseResult:
        body = self._parse(command.body)
        if (not isinstance(command.idempotency_key, str)
                or _OPAQUE.fullmatch(command.idempotency_key) is None
                or _OPAQUE.fullmatch(command.proposal_id) is None):
            raise ChildResponseError("FIELD_VALIDATION_FAILED")
        key = ReceiptKey(command.principal.organization_id, command.principal.principal_id,
                         CONTRACT_NAME, command.proposal_id, command.idempotency_key)
        fingerprint = command_fingerprint(command.proposal_id, body)
        with self._d.repository.transaction() as tx:
            receipt = tx.get_receipt(key)
        if receipt is not None:
            return self._replay(command.principal, receipt, fingerprint)

        access = self._authorized(command.principal, command.proposal_id,
                                  body.expected_proposal_version, body.review_ref)
        turn = self._d.authority.new_operation(command.principal, access, body.turn_id)
        if turn is None:
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        if command.if_match is None:
            raise ChildResponseError("PRECONDITION_REQUIRED")
        try:
            with self._d.repository.transaction() as tx:
                receipt = tx.get_receipt(key)
                if receipt is None:
                    outcome = self._commit(tx, command, body, key, fingerprint, access, turn)
                    return ResponseResult(outcome, False)
        except (RevisionConflict, UniqueConflict):
            # Another unit may have accepted this same operation, including a nested
            # fixture commit. Re-read after rollback and reauthorize its receipt first.
            with self._d.repository.transaction() as tx:
                receipt = tx.get_receipt(key)
            if receipt is None:
                raise ChildResponseError("STALE_AGGREGATE") from None
        return self._replay(command.principal, receipt, fingerprint)

    @staticmethod
    def _parse(body: ChildResponseCommandV1 | str | bytes) -> ChildResponseCommandV1:
        if isinstance(body, ChildResponseCommandV1):
            return body
        try:
            return ChildResponseCommandV1.model_validate_json(body, strict=True)
        except ValidationError as exc:
            code = ("FIELD_NOT_ALLOWED" if any(e["type"] == "extra_forbidden"
                                               for e in exc.errors())
                    else "FIELD_VALIDATION_FAILED")
            raise ChildResponseError(code) from None

    def _authorized(self, principal: Principal, proposal_id: str,
                    version: int | None, review_ref: str | None,
                    content_sha256: str | None = None) -> ReviewAccessSnapshotV1:
        access = self._d.access.authorize(
            principal, proposal_id, expected_proposal_version=version,
            review_ref=review_ref, content_sha256=content_sha256)
        if access is None or not self._d.authority.can_disclose(principal, access):
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        return access

    def _replay(self, principal: Principal, receipt: ResponseReceipt,
                fingerprint: str) -> ResponseResult:
        recorded = receipt.access
        current = self._authorized(principal, recorded.proposal_id, recorded.proposal_version,
                                   recorded.review_ref, recorded.content_sha256)
        if current != recorded:
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        if receipt.fingerprint != fingerprint:
            raise ChildResponseError("IDEMPOTENCY_PAYLOAD_MISMATCH")
        return ResponseResult(receipt.outcome, True)

    def _commit(self, tx: ChildResponseUnitOfWork, command: ResponseCommand,
                body: ChildResponseCommandV1, key: ReceiptKey, fingerprint: str,
                access: ReviewAccessSnapshotV1, turn: TurnSnapshotV1) -> ChildResponseOutcomeV1:
        viewer = _key(access)
        state = tx.get_state(viewer) or ViewerState(viewer)
        if command.if_match != _etag(access, state):
            raise ChildResponseError("STALE_AGGREGATE")
        if state.latest is not None and state.latest.content_sha256 != access.content_sha256:
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        action = ResponseAction(body.action)
        if tx.terminal_marker(viewer) is not None and action is not ResponseAction.DECLINED:
            raise ChildResponseError("RESPONSE_TERMINAL")
        try:
            applied = transition(state, action)
        except ResponseTerminal:
            raise ChildResponseError("RESPONSE_TERMINAL") from None
        now = self._d.clock.now()
        if applied:
            entry = ResponseEntry(
                response_id=self._d.ids.new_id("response"), operation_id=key.idempotency_key,
                key=viewer, response_revision=state.revision + 1,
                class_id=access.class_id, session_id=access.session_id,
                canvas_id=access.canvas_id, content_sha256=access.content_sha256,
                review_ref=access.review_ref, turn_id=turn.turn_id,
                turn_revision=turn.turn_revision, action=action, responded_at=now)
            updated = state.with_entry(entry)
            tx.save_state(expected_revision=state.revision, state=updated)
            tx.append_history(entry)
            if action is ResponseAction.DECLINED:
                tx.mark_terminal(viewer, entry.response_id)
            tx.add_event(TeacherResponseEventV1(
                event_id=self._d.ids.new_id("response_event"), response_id=entry.response_id,
                operation_key=key.idempotency_key, access=access,
                response_revision=updated.revision, turn_id=entry.turn_id,
                turn_revision=entry.turn_revision, action=entry.action.value,
                responded_at=entry.responded_at))
        else:
            assert state.latest is not None
            updated, entry = state, state.latest
        outcome = ChildResponseOutcomeV1(
            applied=applied, response_id=entry.response_id, response_revision=updated.revision,
            etag=_etag(access, updated), proposal_id=access.proposal_id,
            proposal_version=access.proposal_version, content_sha256=access.content_sha256,
            review_ref=access.review_ref, participant_id=access.participant_id,
            child_response=_response(entry))
        tx.put_receipt(ResponseReceipt(key, fingerprint, access, outcome))
        tx.add_audit(ResponseAudit(self._d.ids.new_id("response_audit"), key, access,
                                   turn.turn_id, action, entry.response_id, applied, now))
        return outcome

    def _projection(self, principal: Principal,
                    access: ReviewAccessSnapshotV1) -> ChildResponseProjectionV1:
        turn = self._d.authority.new_operation(principal, access, None)
        if turn is None:
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        with self._d.repository.transaction() as tx:
            state = tx.get_state(_key(access)) or ViewerState(_key(access))
        latest = state.latest
        if latest is not None and latest.content_sha256 != access.content_sha256:
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        return ChildResponseProjectionV1(
            access=access, visibility="available" if latest is None else latest.action.value,
            response_revision=state.revision, etag=_etag(access, state), turn_id=turn.turn_id,
            child_response=None if latest is None else _response(latest))

    def projection(self, principal: Principal, proposal_id: str, *,
                   expected_proposal_version: int | None = None,
                   review_ref: str | None = None) -> ChildResponseProjectionV1:
        access = self._authorized(principal, proposal_id, expected_proposal_version, review_ref)
        return self._projection(principal, access)

    def read(self, principal: Principal, proposal_id: str, *,
             expected_proposal_version: int | None = None, review_ref: str | None = None,
             explicit_reveal: bool = False) -> ChildResponseReadV1:
        allowed = self._d.access.read(
            principal, proposal_id, expected_proposal_version=expected_proposal_version,
            review_ref=review_ref)
        if allowed is None or not self._d.authority.can_disclose(principal, allowed.access):
            raise ChildResponseError("SKETCH_UNAVAILABLE")
        projection = self._projection(principal, allowed.access)
        suppressed = (projection.visibility == "declined"
                      or (projection.visibility == "hidden" and not explicit_reveal))
        return ChildResponseReadV1(projection=projection,
                                   payload=None if suppressed else allowed.payload)

    def teacher_events(self, principal: Principal) -> tuple[TeacherResponseEventV1, ...]:
        with self._d.repository.transaction() as tx:
            events = tx.events()
        return tuple(e for e in events if self._d.authority.teacher_allowed(principal, e.access))
