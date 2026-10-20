import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.ai_contract_candidates import SHAPE_SPECS, check_shape
from sketch2life.contracts.schemas.knowledge_bundles import (
    ClaimEditV1,
    CreateKnowledgeBundleV1,
    EditKnowledgeBundleV1,
    KnowledgeBundleExportV1,
    KnowledgeBundleRecordV1,
    KnowledgeScriptProjectionV1,
    export_from_version,
    record_from_version,
)
from sketch2life.domain.knowledge_bundle import (
    AudienceContextV1,
    AudienceMemberV1,
    FactSection,
    KnowledgeBasisV1,
    KnowledgeBundleVersion,
    ReviewedClaimV1,
    ReviewedSourceV1,
    SourceRefV1,
    build_version,
    catalog_claim,
)


def create_payload() -> dict[str, object]:
    return {
        "session_id": "session",
        "basis_ref": {"kind": "teacher_topic", "ref": "topic", "revision": 1},
        "expected_context_revision": 0,
        "expected_audience_revision": 0,
    }


def test_strict_basis_union_and_context_zero() -> None:
    command = CreateKnowledgeBundleV1.model_validate(create_payload())
    assert command.basis_ref.kind == "teacher_topic"
    assert command.expected_context_revision == 0
    with pytest.raises(ValidationError):
        CreateKnowledgeBundleV1.model_validate(
            {**create_payload(), "expected_context_revision": True}
        )


@pytest.mark.parametrize(
    "field", ["organization_id", "created_by", "contributors", "topic", "content_origin"]
)
def test_client_cannot_override_trusted_scope_attribution_or_topic(field: str) -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        CreateKnowledgeBundleV1.model_validate({**create_payload(), field: "injected"})
    payload = create_payload()
    payload["basis_ref"] = {
        "kind": "confirmed_meaning",
        "ref": "meaning",
        "revision": 1,
        field: "injected",
    }
    with pytest.raises(ValidationError, match="Extra inputs"):
        CreateKnowledgeBundleV1.model_validate(payload)


def test_claim_command_forbids_server_verification_and_duplicate_sources() -> None:
    pin = {"source_id": "source", "revision": 1, "sha256": "a" * 64}
    payload = {
        "claim_id": "claim",
        "revision": 1,
        "text": "Cats are mammals.",
        "source_refs": (pin,),
    }
    assert ClaimEditV1.model_validate(payload).source_refs[0].source_id == "source"
    for field in ("verification_state", "attested_by", "reviewed", "recalled"):
        with pytest.raises(ValidationError, match="Extra inputs"):
            ClaimEditV1.model_validate({**payload, field: "injected"})
    with pytest.raises(ValidationError, match="duplicate source"):
        ClaimEditV1.model_validate({**payload, "source_refs": (pin, pin)})
    with pytest.raises(ValidationError):
        ClaimEditV1.model_validate({**payload, "text": "x" * 401})


@pytest.mark.parametrize("code_point", [0x00, 0x1F, 0x7F, 0x80, 0x85, 0x9F])
@pytest.mark.parametrize("field", ["text", "attestation_reason"])
def test_claim_text_controls_include_del_and_c1(code_point: int, field: str) -> None:
    payload = {
        "claim_id": "claim",
        "revision": 1,
        "text": "Mèo có lông.",
        "source_refs": ({"source_id": "source", "revision": 1, "sha256": "a" * 64},),
        "attestation_reason": "Teacher reason",
        field: f"Mèo{chr(code_point)} có lông.",
    }
    with pytest.raises(ValidationError, match="without control characters"):
        ClaimEditV1.model_validate(payload)


def test_claim_text_allows_line_feed_tab_and_vietnamese_combining_marks() -> None:
    original = "Me\u0300o\nco\u0301\tlo\u0302ng."
    claim = ClaimEditV1.model_validate(
        {
            "claim_id": "claim",
            "revision": 1,
            "text": original,
            "source_refs": ({"source_id": "source", "revision": 1, "sha256": "a" * 64},),
            "attestation_reason": original,
        }
    )
    assert claim.text == claim.attestation_reason == original


def test_create_duplicate_claims_and_fixture_limits_reject() -> None:
    for refs in (("claim", "claim"), tuple(f"claim-{i}" for i in range(25))):
        with pytest.raises(ValidationError):
            CreateKnowledgeBundleV1.model_validate({**create_payload(), "catalog_claim_ids": refs})


