"""Internal candidate cursor metadata; not an external bearer capability or execution grant."""

from pydantic import AwareDatetime, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.ai_policy import StrictPolicyModel


class CopyCandidateCursor(StrictPolicyModel):
    organization_id: OpaqueId
    scope_ref: OpaqueId
    revision: int = Field(ge=0)
    as_of: AwareDatetime
    after: Sha256Hex


class CopyCandidateRequest(StrictPolicyModel):
    limit: int = Field(ge=1, le=256)
    as_of: AwareDatetime | None = None
    cursor: CopyCandidateCursor | None = None

    @model_validator(mode="after")
    def pinned_time(self) -> "CopyCandidateRequest":
        if (self.as_of is None) == (self.cursor is None):
            raise ValueError("supply first-page cutoff OR continuation cursor")
        return self
