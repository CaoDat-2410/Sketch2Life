"""Metadata projection for BE1 gateways; every new use rechecks eligibility."""

from pydantic import ValidationError

from sketch2life.application.learning_content_eligibility import ContentEligibility
from sketch2life.contracts.schemas.content_consumers import (
    ContentLifecycleNoticeV1,
    ContentLifecyclePayloadV1,
    ContentReferenceQueryV1,
    PublishedContentReferenceV1,
)
from sketch2life.contracts.schemas.learning_content import PublicationReviewSet
from sketch2life.domain.learning_content.model import ContentError


class ContentConsumerQueries:
    def __init__(self, eligibility: ContentEligibility) -> None:
        self.eligibility = eligibility

    def resolve_reference(self, principal_id: str, organization_id: str,
                          query: ContentReferenceQueryV1) -> PublishedContentReferenceV1:
        # Never synthesize an eligible reference from an event/receipt/cache.
        result = self.eligibility.resolve(
            principal_id, organization_id, query.record_id,
            age_months=query.age_months, purpose_code=query.purpose_code,
            version=query.version, expected_hash=query.expected_hash)
        if (result.organization_id != organization_id or result.record_id != query.record_id
                or (query.version is not None and result.version != query.version)
                or (query.expected_hash is not None and result.hash != query.expected_hash)
                or len(result.publication_review_ids) != 2):
            raise ContentError("CONTENT_STORAGE_SCOPE_MISMATCH")
        return PublishedContentReferenceV1(
            record_id=result.record_id, organization_id=result.organization_id,
            version=result.version, revision=result.revision, hash=result.hash,
            publication_review_ref=PublicationReviewSet(
                safety_review_id=result.publication_review_ids[0],
                pedagogical_review_id=result.publication_review_ids[1],
                review_policy_version=result.policy_version))


def notice_from_outbox(event_id: str, organization_id: str,
                       payload_json: str) -> ContentLifecycleNoticeV1:
    """Pure owned-payload adapter: does not read/ack/deliver an outbox row."""
    try:
        payload = ContentLifecyclePayloadV1.model_validate_json(payload_json)
        notice = ContentLifecycleNoticeV1(event_id=event_id, payload=payload)
    except ValidationError:
        raise ContentError("CONTENT_INVALID_NOTICE") from None
    if notice.payload.organization_id != organization_id:
        raise ContentError("CONTENT_NOTICE_SCOPE_MISMATCH")
    return notice
