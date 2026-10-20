"""Own07 real UoW/coordinator probes; handler integration is added after part6 review."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Event, RLock, Thread

import pytest

from sketch2life.application.ports.knowledge_bundle import (
    KnowledgeAudit,
    KnowledgeConflict,
    KnowledgeReceipt,
    KnowledgeResult,
    KnowledgeStorageFailure,
)
from sketch2life.application.services.knowledge_bundle import (
    CreateKnowledgeCommand,
    EditKnowledgeCommand,
    KnowledgeBundleError,
)
from sketch2life.contracts.schemas.knowledge_bundles import (
    ClaimEditV1,
    EditKnowledgeBundleV1,
    ExactKnowledgeRefV1,
    FactSectionV1,
    KnowledgeSourceRefV1,
    KnowledgeSupersededV1,
    record_from_version,
)
from sketch2life.domain.knowledge_bundle import (
    AudienceContextV1,
    AudienceMemberV1,
    BundleHead,
    FactSection,
    KnowledgeBasisV1,
    ReviewedClaimV1,
    ReviewedSourceV1,
    SourceRefV1,
    build_version,
    catalog_claim,
    plan_edit,
)
from sketch2life.infrastructure.knowledge_bundle.coordination import KnowledgeCommitCoordinator
from sketch2life.infrastructure.knowledge_bundle.fakes import InMemoryKnowledgeRepository
from sketch2life.infrastructure.knowledge_bundle.harness import (
    ORG,
    SESSION,
    TEACHER_A,
    build_knowledge_harness,
)


def original():
    basis = KnowledgeBasisV1("topic", "teacher_topic", 1, "org", "session", "cats")
    audience = AudienceContextV1(
        "aud", "org", "session", 3, 5, (AudienceMemberV1("child", "age-4"),)
    )
    source = ReviewedSourceV1(
        SourceRefV1("source", 1, "a" * 64),
        "Synthetic source",
        "fixture:cats",
        "2026-10-19",
        "cats",
        ("age-4",),
    )
    claim = catalog_claim(ReviewedClaimV1("claim", 1, "Cats are mammals.", (source.ref,)))
    return build_version(
        bundle_id="bundle",
        basis=basis,
        audience=audience,
        claims=(claim,),
        sources=(source,),
        sections=(FactSection("fact", ("claim",)),),
        imagined_elements=(),
        created_by="teacher",
        created_at="2026-10-19T00:00Z",
    )


def edited(old, label="Changed"):
    claim = replace(
        old.knowledge_claims[0],
        revision=2,
        text=label,
        verification_state="teacher_attested",
        attested_by="teacher",
        attestation_reason="Source-mapped correction",
    )
    value = plan_edit(
        old,
        claims=(claim,),
        correction_ref="correction-" + label,
        teacher_principal_id="teacher",
        reason="Clarify",
    )
    assert value is not None
    return value


def stage(tx, value, operation, old=None):
    tx.put_head(
        BundleHead(
            value.bundle_id,
            value.organization_id,
            value.session_id,
            value.bundle_version,
            value.editorial_revision,
        ),
        0 if old is None else old.bundle_version,
    )
    tx.put_version(value)
    if old is not None:
        tx.put_correction(value.corrections[-1])
    key = ("org", "teacher", "create" if old is None else "edit", value.bundle_id, operation)
    tx.put_receipt(
        KnowledgeReceipt(
            key,
            "fingerprint-" + operation,
            KnowledgeResult(201 if old is None else 200, record_from_version(value)),
            value,
        )
    )
    tx.add_audit(
        KnowledgeAudit(
            operation,
            "create" if old is None else "edit",
            value.bundle_id,
            value.bundle_version,
            "teacher",
        )
    )
    if old is not None:
        tx.add_event(
            KnowledgeSupersededV1(
                event_id="event-" + operation,
                organization_id="org",
                session_id="session",
                old_bundle=ExactKnowledgeRefV1(
                    bundle_id=old.bundle_id,
                    bundle_version=old.bundle_version,
                    bundle_hash=old.bundle_hash,
                ),
                new_bundle=ExactKnowledgeRefV1(
                    bundle_id=value.bundle_id,
                    bundle_version=value.bundle_version,
                    bundle_hash=value.bundle_hash,
                ),
                correction_ref=value.corrections[-1].correction_ref,
                operation_id=operation,
            )
        )


@pytest.mark.parametrize(
    "failure",
    [
        "put_head",
        "put_version",
        "put_correction",
        "put_receipt",
        "add_audit",
        "add_event",
        "commit",
    ],
)
def test_every_staged_edit_failure_rolls_back_all_collections_and_retries(failure):
    repo = InMemoryKnowledgeRepository(KnowledgeCommitCoordinator())
    old = original()
    with repo.transaction() as tx:
        stage(tx, old, "create")
    before = repo.snapshot()
    repo.fail_next(failure)
    new = edited(old)
    with pytest.raises(KnowledgeStorageFailure, match=failure), repo.transaction() as tx:
        stage(tx, new, "edit", old)
    assert repo.snapshot() == before
    assert repo.commits == 1
    with repo.transaction() as tx:
        stage(tx, new, "edit", old)
    after = repo.snapshot()
    assert after.versions[("bundle", 1)].canonical_bytes == old.canonical_bytes
    assert after.versions[("bundle", 2)] == new
    assert len(after.receipts) == 2
    assert len(after.corrections) == len(after.outbox) == 1


def test_nested_accepted_unit_survives_outer_generation_conflict():
    repo = InMemoryKnowledgeRepository(KnowledgeCommitCoordinator())
    old = original()
    with repo.transaction() as tx:
        stage(tx, old, "create")
    inner = edited(old, "Inner")
    outer = edited(old, "Outer")

    def commit_inner():
        repo.before_commit = None
        with repo.transaction() as tx:
            stage(tx, inner, "inner", old)

    repo.before_commit = commit_inner
    with pytest.raises(KnowledgeConflict, match="generation"), repo.transaction() as tx:
        stage(tx, outer, "outer", old)
    stored = repo.snapshot()
    assert stored.versions[("bundle", 2)] == inner
    assert {key[-1] for key in stored.receipts} == {"create", "inner"}
    assert set(stored.outbox) == {"event-inner"}
    assert set(stored.corrections) == {"correction-Inner"}
    assert repo.commits == 2


def test_cas_uniqueness_and_no_public_alias_to_committed_state():
    repo = InMemoryKnowledgeRepository(KnowledgeCommitCoordinator())
    old = original()
    with repo.transaction() as tx:
        stage(tx, old, "create")
    before = repo.snapshot()
    with pytest.raises(KnowledgeConflict), repo.transaction() as tx:
        tx.put_version(old)
    with pytest.raises(KnowledgeConflict), repo.transaction() as tx:
        tx.put_head(BundleHead("bundle", "org", "session", 2, 2), 0)
    with pytest.raises(KnowledgeConflict), repo.transaction() as tx:
        tx.put_receipt(next(iter(before.receipts.values())))
    copied = repo.snapshot()
    copied.heads.clear()
    with repo.transaction() as tx:
        value = tx.get_version("bundle", 1)
        assert value is not None
        value.__dict__["bundle_hash"] = "corrupted copy"
        receipt = tx.get_receipt(next(iter(before.receipts)))
        assert receipt is not None
        receipt.result.record.__dict__["created_by"] = "corrupted copy"
    assert repo.snapshot() == before
    assert repo.commits == 1


@pytest.mark.parametrize("rollback", [False, True])
def test_same_thread_publication_is_not_applied_until_outer_exit(rollback):
    coordinator = KnowledgeCommitCoordinator()
    facts = {"source_current": True}

    def recalled():
        facts["source_current"] = False

    def run():
        with coordinator.unit():
            with coordinator.unit():
                assert coordinator.publish(recalled) is False
                assert facts == {"source_current": True}
            assert facts == {"source_current": True}
            if rollback:
                raise ValueError("unit rollback")

    if rollback:
        with pytest.raises(ValueError, match="unit rollback"):
            run()
    else:
        run()
    assert facts == {"source_current": False}


class ContentionProbe:
    """Signal actual failed try-acquire, not a guessed publisher scheduling delay."""

    def __init__(self):
        self.lock = RLock()
        self.contended = Event()

    def __enter__(self):
        if not self.lock.acquire(blocking=False):
            self.contended.set()
            self.lock.acquire()
        return self

    def __exit__(self, *_):
        self.lock.release()


def test_other_thread_publication_waits_for_actual_lock_contention(monkeypatch):
    coordinator = KnowledgeCommitCoordinator()
    probe = ContentionProbe()
    monkeypatch.setattr(coordinator, "_lock", probe)
    facts = {"source_current": True}
    applied = Event()

    def publish():
        assert coordinator.publish(lambda: facts.update(source_current=False)) is True
        applied.set()

    with coordinator.unit():
        thread = Thread(target=publish)
        thread.start()
        assert probe.contended.wait(5), "publisher did not attempt the held boundary"
        assert facts["source_current"] is True
        assert not applied.is_set()
    thread.join(5)
    assert not thread.is_alive()
    assert applied.is_set()
    assert facts["source_current"] is False


@pytest.mark.parametrize("primary", [False, True])
def test_failed_deferred_callback_does_not_lose_later_publications_or_primary_error(primary):
    coordinator = KnowledgeCommitCoordinator()
    facts = {"current": True}

    def fail():
        raise RuntimeError("publication failure")

    expected = ValueError if primary else RuntimeError
    with pytest.raises(expected) as caught, coordinator.unit():
        assert coordinator.publish(fail) is False
        assert coordinator.publish(lambda: facts.update(current=False)) is False
        if primary:
            raise ValueError("primary unit failure")
    assert facts["current"] is False
    if primary:
        assert str(caught.value) == "primary unit failure"
        assert "Deferred publication" in caught.value.__notes__[0]
    finished = Event()
    thread = Thread(
        target=lambda: (coordinator.publish(lambda: facts.update(current=True)), finished.set())
    )
    thread.start()
    thread.join(5)
    assert not thread.is_alive() and finished.is_set() and facts["current"] is True


def test_after_commit_failure_is_lost_acknowledgement_with_accepted_receipt():
    repo = InMemoryKnowledgeRepository(KnowledgeCommitCoordinator())
    value = original()
    repo.fail_next("after_commit")
    with pytest.raises(KnowledgeStorageFailure, match="after_commit"), repo.transaction() as tx:
        stage(tx, value, "create")
    assert repo.commits == 1
    assert repo.snapshot().versions[("bundle", 1)] == value
    assert len(repo.snapshot().receipts) == 1


@pytest.mark.parametrize("rollback", [False, True])
def test_escaped_completed_unit_cannot_mutate_committed_storage(rollback):
    repo = InMemoryKnowledgeRepository(KnowledgeCommitCoordinator())
    old = original()
    escaped = None

    def execute():
        nonlocal escaped
        with repo.transaction() as tx:
            escaped = tx
            stage(tx, old, "create")
            if rollback:
                raise ValueError("rollback")

    if rollback:
        with pytest.raises(ValueError, match="rollback"):
            execute()
    else:
        execute()
    before = repo.snapshot()
    commits = repo.commits
    assert escaped is not None
    with pytest.raises(KnowledgeStorageFailure, match="closed"):
        escaped.put_head(BundleHead("bundle", "org", "session", 2, 2), 1)
    with pytest.raises(KnowledgeStorageFailure, match="closed"):
        escaped.get_head("bundle")
    assert repo.snapshot() == before
    assert repo.commits == commits


def handler_create(h, *, child=True, key="handler-create"):
    return h.service.create(CreateKnowledgeCommand(TEACHER_A, key, h.create_body(child=child)))


def handler_edit(h, record, *, key="handler-edit", label="Mèo là động vật có vú và có lông."):
    body = EditKnowledgeBundleV1(
        expected_context_revision=record.context_revision,
        expected_audience_revision=record.audience_revision,
        correction_reason="Teacher source-mapped correction",
        claims=(
            ClaimEditV1(
                claim_id=h.claim.claim_id,
                revision=2,
                text=label,
                source_refs=(
                    KnowledgeSourceRefV1(
                        source_id=h.source.ref.source_id,
                        revision=h.source.ref.revision,
                        sha256=h.source.ref.sha256,
                    ),
                ),
                attestation_reason="Teacher takes responsibility",
            ),
        ),
    )
    return EditKnowledgeCommand(
        TEACHER_A, record.bundle_id, key, h.repository.snapshot().heads[record.bundle_id].etag, body
    )


GUARD_REASONS = {
    "source": "SOURCE_RECALLED",
    "basis_revision": "BASIS_REVISION_MISMATCH",
    "basis_confirmation": "BASIS_CHANGED",
    "basis_unconfirmed": "BASIS_UNCONFIRMED",
    "basis_not_applicable": "BASIS_NOT_APPLICABLE",
    "context": "CONTEXT_REVISION_MISMATCH",
    "audience": "AUDIENCE_REVISION_MISMATCH",
    "roster": "CONTRIBUTOR_MEMBERSHIP_REQUIRED",
    "consent": "CONSENT_REQUIRED",
    "policy": "POLICY_CHANGED",
    "policy_revoke": "POLICY_UNAVAILABLE",
    "teacher": "KNOWLEDGE_UNAVAILABLE",
    "disclosure": "KNOWLEDGE_UNAVAILABLE",
    "mutation": "MUTATION_PAUSED",
    "catalog": "CATALOG_CLAIM_MISMATCH",
}


def revoke(h, family):
    if family == "source":
        return h.facts.publish_source(replace(h.source, recalled=True))
    if family.startswith("basis_"):
        changes = {
            "basis_revision": {"revision": 2},
            "basis_confirmation": {"confirmation_ref": "new-confirmation-same-revision"},
            "basis_unconfirmed": {"confirmed": False},
            "basis_not_applicable": {"applicable": False},
        }
        return h.facts.publish_basis(replace(h.child_basis, **changes[family]))
    if family in {"context", "audience", "roster"}:
        changes = {
            "context": {"context_revision": 1},
            "audience": {"audience_revision": 3},
            "roster": {"members": h.audience.members[:1]},
        }
        return h.facts.publish_audience(replace(h.audience, **changes[family]))
    if family == "consent":
        return h.facts.publish_consent(ORG, SESSION, h.child_basis.contributors[-1], False)
    if family == "policy":
        return h.facts.publish_policy("changed-policy", True)
    if family == "policy_revoke":
        return h.facts.publish_policy(h.facts.policy()[0], False)
    if family == "teacher":
        return h.facts.publish_teacher(ORG, SESSION, TEACHER_A.principal_id, False)
    if family == "disclosure":
        return h.facts.publish_disclosure(ORG, SESSION, TEACHER_A.principal_id, False)
    if family == "mutation":
        return h.facts.publish_mutation(ORG, SESSION, False)
    if family == "catalog":
        return h.facts.publish_catalog_claim(replace(h.claim, text="Changed reviewed catalog text"))
    raise AssertionError("uncovered guard family")


@pytest.mark.parametrize("family", GUARD_REASONS)
def test_actual_handler_catches_each_current_guard_published_before_unit(family):
    h = build_knowledge_harness()
    old = handler_create(h).record
    command = handler_edit(h, old)
    before = h.repository.snapshot()

    def before_unit():
        h.repository.before_transaction = None
        assert revoke(h, family) is True

    h.repository.before_transaction = before_unit
    with pytest.raises(KnowledgeBundleError) as caught:
        h.service.edit(command)
    assert caught.value.code == GUARD_REASONS[family]
    assert h.repository.snapshot() == before
    resolution = h.service.read(TEACHER_A, old.bundle_id)
    if family == "mutation":
        assert resolution.ready and resolution.reason is None
        assert resolution.export is not None and resolution.export.bundle_hash == old.bundle_hash
    else:
        assert not resolution.ready and resolution.export is None
        assert resolution.reason == GUARD_REASONS[family]


@pytest.mark.parametrize("family", [family for family in GUARD_REASONS if family != "mutation"])
def test_mutation_pause_preserves_every_other_current_read_and_exact_guard(family):
    h = build_knowledge_harness()
    old = handler_create(h).record
    h.facts.publish_mutation(ORG, SESSION, False)
    assert revoke(h, family) is True
    before = h.repository.snapshot()
    for resolution in (
        h.service.read(TEACHER_A, old.bundle_id),
        h.service.resolve_exact(TEACHER_A, old.bundle_id, 1, old.bundle_hash),
    ):
        assert not resolution.ready and resolution.export is None
        assert resolution.reason == GUARD_REASONS[family]
    assert h.repository.snapshot() == before


@pytest.mark.parametrize("family", GUARD_REASONS)
def test_actual_handler_defers_each_guard_until_accepted_commit_then_withholds(family):
    h = build_knowledge_harness()
    old = handler_create(h).record
    command = handler_edit(h, old)
    if family == "catalog":
        # Retain catalog-reviewed claims here; an explicitly attested correction
        # deliberately depends on its reviewed source, not current catalog wording.
        command = replace(
            command,
            body=command.body.model_copy(
                update={
                    "claims": None,
                    "sections": (
                        FactSectionV1(section_id="catalog-facts", claim_refs=(h.claim.claim_id,)),
                    ),
                }
            ),
        )

    def before_commit():
        h.repository.before_commit = None
        assert revoke(h, family) is False
        # Check actual authorized content while the boundary remains held.
        current = h.service.read(TEACHER_A, old.bundle_id)
        assert current.ready and current.export is not None
        assert current.export.bundle_version == 1
        assert current.export.script_text == old.script_text

    h.repository.before_commit = before_commit
    accepted = h.service.edit(command)
    assert accepted.record.bundle_version == 2 and accepted.record.readiness == "generation_ready"
    current = h.service.read(TEACHER_A, old.bundle_id)
    if family == "mutation":
        assert current.ready and current.reason is None and current.export is not None
        assert current.export.bundle_hash == accepted.record.bundle_hash
        with pytest.raises(KnowledgeBundleError, match="MUTATION_PAUSED"):
            h.service.edit(handler_edit(h, accepted.record, key="after-queued-pause"))
    else:
        assert not current.ready and current.export is None
        assert current.reason == GUARD_REASONS[family]
    assert len(h.repository.snapshot().outbox) == 1


@pytest.mark.parametrize(
    "family", ["source", "basis_confirmation", "context", "consent", "policy_revoke", "disclosure"]
)
def test_actual_handler_deferred_guard_drains_after_rollback_and_lock_releases(family):
    h = build_knowledge_harness()
    old = handler_create(h).record
    before = h.repository.snapshot()
    command = handler_edit(h, old)

    def before_commit():
        h.repository.before_commit = None
        assert revoke(h, family) is False
        assert h.service.read(TEACHER_A, old.bundle_id).ready

    h.repository.before_commit = before_commit
    h.repository.fail_next("commit")
    with pytest.raises(KnowledgeBundleError, match="STORAGE_UNAVAILABLE"):
        h.service.edit(command)
    assert h.repository.snapshot() == before
    current = h.service.read(TEACHER_A, old.bundle_id)
    assert current.export is None and current.reason == GUARD_REASONS[family]
    finished = Event()
    thread = Thread(target=lambda: (h.repository.snapshot(), finished.set()))
    thread.start()
    thread.join(5)
    assert finished.is_set() and not thread.is_alive()


@pytest.mark.parametrize(
    "failure",
    [
        "put_head",
        "put_version",
        "put_correction",
        "put_receipt",
        "add_audit",
        "add_event",
        "commit",
    ],
)
def test_actual_edit_storage_failure_retries_same_key_once(failure):
    h = build_knowledge_harness()
    old = handler_create(h).record
    command = handler_edit(h, old)
    before = h.repository.snapshot()
    h.repository.fail_next(failure)
    with pytest.raises(KnowledgeBundleError) as caught:
        h.service.edit(command)
    assert (caught.value.code, caught.value.status) == ("STORAGE_UNAVAILABLE", 503)
    assert h.repository.snapshot() == before
    accepted = h.service.edit(command)
    assert accepted.status == 200 and not accepted.replayed
    replay = h.service.edit(command)
    assert replay.replayed and replay.result == accepted.result
    snapshot = h.repository.snapshot()
    assert len(snapshot.versions) == 2 and len(snapshot.receipts) == 2
    assert len(snapshot.corrections) == len(snapshot.outbox) == 1


@pytest.mark.parametrize("same_key", [False, True])
def test_actual_nested_edit_preserves_winner_and_recovers_only_same_operation(same_key):
    h = build_knowledge_harness()
    old = handler_create(h).record
    outer = handler_edit(h, old, key="same" if same_key else "outer")
    inner = outer if same_key else handler_edit(h, old, key="inner", label="Mèo có lông.")
    winners = []

    def nested():
        h.repository.before_commit = None
        winners.append(h.service.edit(inner))

    h.repository.before_commit = nested
    if same_key:
        recovered = h.service.edit(outer)
        assert recovered.replayed and recovered.result == winners[0].result
    else:
        with pytest.raises(KnowledgeBundleError, match="STALE_AGGREGATE"):
            h.service.edit(outer)
    state = h.repository.snapshot()
    assert state.versions[(old.bundle_id, 2)].bundle_hash == winners[0].record.bundle_hash
    assert {key[-1] for key in state.receipts} == {
        "handler-create",
        "same" if same_key else "inner",
    }
    assert len(state.versions) == 2 and len(state.corrections) == len(state.outbox) == 1


@pytest.mark.parametrize("same_key", [False, True])
def test_actual_nested_create_preserves_inner_receipt_and_unique_bundle(same_key):
    h = build_knowledge_harness()
    outer = CreateKnowledgeCommand(TEACHER_A, "same" if same_key else "outer", h.create_body())
    inner = outer if same_key else replace(outer, idempotency_key="inner")
    winners = []

    def nested():
        h.repository.before_commit = None
        winners.append(h.service.create(inner))

    h.repository.before_commit = nested
    if same_key:
        recovered = h.service.create(outer)
        assert recovered.replayed and recovered.status == 201
        assert recovered.result == winners[0].result
    else:
        with pytest.raises(KnowledgeBundleError, match="STALE_AGGREGATE"):
            h.service.create(outer)
    stored = h.repository.snapshot()
    assert set(stored.heads) == {winners[0].record.bundle_id}
    assert len(stored.versions) == len(stored.receipts) == len(stored.audit) == 1
    assert not stored.corrections and not stored.outbox


def test_same_operation_nested_recovery_reauthorizes_after_queued_disclosure_withdrawal():
    h = build_knowledge_harness()
    old = handler_create(h).record
    command = handler_edit(h, old, key="same")
    winners = []

    def nested():
        h.repository.before_commit = None
        winners.append(h.service.edit(command))
        assert (
            h.facts.publish_consent(
                ORG, SESSION, h.child_basis.contributors[-1], False, disclose=False
            )
            is False
        )

    h.repository.before_commit = nested
    with pytest.raises(KnowledgeBundleError) as caught:
        h.service.edit(command)
    assert (caught.value.code, caught.value.status) == ("KNOWLEDGE_UNAVAILABLE", 404)
    stored = h.repository.snapshot()
    assert stored.versions[(old.bundle_id, 2)].bundle_hash == winners[0].record.bundle_hash
    assert len(stored.receipts) == len(stored.versions) == 2
    assert len(stored.corrections) == len(stored.outbox) == 1
    assert h.service.read(TEACHER_A, old.bundle_id).export is None


@pytest.mark.parametrize("operation", ["create", "edit"])
def test_lost_acknowledgement_replays_original_result_without_duplicate_side_effects(operation):
    h = build_knowledge_harness()
    if operation == "create":
        command = CreateKnowledgeCommand(TEACHER_A, "lost", h.create_body())
        method = h.service.create
    else:
        old = handler_create(h).record
        command = handler_edit(h, old, key="lost")
        method = h.service.edit
    h.repository.fail_next("after_commit")
    with pytest.raises(KnowledgeBundleError, match="STORAGE_UNAVAILABLE"):
        method(command)
    committed = h.repository.snapshot()
    replay = method(command)
    assert replay.replayed and replay.status == (201 if operation == "create" else 200)
    assert h.repository.snapshot() == committed
    h.facts.publish_disclosure(ORG, SESSION, TEACHER_A.principal_id, False)
    with pytest.raises(KnowledgeBundleError, match="KNOWLEDGE_UNAVAILABLE"):
        method(command)
    assert h.repository.snapshot() == committed


def test_two_actual_edits_with_same_etag_have_one_accepted_version():
    h = build_knowledge_harness()
    old = handler_create(h).record
    commands = [
        handler_edit(h, old, key="first", label="Mèo có lông."),
        handler_edit(h, old, key="second", label="Mèo là động vật có vú."),
    ]
    barrier = Barrier(2)
    h.repository.before_transaction = lambda: barrier.wait(timeout=5)

    def run(command):
        try:
            return h.service.edit(command)
        except KnowledgeBundleError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, commands))
    h.repository.before_transaction = None
    accepted = [value for value in outcomes if not isinstance(value, KnowledgeBundleError)]
    denied = [value for value in outcomes if isinstance(value, KnowledgeBundleError)]
    assert len(accepted) == len(denied) == 1
    assert denied[0].code == "PRECONDITION_FAILED" and denied[0].status == 412
    state = h.repository.snapshot()
    assert len(state.versions) == 2 and len(state.outbox) == len(state.corrections) == 1
    assert state.versions[(old.bundle_id, 2)].bundle_hash == accepted[0].record.bundle_hash


def test_real_other_thread_source_recall_cannot_enter_handler_commit_window(monkeypatch):
    h = build_knowledge_harness()
    old = handler_create(h).record
    command = handler_edit(h, old)
    probe = ContentionProbe()
    monkeypatch.setattr(h.coordinator, "_lock", probe)
    published = Event()
    threads = []

    def publish():
        assert h.facts.publish_source(replace(h.source, recalled=True)) is True
        published.set()

    def before_commit():
        h.repository.before_commit = None
        thread = Thread(target=publish)
        threads.append(thread)
        thread.start()
        assert probe.contended.wait(5)
        assert not published.is_set() and not h.facts.sources()[0].recalled
        assert h.service.read(TEACHER_A, old.bundle_id).ready

    h.repository.before_commit = before_commit
    accepted = h.service.edit(command)
    threads[0].join(5)
    assert not threads[0].is_alive() and published.is_set()
    assert accepted.record.bundle_version == 2
    current = h.service.read(TEACHER_A, old.bundle_id)
    assert not current.ready and current.export is None and current.reason == "SOURCE_RECALLED"


def test_deferred_failure_after_commit_preserves_receipt_and_drains_later_actual_source_recall():
    h = build_knowledge_harness()
    old = handler_create(h).record
    command = handler_edit(h, old)

    def fail():
        raise RuntimeError("publication failed")

    def before_commit():
        h.repository.before_commit = None
        assert h.coordinator.publish(fail) is False
        assert h.facts.publish_source(replace(h.source, recalled=True)) is False

    h.repository.before_commit = before_commit
    with pytest.raises(KnowledgeBundleError, match="STORAGE_UNAVAILABLE"):
        h.service.edit(command)
    committed = h.repository.snapshot()
    assert len(committed.versions) == 2 and len(committed.outbox) == 1
    assert h.service.read(TEACHER_A, old.bundle_id).reason == "SOURCE_RECALLED"
    replay = h.service.edit(command)
    assert replay.replayed and replay.record.bundle_version == 2
    assert h.repository.snapshot() == committed


def test_sourced_teacher_attestation_is_independent_of_later_catalog_claim_wording():
    h = build_knowledge_harness()
    old = handler_create(h).record
    corrected = h.service.edit(handler_edit(h, old))
    assert corrected.record.knowledge_claims[0].verification_state == "teacher_attested"
    h.facts.publish_catalog_claim(replace(h.claim, text="Different catalog wording"))
    current = h.service.read(TEACHER_A, old.bundle_id)
    assert current.ready and current.export is not None
    assert current.export.bundle_hash == corrected.record.bundle_hash
    assert current.export.knowledge_claims[0].attested_by == TEACHER_A.principal_id


@pytest.mark.parametrize("different", ["org", "session", "purpose", "snapshot"])
def test_actual_child_handler_cannot_borrow_consent_from_different_trusted_scope(different):
    h = build_knowledge_harness()
    contributor = h.child_basis.contributors[-1]
    h.facts.publish_consent(ORG, SESSION, contributor, False)
    organization_id, session_id = ORG, SESSION
    borrowed = contributor
    if different == "org":
        organization_id = "other-org"
    elif different == "session":
        session_id = "other-session"
    elif different == "purpose":
        borrowed = replace(contributor, purpose_code="another-purpose")
    else:
        borrowed = replace(contributor, snapshot_ref="another-snapshot")
    h.facts.publish_consent(organization_id, session_id, borrowed, True)
    with pytest.raises(KnowledgeBundleError) as caught:
        handler_create(h)
    assert caught.value.code == "CONSENT_REQUIRED"
    assert not h.repository.snapshot().versions and not h.repository.snapshot().receipts


def test_actual_child_wrong_purpose_is_not_promoted_by_positive_consent_grant():
    h = build_knowledge_harness()
    wrong = replace(h.child_basis.contributors[-1], purpose_code="another-purpose")
    h.facts.publish_basis(
        replace(h.child_basis, contributors=(h.child_basis.contributors[0], wrong))
    )
    h.facts.publish_consent(ORG, SESSION, wrong, True)
    with pytest.raises(KnowledgeBundleError) as caught:
        handler_create(h)
    assert caught.value.code == "PURPOSE_NOT_PERMITTED"
    assert h.repository.commits == 0 and not h.repository.snapshot().receipts


@pytest.mark.parametrize("invalid_header", ["", "x" * 513], ids=["empty", "overflow"])
def test_header_bounds_checked_before_mutation_and_replay(invalid_header):
    h = build_knowledge_harness()
    accepted = handler_create(h)
    before = h.repository.snapshot()
    command = handler_edit(h, accepted.record)
    with pytest.raises(KnowledgeBundleError) as caught:
        h.service.edit(replace(command, if_match=invalid_header))
    assert (caught.value.code, caught.value.status) == ("FIELD_VALIDATION_FAILED", 400)
    with pytest.raises(KnowledgeBundleError) as caught:
        h.service.create(
            CreateKnowledgeCommand(
                TEACHER_A, "handler-create", h.create_body(child=True), invalid_header
            )
        )
    assert caught.value.status == 400
    assert h.repository.snapshot() == before


def test_whitespace_correction_reason_rejects_even_when_content_is_noop():
    h = build_knowledge_harness()
    accepted = handler_create(h)
    body = EditKnowledgeBundleV1(
        expected_context_revision=0,
        expected_audience_revision=2,
        correction_reason="Initial valid reason",
        sections=(FactSectionV1(section_id="facts", claim_refs=(h.claim.claim_id,)),),
    )
    before = h.repository.snapshot()
    raw = json.loads(body.model_dump_json())
    raw["correction_reason"] = " "
    with pytest.raises(KnowledgeBundleError) as caught:
        h.service.edit(
            EditKnowledgeCommand(
                TEACHER_A,
                accepted.record.bundle_id,
                "blank-reason",
                before.heads[accepted.record.bundle_id].etag,
                json.dumps(raw),
            )
        )
    assert caught.value.status == 400 and caught.value.code == "FIELD_VALIDATION_FAILED"
    assert h.repository.snapshot() == before and h.repository.commits == 1
