import json
from contextlib import contextmanager
from dataclasses import replace

import pytest

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.services.knowledge_bundle import (
    CreateKnowledgeCommand,
    EditKnowledgeCommand,
    KnowledgeBundleError,
)
from sketch2life.contracts.schemas.knowledge_bundles import (
    ClaimEditV1,
    EditKnowledgeBundleV1,
    FactSectionV1,
    KnowledgeSourceRefV1,
    StorySectionV1,
)
from sketch2life.infrastructure.knowledge_bundle.harness import (
    FACT_TEXT,
    ORG,
    SESSION,
    TEACHER_A,
    TEACHER_B,
    KnowledgeHarness,
    build_knowledge_harness,
)


def create(harness: KnowledgeHarness, key: str = "create-key", *, child: bool = False):  # type: ignore[no-untyped-def]
    return harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, key, harness.create_body(child=child))
    )


def etag(harness: KnowledgeHarness, bundle_id: str) -> str:
    return harness.repository.snapshot().heads[bundle_id].etag


def correction(
    harness: KnowledgeHarness, text: str = "Mèo thuộc nhóm động vật có vú."
) -> EditKnowledgeBundleV1:
    pin = harness.source.ref
    return EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Teacher source correction",
        claims=(
            ClaimEditV1(
                claim_id=harness.claim.claim_id,
                revision=2,
                text=text,
                source_refs=(
                    KnowledgeSourceRefV1(
                        source_id=pin.source_id, revision=pin.revision, sha256=pin.sha256
                    ),
                ),
                attestation_reason="Teacher accountable for source-grounded attestation",
            ),
        ),
    )


def test_generic_create_sourced_v1_server_attribution_zero_actual_consent() -> None:
    harness = build_knowledge_harness()
    assert harness.facts.consent_calls == 0
    result = create(harness)
    assert result.status == 201 and not result.replayed
    record = result.record
    assert record.bundle_version == record.editorial_revision == 1
    assert record.readiness == "generation_ready" and record.script_text == FACT_TEXT
    assert record.created_by == TEACHER_A.principal_id and record.content_origin == "generic"
    assert record.contributors == () and harness.facts.consent_calls == 0
    state = harness.repository.snapshot()
    assert len(state.heads) == len(state.versions) == len(state.receipts) == len(state.audit) == 1
    assert state.corrections == state.outbox == {}


def test_child_exact_contributors_snapshot_confirmation_and_purpose() -> None:
    harness = build_knowledge_harness()
    result = create(harness, child=True)
    assert result.record.content_origin == "child_derived"
    assert tuple(item.participant_id for item in result.record.contributors) == (
        "child-a",
        "child-b",
    )
    assert tuple(item.snapshot_ref for item in result.record.contributors) == (
        "snapshot-a",
        "snapshot-b",
    )
    assert all(item.purpose_code == "knowledge_media" for item in result.record.contributors)
    assert result.record.confirmation_ref == "teacher-confirmation-1"
    assert harness.facts.consent_calls >= 2


def test_one_child_revocation_fails_entire_create_and_preserves_empty_store() -> None:
    harness = build_knowledge_harness()
    harness.facts.publish_consent(ORG, SESSION, harness.child_basis.contributors[1], False)
    with pytest.raises(KnowledgeBundleError) as failure:
        create(harness, child=True)
    assert failure.value.code == "CONSENT_REQUIRED"
    assert harness.repository.snapshot().versions == harness.repository.snapshot().receipts == {}


@pytest.mark.parametrize("mixed_selection", [False, True])
def test_missing_source_create_is_zero_claim_draft_with_content_action(
    mixed_selection: bool,
) -> None:
    harness = build_knowledge_harness()
    result = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A,
            "missing-source",
            harness.create_body(
                catalog_claim_ids=(harness.claim.claim_id, "missing-catalog-claim")
                if mixed_selection
                else ("missing-catalog-claim",)
            ),
        )
    )
    assert result.status == 201 and result.record.readiness == "needs_content_action"
    assert result.record.knowledge_claims == result.record.script_sections == ()
    assert result.record.script_text == "" and result.record.action_code == "NO_ELIGIBLE_SOURCE"


