import json
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from sketch2life.application.services.knowledge_bundle import (
    CreateKnowledgeCommand,
    EditKnowledgeCommand,
)
from sketch2life.contracts.schemas.knowledge_bundles import (
    ClaimEditV1,
    EditKnowledgeBundleV1,
    ExactKnowledgeRefV1,
    KnowledgeSourceRefV1,
)
from sketch2life.domain.knowledge_bundle import (
    FIXTURE_POLICY,
    AudienceContextV1,
    AudienceMemberV1,
    BasisRef,
    ContributorV1,
    KnowledgeBasisV1,
    KnowledgeRuleViolation,
    ReviewedClaimV1,
    ReviewedSourceV1,
    SourceRefV1,
    canonical_sha256,
    validate_basis,
)
from sketch2life.infrastructure.knowledge_bundle.adapters import (
    FixtureKnowledgeFacts,
    RecordingKnowledgeConsumer,
    _consumer_canonical_digest,
    candidate_video_pin_digest,
    candidate_video_pin_material,
)
from sketch2life.infrastructure.knowledge_bundle.coordination import KnowledgeCommitCoordinator
from sketch2life.infrastructure.knowledge_bundle.harness import (
    ORG,
    SESSION,
    TEACHER_A,
    build_knowledge_harness,
)


def basis() -> KnowledgeBasisV1:
    return KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")


def audience() -> AudienceContextV1:
    return AudienceContextV1("aud", "org", "session", 0, 0, (AudienceMemberV1("child", "age-4"),))


def source() -> ReviewedSourceV1:
    return ReviewedSourceV1(
        SourceRefV1("source", 1, "a" * 64),
        "Synthetic cats",
        "fixture:cats",
        "2026-10-19",
        "cats",
        ("age-4",),
    )


def test_default_deny_and_exact_scope_purpose_snapshot_consent() -> None:
    facts = FixtureKnowledgeFacts(KnowledgeCommitCoordinator())
    contributor = ContributorV1("child", "knowledge_media", "snapshot")
    assert facts.basis(BasisRef("teacher_topic", "topic", 1)) is None
    assert facts.audience("org", "session") is None
    assert facts.sources() == facts.catalog_claims() == ()
    assert not facts.teacher_allowed("org", "teacher", "session")
    assert not facts.disclosure_allowed("org", "teacher", "session")
    assert not facts.mutation_allowed("org", "session")
    assert facts.policy() == (FIXTURE_POLICY, False)
    assert facts.publish_consent("org", "session", contributor, True)
    assert facts.contributor_allowed("org", "session", contributor)
    assert facts.contributor_disclosure_allowed("org", "session", contributor)
    for org, session, changed in [
        ("foreign", "session", contributor),
        ("org", "other-session", contributor),
        ("org", "session", replace(contributor, purpose_code="other-purpose")),
        ("org", "session", replace(contributor, snapshot_ref="other-snapshot")),
    ]:
        assert not facts.contributor_allowed(org, session, changed)
        assert not facts.contributor_disclosure_allowed(org, session, changed)


def test_mutation_teacher_and_child_disclosure_are_independent() -> None:
    facts = FixtureKnowledgeFacts(KnowledgeCommitCoordinator())
    contributor = ContributorV1("child", "knowledge_media", "snapshot")
    facts.publish_teacher("org", "session", "teacher", False, disclose=True)
    facts.publish_consent("org", "session", contributor, False, disclose=True)
    assert not facts.teacher_allowed("org", "teacher", "session")
    assert facts.disclosure_allowed("org", "teacher", "session")
    assert not facts.contributor_allowed("org", "session", contributor)
    assert facts.contributor_disclosure_allowed("org", "session", contributor)
    facts.publish_disclosure("org", "session", "teacher", False)
    facts.publish_consent("org", "session", contributor, True, disclose=False)
    assert not facts.disclosure_allowed("org", "teacher", "session")
    assert facts.contributor_allowed("org", "session", contributor)
    assert not facts.contributor_disclosure_allowed("org", "session", contributor)


