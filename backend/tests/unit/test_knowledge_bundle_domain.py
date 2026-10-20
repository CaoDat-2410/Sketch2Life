import hashlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from sketch2life.domain.knowledge_bundle import (
    AudienceContextV1,
    AudienceMemberV1,
    BasisRef,
    BundleHead,
    ContributorV1,
    CorrectionV1,
    FactSection,
    ImaginedElementV1,
    KnowledgeBasisV1,
    KnowledgeBundleVersion,
    KnowledgeClaimV1,
    KnowledgeRuleViolation,
    ReviewedClaimV1,
    ReviewedSourceV1,
    SourceRefV1,
    StorySection,
    attributed_claim,
    build_version,
    canonical_bytes,
    canonical_sha256,
    catalog_claim,
    content_readiness,
    imagined_literal_overlap,
    plan_edit,
    project_script,
    validate_audience,
    validate_basis,
    validate_claims,
    verify_version,
)


def audience() -> AudienceContextV1:
    return AudienceContextV1(
        "aud",
        "org",
        "session",
        0,
        2,
        (
            AudienceMemberV1("child-a", "age-4"),
            AudienceMemberV1("child-b", "age-8"),
        ),
    )


def child_basis() -> KnowledgeBasisV1:
    return KnowledgeBasisV1(
        "meaning",
        "confirmed_meaning",
        1,
        "org",
        "session",
        "cats",
        (
            "snapshot-a",
            "snapshot-b",
        ),
        (
            ContributorV1("child-a", "knowledge_media", "snapshot-a"),
            ContributorV1("child-b", "knowledge_media", "snapshot-b"),
        ),
        confirmation_ref="teacher-confirmation-1",
    )


def test_generic_topic_has_zero_contributor_consent_calls() -> None:
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    calls: list[str] = []
    validate_basis(
        basis,
        BasisRef("teacher_topic", "topic", 1),
        audience(),
        "org",
        "session",
        lambda member: calls.append(member.participant_id) is None,
    )
    assert calls == []
    with pytest.raises(FrozenInstanceError):
        basis.topic = "changed"  # type: ignore[misc]


def test_child_basis_exact_provenance_and_every_contributor_checked() -> None:
    basis = child_basis()
    calls: list[str] = []
    validate_basis(
        basis,
        BasisRef("confirmed_meaning", "meaning", 1),
        audience(),
        "org",
        "session",
        lambda member: calls.append(member.participant_id) is None,
    )
    assert calls == ["child-a", "child-b"]
    assert tuple(item.snapshot_ref for item in basis.contributors) == basis.source_snapshot_refs
    assert basis.confirmation_ref == "teacher-confirmation-1"
    with pytest.raises(KnowledgeRuleViolation, match="CONSENT_REQUIRED"):
        validate_basis(
            basis,
            BasisRef("confirmed_meaning", "meaning", 1),
            audience(),
            "org",
            "session",
            lambda member: member.participant_id != "child-b",
        )


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"organization_id": "foreign"}, "SCOPE_MISMATCH"),
        ({"session_id": "foreign"}, "SCOPE_MISMATCH"),
        ({"revision": 2}, "BASIS_REVISION_MISMATCH"),
        ({"confirmed": False}, "BASIS_UNCONFIRMED"),
        ({"applicable": False}, "BASIS_NOT_APPLICABLE"),
    ],
)
def test_basis_current_scope_and_revision(change: dict[str, object], reason: str) -> None:
    with pytest.raises(KnowledgeRuleViolation, match=reason):
        validate_basis(
            replace(child_basis(), **change),
            BasisRef("confirmed_meaning", "meaning", 1),
            audience(),
            "org",
            "session",
            lambda _: True,
        )