@pytest.mark.parametrize(
    "principal",
    [
        Principal("admin", ORG, PrincipalRole.ADMIN),
        Principal("device", ORG, PrincipalRole.DEVICE),
        Principal("foreign-teacher", "foreign", PrincipalRole.TEACHER),
        Principal("ungranted-teacher", ORG, PrincipalRole.TEACHER),
    ],
)
def test_roles_foreign_scope_safe_existence_reads_and_writes(principal: Principal) -> None:
    harness = build_knowledge_harness()
    own = create(harness)
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.create(
            CreateKnowledgeCommand(principal, "foreign-create", harness.create_body())
        )
    assert failure.value.status == 404
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                principal,
                own.record.bundle_id,
                "foreign-edit",
                etag(harness, own.record.bundle_id),
                correction(harness),
            )
        )
    assert failure.value.status == 404
    hidden = harness.service.read(principal, own.record.bundle_id)
    missing = harness.service.read(principal, "missing-bundle")
    assert not hidden.ready and hidden.export is None and hidden.reason == missing.reason
    assert harness.repository.snapshot() == before


def test_cross_session_and_client_attribution_json_fail_without_receipt() -> None:
    harness = build_knowledge_harness()
    payload = harness.create_body().model_dump(mode="json")
    for field in (
        "created_by",
        "organization_id",
        "contributors",
        "content_origin",
        "confirmed_topic",
    ):
        with pytest.raises(KnowledgeBundleError) as failure:
            harness.service.create(
                CreateKnowledgeCommand(
                    TEACHER_A, "injected", json.dumps({**payload, field: "injected"})
                )
            )
        assert failure.value.code == "FIELD_NOT_ALLOWED"
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.create(
            CreateKnowledgeCommand(
                TEACHER_A, "cross-session", json.dumps({**payload, "session_id": "other"})
            )
        )
    assert failure.value.status == 404
    assert harness.repository.snapshot().receipts == {}


def test_edit_attestation_projection_v1_immutable_correction_and_exact_event() -> None:
    harness = build_knowledge_harness()
    original = create(harness)
    old = harness.repository.snapshot().versions[(original.record.bundle_id, 1)]
    result = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            original.record.bundle_id,
            "edit-key",
            etag(harness, original.record.bundle_id),
            correction(harness),
        )
    )
    assert result.status == 200 and result.record.bundle_version == 2
    assert result.record.knowledge_claims[0].verification_state == "teacher_attested"
    assert result.record.knowledge_claims[0].attested_by == TEACHER_A.principal_id
    assert result.record.script_text == "Mèo thuộc nhóm động vật có vú."
    state = harness.repository.snapshot()
    assert state.versions[(old.bundle_id, 1)].canonical_bytes == old.canonical_bytes
    assert len(state.corrections) == len(state.outbox) == 1
    event = next(iter(state.outbox.values()))
    assert (
        event.old_bundle.bundle_id,
        event.old_bundle.bundle_version,
        event.old_bundle.bundle_hash,
    ) == (old.bundle_id, 1, old.bundle_hash)
    assert (event.new_bundle.bundle_version, event.new_bundle.bundle_hash) == (
        2,
        result.record.bundle_hash,
    )


def test_old_teacher_attestation_survives_other_teacher_section_edit() -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    second = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            first.record.bundle_id,
            "teacher-a-edit",
            etag(harness, first.record.bundle_id),
            correction(harness),
        )
    )
    body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Teacher B sections",
        sections=(
            FactSectionV1(section_id="teacher-b-fact", claim_refs=(harness.claim.claim_id,)),
        ),
    )
    third = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_B,
            first.record.bundle_id,
            "teacher-b-edit",
            etag(harness, first.record.bundle_id),
            body,
        )
    )
    assert third.record.bundle_version == 3
    assert third.record.knowledge_claims == second.record.knowledge_claims
    assert third.record.knowledge_claims[0].attested_by == TEACHER_A.principal_id
    assert third.record.teacher_corrections[-1].author_principal_id == TEACHER_B.principal_id
    assert harness.service.read(TEACHER_B, first.record.bundle_id).ready


def test_noop_has_no_cas_commit_version_correction_receipt_audit_or_event() -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    before = harness.repository.snapshot()
    commits = harness.repository.commits
    stored = before.versions[(first.record.bundle_id, 1)]
    body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="No semantic change",
        sections=tuple(
            FactSectionV1(section_id=section.section_id, claim_refs=section.claim_refs)
            for section in stored.sections
        ),
    )
    result = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            first.record.bundle_id,
            "noop-key",
            etag(harness, first.record.bundle_id),
            body,
        )
    )
    assert result.no_content_change and not result.replayed
    assert result.code == "NO_CONTENT_CHANGE"
    assert harness.repository.snapshot() == before
    assert harness.repository.commits == commits


