"""FEAT-018-local internal typed fixture-manifest schema for image admission (D1 section 6).

Deliberately test-scoped: this is NOT a public contract and must never be imported from
`sketch2life.contracts`. `MediaFixtureManifestV1` (FEAT-003) cannot represent admission
outcomes — its `expected_decision` admits only `PASS`/`RECAPTURE` — and mandates an
`audio_ref` admission does not have, so this schema exists instead of reusing or widening it.
`SourceMediaReferenceV1` continues to be reused unchanged by the application service for a
successful admission; it is not duplicated here.

`expected_outcome`/`expected_reason` are typed directly against the domain's own
`AdmissionOutcome`/`AdmissionReason` enums (single source of truth, no hand-duplicated string
literals), and a manifest entry is rejected outright if its reason does not actually belong to
its declared outcome, per the domain's own `outcome_for_reason` mapping.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.domain.understanding.image_admission import (
    AdmissionOutcome,
    AdmissionReason,
    outcome_for_reason,
)


class Feat018AdmissionFixtureManifestEntryV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fixture_id: str = Field(pattern=r"^[a-z0-9-]+$")
    generator: str = Field(min_length=1)
    payload_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    declared_width: int | None = Field(default=None, ge=0)
    declared_height: int | None = Field(default=None, ge=0)
    expected_outcome: AdmissionOutcome
    expected_reason: AdmissionReason | None = None
    expected_container: str | None = None
    expected_codec: str | None = None
    expected_pixel_format: str | None = None
    synthetic_data: Literal[True] = True

    @model_validator(mode="after")
    def _validate_outcome_reason_pair(self) -> Feat018AdmissionFixtureManifestEntryV1:
        if self.expected_outcome is AdmissionOutcome.ADMITTED:
            if self.expected_reason is not None:
                raise ValueError(
                    f"fixture {self.fixture_id!r}: ADMITTED entries must not declare "
                    f"an expected_reason (got {self.expected_reason!r})"
                )
            return self
        if self.expected_reason is None:
            raise ValueError(
                f"fixture {self.fixture_id!r}: {self.expected_outcome} entries must "
                "declare an expected_reason"
            )
        actual_outcome = outcome_for_reason(self.expected_reason)
        if actual_outcome is not self.expected_outcome:
            raise ValueError(
                f"fixture {self.fixture_id!r}: reason {self.expected_reason} belongs to "
                f"outcome {actual_outcome}, not the declared {self.expected_outcome}"
            )
        return self


class Feat018AdmissionFixtureManifestV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_name: Literal["Feat018AdmissionFixtureManifestV1"] = (
        "Feat018AdmissionFixtureManifestV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    data_policy: Literal["synthetic-only"] = "synthetic-only"
    generator: str = Field(min_length=1)
    fixtures: tuple[Feat018AdmissionFixtureManifestEntryV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_unique_fixture_ids(self) -> Feat018AdmissionFixtureManifestV1:
        seen: set[str] = set()
        for entry in self.fixtures:
            if entry.fixture_id in seen:
                raise ValueError(f"duplicate fixture_id: {entry.fixture_id!r}")
            seen.add(entry.fixture_id)
        return self