def test_fact_and_story_commands_forbid_arbitrary_text_and_claims_in_story() -> None:
    payload = {
        "expected_context_revision": 0,
        "expected_audience_revision": 0,
        "correction_reason": "Correction",
    }
    for section in [
        {
            "kind": "fact",
            "section_id": "fact",
            "claim_refs": ("claim",),
            "text": "Unrelated sentence.",
        },
        {
            "kind": "story",
            "section_id": "story",
            "imagined_refs": ("wings",),
            "text": "Unrelated factual prose.",
        },
        {
            "kind": "story",
            "section_id": "story",
            "imagined_refs": ("wings",),
            "claim_refs": ("claim",),
        },
    ]:
        with pytest.raises(ValidationError, match="Extra inputs"):
            EditKnowledgeBundleV1.model_validate({**payload, "sections": (section,)})
    with pytest.raises(ValidationError, match="at least one"):
        EditKnowledgeBundleV1.model_validate(payload)


def projection_payload() -> dict[str, object]:
    return {
        "knowledge_claims": (
            {
                "claim_id": "claim",
                "revision": 1,
                "text": "Cats are mammals.",
                "source_refs": ({"source_id": "source", "revision": 1, "sha256": "a" * 64},),
                "verification_state": "catalog_reviewed",
            },
        ),
        "child_imagined_elements": ({"ref": "wings", "revision": 1, "text": "Cats have wings."},),
        "script_sections": (
            {"section_id": "fact", "kind": "fact", "refs": ("claim",), "text": "Cats are mammals."},
            {
                "section_id": "story",
                "kind": "story",
                "refs": ("wings",),
                "text": "Cats have wings.",
            },
        ),
        "script_text": "Cats are mammals.\nCats have wings.",
    }


def test_response_projection_rejects_unrelated_sentence_with_valid_claim_ref() -> None:
    good = KnowledgeScriptProjectionV1.model_validate(projection_payload())
    assert good.script_sections[0].text == "Cats are mammals."
    for kind, refs in [("fact", ("claim",)), ("story", ("wings",))]:
        with pytest.raises(ValidationError, match="exact.*projection"):
            KnowledgeScriptProjectionV1.model_validate(
                {
                    **projection_payload(),
                    "script_sections": (
                        {
                            "section_id": "section",
                            "kind": kind,
                            "refs": refs,
                            "text": "Cats fly to the moon.",
                        },
                    ),
                    "script_text": "Cats fly to the moon.",
                }
            )
    with pytest.raises(ValidationError, match="flat script"):
        KnowledgeScriptProjectionV1.model_validate(
            {**projection_payload(), "script_text": "Unrelated sentence."}
        )


def produced_version() -> KnowledgeBundleVersion:
    source = ReviewedSourceV1(
        SourceRefV1("source", 1, "a" * 64),
        "Synthetic cats",
        "fixture:cats",
        "2026-10-19",
        "cats",
        ("age-4",),
    )
    return build_version(
        bundle_id="bundle",
        basis=KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats"),
        audience=AudienceContextV1(
            "audience", "org", "session", 0, 2, (AudienceMemberV1("child", "age-4"),)
        ),
        claims=(catalog_claim(ReviewedClaimV1("claim", 1, "Cats are mammals.", (source.ref,))),),
        sources=(source,),
        sections=(FactSection("fact", ("claim",)),),
        imagined_elements=(),
        created_by="teacher",
        created_at="2026-10-19T00:00:00Z",
    )


def test_actual_data26_required_fields_and_own_strict_extension() -> None:
    record = record_from_version(produced_version())
    document = record.model_dump(mode="json")
    assert len(SHAPE_SPECS["DATA-26"].required) == 16
    assert set(SHAPE_SPECS["DATA-26"].required) <= set(document)
    assert check_shape("DATA-26", document) == []
    assert record.readiness == "generation_ready"
    assert record.context_revision == 0 and record.audience_revision == 2
    assert record.created_by == "teacher" and record.editorial_state == "draft"
    with pytest.raises(ValidationError, match="Extra inputs"):
        KnowledgeBundleRecordV1.model_validate({**record.model_dump(), "approval": "invented"})