@pytest.mark.parametrize(
    ("header", "status", "code"),
    [
        (None, 428, "PRECONDITION_REQUIRED"),
        ('"wrong-family:1"', 412, "PRECONDITION_FAILED"),
    ],
)
def test_edit_preconditions_typed_and_no_failed_receipt(
    header: str | None, status: int, code: str
) -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A, first.record.bundle_id, "bad-precondition", header, correction(harness)
            )
        )
    assert (failure.value.status, failure.value.code) == (status, code)
    assert harness.repository.snapshot() == before


def test_accepted_replay_original_after_head_advance_pause_and_stale_ifmatch() -> None:
    harness = build_knowledge_harness()
    body = harness.create_body()
    first = harness.service.create(CreateKnowledgeCommand(TEACHER_A, "accepted-create", body))
    old_etag = etag(harness, first.record.bundle_id)
    edit_body = correction(harness)
    second = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A, first.record.bundle_id, "accepted-edit", old_etag, edit_body
        )
    )
    harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            first.record.bundle_id,
            "third",
            etag(harness, first.record.bundle_id),
            correction(harness, "Mèo là một loài động vật có vú."),
        )
    )
    harness.facts.publish_mutation(ORG, SESSION, False)
    before = harness.repository.snapshot()
    replay_create = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "accepted-create", body)
    )
    replay_edit = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A, first.record.bundle_id, "accepted-edit", old_etag, edit_body
        )
    )
    assert replay_create.replayed and replay_create.result == first.result
    assert replay_edit.replayed and replay_edit.result == second.result
    assert replay_create.record.bundle_version == 1 and replay_edit.record.bundle_version == 2
    assert harness.repository.snapshot() == before
    with pytest.raises(KnowledgeBundleError):
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A, first.record.bundle_id, "fresh-paused", old_etag, edit_body
            )
        )


def test_different_body_same_key_conflicts_failed_attempt_key_reusable() -> None:
    harness = build_knowledge_harness()
    original = create(harness, "same-key")
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.create(
            CreateKnowledgeCommand(TEACHER_A, "same-key", harness.create_body(catalog_claim_ids=()))
        )
    assert (failure.value.status, failure.value.code) == (409, "IDEMPOTENCY_PAYLOAD_MISMATCH")
    assert harness.repository.snapshot() == before
    bad_body = harness.create_body().model_copy(update={"expected_context_revision": 1})
    with pytest.raises(KnowledgeBundleError):
        harness.service.create(CreateKnowledgeCommand(TEACHER_A, "reusable-key", bad_body))
    assert all(key[-1] != "reusable-key" for key in harness.repository.snapshot().receipts)
    retry = create(harness, "reusable-key")
    assert retry.status == 201 and retry.record.bundle_id != original.record.bundle_id


def test_disclosure_withdrawal_denies_replay_for_teacher_and_sticky_child_contributors() -> None:
    for child in (False, True):
        harness = build_knowledge_harness()
        body = harness.create_body(child=child)
        first = harness.service.create(CreateKnowledgeCommand(TEACHER_A, "receipt", body))
        if child:
            harness.facts.publish_consent(
                ORG, SESSION, harness.child_basis.contributors[1], False, disclose=False
            )
        else:
            harness.facts.publish_disclosure(ORG, SESSION, TEACHER_A.principal_id, False)
        with pytest.raises(KnowledgeBundleError) as failure:
            harness.service.create(CreateKnowledgeCommand(TEACHER_A, "receipt", body))
        assert failure.value.status == 404
        assert not harness.service.read(TEACHER_A, first.record.bundle_id).ready


def test_storage_failure_rollback_and_retry_without_duplicate_success() -> None:
    harness = build_knowledge_harness()
    harness.repository.fail_next("put_receipt")
    with pytest.raises(KnowledgeBundleError) as failure:
        create(harness, "storage-retry")
    assert (failure.value.status, failure.value.code) == (503, "STORAGE_UNAVAILABLE")
    assert harness.repository.snapshot().versions == harness.repository.snapshot().receipts == {}
    result = create(harness, "storage-retry")
    assert result.status == 201
    replay = create(harness, "storage-retry")
    assert replay.replayed and len(harness.repository.snapshot().versions) == 1


