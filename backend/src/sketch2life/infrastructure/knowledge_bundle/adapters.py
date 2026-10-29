"""Named, deny-by-default BE2-07 fixtures, sharing one publication/read boundary.

These synthetic facts do not implement a real Vision/BE1 authority adapter. No mutable
store escapes; publications capture their inputs before deferred execution.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from sketch2life.contracts.schemas.knowledge_bundles import (
    ExactKnowledgeRefV1,
    KnowledgeBundleExportV1,
    KnowledgeSupersededV1,
)
from sketch2life.domain.knowledge_bundle import (
    CLAIMS_MAX,
    FIXTURE_POLICY,
    SOURCES_MAX,
    AudienceContextV1,
    BasisRef,
    ContributorV1,
    KnowledgeBasisV1,
    KnowledgeRuleViolation,
    ReviewedClaimV1,
    ReviewedSourceV1,
    opaque,
    require,
)
from sketch2life.infrastructure.knowledge_bundle.coordination import KnowledgeCommitCoordinator


class FixtureKnowledgeFacts:
    def __init__(self, coordinator: KnowledgeCommitCoordinator) -> None:
        self._coordinator = coordinator
        self._bases: dict[tuple[str, str], KnowledgeBasisV1] = {}
        self._audiences: dict[tuple[str, str], AudienceContextV1] = {}
        self._sources: dict[str, ReviewedSourceV1] = {}
        self._claims: dict[str, ReviewedClaimV1] = {}
        self._teachers: dict[tuple[str, str, str], bool] = {}
        self._disclosures: dict[tuple[str, str, str], bool] = {}
        self._consents: dict[tuple[str, str, ContributorV1], tuple[bool, bool]] = {}
        self._mutations: dict[tuple[str, str], bool] = {}
        self._policy: tuple[str, bool] = (FIXTURE_POLICY, False)
        self._consent_calls = 0

    @property
    def coordination_token(self) -> object:
        return self._coordinator

    @property
    def consent_calls(self) -> int:
        with self._coordinator.read():
            return self._consent_calls

    def basis(self, ref: BasisRef) -> KnowledgeBasisV1 | None:
        with self._coordinator.read():
            return deepcopy(self._bases.get((ref.kind, ref.ref)))

    def audience(self, organization_id: str, session_id: str) -> AudienceContextV1 | None:
        with self._coordinator.read():
            return deepcopy(self._audiences.get((organization_id, session_id)))

    def sources(self) -> tuple[ReviewedSourceV1, ...]:
        with self._coordinator.read():
            return deepcopy(tuple(self._sources[key] for key in sorted(self._sources)))

    def catalog_claims(self) -> tuple[ReviewedClaimV1, ...]:
        with self._coordinator.read():
            return deepcopy(tuple(self._claims[key] for key in sorted(self._claims)))

    def teacher_allowed(self, organization_id: str, principal_id: str, session_id: str) -> bool:
        with self._coordinator.read():
            return self._teachers.get((organization_id, session_id, principal_id), False)

    def disclosure_allowed(self, organization_id: str, principal_id: str, session_id: str) -> bool:
        with self._coordinator.read():
            return self._disclosures.get((organization_id, session_id, principal_id), False)

    def contributor_allowed(
        self, organization_id: str, session_id: str, contributor: ContributorV1
    ) -> bool:
        with self._coordinator.read():
            self._consent_calls += 1
            return self._consents.get((organization_id, session_id, contributor), (False, False))[0]

    def contributor_disclosure_allowed(
        self, organization_id: str, session_id: str, contributor: ContributorV1
    ) -> bool:
        with self._coordinator.read():
            return self._consents.get((organization_id, session_id, contributor), (False, False))[1]

    def policy(self) -> tuple[str, bool]:
        with self._coordinator.read():
            return self._policy

    def mutation_allowed(self, organization_id: str, session_id: str) -> bool:
        with self._coordinator.read():
            return self._mutations.get((organization_id, session_id), False)

    def publish_basis(self, basis: KnowledgeBasisV1) -> bool:
        captured = deepcopy(basis)
        return self._coordinator.publish(
            lambda: self._bases.__setitem__((captured.kind, captured.ref), captured)
        )

    def publish_audience(self, audience: AudienceContextV1) -> bool:
        captured = deepcopy(audience)
        return self._coordinator.publish(
            lambda: self._audiences.__setitem__(
                (captured.organization_id, captured.session_id), captured
            )
        )

    def publish_source(self, source: ReviewedSourceV1) -> bool:
        captured = deepcopy(source)

        def apply() -> None:
            require(
                captured.ref.source_id in self._sources or len(self._sources) < SOURCES_MAX,
                "COLLECTION_BOUNDS",
            )
            self._sources[captured.ref.source_id] = captured

        return self._coordinator.publish(apply)

    def publish_catalog_claim(self, claim: ReviewedClaimV1) -> bool:
        captured = deepcopy(claim)

        def apply() -> None:
            require(
                captured.claim_id in self._claims or len(self._claims) < CLAIMS_MAX,
                "COLLECTION_BOUNDS",
            )
            self._claims[captured.claim_id] = captured

        return self._coordinator.publish(apply)

    @staticmethod
    def _scope(organization_id: str, session_id: str) -> None:
        opaque(organization_id)
        opaque(session_id)

    @staticmethod
    def _decision(allowed: bool) -> None:
        require(type(allowed) is bool, "INVALID_STATE")

    def publish_teacher(
        self,
        organization_id: str,
        session_id: str,
        principal_id: str,
        allowed: bool,
        disclose: bool = True,
    ) -> bool:
        self._scope(organization_id, session_id)
        opaque(principal_id)
        self._decision(allowed)
        self._decision(disclose)
        key = (organization_id, session_id, principal_id)

        def apply() -> None:
            self._teachers[key] = allowed
            self._disclosures[key] = disclose

        return self._coordinator.publish(apply)

    def publish_disclosure(
        self,
        organization_id: str,
        session_id: str,
        principal_id: str,
        allowed: bool,
    ) -> bool:
        self._scope(organization_id, session_id)
        opaque(principal_id)
        self._decision(allowed)
        return self._coordinator.publish(
            lambda: self._disclosures.__setitem__(
                (organization_id, session_id, principal_id), allowed
            )
        )

    def publish_consent(
        self,
        organization_id: str,
        session_id: str,
        contributor: ContributorV1,
        allowed: bool,
        disclose: bool = True,
    ) -> bool:
        self._scope(organization_id, session_id)
        self._decision(allowed)
        self._decision(disclose)
        captured = deepcopy(contributor)
        return self._coordinator.publish(
            lambda: self._consents.__setitem__(
                (organization_id, session_id, captured), (allowed, disclose)
            )
        )

    def publish_policy(self, ref: str, active: bool = True) -> bool:
        opaque(ref)
        self._decision(active)

        def apply() -> None:
            self._policy = (ref, active)

        return self._coordinator.publish(apply)

    def publish_mutation(self, organization_id: str, session_id: str, allowed: bool) -> bool:
        self._scope(organization_id, session_id)
        self._decision(allowed)
        return self._coordinator.publish(
            lambda: self._mutations.__setitem__((organization_id, session_id), allowed)
        )


class RecordingKnowledgeConsumer:
    """Exact-event projection only; this fixture provides no consumer held lease/fence."""

    def __init__(self) -> None:
        self._registered: set[tuple[str, str, str, int, str]] = set()
        self._invalidated: set[tuple[str, str, str, int, str]] = set()
        self._seen: dict[str, str] = {}

    @staticmethod
    def _key(
        organization_id: str,
        session_id: str,
        ref: ExactKnowledgeRefV1,
    ) -> tuple[str, str, str, int, str]:
        opaque(organization_id)
        opaque(session_id)
        return organization_id, session_id, ref.bundle_id, ref.bundle_version, ref.bundle_hash

    def register(self, organization_id: str, session_id: str, ref: ExactKnowledgeRefV1) -> None:
        self._registered.add(self._key(organization_id, session_id, ref))

    def apply(self, event: KnowledgeSupersededV1) -> bool:
        serialized = event.model_dump_json()
        previous = self._seen.get(event.event_id)
        if previous is not None:
            require(previous == serialized, "EVENT_IDENTITY_MISMATCH")
            return False
        self._seen[event.event_id] = serialized
        # Preserve a received invalidation even if registration happens later.
        self._invalidated.add(self._key(event.organization_id, event.session_id, event.old_bundle))
        return True

    def is_current(self, organization_id: str, session_id: str, ref: ExactKnowledgeRefV1) -> bool:
        key = self._key(organization_id, session_id, ref)
        return key in self._registered and key not in self._invalidated


def _fixture_video_ref(name: str) -> dict[str, str | int]:
    return {
        "ref": "fixture-video-" + name,
        "version": 1,
        "hash": hashlib.sha256(("knowledge-video-fixture-v1:" + name).encode()).hexdigest(),
    }


def candidate_video_pin_material(export: KnowledgeBundleExportV1) -> dict[str, object]:
    """Pinned08 material with explicitly synthetic consumer-owned policy/profile refs.

    This is a conformance fixture for the reviewed-library strategy. It cannot supply
    actual08 policy adoption or a held producer validity boundary across consumer commit.
    """
    require(export.readiness == "generation_ready", "KNOWLEDGE_NOT_READY")
    return {
        "schema": "BE2-08.VideoPin/0.1-candidate",
        "organization_id": export.organization_id,
        "session_id": export.session_id,
        "bundle": {
            "ref": export.bundle_id,
            "version": export.bundle_version,
            "hash": export.bundle_hash,
        },
        "editorial_revision": export.editorial_revision,
        "context_revision": export.context_revision,
        "audience_revision": export.audience_revision,
        "sources": [
            {"ref": source.ref.source_id, "version": source.ref.revision, "hash": source.ref.sha256}
            for source in sorted(
                export.source_records,
                key=lambda item: (item.ref.source_id, item.ref.revision, item.ref.sha256),
            )
        ],
        "strategy": "reviewed_library",
        "policy_epoch": 1,
        "content_profile": _fixture_video_ref("content-profile"),
        "encoding": _fixture_video_ref("encoding"),
        "rights": _fixture_video_ref("rights"),
        "retry_policy": _fixture_video_ref("retry-policy"),
        "policy": _fixture_video_ref("policy"),
        "model_profile": None,
        "library_asset": _fixture_video_ref("library-asset"),
    }


def _consumer_canonical_digest(document: object) -> str:
    # Match the pinned08 native JSON algorithm, which deliberately does not NFC-normalize.
    try:
        encoded = json.dumps(
            document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeError):
        raise KnowledgeRuleViolation("VIDEO_INVALID_CANONICAL_INPUT") from None
    return hashlib.sha256(encoded).hexdigest()


def candidate_video_pin_digest(export: KnowledgeBundleExportV1) -> str:
    return _consumer_canonical_digest(candidate_video_pin_material(export))
