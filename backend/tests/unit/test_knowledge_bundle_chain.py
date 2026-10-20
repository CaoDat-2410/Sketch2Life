"""Final offline scope/side-effect/invariant and exact producer linearization proofs."""

from __future__ import annotations

import ast
import socket
from dataclasses import asdict, replace
from pathlib import Path
from threading import Event, RLock, Thread

import pytest

from sketch2life.application.services.ai_jobs import AiJobService
from sketch2life.application.services.knowledge_bundle import (
    CreateKnowledgeCommand,
    EditKnowledgeCommand,
    KnowledgeBundleError,
    KnowledgeBundleService,
    KnowledgeCommandResult,
    KnowledgeDependencies,
    KnowledgeResolution,
)
from sketch2life.application.services.vision_analysis import DownstreamMeaning, MeaningState
from sketch2life.contracts.schemas.knowledge_bundles import (
    ClaimEditV1,
    EditKnowledgeBundleV1,
    FactSectionV1,
    KnowledgeSourceRefV1,
    TeacherTopicRefV1,
)
from sketch2life.domain.knowledge_bundle import BasisRef
from sketch2life.infrastructure.ai_jobs.fakes import FakeProvider
from sketch2life.infrastructure.knowledge_bundle.adapters import FixtureKnowledgeFacts
from sketch2life.infrastructure.knowledge_bundle.coordination import KnowledgeCommitCoordinator
from sketch2life.infrastructure.knowledge_bundle.harness import (
    ORG,
    SESSION,
    TEACHER_A,
    TEACHER_B,
    KnowledgeFixtureClock,
    build_knowledge_harness,
)

ROOT = Path(__file__).resolve().parents[3]


def edit_command(harness, record, key="edit"):
    return EditKnowledgeCommand(
        TEACHER_A,
        record.bundle_id,
        key,
        harness.repository.snapshot().heads[record.bundle_id].etag,
        EditKnowledgeBundleV1(
            expected_context_revision=record.context_revision,
            expected_audience_revision=record.audience_revision,
            correction_reason="Teacher correction with source responsibility",
            claims=(
                ClaimEditV1(
                    claim_id=harness.claim.claim_id,
                    revision=2,
                    text="Mèo là động vật có vú và có lông.",
                    source_refs=(
                        KnowledgeSourceRefV1(
                            source_id=harness.source.ref.source_id,
                            revision=harness.source.ref.revision,
                            sha256=harness.source.ref.sha256,
                        ),
                    ),
                    attestation_reason="Teacher attests this sourced statement",
                ),
            ),
        ),
    )


def test_actual_downstream_meaning_is_not_an_enriched_authority_adapter():
    actual = DownstreamMeaning(
        "analysis", 1, MeaningState.CONFIRMED, ("Mèo",), "teacher-confirmation", (), ()
    )
    assert actual.analysis_revision == 1 and actual.confirmation_ref == "teacher-confirmation"
    assert not any(
        hasattr(actual, name)
        for name in ("organization_id", "session_id", "contributors", "source_snapshot_refs")
    )
    harness = build_knowledge_harness()
    trusted = harness.facts.basis(BasisRef("confirmed_meaning", harness.child_basis.ref, 1))
    assert isinstance(harness.facts, FixtureKnowledgeFacts) and trusted == harness.child_basis
    assert (trusted.organization_id, trusted.session_id) == (ORG, SESSION)
    assert trusted.confirmation_ref == "teacher-confirmation-1"
    assert trusted.source_snapshot_refs == ("snapshot-a", "snapshot-b")
    assert [
        (item.participant_id, item.purpose_code, item.snapshot_ref) for item in trusted.contributors
    ] == [
        ("child-a", "knowledge_media", "snapshot-a"),
        ("child-b", "knowledge_media", "snapshot-b"),
    ]
    # No real producer adapter is composed; its missing scope is never fabricated.