def publications(
    facts: FixtureKnowledgeFacts,
) -> dict[str, tuple[Callable[[], bool], Callable[[], object], object]]:
    contributor = ContributorV1("child", "knowledge_media", "snapshot")
    claim = ReviewedClaimV1("claim", 1, "Cats are mammals.", (source().ref,))
    return {
        "publish_basis": (
            lambda: facts.publish_basis(basis()),
            lambda: facts.basis(BasisRef("teacher_topic", "topic", 1)),
            basis(),
        ),
        "publish_audience": (
            lambda: facts.publish_audience(audience()),
            lambda: facts.audience("org", "session"),
            audience(),
        ),
        "publish_source": (lambda: facts.publish_source(source()), facts.sources, (source(),)),
        "publish_catalog_claim": (
            lambda: facts.publish_catalog_claim(claim),
            facts.catalog_claims,
            (claim,),
        ),
        "publish_teacher": (
            lambda: facts.publish_teacher("org", "session", "teacher", True),
            lambda: (
                facts.teacher_allowed("org", "teacher", "session"),
                facts.disclosure_allowed("org", "teacher", "session"),
            ),
            (True, True),
        ),
        "publish_disclosure": (
            lambda: facts.publish_disclosure("org", "session", "teacher", True),
            lambda: facts.disclosure_allowed("org", "teacher", "session"),
            True,
        ),
        "publish_consent": (
            lambda: facts.publish_consent("org", "session", contributor, True),
            lambda: (
                facts.contributor_allowed("org", "session", contributor),
                facts.contributor_disclosure_allowed("org", "session", contributor),
            ),
            (True, True),
        ),
        "publish_policy": (
            lambda: facts.publish_policy("new-policy"),
            facts.policy,
            ("new-policy", True),
        ),
        "publish_mutation": (
            lambda: facts.publish_mutation("org", "session", True),
            lambda: facts.mutation_allowed("org", "session"),
            True,
        ),
    }


@pytest.mark.parametrize("rollback", [False, True])
def test_every_public_guard_publication_is_deferred_until_commit_or_rollback(
    rollback: bool,
) -> None:
    coordinator = KnowledgeCommitCoordinator()
    facts = FixtureKnowledgeFacts(coordinator)
    inventory = publications(facts)
    assert set(inventory) == {name for name in dir(facts) if name.startswith("publish_")}
    before = {name: getter() for name, (_, getter, _) in inventory.items()}
    try:
        with coordinator.unit():
            for publish, _, _ in inventory.values():
                assert publish() is False
            assert {name: getter() for name, (_, getter, _) in inventory.items()} == before
            if rollback:
                raise RuntimeError("unit rollback")
    except RuntimeError:
        assert rollback
    assert {name: getter() for name, (_, getter, _) in inventory.items()} == {
        name: expected for name, (_, _, expected) in inventory.items()
    }
    assert facts.coordination_token is coordinator


def test_inputs_captured_before_queue_and_getters_never_alias_stored_facts() -> None:
    coordinator = KnowledgeCommitCoordinator()
    facts = FixtureKnowledgeFacts(coordinator)
    original = basis()
    with coordinator.unit():
        assert facts.publish_basis(original) is False
        # Probe the mutable __dict__ escape available even on a frozen dataclass.
        original.__dict__["topic"] = "caller changed before queue drain"
    returned = facts.basis(BasisRef("teacher_topic", "topic", 1))
    assert returned is not None and returned.topic == "cats"
    returned.__dict__["topic"] = "caller changed returned value"
    again = facts.basis(BasisRef("teacher_topic", "topic", 1))
    assert again is not None and again.topic == "cats" and again is not returned
    published = source()
    facts.publish_source(published)
    facts.sources()[0].__dict__["recalled"] = True
    assert not facts.sources()[0].recalled
    facts.publish_source(replace(published, recalled=True))
    assert facts.sources()[0].recalled


def test_sorted_current_catalog_and_basis_revision_not_fictionally_reconstructed() -> None:
    facts = FixtureKnowledgeFacts(KnowledgeCommitCoordinator())
    facts.publish_basis(replace(basis(), revision=2))
    current = facts.basis(BasisRef("teacher_topic", "topic", 1))
    assert current is not None and current.revision == 2
    for name in ("z", "a"):
        facts.publish_source(replace(source(), ref=SourceRefV1(name, 1, "a" * 64)))
        facts.publish_catalog_claim(ReviewedClaimV1(name, 1, "Cats are mammals.", (source().ref,)))
    assert [item.ref.source_id for item in facts.sources()] == ["a", "z"]
    assert [item.claim_id for item in facts.catalog_claims()] == ["a", "z"]


