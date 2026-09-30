"""Explicit, session-scoped child learning context for deterministic P1 discovery.

This contract intentionally carries no child name, free text, media-derived trait,
diagnosis, or durable-storage identifier. It is supplied afresh for one options read.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import Field, field_validator, model_validator

from sketch2life.contracts.schemas.child_preference_classification import PreferenceConceptId
from sketch2life.contracts.schemas.p1_experience import P1ContractBase, VersionedRefV1

_MATERIAL_OPTION_ID = re.compile(r"(?:GMAT-[A-Z0-9-]+|MAT_[A-Z0-9_]+)")


class AdultConfirmedProgressV1(P1ContractBase):
    activity_id: str = Field(pattern=r"^ACT-[0-9]{4}$")
    objective_id: str = Field(pattern=r"^OBJ_[A-Z0-9_]{2,100}$")
    confirmed_at: date
    confirmed_by: Literal["CAREGIVER", "GUIDE"]


class ChildLearningProfileContextV1(P1ContractBase):
    contract_name: Literal["ChildLearningProfileContextV1"] = "ChildLearningProfileContextV1"
    contract_version: Literal["1.0"] = "1.0"
    profile_declared_by: Literal["CAREGIVER", "GUIDE"]
    profile_recorded_at: datetime
    interests: tuple[str, ...] = Field(default=(), max_length=12)
    dislikes: tuple[str, ...] = Field(default=(), max_length=12)
    adult_confirmed_progress: tuple[AdultConfirmedProgressV1, ...] = Field(
        default=(), max_length=12
    )
    readiness_ids: tuple[str, ...] | None = Field(default=None, max_length=24)
    available_material_option_ids: tuple[str, ...] | None = Field(default=None, max_length=48)
    adult_supervision_available: Literal["NONE", "NEARBY", "DIRECT"] = "NEARBY"
    learning_support_ids: tuple[
        Literal["HANDS_ON", "MOVEMENT", "VISUAL_SEQUENCE", "OBSERVATION"], ...
    ] = Field(default=(), max_length=4)

    @field_validator("profile_recorded_at")
    @classmethod
    def validate_profile_recorded_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("profile recorded_at must include a timezone")
        if value.astimezone(UTC) > datetime.now(UTC) + timedelta(seconds=30):
            raise ValueError("profile recorded_at cannot be future-dated")
        return value

    @field_validator("interests", "dislikes")
    @classmethod
    def validate_concept_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(len(value) > 64 or not value.replace("_", "").isalnum() or not value.isupper()
               for value in values):
            raise ValueError("profile concepts must be bounded catalog identifiers")
        return values

    @field_validator("readiness_ids")
    @classmethod
    def validate_readiness_ids(cls, values: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if values is not None and any(
            len(value) > 80 or not value.startswith("READY_") or not value.isupper()
            for value in values
        ):
            raise ValueError("readiness values must be catalog identifiers")
        return values

    @field_validator("available_material_option_ids")
    @classmethod
    def validate_material_ids(cls, values: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if values is not None and any(
            len(value) > 80 or _MATERIAL_OPTION_ID.fullmatch(value) is None
            for value in values
        ):
            raise ValueError("material values must be catalog identifiers")
        return values

    @model_validator(mode="after")
    def reject_duplicates_and_future_progress(self) -> ChildLearningProfileContextV1:
        for values in (
            self.interests,
            self.dislikes,
            self.readiness_ids or (),
            self.available_material_option_ids or (),
            self.learning_support_ids,
        ):
            if len(values) != len(set(values)):
                raise ValueError("profile selections must not contain duplicates")
        if set(self.interests) & set(self.dislikes):
            raise ValueError("an explicit interest cannot also be a dislike")
        if any(item.confirmed_at > date.today() for item in self.adult_confirmed_progress):
            raise ValueError("adult-confirmed progress cannot be future-dated")
        progress_refs = {
            (item.activity_id, item.objective_id)
            for item in self.adult_confirmed_progress
        }
        if len(progress_refs) != len(self.adult_confirmed_progress):
            raise ValueError("adult-confirmed progress must be unique")
        return self


class P1ContextOptionsRequestV1(P1ContractBase):
    contract_name: Literal["P1ContextOptionsRequestV1"] = "P1ContextOptionsRequestV1"
    contract_version: Literal["1.0"] = "1.0"
    age_months: int = Field(ge=0, le=155)
    child_profile: ChildLearningProfileContextV1 | None = None


class ChildLearningProfileContextV2(P1ContractBase):
    """Minimal session-scoped preference/context fields; no history or supervision level."""

    contract_name: Literal["ChildLearningProfileContextV2"] = "ChildLearningProfileContextV2"
    contract_version: Literal["2.0"] = "2.0"
    profile_declared_by: Literal["CAREGIVER", "GUIDE"]
    profile_recorded_at: datetime
    preference_tags_confirmed: bool = False
    interests: tuple[PreferenceConceptId, ...] = Field(default=(), max_length=12)
    dislikes: tuple[PreferenceConceptId, ...] = Field(default=(), max_length=12)
    readiness_ids: tuple[str, ...] | None = Field(default=None, max_length=24)
    available_material_option_ids: tuple[str, ...] | None = Field(default=None, max_length=48)
    learning_support_ids: tuple[
        Literal["HANDS_ON", "MOVEMENT", "VISUAL_SEQUENCE", "OBSERVATION"], ...
    ] = Field(default=(), max_length=4)

    @field_validator("profile_recorded_at")
    @classmethod
    def validate_profile_recorded_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("profile recorded_at must include a timezone")
        if value.astimezone(UTC) > datetime.now(UTC) + timedelta(seconds=30):
            raise ValueError("profile recorded_at cannot be future-dated")
        return value

    @field_validator("interests", "dislikes")
    @classmethod
    def validate_concept_ids(
        cls, values: tuple[PreferenceConceptId, ...]
    ) -> tuple[PreferenceConceptId, ...]:
        return values

    @field_validator("readiness_ids")
    @classmethod
    def validate_readiness_ids(cls, values: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if values is not None and any(
            len(value) > 80 or not value.startswith("READY_") or not value.isupper()
            for value in values
        ):
            raise ValueError("readiness values must be catalog identifiers")
        return values

    @field_validator("available_material_option_ids")
    @classmethod
    def validate_material_ids(cls, values: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if values is not None and any(
            len(value) > 80 or _MATERIAL_OPTION_ID.fullmatch(value) is None
            for value in values
        ):
            raise ValueError("material values must be catalog identifiers")
        return values

    @model_validator(mode="after")
    def reject_duplicates_and_conflicts(self) -> ChildLearningProfileContextV2:
        for values in (
            self.interests,
            self.dislikes,
            self.readiness_ids or (),
            self.available_material_option_ids or (),
            self.learning_support_ids,
        ):
            if len(values) != len(set(values)):
                raise ValueError("profile selections must not contain duplicates")
        if set(self.interests) & set(self.dislikes):
            raise ValueError("an explicit interest cannot also be a dislike")
        if (self.interests or self.dislikes) and not self.preference_tags_confirmed:
            raise ValueError("preference tags require adult confirmation")
        return self


class ActivityContextCandidateV2(P1ContractBase):
    contract_name: Literal["ActivityContextCandidateV2"] = "ActivityContextCandidateV2"
    contract_version: Literal["2.0"] = "2.0"
    template_ref: VersionedRefV1
    activity_ref: VersionedRefV1
    title_vi: str = Field(min_length=1, max_length=160)
    summary_vi: str = Field(min_length=1, max_length=500)
    age_months_min: int = Field(ge=0, le=155)
    age_months_max: int = Field(ge=0, le=155)
    readiness_ids: tuple[str, ...] = ()
    readiness_metadata_status: Literal["AUTHORED", "UNSPECIFIED"]
    prerequisite_activity_ids: tuple[str, ...] = ()
    material_option_ids: tuple[str, ...] = Field(default=(), max_length=48)
    material_option_groups: tuple[tuple[str, ...], ...] = ()
    material_labels_by_id: dict[str, str] = Field(default_factory=dict, max_length=48)
    minimum_supervision: Literal["NONE", "NEARBY", "DIRECT"]
    supervision_label_vi: str = Field(min_length=1, max_length=120)
    policy_constraints: tuple[str, ...] = ()


class ActivityContextCandidateSetV2(P1ContractBase):
    contract_name: Literal["ActivityContextCandidateSetV2"] = "ActivityContextCandidateSetV2"
    contract_version: Literal["2.0"] = "2.0"
    session_id: str = Field(min_length=1, max_length=120)
    expected_session_version: int = Field(ge=1)
    age_months: int = Field(ge=0, le=155)
    confirmed_anchor_label: str = Field(min_length=1, max_length=200)
    candidates: tuple[ActivityContextCandidateV2, ...] = Field(max_length=3)


class P1ContextOptionsRequestV2(P1ContractBase):
    contract_name: Literal["P1ContextOptionsRequestV2"] = "P1ContextOptionsRequestV2"
    contract_version: Literal["2.0"] = "2.0"
    age_months: int = Field(ge=0, le=155)
    child_profile: ChildLearningProfileContextV2
    adult_participating: Literal[True]
    caregiver_participating: bool = False
    candidate_activity_ids: tuple[str, ...] = Field(min_length=1, max_length=3)
    supervision_confirmed_activity_ids: tuple[str, ...] = Field(min_length=1, max_length=3)

    @field_validator("candidate_activity_ids", "supervision_confirmed_activity_ids")
    @classmethod
    def validate_activity_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not re.fullmatch(r"ACT-[0-9]{4}", value) for value in values):
            raise ValueError("activity references must be catalog IDs")
        if len(values) != len(set(values)):
            raise ValueError("activity references must be unique")
        return values

    @model_validator(mode="after")
    def supervision_must_be_confirmed_per_candidate(self) -> P1ContextOptionsRequestV2:
        if self.age_months < 36 and not self.caregiver_participating:
            raise ValueError("children under three require a participating caregiver")
        if not set(self.supervision_confirmed_activity_ids) <= set(self.candidate_activity_ids):
            raise ValueError("supervision can only be confirmed for displayed candidates")
        return self
