"""Offline, fail-closed adapter from trusted BE1 facts to narrow BE2 context contracts.

The injected source is the future persistence boundary. This module deliberately performs no
database, network, provider or runtime work and does not import the BE1 HTTP layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.vision_analysis import ContextDecision
from sketch2life.domain.assistance import AssistanceRuleViolation, MemberFact
from sketch2life.domain.core_foundation import CoreRuleViolation, validate_age_months
from sketch2life.domain.eligibility import (
    EligibilityBasis,
    EligibilityFacts,
    EligibilityScope,
    ProvisionalDataOrigin,
    SyntheticEligibilityProof,
    evaluate_eligibility,
)
from sketch2life.domain.vision_analysis import ProviderContextMode
from sketch2life.infrastructure.assistance.context_revision import (
    CONTEXT_REVISION_SCHEMA_VERSION,
    context_digest,
    context_revision,
)


@dataclass(frozen=True, slots=True)
class BE1SyntheticProofFact:
    """Persistence-neutral projection of the server-owned synthetic proof row."""

    evidence_id: str
    schema_version: str
    data_origin: str
    scope: EligibilityScope
    run_ref: str
    session_id: str | None
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revocation_revision: int


@dataclass(frozen=True, slots=True)
class BE1FactSnapshot:
    """One current, server-read fact snapshot for exactly one BE1 session participant."""

    organization_id: str
    class_id: str
    session_id: str
    session_state: str
    session_run_ref: str | None
    environment: str
    pilot_enabled: bool
    purpose_ref: str
    child_id: str
    profile_origin: ProvisionalDataOrigin | str | None
    profile_state: str
    age_months: int | None
    age_revision: int | None
    age_source: str | None
    consent_record_ref: str | None
    consent_revision: int | None
    consent_state: str | None
    legal_consent_effective: bool | None
    purpose_granted: bool
    membership_state: str
    group_id: str | None
    proof: BE1SyntheticProofFact | None
    evaluated_at: datetime


@dataclass(frozen=True, slots=True)
class BE1FactRequest:
    organization_id: str
    class_id: str
    session_id: str
    child_id: str
    purpose_ref: str
    audience_participant_ids: tuple[str, ...]
    context_mode: ProviderContextMode


class BE1FactSource(Protocol):
    """Injected read-only owner source; an implementation must honor the exact requested scope."""

    def current_facts(self, request: BE1FactRequest) -> BE1FactSnapshot | None: ...


class FactReaderReason(StrEnum):
    ALLOWED = "ALLOWED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    AUDIENCE_UNSUPPORTED = "AUDIENCE_UNSUPPORTED"
    CONTEXT_MODE_UNSUPPORTED = "CONTEXT_MODE_UNSUPPORTED"
    PROFILE_INACTIVE = "PROFILE_INACTIVE"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    MEMBERSHIP_NOT_ADMITTED = "MEMBERSHIP_NOT_ADMITTED"
    FACTS_INVALID = "FACTS_INVALID"
    LEGAL_BASIS_DEFERRED = "LEGAL_BASIS_DEFERRED"
    ELIGIBILITY_DENIED = "ELIGIBILITY_DENIED"


@dataclass(frozen=True, slots=True)
class BE1FactReadResult:
    reason: FactReaderReason
    member: MemberFact | None = None
    context: ContextDecision | None = None
    context_revision: int | None = None


_PROOF_KEYS = (
    "proof_evidence_id",
    "proof_schema_version",
    "proof_data_origin",
    "proof_organization_id",
    "proof_class_id",
    "proof_child_id",
    "proof_purpose_ref",
    "proof_run_ref",
    "proof_session_id",
    "proof_revocation_revision",
    "proof_issued_at",
    "proof_expires_at",
    "proof_revoked_at",
)
_AGE_SOURCES = frozenset({"LEGACY_UNKNOWN", "SYNTHETIC_FIXTURE", "ADULT_DECLARED"})


def _aware_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("proof timestamp must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _proof_payload(proof: BE1SyntheticProofFact | None) -> dict[str, object]:
    if proof is None:
        return dict.fromkeys(_PROOF_KEYS)
    return {
        "proof_evidence_id": proof.evidence_id,
        "proof_schema_version": proof.schema_version,
        "proof_data_origin": proof.data_origin,
        "proof_organization_id": proof.scope.organization_id,
        "proof_class_id": proof.scope.class_id,
        "proof_child_id": proof.scope.child_id,
        "proof_purpose_ref": proof.scope.purpose_ref,
        "proof_run_ref": proof.run_ref,
        "proof_session_id": proof.session_id,
        "proof_revocation_revision": proof.revocation_revision,
        "proof_issued_at": _aware_utc(proof.issued_at),
        "proof_expires_at": _aware_utc(proof.expires_at),
        "proof_revoked_at": None if proof.revoked_at is None else _aware_utc(proof.revoked_at),
    }


def _context_payload(snapshot: BE1FactSnapshot, basis_version: str) -> dict[str, object]:
    return {
        "schema_version": CONTEXT_REVISION_SCHEMA_VERSION,
        "organization_id": snapshot.organization_id,
        "class_id": snapshot.class_id,
        "session_id": snapshot.session_id,
        "session_state": snapshot.session_state,
        "session_run_ref": snapshot.session_run_ref,
        "environment": snapshot.environment,
        "pilot_enabled": snapshot.pilot_enabled,
        "purpose_ref": snapshot.purpose_ref,
        "child_id": snapshot.child_id,
        "data_origin": (
            str(snapshot.profile_origin) if snapshot.profile_origin is not None else None
        ),
        "profile_state": snapshot.profile_state,
        "age_months": snapshot.age_months,
        "age_revision": snapshot.age_revision,
        "age_source": snapshot.age_source,
        "consent_record_ref": snapshot.consent_record_ref,
        "consent_revision": snapshot.consent_revision,
        "consent_state": snapshot.consent_state,
        "consent_effective": snapshot.legal_consent_effective,
        "purpose_granted": snapshot.purpose_granted,
        "membership_state": snapshot.membership_state,
        "group_id": snapshot.group_id,
        **_proof_payload(snapshot.proof),
        "basis_version": basis_version,
    }


class BE1FactReader:
    """Build synthetic-only single-member BE2 facts from an injected current-facts source."""

    def __init__(self, source: BE1FactSource) -> None:
        self._source = source

    def read(self, request: BE1FactRequest) -> BE1FactReadResult:
        if (
            not request.organization_id
            or not request.class_id
            or not request.session_id
            or not request.child_id
            or not request.purpose_ref
        ):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)
        if len(request.audience_participant_ids) != 1 or request.audience_participant_ids != (
            request.child_id,
        ):
            return BE1FactReadResult(FactReaderReason.AUDIENCE_UNSUPPORTED)
        if request.context_mode is not ProviderContextMode.IMAGE_ONLY:
            return BE1FactReadResult(FactReaderReason.CONTEXT_MODE_UNSUPPORTED)

        try:
            snapshot = self._source.current_facts(request)
        except Exception:
            return BE1FactReadResult(FactReaderReason.SOURCE_UNAVAILABLE)
        if snapshot is None:
            return BE1FactReadResult(FactReaderReason.SOURCE_UNAVAILABLE)

        if (
            snapshot.organization_id != request.organization_id
            or snapshot.class_id != request.class_id
            or snapshot.session_id != request.session_id
            or snapshot.child_id != request.child_id
            or snapshot.purpose_ref != request.purpose_ref
        ):
            return BE1FactReadResult(FactReaderReason.SCOPE_MISMATCH)
        if snapshot.profile_state != "active":
            return BE1FactReadResult(FactReaderReason.PROFILE_INACTIVE)
        if snapshot.session_state != "active":
            return BE1FactReadResult(FactReaderReason.SESSION_NOT_ACTIVE)
        if snapshot.membership_state != "admitted" or not snapshot.group_id:
            return BE1FactReadResult(FactReaderReason.MEMBERSHIP_NOT_ADMITTED)
        if (
            type(snapshot.pilot_enabled) is not bool
            or type(snapshot.purpose_granted) is not bool
            or type(snapshot.age_months) is not int
            or type(snapshot.age_revision) is not int
            or snapshot.age_revision < 1
            or snapshot.age_source not in _AGE_SOURCES
            or type(snapshot.legal_consent_effective) not in (bool, type(None))
        ):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)
        try:
            validate_age_months(snapshot.age_months)
        except (CoreRuleViolation, TypeError):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)

        origin = snapshot.profile_origin
        if (
            origin == ProvisionalDataOrigin.SYNTHETIC_DEV
            and snapshot.age_source != "SYNTHETIC_FIXTURE"
        ):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)
        if origin != ProvisionalDataOrigin.SYNTHETIC_DEV:
            legal = evaluate_eligibility(
                EligibilityFacts(
                    profile_origin=origin,
                    scope=EligibilityScope(
                        request.organization_id,
                        request.class_id,
                        request.child_id,
                        request.purpose_ref,
                    ),
                    legal_consent_effective=snapshot.legal_consent_effective,
                    proof=None,
                    session_run_ref=snapshot.session_run_ref,
                    session_id=request.session_id,
                    environment=snapshot.environment,
                    pilot_enabled=snapshot.pilot_enabled,
                    evaluated_at=snapshot.evaluated_at,
                )
            )
            reason = (
                FactReaderReason.LEGAL_BASIS_DEFERRED
                if legal.basis is EligibilityBasis.LEGAL_CONSENT
                else FactReaderReason.ELIGIBILITY_DENIED
            )
            return BE1FactReadResult(reason)

        proof_fact = snapshot.proof
        if (
            snapshot.consent_record_ref is not None
            or snapshot.consent_revision is not None
            or snapshot.consent_state is not None
            or snapshot.legal_consent_effective is not False
            or snapshot.purpose_granted is not False
            or proof_fact is None
        ):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)
        if (
            type(proof_fact.revocation_revision) is not int
            or proof_fact.revocation_revision < 0
            or (proof_fact.revoked_at is None and proof_fact.revocation_revision != 0)
            or (proof_fact.revoked_at is not None and proof_fact.revocation_revision <= 0)
            or proof_fact.data_origin != ProvisionalDataOrigin.SYNTHETIC_DEV
        ):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)

        proof = SyntheticEligibilityProof(
            evidence_id=proof_fact.evidence_id,
            scope=proof_fact.scope,
            run_ref=proof_fact.run_ref,
            issued_at=proof_fact.issued_at,
            expires_at=proof_fact.expires_at,
            revoked_at=proof_fact.revoked_at,
            session_id=proof_fact.session_id,
            schema_version=proof_fact.schema_version,
        )
        decision = evaluate_eligibility(
            EligibilityFacts(
                profile_origin=origin,
                scope=EligibilityScope(
                    request.organization_id,
                    request.class_id,
                    request.child_id,
                    request.purpose_ref,
                ),
                legal_consent_effective=False,
                proof=proof,
                session_run_ref=snapshot.session_run_ref,
                session_id=request.session_id,
                environment=snapshot.environment,
                pilot_enabled=snapshot.pilot_enabled,
                evaluated_at=snapshot.evaluated_at,
            )
        )
        if decision.basis is not EligibilityBasis.SYNTHETIC_DEV:
            return BE1FactReadResult(FactReaderReason.ELIGIBILITY_DENIED)
        if proof_fact.session_id != request.session_id:
            return BE1FactReadResult(FactReaderReason.ELIGIBILITY_DENIED)

        try:
            payload = _context_payload(snapshot, decision.basis_version)
            revision = context_revision(payload)
            digest = context_digest(payload)
            member = MemberFact(
                participant_id=snapshot.child_id,
                completed_age_months=snapshot.age_months,
                age_provenance_ref=(
                    f"be1-profile-age-v2:{snapshot.age_source}:{snapshot.age_revision}"
                ),
                age_revision=snapshot.age_revision,
                consent_record_ref=None,
                consent_revision=None,
                consent_effective=False,
                purpose_granted=False,
                eligibility_basis=str(decision.basis),
                basis_version=decision.basis_version,
                evidence_ref=decision.evidence_id,
                eligibility_scope=EligibilityScope(
                    request.organization_id,
                    request.class_id,
                    request.child_id,
                    request.purpose_ref,
                ),
            )
            context = ContextDecision(
                context_revision=revision,
                consent_effective=False,
                purpose_granted=False,
                session_active=True,
                audience_age_months=((snapshot.child_id, snapshot.age_months),),
                eligibility_basis=str(decision.basis),
                basis_version=decision.basis_version,
                evidence_ref=decision.evidence_id,
                eligibility_scope=EligibilityScope(
                    request.organization_id,
                    request.class_id,
                    request.child_id,
                    request.purpose_ref,
                ),
                context_digest=digest,
            )
        except (AssistanceRuleViolation, ValueError, TypeError):
            return BE1FactReadResult(FactReaderReason.FACTS_INVALID)

        return BE1FactReadResult(FactReaderReason.ALLOWED, member, context, revision)


__all__ = [
    "BE1FactReadResult",
    "BE1FactReader",
    "BE1FactRequest",
    "BE1FactSnapshot",
    "BE1FactSource",
    "BE1SyntheticProofFact",
    "FactReaderReason",
]
