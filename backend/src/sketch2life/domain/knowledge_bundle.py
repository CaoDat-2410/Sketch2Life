"""Pure BE2-07 candidate knowledge rules; all authority is supplied by trusted ports.

The enriched fixtures are not a Vision/BE1 adapter. Teacher attestation is accountable
source attribution under the named offline policy, never semantic machine verification.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from typing import Literal

from sketch2life.domain.vision_context import strict_canonical_sha256

ID_MAX = 120
SHORT_MAX = 200
CLAIM_MAX = 400
CLAIMS_MAX = 24
SOURCES_MAX = 12
SECTIONS_MAX = 32
IMAGINED_MAX = 8
AUDIENCE_MAX = 32
SCRIPT_MAX = 16000
DOCUMENT_MAX = 196608
PURPOSE = "knowledge_media"
FIXTURE_POLICY = "knowledge-offline-policy-v1"
CONTRACT_VERSION = "0.1-candidate"
CANONICAL_RULES_VERSION = "knowledge-canonical-v1"
_ID = re.compile(r"[A-Za-z0-9_.:-]{1,120}")
# Unicode 15.0 Default_Ignorable_Code_Point, with contiguous property ranges merged.
# https://www.unicode.org/Public/15.0.0/ucd/DerivedCoreProperties.txt
_DEFAULT_IGNORABLE_RANGES = (
    (0x00AD, 0x00AD),
    (0x034F, 0x034F),
    (0x061C, 0x061C),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180F),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x206F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFEFF, 0xFEFF),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
)


class KnowledgeRuleViolation(ValueError):
    """Closed domain rejection with a safe, stable reason code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise KnowledgeRuleViolation(code)


def opaque(value: str) -> None:
    require(type(value) is str and _ID.fullmatch(value) is not None, "INVALID_REFERENCE")


def has_forbidden_text_controls(value: str) -> bool:
    return any(unicodedata.category(char) == "Cc" and char not in "\n\t" for char in value)


def text(value: str, limit: int = SHORT_MAX) -> None:
    require(type(value) is str and 0 < len(value) <= limit and bool(value.strip()), "TEXT_BOUNDS")
    require(not has_forbidden_text_controls(value), "TEXT_CONTROL")


def revision(value: int, minimum: int = 1) -> None:
    require(type(value) is int and value >= minimum, "INVALID_REVISION")


