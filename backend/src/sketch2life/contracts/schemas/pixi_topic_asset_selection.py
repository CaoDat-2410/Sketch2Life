"""Internal, versioned FEAT-028 contracts for AI-assisted Pixi topic asset selection.

These types are backend-internal and do not change frozen FEAT-018 renderer/mobile contracts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ReviewStatus = Literal["REVIEW_PENDING", "APPROVED", "APPLIED"]
RenderRole = Literal["SUBJECT", "ENVIRONMENT", "PROP", "EFFECT"]
SelectionStatus = Literal["READY", "NO_MATCH", "GATE_A_REQUIRED"]


class LocalizedTextV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    en: str = Field(min_length=1, max_length=500)
    vi: str = Field(min_length=1, max_length=500)


class LocalizedAliasesV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    en: tuple[str, ...] = ()
    vi: tuple[str, ...] = ()


class TopicAssetFrameV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class TopicAssetProvenanceV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    source_type: Literal["BUILTIN_IMAGEGEN_OUTPUT"] = Field(alias="sourceType")
    source_manifest: str | None = Field(default=None, alias="sourceManifest")
    generator_output_id: str | None = Field(default=None, alias="generatorOutputId")
    generated_at_utc: str | None = Field(default=None, alias="generatedAtUtc")
    prompt_id: str | None = Field(default=None, alias="promptId")
    asset_file: str = Field(alias="assetFile", min_length=1)
    atlas_sha256: str = Field(alias="atlasSha256", pattern=r"^[a-f0-9]{64}$")
    license_status: Literal["REVIEW_REQUIRED", "CLEARED"] = Field(alias="licenseStatus")
    rights_basis: str = Field(alias="rightsBasis", min_length=1)


class TopicAssetDescriptorV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    asset_id: str = Field(alias="assetId", min_length=1, max_length=160)
    atlas_id: str = Field(alias="atlasId", min_length=1, max_length=100)
    family: str = Field(min_length=1, max_length=100)
    semantic_category: str = Field(alias="semanticCategory", min_length=1, max_length=100)
    label: LocalizedTextV1
    aliases: LocalizedAliasesV1
    visual_description: LocalizedTextV1 = Field(alias="visualDescription")
    topic_tags: tuple[str, ...] = Field(alias="topicTags", min_length=1)
    render_role: RenderRole = Field(alias="renderRole")
    confusable_with: tuple[str, ...] = Field(alias="confusableWith")
    intended_use: str = Field(alias="intendedUse", min_length=1, max_length=300)
    style_profile_ids: tuple[str, ...] = Field(alias="styleProfileIds", min_length=1)
    frame: TopicAssetFrameV1
    review_status: ReviewStatus = Field(alias="reviewStatus")
    runtime_eligible: bool = Field(alias="runtimeEligible")
    provenance: TopicAssetProvenanceV1

    @model_validator(mode="after")
    def enforce_review_gate(self) -> TopicAssetDescriptorV1:
        if self.runtime_eligible and self.review_status not in {"APPROVED", "APPLIED"}:
            raise ValueError("only visually approved or applied assets may be runtime eligible")
        if self.review_status == "REVIEW_PENDING" and self.runtime_eligible:
            raise ValueError("review-pending assets must never be runtime eligible")
        if self.runtime_eligible and self.provenance.license_status != "CLEARED":
            raise ValueError("runtime eligibility requires a cleared rights/license review")
        return self


class AdultConfirmedTopicV1(BaseModel):
    """Selector input; intentionally has no media URI, image, child profile, or free-form claims."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    gate_a_confirmed: bool = Field(alias="gateAConfirmed")
    topic_labels: tuple[str, ...] = Field(alias="topicLabels", min_length=1, max_length=5)
    topic_tags: tuple[str, ...] = Field(default=(), alias="topicTags", max_length=20)
    locale: Literal["en", "vi"] = "vi"
    style_profile_id: str = Field(default="flat-childlike-doodle-v1", alias="styleProfileId")
    requested_roles: tuple[RenderRole, ...] = Field(default=(), alias="requestedRoles")
    max_candidates: int = Field(default=8, alias="maxCandidates", ge=1, le=8)


