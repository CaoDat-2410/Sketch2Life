"""Pure data and fake-service checks for the S11 run/share seed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import pytest

from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from sketch2life.domain.lesson_library.model import validate_content
from tools.seed import data
from tools.seed.guard import SeedGuardError
from tools.seed.s11_org_run_shares import (
    cancel_teacher_run_command,
    count_stage_rows,
    seed_lesson_shares,
    teacher_run_insert_rows,
)
from tools.seed.s11_org_run_shares_data import (
    EXPECTED,
    LESSON_CONTENTS,
    LESSON_RECEIPT_KEYS,
    MANAGER_A,
    ORG_A,
    PARENT_GROUP_A1,
    PARENT_P1,
    PRIVATE_SHARE_SPECS,
    REVIEW_CHANGE_REASON,
    TEACHER_A1,
    TEACHER_A2,
    TEACHER_CONTEXT_SNAPSHOT,
    TEACHER_RUN_CANCEL_KEY,
    TEACHER_RUN_ID,
    TEACHER_RUN_IDEA,
    TEACHER_RUN_INPUT_ID,
    TEACHER_RUN_PROFILE_REF,
    TEACHER_RUN_STATE,
    TEACHER_RUN_TOPIC,
)
from tools.seed.stage_common import StageError, check_database_prefix, seed_principal, stage_key


@dataclass
class _SessionContext:
    session: object

    def __enter__(self) -> object:
        return self.session

    def __exit__(self, *_exc: object) -> Literal[False]:
        return False


class _SessionFactory:
    def __init__(self) -> None:
        self.session = object()

    def __call__(self) -> _SessionContext:
        return _SessionContext(self.session)


class _FakeLessonService:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self._grants: dict[str, str] = {}
        self._grant_number = 0

    def create_lesson(self, **kwargs: Any) -> dict[str, Any]:
        content = kwargs["content"]
        lesson_key = {
            "Vẽ chú gà con": "chicken",
            "Vẽ chiếc thuyền buồm": "sailing",
            "Vẽ bông hoa hướng dương": "sunflower",
        }[content.title]
        self.events.append(("create_lesson", kwargs))
        return {
            "lesson_id": f"lesson-{lesson_key}",
            "current_version": {"version_id": f"version-{lesson_key}"},
        }

    def create_access_grant(self, **kwargs: Any) -> dict[str, Any]:
        self._grant_number += 1
        grant_id = f"grant-{self._grant_number}"
        self._grants[kwargs["idempotency_key"]] = grant_id
        self.events.append(("create_access_grant", kwargs))
        return {"access_grant_id": grant_id, "lesson_id": kwargs["lesson_id"]}

    def decide_access_grant(self, **kwargs: Any) -> dict[str, Any]:
        self.events.append(("decide_access_grant", kwargs))
        return {"state": "CHANGES_REQUESTED"}


def _valid_lesson_model(content: dict[str, Any]) -> LessonContentInputV1:
    model = LessonContentInputV1.model_validate(content)
    validate_content(model.model_dump(mode="json"))
    return model


def test_all_three_lesson_contents_are_structurally_complete_and_specific() -> None:
    assert len(LESSON_CONTENTS) == 3
    for key, content in LESSON_CONTENTS.items():
        model = _valid_lesson_model(content)
        assert model.locale == "vi-VN"
        assert model.target_age_band_ref == data.SUPPORTED_AGE_BAND_REF
        assert model.target_age_band_version == 1
        assert len(model.activities) == 2
        assert all(activity.instructions_text for activity in model.activities)
        assert model.title not in " ".join(model.objectives)
        combined = " ".join(
            [model.title, model.topic, *model.objectives, model.drawing_steps_text]
            + [activity.instructions_text for activity in model.activities]
        )
        assert "[SEED]" not in combined and "lorem ipsum" not in combined.lower()
        assert "Mục tiêu:" not in combined
        assert key in {"chicken", "sailing", "sunflower"}


def test_three_share_specs_cover_the_requested_review_states_and_audiences() -> None:
    by_key = {spec["lesson_key"]: spec for spec in PRIVATE_SHARE_SPECS}
    assert set(by_key) == {"chicken", "sailing", "sunflower"}
    assert by_key["chicken"]["expected_review_state"] == "DRAFT"
    assert by_key["chicken"]["audience_kind"] == "ORGANIZATION"
    assert by_key["chicken"]["expected_visibility"] == "SCHOOL"
    assert by_key["sailing"]["expected_review_state"] == "PENDING_REVIEW"
    assert by_key["sailing"]["audience_kind"] == "PRINCIPAL"
    assert by_key["sailing"]["audience_ref"] == PARENT_P1
    assert by_key["sailing"]["expected_visibility"] == "SELECTED_AUDIENCE"
    assert by_key["sunflower"]["expected_review_state"] == "CHANGES_REQUESTED"
    assert by_key["sunflower"]["audience_kind"] == "PARENT_GROUP"
    assert by_key["sunflower"]["audience_ref"] == PARENT_GROUP_A1
    assert by_key["sunflower"]["expected_visibility"] == "SELECTED_AUDIENCE"
    assert len(LESSON_RECEIPT_KEYS) == EXPECTED["lesson_command_receipts_s11"] == 10
    assert EXPECTED["lesson_access_grants_s11"] == 6


def test_lesson_shares_use_the_service_for_public_review_and_private_grants() -> None:
    factory = _SessionFactory()
    service = _FakeLessonService()
    seed_lesson_shares(
        factory,
        service_factory=lambda _session: cast(Any, service),
    )
    creates = [kwargs for name, kwargs in service.events if name == "create_lesson"]
    grants = [kwargs for name, kwargs in service.events if name == "create_access_grant"]
    decisions = [kwargs for name, kwargs in service.events if name == "decide_access_grant"]
    assert len(creates) == 3 and len(grants) == 6 and len(decisions) == 1
    assert {kwargs["content"].title for kwargs in creates} == set(
        content["title"] for content in LESSON_CONTENTS.values()
    )
    assert {kwargs["actor"] for kwargs in creates} == {TEACHER_A1, TEACHER_A2}
    assert (
        next(kwargs for kwargs in creates if kwargs["content"].title == "Vẽ chiếc thuyền buồm")[
            "actor"
        ]
        == TEACHER_A2
    )
    assert all(kwargs["visibility"] == "PRIVATE" for kwargs in creates)
    public = [kwargs for kwargs in grants if kwargs["audience_kind"] == "PUBLIC"]
    assert len(public) == 2
    assert all(kwargs["audience_ref"] is None for kwargs in public)
    direct = [kwargs for kwargs in grants if kwargs["audience_kind"] == "PRINCIPAL"]
    assert len(direct) == 1
    assert direct[0]["audience_ref"] == PARENT_P1 and direct[0]["capability"] == "VIEW"
    groups = [kwargs for kwargs in grants if kwargs["audience_kind"] == "PARENT_GROUP"]
    assert len(groups) == 2
    assert all(kwargs["audience_ref"] == PARENT_GROUP_A1 for kwargs in groups)
    assert all(kwargs["idempotency_key"].startswith("seed:s11:") for kwargs in grants)
    assert decisions[0]["actor"] == MANAGER_A
    assert decisions[0]["decision"] == "REQUEST_CHANGES"
    assert decisions[0]["reason"] == REVIEW_CHANGE_REASON
    assert decisions[0]["idempotency_key"] == stage_key("s11", "lesson-sunflower-request-changes")


def test_teacher_fixture_rows_match_organization_context_and_have_no_media() -> None:
    run, run_input = teacher_run_insert_rows()
    assert run["run_id"] == TEACHER_RUN_ID
    assert run["actor_scope_kind"] == "ORGANIZATION" and run["actor_scope_ref"] == ORG_A
    assert run["profile_ref"] == TEACHER_RUN_PROFILE_REF == "seed-ch-a-1-1"
    assert run["run_state"] == TEACHER_RUN_STATE == "PREPARATION_REVIEW"
    assert run["active_owner_parent_account_id"] is None
    assert run_input["run_input_id"] == TEACHER_RUN_INPUT_ID
    assert run_input["run_id"] == run["run_id"]
    assert run_input["context_snapshot"] == TEACHER_CONTEXT_SNAPSHOT
    assert run_input["context_snapshot_sha256"] == data.sha256_json(TEACHER_CONTEXT_SNAPSHOT)
    assert run_input["typed_idea"] == TEACHER_RUN_IDEA
    assert run_input["context_confirmed_by"] == data.principal_scope_ref(
        data.SEED_ISSUER, TEACHER_A1
    )
    assert all("asset" not in key for key in run)
    assert all("asset" not in key for key in run_input)
    assert TEACHER_CONTEXT_SNAPSHOT["topic"] == TEACHER_RUN_TOPIC
    assert stage_key("s11", TEACHER_RUN_CANCEL_KEY) == "seed:s11:teacher-run-cancel"


def test_teacher_cancel_uses_the_real_service_shape_and_fixed_idempotency_key() -> None:
    principal = seed_principal(TEACHER_A1)

    class FakeService:
        def __init__(self) -> None:
            self.kwargs: dict[str, Any] = {}

        def cancel_run(self, **kwargs: Any) -> ParentStoryLifecycleRecord:
            self.kwargs = kwargs
            return ParentStoryLifecycleRecord(
                run_id=TEACHER_RUN_ID,
                run_state="DELETE_PENDING",
                revision=2,
                version=2,
                lifecycle_request_ref="request-ref",
                purge_state="REQUESTED",
            )

    service = FakeService()
    result = cancel_teacher_run_command(service, principal)
    assert result.run_state == "DELETE_PENDING"
    assert service.kwargs == {
        "principal": principal,
        "run_id": TEACHER_RUN_ID,
        "expected_revision": 1,
        "idempotency_key": stage_key("s11", TEACHER_RUN_CANCEL_KEY),
    }


def test_teacher_cancel_refuses_service_errors_and_wrong_end_state() -> None:
    principal = seed_principal(TEACHER_A1)

    class FailingService:
        def cancel_run(self, **_kwargs: Any) -> None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    with pytest.raises(StageError, match="S11_TEACHER_CANCEL_FAILED"):
        cancel_teacher_run_command(FailingService(), principal)

    class WrongStateService:
        def cancel_run(self, **_kwargs: Any) -> ParentStoryLifecycleRecord:
            return ParentStoryLifecycleRecord(
                run_id=TEACHER_RUN_ID,
                run_state="COMPLETED",
                revision=1,
                version=1,
                lifecycle_request_ref="request-ref",
                purge_state="NONE",
            )

    with pytest.raises(StageError, match="S11_TEACHER_CANCEL_STATE_INVALID"):
        cancel_teacher_run_command(WrongStateService(), principal)


def test_s11_guard_requires_the_frc08_database_prefix() -> None:
    def environ(database: str) -> dict[str, str]:
        return {
            "S2L_SEED_DATABASE_URL": (
                f"postgresql+psycopg://fixture:fixture@127.0.0.1:5435/{database}"
            )
        }

    with pytest.raises(SeedGuardError):
        check_database_prefix(environ("seed_s11_fixture"))
    check_database_prefix(environ("frc08_seed_s11_fixture"))


def test_count_stage_rows_returns_every_expected_table_key() -> None:
    class Result:
        def __init__(self, value: int) -> None:
            self.value = value

        def scalar_one(self) -> int:
            return self.value

    class Connection:
        def __init__(self) -> None:
            self.index = 0

        def execute(self, _statement: Any) -> Result:
            values = (3, 3, 6, 6, 10, 1, 1, 1)
            value = values[self.index]
            self.index += 1
            return Result(value)

    assert count_stage_rows(Connection()) == EXPECTED  # type: ignore[arg-type]