def test_actual_generic_guard_zero_consent_lookup_and_child_lookup_increments() -> None:
    facts = FixtureKnowledgeFacts(KnowledgeCommitCoordinator())
    validate_basis(
        basis(),
        BasisRef("teacher_topic", "topic", 1),
        audience(),
        "org",
        "session",
        lambda item: facts.contributor_allowed("org", "session", item),
    )
    assert facts.consent_calls == 0
    contributor = ContributorV1("child", "knowledge_media", "snapshot")
    facts.publish_consent("org", "session", contributor, True)
    child = KnowledgeBasisV1(
        "meaning",
        "confirmed_meaning",
        1,
        "org",
        "session",
        "cats",
        ("snapshot",),
        (contributor,),
        confirmation_ref="confirmation",
    )
    validate_basis(
        child,
        BasisRef("confirmed_meaning", "meaning", 1),
        audience(),
        "org",
        "session",
        lambda item: facts.contributor_allowed("org", "session", item),
    )
    assert facts.consent_calls == 1


def test_all_object_fact_publications_and_getters_copy_nested_values() -> None:
    coordinator = KnowledgeCommitCoordinator()
    facts = FixtureKnowledgeFacts(coordinator)
    audience_input = audience()
    source_input = source()
    claim_input = ReviewedClaimV1("claim", 1, "Cats are mammals.", (source_input.ref,))
    with coordinator.unit():
        facts.publish_audience(audience_input)
        facts.publish_source(source_input)
        facts.publish_catalog_claim(claim_input)
        audience_input.members[0].__dict__["age_band"] = "caller-age"
        source_input.ref.__dict__["sha256"] = "b" * 64
        claim_input.__dict__["text"] = "caller text"
    actual_audience = facts.audience("org", "session")
    assert actual_audience is not None and actual_audience.members[0].age_band == "age-4"
    assert facts.sources()[0].ref.sha256 == "a" * 64
    assert facts.catalog_claims()[0].text == "Cats are mammals."

    actual_audience.members[0].__dict__["age_band"] = "caller-age"
    facts.sources()[0].ref.__dict__["sha256"] = "c" * 64
    facts.catalog_claims()[0].__dict__["text"] = "caller text"
    fresh_audience = facts.audience("org", "session")
    assert fresh_audience is not None and fresh_audience.members[0].age_band == "age-4"
    assert facts.sources()[0].ref.sha256 == "a" * 64
    assert facts.catalog_claims()[0].text == "Cats are mammals."


