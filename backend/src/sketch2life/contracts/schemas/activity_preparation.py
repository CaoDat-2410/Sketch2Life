"""Provider-neutral preparation metadata for catalog activities.

Printable packs are deliberately modelled separately from activity materials.  A
material can be substituted at home, while a preparation profile answers whether
the authored activity depends on a reviewed, printable aid.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1


PrintRequirement = Literal[
    "NO_PRINTABLE_ASSET",
    "PRINT_RECOMMENDED",
    "PRINT_REQUIRED",
]
PreparationAssetKind = Literal[
    "MATCHING_CARD_SET",
    "SEQUENCE_CARD_SET",
    "PICTURE_CARD_SET",
    "SORTING_BOARD",
    "WORKSHEET",
    "LABEL_SET",
    "OBSERVATION_RECORD_SHEET",
    "REFERENCE_SHEET",
    "OTHER_REVIEWED_PRINTABLE",
]
AssetSetStatus = Literal[
    "NOT_APPLICABLE",
    "PLANNED",
    "READY",
    "BLOCKED",
    "DEPRECATED",
]


class PrintDefaultsV1(BaseModel):
    """Safe defaults used by the future parent/guide print flow."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    paper_size: Literal["A4"] = "A4"
    preferred_format: Literal["PDF"] = "PDF"
    editable_source_formats: tuple[Literal["SVG", "PNG"], ...] = Field(
        default=("SVG", "PNG"), min_length=1, max_length=2
    )
    color_mode: Literal["COLOR", "GRAYSCALE"] = "COLOR"
    copies: int = Field(default=1, ge=1, le=10)
    cut_required: bool = False
    lamination: Literal["NOT_NEEDED", "OPTIONAL", "RECOMMENDED"] = "OPTIONAL"


class PreparationProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Literal["AUTHORED_CATALOG"] = "AUTHORED_CATALOG"
    review_status: Literal[
        "PENDING_OWNER_REVIEW",
        "OWNER_REVIEWED",
        "APPROVED",
    ] = "PENDING_OWNER_REVIEW"
    classification_version: str = Field(min_length=1, max_length=40)


class ActivityPreparationProfileV1(BaseModel):
    """Exactly one preparation decision for one activity version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ActivityPreparationProfileV1"] = (
        "ActivityPreparationProfileV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    activity_ref: VersionedRefV1
    catalog_revision: str = Field(min_length=1, max_length=120)
    print_requirement: PrintRequirement
    guide_note_vi: str = Field(min_length=1, max_length=320)
    planned_asset_kinds: tuple[PreparationAssetKind, ...] = Field(
        default=(), max_length=4
    )
    asset_set_status: AssetSetStatus
    asset_set_refs: tuple[str, ...] = Field(default=(), max_length=4)
    print_defaults: PrintDefaultsV1 | None = None
    provenance: PreparationProvenanceV1

    @model_validator(mode="after")
    def validate_preparation_state(self) -> ActivityPreparationProfileV1:
        if len(self.planned_asset_kinds) != len(set(self.planned_asset_kinds)):
            raise ValueError("planned printable asset kinds must be unique")
        if len(self.asset_set_refs) != len(set(self.asset_set_refs)):
            raise ValueError("asset set refs must be unique")
        if self.print_requirement == "NO_PRINTABLE_ASSET":
            if (
                self.planned_asset_kinds
                or self.asset_set_refs
                or self.asset_set_status != "NOT_APPLICABLE"
                or self.print_defaults is not None
            ):
                raise ValueError(
                    "NO_PRINTABLE_ASSET cannot declare printable kinds, refs or defaults"
                )
            return self

        if not self.planned_asset_kinds:
            raise ValueError("printable activity requires at least one planned asset kind")
        if self.asset_set_status == "NOT_APPLICABLE":
            raise ValueError("printable activity cannot be NOT_APPLICABLE")
        if self.print_defaults is None:
            raise ValueError("printable activity requires print defaults")
        if self.asset_set_refs and self.asset_set_status not in {"READY", "DEPRECATED"}:
            raise ValueError("asset refs require a reviewed READY or DEPRECATED asset set")
        if self.asset_set_refs and self.provenance.review_status != "APPROVED":
            raise ValueError("asset refs require approved preparation provenance")
        return self


class ActivityPreparationCatalogV1(BaseModel):
    """Versioned manifest covering the active merged activity catalog."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["ActivityPreparationCatalogV1"] = (
        "ActivityPreparationCatalogV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    catalog_revision: str = Field(min_length=1, max_length=120)
    profiles: tuple[ActivityPreparationProfileV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_catalog(self) -> ActivityPreparationCatalogV1:
        refs = [(profile.activity_ref.id, profile.activity_ref.version) for profile in self.profiles]
        if len(refs) != len(set(refs)):
            raise ValueError("activity preparation catalog contains duplicate activity refs")
        if any(profile.catalog_revision != self.catalog_revision for profile in self.profiles):
            raise ValueError("activity preparation profile revision does not match catalog")
        return self


__all__ = [
    "ActivityPreparationCatalogV1",
    "ActivityPreparationProfileV1",
    "AssetSetStatus",
    "PreparationAssetKind",
    "PreparationProvenanceV1",
    "PrintDefaultsV1",
    "PrintRequirement",
]
