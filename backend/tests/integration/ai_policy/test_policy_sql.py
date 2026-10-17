"""Actual PG17 tests prepared for opt-in execution; skips are NOT_RUN, not proof."""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier

import pytest
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import DBAPIError

from alembic import command
from sketch2life.application.ports.ai_policy import PolicyEvent, PolicyReceipt
from sketch2life.domain.ai_policy import model as policy
from sketch2life.infrastructure.ai_policy.sql import SqlPolicyStore
from sketch2life.infrastructure.ai_policy.tables import EVENT, OUTBOX, RECEIPT, REVIEW, VERSION
from tests.unit.test_ai_policy_domain import AUTHOR, NOW, REVIEWER, draft, proof

BACKEND = Path(__file__).resolve().parents[3]


@pytest.fixture
def harness(policy_engine, monkeypatch):
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL",
                       policy_engine.url.render_as_string(hide_password=False))
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "ai_policy@head")
    return SqlPolicyStore(policy_engine), config


def persist(store, record, action, expected):
    with store.transaction() as tx:
        tx.save(record, expected_revision=expected, event=PolicyEvent(
            "event-" + str(record.revision), "ai_policy." + action, "synthetic-actor", NOW))
    return record


def seed(store):
    return persist(store, draft(), "create", None)


def counts(store):
    with store.engine.connect() as connection:
        return tuple(connection.scalar(select(func.count()).select_from(table))
                     for table in (VERSION, REVIEW, RECEIPT, EVENT, OUTBOX))


def published(store):
    original = seed(store)
    record = persist(store, policy.submit(original, AUTHOR, expected_revision=1),
                     "submit_review", 1)
    for dimension in ("safety", "pedagogical"):
        previous = record.revision
        record = policy.record_review(record, REVIEWER, proof(record, dimension),
                                      expected_revision=previous,
                                      expected_review_revision=record.review_revision)
        persist(store, record, "record_review", previous)
    result = policy.publish(record, REVIEWER, expected_revision=record.revision,
                            safety_review_id=record.reviews[0].review_id,
                            pedagogical_review_id=record.reviews[1].review_id,
                            current_review_policy="fixture.governance")
    return persist(store, result, "publish", record.revision)


def test_module_upgrade_downgrade_isolated(harness):
    store, config = harness
    schemas = inspect(store.engine).get_schema_names()
    assert "ai_jobs" not in schemas and "learning_content" not in schemas
    assert len(inspect(store.engine).get_table_names(schema="ai_policy")) == 6
    command.downgrade(config, "ai_policy@base")
    assert "ai_policy" not in inspect(store.engine).get_schema_names()
    command.upgrade(config, "ai_policy@head")


def test_child_process_restart_reads_committed_policy_and_scoped_outbox(harness):
    store, _ = harness
    original = seed(store)
    environment = os.environ | {
        "AP_CHILD_DATABASE_URL": store.engine.url.render_as_string(hide_password=False)}
    child = subprocess.run([sys.executable, "-c", '''
import json, os
from sqlalchemy import create_engine, select, func
from sketch2life.infrastructure.ai_policy.sql import SqlPolicyStore
from sketch2life.infrastructure.ai_policy.tables import OUTBOX
engine = create_engine(os.environ["AP_CHILD_DATABASE_URL"], hide_parameters=True)
with SqlPolicyStore(engine).transaction() as tx:
    item = tx.load("school", "record")
    assert item is not None
    result = {"hash": item.hash, "revision": item.revision, "pid": os.getpid()}
with engine.connect() as connection:
    result["outbox"] = connection.scalar(select(func.count()).select_from(OUTBOX))
engine.dispose()
print(json.dumps(result))
'''], cwd=BACKEND, env=environment, capture_output=True, text=True, timeout=30, check=True)
    result = json.loads(child.stdout)
    assert result["pid"] != os.getpid()
    assert (result["hash"], result["revision"], result["outbox"]) == (original.hash, 1, 1)


def test_transaction_failure_rolls_back_lifecycle_receipt_event_outbox(harness):
    store, _ = harness
    with pytest.raises(PolicyErrorForTest), store.transaction() as tx:
        tx.save(draft(), expected_revision=None,
                event=PolicyEvent("event", "ai_policy.create", "author", NOW))
        tx.add_receipt(PolicyReceipt("school", "author", "key", "a" * 64, "{}"))
        raise PolicyErrorForTest
    assert counts(store) == (0, 0, 0, 0, 0)


class PolicyErrorForTest(Exception):
    """Synthetic crash before UoW commit, not a storage substitute."""


def test_concurrent_writers_have_one_record_cas_winner(harness):
    store, _ = harness
    record = seed(store)
    updated = policy.submit(record, AUTHOR, expected_revision=1)
    barrier = Barrier(2)

    def write(index):
        barrier.wait(timeout=10)
        try:
            with store.transaction() as tx:
                tx.save(updated, expected_revision=1, event=PolicyEvent(
                    "race-" + str(index), "ai_policy.submit_review", "author", NOW))
            return "committed"
        except policy.PolicyError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, (1, 2)))
    assert sorted(results) == ["AI_POLICY_STALE_REVISION", "committed"]
    assert counts(store) == (1, 0, 0, 2, 2)