def test_missing_trusted_metadata_and_per_member_purpose_membership_rejected() -> None:
    with pytest.raises(KnowledgeRuleViolation, match="TRUSTED_CONFIRMATION_REQUIRED"):
        replace(child_basis(), confirmation_ref=None)
    with pytest.raises(KnowledgeRuleViolation, match="TRUSTED_METADATA_REQUIRED"):
        replace(child_basis(), contributors=())
    for contributor, reason in [
        (ContributorV1("child-c", "knowledge_media", "snapshot-a"), "MEMBERSHIP"),
        (ContributorV1("child-a", "other-purpose", "snapshot-a"), "PURPOSE"),
    ]:
        with pytest.raises(KnowledgeRuleViolation, match=reason):
            validate_basis(
                replace(child_basis(), contributors=(contributor,)),
                BasisRef("confirmed_meaning", "meaning", 1),
                audience(),
                "org",
                "session",
                lambda _: True,
            )


def test_audience_context_and_audience_revisions_are_separate() -> None:
    validate_audience(audience(), "org", "session", 0, 2)
    for expected, reason in [((2, 2), "CONTEXT_REVISION"), ((0, 0), "AUDIENCE_REVISION")]:
        with pytest.raises(KnowledgeRuleViolation, match=reason):
            validate_audience(audience(), "org", "session", *expected)
    assert [member.age_band for member in audience().members] == ["age-4", "age-8"]


def test_generic_cannot_launder_child_snapshot_provenance() -> None:
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    with pytest.raises(KnowledgeRuleViolation, match="GENERIC_PROVENANCE_CONFLICT"):
        replace(basis, source_snapshot_refs=("child-snapshot",))


def source() -> ReviewedSourceV1:
    return ReviewedSourceV1(
        SourceRefV1("source", 1, "a" * 64),
        "Synthetic cats",
        "fixture:cats",
        "2026-10-19",
        "cats",
        ("age-4", "age-8"),
    )


def reviewed_claim() -> ReviewedClaimV1:
    return ReviewedClaimV1("claim", 1, "Cats are mammals.", (source().ref,))


def test_exact_catalog_and_accountable_teacher_attestation() -> None:
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    claim = catalog_claim(reviewed_claim())
    assert validate_claims((claim,), (reviewed_claim(),), (source(),), basis, audience()) == (
        source(),
    )
    attested = attributed_claim(
        "claim",
        2,
        "A cat is a mammal.",
        (source().ref,),
        (reviewed_claim(),),
        "teacher",
        "Teacher correction with source",
    )
    assert attested.verification_state == "teacher_attested"
    assert attested.attested_by == "teacher"
    assert validate_claims((attested,), (reviewed_claim(),), (source(),), basis, audience()) == (
        source(),
    )
    assert (
        attributed_claim(
            "claim", 1, "Cats are mammals.", (source().ref,), (reviewed_claim(),), "teacher", None
        )
        == claim
    )
    with pytest.raises(KnowledgeRuleViolation, match="ATTESTATION_REQUIRED"):
        attributed_claim("claim", 2, "A cat is a mammal.", (source().ref,), (), "teacher", None)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"state": "unreviewed"}, "SOURCE_NOT_REVIEWED"),
        ({"recalled": True}, "SOURCE_RECALLED"),
        ({"topic": "dogs"}, "SOURCE_TOPIC_MISMATCH"),
        ({"age_bands": ("age-4",)}, "SOURCE_AGE_MISMATCH"),
        ({"ref": SourceRefV1("source", 2, "a" * 64)}, "SOURCE_REVISION_MISMATCH"),
        ({"ref": SourceRefV1("source", 1, "b" * 64)}, "SOURCE_HASH_MISMATCH"),
    ],
)
def test_source_current_pins_review_recall_topic_and_each_age(
    change: dict[str, object], reason: str
) -> None:
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    with pytest.raises(KnowledgeRuleViolation, match=reason):
        validate_claims(
            (catalog_claim(reviewed_claim()),),
            (reviewed_claim(),),
            (replace(source(), **change),),
            basis,
            audience(),
        )