def test_actual_knowledge_flows_call_no_job_provider_or_network_and_invent_no_approval(monkeypatch):
    calls = []

    def forbidden(label):
        def reject(*args, **kwargs):
            calls.append(label)
            raise AssertionError(f"unexpected knowledge side effect: {label}")

        return reject

    monkeypatch.setattr(AiJobService, "create_job", forbidden("job"))
    monkeypatch.setattr(FakeProvider, "run", forbidden("provider/model"))
    monkeypatch.setattr(socket.socket, "connect", forbidden("network"))
    harness = build_knowledge_harness()
    draft = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A, "missing", harness.create_body(catalog_claim_ids=("missing",))
        )
    )
    assert draft.status == 201 and draft.record.knowledge_claims == ()
    assert draft.record.readiness == "needs_content_action"
    assert draft.record.action_code == "NO_ELIGIBLE_SOURCE"
    sourced = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "sourced", harness.create_body())
    )
    assert sourced.record.editorial_state == "draft"
    assert sourced.record.readiness == "generation_ready"
    child = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A, "child", harness.create_body(child=True, imagined_refs=("cat-wings",))
        )
    )
    corrected = harness.service.edit(edit_command(harness, child.record))
    current = harness.service.resolve_exact(
        TEACHER_A,
        child.record.bundle_id,
        corrected.record.bundle_version,
        corrected.record.bundle_hash,
    )
    assert current.ready and current.export is not None
    assert current.export.script_sections[-1].kind == "story"
    assert calls == []
    assert "pre_render_approval" not in type(sourced.record).model_fields
    assert "final_video_approved" not in type(sourced.record).model_fields
    paths = list((ROOT / "backend/src/sketch2life").glob("**/knowledge_bundle.py"))
    paths += list((ROOT / "backend/src/sketch2life/infrastructure/knowledge_bundle").glob("*.py"))
    assert paths
    for path in paths:
        imports = [
            node.module or ""
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.ImportFrom)
        ]
        assert not any(
            module.startswith(
                (
                    "sketch2life.application.services.ai_jobs",
                    "sketch2life.infrastructure.ai_jobs",
                    "sketch2life.infrastructure.inference",
                )
            )
            or ".providers" in module
            for module in imports
        ), path.name


def test_existing_other_session_bundle_read_edit_denial_is_safe_and_scoped():
    harness = build_knowledge_harness()
    other_session = "other-session"
    other_topic = replace(harness.topic, ref="other-topic", session_id=other_session)
    other_audience = replace(harness.audience, ref="other-audience", session_id=other_session)
    harness.facts.publish_basis(other_topic)
    harness.facts.publish_audience(other_audience)
    harness.facts.publish_teacher(ORG, other_session, TEACHER_B.principal_id, True)
    harness.facts.publish_mutation(ORG, other_session, True)
    body = harness.create_body().model_copy(
        update={
            "session_id": other_session,
            "basis_ref": TeacherTopicRefV1(kind="teacher_topic", ref=other_topic.ref, revision=1),
        }
    )
    foreign = harness.service.create(CreateKnowledgeCommand(TEACHER_B, "other-create", body))
    assert harness.service.read(TEACHER_B, foreign.record.bundle_id).ready
    before = harness.repository.snapshot()
    denied = harness.service.read(TEACHER_A, foreign.record.bundle_id)
    absent = harness.service.read(TEACHER_A, "missing-bundle")
    assert denied == absent == KnowledgeResolution(False, "KNOWLEDGE_UNAVAILABLE")
    for target in (foreign.record.bundle_id, "missing-bundle"):
        with pytest.raises(KnowledgeBundleError) as caught:
            harness.service.edit(
                EditKnowledgeCommand(
                    TEACHER_A,
                    target,
                    "cross-session-edit",
                    before.heads[foreign.record.bundle_id].etag,
                    EditKnowledgeBundleV1(
                        expected_context_revision=0,
                        expected_audience_revision=2,
                        correction_reason="Attempt scoped edit",
                        sections=(
                            FactSectionV1(
                                section_id="new-facts", claim_refs=(harness.claim.claim_id,)
                            ),
                        ),
                    ),
                )
            )
        assert (caught.value.code, caught.value.status) == ("KNOWLEDGE_UNAVAILABLE", 404)
    assert harness.repository.snapshot() == before
    assert harness.facts.consent_calls == 0


def test_mismatched_repository_and_guard_coordinators_reject_before_any_operation():
    harness = build_knowledge_harness()
    other_facts = FixtureKnowledgeFacts(KnowledgeCommitCoordinator())
    with pytest.raises(ValueError, match="same coordinated boundary"):
        KnowledgeBundleService(
            KnowledgeDependencies(harness.repository, other_facts, KnowledgeFixtureClock())
        )
    assert harness.repository.commits == 0 and not harness.repository.snapshot().versions
    assert other_facts.consent_calls == 0
    accepted = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "coherent", harness.create_body())
    )
    assert accepted.status == 201


