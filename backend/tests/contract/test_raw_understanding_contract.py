from __future__ import annotations

from pydantic import TypeAdapter

from sketch2life.contracts.schemas.raw_understanding import (
    RawUnderstandingResultV1,
    RawUnderstandingSuccessV1,
)


def test_raw_understanding_is_a_discriminated_versioned_contract() -> None:
    schema = TypeAdapter(RawUnderstandingResultV1).json_schema()
    assert schema["discriminator"]["propertyName"] == "status"
    assert "RawUnderstandingSuccessV1" in str(schema)


def test_success_contract_serializes_without_gate_or_provider_decisions() -> None:
    assert RawUnderstandingSuccessV1.model_fields["gate_a_required"].default is True
    assert "eligibility" not in RawUnderstandingSuccessV1.model_fields
    assert "activity" not in RawUnderstandingSuccessV1.model_fields
    assert "objective" not in RawUnderstandingSuccessV1.model_fields
    assert "provider_url" not in RawUnderstandingSuccessV1.model_fields