def test_source_missing_catalog_mismatch_and_historical_attribution() -> None:
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    claim = catalog_claim(reviewed_claim())
    for claims, catalog, sources, reason in [
        ((claim,), (reviewed_claim(),), (), "SOURCE_MISSING"),
        (
            (replace(claim, text="Unsupported sentence."),),
            (reviewed_claim(),),
            (source(),),
            "CATALOG_CLAIM_MISMATCH",
        ),
    ]:
        with pytest.raises(KnowledgeRuleViolation, match=reason):
            validate_claims(claims, catalog, sources, basis, audience())
    assert validate_claims((), (), (), basis, audience()) == ()
    historical = KnowledgeClaimV1(
        "claim", 2, "Changed", (source().ref,), "teacher_attested", "teacher-a", "Reason"
    )
    assert validate_claims((historical,), (), (source(),), basis, audience()) == (source(),)
    assert historical.attested_by == "teacher-a"


def test_multi_source_fact_uniqueness_and_bounds() -> None:
    second = replace(source(), ref=SourceRefV1("second-source", 1, "b" * 64))
    fact = replace(reviewed_claim(), source_refs=(second.ref, source().ref))
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    assert tuple(
        item.ref.source_id
        for item in validate_claims(
            (catalog_claim(fact),), (fact,), (source(), second), basis, audience()
        )
    ) == ("second-source", "source")
    with pytest.raises(KnowledgeRuleViolation, match="DUPLICATE_REFERENCE"):
        replace(fact, source_refs=(source().ref, source().ref))
    with pytest.raises(KnowledgeRuleViolation, match="COLLECTION_BOUNDS"):
        validate_claims(
            tuple(replace(catalog_claim(fact), claim_id=f"claim-{i}") for i in range(25)),
            (),
            (),
            basis,
            audience(),
        )


def test_exact_fact_story_projection_order_and_claim_correction() -> None:
    claims = (catalog_claim(reviewed_claim()),)
    imagined = (ImaginedElementV1("wings", 1, "Cats have wings."),)
    sections = (FactSection("fact", ("claim",)), StorySection("story", ("wings",)))
    structured, flat = project_script(sections, claims, imagined)
    assert [(item.kind, item.text) for item in structured] == [
        ("fact", "Cats are mammals."),
        ("story", "Cats have wings."),
    ]
    assert flat == "Cats are mammals.\nCats have wings."
    corrected = replace(
        claims[0],
        text="A cat is a mammal.",
        revision=2,
        verification_state="teacher_attested",
        attested_by="teacher",
        attestation_reason="Reason",
    )
    assert (
        project_script(sections, (corrected,), imagined)[1]
        == "A cat is a mammal.\nCats have wings."
    )
    second = replace(claims[0], claim_id="second", text="Cats have fur.")
    assert (
        project_script((FactSection("fact", ("second", "claim")),), claims + (second,), ())[1]
        == "Cats have fur.\nCats are mammals."
    )


def test_unknown_duplicate_refs_and_literal_imagined_fact_laundering() -> None:
    claim = catalog_claim(reviewed_claim())
    for sections, reason in [
        ((FactSection("fact", ("unknown",)),), "UNKNOWN_CLAIM_REFERENCE"),
        ((StorySection("story", ("unknown",)),), "UNKNOWN_IMAGINED_REFERENCE"),
    ]:
        with pytest.raises(KnowledgeRuleViolation, match=reason):
            project_script(sections, (claim,), ())
    with pytest.raises(KnowledgeRuleViolation, match="DUPLICATE_REFERENCE"):
        FactSection("fact", ("claim", "claim"))
    imaginary = (ImaginedElementV1("fiction", 1, "Mèo có cánh"),)
    leaked = replace(claim, text="MÈO CÓ CÁNH in the sky.")
    with pytest.raises(KnowledgeRuleViolation, match="IMAGINED_AS_FACT"):
        project_script((FactSection("fact", ("claim",)),), (leaked,), imaginary)
    with pytest.raises(KnowledgeRuleViolation, match="IMAGINED_AS_FACT"):
        project_script(
            (FactSection("fact", ("claim",)),), (leaked,), (), forbidden_imagined=imaginary
        )


def test_total_script_bound_rejects_without_truncation() -> None:
    claims = tuple(
        replace(catalog_claim(reviewed_claim()), claim_id=f"claim-{i}", text="x" * 400)
        for i in range(24)
    )
    section = FactSection("fact", tuple(item.claim_id for item in claims))
    with pytest.raises(KnowledgeRuleViolation, match="SCRIPT_BOUNDS"):
        project_script((section, replace(section, section_id="second")), claims, ())