class TopicAssetCandidateV1(BaseModel):
    """Minimal semantic descriptor sent to a model; excludes paths, hashes, and frame geometry."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    asset_id: str = Field(alias="assetId", min_length=1)
    family: str = Field(min_length=1)
    label: LocalizedTextV1
    aliases: LocalizedAliasesV1
    visual_description: LocalizedTextV1 = Field(alias="visualDescription")
    topic_tags: tuple[str, ...] = Field(alias="topicTags")
    render_role: RenderRole = Field(alias="renderRole")
    confusable_with: tuple[str, ...] = Field(alias="confusableWith")
    intended_use: str = Field(alias="intendedUse")


class TopicAssetAuthoringQueueProposalV1(BaseModel):
    """Safe authoring-time miss record; contains no child media or generated asset."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    contract_name: Literal["PixiTopicAssetAuthoringQueueProposalV1"] = (
        "PixiTopicAssetAuthoringQueueProposalV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    status: Literal["AWAITING_HUMAN_AUTHORING_REVIEW"] = "AWAITING_HUMAN_AUTHORING_REVIEW"
    topic_labels: tuple[str, ...] = Field(alias="topicLabels", min_length=1)
    topic_tags: tuple[str, ...] = Field(default=(), alias="topicTags")
    reason_code: Literal[
        "NO_APPROVED_ASSETS", "NO_COMPATIBLE_APPROVED_ASSETS", "NO_SEMANTIC_MATCH"
    ] = Field(alias="reasonCode")
    original_art_preserved: Literal[True] = Field(default=True, alias="originalArtPreserved")
    child_media_included: Literal[False] = Field(default=False, alias="childMediaIncluded")
    provider_generation_requested: Literal[False] = Field(
        default=False, alias="providerGenerationRequested"
    )


class TopicAssetCandidateContextV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    contract_name: Literal["PixiTopicCandidateContextV1"] = "PixiTopicCandidateContextV1"
    contract_version: Literal["1.0"] = "1.0"
    status: SelectionStatus
    confirmed_topic_labels: tuple[str, ...] = Field(alias="confirmedTopicLabels", min_length=1)
    confirmed_topic_tags: tuple[str, ...] = Field(default=(), alias="confirmedTopicTags")
    candidates: tuple[TopicAssetCandidateV1, ...] = ()
    miss_reason: (
        Literal[
            "NO_APPROVED_ASSETS",
            "NO_COMPATIBLE_APPROVED_ASSETS",
            "NO_SEMANTIC_MATCH",
            "GATE_A_REQUIRED",
        ]
        | None
    ) = Field(default=None, alias="missReason")
    authoring_queue_proposal: TopicAssetAuthoringQueueProposalV1 | None = Field(
        default=None, alias="authoringQueueProposal"
    )

    @model_validator(mode="after")
    def validate_context_state(self) -> TopicAssetCandidateContextV1:
        if self.status == "READY" and (
            not self.candidates
            or self.miss_reason is not None
            or self.authoring_queue_proposal is not None
        ):
            raise ValueError("ready context needs candidates without a miss or queue proposal")
        if self.status == "GATE_A_REQUIRED" and (
            self.candidates
            or self.miss_reason != "GATE_A_REQUIRED"
            or self.authoring_queue_proposal is not None
        ):
            raise ValueError("Gate A miss cannot create an authoring queue proposal")
        if self.status == "NO_MATCH" and (
            self.candidates
            or self.miss_reason
            not in {
                "NO_APPROVED_ASSETS",
                "NO_COMPATIBLE_APPROVED_ASSETS",
                "NO_SEMANTIC_MATCH",
            }
            or self.authoring_queue_proposal is None
            or self.authoring_queue_proposal.reason_code != self.miss_reason
        ):
            raise ValueError("topic no-match needs a typed authoring queue proposal")
        return self


class TopicAssetSelectionOutputV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    asset_ids: tuple[str, ...] = Field(alias="assetIds", max_length=4)
    no_match: bool = Field(alias="noMatch")

    @model_validator(mode="after")
    def validate_no_match_flag(self) -> TopicAssetSelectionOutputV1:
        if self.no_match != (len(self.asset_ids) == 0):
            raise ValueError("noMatch must be true exactly when assetIds is empty")
        if len(set(self.asset_ids)) != len(self.asset_ids):
            raise ValueError("assetIds must be unique")
        return self


__all__ = [
    "AdultConfirmedTopicV1",
    "LocalizedAliasesV1",
    "LocalizedTextV1",
    "TopicAssetCandidateContextV1",
    "TopicAssetCandidateV1",
    "TopicAssetAuthoringQueueProposalV1",
    "TopicAssetDescriptorV1",
    "TopicAssetFrameV1",
    "TopicAssetProvenanceV1",
    "TopicAssetSelectionOutputV1",
]
