"""Strict BE2-07 0.1-candidate DTOs. Server authority cannot be supplied by commands."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]


def _text(value: str) -> str:
    if not value.strip() or any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ValueError("text must be nonblank without control characters")
    return value


ShortText = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_text)]
ClaimText = Annotated[str, Field(min_length=1, max_length=400), AfterValidator(_text)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class StrictKnowledgeV1(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class TeacherTopicRefV1(StrictKnowledgeV1):
    kind: Literal["teacher_topic"]
    ref: OpaqueId
    revision: int = Field(ge=1)


class ConfirmedMeaningRefV1(StrictKnowledgeV1):
    kind: Literal["confirmed_meaning"]
    ref: OpaqueId
    revision: int = Field(ge=1)


KnowledgeBasisRefV1 = Annotated[
    TeacherTopicRefV1 | ConfirmedMeaningRefV1, Field(discriminator="kind")
]


class CreateKnowledgeBundleV1(StrictKnowledgeV1):
    session_id: OpaqueId
    basis_ref: KnowledgeBasisRefV1
    expected_context_revision: int = Field(ge=0)
    expected_audience_revision: int = Field(ge=0)
    catalog_claim_ids: tuple[OpaqueId, ...] = Field(default=(), max_length=24)
    imagined_refs: tuple[OpaqueId, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def unique_refs(self) -> CreateKnowledgeBundleV1:
        if len(set(self.catalog_claim_ids)) != len(self.catalog_claim_ids):
            raise ValueError("duplicate catalog claim refs")
        if len(set(self.imagined_refs)) != len(self.imagined_refs):
            raise ValueError("duplicate imagined refs")
        return self


class KnowledgeSourceRefV1(StrictKnowledgeV1):
    source_id: OpaqueId
    revision: int = Field(ge=1)
    sha256: Sha256


class ClaimEditV1(StrictKnowledgeV1):
    claim_id: OpaqueId
    revision: int = Field(ge=1)
    text: ClaimText
    source_refs: tuple[KnowledgeSourceRefV1, ...] = Field(min_length=1, max_length=12)
    attestation_reason: ShortText | None = None

    @model_validator(mode="after")
    def unique_sources(self) -> ClaimEditV1:
        if len({ref.source_id for ref in self.source_refs}) != len(self.source_refs):
            raise ValueError("duplicate source refs")
        return self


class FactSectionV1(StrictKnowledgeV1):
    kind: Literal["fact"] = "fact"
    section_id: OpaqueId
    claim_refs: tuple[OpaqueId, ...] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def unique_claim_refs(self) -> FactSectionV1:
        if len(set(self.claim_refs)) != len(self.claim_refs):
            raise ValueError("duplicate claim refs")
        return self


class StorySectionV1(StrictKnowledgeV1):
    kind: Literal["story"] = "story"
    section_id: OpaqueId
    imagined_refs: tuple[OpaqueId, ...] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def unique_imagined_refs(self) -> StorySectionV1:
        if len(set(self.imagined_refs)) != len(self.imagined_refs):
            raise ValueError("duplicate imagined refs")
        return self


ScriptSectionV1 = Annotated[FactSectionV1 | StorySectionV1, Field(discriminator="kind")]


class EditKnowledgeBundleV1(StrictKnowledgeV1):
    expected_context_revision: int = Field(ge=0)
    expected_audience_revision: int = Field(ge=0)
    correction_reason: ShortText
    claims: tuple[ClaimEditV1, ...] | None = Field(default=None, max_length=24)
    sections: tuple[ScriptSectionV1, ...] | None = Field(default=None, max_length=32)
    imagined_refs: tuple[OpaqueId, ...] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def changed_fields(self) -> EditKnowledgeBundleV1:
        if self.claims is None and self.sections is None and self.imagined_refs is None:
            raise ValueError("at least one content field is required")
        for refs in (
            tuple(claim.claim_id for claim in self.claims) if self.claims is not None else (),
            tuple(section.section_id for section in self.sections)
            if self.sections is not None
            else (),
            self.imagined_refs or (),
        ):
            if len(set(refs)) != len(refs):
                raise ValueError("duplicate content refs")
        return self


class KnowledgeClaimRecordV1(ClaimEditV1):
    verification_state: Literal["catalog_reviewed", "teacher_attested"]
    attested_by: OpaqueId | None = None


class ImaginedElementRecordV1(StrictKnowledgeV1):
    ref: OpaqueId
    revision: int = Field(ge=1)
    text: ShortText


class ProjectedScriptSectionV1(StrictKnowledgeV1):
    section_id: OpaqueId
    kind: Literal["fact", "story"]
    refs: tuple[OpaqueId, ...] = Field(min_length=1, max_length=24)
    text: Annotated[str, Field(min_length=1, max_length=16000)]


class KnowledgeScriptProjectionV1(StrictKnowledgeV1):
    knowledge_claims: tuple[KnowledgeClaimRecordV1, ...] = Field(max_length=24)
    child_imagined_elements: tuple[ImaginedElementRecordV1, ...] = Field(max_length=8)
    script_sections: tuple[ProjectedScriptSectionV1, ...] = Field(max_length=32)
    script_text: Annotated[str, Field(max_length=16000)]

    @model_validator(mode="after")
    def exact_projection(self) -> KnowledgeScriptProjectionV1:
        from sketch2life.domain.knowledge_bundle import (
            FactSection,
            ImaginedElementV1,
            KnowledgeClaimV1,
            SourceRefV1,
            StorySection,
            project_script,
        )

        claims = tuple(
            KnowledgeClaimV1(
                item.claim_id,
                item.revision,
                item.text,
                tuple(
                    SourceRefV1(pin.source_id, pin.revision, pin.sha256) for pin in item.source_refs
                ),
                item.verification_state,
                item.attested_by,
                item.attestation_reason,
            )
            for item in self.knowledge_claims
        )
        imagined = tuple(
            ImaginedElementV1(item.ref, item.revision, item.text)
            for item in self.child_imagined_elements
        )
        sections = tuple(
            FactSection(item.section_id, item.refs)
            if item.kind == "fact"
            else StorySection(item.section_id, item.refs)
            for item in self.script_sections
        )
        projected, flat = project_script(sections, claims, imagined)
        if any(
            actual.text != expected.text
            for actual, expected in zip(self.script_sections, projected, strict=True)
        ):
            raise ValueError("section text must equal exact claim/imagined projection")
        if self.script_text != flat:
            raise ValueError("flat script must equal exact section projection")
        return self


class ReviewedSourceRecordV1(StrictKnowledgeV1):
    ref: KnowledgeSourceRefV1
    title: ShortText
    locator: ShortText
    reviewed_at: ShortText
    topic: ShortText
    age_bands: tuple[OpaqueId, ...] = Field(min_length=1, max_length=32)
    state: Literal["reviewed", "unreviewed"]
    recalled: bool


class ContributorRecordV1(StrictKnowledgeV1):
    participant_id: OpaqueId
    purpose_code: Literal["knowledge_media"]
    snapshot_ref: OpaqueId


class AudienceMemberRecordV1(StrictKnowledgeV1):
    participant_id: OpaqueId
    age_band: OpaqueId


class KnowledgeBasisSnapshotRecordV1(StrictKnowledgeV1):
    ref: OpaqueId
    kind: Literal["teacher_topic", "confirmed_meaning"]
    revision: int = Field(ge=1)
    organization_id: OpaqueId
    session_id: OpaqueId
    topic: ShortText
    source_snapshot_refs: tuple[OpaqueId, ...] = Field(max_length=32)
    contributors: tuple[ContributorRecordV1, ...] = Field(max_length=32)
    imagined_elements: tuple[ImaginedElementRecordV1, ...] = Field(max_length=8)
    confirmation_ref: OpaqueId | None

    @model_validator(mode="after")
    def trusted_metadata(self) -> KnowledgeBasisSnapshotRecordV1:
        from sketch2life.domain.knowledge_bundle import (
            ContributorV1,
            ImaginedElementV1,
            KnowledgeBasisV1,
        )

        KnowledgeBasisV1(
            self.ref,
            self.kind,
            self.revision,
            self.organization_id,
            self.session_id,
            self.topic,
            self.source_snapshot_refs,
            tuple(
                ContributorV1(item.participant_id, item.purpose_code, item.snapshot_ref)
                for item in self.contributors
            ),
            tuple(
                ImaginedElementV1(item.ref, item.revision, item.text)
                for item in self.imagined_elements
            ),
            confirmation_ref=self.confirmation_ref,
        )
        return self


class CorrectionRecordV1(StrictKnowledgeV1):
    correction_ref: OpaqueId
    author_principal_id: OpaqueId
    reason: ShortText
    from_version: int = Field(ge=1)
    to_version: int = Field(ge=2)

    @model_validator(mode="after")
    def consecutive_versions(self) -> CorrectionRecordV1:
        if self.to_version != self.from_version + 1:
            raise ValueError("correction versions must be consecutive")
        return self


class KnowledgeBundleRecordV1(KnowledgeScriptProjectionV1):
    contract_name: Literal["KnowledgeBundle"] = "KnowledgeBundle"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    bundle_id: OpaqueId
    bundle_version: int = Field(ge=1)
    organization_id: OpaqueId
    session_id: OpaqueId
    audience_context_ref: OpaqueId
    audience_members: tuple[AudienceMemberRecordV1, ...] = Field(min_length=1, max_length=32)
    context_revision: int = Field(ge=0)
    audience_revision: int = Field(ge=0)
    source_snapshot_refs: tuple[OpaqueId, ...] = Field(max_length=32)
    confirmed_topic: ShortText
    basis_ref: KnowledgeBasisRefV1
    confirmation_ref: OpaqueId | None
    basis_snapshot: KnowledgeBasisSnapshotRecordV1
    source_records: tuple[ReviewedSourceRecordV1, ...] = Field(max_length=12)
    editorial_revision: int = Field(ge=1)
    editorial_state: Literal["draft"] = "draft"
    created_by: OpaqueId
    created_at: ShortText
    teacher_corrections: tuple[CorrectionRecordV1, ...]
    contributors: tuple[ContributorRecordV1, ...] = Field(max_length=32)
    content_origin: Literal["generic", "child_derived"]
    policy_ref: OpaqueId
    bundle_hash: Sha256
    readiness: Literal["generation_ready", "needs_content_action", "unavailable"]
    action_code: OpaqueId | None = None

    @model_validator(mode="after")
    def provenance_and_sources(self) -> KnowledgeBundleRecordV1:
        from sketch2life.domain.knowledge_bundle import content_readiness, imagined_literal_overlap

        snapshot = self.basis_snapshot
        if any(
            imagined_literal_overlap(claim.text, literal.text)
            for literal in snapshot.imagined_elements
            for claim in self.knowledge_claims
        ):
            raise ValueError("IMAGINED_AS_FACT: full trusted basis literal cannot appear in facts")
        expected_readiness, expected_action = content_readiness(
            bool(self.knowledge_claims),
            any(section.kind == "fact" for section in self.script_sections),
        )
        if self.readiness == "unavailable":
            if self.action_code is None:
                raise ValueError("unavailable readiness requires an explicit action")
        elif (self.readiness, self.action_code) != (expected_readiness, expected_action):
            raise ValueError("readiness and action must match structural content")
        if (
            snapshot.organization_id,
            snapshot.session_id,
            snapshot.kind,
            snapshot.ref,
            snapshot.revision,
            snapshot.topic,
            snapshot.source_snapshot_refs,
            snapshot.contributors,
            snapshot.confirmation_ref,
        ) != (
            self.organization_id,
            self.session_id,
            self.basis_ref.kind,
            self.basis_ref.ref,
            self.basis_ref.revision,
            self.confirmed_topic,
            self.source_snapshot_refs,
            self.contributors,
            self.confirmation_ref,
        ):
            raise ValueError("basis snapshot must match exact record provenance")
        if any(item not in snapshot.imagined_elements for item in self.child_imagined_elements):
            raise ValueError("imagined selections must come from exact trusted basis")
        if self.editorial_revision != self.bundle_version:
            raise ValueError("editorial revision must match content revision")
        if len(self.teacher_corrections) != self.bundle_version - 1:
            raise ValueError("correction history must be cumulative")
        if any(
            item.from_version != index + 1 or item.to_version != index + 2
            for index, item in enumerate(self.teacher_corrections)
        ):
            raise ValueError("correction history must be consecutive")
        if self.basis_ref.kind == "confirmed_meaning":
            if (
                self.content_origin != "child_derived"
                or not self.contributors
                or not self.confirmation_ref
            ):
                raise ValueError("confirmed meaning requires exact child provenance")
        elif (
            self.content_origin != "generic"
            or self.contributors
            or self.source_snapshot_refs
            or self.confirmation_ref is not None
            or self.child_imagined_elements
        ):
            raise ValueError("generic basis cannot carry child provenance")
        for refs in (
            tuple(item.participant_id for item in self.audience_members),
            tuple(item.participant_id for item in self.contributors),
            tuple(item.ref.source_id for item in self.source_records),
            tuple(item.correction_ref for item in self.teacher_corrections),
            self.source_snapshot_refs,
        ):
            if len(set(refs)) != len(refs):
                raise ValueError("duplicate provenance refs")
        selected = {item.ref.source_id: item for item in self.source_records}
        audience_ids = {item.participant_id for item in self.audience_members}
        if any(
            item.participant_id not in audience_ids
            or item.snapshot_ref not in self.source_snapshot_refs
            for item in self.contributors
        ):
            raise ValueError("contributor membership and snapshot provenance required")
        referenced = {pin.source_id for claim in self.knowledge_claims for pin in claim.source_refs}
        if referenced != set(selected):
            raise ValueError("source records must equal referenced sources")
        for claim in self.knowledge_claims:
            for pin in claim.source_refs:
                if pin != selected[pin.source_id].ref:
                    raise ValueError("claim source pins must match exact source records")
        if self.readiness == "generation_ready" and (
            not self.knowledge_claims
            or not any(section.kind == "fact" for section in self.script_sections)
            or any(
                item.state != "reviewed"
                or item.recalled
                or item.topic != self.confirmed_topic
                or any(member.age_band not in item.age_bands for member in self.audience_members)
                for item in self.source_records
            )
        ):
            raise ValueError("generation ready requires sourced facts")
        return self


class KnowledgeBundleExportV1(KnowledgeBundleRecordV1):
    canonical_json: Annotated[str, Field(min_length=1, max_length=196608)]
    canonical_rules_version: Literal["knowledge-canonical-v1"] = "knowledge-canonical-v1"

    @model_validator(mode="after")
    def exact_canonical_identity(self) -> KnowledgeBundleExportV1:
        from sketch2life.domain.knowledge_bundle import canonical_bytes

        encoded = self.canonical_json.encode("utf-8")
        if hashlib.sha256(encoded).hexdigest() != self.bundle_hash:
            raise ValueError("canonical bytes hash differs from bundle hash")
        document = self.model_dump(
            mode="json",
            exclude={
                "bundle_hash",
                "readiness",
                "action_code",
                "canonical_json",
            },
        )
        if canonical_bytes(document) != encoded:
            raise ValueError("canonical content differs from exact exported record")
        return self


class ExactKnowledgeRefV1(StrictKnowledgeV1):
    bundle_id: OpaqueId
    bundle_version: int = Field(ge=1)
    bundle_hash: Sha256


class KnowledgeSupersededV1(StrictKnowledgeV1):
    contract_name: Literal["KnowledgeSupersededV1"] = "KnowledgeSupersededV1"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    event_id: OpaqueId
    organization_id: OpaqueId
    session_id: OpaqueId
    old_bundle: ExactKnowledgeRefV1
    new_bundle: ExactKnowledgeRefV1
    correction_ref: OpaqueId
    operation_id: OpaqueId

    @model_validator(mode="after")
    def exact_successor(self) -> KnowledgeSupersededV1:
        if self.old_bundle.bundle_id != self.new_bundle.bundle_id:
            raise ValueError("supersession must name the same bundle")
        if self.new_bundle.bundle_version != self.old_bundle.bundle_version + 1:
            raise ValueError("supersession must name consecutive exact versions")
        return self


def record_from_version(
    version: KnowledgeBundleVersion,
    readiness: Literal["generation_ready", "needs_content_action", "unavailable"] | None = None,
    action_code: str | None = None,
) -> KnowledgeBundleRecordV1:
    from sketch2life.domain.knowledge_bundle import content_readiness, verify_version

    verify_version(version)
    document = json.loads(version.canonical_bytes)
    del document["canonical_rules_version"]
    expected_readiness, expected_action = content_readiness(
        bool(version.knowledge_claims),
        any(section.kind == "fact" for section in version.projected_sections),
    )
    if readiness is None:
        readiness = expected_readiness
    if action_code is None and readiness != "unavailable":
        action_code = expected_action
    # JSON round-trip is this internal producer boundary, not a claim to reject duplicate
    # keys lost by an arbitrary external parser. The exact canonical bytes are verified.
    return KnowledgeBundleRecordV1.model_validate_json(
        json.dumps(
            {
                **document,
                "bundle_hash": version.bundle_hash,
                "readiness": readiness,
                "action_code": action_code,
            }
        )
    )


def export_from_version(version: KnowledgeBundleVersion) -> KnowledgeBundleExportV1:
    record = record_from_version(version)
    return KnowledgeBundleExportV1.model_validate(
        {
            **record.model_dump(),
            "canonical_json": version.canonical_bytes.decode("utf-8"),
        }
    )


if TYPE_CHECKING:
    from sketch2life.domain.knowledge_bundle import KnowledgeBundleVersion
