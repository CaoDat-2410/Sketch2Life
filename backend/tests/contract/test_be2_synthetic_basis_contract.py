"""Eligibility basis stays in trusted BE2 facts and is not accepted from clients."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from sketch2life.contracts.schemas.analysis_context_results import (
    AnalysisRecordV2,
    AnalysisWorkerCandidateV2,
    TypedProvenanceV2,
)
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisRecordV1,
    AnalysisWorkerCandidateV1,
)
from sketch2life.contracts.schemas.assistance_requests import (
    AssistanceRequestCommandV1,
    AssistanceRequestDeviceViewV1,
    AssistanceRequestRecordV1,
)

_INTERNAL_ELIGIBILITY_FIELDS = {
    "consent_effective",
    "purpose_granted",
    "eligibility_basis",
    "basis_version",
    "evidence_ref",
    "eligibility_scope",
}
_DTO_TYPES: tuple[type[BaseModel], ...] = (
    AssistanceRequestCommandV1,
    AssistanceRequestRecordV1,
    AssistanceRequestDeviceViewV1,
    AnalysisWorkerCandidateV1,
    AnalysisRecordV1,
    TypedProvenanceV2,
    AnalysisWorkerCandidateV2,
    AnalysisRecordV2,
)


def test_wire_dtos_do_not_expose_internal_consent_or_eligibility_facts() -> None:
    for dto in _DTO_TYPES:
        assert not (_INTERNAL_ELIGIBILITY_FIELDS & dto.model_fields.keys()), dto.__name__


def test_client_cannot_supply_synthetic_eligibility_basis() -> None:
    command = {
        "canvas_id": "synthetic-canvas",
        "checkpoint_ref": {
            "checkpoint_id": "synthetic-checkpoint",
            "document_epoch": 0,
            "server_sequence": 0,
            "hash": "a" * 64,
        },
        "target_scope": {"kind": "individual", "participant_id": "synthetic-child"},
        "requested_level": "basic",
        "request_reason": "child_request",
        "context_revision": 0,
        "client_request_id": "synthetic-request",
        "eligibility_basis": "SYNTHETIC_DEV",
    }

    with pytest.raises(ValidationError):
        AssistanceRequestCommandV1.model_validate(command)
