"""Shared05 DTO consumer refinement only, no authority/session/access adoption."""

import pytest

from sketch2life.application.video_review_contract import bind_video_review
from sketch2life.contracts.schemas.ai_contract_candidates import ExactContentReviewCommandV1
from sketch2life.domain.knowledge_video.model import VideoError
from tests.unit.test_video_review_domain import subject


def command(**changes):
    target = subject()
    return ExactContentReviewCommandV1.model_validate(
        {
            "target_kind": "knowledge_video",
            "target_id": target.video_id,
            "target_version": target.video_version,
            "target_hash": target.artifact.hash,
            "source_context_revision": target.source_context_revision,
            "decision": "approve",
            "review_context": {
                "kind": "session_content",
                "session_id": "session",
                "audience_context_revision": 0,
                "consent_revision_refs": ({"subject_ref": "child", "revision": 1},),
                "review_purpose": "teaching_delivery",
            },
            "audience_scope": {
                "session_id": "session",
                "group_ids": ("group",),
                "participant_ids": ("child",),
            },
        }
        | changes
    )


def test_shared_command_reused_not_forked_and_native_output_normalized():
    result = bind_video_review(command(), subject())
    assert type(result) is ExactContentReviewCommandV1
    assert result.target_hash != subject().pin_digest


@pytest.mark.parametrize(
    "changes",
    [
        {"target_kind": "learning_content"},
        {"target_id": "other"},
        {"target_version": 2},
        {"target_hash": "c" * 64},
        {"target_hash": subject().pin_digest},
        {"source_context_revision": 1},
        {"review_dimension": "safety"},
        {"expected_review_revision": 1},
    ],
)
def test_inapplicable_target_or_generic_fields_not_session_approval(changes):
    with pytest.raises(VideoError):
        bind_video_review(command(**changes), subject())


@pytest.mark.parametrize(
    "changes",
    [
        {"target_version": True},
        {"target_hash": "private/url"},
        {"decision": "play"},
        {"source_context_revision": True},
    ],
)
def test_forged_native_shared_dto_not_trusted(changes):
    forged = command().model_copy(update=changes)
    with pytest.raises(VideoError):
        bind_video_review(forged, subject())


@pytest.mark.parametrize(
    "field,value",
    [
        ("audience_context_revision", 1),
        ("consent_revision_refs", ({"subject_ref": "child", "revision": 2},)),
    ],
)
def test_context_consent_change_not_approved_by_matching_media_hash(field, value):
    original = command()
    context = original.review_context.model_dump(mode="python") | {field: value}
    changed = command(review_context=context)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_TARGET_MISMATCH"):
        bind_video_review(changed, subject())


@pytest.mark.parametrize(
    "field,value",
    [
        ("group_ids", ("other",)),
        ("participant_ids", ("other",)),
        ("group_ids", ("group", "group")),
        ("participant_ids", ("child", "child")),
    ],
)
def test_audience_must_match_authoritatively_resolved_subset(field, value):
    audience = command().audience_scope.model_dump(mode="python") | {field: value}
    with pytest.raises(VideoError):
        bind_video_review(command(audience_scope=audience), subject())


def test_generic_library_published_review_cannot_authorize_session_video():
    generic = command(
        review_context={
            "kind": "generic_library",
            "content_kind": "knowledge_video",
            "age_policy_ref": "age",
            "content_policy_ref": "policy",
            "publication_scope": "school_library",
            "review_purpose": "library_publication",
        },
        audience_scope={
            "publication_scope": "school_library",
            "age_policy_ref": "age",
            "purpose_codes": ("learning",),
        },
        review_dimension="safety",
        expected_review_revision=0,
    )
    with pytest.raises(VideoError, match="VIDEO_REVIEW_INVALID_CONTEXT"):
        bind_video_review(generic, subject())


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_whitespace_reason_rejected_by_owned_consumer_without_shared_schema_change(decision):
    with pytest.raises(VideoError):
        bind_video_review(command(decision=decision, reason="  "), subject())


def test_forged_resolved_subject_is_not_trusted():
    target = subject()
    object.__setattr__(target, "video_version", True)
    with pytest.raises(VideoError):
        bind_video_review(command(), target)
