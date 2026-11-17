"""Deterministic synthetic own07 composition. No provider, HTTP or real owner adapter."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.services.knowledge_bundle import (
    KnowledgeBundleService,
    KnowledgeDependencies,
)
from sketch2life.contracts.schemas.knowledge_bundles import (
    ConfirmedMeaningRefV1,
    CreateKnowledgeBundleV1,
    TeacherTopicRefV1,
)
from sketch2life.domain.knowledge_bundle import (
    FIXTURE_POLICY,
    AudienceContextV1,
    AudienceMemberV1,
    ContributorV1,
    ImaginedElementV1,
    KnowledgeBasisV1,
    ReviewedClaimV1,
    ReviewedSourceV1,
    SourceRefV1,
)
from sketch2life.infrastructure.knowledge_bundle.adapters import FixtureKnowledgeFacts
from sketch2life.infrastructure.knowledge_bundle.coordination import KnowledgeCommitCoordinator
from sketch2life.infrastructure.knowledge_bundle.fakes import InMemoryKnowledgeRepository

ORG = "org"
SESSION = "session"
TEACHER_A = Principal("teacher-a", ORG, PrincipalRole.TEACHER)
TEACHER_B = Principal("teacher-b", ORG, PrincipalRole.TEACHER)
FACT_TEXT = "Mèo là động vật có vú."
IMAGINED_TEXT = "Mèo có cánh."


@dataclass(frozen=True)
class KnowledgeFixtureClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 19, 0, 0, 0, tzinfo=UTC)


@dataclass(frozen=True)
class KnowledgeHarness:
    coordinator: KnowledgeCommitCoordinator
    repository: InMemoryKnowledgeRepository
    facts: FixtureKnowledgeFacts
    service: KnowledgeBundleService
    topic: KnowledgeBasisV1
    child_basis: KnowledgeBasisV1
    audience: AudienceContextV1
    source: ReviewedSourceV1
    claim: ReviewedClaimV1

    def create_body(
        self,
        *,
        child: bool = False,
        catalog_claim_ids: tuple[str, ...] | None = None,
        imagined_refs: tuple[str, ...] = (),
    ) -> CreateKnowledgeBundleV1:
        basis_ref = (
            ConfirmedMeaningRefV1(
                kind="confirmed_meaning",
                ref=self.child_basis.ref,
                revision=self.child_basis.revision,
            )
            if child
            else TeacherTopicRefV1(
                kind="teacher_topic", ref=self.topic.ref, revision=self.topic.revision
            )
        )
        return CreateKnowledgeBundleV1(
            session_id=SESSION,
            basis_ref=basis_ref,
            expected_context_revision=self.audience.context_revision,
            expected_audience_revision=self.audience.audience_revision,
            catalog_claim_ids=(self.claim.claim_id,)
            if catalog_claim_ids is None
            else catalog_claim_ids,
            imagined_refs=imagined_refs,
        )


def build_knowledge_harness() -> KnowledgeHarness:
    coordinator = KnowledgeCommitCoordinator()
    repository = InMemoryKnowledgeRepository(coordinator)
    facts = FixtureKnowledgeFacts(coordinator)
    topic = KnowledgeBasisV1("topic-cats", "teacher_topic", 1, ORG, SESSION, "Mèo")
    audience = AudienceContextV1(
        "audience-cats",
        ORG,
        SESSION,
        0,
        2,
        (
            AudienceMemberV1("child-a", "age-4"),
            AudienceMemberV1("child-b", "age-8"),
        ),
    )
    contributors = (
        ContributorV1("child-a", "knowledge_media", "snapshot-a"),
        ContributorV1("child-b", "knowledge_media", "snapshot-b"),
    )
    child_basis = KnowledgeBasisV1(
        "meaning-cats",
        "confirmed_meaning",
        1,
        ORG,
        SESSION,
        "Mèo",
        ("snapshot-a", "snapshot-b"),
        contributors,
        (ImaginedElementV1("cat-wings", 1, IMAGINED_TEXT),),
        confirmation_ref="teacher-confirmation-1",
    )
    source = ReviewedSourceV1(
        SourceRefV1(
            "source-cats", 1, hashlib.sha256(b"synthetic-reviewed-cat-source-v1").hexdigest()
        ),
        "Synthetic reviewed cat source",
        "fixture:reviewed-cats-v1",
        "2026-10-19",
        "Mèo",
        ("age-4", "age-8"),
    )
    claim = ReviewedClaimV1("cats-mammal", 1, FACT_TEXT, (source.ref,))
    facts.publish_basis(topic)
    facts.publish_basis(child_basis)
    facts.publish_audience(audience)
    facts.publish_source(source)
    facts.publish_catalog_claim(claim)
    facts.publish_teacher(ORG, SESSION, TEACHER_A.principal_id, True)
    facts.publish_teacher(ORG, SESSION, TEACHER_B.principal_id, True)
    for contributor in contributors:
        facts.publish_consent(ORG, SESSION, contributor, True)
    facts.publish_policy(FIXTURE_POLICY, True)
    facts.publish_mutation(ORG, SESSION, True)
    service = KnowledgeBundleService(
        KnowledgeDependencies(repository, facts, KnowledgeFixtureClock())
    )
    return KnowledgeHarness(
        coordinator, repository, facts, service, topic, child_basis, audience, source, claim
    )
