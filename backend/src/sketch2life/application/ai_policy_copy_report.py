"""Pure allowlist projection of trusted current-copy state, not receipt verification."""

from sketch2life.application.ai_policy_copy_resolution import foundation_copy
from sketch2life.application.ports.ai_policy_copy_registry import CopyRegistryPage
from sketch2life.contracts.schemas.ai_policy_copy_inventory import CopyInventoryReadRequest
from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import CopyLifecycleRecord
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.contracts.schemas.ai_policy_copy_report import CopyReportPage
from sketch2life.domain.ai_jobs.provider_copy import report_label
from sketch2life.domain.ai_policy.model import PolicyError


def project_copy_report(
    organization_id: str,
    request: CopyInventoryReadRequest,
    page: CopyRegistryPage,
    states: tuple[CopyLifecycleRecord, ...],
) -> CopyReportPage:
    try:
        if len(page.records) != len(states) or len(states) > request.limit:
            raise ValueError("copy report page bounds mismatch")
        if request.expected_revision is not None and page.revision != request.expected_revision:
            raise ValueError("copy report revision mismatch")
        coverage = "unknown"
        if page.coverage is not None:
            proof = CopyCoverageObservation.model_validate(
                page.coverage.model_dump(mode="python"), strict=True
            )
            if (proof.organization_id, proof.scope_ref, proof.expected_revision + 1) != (
                organization_id,
                request.scope_ref,
                page.revision,
            ):
                raise ValueError("copy report coverage mismatch")
            coverage = (
                "reported_complete"
                if set(proof.required_sources) == set(proof.observed_sources)
                else "partial"
            )
        items = []
        for registered, raw in zip(page.records, states, strict=True):
            original = CopyRegistryRegistration.model_validate(
                registered.registration.model_dump(mode="python"), strict=True
            )
            current = CopyLifecycleRecord.model_validate(raw.model_dump(mode="python"), strict=True)
            if current.registration != original or (
                original.organization_id,
                original.scope_ref,
            ) != (organization_id, request.scope_ref):
                raise ValueError("copy report current binding mismatch")
            if request.after is not None and original.copy_id <= request.after:
                raise ValueError("copy report cursor went backwards")
            copy = foundation_copy(current)
            acknowledgment = "not_confirmed"
            if current.cancel_confirmed:
                acknowledgment = (
                    "provider_confirmed_recorded"
                    if current.cancel_evidence_kind == "provider"
                    else "fixture_confirmed_not_actual"
                )
            items.append(
                dict(
                    copy_id=original.copy_id,
                    kind=original.kind,
                    revision=current.revision,
                    label=report_label(copy),
                    actual_deletion_proven=copy.actual_deletion_proven,
                    purge_receipt=current.purge_reference,
                    purge_evidence_kind=current.purge_evidence_kind,
                    cancel_acknowledgment=acknowledgment,
                )
            )
        return CopyReportPage.model_validate(
            dict(
                organization_id=organization_id,
                scope_ref=request.scope_ref,
                revision=page.revision,
                scope_purging=page.scope_purging,
                records=tuple(items),
                next_after=page.next_after,
                inventory_coverage=coverage,
            ),
            strict=True,
        )
    except (ValueError, TypeError, AttributeError):
        raise PolicyError("AI_POLICY_INVALID_COPY_REPORT_STORAGE") from None