def unique(values: tuple[str, ...], maximum: int, *, nonempty: bool = False) -> None:
    require(type(values) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
    require((not nonempty or bool(values)) and len(values) <= maximum, "COLLECTION_BOUNDS")
    require(len(set(values)) == len(values), "DUPLICATE_REFERENCE")
    for value in values:
        opaque(value)


@dataclass(frozen=True)
class BasisRef:
    kind: Literal["teacher_topic", "confirmed_meaning"]
    ref: str
    revision: int

    def __post_init__(self) -> None:
        require(self.kind in {"teacher_topic", "confirmed_meaning"}, "INVALID_BASIS_KIND")
        opaque(self.ref)
        revision(self.revision)


@dataclass(frozen=True)
class ContributorV1:
    participant_id: str
    purpose_code: str
    snapshot_ref: str

    def __post_init__(self) -> None:
        for value in (self.participant_id, self.purpose_code, self.snapshot_ref):
            opaque(value)


@dataclass(frozen=True)
class ImaginedElementV1:
    ref: str
    revision: int
    text: str

    def __post_init__(self) -> None:
        opaque(self.ref)
        revision(self.revision)
        text(self.text)


@dataclass(frozen=True)
class KnowledgeBasisV1:
    ref: str
    kind: Literal["teacher_topic", "confirmed_meaning"]
    revision: int
    organization_id: str
    session_id: str
    topic: str
    source_snapshot_refs: tuple[str, ...] = ()
    contributors: tuple[ContributorV1, ...] = ()
    imagined_elements: tuple[ImaginedElementV1, ...] = ()
    confirmed: bool = True
    applicable: bool = True
    confirmation_ref: str | None = None

    def __post_init__(self) -> None:
        BasisRef(self.kind, self.ref, self.revision)
        opaque(self.organization_id)
        opaque(self.session_id)
        text(self.topic)
        unique(self.source_snapshot_refs, AUDIENCE_MAX)
        require(type(self.contributors) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
        require(type(self.imagined_elements) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
        unique(tuple(item.participant_id for item in self.contributors), AUDIENCE_MAX)
        unique(tuple(item.ref for item in self.imagined_elements), IMAGINED_MAX)
        require(type(self.confirmed) is bool and type(self.applicable) is bool, "INVALID_STATE")
        if self.kind == "confirmed_meaning":
            require(self.confirmation_ref is not None, "TRUSTED_CONFIRMATION_REQUIRED")
            assert self.confirmation_ref is not None
            opaque(self.confirmation_ref)
            require(
                bool(self.contributors) and bool(self.source_snapshot_refs),
                "TRUSTED_METADATA_REQUIRED",
            )
            require(
                all(item.snapshot_ref in self.source_snapshot_refs for item in self.contributors),
                "TRUSTED_METADATA_REQUIRED",
            )
        else:
            require(
                not self.contributors
                and not self.imagined_elements
                and not self.source_snapshot_refs
                and self.confirmation_ref is None,
                "GENERIC_PROVENANCE_CONFLICT",
            )


@dataclass(frozen=True)
class AudienceMemberV1:
    participant_id: str
    age_band: str

    def __post_init__(self) -> None:
        opaque(self.participant_id)
        opaque(self.age_band)


@dataclass(frozen=True)
class AudienceContextV1:
    ref: str
    organization_id: str
    session_id: str
    context_revision: int
    audience_revision: int
    members: tuple[AudienceMemberV1, ...]

    def __post_init__(self) -> None:
        for value in (self.ref, self.organization_id, self.session_id):
            opaque(value)
        revision(self.context_revision, 0)
        revision(self.audience_revision, 0)
        require(type(self.members) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
        unique(tuple(item.participant_id for item in self.members), AUDIENCE_MAX, nonempty=True)


def validate_audience(
    audience: AudienceContextV1,
    organization_id: str,
    session_id: str,
    expected_context_revision: int,
    expected_audience_revision: int,
) -> None:
    require(
        (audience.organization_id, audience.session_id) == (organization_id, session_id),
        "SCOPE_MISMATCH",
    )
    require(audience.context_revision == expected_context_revision, "CONTEXT_REVISION_MISMATCH")
    require(audience.audience_revision == expected_audience_revision, "AUDIENCE_REVISION_MISMATCH")


def validate_basis(
    basis: KnowledgeBasisV1,
    requested: BasisRef,
    audience: AudienceContextV1,
    organization_id: str,
    session_id: str,
    contributor_allowed: Callable[[ContributorV1], bool],
) -> None:
    require(
        (basis.organization_id, basis.session_id) == (organization_id, session_id), "SCOPE_MISMATCH"
    )
    require(
        (basis.kind, basis.ref, basis.revision)
        == (requested.kind, requested.ref, requested.revision),
        "BASIS_REVISION_MISMATCH",
    )
    require(basis.confirmed, "BASIS_UNCONFIRMED")
    require(basis.applicable, "BASIS_NOT_APPLICABLE")
    require(
        (audience.organization_id, audience.session_id) == (organization_id, session_id),
        "SCOPE_MISMATCH",
    )
    members = {item.participant_id for item in audience.members}
    for contributor in basis.contributors:
        require(contributor.participant_id in members, "CONTRIBUTOR_MEMBERSHIP_REQUIRED")
        require(contributor.purpose_code == PURPOSE, "PURPOSE_NOT_PERMITTED")
        require(contributor_allowed(contributor), "CONSENT_REQUIRED")


def _literal_ignorable(char: str) -> bool:
    code_point = ord(char)
    return unicodedata.category(char) == "Cf" or any(
        lower <= code_point <= upper for lower, upper in _DEFAULT_IGNORABLE_RANGES
    )


def _literal_signatures(value: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    # Remove CGJ before normalization so it cannot inhibit Vietnamese mark composition.
    filtered = "".join(char for char in value if not _literal_ignorable(char))
    normalized = unicodedata.normalize("NFKC", filtered).casefold()
    visible = unicodedata.normalize(
        "NFKC", "".join(char for char in normalized if not _literal_ignorable(char))
    )
    boundaries = "".join(
        " " if unicodedata.category(char).startswith("P") else char for char in visible
    )
    stripped = "".join(char for char in visible if not unicodedata.category(char).startswith("P"))
    return tuple(boundaries.split()), tuple(stripped.split())


def imagined_literal_overlap(claim_text: str, imagined_text: str) -> bool:
    """Conservative comparison only; preserve stored text and NFC canonical identity.

    Whole token containment in either direction intentionally rejects a short factual
    phrase wholly contained in a longer imagined phrase. This is not semantic matching,
    accent removal, homoglyph detection or a guarantee to recognize every paraphrase.
    """

    def contains(haystack: tuple[str, ...], needle: tuple[str, ...]) -> bool:
        return bool(needle) and any(
            haystack[index : index + len(needle)] == needle
            for index in range(len(haystack) - len(needle) + 1)
        )

    return any(
        contains(claim, imagined) or contains(imagined, claim)
        for claim, imagined in zip(
            _literal_signatures(claim_text), _literal_signatures(imagined_text), strict=True
        )
    )


def content_readiness(
    has_claims: bool,
    has_fact_section: bool,
) -> tuple[Literal["generation_ready", "needs_content_action"], str | None]:
    """Structural content state only; current authorization/policy are separate guards."""
    require(type(has_claims) is bool and type(has_fact_section) is bool, "INVALID_STATE")
    if not has_claims:
        return "needs_content_action", "NO_ELIGIBLE_SOURCE"
    if not has_fact_section:
        return "needs_content_action", "FACT_SECTION_REQUIRED"
    return "generation_ready", None


@dataclass(frozen=True)
class SourceRefV1:
    source_id: str
    revision: int
    sha256: str

    def __post_init__(self) -> None:
        opaque(self.source_id)
        revision(self.revision)
        require(re.fullmatch(r"[0-9a-f]{64}", self.sha256) is not None, "INVALID_HASH")


def source_refs(refs: tuple[SourceRefV1, ...]) -> None:
    require(type(refs) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
    unique(tuple(ref.source_id for ref in refs), SOURCES_MAX, nonempty=True)


@dataclass(frozen=True)
class ReviewedSourceV1:
    ref: SourceRefV1
    title: str
    locator: str
    reviewed_at: str
    topic: str
    age_bands: tuple[str, ...]
    state: Literal["reviewed", "unreviewed"] = "reviewed"
    recalled: bool = False

    def __post_init__(self) -> None:
        for value in (self.title, self.locator, self.reviewed_at, self.topic):
            text(value)
        unique(self.age_bands, AUDIENCE_MAX, nonempty=True)
        require(self.state in {"reviewed", "unreviewed"}, "INVALID_SOURCE_STATE")
        require(type(self.recalled) is bool, "INVALID_SOURCE_STATE")


@dataclass(frozen=True)
class ReviewedClaimV1:
    claim_id: str
    revision: int
    text: str
    source_refs: tuple[SourceRefV1, ...]

    def __post_init__(self) -> None:
        opaque(self.claim_id)
        revision(self.revision)
        text(self.text, CLAIM_MAX)
        source_refs(self.source_refs)


@dataclass(frozen=True)
class KnowledgeClaimV1:
    claim_id: str
    revision: int
    text: str
    source_refs: tuple[SourceRefV1, ...]
    verification_state: Literal["catalog_reviewed", "teacher_attested"]
    attested_by: str | None = None
    attestation_reason: str | None = None

    def __post_init__(self) -> None:
        ReviewedClaimV1(self.claim_id, self.revision, self.text, self.source_refs)
        require(
            self.verification_state in {"catalog_reviewed", "teacher_attested"},
            "INVALID_CLAIM_STATE",
        )
        if self.verification_state == "teacher_attested":
            require(
                self.attested_by is not None and self.attestation_reason is not None,
                "ATTESTATION_REQUIRED",
            )
            assert self.attested_by is not None and self.attestation_reason is not None
            opaque(self.attested_by)
            text(self.attestation_reason)
        else:
            require(
                self.attested_by is None and self.attestation_reason is None, "INVALID_ATTRIBUTION"
            )


def catalog_claim(claim: ReviewedClaimV1) -> KnowledgeClaimV1:
    return KnowledgeClaimV1(
        claim.claim_id, claim.revision, claim.text, claim.source_refs, "catalog_reviewed"
    )


def attributed_claim(
    claim_id: str,
    claim_revision: int,
    claim_text: str,
    refs: tuple[SourceRefV1, ...],
    catalog: tuple[ReviewedClaimV1, ...],
    teacher_principal_id: str,
    reason: str | None,
    previous: KnowledgeClaimV1 | None = None,
) -> KnowledgeClaimV1:
    candidate = ReviewedClaimV1(claim_id, claim_revision, claim_text, refs)
    if previous is not None and (
        previous.claim_id,
        previous.revision,
        previous.text,
        previous.source_refs,
        previous.attestation_reason,
    ) == (claim_id, claim_revision, claim_text, refs, reason):
        return previous
    if candidate in catalog:
        return catalog_claim(candidate)
    return KnowledgeClaimV1(
        claim_id, claim_revision, claim_text, refs, "teacher_attested", teacher_principal_id, reason
    )


def validate_claims(
    claims: tuple[KnowledgeClaimV1, ...],
    catalog_claims: tuple[ReviewedClaimV1, ...],
    sources: tuple[ReviewedSourceV1, ...],
    basis: KnowledgeBasisV1,
    audience: AudienceContextV1,
) -> tuple[ReviewedSourceV1, ...]:
    require(type(claims) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
    unique(tuple(claim.claim_id for claim in claims), CLAIMS_MAX)
    unique(tuple(claim.claim_id for claim in catalog_claims), CLAIMS_MAX)
    unique(tuple(source.ref.source_id for source in sources), SOURCES_MAX)
    source_map = {source.ref.source_id: source for source in sources}
    selected: dict[str, ReviewedSourceV1] = {}
    for claim in claims:
        if claim.verification_state == "catalog_reviewed":
            require(
                ReviewedClaimV1(claim.claim_id, claim.revision, claim.text, claim.source_refs)
                in catalog_claims,
                "CATALOG_CLAIM_MISMATCH",
            )
        for pin in claim.source_refs:
            source = source_map.get(pin.source_id)
            require(source is not None, "SOURCE_MISSING")
            assert source is not None
            require(source.ref.revision == pin.revision, "SOURCE_REVISION_MISMATCH")
            require(source.ref.sha256 == pin.sha256, "SOURCE_HASH_MISMATCH")
            require(source.state == "reviewed", "SOURCE_NOT_REVIEWED")
            require(not source.recalled, "SOURCE_RECALLED")
            require(source.topic == basis.topic, "SOURCE_TOPIC_MISMATCH")
            require(
                all(member.age_band in source.age_bands for member in audience.members),
                "SOURCE_AGE_MISMATCH",
            )
            selected[pin.source_id] = source
    require(len(selected) <= SOURCES_MAX, "COLLECTION_BOUNDS")
    return tuple(selected[key] for key in sorted(selected))


@dataclass(frozen=True)
class FactSection:
    section_id: str
    claim_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        opaque(self.section_id)
        unique(self.claim_refs, CLAIMS_MAX, nonempty=True)


@dataclass(frozen=True)
class StorySection:
    section_id: str
    imagined_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        opaque(self.section_id)
        unique(self.imagined_refs, IMAGINED_MAX, nonempty=True)


@dataclass(frozen=True)
class ProjectedSectionV1:
    section_id: str
    kind: Literal["fact", "story"]
    refs: tuple[str, ...]
    text: str


ScriptSection = FactSection | StorySection


def project_script(
    sections: tuple[ScriptSection, ...],
    claims: tuple[KnowledgeClaimV1, ...],
    imagined_elements: tuple[ImaginedElementV1, ...],
    *,
    forbidden_imagined: tuple[ImaginedElementV1, ...] = (),
) -> tuple[tuple[ProjectedSectionV1, ...], str]:
    require(type(sections) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
    require(type(imagined_elements) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
    unique(tuple(section.section_id for section in sections), SECTIONS_MAX)
    unique(tuple(claim.claim_id for claim in claims), CLAIMS_MAX)
    unique(tuple(element.ref for element in imagined_elements), IMAGINED_MAX)
    claim_map = {claim.claim_id: claim.text for claim in claims}
    imagined_map = {element.ref: element.text for element in imagined_elements}
    literals = imagined_elements + forbidden_imagined
    for claim in claims:
        require(
            not any(imagined_literal_overlap(claim.text, item.text) for item in literals),
            "IMAGINED_AS_FACT",
        )
    projected: list[ProjectedSectionV1] = []
    for section in sections:
        if isinstance(section, FactSection):
            require(all(ref in claim_map for ref in section.claim_refs), "UNKNOWN_CLAIM_REFERENCE")
            content = "\n".join(claim_map[ref] for ref in section.claim_refs)
            projected.append(
                ProjectedSectionV1(section.section_id, "fact", section.claim_refs, content)
            )
        else:
            require(isinstance(section, StorySection), "INVALID_SECTION")
            require(
                all(ref in imagined_map for ref in section.imagined_refs),
                "UNKNOWN_IMAGINED_REFERENCE",
            )
            content = "\n".join(imagined_map[ref] for ref in section.imagined_refs)
            projected.append(
                ProjectedSectionV1(section.section_id, "story", section.imagined_refs, content)
            )
    flat = "\n".join(section.text for section in projected)
    require(len(flat) <= SCRIPT_MAX, "SCRIPT_BOUNDS")
    return tuple(projected), flat


def _normalize(value: object) -> object:
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        return unicodedata.normalize("NFC", value)
    if type(value) is list:
        return [_normalize(item) for item in value]
    if type(value) is dict:
        result: dict[str, object] = {}
        for key, item in value.items():
            require(type(key) is str, "CANONICAL_KEY_TYPE")
            normalized = unicodedata.normalize("NFC", key)
            require(normalized not in result, "NFC_DUPLICATE_KEY")
            result[normalized] = _normalize(item)
        return result
    raise KnowledgeRuleViolation("CANONICAL_TYPE")


def canonical_bytes(document: Mapping[str, object]) -> bytes:
    normalized = _normalize(dict(document))
    assert isinstance(normalized, dict)
    try:
        encoded = json.dumps(
            normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (UnicodeError, ValueError):
        raise KnowledgeRuleViolation("CANONICAL_TYPE") from None
    require(len(encoded) <= DOCUMENT_MAX, "DOCUMENT_BOUNDS")
    require(
        hashlib.sha256(encoded).hexdigest() == strict_canonical_sha256(normalized),
        "CANONICAL_HASH_MISMATCH",
    )
    return encoded


def canonical_sha256(document: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_bytes(document)).hexdigest()


def _native(value: object) -> object:
    """Convert our typed immutable value graph to JSON arrays, never request coercion."""
    if isinstance(value, tuple):
        return [_native(item) for item in value]
    if isinstance(value, dict):
        return {key: _native(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class CorrectionV1:
    correction_ref: str
    author_principal_id: str
    reason: str
    from_version: int
    to_version: int

    def __post_init__(self) -> None:
        opaque(self.correction_ref)
        opaque(self.author_principal_id)
        text(self.reason)
        revision(self.from_version)
        require(
            type(self.to_version) is int and self.to_version == self.from_version + 1,
            "CORRECTION_VERSION",
        )


@dataclass(frozen=True)
class BundleHead:
    bundle_id: str
    organization_id: str
    session_id: str
    current_version: int
    editorial_revision: int

    def __post_init__(self) -> None:
        for value in (self.bundle_id, self.organization_id, self.session_id):
            opaque(value)
        revision(self.current_version)
        revision(self.editorial_revision)

    @property
    def etag(self) -> str:
        return (
            f'"knowledge-bundle:{self.bundle_id}:{self.current_version}:{self.editorial_revision}"'
        )


@dataclass(frozen=True)
class KnowledgeBundleVersion:
    bundle_id: str
    bundle_version: int
    organization_id: str
    session_id: str
    basis: KnowledgeBasisV1
    audience: AudienceContextV1
    knowledge_claims: tuple[KnowledgeClaimV1, ...]
    source_records: tuple[ReviewedSourceV1, ...]
    sections: tuple[ScriptSection, ...]
    imagined_elements: tuple[ImaginedElementV1, ...]
    contributors: tuple[ContributorV1, ...]
    content_origin: Literal["generic", "child_derived"]
    created_by: str
    created_at: str
    editorial_revision: int
    corrections: tuple[CorrectionV1, ...]
    policy_ref: str
    canonical_bytes: bytes
    bundle_hash: str

    @property
    def projected_sections(self) -> tuple[ProjectedSectionV1, ...]:
        return project_script(
            self.sections,
            self.knowledge_claims,
            self.imagined_elements,
            forbidden_imagined=self.basis.imagined_elements,
        )[0]

    @property
    def script_text(self) -> str:
        return project_script(
            self.sections,
            self.knowledge_claims,
            self.imagined_elements,
            forbidden_imagined=self.basis.imagined_elements,
        )[1]


def version_document(version: KnowledgeBundleVersion) -> dict[str, object]:
    basis_snapshot = asdict(version.basis)
    # These historical flags are invariant true. Current decisions come from trusted ports.
    del basis_snapshot["confirmed"]
    del basis_snapshot["applicable"]
    return {
        "canonical_rules_version": CANONICAL_RULES_VERSION,
        "contract_name": "KnowledgeBundle",
        "contract_version": CONTRACT_VERSION,
        "bundle_id": version.bundle_id,
        "bundle_version": version.bundle_version,
        "organization_id": version.organization_id,
        "session_id": version.session_id,
        "audience_context_ref": version.audience.ref,
        "context_revision": version.audience.context_revision,
        "audience_revision": version.audience.audience_revision,
        "audience_members": _native(tuple(asdict(item) for item in version.audience.members)),
        "source_snapshot_refs": list(version.basis.source_snapshot_refs),
        "confirmed_topic": version.basis.topic,
        "basis_ref": {
            "kind": version.basis.kind,
            "ref": version.basis.ref,
            "revision": version.basis.revision,
        },
        "confirmation_ref": version.basis.confirmation_ref,
        "basis_snapshot": _native(basis_snapshot),
        "knowledge_claims": _native(tuple(asdict(item) for item in version.knowledge_claims)),
        "source_records": _native(tuple(asdict(item) for item in version.source_records)),
        "script_sections": _native(tuple(asdict(item) for item in version.projected_sections)),
        "script_text": version.script_text,
        "editorial_revision": version.editorial_revision,
        "editorial_state": "draft",
        "created_by": version.created_by,
        "created_at": version.created_at,
        "child_imagined_elements": _native(
            tuple(asdict(item) for item in version.imagined_elements)
        ),
        "teacher_corrections": _native(tuple(asdict(item) for item in version.corrections)),
        "contributors": _native(tuple(asdict(item) for item in version.contributors)),
        "content_origin": version.content_origin,
        "policy_ref": version.policy_ref,
    }


def verify_version(version: KnowledgeBundleVersion) -> None:
    require(
        (version.organization_id, version.session_id)
        == (version.basis.organization_id, version.basis.session_id)
        == (version.audience.organization_id, version.audience.session_id),
        "SCOPE_MISMATCH",
    )
    rebuilt = build_version(
        bundle_id=version.bundle_id,
        basis=version.basis,
        audience=version.audience,
        claims=version.knowledge_claims,
        sources=version.source_records,
        sections=version.sections,
        imagined_elements=version.imagined_elements,
        created_by=version.created_by,
        created_at=version.created_at,
        bundle_version=version.bundle_version,
        editorial_revision=version.editorial_revision,
        corrections=version.corrections,
        content_origin=version.content_origin,
        contributors=version.contributors,
        policy_ref=version.policy_ref,
    )
    expected = rebuilt.canonical_bytes
    require(
        type(version.canonical_bytes) is bytes and expected == version.canonical_bytes,
        "CANONICAL_BYTES_MISMATCH",
    )
    require(hashlib.sha256(expected).hexdigest() == version.bundle_hash, "BUNDLE_HASH_MISMATCH")


def build_version(
    *,
    bundle_id: str,
    basis: KnowledgeBasisV1,
    audience: AudienceContextV1,
    claims: tuple[KnowledgeClaimV1, ...],
    sources: tuple[ReviewedSourceV1, ...],
    sections: tuple[ScriptSection, ...],
    imagined_elements: tuple[ImaginedElementV1, ...],
    created_by: str,
    created_at: str,
    bundle_version: int = 1,
    editorial_revision: int = 1,
    corrections: tuple[CorrectionV1, ...] = (),
    content_origin: Literal["generic", "child_derived"] | None = None,
    contributors: tuple[ContributorV1, ...] | None = None,
    policy_ref: str = FIXTURE_POLICY,
) -> KnowledgeBundleVersion:
    opaque(bundle_id)
    opaque(created_by)
    text(created_at)
    opaque(policy_ref)
    revision(bundle_version)
    revision(editorial_revision)
    require(editorial_revision == bundle_version, "EDITORIAL_REVISION_MISMATCH")
    require(
        (basis.organization_id, basis.session_id)
        == (audience.organization_id, audience.session_id),
        "SCOPE_MISMATCH",
    )
    require(basis.confirmed, "BASIS_UNCONFIRMED")
    require(basis.applicable, "BASIS_NOT_APPLICABLE")
    require(
        type(corrections) is tuple and len(corrections) == bundle_version - 1, "CORRECTION_HISTORY"
    )
    require(
        len({item.correction_ref for item in corrections}) == len(corrections),
        "DUPLICATE_CORRECTION",
    )
    require(
        all(
            item.from_version == index + 1 and item.to_version == index + 2
            for index, item in enumerate(corrections)
        ),
        "CORRECTION_HISTORY",
    )
    origin: Literal["generic", "child_derived"] = (
        "child_derived" if basis.kind == "confirmed_meaning" else "generic"
    )
    require(content_origin is None or content_origin == origin, "PROVENANCE_DOWNGRADE")
    require(contributors is None or contributors == basis.contributors, "PROVENANCE_DOWNGRADE")
    require(type(claims) is tuple and type(sources) is tuple, "IMMUTABLE_SEQUENCE_REQUIRED")
    unique(tuple(item.claim_id for item in claims), CLAIMS_MAX)
    unique(tuple(item.ref.source_id for item in sources), SOURCES_MAX)
    pinned_sources = {item.ref.source_id: item.ref for item in sources}
    require(
        {pin.source_id for claim in claims for pin in claim.source_refs} == set(pinned_sources),
        "SOURCE_PIN_MISMATCH",
    )
    require(
        all(pinned_sources[pin.source_id] == pin for claim in claims for pin in claim.source_refs),
        "SOURCE_PIN_MISMATCH",
    )
    require(
        all(item in basis.imagined_elements for item in imagined_elements),
        "UNKNOWN_IMAGINED_REFERENCE",
    )
    project_script(sections, claims, imagined_elements, forbidden_imagined=basis.imagined_elements)
    result = KnowledgeBundleVersion(
        bundle_id,
        bundle_version,
        basis.organization_id,
        basis.session_id,
        basis,
        audience,
        claims,
        tuple(sorted(sources, key=lambda item: item.ref.source_id)),
        sections,
        imagined_elements,
        basis.contributors,
        origin,
        created_by,
        created_at,
        editorial_revision,
        corrections,
        policy_ref,
        b"",
        "",
    )
    encoded = canonical_bytes(version_document(result))
    return replace(result, canonical_bytes=encoded, bundle_hash=hashlib.sha256(encoded).hexdigest())


def plan_edit(
    old: KnowledgeBundleVersion,
    *,
    correction_ref: str,
    teacher_principal_id: str,
    reason: str,
    claims: tuple[KnowledgeClaimV1, ...] | None = None,
    sources: tuple[ReviewedSourceV1, ...] | None = None,
    sections: tuple[ScriptSection, ...] | None = None,
    imagined_elements: tuple[ImaginedElementV1, ...] | None = None,
) -> KnowledgeBundleVersion | None:
    verify_version(old)
    candidate = replace(
        old,
        knowledge_claims=old.knowledge_claims if claims is None else claims,
        source_records=old.source_records
        if sources is None
        else tuple(sorted(sources, key=lambda item: item.ref.source_id)),
        sections=old.sections if sections is None else sections,
        imagined_elements=old.imagined_elements if imagined_elements is None else imagined_elements,
    )
    # Compare normalized semantic content before allocating correction/version identities.
    if canonical_bytes(version_document(candidate)) == old.canonical_bytes:
        return None
    correction = CorrectionV1(
        correction_ref, teacher_principal_id, reason, old.bundle_version, old.bundle_version + 1
    )
    return build_version(
        bundle_id=old.bundle_id,
        basis=old.basis,
        audience=old.audience,
        claims=candidate.knowledge_claims,
        sources=candidate.source_records,
        sections=candidate.sections,
        imagined_elements=candidate.imagined_elements,
        created_by=old.created_by,
        created_at=old.created_at,
        bundle_version=old.bundle_version + 1,
        editorial_revision=old.editorial_revision + 1,
        corrections=old.corrections + (correction,),
        content_origin=old.content_origin,
        contributors=old.contributors,
        policy_ref=old.policy_ref,
    )
