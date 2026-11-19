"""Pure checks of the S7a writer logic (FEAT-066 SEED-7a, package Draft 3 test T3).

The decision table, the run-state check and the error mapping run against a fake
service. No database, settings or provider is touched.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.services.parent_story_runs import ParentStoryRunServiceError
from tools.seed import data
from tools.seed.s7a_runs import S7aError, ensure_parent_run

PARENT_KEY, PROFILE_KEY, TOPIC, IDEA = data.S7A_RUN_SPECS[0]
PROFILE_ID = data.parent_profile_id(PROFILE_KEY)
PRINCIPAL = VerifiedPrincipal(
    subject=data.PARENT_SUBJECTS[PARENT_KEY], issuer=data.SEED_ISSUER, roles=frozenset()
)
ACCOUNT_ID = data.parent_account_id(PARENT_KEY)


def _record(
    *,
    state: str = "INPUT_PROCESSING",
    confirmed: bool = False,
    topic: str = TOPIC,
    idea: str = IDEA,
    profile_id: uuid.UUID = PROFILE_ID,
) -> ParentStoryRunRecord:
    snapshot = {"topic": topic, "adult_confirmed_idea": idea, "age_months": 72}
    now = datetime(2026, 11, 19, tzinfo=UTC)
    return ParentStoryRunRecord(
        run_id="run-fake",
        run_state=state,
        run_revision=1,
        parent_profile_id=profile_id,
        profile_revision_ref=uuid.uuid4(),
        context_revision=1,
        context_confirmed=confirmed,
        context_snapshot=snapshot,
        context_snapshot_sha256=data.sha256_json(snapshot),
        current_input_revision=1,
        understanding_revision=None,
        subject_label=None,
        candidate=None,
        story_revision_id=None,
        story_revision_no=None,
        story_status=None,
        story_sha256=None,
        story_content=None,
        job_state=None,
        retryable=False,
        error_code=None,
        created_at=now,
        updated_at=now,
    )


def _lifecycle() -> ParentStoryLifecycleRecord:
    return ParentStoryLifecycleRecord(
        run_id="run-fake",
        run_state="DELETE_PENDING",
        revision=2,
        version=2,
        lifecycle_request_ref="request-fake",
        purge_state="REQUESTED",
    )


@dataclass
class FakeService:
    active: Any = None
    created: Any = None
    confirmed: Any = None
    create_error: Exception | None = None
    confirm_error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    def get_active_run(self, **_kwargs: Any) -> Any:
        self.calls.append("get_active_run")
        return self.active

    def create_run(self, **kwargs: Any) -> Any:
        self.calls.append("create_run")
        assert kwargs["idempotency_key"] == data.s7a_create_key(PARENT_KEY)
        assert kwargs["topic"] == TOPIC and kwargs["adult_confirmed_idea"] == IDEA
        if self.create_error is not None:
            raise self.create_error
        return self.created

    def confirm_context(self, **kwargs: Any) -> Any:
        self.calls.append("confirm_context")
        assert kwargs["idempotency_key"] == data.s7a_confirm_key(PARENT_KEY)
        if self.confirm_error is not None:
            raise self.confirm_error
        return self.confirmed


def _run(service: FakeService) -> str:
    return ensure_parent_run(
        service,
        principal=PRINCIPAL,
        account_id=ACCOUNT_ID,
        profile_id=PROFILE_ID,
        parent_key=PARENT_KEY,
        topic=TOPIC,
        idea=IDEA,
    )


def test_row_1_no_active_run_creates_then_confirms() -> None:
    service = FakeService(created=_record(), confirmed=_record(confirmed=True))
    assert _run(service) == "created"
    assert service.calls == ["get_active_run", "create_run", "confirm_context"]


def test_row_2_unconfirmed_seed_run_only_confirms() -> None:
    service = FakeService(active=_record(), confirmed=_record(confirmed=True))
    assert _run(service) == "confirmed"
    assert service.calls == ["get_active_run", "confirm_context"]


def test_row_3_confirmed_seed_run_changes_nothing() -> None:
    service = FakeService(active=_record(confirmed=True))
    assert _run(service) == "kept"
    assert service.calls == ["get_active_run"]


@pytest.mark.parametrize(
    "active",
    [
        _record(topic="another topic"),
        _record(idea="another idea"),
        _record(profile_id=uuid.uuid4()),
    ],
)
def test_row_4_foreign_active_run_stops(active: ParentStoryRunRecord) -> None:
    service = FakeService(active=active)
    with pytest.raises(S7aError) as info:
        _run(service)
    assert info.value.code == "S7A_FOREIGN_ACTIVE_RUN"
    assert service.calls == ["get_active_run"]


def test_a_tampered_snapshot_hash_is_foreign() -> None:
    tampered = replace(_record(confirmed=True), context_snapshot_sha256="0" * 64)
    service = FakeService(active=tampered)
    with pytest.raises(S7aError) as info:
        _run(service)
    assert info.value.code == "S7A_FOREIGN_ACTIVE_RUN"


def test_foreign_run_in_another_state_is_foreign_not_unexpected() -> None:
    service = FakeService(active=_record(state="COMPLETED", topic="another topic"))
    with pytest.raises(S7aError) as info:
        _run(service)
    assert info.value.code == "S7A_FOREIGN_ACTIVE_RUN"


@pytest.mark.parametrize(
    "view",
    [_lifecycle(), _record(state="DELETE_PENDING"), _record(state="COMPLETED")],
)
def test_other_run_states_stop_after_create_or_in_the_table(view: Any) -> None:
    created = FakeService(created=view)
    with pytest.raises(S7aError) as info:
        _run(created)
    assert info.value.code == "S7A_UNEXPECTED_RUN_STATE"
    assert created.calls == ["get_active_run", "create_run"]

    active = FakeService(active=view)
    with pytest.raises(S7aError) as info:
        _run(active)
    assert info.value.code == "S7A_UNEXPECTED_RUN_STATE"
    assert active.calls == ["get_active_run"]


def test_a_confirm_that_leaves_the_context_unconfirmed_stops() -> None:
    service = FakeService(created=_record(), confirmed=_record(confirmed=False))
    with pytest.raises(S7aError) as info:
        _run(service)
    assert info.value.code == "S7A_UNEXPECTED_RUN_STATE"


@pytest.mark.parametrize(
    "error",
    [
        ParentStoryRunError(409, "ACTIVE_RUN_EXISTS"),
        ParentStoryRunServiceError(422, "PARENT_STORY_TOPIC_INVALID"),
    ],
)
def test_errors_map_to_a_fixed_code_only(error: Exception) -> None:
    code = error.code  # type: ignore[attr-defined]
    with pytest.raises(S7aError) as info:
        _run(FakeService(create_error=error))
    assert info.value.code == f"S7A_COMMAND_FAILED_{code}"
    assert str(info.value) == info.value.code
    assert info.value.__cause__ is None
    assert info.value.__suppress_context__ is True


def test_confirm_errors_map_too() -> None:
    service = FakeService(
        created=_record(), confirm_error=ParentStoryRunError(409, "STALE_REVISION")
    )
    with pytest.raises(S7aError) as info:
        _run(service)
    assert info.value.code == "S7A_COMMAND_FAILED_STALE_REVISION"


def test_the_writer_module_does_not_import_the_modal_client() -> None:
    backend = Path(__file__).resolve().parents[2]
    code = "import sys, tools.seed.s7a_runs; sys.exit(1 if 'modal' in sys.modules else 0)"
    env = {**os.environ, "PYTHONPATH": str(backend / "src")}
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], cwd=backend, env=env, capture_output=True, check=False
    )
    assert result.returncode == 0
