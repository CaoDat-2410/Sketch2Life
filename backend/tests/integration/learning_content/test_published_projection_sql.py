"""C3a PostgreSQL projection regression, separate from frozen C2's 9-case pack."""

from __future__ import annotations

from datetime import UTC, datetime

from sketch2life.application.ports.learning_content import ContentEvent
from sketch2life.domain.learning_content import model as domain
from sketch2life.domain.learning_content.model import Authority, Capability, ReviewProof
from sketch2life.infrastructure.learning_content.sql import SqlContentStore
from tests.integration.learning_content.test_content_sql import migrate

NOW = datetime(2026, 10, 17, tzinfo=UTC)
AUTHOR = Authority("author", "school", frozenset(Capability))
REVIEWER = Authority("reviewer", "school", frozenset(Capability))


def test_published_projection_survives_new_draft_and_removes_recalled_version(
    content_engine, monkeypatch,
) -> None:
    migrate(content_engine, monkeypatch)
    store = SqlContentStore(content_engine)
    content = domain.create("record", AUTHOR, {"title": "Butterfly"}, NOW)

    def save(item, expected):
        with store.transaction() as tx:
            tx.save(item, expected_revision=expected,
                    event=ContentEvent(f"event-{item.revision}", "changed", "author", NOW))

    save(content, None)
    prior = content.revision
    content = domain.submit(content, AUTHOR, expected_revision=prior)
    save(content, prior)
    for dimension in ("safety", "pedagogical"):
        prior = content.revision
        proof = ReviewProof(dimension, dimension, "approve", "record", 1, content.hash,
                            content.context_revision, "audience", "reviewer", "policy-v1",
                            content.review_revision + 1)
        content = domain.record_review(content, REVIEWER, proof, expected_revision=prior,
                                       expected_review_revision=content.review_revision)
        save(content, prior)
    prior = content.revision
    content = domain.publish(content, REVIEWER, expected_revision=prior,
                             safety_review_id="safety", pedagogical_review_id="pedagogical",
                             policy_version="policy-v1", audience_hash="audience")
    save(content, prior)
    draft = domain.edit(content, AUTHOR, {"title": "New draft"}, NOW,
                        expected_revision=content.revision, next_version=2)
    save(draft, content.revision)
    with store.transaction() as tx:
        versions = tx.published_versions("school", "record")
        assert [(v.version, v.hash) for v in versions] == [(1, content.hash)]
        assert versions[0].revision == draft.revision
        assert tx.published_versions("other-school", "record") == ()
        assert tx.published_versions("school", "missing") == ()
    with store.transaction() as tx:
        old = tx.load("school", "record", version=1, for_update=True)
        recalled = domain.retire(old, REVIEWER, NOW, expected_revision=old.revision,
                                 reason="source withdrawn")
        tx.save(recalled, expected_revision=old.revision,
                event=ContentEvent("recall", "recalled", "reviewer", NOW))
    with store.transaction() as tx:
        assert tx.published_versions("school", "record") == ()
        assert tx.load("school", "record").version == 2
        assert tx.load("school", "record", version=1).hash == content.hash