@pytest.mark.parametrize(
    ("pin_change", "source_change", "code"),
    [
        ({"source_id": "missing"}, {}, "SOURCE_MISSING"),
        ({"revision": 2}, {}, "SOURCE_REVISION_MISMATCH"),
        ({"sha256": "0" * 64}, {}, "SOURCE_HASH_MISMATCH"),
        ({}, {"state": "unreviewed"}, "SOURCE_NOT_REVIEWED"),
        ({}, {"recalled": True}, "SOURCE_RECALLED"),
        ({}, {"topic": "Dogs"}, "SOURCE_TOPIC_MISMATCH"),
        ({}, {"age_bands": ("age-4",)}, "SOURCE_AGE_MISMATCH"),
    ],
)
def test_explicit_invalid_source_edit_rejects_atomically(
    pin_change: dict[str, object], source_change: dict[str, object], code: str
) -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    body = correction(harness)
    if pin_change:
        claim = body.claims[0]
        body = body.model_copy(
            update={
                "claims": (
                    claim.model_copy(
                        update={
                            "source_refs": (claim.source_refs[0].model_copy(update=pin_change),)
                        }
                    ),
                )
            }
        )
    if source_change:
        harness.facts.publish_source(replace(harness.source, **source_change))
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "bad-source",
                etag(harness, first.record.bundle_id),
                body,
            )
        )
    assert failure.value.code == code
    assert harness.repository.snapshot() == before


def test_changed_confirmation_same_revision_withholds_content_and_does_not_write() -> None:
    harness = build_knowledge_harness()
    first = create(harness, child=True)
    before = harness.repository.snapshot()
    harness.facts.publish_basis(
        replace(harness.child_basis, confirmation_ref="different-confirmation")
    )
    result = harness.service.read(TEACHER_A, first.record.bundle_id)
    assert not result.ready and result.export is None
    assert harness.repository.snapshot() == before


@pytest.mark.parametrize(
    "document",
    [
        '{"session_id":"session","session_id":"other"}',
        '{"é":1,"e\\u0301":2}',
        '{"expected_context_revision":NaN}',
        " " * 196609,
    ],
    ids=("duplicate-key", "nfc-key-collision", "non-native-number", "document-overflow"),
)
def test_raw_duplicate_normalized_keys_non_native_and_document_overflow_reject(
    document: str,
) -> None:
    harness = build_knowledge_harness()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.create(CreateKnowledgeCommand(TEACHER_A, "bad-document", document))
    assert failure.value.status == 400
    assert harness.repository.snapshot().versions == harness.repository.snapshot().receipts == {}


def test_create_key_required_precondition_forbidden_and_principal_receipt_scopes_independent() -> (
    None
):
    harness = build_knowledge_harness()
    for key, if_match, code in [
        (None, None, "FIELD_VALIDATION_FAILED"),
        ("fresh-key", '"knowledge-bundle:other:1:1"', "CREATE_PRECONDITION_NOT_ALLOWED"),
    ]:
        with pytest.raises(KnowledgeBundleError) as failure:
            harness.service.create(
                CreateKnowledgeCommand(TEACHER_A, key, harness.create_body(), if_match)
            )
        assert failure.value.code == code
    first = create(harness, "cross-principal-key")
    other = harness.service.create(
        CreateKnowledgeCommand(TEACHER_B, "cross-principal-key", harness.create_body())
    )
    assert other.status == 201 and not other.replayed
    assert first.record.bundle_id != other.record.bundle_id
    assert other.record.created_by == TEACHER_B.principal_id
    assert {key[1] for key in harness.repository.snapshot().receipts} == {
        TEACHER_A.principal_id,
        TEACHER_B.principal_id,
    }


