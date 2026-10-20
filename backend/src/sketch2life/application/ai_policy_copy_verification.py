"""Exact guarded evidence verification bridge to EXISTING foundation purge receipt."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from pydantic import TypeAdapter

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ports.ai_policy_copy import ProviderCopyVerificationBoundary
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import (
    CopyAuthorityGrant,
    CopyReceiptReference,
    CopyVerificationBinding,
    ProviderCopyCommand,
    VerifiedCopyReceipt,
)
from sketch2life.domain.ai_jobs.provider_copy import (
    CopyKind,
    CopyStatus,
    EvidenceKind,
    ProviderCopy,
    PurgeReceipt,
    ReceiptOutcome,
)
from sketch2life.domain.ai_policy.model import PolicyError

_ID = TypeAdapter(OpaqueId)


class ProviderCopyReceiptVerifier:
    def __init__(
        self,
        boundary: ProviderCopyVerificationBoundary,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.boundary = boundary
        self.clock = clock or (lambda: datetime.now(UTC))

    def _grant(
        self, grant: CopyAuthorityGrant, principal: str, org: str, digest: str
    ) -> CopyAuthorityGrant:
        return validate_copy_grant(grant, principal, org, digest, self.clock())

    @contextmanager
    def purge_receipt(
        self,
        principal_id: str,
        organization_id: str,
        command: ProviderCopyCommand,
        copy: ProviderCopy,
        reference: CopyReceiptReference,
    ) -> Iterator[PurgeReceipt]:
        """Hold current guard through caller's eventual registry mutation/commit.

        No provider dispatch or registry mutation here. Receipt outside this
        context is metadata, not permission; foundation transitions remain reused.
        """
        try:
            command = ProviderCopyCommand.model_validate(
                command.model_dump(mode="python"), strict=True
            )
            reference = CopyReceiptReference.model_validate(
                reference.model_dump(mode="python"), strict=True
            )
            for value in (
                principal_id,
                organization_id,
                copy.copy_id,
                copy.organization_id,
                copy.scope_ref,
                copy.provider_profile,
            ):
                _ID.validate_python(value, strict=True)
            if (
                not isinstance(copy.kind, CopyKind)
                or not isinstance(copy.status, CopyStatus)
                or command.operation != "purge"
            ):
                raise ValueError("invalid purge target")
            if (copy.organization_id, copy.scope_ref) != (organization_id, command.scope_ref):
                raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        except PolicyError:
            raise
        except (TypeError, ValueError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_REQUEST") from None
        digest = _digest(
            dict(
                principal_id=principal_id,
                organization_id=organization_id,
                command=command.model_dump(mode="json"),
            )
        )
        try:
            with self.boundary.guard(principal_id, organization_id) as access:
                grant = self._grant(
                    access.authorize(command, digest), principal_id, organization_id, digest
                )
                raw_profile = access.resolve_profile(copy)
                try:
                    profile = PolicyDefinitionRef.model_validate(
                        raw_profile.model_dump(mode="python"), strict=True
                    )
                except (TypeError, ValueError, AttributeError):
                    raise PolicyError("AI_POLICY_COPY_PROFILE_MISMATCH") from None
                if profile.ref != copy.provider_profile:
                    raise PolicyError("AI_POLICY_COPY_PROFILE_MISMATCH")
                binding = CopyVerificationBinding(
                    principal_id=principal_id,
                    organization_id=organization_id,
                    command=command,
                    authority_revision=grant.authority_revision,
                    copy_id=copy.copy_id,
                    kind=copy.kind.value,
                    profile_ref=profile,
                )
                binding_digest = _digest(binding.model_dump(mode="json"))
                raw = access.verify_receipt(binding, reference, binding_digest)
                try:
                    proof = VerifiedCopyReceipt.model_validate(
                        raw.model_dump(mode="python"), strict=True
                    )
                except (TypeError, ValueError, AttributeError):
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_MISMATCH") from None
                if proof.binding_digest != binding_digest or proof.reference != reference:
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_MISMATCH")
                # Detect revocation/expiry during verification, not just entry.
                current = self._grant(
                    access.authorize(command, digest), principal_id, organization_id, digest
                )
                if current != grant:
                    raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
                if proof.expires_at <= self.clock():
                    raise PolicyError("AI_POLICY_COPY_RECEIPT_EXPIRED")
                yield PurgeReceipt(
                    reference.ref,
                    copy.copy_id,
                    ReceiptOutcome(proof.outcome),
                    proof.verified,
                    EvidenceKind(proof.evidence_kind),
                    proof.reason_code,
                )
                # Owner fence is held until caller registry commit. It must block
                # revocation until exit; this context isn't a detached grant.
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE") from None