def test_exact_export_binds_full_record_to_canonical_bytes_and_separate_digest_namespace() -> None:
    version = produced_version()
    exported = export_from_version(version)
    assert exported.canonical_json.encode() == version.canonical_bytes
    assert exported.bundle_hash == version.bundle_hash
    assert "pin_digest" not in exported.model_dump()
    # Changing both claim and projected text keeps projection valid but fails canonical binding.
    record = exported.model_dump()
    record["knowledge_claims"] = ({**record["knowledge_claims"][0], "text": "Changed."},)
    record["script_sections"] = ({**record["script_sections"][0], "text": "Changed."},)
    record["script_text"] = "Changed."
    with pytest.raises(ValidationError, match="canonical content"):
        KnowledgeBundleExportV1.model_validate(record)
    with pytest.raises(ValidationError, match="canonical bytes hash"):
        KnowledgeBundleExportV1.model_validate({**exported.model_dump(), "canonical_json": "{}"})


def test_zero_claim_draft_and_invalid_ready_source_record() -> None:
    from dataclasses import replace

    original = produced_version()
    draft = build_version(
        bundle_id="draft",
        basis=original.basis,
        audience=original.audience,
        claims=(),
        sources=(),
        sections=(),
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    record = record_from_version(draft, action_code="NO_ELIGIBLE_SOURCE")
    assert record.readiness == "needs_content_action" and record.knowledge_claims == ()
    bad_source = replace(original.source_records[0], recalled=True)
    changed = build_version(
        bundle_id="recalled",
        basis=original.basis,
        audience=original.audience,
        claims=original.knowledge_claims,
        sources=(bad_source,),
        sections=original.sections,
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    with pytest.raises(ValidationError, match="generation ready"):
        record_from_version(changed)


def test_edit_reason_and_section_collection_bounds() -> None:
    payload = {
        "expected_context_revision": 0,
        "expected_audience_revision": 0,
        "correction_reason": "Correction",
        "sections": (),
    }
    for reason in (" ", "x" * 201, "bad\x00reason"):
        with pytest.raises(ValidationError):
            EditKnowledgeBundleV1.model_validate({**payload, "correction_reason": reason})
    with pytest.raises(ValidationError):
        EditKnowledgeBundleV1.model_validate(
            {
                **payload,
                "sections": tuple(
                    {"kind": "fact", "section_id": f"section-{i}", "claim_refs": ("claim",)}
                    for i in range(33)
                ),
            }
        )


def test_record_full_basis_literal_and_hidden_imagined_metadata_rejected() -> None:
    from dataclasses import replace

    from sketch2life.domain.knowledge_bundle import ContributorV1, ImaginedElementV1

    original = produced_version()
    imagined = ImaginedElementV1("wings", 1, "Cats have wings.")
    basis = KnowledgeBasisV1(
        "meaning",
        "confirmed_meaning",
        1,
        "org",
        "session",
        "cats",
        ("snapshot",),
        (ContributorV1("child", "knowledge_media", "snapshot"),),
        (imagined,),
        confirmation_ref="confirmation",
    )
    child = build_version(
        bundle_id="child-bundle",
        basis=basis,
        audience=original.audience,
        claims=original.knowledge_claims,
        sources=original.source_records,
        sections=original.sections,
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    record = record_from_version(child)
    payload = record.model_dump()
    payload["knowledge_claims"] = (
        {
            **payload["knowledge_claims"][0],
            "text": "Cats have wings.",
            "verification_state": "teacher_attested",
            "attested_by": "teacher",
            "attestation_reason": "Reason",
        },
    )
    payload["script_sections"] = ({**payload["script_sections"][0], "text": "Cats have wings."},)
    payload["script_text"] = "Cats have wings."
    with pytest.raises(ValidationError, match="IMAGINED_AS_FACT"):
        KnowledgeBundleRecordV1.model_validate(payload)
    for version in (original, child):
        payload = record_from_version(version).model_dump()
        payload["basis_snapshot"]["imagined_elements"] = (
            {"ref": "wings", "revision": 1, "text": "Cats have wings."},
        ) * (2 if version is child else 1)
        with pytest.raises(
            ValidationError, match="DUPLICATE_REFERENCE|GENERIC_PROVENANCE_CONFLICT"
        ):
            KnowledgeBundleRecordV1.model_validate(payload)
    assert record_from_version(replace(child)).child_imagined_elements == ()


@pytest.mark.parametrize(
    "claim_text",
    [
        "Mèo có cánh",
        "Mèo  có cánh.",
        "Mèo có c\u200bánh.",
        "Ｍèo có cánh.",
        "Mèo có",
        "Mèo có c\u034fánh.",
        "Mèo có c\ufe0fánh.",
        "Mèo có c\u180bánh.",
        "Mèo có c\u3164ánh.",
        "Me\u034f\u0300o có cánh.",
    ],
)
def test_full_basis_record_rejects_tiny_imagined_literal_variants(claim_text: str) -> None:
    for obfuscate_basis in (False, True):
        _assert_full_basis_literal_rejected(claim_text, obfuscate_basis)


def _assert_full_basis_literal_rejected(claim_text: str, obfuscate_basis: bool) -> None:
    from sketch2life.domain.knowledge_bundle import ContributorV1, ImaginedElementV1

    original = produced_version()
    basis = KnowledgeBasisV1(
        "meaning",
        "confirmed_meaning",
        1,
        "org",
        "session",
        "cats",
        ("snapshot",),
        (ContributorV1("child", "knowledge_media", "snapshot"),),
        (ImaginedElementV1("wings", 1, claim_text if obfuscate_basis else "Mèo có cánh."),),
        confirmation_ref="confirmation",
    )
    child = build_version(
        bundle_id="literal-boundary",
        basis=basis,
        audience=original.audience,
        claims=original.knowledge_claims,
        sources=original.source_records,
        sections=original.sections,
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    payload = record_from_version(child).model_dump()
    claim_text = "Mèo có cánh." if obfuscate_basis else claim_text
    payload["knowledge_claims"] = (
        {
            **payload["knowledge_claims"][0],
            "text": claim_text,
            "verification_state": "teacher_attested",
            "attested_by": "teacher",
            "attestation_reason": "Reason",
        },
    )
    payload["script_sections"] = ({**payload["script_sections"][0], "text": claim_text},)
    payload["script_text"] = claim_text
    with pytest.raises(ValidationError, match="IMAGINED_AS_FACT"):
        KnowledgeBundleRecordV1.model_validate(payload)


@pytest.mark.parametrize("has_claims", [False, True])
def test_record_producer_derives_required_content_action(has_claims: bool) -> None:
    original = produced_version()
    version = build_version(
        bundle_id="content-action",
        basis=original.basis,
        audience=original.audience,
        claims=original.knowledge_claims if has_claims else (),
        sources=original.source_records if has_claims else (),
        sections=(),
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    record = record_from_version(version)
    assert record.readiness == "needs_content_action"
    assert record.action_code == ("FACT_SECTION_REQUIRED" if has_claims else "NO_ELIGIBLE_SOURCE")


@pytest.mark.parametrize(
    ("readiness", "action_code"),
    [
        ("generation_ready", "NO_ELIGIBLE_SOURCE"),
        ("needs_content_action", None),
        ("needs_content_action", "NO_ELIGIBLE_SOURCE"),
        ("unavailable", None),
    ],
)
def test_record_rejects_contradictory_readiness_action(
    readiness: str, action_code: str | None
) -> None:
    record = record_from_version(produced_version())
    with pytest.raises(ValidationError, match="readiness|action"):
        KnowledgeBundleRecordV1.model_validate(
            {**record.model_dump(), "readiness": readiness, "action_code": action_code}
        )


@pytest.mark.parametrize("has_claims", [False, True])
def test_content_action_pair_is_strict_for_each_nonready_structure(has_claims: bool) -> None:
    original = produced_version()
    version = build_version(
        bundle_id="content-action-table",
        basis=original.basis,
        audience=original.audience,
        claims=original.knowledge_claims if has_claims else (),
        sources=original.source_records if has_claims else (),
        sections=(),
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    record = record_from_version(version)
    expected = "FACT_SECTION_REQUIRED" if has_claims else "NO_ELIGIBLE_SOURCE"
    assert record.action_code == expected
    for code in (
        None,
        "WRONG_ACTION",
        "NO_ELIGIBLE_SOURCE" if has_claims else "FACT_SECTION_REQUIRED",
    ):
        with pytest.raises(ValidationError, match="readiness|action"):
            KnowledgeBundleRecordV1.model_validate({**record.model_dump(), "action_code": code})


def test_unavailable_record_requires_explicit_bounded_action_and_default_never_emits_it() -> None:
    version = produced_version()
    record = record_from_version(version)
    assert record.readiness == "generation_ready" and record.action_code is None
    for code in (None, "", " ", "x" * 121):
        with pytest.raises(ValidationError):
            KnowledgeBundleRecordV1.model_validate(
                {**record.model_dump(), "readiness": "unavailable", "action_code": code}
            )
    explicit = record_from_version(
        version, readiness="unavailable", action_code="POLICY_UNAVAILABLE"
    )
    assert explicit.readiness == "unavailable" and explicit.action_code == "POLICY_UNAVAILABLE"
