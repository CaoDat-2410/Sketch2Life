"""BE2-05 race/replay/rollback acceptance (plan §4.6, §10.3) with deterministic handshakes.

The 05 final unit runs inside the shared ``AssistanceCommitCoordinator``. Handshakes use Events
with timeouts and the existing ``HookedOwnerFences.after_successful_hold`` seam; no sleeps.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest

from sketch2life.application.services.sketch_generation import (
    NoticeKind,
    OwnerNotice,
    ReviseLevelCommand,
)
from sketch2life.application.services.sketch_review import (
    DECISION_ROUNDS,
    ReviewResult,
    SketchReviewError,
)
from sketch2life.application.services.vision_analysis import CorrectionCommand
from sketch2life.domain.vision_analysis import analysis_etag
from sketch2life.infrastructure.ai_jobs.fakes import eligibility_fence_scope
from sketch2life.infrastructure.assistance.harness import CHILD_A, DEVICE_A, LEVEL, ORG, TEACHER
from sketch2life.infrastructure.sketch_review.coordination import sketch_review_fence_scope
from sketch2life.infrastructure.sketch_review.harness import (
    SketchReviewHarness,
    build_sketch_review_harness,
)

TIMEOUT = 5.0


@pytest.fixture
def h() -> SketchReviewHarness:
    return build_sketch_review_harness()


def _ready(h: SketchReviewHarness, **kwargs: Any) -> str:
    proposal_id = h.pending(**kwargs)
    h.moderate(proposal_id)
    return proposal_id


def _effective_approvals(h: SketchReviewHarness, proposal_id: str) -> list[str]:
    return [e.review_id for e in h.store.snapshot().entries.get(proposal_id, ())
            if str(e.decision) == "approve" and str(e.state) == "effective"]


def _wrap_moderation(h: SketchReviewHarness, before: Callable[[], object]) -> list[int]:
    """Run ``before`` once at plan step 3 (inside ``_prepare``, outside the unit)."""

    calls = [0]
    original = h.moderation.moderate

    def moderate(*args: Any) -> Any:
        calls[0] += 1
        if calls[0] == 1:
            before()
        return original(*args)

    h.moderation.moderate = moderate  # type: ignore[method-assign]
    return calls


def _count_tokens(h: SketchReviewHarness) -> list[int]:
    calls = [0]
    original = h.tokens.token

    def token(*args: Any) -> Any:
        calls[0] += 1
        return original(*args)

    h.tokens.token = token  # type: ignore[method-assign]
    return calls


def _stale_holds(h: SketchReviewHarness) -> int:
    return sum(1 for result in h.chain.h.fences.holds if not result.current)


def _post_hold_publication(h: SketchReviewHarness, publish: Callable[[], object],
                           log: list[str]) -> threading.Thread:
    """Hook after the successful 05 hold: another thread attempts an owner publication;
    the hook waits until that thread has called ``request_publication`` (it then blocks on
    the coordinator) before the 05 unit continues to its commit."""

    coordinator = h.chain.h.coordinator
    attempted = threading.Event()
    original = coordinator.request_publication
    worker_ident: list[int] = []

    def request_publication(publication: Callable[[], object]) -> bool:
        if worker_ident and threading.get_ident() == worker_ident[0]:
            log.append("publication_attempted")
            attempted.set()

            def tracked() -> object:
                result = publication()
                log.append("publication_applied")
                return result

            return original(tracked)
        return original(publication)

    coordinator.request_publication = request_publication  # type: ignore[method-assign]

    def run() -> None:
        worker_ident.append(threading.get_ident())  # recorded before any publication call
        publish()

    worker = threading.Thread(target=run, daemon=True)

    def before_commit() -> None:
        log.append("review_commit")

    def hook() -> None:
        assert coordinator.in_assistance()  # inside the 05 unit
        log.append("hold_ok")
        h.store.before_commit = before_commit  # armed here: the next commit is this unit's
        worker.start()
        assert attempted.wait(TIMEOUT), "publication thread never attempted"

    h.chain.h.fences.after_successful_hold = hook
    return worker


@pytest.mark.parametrize("publication", ["quarantine", "consent"])
def test_rv_r01_r02_publication_after_hold_waits_for_review_commit(
    h: SketchReviewHarness, publication: str,
) -> None:
    proposal_id = _ready(h)
    asset_ref = h.target(proposal_id).ref_set[0]
    etag = h.etag(proposal_id)
    log: list[str] = []
    publish: Callable[[], object] = (
        (lambda: h.quarantine((asset_ref,))) if publication == "quarantine"
        else h.revoke_producer_consent)
    worker = _post_hold_publication(h, publish, log)
    result = h.review(proposal_id, "approve", etag=etag)
    worker.join(TIMEOUT)
    assert not worker.is_alive()
    assert result.status == 201
    assert log == ["hold_ok", "publication_attempted", "review_commit", "publication_applied"]
    # After the owner publication, the approval is no longer usable (pull) and goes stale.
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    assert h.service.refresh(proposal_id, ORG) == (result.data["record"]["review_id"],)


def test_rv_r03_sketch_policy_change_before_hold_restarts(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    snapshot = h.chain.policy.snapshot
    assert snapshot is not None
    _wrap_moderation(h, lambda: h.chain.publish_policy(replace(snapshot, enabled=False)))
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve", etag=etag)
    assert _stale_holds(h) == 1  # the final hold saw the moved sketch-policy epoch
    assert raised.value.code == "STALE_AGGREGATE"  # round 2: producer review_revision moved
    assert h.target(proposal_id).status_reason == "POLICY_CHANGED"
    assert not _effective_approvals(h, proposal_id)


def test_rv_r04_vision_write_before_hold_restarts(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    analysis_id = h.target(proposal_id).analysis_id

    def confirm() -> None:
        head = h.chain.h.vision_store.snapshot().heads[analysis_id]
        h.chain.h.vision.submit_correction(CorrectionCommand(
            principal=TEACHER, analysis_id=analysis_id, idempotency_key="key_fx_r04",
            if_match=analysis_etag(analysis_id, head.analysis_revision),
            intended_objects=("tiger",), correction_reason="Teacher confirmed meaning",
            expected_context_revision=head.context_revision))

    _wrap_moderation(h, confirm)
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve", etag=etag)
    assert _stale_holds(h) == 1  # the analysis epoch moved: never committed on the old token
    assert raised.value.code == "STALE_AGGREGATE"
    assert h.target(proposal_id).status_reason == "MEANING_CHANGED"
    assert not _effective_approvals(h, proposal_id)


def test_rv_r05_result_document_quarantine_before_hold_restarts(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    target = h.target(proposal_id)
    assert target.result_document is not None
    etag = h.etag(proposal_id)
    _wrap_moderation(h, lambda: h.quarantine((target.result_document.artifact_ref,)))  # type: ignore[union-attr]
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve", etag=etag)
    assert _stale_holds(h) == 1  # the final hold saw artifact:{result_document}
    assert raised.value.code == "STALE_AGGREGATE"
    assert h.target(proposal_id).status_reason == "ARTIFACT_QUARANTINED"
    assert not _effective_approvals(h, proposal_id)


def test_rv_r06_05_policy_change_before_hold_decides_on_new_policy(
    h: SketchReviewHarness,
) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    assert h.policy.snapshot is not None
    new_policy = replace(h.policy.snapshot, version="2")
    _wrap_moderation(h, lambda: h.publish_review_policy(new_policy))
    tokens = _count_tokens(h)
    result = h.review(proposal_id, "approve", etag=etag)
    assert tokens[0] == 2 and result.status == 201
    entry = h.store.snapshot().entries[proposal_id][0]
    assert entry.policy_version.startswith("fixture.sketch_review.v0@2")


def test_rv_r06b_grant_revoked_before_hold(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    _wrap_moderation(h, lambda: h.publish_grant_change(
        TEACHER, lambda: h.authority.teachers.pop(TEACHER.principal_id)))
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve", etag=etag)
    assert raised.value.code == "RESOURCE_NOT_FOUND"
    assert not _effective_approvals(h, proposal_id)


def test_rv_r07_every_04_mutation_of_pending_bumps_eligibility() -> None:
    def epoch(h: SketchReviewHarness) -> int:
        return h.chain.h.fences.epochs[eligibility_fence_scope(ORG)]

    # (a) public revalidation after an unbumped owner fact change
    a = build_sketch_review_harness()
    a_id = a.pending()
    before = epoch(a)
    a.chain.h.owner.update_member(CHILD_A, consent_effective=False)
    assert a.target(a_id).pipeline_state == "stale" and epoch(a) > before
    # (b) owner notice
    b = build_sketch_review_harness()
    b_id = b.pending()
    before = epoch(b)
    b.chain.service.apply_owner_notice(OwnerNotice("notice_fx_r07", ORG,
                                                   NoticeKind.CONSENT_REVOKED,
                                                   participant_id=CHILD_A))
    assert b.target(b_id).pipeline_state == "stale" and epoch(b) > before
    # (c) support-level revision
    c = build_sketch_review_harness()
    c_id = c.pending()
    before = epoch(c)
    c.chain.service.revise_level(ReviseLevelCommand(TEACHER, c_id, "key_fx_r07c",
                                                    c.chain.proposal(c_id).etag(), LEVEL))
    assert epoch(c) > before


def test_rv_r08_identity_change_between_snapshot_and_read(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    original = h.targets.read
    calls = [0]

    def read(pid: str) -> Any:
        calls[0] += 1
        if calls[0] == 2:  # after the step-1 snapshot and token: producer revises the level
            h.chain.service.revise_level(ReviseLevelCommand(
                TEACHER, pid, "key_fx_r08", h.chain.proposal(pid).etag(), LEVEL))
        return original(pid)

    h.targets.read = read  # type: ignore[method-assign]
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve", etag=etag)
    assert raised.value.code in {"INVALID_STATE", "STALE_AGGREGATE"}
    assert not h.store.snapshot().entries


def test_rv_r09_same_thread_publication_is_deferred_to_unit_exit(
    h: SketchReviewHarness,
) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    assert h.policy.snapshot is not None
    new_policy = replace(h.policy.snapshot, version="2")
    observed: list[object] = []

    def before_commit() -> None:
        observed.append(h.policy.snapshot)

    def hook() -> None:
        observed.append(h.publish_review_policy(new_policy))  # same thread, inside unit
        observed.append(h.policy.snapshot)
        h.store.before_commit = before_commit

    h.chain.h.fences.after_successful_hold = hook
    result = h.review(proposal_id, "approve", etag=etag)
    assert result.status == 201
    assert observed[0] is False  # deferred, not run inside the unit
    assert observed[1] is not new_policy and observed[2] is not new_policy
    assert h.policy.snapshot is new_policy  # ran after the unit exited
    assert h.service.refresh(proposal_id, ORG) == (result.data["record"]["review_id"],)


def test_rv_r10_rollback_bumps_nothing_and_deferred_still_runs(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    assert h.policy.snapshot is not None
    new_policy = replace(h.policy.snapshot, version="2")
    scope = sketch_review_fence_scope(ORG, proposal_id)
    epoch_before = h.chain.h.fences.epochs[scope]
    state_before = h.store.snapshot()
    def hook() -> None:
        h.publish_review_policy(new_policy)  # same thread, deferred
        h.store.fail_next_commit = True  # armed inside the unit: this unit's commit fails

    h.chain.h.fences.after_successful_hold = hook
    with pytest.raises(RuntimeError, match="injected sketch review commit failure"):
        h.review(proposal_id, "approve", etag=etag)
    assert not h.store.snapshot().entries
    after = h.store.snapshot()
    assert (after.receipts, after.heads, after.audit) == (
        state_before.receipts, state_before.heads, state_before.audit)
    assert h.chain.h.fences.epochs[scope] == epoch_before
    assert h.policy.snapshot is new_policy  # deferred publication ran after rollback


def test_rv_r11_exception_releases_the_coordinator(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    h.chain.h.fences.after_successful_hold = lambda: setattr(h.store, "fail_next_commit", True)
    with pytest.raises(RuntimeError, match="injected sketch review commit failure"):
        h.review(proposal_id, "approve", etag=etag, key="key_fx_r11")
    assert not h.store.snapshot().entries
    acquired = threading.Event()

    def other() -> None:
        with h.chain.h.coordinator.assistance():
            acquired.set()

    thread = threading.Thread(target=other, daemon=True)
    thread.start()
    assert acquired.wait(TIMEOUT)
    thread.join(TIMEOUT)
    assert h.review(proposal_id, "approve", etag=etag, key="key_fx_r11").status == 201


def _race(h: SketchReviewHarness, proposal_id: str,
          commands: list[tuple[str, str]], etag: str) -> list[ReviewResult | SketchReviewError]:
    """Run commands in threads that all pass plan step 3 before any enters the unit."""

    barrier = threading.Barrier(len(commands), timeout=TIMEOUT)
    original = h.moderation.moderate

    def moderate(*args: Any) -> Any:
        verdict = original(*args)
        barrier.wait()
        return verdict

    h.moderation.moderate = moderate  # type: ignore[method-assign]
    results: list[ReviewResult | SketchReviewError] = [None] * len(commands)  # type: ignore[list-item]

    def run(index: int, decision: str, key: str) -> None:
        try:
            results[index] = h.review(proposal_id, decision, etag=etag, key=key)
        except SketchReviewError as exc:
            results[index] = exc

    threads = [threading.Thread(target=run, args=(i, d, k), daemon=True)
               for i, (d, k) in enumerate(commands)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(TIMEOUT)
    h.moderation.moderate = original  # type: ignore[method-assign]
    return results


def test_rv_r12_same_etag_race_and_fresh_retry_d2(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    results = _race(h, proposal_id, [("approve", "key_fx_r12a"), ("reject", "key_fx_r12r")],
                    etag)
    wins = [r for r in results if isinstance(r, ReviewResult)]
    losses = [r for r in results if isinstance(r, SketchReviewError)]
    assert len(wins) == 1 and len(losses) == 1 and losses[0].code == "STALE_AGGREGATE"
    if wins[0].data["decision"] == "approve":
        # the original reject lost; a successful reject needs a fresh ETag and a new key
        retry = h.review(proposal_id, "reject", key="key_fx_r12r_retry")
        assert retry.status == 201
        assert not _effective_approvals(h, proposal_id)
        assert len(h.store.snapshot().markers) == 1
    else:
        with pytest.raises(SketchReviewError) as raised:
            h.review(proposal_id, "approve", key="key_fx_r12a_retry")
        assert raised.value.code == "INVALID_STATE"
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    with pytest.raises(SketchReviewError) as stale:  # the old ETag is never accepted again
        h.review(proposal_id, "reject", etag=etag, key="key_fx_r12_old")
    assert stale.value.code == "STALE_AGGREGATE"


def test_rv_r13_two_approvals_one_review(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    results = _race(h, proposal_id, [("approve", "key_fx_r13a"), ("approve", "key_fx_r13b")],
                    etag)
    assert sorted(type(r).__name__ for r in results) == ["ReviewResult", "SketchReviewError"]
    assert len(_effective_approvals(h, proposal_id)) == 1


def test_rv_r14_same_key_concurrently_commits_once(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    results = _race(h, proposal_id, [("approve", "key_fx_r14"), ("approve", "key_fx_r14")],
                    etag)
    assert all(isinstance(r, ReviewResult) for r in results)
    replayed = [r.replayed for r in results if isinstance(r, ReviewResult)]
    assert sorted(replayed) == [False, True]
    assert len(h.store.snapshot().entries[proposal_id]) == 1


def test_rv_r15_unstable_token_gives_up(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    etag = h.etag(proposal_id)
    original = h.moderation.moderate

    def moderate(*args: Any) -> Any:
        h.chain.h.fences.bump(eligibility_fence_scope(ORG))
        return original(*args)

    h.moderation.moderate = moderate  # type: ignore[method-assign]
    tokens = _count_tokens(h)
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve", etag=etag)
    assert raised.value.code == "DEPENDENCY_UNAVAILABLE"
    assert tokens[0] == DECISION_ROUNDS
    assert not h.store.snapshot().entries


def test_rv_r16_duplicate_notice_is_idempotent(h: SketchReviewHarness) -> None:
    proposal_id = _ready(h)
    result = h.review(proposal_id, "approve")
    h.revoke_producer_consent()
    first = h.service.apply_target_notice("notice_fx_r16", ORG, proposal_id)
    assert first == (result.data["record"]["review_id"],)
    intents = len(h.store.snapshot().intents)
    assert h.service.apply_target_notice("notice_fx_r16", ORG, proposal_id) == ()
    assert len(h.store.snapshot().intents) == intents


@pytest.mark.parametrize("order", ["reject_then_policy", "policy_inside_reject"])
def test_rv_r17_reject_and_05_policy_interleavings(h: SketchReviewHarness, order: str) -> None:
    proposal_id = _ready(h)
    assert h.policy.snapshot is not None
    new_policy = replace(h.policy.snapshot, version="2")
    if order == "reject_then_policy":
        h.review(proposal_id, "reject")
        h.publish_review_policy(new_policy)
    else:
        _wrap_moderation(h, lambda: h.publish_review_policy(new_policy))
        h.review(proposal_id, "reject", etag=h.etag(proposal_id))
    h.service.refresh(proposal_id, ORG)
    assert len(h.store.snapshot().markers) == 1
    with pytest.raises(SketchReviewError) as raised:
        h.review(proposal_id, "approve")
    assert raised.value.code == "INVALID_STATE"
