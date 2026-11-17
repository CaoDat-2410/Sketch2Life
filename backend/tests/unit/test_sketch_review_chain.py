"""BE2-05 chain 04 -> 05 and the producer boundary (RV-N15a/b/c)."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.services.sketch_generation import SketchGenerationService
from sketch2life.domain.sketch_proposal import SketchProposal
from sketch2life.infrastructure.ai_jobs.fakes import eligibility_fence_scope
from sketch2life.infrastructure.assistance.harness import CHILD_A, DEVICE_A, ORG, TEACHER
from sketch2life.infrastructure.sketch_generation.adapters import CoordinatedSketchArtifactPort
from sketch2life.infrastructure.sketch_review.adapters import (
    TargetIntegrityError,
    to_review_target,
)
from sketch2life.infrastructure.sketch_review.harness import (
    SketchReviewHarness,
    build_sketch_review_harness,
)

SRC = Path(__file__).resolve().parents[2] / "src/sketch2life"
FILES_05 = (
    SRC / "domain/sketch_review.py",
    SRC / "contracts/schemas/sketch_reviews.py",
    SRC / "application/ports/sketch_review.py",
    SRC / "application/services/sketch_review.py",
    SRC / "infrastructure/sketch_review/adapters.py",
    SRC / "infrastructure/sketch_review/coordination.py",
    SRC / "infrastructure/sketch_review/fakes.py",
)
ALLOWED_SERVICE_CALLS = {"revalidate", "get_record"}
ALLOWED_PORT_CALLS = {"describe", "quarantine"}


class _Spy:
    def __init__(self, inner: object, allowed: set[str], calls: list[str]) -> None:
        self._inner, self._allowed, self._calls = inner, allowed, calls

    def __getattr__(self, name: str) -> Any:
        if name not in self._allowed:
            raise AssertionError(f"05 used non-allowlisted producer call {name}")
        self._calls.append(name)
        return getattr(self._inner, name)


def _content(proposal: SketchProposal) -> list[object]:
    """Immutable content/source/provenance of every version (RV-N15b)."""

    rows: list[object] = [proposal.proposal_id, proposal.binding]
    for version in proposal.versions:
        rows.append((version.version, version.level, version.generation_digest,
                     version.promoted))
    return rows


@pytest.fixture
def h() -> SketchReviewHarness:
    return build_sketch_review_harness()


def test_rv_n15a_only_allowlisted_public_calls(h: SketchReviewHarness) -> None:
    calls: list[str] = []
    h.targets._service = _Spy(h.chain.service, ALLOWED_SERVICE_CALLS, calls)  # type: ignore[assignment]
    h.artifacts._port = _Spy(h.chain.artifact_port, ALLOWED_PORT_CALLS, calls)  # type: ignore[assignment]
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.service.queue_item(TEACHER, proposal_id)
    h.review(proposal_id, "approve")
    h.service.child_payload(DEVICE_A, proposal_id)
    h.review(proposal_id, "reject")
    h.service.refresh(proposal_id, ORG)
    h.service.deliver_quarantine()
    assert set(calls) <= ALLOWED_SERVICE_CALLS | ALLOWED_PORT_CALLS
    assert {"revalidate", "get_record", "describe"} <= set(calls)


def test_rv_n15a_static_no_producer_store_access() -> None:
    forbidden = {"InMemorySketchStore", "CoordinatedSketchRepository", "SketchUnitOfWork",
                 "SketchProposalRepository", "peek", "repository"}
    for path in FILES_05:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        names |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                  and node.module and "sketch_generation" in node.module for alias in node.names}
        hit = forbidden & names
        if path.name == "sketch_review.py" and path.parent.name == "services":
            hit -= {"repository"}  # the 05 service's own repository dependency
        if path.name == "coordination.py":
            hit -= {"repository"}
        assert not hit, f"{path.name} touches producer storage: {hit}"


def test_rv_n15b_content_source_provenance_unchanged(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    source_before = h.chain.h.source_p
    before = _content(h.chain.proposal(proposal_id))
    h.moderate(proposal_id)
    h.review(proposal_id, "approve")
    h.service.child_payload(DEVICE_A, proposal_id)
    h.review(proposal_id, "reject")
    h.service.refresh(proposal_id, ORG)
    assert _content(h.chain.proposal(proposal_id)) == before
    assert h.chain.h.source_p == source_before


def test_rv_n15c_public_revalidation_mutation_is_bounded(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, "approve")
    before = h.chain.proposal(proposal_id)
    events_before = len(h.chain.store.snapshot().events)
    epoch_before = h.chain.h.fences.epochs[eligibility_fence_scope(ORG)]
    h.chain.h.owner.update_member(CHILD_A, consent_effective=False)  # unbumped owner fact
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    after = h.chain.proposal(proposal_id)
    # lifecycle/revision mutation performed by 04's public revalidation, and only that:
    assert str(after.current.pipeline_state) == "stale"
    assert str(after.current.status_reason) == "CONSENT_REVOKED"
    assert after.review_revision == before.review_revision + 1
    assert after.record_version == before.record_version + 1
    assert replace(after.current, pipeline_state=before.current.pipeline_state,
                   status_reason=before.current.status_reason,
                   moderation_state=before.current.moderation_state,
                   cleanup_job_ids=before.current.cleanup_job_ids) == before.current
    assert replace(after, versions=before.versions, record_version=before.record_version,
                   review_revision=before.review_revision,
                   updated_at=before.updated_at) == before
    # ... with its event and the eligibility epoch bump:
    new_events = h.chain.store.snapshot().events[events_before:]
    assert [str(e.reason) for e in new_events if e.proposal_id == proposal_id] == [
        "CONSENT_REVOKED"]
    assert h.chain.h.fences.epochs[eligibility_fence_scope(ORG)] > epoch_before


def test_chain_target_matches_producer_hash_and_detects_tamper(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    proposal = h.chain.proposal(proposal_id)
    target = to_review_target(proposal)
    assert target.content_sha256 == proposal.current.promoted.content_sha256  # type: ignore[union-attr]
    promoted = proposal.current.promoted
    assert promoted is not None
    tampered = replace(proposal, versions=(replace(proposal.current, promoted=replace(
        promoted, text="tampered")),))
    with pytest.raises(TargetIntegrityError):
        to_review_target(tampered)


def test_chain_uses_the_shared_coordinator_and_fences(h: SketchReviewHarness) -> None:
    assert h.repository._coordinator is h.chain.h.coordinator  # type: ignore[attr-defined]
    assert h.repository._fences is h.chain.h.fences  # type: ignore[attr-defined]
    assert isinstance(h.chain.service, SketchGenerationService)
    assert isinstance(h.chain.artifact_port, CoordinatedSketchArtifactPort)
