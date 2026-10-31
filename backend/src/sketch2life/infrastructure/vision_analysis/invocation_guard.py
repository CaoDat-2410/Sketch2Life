"""Durable single-use guard for one provider invocation attempt."""

from __future__ import annotations

import re
from contextlib import suppress
from uuid import UUID

from sketch2life.application.ports.vision_analysis import (
    InvocationGuardState,
    InvocationResponseMetadata,
    InvocationTerminalState,
    ObservationFailed,
    ObservationFailureCode,
    ObservationOutcome,
    ObservationRequest,
    ObservationSucceeded,
    VisionObservationPort,
)
from sketch2life.domain.vision_analysis import EvidenceKind, ProviderContextMode
from sketch2life.domain.vision_context import ContextCapability
from sketch2life.infrastructure.vision_analysis.ledger import InvocationLedger, InvocationState

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class InvocationLedgerGuard:
    """Bind one server-issued run to one job attempt and one durable ledger row."""

    def __init__(
        self,
        *,
        ledger: InvocationLedger,
        run_id: str,
        job_id: str,
        attempt_id: str,
        organization_id: str,
    ) -> None:
        self._ledger = ledger
        self.run_id = run_id
        self.job_id = job_id
        self.attempt_id = attempt_id
        self.organization_id = organization_id
        self._state = InvocationGuardState.NEW
        self._response = InvocationResponseMetadata()

    @property
    def state(self) -> InvocationGuardState:
        return self._state

    @property
    def response_metadata(self) -> InvocationResponseMetadata:
        return self._response

    def claim(self) -> ObservationFailureCode | None:
        if self._state is not InvocationGuardState.NEW:
            return ObservationFailureCode.NOT_SENT_RUN_ALREADY_USED
        try:
            UUID(self.run_id)
            if not all((self.job_id, self.attempt_id, self.organization_id)):
                raise ValueError("invocation identity is incomplete")
            claimed = self._ledger.claim(
                run_id=self.run_id,
                job_id=self.job_id,
                attempt_id=self.attempt_id,
                organization_id=self.organization_id,
            )
        except Exception:
            self._state = InvocationGuardState.REFUSED
            return ObservationFailureCode.NOT_SENT_GUARD_REFUSED
        if claimed:
            self._state = InvocationGuardState.CLAIMED
            return None

        try:
            previous = self._ledger.get(self.run_id)
        except Exception:
            self._state = InvocationGuardState.PRIOR_OUTCOME_UNKNOWN
            return ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
        if previous is None or previous.state in {InvocationState.SENT, InvocationState.UNKNOWN}:
            self._state = InvocationGuardState.PRIOR_OUTCOME_UNKNOWN
            return ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN
        self._state = InvocationGuardState.USED
        return ObservationFailureCode.NOT_SENT_RUN_ALREADY_USED

    def mark_sent(self) -> ObservationFailureCode | None:
        if self._state is not InvocationGuardState.CLAIMED:
            self._state = InvocationGuardState.REFUSED
            return ObservationFailureCode.NOT_SENT_GUARD_REFUSED
        try:
            marked = self._ledger.mark_sent(
                run_id=self.run_id,
                job_id=self.job_id,
                attempt_id=self.attempt_id,
                organization_id=self.organization_id,
            )
        except Exception:
            marked = False
        if not marked:
            self._state = InvocationGuardState.REFUSED
            return ObservationFailureCode.NOT_SENT_GUARD_REFUSED
        self._state = InvocationGuardState.SENT
        return None

    def record_response(
        self,
        *,
        status_code: int | None,
        body_sha256: str | None,
        body_complete: bool,
        json_object: bool,
        within_deadline: bool,
    ) -> None:
        safe_hash = body_sha256 if body_sha256 is None or _SHA256.fullmatch(body_sha256) else None
        self._response = InvocationResponseMetadata(
            status_code=status_code,
            body_sha256=safe_hash,
            body_complete=body_complete,
            json_object=json_object,
            within_deadline=within_deadline,
            bridge_validated=self._response.bridge_validated,
        )

    def mark_bridge_outcome_validated(self) -> None:
        metadata = self._response
        if (
            self._state is InvocationGuardState.SENT
            and metadata.status_code == 200
            and metadata.body_complete
            and metadata.json_object
            and metadata.within_deadline
        ):
            self._response = InvocationResponseMetadata(
                status_code=metadata.status_code,
                body_sha256=metadata.body_sha256,
                body_complete=metadata.body_complete,
                json_object=metadata.json_object,
                within_deadline=metadata.within_deadline,
                bridge_validated=True,
            )

    def finalize(
        self,
        state: InvocationTerminalState,
        result_sha256: str | None = None,
    ) -> bool:
        if self._state is not InvocationGuardState.SENT:
            return False
        result_sha256 = result_sha256 or self._response.body_sha256
        try:
            completed = self._ledger.complete(
                run_id=self.run_id,
                job_id=self.job_id,
                attempt_id=self.attempt_id,
                organization_id=self.organization_id,
                state=state.value,
                result_sha256=result_sha256,
            )
        except Exception:
            completed = False
        if completed:
            self._state = InvocationGuardState(state.value)
            return True

        if state is not InvocationTerminalState.UNKNOWN:
            # Keep the local result UNKNOWN even if this best-effort ledger write is unavailable.
            with suppress(Exception):
                self._ledger.complete(
                    run_id=self.run_id,
                    job_id=self.job_id,
                    attempt_id=self.attempt_id,
                    organization_id=self.organization_id,
                    state=InvocationState.UNKNOWN.value,
                    result_sha256=result_sha256,
                )
        self._state = InvocationGuardState.UNKNOWN
        return False