def test_duplicate_receipt_rolls_back_second_command(harness):
    store, _ = harness
    record = seed(store)
    receipt = PolicyReceipt("school", "author", "same-key", "a" * 64, "{}")
    with store.transaction() as tx:
        tx.add_receipt(receipt)
    updated = policy.submit(record, AUTHOR, expected_revision=1)
    with (pytest.raises(policy.PolicyError, match="AI_POLICY_WRITE_CONFLICT"),
          store.transaction() as tx):
        tx.save(updated, expected_revision=1,
                event=PolicyEvent("submit", "ai_policy.submit_review", "author", NOW))
        tx.add_receipt(receipt)
    assert counts(store) == (1, 0, 1, 1, 1)
    with store.transaction() as tx:
        assert tx.load("school", "record").state == policy.State.DRAFT
        assert tx.receipt("school", "author", "same-key") == receipt
        assert tx.receipt("other", "author", "same-key") is None


@pytest.mark.parametrize("statement", [
    "UPDATE ai_policy.version SET body_json='{}'",
    "UPDATE ai_policy.version SET hash=repeat('b',64)",
    "UPDATE ai_policy.review SET proof='{}'::jsonb",
    "UPDATE ai_policy.event SET payload='{}'::jsonb",
    "UPDATE ai_policy.receipt SET result_json='{}'",
    "DELETE FROM ai_policy.version",
])
def test_raw_sql_cannot_rewrite_version_or_history(harness, statement):
    store, _ = harness
    record = published(store)
    with store.transaction() as tx:
        tx.add_receipt(PolicyReceipt("school", "author", "immutable", "a" * 64, '{"ok":true}'))
    with pytest.raises(DBAPIError), store.engine.begin() as connection:
        connection.execute(text(statement))
    with store.transaction() as tx:
        assert tx.load("school", "record") == record


def test_replacing_review_dimension_roundtrips_order_and_preserves_all_proofs(harness):
    store, _ = harness
    record = seed(store)
    record = persist(store, policy.submit(record, AUTHOR, expected_revision=1), "submit_review", 1)
    for dimension in ("safety", "pedagogical", "safety"):
        previous = record.revision
        record = policy.record_review(record, REVIEWER, proof(record, dimension),
                                      expected_revision=previous,
                                      expected_review_revision=record.review_revision)
        persist(store, record, "record_review", previous)
    with store.transaction() as tx:
        assert tx.load("school", "record") == record
        history = tx.review_history("school", "record", version=1, after_revision=0, limit=100)
    assert len(history) == 3 and [p.dimension for p in record.reviews] == ["pedagogical", "safety"]


def test_review_history_survives_resubmission(harness):
    store, _ = harness
    record = seed(store)
    record = persist(store, policy.submit(record, AUTHOR, expected_revision=1), "submit_review", 1)
    rejected = policy.record_review(record, REVIEWER,
                                    proof(record, decision="reject", reason="synthetic changes"),
                                    expected_revision=record.revision,
                                    expected_review_revision=record.review_revision)
    persist(store, rejected, "record_review", record.revision)
    resubmitted = policy.submit(rejected, AUTHOR, expected_revision=rejected.revision)
    persist(store, resubmitted, "submit_review", rejected.revision)
    with store.transaction() as tx:
        assert tx.load("school", "record").reviews == ()
        history = tx.review_history("school", "record", version=1, after_revision=0, limit=100)
        assert history == rejected.reviews
        assert tx.review_history("other", "record", version=1, after_revision=0, limit=100) == ()


def test_old_published_version_recall_does_not_replace_new_head(harness):
    store, _ = harness
    old = published(store)
    new = policy.edit(old, AUTHOR, {"synthetic": "new"}, NOW,
                       expected_revision=old.revision, next_version=2)
    persist(store, new, "edit", old.revision)
    with store.transaction() as tx:
        pinned = tx.load("school", "record", version=1, for_update=True)
        assert pinned.state == policy.State.PUBLISHED and pinned.revision == new.revision
        retired = policy.retire(pinned, REVIEWER, NOW, expected_revision=pinned.revision,
                                 archive=False, reason="synthetic disable")
        tx.save(retired, expected_revision=pinned.revision,
                event=PolicyEvent("recall-old", "ai_policy.recall", "operator", NOW))
    with store.transaction() as tx:
        assert tx.load("school", "record").version == 2
        assert tx.load("school", "record").state == policy.State.DRAFT
        assert tx.load("school", "record", version=1).state == policy.State.RECALLED
        assert tx.load("school", "record", version=99) is None
        assert tx.load("other-school", "record") is None
    assert counts(store) == (2, 2, 0, 7, 7)


def test_repository_rejects_rewritten_body_and_rolls_back(harness):
    store, _ = harness
    record = seed(store)
    updated = policy.submit(record, AUTHOR, expected_revision=1)
    bad = policy.create("record", AUTHOR, {"changed": True}, NOW)
    updated = replace(updated, body_json=bad.body_json, hash=bad.hash)
    with pytest.raises(policy.PolicyError, match="AI_POLICY_IMMUTABLE_VERSION"):
        persist(store, updated, "submit_review", 1)
    assert counts(store) == (1, 0, 0, 1, 1)