def test_exact_producer_resolve_supersession_before_event_delivery_and_recording_consumer() -> None:
    harness = build_knowledge_harness()
    first = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "exact-export", harness.create_body())
    )
    old_ref = ExactKnowledgeRefV1(
        bundle_id=first.record.bundle_id, bundle_version=1, bundle_hash=first.record.bundle_hash
    )
    before = harness.service.resolve_exact(TEACHER_A, old_ref.bundle_id, 1, old_ref.bundle_hash)
    assert before.ready and before.export is not None
    old_bytes = before.export.canonical_json.encode()
    consumer = RecordingKnowledgeConsumer()
    consumer.register(ORG, SESSION, old_ref)
    unrelated = [
        (ORG, SESSION, old_ref.model_copy(update={"bundle_id": "unrelated"})),
        (ORG, SESSION, old_ref.model_copy(update={"bundle_hash": "0" * 64})),
        (ORG, SESSION, old_ref.model_copy(update={"bundle_version": 3})),
        ("other-org", SESSION, old_ref),
        (ORG, "other-session", old_ref),
    ]
    for org, session, ref in unrelated:
        consumer.register(org, session, ref)
    source_ref = harness.source.ref
    body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Teacher exact correction",
        claims=(
            ClaimEditV1(
                claim_id=harness.claim.claim_id,
                revision=2,
                text="Mèo thuộc nhóm động vật có vú.",
                source_refs=(
                    KnowledgeSourceRefV1(
                        source_id=source_ref.source_id,
                        revision=source_ref.revision,
                        sha256=source_ref.sha256,
                    ),
                ),
                attestation_reason="Teacher accountable",
            ),
        ),
    )
    second = harness.service.edit(
        EditKnowledgeCommand(
            TEACHER_A,
            first.record.bundle_id,
            "exact-edit",
            harness.repository.snapshot().heads[first.record.bundle_id].etag,
            body,
        )
    )
    assert consumer.is_current(ORG, SESSION, old_ref)  # delivery has not happened
    denied = harness.service.resolve_exact(TEACHER_A, old_ref.bundle_id, 1, old_ref.bundle_hash)
    assert not denied.ready and denied.export is None
    assert (
        harness.repository.snapshot().versions[(old_ref.bundle_id, 1)].canonical_bytes == old_bytes
    )
    current = harness.service.resolve_exact(
        TEACHER_A, old_ref.bundle_id, 2, second.record.bundle_hash
    )
    assert current.ready and current.export is not None
    assert (
        current.export.editorial_revision,
        current.export.context_revision,
        current.export.audience_revision,
    ) == (2, 0, 2)
    assert current.export.source_records[0].ref.sha256 == source_ref.sha256
    assert current.export.basis_ref == first.record.basis_ref
    event = next(iter(harness.repository.snapshot().outbox.values()))
    new_ref = event.new_bundle
    consumer.register(ORG, SESSION, new_ref)
    assert consumer.apply(event) is True and consumer.apply(event) is False
    assert not consumer.is_current(ORG, SESSION, old_ref)
    assert consumer.is_current(ORG, SESSION, new_ref)
    assert all(consumer.is_current(org, session, ref) for org, session, ref in unrelated)
    with pytest.raises(KnowledgeRuleViolation, match="EVENT_IDENTITY_MISMATCH"):
        consumer.apply(event.model_copy(update={"operation_id": "different-operation"}))
    late = RecordingKnowledgeConsumer()
    assert late.apply(event)
    late.register(ORG, SESSION, old_ref)
    assert not late.is_current(ORG, SESSION, old_ref)


@pytest.mark.parametrize("tamper", ["bytes", "hash"])
def test_actual_producer_read_withholds_tampered_storage_content(
    monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    harness = build_knowledge_harness()
    created = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "tamper-export", harness.create_body())
    )
    original_transaction = harness.repository.transaction

    @contextmanager
    def tampered_transaction():  # type: ignore[no-untyped-def]
        with original_transaction() as tx:
            getter = tx.get_version

            def changed(bundle_id: str, version: int):  # type: ignore[no-untyped-def]
                value = getter(bundle_id, version)
                assert value is not None
                return (
                    replace(value, canonical_bytes=b"{}")
                    if tamper == "bytes"
                    else replace(value, bundle_hash="0" * 64)
                )

            tx.get_version = changed
            yield tx

    before = harness.repository.snapshot()
    monkeypatch.setattr(harness.repository, "transaction", tampered_transaction)
    resolution = harness.service.resolve_exact(
        TEACHER_A, created.record.bundle_id, 1, created.record.bundle_hash
    )
    assert not resolution.ready and resolution.export is None
    assert harness.repository.snapshot() == before


