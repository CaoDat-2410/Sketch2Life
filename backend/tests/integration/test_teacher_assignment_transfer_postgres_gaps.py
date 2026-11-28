"""Additional BE1 PostgreSQL integration tests for T-6b gaps identified in cold review R1."""

# ruff: noqa: F811

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from sketch2life.application.ports.teacher_assignment_transfer import (
    TeacherAssignmentTransferError,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    Be1TeacherAssignmentTransferModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.teacher_assignment_transfer_repository import (
    SqlTeacherAssignmentTransferRepository,
)
from tests.integration.test_m9b_first_assignment_postgres import (
    M9bApi,
    _assign,
    _class,
    _h,
    _identity,
    m9b_api,  # noqa: F401 - pytest fixture
)
from tests.integration.test_teacher_assignment_transfer_postgres import (
    _reassign,
    _status,
)


@pytest.mark.integration
def test_concurrent_same_key_reassign_creates_one_transfer_and_receipt(
    m9b_api: M9bApi,
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    api = m9b_api
    class_id = _class(api, "concurrent-same-key")
    _old_subject, old_ref = _identity(api, "conc-old", rows=((api.organization_id, None),))
    _new_subject, new_ref = _identity(api, "conc-new", rows=((api.organization_id, None),))
    assert _assign(api, class_id, old_ref, 1, f"t6b-init-{uuid4()}").status_code == 200

    key = f"t6b-conc-{uuid4()}"
    barrier = Barrier(2)

    def send() -> tuple[int, dict[str, object]]:
        barrier.wait()
        resp = _reassign(api, class_id, new_ref, 2, key)
        return resp.status_code, resp.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: send(), range(2)))

    assert [status for status, _ in results] == [202, 202]
    assert results[0][1] == results[1][1]
    with api.session()() as db:
        transfer_count = db.scalar(
            select(func.count())
            .select_from(Be1TeacherAssignmentTransferModel)
            .where(
                Be1TeacherAssignmentTransferModel.class_id == class_id,
                Be1TeacherAssignmentTransferModel.idempotency_key == key,
            )
        )
        receipt_count = db.scalar(
            select(func.count())
            .select_from(Be1CommandReceiptModel)
            .where(
                Be1CommandReceiptModel.principal_ref == api.manager,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )
    assert transfer_count == 1
    assert receipt_count == 1


@pytest.mark.integration
def test_fault_after_story_commit_before_finalize_reconciles_and_completes_on_replay(
    m9b_api: M9bApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    api = m9b_api
    class_id = _class(api, "fault-finalize")
    old_subject, old_ref = _identity(api, "fault-old", rows=((api.organization_id, None),))
    new_subject, new_ref = _identity(api, "fault-new", rows=((api.organization_id, None),))
    assert _assign(api, class_id, old_ref, 1, f"t6b-init-{uuid4()}").status_code == 200

    original_finalize = SqlTeacherAssignmentTransferRepository.finalize
    calls = 0

    def fail_once(repository, command, record, *, story_receipt_ref):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE")
        return original_finalize(repository, command, record, story_receipt_ref=story_receipt_ref)

    monkeypatch.setattr(SqlTeacherAssignmentTransferRepository, "finalize", fail_once)
    key = f"t6b-finalize-fault-{uuid4()}"
    first = _reassign(api, class_id, new_ref, 2, key)
    assert first.status_code == 202, first.text
    pending = _status(api, first.json())
    assert pending.status_code == 200
    assert pending.json()["state"] == "RECONCILE_REQUIRED"
    assert pending.json()["last_failure_code"] == "BE1_FINALIZE_UNCERTAIN"

    with api.session()() as db:
        active_rows = db.scalars(
            select(OrganizationAssignmentModel.subject).where(
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            )
        ).all()
    assert active_rows == []

    replay = _reassign(api, class_id, new_ref, 2, key)
    assert replay.status_code == 202
    assert replay.json() == first.json()
    done = _status(api, replay.json())
    assert done.status_code == 200
    assert done.json()["state"] == "COMPLETED"
    with api.session()() as db:
        active_rows = db.scalars(
            select(OrganizationAssignmentModel.subject).where(
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            )
        ).all()
    assert active_rows == [new_subject]
    assert old_subject not in active_rows


@pytest.mark.integration
def test_pending_class_blocks_writes_while_status_and_candidates_reads_work(
    m9b_api: M9bApi, monkeypatch: pytest.MonkeyPatch
) -> None:
    """covers: IMPL_REVIEW_D_T-6B_R1_20261125.md P2-4"""
    api = m9b_api
    class_id = _class(api, "pending-fenced-writes")
    _old_subject, old_ref = _identity(api, "fence-old", rows=((api.organization_id, None),))
    _new_subject, new_ref = _identity(api, "fence-new", rows=((api.organization_id, None),))
    _third_subject, third_ref = _identity(api, "fence-third", rows=((api.organization_id, None),))
    assert _assign(api, class_id, old_ref, 1, f"t6b-init-{uuid4()}").status_code == 200

    original_finalize = SqlTeacherAssignmentTransferRepository.finalize

    def fail_finalize(repository, command, record, *, story_receipt_ref):
        raise TeacherAssignmentTransferError(503, "DATABASE_UNAVAILABLE")

    monkeypatch.setattr(SqlTeacherAssignmentTransferRepository, "finalize", fail_finalize)
    accepted = _reassign(api, class_id, new_ref, 2, f"t6b-fence-{uuid4()}")
    assert accepted.status_code == 202

    second_reassign = _reassign(api, class_id, third_ref, 3, f"t6b-second-{uuid4()}")
    assert second_reassign.status_code == 409
    assert second_reassign.json()["code"] == "RESOURCE_CONFLICT"

    suspend = api.client.post(
        f"/api/be1/v1/classes/{class_id}/suspend",
        headers=_h(api.manager, **{"Idempotency-Key": f"t6b-suspend-{uuid4()}", "If-Match": '"2"'}),
    )
    assert suspend.status_code == 409

    status = _status(api, accepted.json())
    assert status.status_code == 200
    assert status.json()["state"] == "RECONCILE_REQUIRED"
    candidates = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-candidates",
        headers=_h(api.manager),
    )
    assert candidates.status_code == 200
    monkeypatch.setattr(SqlTeacherAssignmentTransferRepository, "finalize", original_finalize)


@pytest.mark.integration
def test_stale_revision_method_swap_and_current_teacher_conflict_on_postgres(
    m9b_api: M9bApi,
) -> None:
    """covers: D_T-6B_PROMPT.md §5"""
    api = m9b_api
    class_id = _class(api, "stale-swap-self")
    _old_subject, old_ref = _identity(api, "self-old", rows=((api.organization_id, None),))
    _new_subject, new_ref = _identity(api, "self-new", rows=((api.organization_id, None),))
    assert _assign(api, class_id, old_ref, 1, f"t6b-init-{uuid4()}").status_code == 200

    stale = _reassign(api, class_id, new_ref, 1, f"t6b-stale-{uuid4()}")
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2

    same_teacher = _reassign(api, class_id, old_ref, 2, f"t6b-self-{uuid4()}")
    assert same_teacher.status_code == 409
    assert same_teacher.json()["code"] == "RESOURCE_CONFLICT"

    shared_key = f"t6b-swap-{uuid4()}"
    reassign = _reassign(api, class_id, new_ref, 2, shared_key)
    assert reassign.status_code == 202
    swap = api.client.delete(
        f"/api/be1/v1/classes/{class_id}/assignments/current",
        headers=_h(api.manager, **{"Idempotency-Key": shared_key, "If-Match": '"4"'}),
    )
    assert swap.status_code == 400
    assert swap.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