def test_derived_script_edits_preserve_original_facts_snapshots_and_v1_bytes():
    harness = build_knowledge_harness()
    originals = (
        asdict(harness.child_basis),
        asdict(harness.audience),
        asdict(harness.source),
        asdict(harness.claim),
    )
    first = harness.service.create(
        CreateKnowledgeCommand(
            TEACHER_A, "origin", harness.create_body(child=True, imagined_refs=("cat-wings",))
        )
    )
    before = harness.repository.snapshot().versions[(first.record.bundle_id, 1)].canonical_bytes
    second = harness.service.edit(edit_command(harness, first.record))
    assert originals == (
        asdict(harness.child_basis),
        asdict(harness.audience),
        asdict(harness.source),
        asdict(harness.claim),
    )
    assert harness.facts.catalog_claims() == (harness.claim,)
    assert harness.facts.sources() == (harness.source,)
    assert (
        harness.facts.basis(BasisRef("confirmed_meaning", harness.child_basis.ref, 1))
        == harness.child_basis
    )
    assert first.record.source_snapshot_refs == second.record.source_snapshot_refs
    assert first.record.contributors == second.record.contributors
    assert first.record.content_origin == second.record.content_origin == "child_derived"
    assert (
        harness.repository.snapshot().versions[(first.record.bundle_id, 1)].canonical_bytes
        == before
    )


class ContendedBoundary:
    def __init__(self):
        self.lock = RLock()
        self.waiting = Event()

    def __enter__(self):
        if not self.lock.acquire(blocking=False):
            self.waiting.set()
            self.lock.acquire()
        return self

    def __exit__(self, *_):
        self.lock.release()


@pytest.mark.parametrize("first_operation", ["resolve", "edit"])
def test_exact_resolve_and_edit_are_linearized_without_event_delivery(monkeypatch, first_operation):
    harness = build_knowledge_harness()
    old = harness.service.create(
        CreateKnowledgeCommand(TEACHER_A, "initial", harness.create_body())
    ).record
    command = edit_command(harness, old)
    boundary = ContendedBoundary()
    monkeypatch.setattr(harness.coordinator, "_lock", boundary)
    completed = Event()
    outcomes = []
    threads = []

    def worker(operation):
        try:
            if operation == "edit":
                outcomes.append(harness.service.edit(command))
            else:
                outcomes.append(
                    harness.service.resolve_exact(TEACHER_A, old.bundle_id, 1, old.bundle_hash)
                )
        except Exception as exc:
            outcomes.append(exc)
        finally:
            completed.set()

    def start_contended(operation):
        thread = Thread(target=worker, args=(operation,))
        threads.append(thread)
        thread.start()
        assert boundary.waiting.wait(5), "second operation did not contend for actual held lock"
        assert not completed.is_set()
        assert harness.repository.snapshot().heads[old.bundle_id].current_version == 1

    if first_operation == "resolve":
        original_current = harness.service._current

        def current(principal, value):
            monkeypatch.setattr(harness.service, "_current", original_current)
            start_contended("edit")
            original_current(principal, value)

        monkeypatch.setattr(harness.service, "_current", current)
        resolved = harness.service.resolve_exact(TEACHER_A, old.bundle_id, 1, old.bundle_hash)
        assert resolved.ready and resolved.export is not None
        assert (
            resolved.export.bundle_version == 1 and resolved.export.bundle_hash == old.bundle_hash
        )
    else:

        def before_commit():
            harness.repository.before_commit = None
            start_contended("resolve")

        harness.repository.before_commit = before_commit
        edited = harness.service.edit(command)
        assert edited.record.bundle_version == 2
    threads[0].join(5)
    assert not threads[0].is_alive() and completed.is_set()
    if first_operation == "resolve":
        assert isinstance(outcomes[0], KnowledgeCommandResult)
        assert outcomes[0].record.bundle_version == 2
    else:
        assert outcomes == [KnowledgeResolution(False, "BUNDLE_SUPERSEDED")]
    denied = harness.service.resolve_exact(TEACHER_A, old.bundle_id, 1, old.bundle_hash)
    assert denied == KnowledgeResolution(False, "BUNDLE_SUPERSEDED")
    state = harness.repository.snapshot()
    assert state.heads[old.bundle_id].current_version == 2
    assert len(state.outbox) == 1  # No consumer was composed or delivery drained.
