"""Producer examples built from actual deterministic commands, never handwritten records."""

from __future__ import annotations

from dataclasses import replace

from sketch2life.application.services.knowledge_bundle import (
    CreateKnowledgeCommand,
    EditKnowledgeCommand,
    KnowledgeCommandResult,
    KnowledgeResolution,
)
from sketch2life.contracts.schemas.knowledge_bundles import (
    ClaimEditV1,
    EditKnowledgeBundleV1,
    ExactKnowledgeRefV1,
    FactSectionV1,
    KnowledgeSourceRefV1,
)
from sketch2life.infrastructure.knowledge_bundle.adapters import (
    RecordingKnowledgeConsumer,
    candidate_video_pin_digest,
    candidate_video_pin_material,
)
from sketch2life.infrastructure.knowledge_bundle.harness import (
    ORG,
    SESSION,
    TEACHER_A,
    TEACHER_B,
    build_knowledge_harness,
)


def _result(result: KnowledgeCommandResult) -> dict[str, object]:
    return {
        "status": result.status,
        "replayed": result.replayed,
        "no_content_change": result.no_content_change,
        "code": result.code,
        "record": result.record.model_dump(mode="json"),
    }


def _resolution(result: KnowledgeResolution) -> dict[str, object]:
    return {
        "ready": result.ready,
        "reason": result.reason,
        "export": result.export.model_dump(mode="json") if result.export is not None else None,
    }


def build_knowledge_examples() -> dict[str, object]:
    harness = build_knowledge_harness()
    body = harness.create_body()
    first = harness.service.create(CreateKnowledgeCommand(TEACHER_A, "example-create", body))
    old_ref = ExactKnowledgeRefV1(
        bundle_id=first.record.bundle_id, bundle_version=1, bundle_hash=first.record.bundle_hash
    )
    source_pin = harness.source.ref
    edit_body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Teacher-sourced scientific wording",
        claims=(
            ClaimEditV1(
                claim_id=harness.claim.claim_id,
                revision=2,
                text="Mèo thuộc nhóm động vật có vú.",
                source_refs=(
                    KnowledgeSourceRefV1(
                        source_id=source_pin.source_id,
                        revision=source_pin.revision,
                        sha256=source_pin.sha256,
                    ),
                ),
                attestation_reason=(
                    "Teacher accepts responsibility for this explicitly sourced wording."
                ),
            ),
        ),
    )
    second = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_B,
            old_ref.bundle_id,
            "example-edit",
            harness.repository.snapshot().heads[old_ref.bundle_id].etag,
            edit_body,
        )
    )
    new_ref = ExactKnowledgeRefV1(
        bundle_id=second.record.bundle_id, bundle_version=2, bundle_hash=second.record.bundle_hash
    )
    historical_replay = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "example-create", body)
    )
    old_resolution = harness.service.resolve_exact(
        TEACHER_A, old_ref.bundle_id, 1, old_ref.bundle_hash
    )
    current_resolution = harness.service.resolve_exact(
        TEACHER_A, new_ref.bundle_id, 2, new_ref.bundle_hash
    )
    assert current_resolution.export is not None
    event = next(
        item
        for item in harness.repository.snapshot().outbox.values()
        if item.old_bundle.bundle_id == old_ref.bundle_id
    )
    consumer = RecordingKnowledgeConsumer()
    consumer.register(ORG, SESSION, old_ref)
    consumer.register(ORG, SESSION, new_ref)
    unrelated = old_ref.model_copy(update={"bundle_id": "unrelated-bundle"})
    consumer.register(ORG, SESSION, unrelated)
    old_before_delivery = consumer.is_current(ORG, SESSION, old_ref)
    first_apply, replay_apply = consumer.apply(event), consumer.apply(event)

    noop_body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Same ordered factual references",
        sections=(FactSectionV1(section_id="facts", claim_refs=(harness.claim.claim_id,)),),
    )
    before_noop, commits = harness.repository.snapshot(), harness.repository.commits
    noop = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            old_ref.bundle_id,
            "example-noop",
            harness.repository.snapshot().heads[old_ref.bundle_id].etag,
            noop_body,
        )
    )
    noop_store_unchanged = (
        before_noop == harness.repository.snapshot() and commits == harness.repository.commits
    )

    missing = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A,
            "example-missing",
            harness.create_body(catalog_claim_ids=("missing-catalog-claim",)),
        )
    )
    child = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A,
            "example-child",
            harness.create_body(child=True, imagined_refs=("cat-wings",)),
        )
    )
    child_removed = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            child.record.bundle_id,
            "example-child-remove",
            harness.repository.snapshot().heads[child.record.bundle_id].etag,
            EditKnowledgeBundleV1(
                expected_context_revision=0,
                expected_audience_revision=2,
                correction_reason="Remove selected imagined story while retaining child provenance",
                imagined_refs=(),
                sections=(FactSectionV1(section_id="facts", claim_refs=(harness.claim.claim_id,)),),
            ),
        )
    )
    harness.facts.publish_source(replace(harness.source, recalled=True))
    recalled = harness.service.resolve_exact(TEACHER_A, new_ref.bundle_id, 2, new_ref.bundle_hash)

    return {
        "scope": "FIXTURE_ONLY / 0.1-candidate",
        "limitations": [
            "Receipt readiness is historical; every current use requires authorized resolve_exact.",
            (
                "Teacher is accountable for explicitly sourced attestation; "
                "no semantic machine verification."
            ),
            (
                "Sources, identities, policy and consumer profiles are synthetic fixtures, "
                "not production adoption."
            ),
            (
                "Recording consumer proves exact event projection only; actual08 held "
                "lease/fence and delivery remain open."
            ),
        ],
        "generic_create": _result(first),
        "teacher_attested_edit": _result(second),
        "historical_accepted_create_replay": _result(historical_replay),
        "superseded_exact_without_delivery": _resolution(old_resolution),
        "current_exact_export_before_recall": _resolution(current_resolution),
        "superseded_event": event.model_dump(mode="json"),
        "recording_consumer": {
            "old_before_delivery": old_before_delivery,
            "first_apply": first_apply,
            "replayed_apply": replay_apply,
            "old_after_delivery": consumer.is_current(ORG, SESSION, old_ref),
            "new_after_delivery": consumer.is_current(ORG, SESSION, new_ref),
            "unrelated_after_delivery": consumer.is_current(ORG, SESSION, unrelated),
        },
        "candidate_video_pin": {
            "material": candidate_video_pin_material(current_resolution.export),
            "digest": candidate_video_pin_digest(current_resolution.export),
        },
        "no_content_change": {"result": _result(noop), "store_unchanged": noop_store_unchanged},
        "missing_source_draft": _result(missing),
        "child_story_create": _result(child),
        "child_imagined_removed": _result(child_removed),
        "current_exact_after_source_recall": _resolution(recalled),
    }
