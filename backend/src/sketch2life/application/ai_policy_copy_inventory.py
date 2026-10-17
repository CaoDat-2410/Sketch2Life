"""Guarded inventory metadata operations, not provider dispatch or deletion authority."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from pydantic import TypeAdapter

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_authority import validate_copy_grant
from sketch2life.application.ports.ai_policy_copy_inventory import (
    CopyInventoryAccess,
    CopyInventoryAction,
    CopyInventoryBoundary,
)
from sketch2life.application.ports.ai_policy_copy_registry import (
    CopyRegistryPage,
    ProviderCopyInventoryStore,
    RegisteredProviderCopy,
)
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant, CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_inventory import (
    CopyInventoryContext,
    CopyInventoryCoverageProof,
    CopyInventoryReadRequest,
    CopyInventorySourceProof,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_policy.model import PolicyError

_ID = TypeAdapter(OpaqueId)


def _native[T: StrictPolicyModel](
    model: type[T], value: T, *, error: str = "AI_POLICY_INVALID_COPY_REGISTRY_REQUEST"
) -> T:
    try:
        return model.model_validate(value.model_dump(mode="python"), strict=True)
    except (TypeError, ValueError, AttributeError):
        raise PolicyError(error) from None


class ProviderCopyInventoryService:
    def __init__(
        self,
        store: ProviderCopyInventoryStore,
        boundary: CopyInventoryBoundary,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store, self.boundary = store, boundary
        self.clock = clock or (lambda: datetime.now(UTC))

    @contextmanager
    def _hold(
        self,
        principal: str,
        org: str,
        context: CopyInventoryContext,
        action: CopyInventoryAction,
        payload: dict[str, object],
    ) -> Iterator[tuple[CopyInventoryAccess, CopyAuthorityGrant, str]]:
        try:
            _ID.validate_python(principal, strict=True)
            _ID.validate_python(org, strict=True)
        except (ValueError, TypeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_REQUEST") from None
        digest = _digest(
            dict(
                principal_id=principal,
                organization_id=org,
                action="copy_inventory." + action,
                context=context.model_dump(mode="json"),
                payload=payload,
            )
        )
        try:
            with self.boundary.guard(principal, org, context) as access:
                grant = validate_copy_grant(
                    access.authorize(context, action, digest), principal, org, digest, self.clock()
                )
                yield access, grant, digest
        except PolicyError:
            raise
        except Exception:
            raise PolicyError("AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE") from None

    def _source(
        self, proof: CopyInventorySourceProof, digest: str, reference: CopyReceiptReference
    ) -> None:
        if proof.binding_digest != digest or proof.reference != reference:
            raise PolicyError("AI_POLICY_COPY_SOURCE_MISMATCH")
        if proof.verified is not True:
            raise PolicyError("AI_POLICY_COPY_SOURCE_UNVERIFIED")
        if proof.expires_at <= self.clock():
            raise PolicyError("AI_POLICY_COPY_SOURCE_EXPIRED")

    def _confirm(
        self,
        access: CopyInventoryAccess,
        original: CopyAuthorityGrant,
        principal: str,
        org: str,
        context: CopyInventoryContext,
        action: CopyInventoryAction,
        digest: str,
        proof: CopyInventorySourceProof | None = None,
        reference: CopyReceiptReference | None = None,
    ) -> None:
        current = validate_copy_grant(
            access.authorize(context, action, digest), principal, org, digest, self.clock()
        )
        if current != original:
            raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
        if proof is not None and reference is not None:
            self._source(proof, digest, reference)

    def register(
        self,
        principal_id: str,
        organization_id: str,
        context: CopyInventoryContext,
        registration: CopyRegistryRegistration,
        reference: CopyReceiptReference,
    ) -> RegisteredProviderCopy:
        context = _native(CopyInventoryContext, context)
        registration = _native(CopyRegistryRegistration, registration)
        reference = _native(CopyReceiptReference, reference)
        if (registration.organization_id, registration.scope_ref) != (
            organization_id,
            context.scope_ref,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        with self._hold(
            principal_id,
            organization_id,
            context,
            "register",
            dict(
                registration=registration.model_dump(mode="json"),
                reference=reference.model_dump(mode="json"),
            ),
        ) as (access, grant, digest):
            proof = _native(
                CopyInventorySourceProof,
                access.registration_source(
                    context,
                    registration,
                    reference,
                    digest,
                ),
                error="AI_POLICY_COPY_SOURCE_MISMATCH",
            )
            self._source(proof, digest, reference)
            with self.store.transaction(
                organization_id, context.scope_ref, principal_id=principal_id, for_update=True
            ) as tx:
                result = tx.register(registration)
                self._confirm(
                    access,
                    grant,
                    principal_id,
                    organization_id,
                    context,
                    "register",
                    digest,
                    proof,
                    reference,
                )
            return result

    def page(
        self, principal_id: str, organization_id: str, request: CopyInventoryReadRequest
    ) -> CopyRegistryPage:
        request = _native(CopyInventoryReadRequest, request)
        context = CopyInventoryContext(
            data_request_ref=request.data_request_ref, scope_ref=request.scope_ref
        )
        with self._hold(
            principal_id, organization_id, context, "read", request.model_dump(mode="json")
        ) as (access, grant, digest):
            with self.store.transaction(
                organization_id, context.scope_ref, principal_id=principal_id
            ) as tx:
                result = tx.page(
                    limit=request.limit,
                    after=request.after,
                    expected_revision=request.expected_revision,
                )
                self._confirm(access, grant, principal_id, organization_id, context, "read", digest)
            return result

    def fence(self, principal_id: str, organization_id: str, context: CopyInventoryContext) -> int:
        """Monotonic scope block only; no cancellation/purge or acknowledgment implied."""
        context = _native(CopyInventoryContext, context)
        with self._hold(principal_id, organization_id, context, "fence", {}) as (
            access,
            grant,
            digest,
        ):
            with self.store.transaction(
                organization_id, context.scope_ref, principal_id=principal_id, for_update=True
            ) as tx:
                revision = tx.mark_purging()
                self._confirm(
                    access, grant, principal_id, organization_id, context, "fence", digest
                )
            return revision

    def coverage(
        self,
        principal_id: str,
        organization_id: str,
        context: CopyInventoryContext,
        *,
        expected_revision: int,
        reference: CopyReceiptReference,
    ) -> int:
        context = _native(CopyInventoryContext, context)
        reference = _native(CopyReceiptReference, reference)
        if type(expected_revision) is not int or expected_revision < 0:
            raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_REQUEST")
        with self._hold(
            principal_id,
            organization_id,
            context,
            "coverage",
            dict(
                expected_revision=expected_revision,
                reference=reference.model_dump(mode="json"),
            ),
        ) as (access, grant, digest):
            proof = _native(
                CopyInventoryCoverageProof,
                access.coverage_source(
                    context,
                    expected_revision,
                    reference,
                    digest,
                ),
                error="AI_POLICY_COPY_SOURCE_MISMATCH",
            )
            self._source(proof, digest, reference)
            observation: CopyCoverageObservation = proof.observation
            if (
                observation.organization_id,
                observation.scope_ref,
                observation.expected_revision,
                observation.attestation_ref,
            ) != (
                organization_id,
                context.scope_ref,
                expected_revision,
                reference,
            ):
                raise PolicyError("AI_POLICY_COPY_SOURCE_MISMATCH")
            with self.store.transaction(
                organization_id, context.scope_ref, principal_id=principal_id, for_update=True
            ) as tx:
                revision = tx.record_coverage(observation)
                self._confirm(
                    access,
                    grant,
                    principal_id,
                    organization_id,
                    context,
                    "coverage",
                    digest,
                    proof,
                    reference,
                )
            return revision