def test_child_imagined_removed_keeps_provenance_and_cannot_become_fact() -> None:
    harness = build_knowledge_harness()
    body = harness.create_body(child=True, imagined_refs=("cat-wings",))
    first = harness.service.create(CreateKnowledgeCommand(TEACHER_A, "child-imagined", body))
    assert first.record.script_sections[1].kind == "story"
    assert first.record.script_sections[1].text == "Mèo có cánh."
    strip = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Remove selected imagined",
        imagined_refs=(),
        sections=(FactSectionV1(section_id="facts", claim_refs=(harness.claim.claim_id,)),),
    )
    second = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            first.record.bundle_id,
            "remove-imagined",
            etag(harness, first.record.bundle_id),
            strip,
        )
    )
    assert (
        second.record.child_imagined_elements == ()
        and second.record.content_origin == "child_derived"
    )
    assert second.record.contributors == first.record.contributors
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "imagined-fact",
                etag(harness, first.record.bundle_id),
                correction(harness, "Mèo có cánh."),
            )
        )
    assert failure.value.code == "IMAGINED_AS_FACT"
    assert harness.repository.snapshot() == before
    harness.facts.publish_consent(
        ORG, SESSION, harness.child_basis.contributors[1], False, disclose=False
    )
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(TEACHER_A, first.record.bundle_id, "remove-imagined", None, strip)
        )
    assert failure.value.status == 404


@pytest.mark.parametrize(
    "claim_text",
    [
        "Mèo có cánh",
        "Mèo  có cánh.",
        "Mèo có c\u200bánh.",
        "Ｍèo có cánh.",
        "Mèo,có cánh.",
        "Mèo có cá.nh.",
        "Mèo có c\u034fánh.",
        "Mèo có c\ufe0fánh.",
        "Mèo có c\u180bánh.",
        "Mèo có c\u3164ánh.",
        "Me\u034f\u0300o có cánh.",
    ],
)
def test_imagined_fact_tiny_variants_reject_after_selection_removed(claim_text: str) -> None:
    harness = build_knowledge_harness()
    first = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A, "variant-create", harness.create_body(child=True, imagined_refs=())
        )
    )
    before = harness.repository.snapshot()
    commits = harness.repository.commits
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "variant-edit",
                etag(harness, first.record.bundle_id),
                correction(harness, claim_text),
            )
        )
    assert failure.value.code == "IMAGINED_AS_FACT"
    assert harness.repository.snapshot() == before and harness.repository.commits == commits


@pytest.mark.parametrize(
    "imagined_text",
    [
        "Mèo có c\u034fánh.",
        "Mèo có c\ufe0fánh.",
        "Mèo có c\u180bánh.",
        "Mèo có c\u3164ánh.",
        "Me\u034f\u0300o có cánh.",
    ],
)
def test_obfuscated_trusted_imagined_text_cannot_become_fact(imagined_text: str) -> None:
    harness = build_knowledge_harness()
    harness.facts.publish_basis(
        replace(
            harness.child_basis,
            imagined_elements=(
                replace(harness.child_basis.imagined_elements[0], text=imagined_text),
            ),
        )
    )
    first = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A, "obfuscated-basis-create", harness.create_body(child=True, imagined_refs=())
        )
    )
    before = harness.repository.snapshot()
    commits = harness.repository.commits
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "obfuscated-basis-edit",
                etag(harness, first.record.bundle_id),
                correction(harness, "Mèo có cánh."),
            )
        )
    assert failure.value.code == "IMAGINED_AS_FACT"
    assert harness.repository.snapshot() == before and harness.repository.commits == commits


@pytest.mark.parametrize("code_point", [0x7F, 0x80, 0x85, 0x9F])
def test_edit_handler_rejects_del_and_c1_without_writes(code_point: int) -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    payload = json.loads(correction(harness).model_dump_json())
    payload["claims"][0]["text"] = f"Mèo có c{chr(code_point)}ánh."
    before = harness.repository.snapshot()
    commits = harness.repository.commits
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "control-edit",
                etag(harness, first.record.bundle_id),
                json.dumps(payload, ensure_ascii=False),
            )
        )
    assert failure.value.status == 400 and failure.value.code == "FIELD_VALIDATION_FAILED"
    assert harness.repository.snapshot() == before and harness.repository.commits == commits


def test_fact_fragment_of_longer_imagined_literal_rejects_without_writes() -> None:
    harness = build_knowledge_harness()
    harness.facts.publish_basis(
        replace(
            harness.child_basis,
            imagined_elements=(
                replace(
                    harness.child_basis.imagined_elements[0],
                    text="Mèo có cánh và bay qua mặt trăng.",
                ),
            ),
        )
    )
    first = create(harness, child=True)
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError) as failure:
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "imagined-fragment",
                etag(harness, first.record.bundle_id),
                correction(harness, "Mèo có cánh."),
            )
        )
    assert failure.value.code == "IMAGINED_AS_FACT"
    assert harness.repository.snapshot() == before