def version() -> KnowledgeBundleVersion:
    return build_version(
        bundle_id="bundle",
        basis=KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats"),
        audience=audience(),
        claims=(catalog_claim(reviewed_claim()),),
        sources=(source(),),
        sections=(FactSection("fact", ("claim",)),),
        imagined_elements=(),
        created_by="teacher-a",
        created_at="2026-10-19T00:00:00Z",
    )


def test_canonical_nfc_sorted_native_vectors_and_hash_exclusions() -> None:
    actual = canonical_bytes({"z": [True, None, 3], "e\u0301": "Me\u0300o"})
    assert actual == '{"z":[true,null,3],"é":"Mèo"}'.encode()
    assert (
        canonical_sha256({"é": "Mèo", "z": [True, None, 3]}) == hashlib.sha256(actual).hexdigest()
    )
    document = json.loads(version().canonical_bytes)
    assert "bundle_hash" not in document
    assert "readiness" not in document
    assert document["canonical_rules_version"] == "knowledge-canonical-v1"
    assert document["context_revision"] == 0
    assert document["audience_revision"] == 2


@pytest.mark.parametrize(
    "document",
    [
        {"x": 1.0},
        {"x": float("nan")},
        {"x": float("inf")},
        {"x": object()},
        {"x": (1, 2)},
        {"x": b"bytes"},
        {1: "integer key"},
        {"e\u0301": 1, "é": 2},
        {"x": "\ud800"},
        {"x": 10**5000},
    ],
)
def test_canonical_unsupported_and_normalized_duplicate_keys_rejected(
    document: dict[str, object],
) -> None:
    with pytest.raises(KnowledgeRuleViolation, match="CANONICAL|NFC_DUPLICATE"):
        canonical_bytes(document)


def test_immutable_v1_v2_correction_hash_and_pure_noop() -> None:
    original = version()
    saved = original.canonical_bytes
    assert (
        plan_edit(
            original,
            correction_ref="unused",
            teacher_principal_id="teacher-b",
            reason="No content change",
            claims=original.knowledge_claims,
        )
        is None
    )
    new_claim = attributed_claim(
        "claim",
        2,
        "A cat is a mammal.",
        (source().ref,),
        (reviewed_claim(),),
        "teacher-b",
        "Teacher correction",
    )
    edited = plan_edit(
        original,
        correction_ref="correction-1",
        teacher_principal_id="teacher-b",
        reason="Teacher correction",
        claims=(new_claim,),
    )
    assert edited is not None
    assert original.bundle_version == 1 and original.canonical_bytes == saved
    assert edited.bundle_version == edited.editorial_revision == 2
    assert edited.bundle_hash != original.bundle_hash
    assert edited.script_text == "A cat is a mammal."
    assert edited.corrections == (
        CorrectionV1("correction-1", "teacher-b", "Teacher correction", 1, 2),
    )
    assert edited.created_by == "teacher-a" and edited.created_at == original.created_at
    assert edited.basis == original.basis and edited.audience == original.audience
    verify_version(original)
    verify_version(edited)
    assert BundleHead("bundle", "org", "session", 2, 2).etag == '"knowledge-bundle:bundle:2:2"'


def test_tamper_bytes_hash_and_content_cannot_rehash_from_current_facts() -> None:
    original = version()
    for changed, reason in [
        (replace(original, canonical_bytes=b"{}"), "CANONICAL_BYTES_MISMATCH"),
        (replace(original, bundle_hash="0" * 64), "BUNDLE_HASH_MISMATCH"),
        (replace(original, created_by="other"), "CANONICAL_BYTES_MISMATCH"),
        (
            replace(original, basis=replace(original.basis, organization_id="foreign")),
            "SCOPE_MISMATCH",
        ),
        (
            replace(original, audience=replace(original.audience, session_id="foreign")),
            "SCOPE_MISMATCH",
        ),
        (
            replace(original, basis=replace(original.basis, applicable=False)),
            "BASIS_NOT_APPLICABLE",
        ),
    ]:
        with pytest.raises(KnowledgeRuleViolation, match=reason):
            verify_version(changed)
    with pytest.raises(KnowledgeRuleViolation, match="INVALID_REVISION"):
        BundleHead("bundle", "org", "session", 0, 1)


