"""Allowlisted copy report; stored receipt metadata never closes a BE1 request."""

from typing import Literal

from pydantic import Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference


class CopyReportItem(StrictPolicyModel):
    copy_id: OpaqueId
    kind: Literal["input", "output", "job", "cache"]
    revision: int = Field(ge=0)
    label: Literal[
        "discovered",
        "cancel_requested",
        "purge_requested",
        "pending",
        "unsupported",
        "exception",
        "deleted",
        "fixture_deleted_not_actual",
    ]
    actual_deletion_proven: bool
    purge_receipt: CopyReceiptReference | None
    purge_evidence_kind: Literal["fixture", "provider"] | None
    cancel_acknowledgment: Literal[
        "not_confirmed", "fixture_confirmed_not_actual", "provider_confirmed_recorded"
    ]

    @model_validator(mode="after")
    def consistent(self) -> "CopyReportItem":
        if self.actual_deletion_proven != (self.label == "deleted"):
            raise ValueError("actual deletion label mismatch")
        if (self.purge_receipt is None) != (self.purge_evidence_kind is None):
            raise ValueError("receipt classification mismatch")
        if self.label in {"deleted", "fixture_deleted_not_actual"}:
            expected = "provider" if self.actual_deletion_proven else "fixture"
            if self.purge_receipt is None or self.purge_evidence_kind != expected:
                raise ValueError("deletion requires classified receipt")
        return self


class CopyReportPage(StrictPolicyModel):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    organization_id: OpaqueId
    scope_ref: OpaqueId
    revision: int = Field(ge=0)
    scope_purging: bool
    records: tuple[CopyReportItem, ...] = Field(max_length=256)
    next_after: OpaqueId | None
    inventory_coverage: Literal["unknown", "partial", "reported_complete"]
    coverage_semantics: Literal["stored_attestation_not_current_completeness"] = (
        "stored_attestation_not_current_completeness"
    )
    overall_deletion: Literal["not_established"] = "not_established"

    @model_validator(mode="after")
    def cursor_order(self) -> "CopyReportPage":
        keys = tuple(item.copy_id for item in self.records)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("copy report order/identity mismatch")
        if self.next_after is not None and (not keys or self.next_after != keys[-1]):
            raise ValueError("copy report cursor mismatch")
        return self