class InvocationGuardedVisionObservationPort:
    """Apply terminal V2 classification only after the transport and bridge both validate."""

    def __init__(self, inner: VisionObservationPort, guard: InvocationLedgerGuard) -> None:
        if not self._uses_guard(inner, guard):
            raise ValueError("bridge and transport must use the same invocation guard")
        self._inner = inner
        self._guard = guard

    @staticmethod
    def _uses_guard(inner: VisionObservationPort, guard: InvocationLedgerGuard) -> bool:
        try:
            return getattr(inner, "invocation_guard_identity", None) is guard
        except Exception:
            return False

    @property
    def supported_context_modes(self) -> frozenset[ProviderContextMode]:
        return self._inner.supported_context_modes

    @property
    def context_capability(self) -> ContextCapability | None:
        return self._inner.context_capability

    def observe(self, request: ObservationRequest) -> ObservationOutcome:
        if not self._uses_guard(self._inner, self._guard):
            state = self._guard.state
            if state is InvocationGuardState.SENT:
                return self._unknown()
            if state in {InvocationGuardState.UNKNOWN, InvocationGuardState.PRIOR_OUTCOME_UNKNOWN}:
                return ObservationFailed(ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN, True)
            return ObservationFailed(ObservationFailureCode.NOT_SENT_GUARD_REFUSED, False)

        try:
            outcome = self._inner.observe(request)
        except Exception:
            if self._guard.state is InvocationGuardState.SENT:
                return self._unknown()
            if self._guard.state is InvocationGuardState.PRIOR_OUTCOME_UNKNOWN:
                return ObservationFailed(ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN, True)
            if self._guard.state is InvocationGuardState.REFUSED:
                return ObservationFailed(ObservationFailureCode.NOT_SENT_GUARD_REFUSED, False)
            if self._guard.state is InvocationGuardState.NEW:
                raise RuntimeError("bound vision bridge raised before guard claim") from None
            return ObservationFailed(ObservationFailureCode.PROVIDER_ERROR, False)

        state = self._guard.state
        if state is InvocationGuardState.NEW:
            if isinstance(outcome, ObservationFailed) and not outcome.provider_invoked:
                return outcome
            raise RuntimeError("bound vision bridge returned an outcome before guard claim")
        if state is InvocationGuardState.REFUSED:
            return ObservationFailed(ObservationFailureCode.NOT_SENT_GUARD_REFUSED, False)
        if state is InvocationGuardState.USED:
            return ObservationFailed(ObservationFailureCode.NOT_SENT_RUN_ALREADY_USED, False)
        if state is InvocationGuardState.PRIOR_OUTCOME_UNKNOWN:
            return ObservationFailed(ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN, True)
        if state is InvocationGuardState.CLAIMED:
            if isinstance(outcome, ObservationFailed):
                return ObservationFailed(outcome.code, False, detail=outcome.detail)
            return ObservationFailed(ObservationFailureCode.PROVIDER_ERROR, False)

        metadata = self._guard.response_metadata
        if not (
            state is InvocationGuardState.SENT
            and metadata.status_code == 200
            and metadata.body_complete
            and metadata.json_object
            and metadata.within_deadline
            and metadata.bridge_validated
        ):
            return self._unknown()

        if isinstance(outcome, ObservationSucceeded):
            if not self._guard.finalize(InvocationTerminalState.SUCCEEDED, metadata.body_sha256):
                return self._unknown()
            evidence = outcome.evidence
            live_evidence = evidence.__class__(
                evidence_kind=EvidenceKind.LIVE_LEGACY_BRIDGE,
                provider_context_mode=evidence.provider_context_mode,
                adapter_id=evidence.adapter_id,
                result_contract=evidence.result_contract,
                result_sha256=evidence.result_sha256,
                executed_at=evidence.executed_at,
                transport_attempts=evidence.transport_attempts,
                profile_id=evidence.profile_id,
                profile_catalog_hash=evidence.profile_catalog_hash,
                config_hash=evidence.config_hash,
                adapter_version=evidence.adapter_version,
                model_identifier=evidence.model_identifier,
                model_revision=evidence.model_revision,
                content_policy_version=evidence.content_policy_version,
                policy_match_view_version=evidence.policy_match_view_version,
                context_binding=evidence.context_binding,
            )
            return ObservationSucceeded(
                outcome.observation, live_evidence, outcome.moderation, outcome.result_document
            )

        if not self._guard.finalize(InvocationTerminalState.FAILED, metadata.body_sha256):
            return self._unknown()
        return ObservationFailed(
            outcome.code,
            provider_invoked=True,
            retryable=outcome.retryable,
            detail=outcome.detail,
        )

    def _unknown(self) -> ObservationFailed:
        metadata = self._guard.response_metadata
        self._guard.finalize(InvocationTerminalState.UNKNOWN, metadata.body_sha256)
        return ObservationFailed(
            ObservationFailureCode.PROVIDER_OUTCOME_UNKNOWN,
            provider_invoked=True,
            retryable=False,
            detail="POST_SEND_OUTCOME_AMBIGUOUS",
        )


__all__ = ["InvocationGuardedVisionObservationPort", "InvocationLedgerGuard"]
