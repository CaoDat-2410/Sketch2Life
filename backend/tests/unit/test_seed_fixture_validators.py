"""Offline contract preflight for every seeded stage request/domain input."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.services.notifications import validate_command
from sketch2life.application.services.parent_consent_policies import ParentConsentPolicyService
from sketch2life.application.services.parent_story_runs import ParentStoryRunService
from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest, MoveProfileRequest
from sketch2life.contracts.schemas.lesson_library import (
    CreateLessonAccessGrantRequestV1,
    DecideLessonAccessGrantRequestV1,
    LessonContentInputV1,
)
from sketch2life.contracts.schemas.lesson_occurrences import (
    ConfirmPlanRevisionRequestV1,
    CreateLessonOccurrenceRequestV1,
    CreatePlanRevisionRequestV1,
    EditDocumentRevisionRequestV1,
    PlanDocumentRefV1,
)
from sketch2life.contracts.schemas.modal_ai import (
    ParentActivityCatalogCandidateV2,
    ParentActivitySuggestionWorkerRequestV3,
    ParentSuggestedActivityV2,
)
from sketch2life.contracts.schemas.parent_activity_selection import ParentActivitySuggestionSetV1
from sketch2life.contracts.schemas.parent_consent_policies import ParentConsentPolicyCreateRequestV1
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryRunCancelRequestV1,
    ParentStoryRunCreateRequestV1,
    ParentSubjectConfirmationRequestV1,
)
from sketch2life.contracts.schemas.platform_admin import (
    CapacityPriceInput,
    CapacityQuoteInput,
    FeedbackInput,
    IncludedQuotaInput,
    QuotaAllocationInput,
    QuotaProductInput,
    SandboxPaymentInput,
)
from sketch2life.contracts.schemas.profile_sharing import CreateShareGrantRequestV1
from sketch2life.domain.lesson_library.model import canonical_content_hash, validate_content
from sketch2life.domain.parent_profile_context import ContextEntryDraft, validate_entry
from sketch2life.domain.parent_profiles import (
    ProfileSnapshot,
    validate_idempotency_key,
    validate_snapshot,
)
from sketch2life.domain.profile_sharing import normalize_granted_fields
from tools.seed import (
    data,
    s7b_story_states_data,
    s8_lessons,
    s8_lessons_data,
    s9_classes,
    s9_classes_data,
    s10_inbox,
    s10_inbox_data,
    s11_org_run_shares_data,
    s12_story_v4a_data,
    s13_system_demo_data,
    seed2_abc,
)


def _validated_lesson_content(value: dict[str, Any]) -> dict[str, Any]:
    content = LessonContentInputV1.model_validate(value)
    normalized = content.model_dump(mode="python")
    validate_content(normalized)
    return normalized


def _age_band_months(age_months: int) -> str:
    if 36 <= age_months <= 71:
        return "36-71"
    if 72 <= age_months <= 107:
        return "72-107"
    if 108 <= age_months <= 120:
        return "108-120"
    raise AssertionError(f"unsupported seeded age: {age_months}")


def test_s7b_story_values_pass_product_and_domain_validators() -> None:
    validate_snapshot(s7b_story_states_data.PROFILE_SNAPSHOT)
    profile_ref = str(data.parent_profile_id(s7b_story_states_data.PROFILE_KEY))
    for topic, idea in (s7b_story_states_data.P3_RUN_A, s7b_story_states_data.P3_RUN_B):
        ParentStoryRunCreateRequestV1.model_validate(
            {"parent_profile_id": profile_ref, "topic": topic, "adult_confirmed_idea": idea}
        )
        ParentStoryRunService._normalize_create_values(
            topic=topic,
            adult_confirmed_idea=idea,
            intended_drawing_subject=None,
        )

    for subject in (s7b_story_states_data.P4_SUBJECT, s7b_story_states_data.P5_SUBJECT):
        ParentSubjectConfirmationRequestV1.model_validate(
            {"expected_understanding_revision": 1, "confirmed_subject": subject}
        )

    for result in s7b_story_states_data.STORY_RESULTS.values():
        normalized, digest = normalize_story_output(
            result.story, confirmed_subject=s7b_story_states_data.P4_SUBJECT
        )
        assert len(digest) == 64
        assert normalized["title"] == result.story["title"]


def test_s8_occurrences_documents_plans_and_pinned_lesson_hashes_validate_offline() -> None:
    for spec in s8_lessons_data.OCCURRENCES:
        version_ref = None
        if spec.lesson_key is not None and spec.lesson_version_no is not None:
            version_ref = s8_lessons._pin(spec.lesson_key, spec.lesson_version_no).model_dump(
                mode="json"
            )
        CreateLessonOccurrenceRequestV1.model_validate(
            {
                "class_id": data.class_id("a", spec.class_number),
                "title": spec.title,
                "scheduled_date": spec.scheduled_date.isoformat(),
                "lesson_version_ref": version_ref,
            }
        )

    for document in s8_lessons_data.DOCUMENTS:
        EditDocumentRevisionRequestV1(
            extracted_text=document.extracted_text,
            expected_head_revision_no=1,
        )
    EditDocumentRevisionRequestV1(
        extracted_text=s8_lessons_data.DOCUMENT_EDIT_TEXT,
        expected_head_revision_no=1,
    )

    occurrence_by_key = {item.key: item for item in s8_lessons_data.OCCURRENCES}
    for plan in s8_lessons_data.PLANS:
        occurrence = occurrence_by_key[plan.occurrence_key]
        document_ref = None
        if plan.document_revision_no is not None:
            document_spec = next(
                item
                for item in s8_lessons_data.DOCUMENTS
                if item.occurrence_key == plan.occurrence_key
            )
            document_ref = PlanDocumentRefV1(
                document_id=s8_lessons.source_document_id(document_spec.key),
                revision_no=plan.document_revision_no,
            )
        CreatePlanRevisionRequestV1(
            expected_head_revision_no=plan.expected_head_revision_no,
            document_revision_ref=document_ref,
            objectives=list(plan.objectives),
            teacher_direction=plan.teacher_direction,
            safety_notes=plan.safety_notes,
            activities=s8_lessons._lesson_activity_inputs(occurrence, plan.activity_orders),
        )
        if plan.confirm:
            ConfirmPlanRevisionRequestV1(expected_plan_hash=hashlib.sha256(b"s8-plan").hexdigest())

    activities_by_version: dict[str, list[dict[str, Any]]] = {}
    for activity in data.version_activity_rows():
        activities_by_version.setdefault(str(activity["version_id"]), []).append(activity)
    for version in data.library_version_rows():
        activities = sorted(
            activities_by_version[str(version["version_id"])],
            key=lambda row: int(row["activity_order"]),
        )
        content = {
            **version["content_json"],
            "activities": [row["activity_json"] for row in activities],
        }
        normalized = _validated_lesson_content(content)
        assert canonical_content_hash(normalized) == version["structured_content_hash"]


def test_s9_realistic_profiles_use_domain_revision_hash_without_http_name_schema() -> None:
    profiles = s9_classes_data.lifecycle_profile_rows() + s9_classes_data.keyed_profile_rows()
    for profile in profiles:
        snapshot = ProfileSnapshot(
            display_name=str(profile["display_name"]),
            age_months=int(profile["age_months"]),
            interests_summary=None,
        )
        validate_snapshot(snapshot)
        revision = data.baseline_revision_row(profile)
        assert revision["revision_hash"] == data.revision_hash(
            child_id=str(profile["child_id"]),
            revision_no=1,
            display_name=str(profile["display_name"]),
            age_months=int(profile["age_months"]),
            structured_interests=[],
        )

    for profile in s9_classes_data.keyed_profile_rows():
        with pytest.raises(ValidationError):
            CreateProfileRequest.model_validate(
                {
                    "display_name": profile["display_name"],
                    "age_months": profile["age_months"],
                    "consent_id": None,
                }
            )
    MoveProfileRequest(
        target_class_id=data.class_id("a", s9_classes_data.MOVE_TO_CLASS_NUMBER),
        target_class_revision=1,
    )
    assert s9_classes._profile_fingerprint(
        key=b"x" * 32,
        subject=data.ORG_A_TEACHERS[0],
        scope=s9_classes_data.profile_create_scope(),
        display_name=str(s9_classes_data.keyed_profile_rows()[0]["display_name"]),
        age_months=int(s9_classes_data.keyed_profile_rows()[0]["age_months"]),
        consent_id=None,
        expected_revision=1,
    )


def test_s10_notification_specs_pass_the_real_domain_command_validator() -> None:
    for spec in s10_inbox_data.ITEMS:
        parameters = {
            key: (
                f"seed-{spec.key}"
                if isinstance(value, str) and value.startswith(s10_inbox_data.REF)
                else value
            )
            for key, value in spec.safe_parameters.items()
        }
        validate_command(s10_inbox._command(spec, parameters), created_at=spec.created_at)


def test_s11_lesson_and_share_commands_pass_product_validators() -> None:
    for content in s11_org_run_shares_data.LESSON_CONTENTS.values():
        _validated_lesson_content(content)
    ParentStoryRunService._normalize_create_values(
        topic=s11_org_run_shares_data.TEACHER_RUN_TOPIC,
        adult_confirmed_idea=s11_org_run_shares_data.TEACHER_RUN_IDEA,
        intended_drawing_subject=None,
    )
    ParentStoryRunCancelRequestV1(expected_revision=s11_org_run_shares_data.TEACHER_RUN_REVISION)
    validate_idempotency_key(s11_org_run_shares_data.TEACHER_RUN_CANCEL_KEY)

    for spec in s11_org_run_shares_data.PRIVATE_SHARE_SPECS:
        CreateLessonAccessGrantRequestV1(
            version_id=data.version_id(str(spec["lesson_key"]), 1),
            audience_kind=spec["audience_kind"],
            audience_ref=spec["audience_ref"],
            capability=spec["capability"],
        )
    for lesson_key in s11_org_run_shares_data.REVIEW_REQUEST_LESSONS:
        CreateLessonAccessGrantRequestV1(
            version_id=data.version_id(lesson_key, 1),
            audience_kind="PUBLIC",
            audience_ref=None,
            capability="VIEW",
        )
    DecideLessonAccessGrantRequestV1(
        decision="REQUEST_CHANGES",
        reason=s11_org_run_shares_data.REVIEW_CHANGE_REASON,
    )


def test_s12_lesson_age_bands_suggestions_and_fixture_hashes_validate_offline() -> None:
    content = {
        **s12_story_v4a_data.LESSON_CONTENT,
        "activities": list(s12_story_v4a_data.LESSON_ACTIVITIES),
    }
    normalized_content = _validated_lesson_content(content)
    assert canonical_content_hash(normalized_content) == s12_story_v4a_data.LESSON_CONTENT_HASH

    parent = s12_story_v4a_data.PARENTS_BY_KEY["p6"]
    bundle = s12_story_v4a_data.build_static_fixture_bundle()
    run_input = next(
        row
        for row in bundle["run_inputs"]
        if row["run_id"] == s12_story_v4a_data.RUN_STARTED_ID
    )
    understanding = next(
        row
        for row in bundle["understandings"]
        if row["run_id"] == s12_story_v4a_data.RUN_STARTED_ID
    )
    visible_features = understanding["result_snapshot"]["result"]["visible_features"]
    age_band = _age_band_months(parent.age_months)
    catalog_candidates = [
        ParentActivityCatalogCandidateV2.model_validate(
            {
                "candidate_ref": f"C{index:03d}",
                "lesson_topic": s12_story_v4a_data.LESSON_CONTENT["topic"],
                "drawing_subject": s12_story_v4a_data.LESSON_CONTENT["drawing_subject"],
                "age_band_months": age_band,
                "activity": activity,
            }
        )
        for index, activity in enumerate(s12_story_v4a_data.LESSON_ACTIVITIES, start=1)
    ]
    ParentActivitySuggestionWorkerRequestV3.model_validate(
        {
            "schema_version": "sketch2life.parent-activity-suggest-input.v3",
            "age_band_months": age_band,
            "age_band_ref": s12_story_v4a_data.OUTDOOR_AGE_BAND_REF,
            "topic": s12_story_v4a_data.LESSON_CONTENT["topic"],
            "adult_confirmed_idea": run_input["typed_idea"],
            "confirmed_subject": understanding["subject_label"],
            "visible_features": visible_features,
            "profile_interest_tags": [],
            "narration_interest_tags": [],
            "candidate_activities": [
                candidate.model_dump(mode="python") for candidate in catalog_candidates
            ],
        }
    )

    activity = s12_story_v4a_data.LESSON_ACTIVITIES[0]
    suggested_activity = ParentSuggestedActivityV2.model_validate(
        {
            **activity,
            "source": "PUBLISHED_SHARED_LESSON",
            "source_lesson_id": s12_story_v4a_data.LESSON_ID,
            "source_lesson_title": s12_story_v4a_data.LESSON_CONTENT["title"],
            "source_lesson_version_id": s12_story_v4a_data.LESSON_VERSION_ID,
            "source_content_sha256": s12_story_v4a_data.LESSON_CONTENT_HASH,
            "source_activity_index": 0,
            "match_reason": s12_story_v4a_data.PARENT_ACTIVITY_MATCH_REASON,
        }
    )
    activities = [suggested_activity.model_dump(mode="python")]
    activity_bytes = json.dumps(
        activities, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    ParentActivitySuggestionSetV1.model_validate(
        {
            "contract": "ParentActivitySuggestionSetV1",
            "request_id": s12_story_v4a_data.PARENT_ACTIVITY_REQUEST_ID,
            "story_run_id": s12_story_v4a_data.RUN_STARTED_ID,
            "suggestion_set_id": s12_story_v4a_data.s12_uuid_text("suggestion-set:started:1"),
            "set_revision": 1,
            "understanding_revision": 1,
            "selection_mode": "CATALOG_SELECTION",
            "catalog_candidate_count": len(catalog_candidates),
            "activities_snapshot_sha256": hashlib.sha256(activity_bytes).hexdigest(),
            "review_required": True,
            "modal_call_id": None,
            "activities": activities,
        }
    )

    for row in bundle["activity_selections"]:
        assert data.sha256_json(row["activity_snapshot"]) == row["activity_snapshot_sha256"]


def test_s13_policy_context_sharing_feedback_and_billing_inputs_validate_offline() -> None:
    ParentConsentPolicyCreateRequestV1.model_validate(
        {
            "policy_version": s13_system_demo_data.CONSENT_POLICY_VERSION,
            "consent_text": s13_system_demo_data.CONSENT_POLICY_TEXT,
        }
    )
    policy_repository = type(
        "PolicyRepository",
        (),
        {"create_draft": lambda self, **kwargs: kwargs},
    )()
    ParentConsentPolicyService(policy_repository).create_draft(
        version=s13_system_demo_data.CONSENT_POLICY_VERSION,
        text=s13_system_demo_data.CONSENT_POLICY_TEXT,
        actor_subject=data.PLATFORM_ADMIN_SUBJECT,
    )

    context_entry = validate_entry(
        ContextEntryDraft(
            entry_kind="OBSERVATION",
            short_text=s13_system_demo_data.PARENT_CONTEXT_ENTRY_TEXT,
            source_kind=s13_system_demo_data.PARENT_CONTEXT_ENTRY_SOURCE_KIND,
            source_ref=None,
            approximate_date=data.SEED_TIME.date(),
        )
    )
    assert context_entry.short_text == s13_system_demo_data.PARENT_CONTEXT_ENTRY_TEXT
    validate_idempotency_key(s13_system_demo_data.PARENT_CONTEXT_ENTRY_IDEMPOTENCY_KEY)

    share_request = CreateShareGrantRequestV1.model_validate(
        {
            "profile_id": str(data.parent_profile_id(s13_system_demo_data.PARENT_PROFILE_KEY)),
            "granted_fields": list(s13_system_demo_data.PARENT_SHARE_GRANTED_FIELDS),
        }
    )
    assert normalize_granted_fields(share_request.granted_fields) == ("AGE_BAND", "DISPLAY_NAME")
    FeedbackInput.model_validate({"body": s13_system_demo_data.PARENT_FEEDBACK_TEXT})

    for product in s13_system_demo_data.QUOTA_PRODUCTS:
        QuotaProductInput.model_validate(dict(product))
    CapacityPriceInput.model_validate(dict(s13_system_demo_data.CAPACITY_PRICE))
    CapacityQuoteInput.model_validate(
        {
            "mode": "START",
            "organization_ref": data.org_id("a"),
            "price_id": data.seed_uuid_text("s13:capacity-price-validation"),
            "addon_slots": 0,
        }
    )
    SandboxPaymentInput.model_validate(
        {
            "event_id": s13_system_demo_data.CAPACITY_PAYMENT_EVENT_ID,
            "paid": True,
            "amount_vnd": s13_system_demo_data.CAPACITY_PRICE["base_amount_vnd"],
        }
    )
    for owner_kind, owner_ref, units in (
        (
            "PARENT_ACCOUNT",
            data.parent_account_id(s13_system_demo_data.PARENT_KEY),
            s13_system_demo_data.PARENT_QUOTA_UNITS,
        ),
        ("ORGANIZATION", data.org_id("a"), s13_system_demo_data.ORGANIZATION_QUOTA_UNITS),
    ):
        IncludedQuotaInput.model_validate(
            {"owner_kind": owner_kind, "owner_ref": owner_ref, "units": units}
        )
    QuotaAllocationInput.model_validate(
        {
            "teacher_ref": data.ORG_A_TEACHERS[0],
            "units": s13_system_demo_data.TEACHER_QUOTA_UNITS,
        }
    )


def test_seed2_abc_orders_all_fresh_database_prerequisites_before_s13() -> None:
    names = [name for name, _runner in seed2_abc.STAGES]
    assert names == [
        "s8_lessons",
        "s9_classes",
        "s7b_story_states",
        "s10_inbox",
        "s11_org_run_shares",
        "s12_story_v4a",
        "s13_system_demo",
    ]
    assert names.index("s7b_story_states") < names.index("s10_inbox")
    assert names.index("s8_lessons") < names.index("s10_inbox")
    assert names.index("s12_story_v4a") < names.index("s13_system_demo")