def test_child_origin_contributors_sticky_after_imagined_removed_and_no_literal_laundering() -> (
    None
):
    imagined = ImaginedElementV1("wings", 1, "Cats have wings.")
    basis = replace(child_basis(), imagined_elements=(imagined,))
    original = build_version(
        bundle_id="child-bundle",
        basis=basis,
        audience=audience(),
        claims=(catalog_claim(reviewed_claim()),),
        sources=(source(),),
        sections=(FactSection("fact", ("claim",)), StorySection("story", ("wings",))),
        imagined_elements=(imagined,),
        created_by="teacher",
        created_at="2026-10-19T00:00:00Z",
    )
    edited = plan_edit(
        original,
        correction_ref="remove-imagined",
        teacher_principal_id="teacher",
        reason="Remove selected story",
        sections=(FactSection("fact", ("claim",)),),
        imagined_elements=(),
    )
    assert edited is not None and edited.content_origin == "child_derived"
    assert edited.contributors == basis.contributors
    assert edited.basis.confirmation_ref == "teacher-confirmation-1"
    with pytest.raises(KnowledgeRuleViolation, match="IMAGINED_AS_FACT"):
        plan_edit(
            edited,
            correction_ref="launder",
            teacher_principal_id="teacher",
            reason="Correction",
            claims=(replace(original.knowledge_claims[0], text="Cats have wings."),),
        )


def test_document_and_correction_history_overflow_reject_atomically() -> None:
    original = version()
    with pytest.raises(KnowledgeRuleViolation, match="DOCUMENT_BOUNDS"):
        canonical_bytes({"x": "é" * 100000})
    history = tuple(
        CorrectionV1(f"correction-{i}", "teacher", "r" * 200, i, i + 1) for i in range(1, 801)
    )
    with pytest.raises(KnowledgeRuleViolation, match="DOCUMENT_BOUNDS"):
        build_version(
            bundle_id=original.bundle_id,
            basis=original.basis,
            audience=original.audience,
            claims=original.knowledge_claims,
            sources=original.source_records,
            sections=original.sections,
            imagined_elements=(),
            created_by=original.created_by,
            created_at=original.created_at,
            bundle_version=801,
            editorial_revision=801,
            corrections=history,
        )
    assert original.bundle_version == 1 and original.corrections == ()


def test_pure_constructor_rejects_dangling_source_pin_and_provenance_downgrade() -> None:
    original = version()
    with pytest.raises(KnowledgeRuleViolation, match="SOURCE_PIN_MISMATCH"):
        build_version(
            bundle_id=original.bundle_id,
            basis=original.basis,
            audience=original.audience,
            claims=original.knowledge_claims,
            sources=(),
            sections=original.sections,
            imagined_elements=(),
            created_by=original.created_by,
            created_at=original.created_at,
        )


def test_pure_provenance_downgrade_and_full_hidden_basis_imagined_tamper() -> None:
    original = version()
    with pytest.raises(KnowledgeRuleViolation, match="PROVENANCE_DOWNGRADE"):
        build_version(
            bundle_id="child",
            basis=child_basis(),
            audience=audience(),
            claims=(),
            sources=(),
            sections=(),
            imagined_elements=(),
            created_by="teacher",
            created_at=original.created_at,
            content_origin="generic",
        )
    basis = replace(
        child_basis(), imagined_elements=(ImaginedElementV1("wings", 1, "Cats have wings."),)
    )
    child = build_version(
        bundle_id="child",
        basis=basis,
        audience=audience(),
        claims=(),
        sources=(),
        sections=(),
        imagined_elements=(),
        created_by="teacher",
        created_at=original.created_at,
    )
    # Removing an unselected trusted imagined item changes the full protected basis.
    with pytest.raises(KnowledgeRuleViolation, match="CANONICAL_BYTES_MISMATCH"):
        verify_version(replace(child, basis=replace(basis, imagined_elements=())))


