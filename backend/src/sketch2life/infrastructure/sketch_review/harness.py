"""BE2-05 synthetic harness (FIXTURE_ONLY): real BE2-04 chain + 05 on the shared coordinator.

``build_sketch_review_harness`` builds the accepted SK1 chain harness unchanged and composes the
05 service over the SAME ``AssistanceCommitCoordinator`` and ``HookedOwnerFences``. Proposals
reviewed here are produced by the real ``SketchGenerationService`` (no handcrafted records).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.ports.sketch_generation import GenerationRequest, GenerationSucceeded
from sketch2life.application.ports.sketch_review import ReviewPolicy
from sketch2life.application.services.sketch_review import (
    ReviewCommand,
    ReviewResult,
    SketchReviewDependencies,
    SketchReviewService,
)
from sketch2life.contracts.schemas.ai_contract_candidates import (
    ConsentRevisionRefV1,
    ExactContentReviewCommandV1,
    SessionAudienceV1,
    SessionContentContextV1,
)
from sketch2life.domain.sketch_proposal import OutputPart
from sketch2life.domain.sketch_review import ReviewTarget
from sketch2life.infrastructure.ai_jobs.fakes import grant_fence_scope
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    CHILD_C,
    CLASS,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    LEVEL,
    LEVEL_2,
    ORG,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    SESSION,
    TEACHER,
)
from sketch2life.infrastructure.sketch_generation.fakes import default_outcome
from sketch2life.infrastructure.sketch_generation.harness import (
    SketchChainHarness,
    build_sketch_chain_harness,
)
from sketch2life.infrastructure.sketch_review.adapters import (
    CoordinatedReviewArtifacts,
    SketchServiceReviewTargetReader,
)
from sketch2life.infrastructure.sketch_review.coordination import (
    CoordinatedReviewTokens,
    CoordinatedSketchReviewRepository,
    InMemorySketchReviewStore,
    ReviewEligibilityEpochs,
    review_context_fence_scope,
    review_policy_fence_scope,
)
from sketch2life.infrastructure.sketch_review.fakes import (
    FIXTURE_BLOCKED_TERM,
    DeviceBinding,
    FakeChildCache,
    FakeReadModelDispatcher,
    FakeReviewAuthority,
    FakeReviewContext,
    FakeTicketIssuer,
    FixtureReviewPolicy,
    FixtureSketchModeration,
    fixture_review_policy,
)

REVIEW_CONTEXT_REVISION = 5


def unsafe_text_outcome(request: GenerationRequest) -> GenerationSucceeded:
    """Generator output that the 05 fixture moderation blocks (text carries the fixture term)."""

    outcome = default_outcome(request)
    parts = tuple(replace(p, text=f"{p.text} {FIXTURE_BLOCKED_TERM}")
                  if p.kind == "text_or_question" and p.text else p for p in outcome.parts)
    if not any(p.kind == "text_or_question" for p in parts):
        parts = (*parts, OutputPart("text_or_question", text=FIXTURE_BLOCKED_TERM))
    return replace(outcome, parts=parts)


@dataclass
class SketchReviewHarness:
    chain: SketchChainHarness
    store: InMemorySketchReviewStore
    repository: CoordinatedSketchReviewRepository
    tokens: CoordinatedReviewTokens
    epochs: ReviewEligibilityEpochs
    targets: SketchServiceReviewTargetReader
    artifacts: CoordinatedReviewArtifacts
    policy: FixtureReviewPolicy
    context: FakeReviewContext
    authority: FakeReviewAuthority
    moderation: FixtureSketchModeration
    service: SketchReviewService
    ticket: FakeTicketIssuer
    cache: FakeChildCache
    dispatcher: FakeReadModelDispatcher
    keys: int = 0

    # ------------------------------------------------------------- producer side
    def pending(self, *, level: str = LEVEL_2, group: bool = False,
                unsafe: bool = False) -> str:
        """One real 04 proposal; within one harness each call needs a distinct A1 request
        (level/canvas), because an identical request is an A1 cache hit without a new job."""

        chain = self.chain
        if unsafe:
            chain.generator.script = unsafe_text_outcome
        command = (chain.h.group_command(level=level) if group
                   else chain.h.command(level=level))
        proposal_id = chain.open_ready(command)
        chain.run_sketch(proposal_id)
        chain.generator.script = None
        target = self.target(proposal_id)
        assert target.reviewable, target.pipeline_state
        return proposal_id

    def target(self, proposal_id: str) -> ReviewTarget:
        target = self.targets.read(proposal_id)
        assert target is not None
        return target

    # ------------------------------------------------------------- 05 commands
    def key(self) -> str:
        self.keys += 1
        return f"key_fx_be205_{self.keys:04d}"

    def etag(self, proposal_id: str, principal: Principal = TEACHER) -> str:
        return str(self.service.queue_item(principal, proposal_id)["review_etag"])

    def command(self, proposal_id: str, decision: str = "approve", *, reason: str | None = None,
                participants: tuple[str, ...] | None = None, groups: tuple[str, ...] | None = None,
                audience_revision: int | None = None,
                consent: tuple[tuple[str, int], ...] | None = None,
                target: ReviewTarget | None = None) -> ExactContentReviewCommandV1:
        target = target or self.target(proposal_id)
        snapshot = self.context.current(ORG, target.session_id, (target.contributor,))
        assert snapshot is not None
        if reason is None and decision != "approve":
            reason = f"Fixture reason for {decision}"
        refs = consent if consent is not None else snapshot.consent_refs
        return ExactContentReviewCommandV1(
            target_kind="sketch_proposal", target_id=proposal_id,
            target_version=target.proposal_version,
            target_hash=target.content_sha256 or "0" * 64,
            source_context_revision=target.context_revision,
            decision=decision,  # type: ignore[arg-type]
            reason=reason,
            review_context=SessionContentContextV1(
                kind="session_content", session_id=target.session_id,
                audience_context_revision=(audience_revision if audience_revision is not None
                                           else snapshot.audience_context_revision),
                consent_revision_refs=tuple(ConsentRevisionRefV1(subject_ref=s, revision=r)
                                            for s, r in refs),
                review_purpose="teaching_delivery"),
            audience_scope=SessionAudienceV1(
                session_id=target.session_id,
                group_ids=groups if groups is not None else (
                    (target.group_id,) if target.group_id else ()),
                participant_ids=participants if participants is not None else target.audience),
        )

    def review(self, proposal_id: str, decision: str = "approve", *,
               principal: Principal = TEACHER, key: str | None = None, etag: str | None = "auto",
               body: Any = None, **command: Any) -> ReviewResult:
        if etag == "auto":
            etag = self.etag(proposal_id)
        payload = body if body is not None else self.command(proposal_id, decision, **command)
        return self.service.record_review(ReviewCommand(
            principal, proposal_id, key if key is not None else self.key(), etag, payload))

    def moderate(self, proposal_id: str) -> object:
        return self.service.moderate(TEACHER, proposal_id)

    # ------------------------------------------------------------- owner publications
    def publish_review_policy(self, snapshot: ReviewPolicy | None) -> bool:
        def publication() -> None:
            self.policy.snapshot = snapshot
            self.chain.h.fences.bump(review_policy_fence_scope(ORG))

        return self.chain.h.coordinator.request_publication(publication)

    def publish_review_context(self, change: Callable[[], object]) -> bool:
        def publication() -> None:
            change()
            self.chain.h.fences.bump(review_context_fence_scope(ORG, SESSION))

        return self.chain.h.coordinator.request_publication(publication)

    def bump_audience_revision(self) -> bool:
        def change() -> None:
            self.context.sessions[(ORG, SESSION)].audience_context_revision += 1

        return self.publish_review_context(change)

    def publish_grant_change(self, principal: Principal, change: Callable[[], object]) -> bool:
        def publication() -> None:
            change()
            self.chain.h.fences.bump(grant_fence_scope(ORG, principal.principal_id))

        return self.chain.h.coordinator.request_publication(publication)

    def revoke_producer_consent(self, participant: str = CHILD_A) -> bool:
        return self.chain.h.publish_owner_change(
            lambda: self.chain.h.owner.update_member(participant, consent_effective=False))

    def quarantine(self, refs: tuple[str, ...]) -> bool:
        return self.chain.owner_quarantine(refs, "FIXTURE_OWNER_QUARANTINE")


def build_sketch_review_harness(**chain_options: Any) -> SketchReviewHarness:
    chain = build_sketch_chain_harness(**chain_options)
    coordinator, fences = chain.h.coordinator, chain.h.fences
    store = InMemorySketchReviewStore(fences)
    repository = CoordinatedSketchReviewRepository(store, coordinator, fences)
    tokens = CoordinatedReviewTokens(fences, coordinator)
    epochs = ReviewEligibilityEpochs(fences, coordinator)
    targets = SketchServiceReviewTargetReader(chain.service)
    artifacts = CoordinatedReviewArtifacts(chain.artifact_port)
    policy = FixtureReviewPolicy(fixture_review_policy())
    context = FakeReviewContext()
    context.set_session(ORG, SESSION, revision=REVIEW_CONTEXT_REVISION,
                        members=(CHILD_A, CHILD_B, CHILD_C))
    authority = FakeReviewAuthority()
    authority.teachers[TEACHER.principal_id] = (ORG, frozenset({CLASS}))
    authority.teachers[OTHER_CLASS_TEACHER.principal_id] = (ORG, frozenset({"class_fx_b"}))
    authority.teachers[OUTSIDER.principal_id] = (OUTSIDER.organization_id, frozenset({CLASS}))
    authority.devices[DEVICE_A.principal_id] = DeviceBinding(ORG, SESSION, CHILD_A)
    authority.devices[DEVICE_GA.principal_id] = DeviceBinding(ORG, SESSION, CHILD_A)
    authority.devices[DEVICE_GB.principal_id] = DeviceBinding(ORG, SESSION, CHILD_B)
    moderation = FixtureSketchModeration()
    service = SketchReviewService(SketchReviewDependencies(
        targets=targets, artifacts=artifacts, repository=repository, tokens=tokens,
        moderation=moderation, authority=authority, context=context, policy=policy,
        quarantine=artifacts, clock=chain.h.clock, ids=chain.h.ids,
    ))
    ticket = FakeTicketIssuer(service.eligibility)
    cache = FakeChildCache(service.child_payload, epochs.epoch, service.eligibility)
    dispatcher = FakeReadModelDispatcher(service.child_payload, (DEVICE_A, DEVICE_GB))
    return SketchReviewHarness(
        chain=chain, store=store, repository=repository, tokens=tokens, epochs=epochs,
        targets=targets, artifacts=artifacts, policy=policy, context=context,
        authority=authority, moderation=moderation, service=service, ticket=ticket,
        cache=cache, dispatcher=dispatcher,
    )


EXAMPLES_FIXTURE_ID = "FEAT-052-BE205-H-AI-REVIEW"


def build_sketch_review_examples() -> dict[str, object]:
    """Deterministic examples generated from a real 04 -> 05 run (fixture C04)."""

    h = build_sketch_review_harness()
    proposal_id = h.pending()
    h.moderate(proposal_id)
    pending_queue = h.service.queue_item(TEACHER, proposal_id)
    approved = h.review(proposal_id, "approve")
    child = h.service.child_payload(DEVICE_A, proposal_id)
    rejected_id = h.pending(level=LEVEL)  # a distinct A1 request (same level would be a cache hit)
    h.moderate(rejected_id)
    rejected = h.review(rejected_id, "reject")
    rejected_child = h.service.child_payload(DEVICE_A, rejected_id)
    return {
        "fixture_id": EXAMPLES_FIXTURE_ID,
        "synthetic_only": True,
        "contract_version": "0.1-candidate",
        "examples": {
            "queue_item_pending": pending_queue,
            "review_result_approve": dict(approved.data),
            "child_payload_approved": child,
            "review_result_reject": dict(rejected.data),
            "child_payload_rejected": rejected_child,
        },
    }


__all__ = [
    "EXAMPLES_FIXTURE_ID",
    "REVIEW_CONTEXT_REVISION",
    "SketchReviewHarness",
    "build_sketch_review_examples",
    "build_sketch_review_harness",
    "unsafe_text_outcome",
]
