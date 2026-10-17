"""BE2-12 current published-content projection; no permissive default adapters."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from sketch2life.application.ports.learning_content import (
    ContentAccess,
    ContentBoundary,
    ContentStore,
)
from sketch2life.contracts.schemas.learning_content import ContentWrite
from sketch2life.domain.learning_content.model import (
    Capability,
    ContentError,
    ContentState,
    ContentVersion,
    authorize,
    canonical_json,
    check_publication_reviews,
    content_hash,
)


def audience_hash(body: ContentWrite) -> str:
    """DATA-24 library audience v1; purposes are a unique, unordered set.

    This does NOT normalize the authored payload hash or receipt fingerprint.
    """
    return content_hash(canonical_json({
        "publication_scope": "school_library",
        "age_policy_ref": body.age_eligibility.age_policy_ref,
        "purpose_codes": sorted(body.purpose_codes),
    }))


def eligible_body(content: ContentVersion, access: ContentAccess) -> ContentWrite:
    """Exact policy/source eligibility shared by publication and resolution.

    Owner calls must raise safe ContentError codes on dependency failure; no
    cached or caller-declared source classification can supply this decision.
    Child-derived content remains closed pending a separately adopted contract.
    """
    if content_hash(content.body_json) != content.hash:
        raise ContentError("CONTENT_HASH_MISMATCH")
    try:
        body = ContentWrite.model_validate_json(content.body_json)
    except ValidationError:
        raise ContentError("CONTENT_INVALID_STORED_PAYLOAD") from None
    policy = access.policy
    if (not policy.version or body.content_policy_ref != policy.content_policy_ref
            or body.age_eligibility.age_policy_ref != policy.age_policy_ref
            or body.content_kind not in policy.content_kinds
            or not set(body.purpose_codes).issubset(policy.purpose_codes)):
        raise ContentError("CONTENT_POLICY_DENIED")
    assessment = access.assess_sources(content)
    if (assessment.organization_id, assessment.record_id, assessment.version,
        assessment.hash, assessment.policy_version) != (
        content.organization_id, content.record_id, content.version, content.hash, policy.version
    ):
        raise ContentError("CONTENT_SOURCE_MISMATCH")
    if assessment.classification != "generic_authored":
        raise ContentError("CONTENT_SOURCE_AUTHORITY_REQUIRED")
    if assessment.usage_allowed is not True or assessment.moderation_passed is not True:
        raise ContentError("CONTENT_SOURCE_DENIED")
    return body


def published_body(content: ContentVersion, access: ContentAccess) -> ContentWrite:
    if content.state != ContentState.PUBLISHED:
        raise ContentError("CONTENT_NOT_PUBLISHED")
    body = eligible_body(content, access)
    if (content.publication_policy_version != access.policy.version
            or len(content.publication_review_ids) != 2):
        raise ContentError("CONTENT_REVIEW_REQUIRED")
    safety, pedagogical = content.publication_review_ids
    check_publication_reviews(content, safety_review_id=safety,
                              pedagogical_review_id=pedagogical,
                              policy_version=access.policy.version,
                              audience_hash=audience_hash(body))
    # Domain proof checks exact dimension/target/context/audience/policy. The
    # owner port separately checks current reviewer authority/effectiveness.
    for proof in content.reviews:
        if (proof.review_id in content.publication_review_ids
                and access.review_effective(content, proof) is not True):
            raise ContentError("CONTENT_REVIEW_INEFFECTIVE")
    return body


@dataclass(frozen=True, slots=True)
class PublishedContent:
    record_id: str
    organization_id: str
    version: int
    revision: int
    hash: str
    content: ContentWrite
    publication_review_ids: tuple[str, ...]
    policy_version: str


class ContentEligibility:
    def __init__(self, store: ContentStore, boundary: ContentBoundary) -> None:
        self.store = store
        self.boundary = boundary

    def resolve(self, principal_id: str, organization_id: str, record_id: str, *,
                age_months: int, purpose_code: str, version: int | None = None,
                expected_hash: str | None = None) -> PublishedContent:
        if (type(age_months) is not int or age_months < 0 or not purpose_code
                or (version is not None and (type(version) is not int or version < 1))
                or (expected_hash is not None and version is None)):
            raise ContentError("CONTENT_INVALID_QUERY")
        # Guard exits AFTER storage commit, not just after the last SQL call.
        with self.boundary.guard(principal_id, organization_id) as access:
            if (access.authority.principal_id, access.authority.organization_id) != (
                principal_id, organization_id
            ):
                raise ContentError("CONTENT_INVALID_AUTHORITY")
            authorize(access.authority, organization_id, Capability.READ)
            with self.store.transaction() as tx:
                candidates: tuple[ContentVersion, ...]
                if version is not None:
                    content = tx.load(organization_id, record_id, version=version)
                    candidates = () if content is None else (content,)
                else:
                    candidates = tuple(sorted(
                        tx.published_versions(organization_id, record_id),
                        key=lambda item: item.version, reverse=True))
                for content in candidates:
                    if (content.organization_id != organization_id
                            or content.record_id != record_id
                            or (version is not None and content.version != version)):
                        raise ContentError("CONTENT_STORAGE_SCOPE_MISMATCH")
                    if expected_hash is not None and expected_hash != content.hash:
                        raise ContentError("CONTENT_HASH_MISMATCH")
                    # Fail closed on policy/source/review errors rather than
                    # silently masking dependency failures by choosing old data.
                    body = published_body(content, access)
                    if (body.age_eligibility.min_months <= age_months
                            <= body.age_eligibility.max_months
                            and purpose_code in body.purpose_codes):
                        return PublishedContent(
                            content.record_id, organization_id, content.version, content.revision,
                            content.hash, body, content.publication_review_ids,
                            access.policy.version)
                    if version is not None:
                        raise ContentError("CONTENT_AUDIENCE_DENIED")
                raise ContentError("CONTENT_NOT_ELIGIBLE")