def test_pure_collection_and_scalar_limits() -> None:
    with pytest.raises(KnowledgeRuleViolation, match="TEXT_BOUNDS"):
        replace(reviewed_claim(), text="x" * 401)
    with pytest.raises(KnowledgeRuleViolation, match="TEXT_BOUNDS"):
        replace(source(), title="x" * 201)
    with pytest.raises(KnowledgeRuleViolation, match="COLLECTION_BOUNDS"):
        replace(
            audience(), members=tuple(AudienceMemberV1(f"member-{i}", "age-4") for i in range(33))
        )
    with pytest.raises(KnowledgeRuleViolation, match="COLLECTION_BOUNDS"):
        replace(
            child_basis(),
            imagined_elements=tuple(
                ImaginedElementV1(f"imagined-{i}", 1, "Story") for i in range(9)
            ),
        )
    with pytest.raises(KnowledgeRuleViolation, match="COLLECTION_BOUNDS"):
        project_script(
            tuple(FactSection(f"section-{i}", ("claim",)) for i in range(33)),
            (catalog_claim(reviewed_claim()),),
            (),
        )


@pytest.mark.parametrize(
    "claim_text",
    [
        "Mèo có cánh",
        "Mèo  có cánh.",
        "Mèo có c\u200bánh.",
        "Ｍèo có cánh.",
        "Mèo có",
        "Mèo,có,cánh.",
        "Mèo có c-ánh.",
    ],
)
def test_tiny_imagined_literal_variants_cannot_become_facts(claim_text: str) -> None:
    imagined = (ImaginedElementV1("wings", 1, "Mèo có cánh."),)
    claim = replace(catalog_claim(reviewed_claim()), text=claim_text)
    with pytest.raises(KnowledgeRuleViolation, match="IMAGINED_AS_FACT"):
        project_script(
            (FactSection("fact", ("claim",)),), (claim,), (), forbidden_imagined=imagined
        )


@pytest.mark.parametrize(
    "code_point",
    [
        0x034F,
        0x115F,
        0x1160,
        0x17B4,
        0x17B5,
        0x180B,
        0x180F,
        0x3164,
        0xFE0F,
        0xFFA0,
        0xFFF0,
        0xFFF8,
        0xE0000,
        0xE01EF,
        0xE0FFF,
    ],
)
@pytest.mark.parametrize("imagined_obfuscated", [False, True])
def test_default_ignorable_literal_obfuscation_is_not_a_fact(
    code_point: int, imagined_obfuscated: bool
) -> None:
    plain = "Mèo có cánh."
    obfuscated = f"Mèo có c{chr(code_point)}ánh."
    claim_text, imagined_text = (plain, obfuscated) if imagined_obfuscated else (obfuscated, plain)
    claim = replace(catalog_claim(reviewed_claim()), text=claim_text)
    with pytest.raises(KnowledgeRuleViolation, match="IMAGINED_AS_FACT"):
        project_script(
            (FactSection("fact", ("claim",)),),
            (claim,),
            (),
            forbidden_imagined=(ImaginedElementV1("wings", 1, imagined_text),),
        )


@pytest.mark.parametrize("code_point", [0x00, 0x1F, 0x7F, 0x80, 0x85, 0x9F])
def test_text_controls_include_del_and_c1(code_point: int) -> None:
    with pytest.raises(KnowledgeRuleViolation, match="TEXT_CONTROL"):
        replace(catalog_claim(reviewed_claim()), text=f"Mèo{chr(code_point)} có lông.")


def test_text_controls_allow_line_feed_tab_and_vietnamese_combining_marks() -> None:
    original = "Me\u0300o\nco\u0301\tlo\u0302ng."
    claim = replace(catalog_claim(reviewed_claim()), text=original)
    assert claim.text == original
    assert project_script((FactSection("fact", ("claim",)),), (claim,), ())[1] == original
    assert canonical_bytes({"text": original}) == '{"text":"Mèo\\ncó\\tlông."}'.encode()