def test_unchanged_claim_resubmission_is_noop_and_mixed_edit_preserves_original_attestor() -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    body = correction(harness)
    second = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            first.record.bundle_id,
            "a-attests",
            etag(harness, first.record.bundle_id),
            body,
        )
    )
    before = harness.repository.snapshot()
    commits = harness.repository.commits
    same = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_B,
            first.record.bundle_id,
            "b-resubmits",
            etag(harness, first.record.bundle_id),
            body.model_copy(update={"correction_reason": "B retains A's unchanged claim"}),
        )
    )
    assert same.no_content_change and same.record == second.record
    assert harness.repository.snapshot() == before and harness.repository.commits == commits
    added = body.claims[0].model_copy(
        update={
            "claim_id": "cats-fur",
            "revision": 1,
            "text": "Mèo có lông.",
            "attestation_reason": "B is accountable for the new claim",
        }
    )
    third = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_B,
            first.record.bundle_id,
            "b-adds",
            etag(harness, first.record.bundle_id),
            body.model_copy(
                update={
                    "claims": (*body.claims, added),
                    "sections": (
                        FactSectionV1(
                            section_id="both-facts",
                            claim_refs=(harness.claim.claim_id, "cats-fur"),
                        ),
                    ),
                    "correction_reason": "B adds a sourced claim while retaining A's claim",
                }
            ),
        )
    )
    assert third.record.bundle_version == 3
    assert third.record.knowledge_claims[0] == second.record.knowledge_claims[0]
    assert third.record.knowledge_claims[0].attested_by == TEACHER_A.principal_id
    assert third.record.knowledge_claims[1].attested_by == TEACHER_B.principal_id
    assert (
        harness.repository.snapshot().versions[(first.record.bundle_id, 2)]
        == before.versions[(first.record.bundle_id, 2)]
    )


def test_mutation_only_pause_preserves_current_reads_and_replay_but_denies_new_writes() -> None:
    harness = build_knowledge_harness()
    first = create(harness, child=True)
    harness.facts.publish_mutation(ORG, SESSION, False)
    before = harness.repository.snapshot()
    for resolution in (
        harness.service.read(TEACHER_A, first.record.bundle_id),
        harness.service.resolve_exact(
            TEACHER_A, first.record.bundle_id, 1, first.record.bundle_hash
        ),
    ):
        assert resolution.ready and resolution.reason is None and resolution.export is not None
        assert resolution.export.bundle_hash == first.record.bundle_hash
    replay = create(harness, child=True)
    assert replay.replayed and replay.result == first.result
    with pytest.raises(KnowledgeBundleError, match="MUTATION_PAUSED"):
        create(harness, "paused-fresh-create", child=True)
    with pytest.raises(KnowledgeBundleError, match="MUTATION_PAUSED"):
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "paused-fresh-edit",
                etag(harness, first.record.bundle_id),
                correction(harness),
            )
        )
    assert harness.repository.snapshot() == before
    harness.facts.publish_source(replace(harness.source, recalled=True))
    denied = harness.service.resolve_exact(
        TEACHER_A, first.record.bundle_id, 1, first.record.bundle_hash
    )
    assert not denied.ready and denied.export is None and denied.reason == "SOURCE_RECALLED"


def test_story_only_record_and_resolver_return_fact_section_content_action() -> None:
    harness = build_knowledge_harness()
    first = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A,
            "story-only-create",
            harness.create_body(child=True, imagined_refs=("cat-wings",)),
        )
    )
    body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Retain sourced claim but use only the story section",
        sections=(StorySectionV1(section_id="story", imagined_refs=("cat-wings",)),),
    )
    header = etag(harness, first.record.bundle_id)
    command = EditKnowledgeCommand(TEACHER_A, first.record.bundle_id, "story-only", header, body)
    result = harness.service.edit(command)
    assert result.record.knowledge_claims == first.record.knowledge_claims
    assert result.record.readiness == "needs_content_action"
    assert result.record.action_code == "FACT_SECTION_REQUIRED"
    before = harness.repository.snapshot()
    for resolution in (
        harness.service.read(TEACHER_A, first.record.bundle_id),
        harness.service.resolve_exact(
            TEACHER_A, first.record.bundle_id, 2, result.record.bundle_hash
        ),
    ):
        assert not resolution.ready and resolution.export is None
        assert resolution.reason == result.record.action_code
    assert harness.service.edit(command).result == result.result
    assert harness.repository.snapshot() == before