@pytest.mark.parametrize(
    ("mismatch", "expected_reason"),
    [
        ("hash", "EXACT_BUNDLE_MISMATCH"),
        ("unknown-id", "KNOWLEDGE_UNAVAILABLE"),
        ("other-bundle-id", "EXACT_BUNDLE_MISMATCH"),
        ("version", "BUNDLE_SUPERSEDED"),
    ],
)
def test_actual_exact_resolver_rejects_mismatched_requested_pins_without_writes(
    mismatch: str, expected_reason: str
) -> None:
    harness = build_knowledge_harness()
    first = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "exact-pin-first", harness.create_body())
    ).record
    other = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "exact-pin-other", harness.create_body())
    ).record
    assert first.bundle_id != other.bundle_id and first.bundle_hash != other.bundle_hash
    before = harness.repository.snapshot()
    commits = harness.repository.commits

    valid = harness.service.resolve_exact(
        TEACHER_A, first.bundle_id, first.bundle_version, first.bundle_hash
    )
    assert valid.ready and valid.reason is None and valid.export is not None
    assert (
        valid.export.bundle_id,
        valid.export.bundle_version,
        valid.export.bundle_hash,
    ) == (first.bundle_id, first.bundle_version, first.bundle_hash)

    requested_id = first.bundle_id
    requested_version = first.bundle_version
    requested_hash = first.bundle_hash
    if mismatch == "hash":
        # Flip one valid hexadecimal digit, so the pin stays well formed and differs.
        requested_hash = ("0" if first.bundle_hash[0] != "0" else "1") + first.bundle_hash[1:]
    elif mismatch == "unknown-id":
        requested_id = "unknown-exact-bundle"
    elif mismatch == "other-bundle-id":
        requested_id = other.bundle_id
    else:
        requested_version += 1

    denied = harness.service.resolve_exact(
        TEACHER_A, requested_id, requested_version, requested_hash
    )
    assert not denied.ready and denied.reason == expected_reason and denied.export is None
    assert harness.repository.snapshot() == before
    assert harness.repository.commits == commits


def test_candidate_video_pin_material_matches_pinned_consumer_shape_and_known_digest() -> None:
    harness = build_knowledge_harness()
    result = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "video-vector", harness.create_body())
    )
    resolution = harness.service.resolve_exact(
        TEACHER_A, result.record.bundle_id, 1, result.record.bundle_hash
    )
    assert resolution.ready and resolution.export is not None
    expected = {
        "schema": "BE2-08.VideoPin/0.1-candidate",
        "organization_id": "org",
        "session_id": "session",
        "bundle": {
            "ref": "kb-2cf3d6a45815a18b5de2b0894a31149a9adba22c3d263ba2dbd4d639c0f186c4",
            "version": 1,
            "hash": "1b2579bfb3d978bba9bc7fc4fc1e4c117907cfb23b47e995b2626c1d3c6e851b",
        },
        "editorial_revision": 1,
        "context_revision": 0,
        "audience_revision": 2,
        "sources": [
            {
                "ref": "source-cats",
                "version": 1,
                "hash": "98d21d4f24f4d0bc5610fddeab9229d86d07c63a978f0f273200c3b7545c0360",
            }
        ],
        "strategy": "reviewed_library",
        "policy_epoch": 1,
        "content_profile": {
            "ref": "fixture-video-content-profile",
            "version": 1,
            "hash": "75592235771ff4c44ce1fd6e23ba31d5dfa11e520f5812b491c267f46b3139ab",
        },
        "encoding": {
            "ref": "fixture-video-encoding",
            "version": 1,
            "hash": "2eba25fb85a9248bbe11cab581ca076fa9ef4bac79d6737acd72a3f1e738ab8c",
        },
        "rights": {
            "ref": "fixture-video-rights",
            "version": 1,
            "hash": "8d6802d8c172c89dc85d33baf2e8b69eff704605abc76164dfbd00de8aa83928",
        },
        "retry_policy": {
            "ref": "fixture-video-retry-policy",
            "version": 1,
            "hash": "6e37737aff8f661dc292638745ea2572af155cfa05116fa1d1f7dd63ab53d06f",
        },
        "policy": {
            "ref": "fixture-video-policy",
            "version": 1,
            "hash": "cc9b294dbc977222554393718500e2cae5b0da074ff869307c56a189932f8856",
        },
        "model_profile": None,
        "library_asset": {
            "ref": "fixture-video-library-asset",
            "version": 1,
            "hash": "11c3b05a1e9b60e8af7e60afe26bbfb0430559651365cd40fc00dae9cafda1f2",
        },
    }
    assert candidate_video_pin_material(resolution.export) == expected
    assert (
        candidate_video_pin_digest(resolution.export)
        == "e2104355226fdd4f520fdfb6a9d3029ba356d126fda99179bc27611858c1b0cb"
    )
    assert candidate_video_pin_digest(resolution.export) != resolution.export.bundle_hash