@pytest.mark.parametrize(
    ("claim", "imagined", "overlap"),
    [
        ("A cat is a mammal.", "cat", True),
        ("cat", "A cat with wings.", True),
        ("education", "cat", False),
        ("a catapult", "cat", False),
        ("Mèo là động vật có vú.", "Mèo có cánh.", False),
        ("cat", "...\u200b", False),
        ("...", "cat", False),
        ("Mèo có cánh", "Mèo, có, cánh.", True),
        ("Mèo có cánh", "Mèo có c-ánh.", True),
        ("Meo co canh", "Mèo có cánh.", False),
        ("Me\u034f\u0300o có cánh.", "Mèo có cánh.", True),
        ("Mèo có cánh.", "Me\u034f\u0300o có cánh.", True),
        ("Mèo có cánh.", "\u034f\u180b\u3164\ufe0f", False),
        ("\u034f\u180b\u3164\ufe0f", "Mèo có cánh.", False),
        ("cánh", "canh", False),
        ("canh", "cánh", False),
    ],
)
def test_literal_overlap_token_boundaries_empty_signatures_and_diacritics(
    claim: str,
    imagined: str,
    overlap: bool,
) -> None:
    assert imagined_literal_overlap(claim, imagined) is overlap


def test_literal_comparison_does_not_rewrite_stored_text_or_canonical_nfc() -> None:
    text = "Ｍèo,  có c\u200bánh."
    assert imagined_literal_overlap(text, "Mèo có cánh.")
    assert canonical_bytes({"text": text}) == '{"text":"Ｍèo,  có c\u200bánh."}'.encode("utf-8")
    claim = replace(catalog_claim(reviewed_claim()), text=text)
    assert project_script((FactSection("fact", ("claim",)),), (claim,), ())[1] == text
    assert claim.text == text


def test_default_ignorable_comparison_does_not_rewrite_text_or_canonical_bytes() -> None:
    original = "Mèo có c\u034f\u180b\u3164\ufe0fánh."
    assert imagined_literal_overlap(original, "Mèo có cánh.")
    claim = replace(catalog_claim(reviewed_claim()), text=original)
    assert claim.text == original
    assert project_script((FactSection("fact", ("claim",)),), (claim,), ())[1] == original
    assert canonical_bytes({"text": original}) == (
        '{"text":"Mèo có c\u034f\u180b\u3164\ufe0fánh."}'.encode()
    )


@pytest.mark.parametrize(
    ("has_claims", "has_facts", "expected"),
    [
        (False, False, ("needs_content_action", "NO_ELIGIBLE_SOURCE")),
        (False, True, ("needs_content_action", "NO_ELIGIBLE_SOURCE")),
        (True, False, ("needs_content_action", "FACT_SECTION_REQUIRED")),
        (True, True, ("generation_ready", None)),
    ],
)
def test_structural_content_readiness_table(
    has_claims: bool,
    has_facts: bool,
    expected: tuple[str, str | None],
) -> None:
    assert content_readiness(has_claims, has_facts) == expected


def test_unchanged_attested_claim_reuses_trusted_author_but_changed_claim_uses_editor() -> None:
    previous = attributed_claim(
        "claim", 2, "A cat is a mammal.", (source().ref,), (), "teacher-a", "Teacher A attestation"
    )
    reused = attributed_claim(
        previous.claim_id,
        previous.revision,
        previous.text,
        previous.source_refs,
        (),
        "teacher-b",
        previous.attestation_reason,
        previous=previous,
    )
    assert reused is previous and reused.attested_by == "teacher-a"
    for change in (
        {"claim_id": "other-claim"},
        {"claim_revision": 3},
        {"claim_text": "Changed text."},
        {"refs": (SourceRefV1("source", 1, "b" * 64),)},
        {"reason": "Teacher B new reason"},
    ):
        request = {
            "claim_id": previous.claim_id,
            "claim_revision": previous.revision,
            "claim_text": previous.text,
            "refs": previous.source_refs,
            "catalog": (),
            "teacher_principal_id": "teacher-b",
            "reason": previous.attestation_reason,
            "previous": previous,
            **change,
        }
        changed = attributed_claim(**request)
        assert changed is not previous and changed.attested_by == "teacher-b"
    assert previous.attested_by == "teacher-a"