def test_recalled_bundle_requires_new_bundle_with_eligible_sources() -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    replacement_source = replace(
        harness.source,
        ref=replace(harness.source.ref, source_id="source-replacement", sha256="b" * 64),
    )
    replacement_claim = replace(
        harness.claim, claim_id="cats-replacement", source_refs=(replacement_source.ref,)
    )
    harness.facts.publish_source(replace(harness.source, recalled=True))
    harness.facts.publish_source(replacement_source)
    harness.facts.publish_catalog_claim(replacement_claim)
    body = correction(harness)
    item = body.claims[0].model_copy(
        update={
            "source_refs": (
                KnowledgeSourceRefV1(
                    source_id=replacement_source.ref.source_id,
                    revision=replacement_source.ref.revision,
                    sha256=replacement_source.ref.sha256,
                ),
            )
        }
    )
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError, match="SOURCE_RECALLED"):
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "repair-recalled",
                etag(harness, first.record.bundle_id),
                body.model_copy(update={"claims": (item,)}),
            )
        )
    assert harness.repository.snapshot() == before
    fresh = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A,
            "replacement-bundle",
            harness.create_body(catalog_claim_ids=(replacement_claim.claim_id,)),
        )
    )
    assert fresh.record.bundle_id != first.record.bundle_id
    assert fresh.record.readiness == "generation_ready"
    assert fresh.record.source_records[0].ref.source_id == replacement_source.ref.source_id


@pytest.mark.parametrize("changed", ["audience", "source_record"])
def test_same_revision_fact_changes_deny_current_read_and_edit_without_writes(changed: str) -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    if changed == "audience":
        harness.facts.publish_audience(
            replace(
                harness.audience,
                members=(
                    *harness.audience.members,
                    replace(harness.audience.members[-1], participant_id="extra-child"),
                ),
            )
        )
        code = "AUDIENCE_CHANGED"
    else:
        harness.facts.publish_source(replace(harness.source, title="Changed source metadata"))
        code = "SOURCE_RECORD_CHANGED"
    before = harness.repository.snapshot()
    resolution = harness.service.read(TEACHER_A, first.record.bundle_id)
    assert not resolution.ready and resolution.export is None and resolution.reason == code
    with pytest.raises(KnowledgeBundleError, match=code):
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "changed-pin",
                etag(harness, first.record.bundle_id),
                correction(harness),
            )
        )
    assert harness.repository.snapshot() == before


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("expected_context_revision", "CONTEXT_REVISION_MISMATCH"),
        ("expected_audience_revision", "AUDIENCE_REVISION_MISMATCH"),
    ],
)
def test_edit_expected_revision_mismatch_rejects_atomically(field: str, code: str) -> None:
    harness = build_knowledge_harness()
    first = create(harness)
    before = harness.repository.snapshot()
    with pytest.raises(KnowledgeBundleError, match=code):
        harness.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                first.record.bundle_id,
                "stale-body-pin",
                etag(harness, first.record.bundle_id),
                correction(harness).model_copy(update={field: 99}),
            )
        )
    assert harness.repository.snapshot() == before


@pytest.mark.parametrize("corruption", ["body", "readiness", "status"])
def test_corrupt_accepted_receipt_is_rejected_without_writes(monkeypatch, corruption: str) -> None:
    harness = build_knowledge_harness()
    create(harness)
    transaction = harness.repository.transaction

    @contextmanager
    def corrupt_transaction():
        with transaction() as tx:
            get_receipt = tx.get_receipt

            def corrupt_receipt(key):
                receipt = get_receipt(key)
                if receipt is None:
                    return None
                result = receipt.result
                if corruption == "status":
                    result = replace(result, status=200)
                else:
                    update = (
                        {"created_by": "wrong-teacher"}
                        if corruption == "body"
                        else {"readiness": "unavailable", "action_code": "SOURCE_RECALLED"}
                    )
                    result = replace(result, record=result.record.model_copy(update=update))
                return replace(receipt, result=result)

            monkeypatch.setattr(tx, "get_receipt", corrupt_receipt)
            yield tx

    monkeypatch.setattr(harness.repository, "transaction", corrupt_transaction)
    before = harness.repository.snapshot()
    commits = harness.repository.commits
    with pytest.raises(KnowledgeBundleError, match="RECEIPT_CONTENT_MISMATCH"):
        create(harness)
    assert harness.repository.snapshot() == before and harness.repository.commits == commits