def test_native_normalized_vectors_and_nfd_digest_difference_are_explicit() -> None:
    normalized = {"text": "Mèo", "values": [True, None, 3]}
    nfd = {"text": "Me\u0300o", "values": [True, None, 3]}
    assert (
        _consumer_canonical_digest(normalized)
        == "a57090f53e955569faa8948c97f721b8f948a28068f074ffa1f17463053e30ef"
    )
    assert canonical_sha256(normalized) == _consumer_canonical_digest(normalized)
    assert (
        _consumer_canonical_digest(nfd)
        == "2483794c086454fa3b80ddd6f135d3acfab70cffcb0e840194c32f281e8332d0"
    )
    assert canonical_sha256(nfd) == canonical_sha256(normalized)
    assert _consumer_canonical_digest(nfd) != canonical_sha256(nfd)


def test_candidate_pin_sources_are_exact_sorted_set_and_draft_not_pinnable() -> None:
    harness = build_knowledge_harness()
    second_source = replace(harness.source, ref=SourceRefV1("a-source", 2, "b" * 64))
    harness.facts.publish_source(second_source)
    harness.facts.publish_catalog_claim(
        replace(harness.claim, revision=2, source_refs=(harness.source.ref, second_source.ref))
    )
    result = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "two-sources", harness.create_body())
    )
    export = harness.service.resolve_exact(
        TEACHER_A, result.record.bundle_id, 1, result.record.bundle_hash
    ).export
    assert export is not None
    assert candidate_video_pin_material(export)["sources"] == [
        {"ref": "a-source", "version": 2, "hash": "b" * 64},
        {"ref": harness.source.ref.source_id, "version": 1, "hash": harness.source.ref.sha256},
    ]
    # A historical record does not grant a valid consumer lease; draft export is refused.
    with pytest.raises(KnowledgeRuleViolation, match="KNOWLEDGE_NOT_READY"):
        candidate_video_pin_material(
            export.model_copy(update={"readiness": "needs_content_action"})
        )


def test_actual_producer_examples_are_deterministic_and_saved_artifact_json_equal() -> None:
    from sketch2life.infrastructure.knowledge_bundle.examples import build_knowledge_examples

    produced = build_knowledge_examples()
    assert produced == build_knowledge_examples()
    path = (
        Path(__file__).resolve().parents[3]
        / "features/FEAT-056-be2-knowledge-script/artifacts/KNOWLEDGE_BUNDLE_EXAMPLES.json"
    )
    assert json.loads(path.read_text(encoding="utf-8")) == produced
    # Assertions cover actual values; JSON value equality is not serialized byte equality.
    assert produced["generic_create"]["record"]["bundle_version"] == 1
    assert produced["generic_create"]["status"] == 201
    assert produced["generic_create"]["replayed"] is False
    assert produced["teacher_attested_edit"]["record"]["bundle_version"] == 2
    assert produced["teacher_attested_edit"]["status"] == 200
    assert produced["teacher_attested_edit"]["replayed"] is False
    assert produced["historical_accepted_create_replay"]["status"] == 201
    assert produced["historical_accepted_create_replay"]["replayed"] is True
    assert (
        produced["historical_accepted_create_replay"]["record"]
        == produced["generic_create"]["record"]
    )
    assert produced["superseded_exact_without_delivery"]["export"] is None
    assert produced["recording_consumer"] == {
        "old_before_delivery": True,
        "first_apply": True,
        "replayed_apply": False,
        "old_after_delivery": False,
        "new_after_delivery": True,
        "unrelated_after_delivery": True,
    }
    assert produced["no_content_change"]["store_unchanged"] is True
    assert produced["no_content_change"]["result"]["code"] == "NO_CONTENT_CHANGE"
    assert produced["missing_source_draft"]["record"]["knowledge_claims"] == []
    assert produced["child_imagined_removed"]["record"]["content_origin"] == "child_derived"
    assert (
        produced["child_imagined_removed"]["record"]["contributors"]
        == produced["child_story_create"]["record"]["contributors"]
    )
    assert produced["current_exact_after_source_recall"]["ready"] is False
    assert produced["current_exact_after_source_recall"]["export"] is None
