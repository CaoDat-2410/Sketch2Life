"""C3a component fixtures only: NOT real BE1 authority/revocation fencing proof."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from typing import cast

import pytest

from sketch2life.application.learning_content_eligibility import ContentEligibility, audience_hash
from sketch2life.application.ports.learning_content import (
    ContentAccess,
    ContentBoundary,
    ContentPolicy,
    ContentStore,
    ContentTransaction,
    SourceAssessment,
)
from sketch2life.contracts.schemas.learning_content import ContentWrite
from sketch2life.domain.learning_content import model as domain
from sketch2life.domain.learning_content.model import (
    Authority,
    Capability,
    ContentError,
    ContentState,
    ContentVersion,
    ReviewProof,
)

NOW = datetime(2026, 10, 17, tzinfo=UTC)
AUTHOR = Authority("author", "school", frozenset(Capability))
REVIEWER = Authority("reviewer", "school", frozenset(Capability))
BODY = ContentWrite.model_validate_json('''{
 "content_kind":"knowledge","title":"Butterfly","asset_refs":[],
 "source_refs":[{"ref":"source","version":1,"hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}],
 "age_eligibility":{"age_policy_ref":"ages-v1","min_months":36,"max_months":72},
 "purpose_codes":["teaching"],"editorial_note":"","content_policy_ref":"content-v1"
}''')


def published() -> ContentVersion:
    item = domain.create("record", AUTHOR, BODY.model_dump(mode="json"), NOW)
    item = domain.submit(item, AUTHOR, expected_revision=item.revision)
    for dimension in ("safety", "pedagogical"):
        proof = ReviewProof(
            dimension, dimension, "approve", item.record_id, item.version, item.hash,
            item.context_revision, audience_hash(BODY), "reviewer", "policy-v1",
            item.review_revision + 1)
        item = domain.record_review(item, REVIEWER, proof, expected_revision=item.revision,
                                    expected_review_revision=item.review_revision)
    return domain.publish(item, REVIEWER, expected_revision=item.revision,
                          safety_review_id="safety", pedagogical_review_id="pedagogical",
                          policy_version="policy-v1", audience_hash=audience_hash(BODY))


class FixtureAccess:
    def __init__(self) -> None:
        self.authority = Authority("consumer", "school", frozenset({Capability.READ}))
        self.policy = ContentPolicy("policy-v1", "content-v1", "ages-v1",
                                    frozenset({"knowledge"}), frozenset({"teaching"}))
        self.classification = "generic_authored"
        self.usage_allowed = True
        self.moderation_passed = True
        self.effective = True
        self.assessment_hash: str | None = None
        self.assessed = 0

    def assess_sources(self, content: ContentVersion) -> SourceAssessment:
        self.assessed += 1
        return SourceAssessment(
            content.organization_id, content.record_id, content.version,
            self.assessment_hash or content.hash,
            self.policy.version, self.classification, self.usage_allowed, self.moderation_passed)

    def review_effective(self, content: ContentVersion, proof: ReviewProof) -> bool:
        return self.effective


class FixtureBoundary:
    def __init__(self, access: FixtureAccess) -> None:
        self.access = access
        self.held = False
        self.order: list[str] = []

    @contextmanager
    def guard(self, principal_id: str, organization_id: str) -> Iterator[ContentAccess]:
        self.held = True
        self.order.append("guard-enter")
        try:
            yield self.access
        finally:
            self.order.append("guard-exit")
            self.held = False


class FixtureStore:
    """Read-only transaction spy; casting is local to explicitly incomplete fixtures."""

    def __init__(self, boundary: FixtureBoundary) -> None:
        self.boundary = boundary
        self.items = [published()]
        self.requested_versions: list[int | None] = []

    @contextmanager
    def transaction(self) -> Iterator[ContentTransaction]:
        assert self.boundary.held
        self.boundary.order.append("transaction-enter")
        try:
            yield cast(ContentTransaction, self)
        except Exception:
            assert self.boundary.held
            self.boundary.order.append("transaction-rollback")
            raise
        else:
            assert self.boundary.held
            self.boundary.order.append("transaction-commit")

    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> ContentVersion | None:
        self.requested_versions.append(version)
        return next((item for item in self.items if item.version == version), None)

    def published_versions(self, organization_id: str,
                           record_id: str) -> tuple[ContentVersion, ...]:
        return tuple(item for item in self.items if item.state == ContentState.PUBLISHED)


@pytest.fixture
def harness() -> tuple[ContentEligibility, FixtureAccess, FixtureStore, FixtureBoundary]:
    access = FixtureAccess()
    boundary = FixtureBoundary(access)
    store = FixtureStore(boundary)
    service = ContentEligibility(cast(ContentStore, store), cast(ContentBoundary, boundary))
    return service, access, store, boundary


def resolve(service: ContentEligibility, *, version: int | None = None):
    return service.resolve("consumer", "school", "record", age_months=48,
                           purpose_code="teaching", version=version)


def test_published_resolution_keeps_guard_through_commit(harness) -> None:
    service, access, store, boundary = harness
    result = resolve(service)
    assert result.version == 1 and result.hash == store.items[0].hash
    assert result.publication_review_ids == ("safety", "pedagogical")
    assert access.assessed == 1
    assert boundary.order == ["guard-enter", "transaction-enter",
                              "transaction-commit", "guard-exit"]


def test_draft_does_not_hide_published_version(harness) -> None:
    service, _, store, _ = harness
    store.items.append(domain.edit(store.items[0], AUTHOR, BODY.model_dump(mode="json"), NOW,
                                    expected_revision=store.items[0].revision, next_version=2))
    assert resolve(service).version == 1
    with pytest.raises(ContentError, match="CONTENT_NOT_PUBLISHED"):
        resolve(service, version=2)
    assert store.requested_versions == [2]


@pytest.mark.parametrize("state", [ContentState.RECALLED, ContentState.ARCHIVED,
                                   ContentState.DRAFT, ContentState.SUBMITTED])
def test_nonpublished_never_resolved_even_by_exact_version(harness, state) -> None:
    service, _, store, _ = harness
    store.items[0] = replace(store.items[0], state=state)
    with pytest.raises(ContentError, match="CONTENT_NOT_ELIGIBLE"):
        resolve(service)
    with pytest.raises(ContentError, match="CONTENT_NOT_PUBLISHED"):
        resolve(service, version=1)


@pytest.mark.parametrize("change,code", [
    ("revoked_authority", "CONTENT_FORBIDDEN"),
    ("wrong_principal", "CONTENT_INVALID_AUTHORITY"),
    ("wrong_school", "CONTENT_INVALID_AUTHORITY"),
    ("policy", "CONTENT_POLICY_DENIED"),
    ("age_policy", "CONTENT_POLICY_DENIED"),
    ("kind", "CONTENT_POLICY_DENIED"),
    ("purposes", "CONTENT_POLICY_DENIED"),
    ("child", "CONTENT_SOURCE_AUTHORITY_REQUIRED"),
    ("unknown_source", "CONTENT_SOURCE_AUTHORITY_REQUIRED"),
    ("rights", "CONTENT_SOURCE_DENIED"),
    ("moderation", "CONTENT_SOURCE_DENIED"),
    ("assessment_hash", "CONTENT_SOURCE_MISMATCH"),
    ("review_revoked", "CONTENT_REVIEW_INEFFECTIVE"),
    ("new_review_policy", "CONTENT_REVIEW_REQUIRED"),
])
def test_current_guards_deny_after_prior_success(harness, change, code) -> None:
    service, access, _, boundary = harness
    resolve(service)
    if change == "revoked_authority":
        access.authority = replace(access.authority, capabilities=frozenset())
    elif change == "wrong_principal":
        access.authority = replace(access.authority, principal_id="other")
    elif change == "wrong_school":
        access.authority = replace(access.authority, organization_id="other")
    elif change == "policy":
        access.policy = replace(access.policy, content_policy_ref="new")
    elif change == "age_policy":
        access.policy = replace(access.policy, age_policy_ref="new")
    elif change == "kind":
        access.policy = replace(access.policy, content_kinds=frozenset())
    elif change == "purposes":
        access.policy = replace(access.policy, purpose_codes=frozenset())
    elif change in {"child", "unknown_source"}:
        access.classification = "child_derived" if change == "child" else "unknown"
    elif change == "rights":
        access.usage_allowed = False
    elif change == "moderation":
        access.moderation_passed = False
    elif change == "assessment_hash":
        access.assessment_hash = "b" * 64
    elif change == "review_revoked":
        access.effective = False
    elif change == "new_review_policy":
        access.policy = replace(access.policy, version="policy-v2")
    with pytest.raises(ContentError, match=code):
        resolve(service)
    assert not boundary.held


@pytest.mark.parametrize("field,value,code", [
    ("hash", "b" * 64, "CONTENT_HASH_MISMATCH"),
    ("organization_id", "other", "CONTENT_STORAGE_SCOPE_MISMATCH"),
    ("record_id", "other", "CONTENT_STORAGE_SCOPE_MISMATCH"),
    ("publication_review_ids", (), "CONTENT_REVIEW_REQUIRED"),
    ("publication_review_ids", ("pedagogical", "safety"), "CONTENT_REVIEW_REQUIRED"),
])
def test_corrupt_storage_does_not_bypass_proof(harness, field, value, code) -> None:
    service, _, store, _ = harness
    store.items[0] = replace(store.items[0], **{field: value})
    with pytest.raises(ContentError, match=code):
        resolve(service)


def test_exact_missing_version_or_wrong_hash_never_falls_back(harness) -> None:
    service, _, _, _ = harness
    with pytest.raises(ContentError, match="CONTENT_NOT_ELIGIBLE"):
        resolve(service, version=9)
    with pytest.raises(ContentError, match="CONTENT_HASH_MISMATCH"):
        service.resolve("consumer", "school", "record", age_months=48,
                        purpose_code="teaching", version=1, expected_hash="b" * 64)


@pytest.mark.parametrize("age,purpose", [(35, "teaching"), (73, "teaching"), (48, "other")])
def test_requested_audience_must_fit(harness, age, purpose) -> None:
    service, _, _, _ = harness
    with pytest.raises(ContentError, match="CONTENT_AUDIENCE_DENIED"):
        service.resolve("consumer", "school", "record", age_months=age,
                        purpose_code=purpose, version=1)


@pytest.mark.parametrize("age,version", [(True, 1), (-1, 1), (48, True), (48, 0)])
def test_invalid_query_rejected_before_dependency_access(harness, age, version) -> None:
    service, access, _, boundary = harness
    with pytest.raises(ContentError, match="CONTENT_INVALID_QUERY"):
        service.resolve("consumer", "school", "record", age_months=age,
                        purpose_code="teaching", version=version)
    assert access.assessed == 0 and boundary.order == []


@pytest.mark.parametrize("field,value", [
    ("target_version", 2), ("target_hash", "b" * 64), ("context_revision", 9),
    ("audience_hash", "b" * 64), ("policy_version", "old-policy"),
    ("reviewer_id", "author"), ("decision", "reject"), ("state", "revoked"),
])
def test_snapshot_review_proof_must_also_remain_exact(harness, field, value) -> None:
    service, _, store, _ = harness
    item = store.items[0]
    bad = replace(item.reviews[0], **{field: value})
    store.items[0] = replace(item, reviews=(bad, item.reviews[1]))
    with pytest.raises(ContentError, match="CONTENT_REVIEW_MISMATCH"):
        resolve(service)


def test_default_sorts_published_versions_newest_first(harness) -> None:
    service, _, store, _ = harness
    old = store.items[0]
    newer = replace(old, version=2,
                    reviews=tuple(replace(p, target_version=2) for p in old.reviews))
    store.items.append(newer)
    assert resolve(service).version == 2


def test_hash_without_explicit_version_rejected_before_dependencies(harness) -> None:
    service, _, _, boundary = harness
    with pytest.raises(ContentError, match="CONTENT_INVALID_QUERY"):
        service.resolve("consumer", "school", "record", age_months=48,
                        purpose_code="teaching", expected_hash="a" * 64)
    assert boundary.order == []


def test_invalid_stored_body_produces_only_safe_code(harness) -> None:
    service, _, store, boundary = harness
    body = '{"unrecognized":"do-not-echo-this-content"}'
    store.items[0] = replace(store.items[0], body_json=body, hash=domain.content_hash(body))
    with pytest.raises(ContentError) as error:
        resolve(service)
    assert str(error.value) == "CONTENT_INVALID_STORED_PAYLOAD"
    assert error.value.__suppress_context__
    assert boundary.order[-2:] == ["transaction-rollback", "guard-exit"]
