"""Pure decisions over server-fetched facts for the FEAT-064 dev pilot.

Origin names are PROVISIONAL until the BE1 owner confirms the schema. This
module grants no authority to client assertions and performs no proof lookup.
The caller must obtain proof and legal facts from trusted server storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

BASIS_VERSION = "eligibility-decision-v1"
PROOF_VERSION = "synthetic-dev-eligibility-v1"


class ProvisionalDataOrigin(StrEnum):
    """PROVISIONAL domain names; not an approved persistence schema."""

    REAL = "REAL"
    SYNTHETIC_DEV = "SYNTHETIC_DEV"
    LEGACY_UNCLASSIFIED = "LEGACY_UNCLASSIFIED"


class EligibilityBasis(StrEnum):
    LEGAL_CONSENT = "LEGAL_CONSENT"
    SYNTHETIC_DEV = "SYNTHETIC_DEV"
    DENIED = "DENIED"


class EligibilityReason(StrEnum):
    LEGAL_CONSENT_EFFECTIVE = "LEGAL_CONSENT_EFFECTIVE"
    SYNTHETIC_PROOF_VALID = "SYNTHETIC_PROOF_VALID"
    INVALID_FACTS = "INVALID_FACTS"
    ORIGIN_NOT_ALLOWED = "ORIGIN_NOT_ALLOWED"
    LEGAL_CONSENT_NOT_EFFECTIVE = "LEGAL_CONSENT_NOT_EFFECTIVE"
    PROOF_ON_LEGAL_PROFILE = "PROOF_ON_LEGAL_PROFILE"
    CONFLICTING_BASIS = "CONFLICTING_BASIS"
    ENVIRONMENT_DENIED = "ENVIRONMENT_DENIED"
    PILOT_DISABLED = "PILOT_DISABLED"
    PROOF_REQUIRED = "PROOF_REQUIRED"
    INVALID_PROOF = "INVALID_PROOF"
    PROOF_REVOKED = "PROOF_REVOKED"
    PROOF_NOT_YET_VALID = "PROOF_NOT_YET_VALID"
    PROOF_EXPIRED = "PROOF_EXPIRED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    RUN_REQUIRED = "RUN_REQUIRED"
    RUN_MISMATCH = "RUN_MISMATCH"
    SESSION_MISMATCH = "SESSION_MISMATCH"


@dataclass(frozen=True, slots=True)
class EligibilityScope:
    organization_id: str
    class_id: str
    child_id: str
    purpose_ref: str


@dataclass(frozen=True, slots=True)
class SyntheticEligibilityProof:
    """Trusted stored proof facts, not a request-body DTO or signature verifier."""

    evidence_id: str
    scope: EligibilityScope
    run_ref: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    session_id: str | None = None
    schema_version: str = PROOF_VERSION


@dataclass(frozen=True, slots=True)
class EligibilityFacts:
    profile_origin: ProvisionalDataOrigin | str | None
    scope: EligibilityScope
    legal_consent_effective: bool | None
    proof: SyntheticEligibilityProof | None
    # Caller reads this value from session.configuration["pilot_run_ref"].
    session_run_ref: str | None
    session_id: str | None
    environment: str | None
    pilot_enabled: bool
    evaluated_at: datetime


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """Separate eligibility basis; deliberately has no consent-effective field."""

    basis: EligibilityBasis
    reason: EligibilityReason
    basis_version: str = BASIS_VERSION
    evidence_id: str | None = None


def _denied(reason: EligibilityReason) -> EligibilityDecision:
    return EligibilityDecision(EligibilityBasis.DENIED, reason)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_scope(scope: object) -> bool:
    return isinstance(scope, EligibilityScope) and all(
        _nonempty(value)
        for value in (scope.organization_id, scope.class_id, scope.child_id, scope.purpose_ref)
    )


def _aware(value: object) -> bool:
    return (
        isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
    )


def evaluate_eligibility(facts: EligibilityFacts) -> EligibilityDecision:
    """Decide from current fetched facts without changing consent or stored state."""

    if not isinstance(facts, EligibilityFacts) or not _valid_scope(facts.scope):
        return _denied(EligibilityReason.INVALID_FACTS)
    if facts.profile_origin not in tuple(ProvisionalDataOrigin):
        return _denied(EligibilityReason.ORIGIN_NOT_ALLOWED)

    if facts.profile_origin != ProvisionalDataOrigin.SYNTHETIC_DEV:
        if facts.proof is not None:
            return _denied(EligibilityReason.PROOF_ON_LEGAL_PROFILE)
        # Preserve the existing effective lookup even for legacy profiles.
        if facts.legal_consent_effective is True:
            return EligibilityDecision(
                EligibilityBasis.LEGAL_CONSENT,
                EligibilityReason.LEGAL_CONSENT_EFFECTIVE,
            )
        return _denied(EligibilityReason.LEGAL_CONSENT_NOT_EFFECTIVE)

    if facts.legal_consent_effective is not False and facts.legal_consent_effective is not None:
        return _denied(EligibilityReason.CONFLICTING_BASIS)
    if facts.environment not in ("local", "test"):
        return _denied(EligibilityReason.ENVIRONMENT_DENIED)
    if facts.pilot_enabled is not True:
        return _denied(EligibilityReason.PILOT_DISABLED)
    if not _aware(facts.evaluated_at):
        return _denied(EligibilityReason.INVALID_FACTS)
    if not _nonempty(facts.session_run_ref):
        return _denied(EligibilityReason.RUN_REQUIRED)
    proof = facts.proof
    if proof is None:
        return _denied(EligibilityReason.PROOF_REQUIRED)
    if not isinstance(proof, SyntheticEligibilityProof):
        return _denied(EligibilityReason.INVALID_PROOF)
    if (
        not _nonempty(proof.evidence_id)
        or not _valid_scope(proof.scope)
        or not _nonempty(proof.run_ref)
        or proof.schema_version != PROOF_VERSION
        or (proof.session_id is not None and not _nonempty(proof.session_id))
        or not _aware(proof.issued_at)
        or not _aware(proof.expires_at)
    ):
        return _denied(EligibilityReason.INVALID_PROOF)
    # Same-zone datetime comparison ignores fold during a repeated DST hour.
    issued_at = proof.issued_at.astimezone(UTC)
    expires_at = proof.expires_at.astimezone(UTC)
    evaluated_at = facts.evaluated_at.astimezone(UTC)
    if expires_at <= issued_at:
        return _denied(EligibilityReason.INVALID_PROOF)
    if proof.revoked_at is not None:
        return _denied(EligibilityReason.PROOF_REVOKED)
    if proof.scope != facts.scope:
        return _denied(EligibilityReason.SCOPE_MISMATCH)
    if proof.run_ref != facts.session_run_ref:
        return _denied(EligibilityReason.RUN_MISMATCH)
    if proof.session_id is not None and proof.session_id != facts.session_id:
        return _denied(EligibilityReason.SESSION_MISMATCH)
    if issued_at > evaluated_at:
        return _denied(EligibilityReason.PROOF_NOT_YET_VALID)
    if expires_at <= evaluated_at:
        return _denied(EligibilityReason.PROOF_EXPIRED)
    return EligibilityDecision(
        EligibilityBasis.SYNTHETIC_DEV,
        EligibilityReason.SYNTHETIC_PROOF_VALID,
        evidence_id=proof.evidence_id,
    )
