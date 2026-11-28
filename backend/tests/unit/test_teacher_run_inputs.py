"""FEAT-066 T-4b3a: the Teacher input steps, offline (statement-recording sessions, no database).

Plan section 10 (T-4b3a unit): the repository helper, the Teacher worker input and its bounds, the
real story client refusing a Teacher input before any provider call, the SUBJECT rule and the
attempt count by command kind, the audit writer, the reaper predicates, the receipt finalizer and
the upload policy. The PostgreSQL modules under ``tests/integration/story_teacher`` run the same
rules against real rows.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import (
    RunActor,
    RunActorKind,
    TeacherRunAccess,
)
from sketch2life.domain import story_teacher
from sketch2life.infrastructure.ai.modal_function_client import ModalStoryFunctionClient
from sketch2life.infrastructure.persistence import parent_story_repository as repository_module
from sketch2life.infrastructure.persistence import story_task_reaper_store as reaper_module
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    job_side_repository,
    story_task_audit_scope,
    write_story_task_audit,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_video.repository import OPERATION, SqlStoryVideoRepository
from sketch2life.infrastructure.uploads.purposes import (
    OCCURRENCE_DOCUMENT,
    POLICIES,
    RUN_ARTWORK,
    RUN_AUDIO,
)
from sketch2life.interfaces.http.story_run_actor import story_run_repository

PRINCIPAL = VerifiedPrincipal("adult-1", "issuer-1", frozenset())
ORG = "org-1"
RUN_ID = "22222222-2222-4222-8222-222222222222"
TEACHER = RunActor(RunActorKind.TEACHER, "account-1")
PARENT = RunActor(RunActorKind.PARENT, "account-2")
_DIALECT = postgresql.dialect()  # type: ignore[no-untyped-call]
V3_WORKER_KEYS = {
    "schema_version",
    "role",
    "language",
    "topic",
    "confirmed_subject",
    "understanding_revision",
    "drawing_sha256",
    "visible_features",
    "child_age_months",
    "context_revision",
    "adult_confirmed_idea",
    "rewrite_instruction",
    "lesson_subject_learning_notes",
    "lesson_direction",
    "primary_activity",
    "primary_activity_sha256",
}


def _sql(statement: Any) -> str:
    return str(statement.compile(dialect=_DIALECT, compile_kwargs={"literal_binds": True}))


class _Stop(Exception):
    """Raised by a recording session once the statement under test has been captured."""


class _Recorder:
    def __init__(self, *, scalar: Any = None, stop: bool = False) -> None:
        self.statements: list[Any] = []
        self.scalar_value = scalar
        self.stop = stop

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        row = {"revision_no": 1}
        return SimpleNamespace(
            mappings=lambda: SimpleNamespace(one_or_none=lambda: row, first=lambda: row)
        )

    def scalar(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        if self.stop:
            raise _Stop
        return self.scalar_value

    def rollback(self) -> None:
        pass


# ------------------------------------------------------------------------------ the helper (D1)
def test_a_parent_actor_builds_the_repository_exactly_as_before_t4a1() -> None:
    repository = story_run_repository(_Recorder(), PARENT)  # type: ignore[arg-type]
    assert isinstance(repository, SqlParentStoryRunRepository)
    assert repository._actor is None and repository._teacher_access is None
    assert repository._job_side is False and repository._job_side_organization is None


def test_a_teacher_actor_builds_the_repository_with_the_actor_and_the_access_port() -> None:
    repository = story_run_repository(_Recorder(), TEACHER)  # type: ignore[arg-type]
    assert repository._actor == TEACHER
    assert isinstance(repository._teacher_access, SqlTeacherRunAccess)
    assert repository._job_side is False


def test_the_job_side_helper_is_the_parent_repository_for_a_parent_or_no_actor() -> None:
    for actor in (None, PARENT):
        repository = job_side_repository(_Recorder(), actor, None)  # type: ignore[arg-type]
        assert repository._actor is None and repository._job_side is False
    teacher = job_side_repository(_Recorder(), TEACHER, ORG)  # type: ignore[arg-type]
    assert teacher._actor == TEACHER and teacher._job_side is True
    assert teacher._job_side_organization == ORG and teacher._teacher_access is None


# ------------------------------------------------------------ the Teacher worker input (D7b)
CONTEXT = {
    "schema_version": story_teacher.TEACHER_CONTEXT_SCHEMA,
    "selection_id": "selection-1",
    "age_months": 60,
    "age_revision": 1,
    "objectives": ["Nhận biết hình tròn", "Kể chuyện chú mèo"],
    "teacher_direction": "Câu chuyện về chú mèo đi tìm bạn",
    "activity_title": "Vẽ bằng ngón tay",
    "activity_snapshot_hash": "a" * 64,
}


def test_the_lesson_direction_is_a_closed_bounded_shape_of_the_context() -> None:
    direction = story_teacher.teacher_lesson_direction(CONTEXT)
    assert direction is not None
    assert tuple(direction) == story_teacher.LESSON_DIRECTION_KEYS
    assert direction["teacher_direction"] == CONTEXT["teacher_direction"]
    assert direction["objectives"] == CONTEXT["objectives"]
    assert direction["activity_title"] == CONTEXT["activity_title"]
    # nothing else of the snapshot travels: no selection id, no hash, no revision
    text = str(direction)
    assert "selection-1" not in text and "a" * 64 not in text


def test_the_lesson_direction_is_bounded_and_stable_for_the_same_snapshot() -> None:
    long = {
        **CONTEXT,
        "teacher_direction": "d" * 5000,
        "objectives": [f"objective {n} " + "o" * 900 for n in range(30)],
        "activity_title": "t" * 900,
    }
    direction = story_teacher.teacher_lesson_direction(long)
    assert direction is not None
    assert len(direction["teacher_direction"]) == story_teacher.LESSON_DIRECTION_TEXT_CHARS
    assert len(direction["objectives"]) == story_teacher.LESSON_DIRECTION_OBJECTIVES_MAX
    assert all(
        len(item) <= story_teacher.LESSON_DIRECTION_OBJECTIVE_CHARS
        for item in direction["objectives"]
    )
    assert len(direction["activity_title"]) == story_teacher.LESSON_DIRECTION_TITLE_CHARS
    assert story_teacher.teacher_lesson_direction(long) == direction  # a pure function


def test_an_empty_context_gives_no_direction() -> None:
    assert story_teacher.teacher_lesson_direction({}) is None
    empty = {**CONTEXT, "objectives": [], "teacher_direction": "  ", "activity_title": None}
    assert story_teacher.teacher_lesson_direction(empty) is None
    only_title = {**empty, "activity_title": "Vẽ"}
    assert story_teacher.teacher_lesson_direction(only_title) == {
        "teacher_direction": "",
        "objectives": [],
        "activity_title": "Vẽ",
    }


def test_parent_and_teacher_rewrite_literals_use_the_same_v3_key_set() -> None:
    source = inspect.getsource(SqlParentStoryRunRepository.reserve_story_rewrite)
    tree = ast.parse("class _C:\n" + "\n".join("    " + line for line in source.splitlines()))
    literals = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        and any(
            isinstance(key, ast.Constant) and key.value == "schema_version" for key in node.keys
        )
        and any(isinstance(key, ast.Constant) and key.value == "role" for key in node.keys)
    ]
    assert len(literals) == 2
    for literal in literals:
        keys = {key.value for key in literal.keys if isinstance(key, ast.Constant)}
        assert keys == V3_WORKER_KEYS
    assert '"role": "TEACHER"' in source and '"role": "PARENT"' in source
    assert "pinned_story_activity(" in source
    assert 'occurrence_id=str(run["occurrence_ref"])' in source
    assert 'organization_id=str(run["actor_scope_ref"])' in source
    assert "teacher_lesson_direction_text(context)" in source


def test_the_modal_client_still_refuses_an_unmapped_teacher_input() -> None:
    """The adapter maps Teacher to the worker gate value before invoking this strict client."""

    touched: list[str] = []

    class _Volume:
        def __getattr__(self, name: str) -> Any:
            touched.append(f"volume.{name}")
            raise AssertionError(name)

    class _Function:
        def __getattr__(self, name: str) -> Any:
            touched.append(f"function.{name}")
            raise AssertionError(name)

    client = ModalStoryFunctionClient(volume=_Volume(), function=_Function())
    activity = {
        "title": "classroom drawing",
        "objective": "name one shape",
        "materials_text": "",
        "preparation_text": "",
        "instructions_text": "draw one shape",
        "observation_notes": "",
        "safety_notes": "",
        "activity_kind": "indoor",
    }
    worker_input = {
        "schema_version": "sketch2life.story-generation-input.v3",
        "role": "TEACHER",
        "language": "vi",
        "topic": "classroom drawing",
        "confirmed_subject": "dragon",
        "understanding_revision": 1,
        "drawing_sha256": "a" * 64,
        "visible_features": ["wings"],
        "child_age_months": 60,
        "context_revision": 1,
        "adult_confirmed_idea": "idea",
        "rewrite_instruction": "instruction",
        "lesson_subject_learning_notes": None,
        "lesson_direction": "Name one shape.",
        "primary_activity": activity,
        "primary_activity_sha256": "0" * 64,
    }
    with pytest.raises(ValueError, match="Parent role"):
        client.generate({"worker_input": worker_input})
    assert touched == []


# ----------------------------------------------------------- the SUBJECT rule and attempts (D7)
def _basis_statement(repository: SqlParentStoryRunRepository) -> str:
    session = repository._session
    run = {"run_id": RUN_ID, "understanding_revision": 1}
    with pytest.raises(_Stop):
        repository._story_generation_basis(
            principal=PRINCIPAL,
            run=run,
            expected_understanding_revision=1,
            subject_error=(422, "SUBJECT_NOT_CONFIRMED"),
        )
    return _sql(session.statements[-1])  # type: ignore[attr-defined]


def test_the_subject_decision_of_a_parent_run_is_the_callers_own() -> None:
    parent = SqlParentStoryRunRepository(_Recorder(stop=True))  # type: ignore[arg-type]
    sql = _basis_statement(parent)
    assert f"actor_scope_ref = '{repository_module._principal_scope_ref(PRINCIPAL)}'" in sql
    assert "actor_scope_kind" not in sql.split("WHERE", 1)[1]
    assert "stage = 'SUBJECT'" in sql and "decision = 'CONFIRM'" in sql


def test_the_subject_decision_of_a_teacher_run_is_any_teacher_command_scope() -> None:
    teacher = SqlParentStoryRunRepository(
        _Recorder(stop=True),  # type: ignore[arg-type]
        actor=TEACHER,
        teacher_access=SimpleNamespace(),
    )
    sql = _basis_statement(teacher)
    where = sql.split("WHERE", 1)[1]
    assert "actor_scope_kind = 'ORGANIZATION'" in where
    assert "actor_scope_ref" not in where  # not "the same person": the run's Teacher scope
    assert repository_module._principal_scope_ref(PRINCIPAL) not in sql
    assert f"run_id = '{RUN_ID}'" in where


def test_the_attempts_of_a_slot_are_counted_by_the_owner_or_by_the_run_kind() -> None:
    parent_session = _Recorder(scalar=2)
    parent_run = {"run_id": RUN_ID, "actor_scope_kind": "PARENT_ACCOUNT", "actor_scope_ref": "p"}
    used = SqlParentStoryRunRepository(parent_session)._rewrite_attempts_used(  # type: ignore[arg-type]
        parent_run, "p", 2
    )
    assert used == 2
    parent_sql = _sql(parent_session.statements[0])
    assert (
        "actor_scope_kind = 'PARENT_ACCOUNT'" in parent_sql
        and "actor_scope_ref = 'p'" in parent_sql
    )
    teacher_session = _Recorder(scalar=3)
    teacher_run = {"run_id": RUN_ID, "actor_scope_kind": "ORGANIZATION", "actor_scope_ref": ORG}
    used = SqlParentStoryRunRepository(teacher_session)._rewrite_attempts_used(  # type: ignore[arg-type]
        teacher_run, "ignored-digest", 2
    )
    assert used == 3
    teacher_sql = _sql(teacher_session.statements[0])
    where = teacher_sql.split("WHERE", 1)[1]
    assert "actor_scope_kind = 'ORGANIZATION'" in where
    assert "actor_scope_ref" not in where and "ignored-digest" not in teacher_sql
    for sql in (parent_sql, teacher_sql):
        assert "operation = 'GENERATE_STORY_REVISION'" in sql
        assert f"idempotency_scope_ref = '{RUN_ID}'" in sql and "response_status = 202" in sql


# ------------------------------------------------------------------------ the audit writer (D13)
def _insert_params(session: _Recorder) -> dict[str, Any]:
    return dict(session.statements[0].compile(dialect=_DIALECT).params)


def test_the_parent_audit_row_is_written_exactly_as_before() -> None:
    session = _Recorder()
    now = datetime.now(UTC)
    write_story_task_audit(
        session,  # type: ignore[arg-type]
        owner_scope_ref="parent-scope",
        actor_ref="actor",
        action="STORY_REWRITE_ATTEMPT_FAILED",
        run_id=RUN_ID,
        decision="PROVIDER_TIMEOUT",
        run_revision=4,
        now=now,
    )
    params = _insert_params(session)
    assert params["owner_scope_kind"] == "PARENT_ACCOUNT"
    assert params["organization_id"] is None and params["owner_scope_ref"] == "parent-scope"
    assert params["resource_id"] == RUN_ID and params["decision"] == "PROVIDER_TIMEOUT"


def test_the_teacher_audit_row_is_scoped_to_the_organization_with_a_safe_code_only() -> None:
    session = _Recorder()
    run = {"actor_scope_kind": "ORGANIZATION", "actor_scope_ref": ORG}
    write_story_task_audit(
        session,  # type: ignore[arg-type]
        actor_ref="system:story-task-reaper",
        action="STORY_TASK_TIMED_OUT_STORY",
        run_id=RUN_ID,
        decision="PROVIDER_TIMEOUT",
        run_revision=4,
        now=datetime.now(UTC),
        **story_task_audit_scope(run),
    )
    params = _insert_params(session)
    assert params["owner_scope_kind"] == "ORGANIZATION"
    assert params["organization_id"] == ORG and params["owner_scope_ref"] == ORG
    assert params["resource_type"] and params["resource_id"] == RUN_ID
    assert set(params) >= {"audit_id", "actor_ref", "action", "decision", "created_at"}


def test_the_audit_scope_of_a_run_row_by_kind() -> None:
    assert story_task_audit_scope(
        {"actor_scope_kind": "PARENT_ACCOUNT", "actor_scope_ref": "p"}
    ) == {"owner_scope_ref": "p"}
    assert story_task_audit_scope({"actor_scope_ref": "p"}) == {"owner_scope_ref": "p"}
    assert story_task_audit_scope({"actor_scope_kind": "ORGANIZATION", "actor_scope_ref": ORG}) == {
        "owner_scope_kind": "ORGANIZATION",
        "owner_scope_ref": ORG,
        "organization_id": ORG,
    }


# ----------------------------------------------------------------------------- the reaper (D13)
def test_the_story_lane_is_the_parent_lane_and_the_pinned_teacher_lane() -> None:
    sql = _sql(reaper_module._story_lane())
    assert "actor_scope_kind = 'PARENT_ACCOUNT'" in sql
    assert "actor_scope_kind = 'ORGANIZATION' AND story.runs.occurrence_ref IS NOT NULL" in sql
    assert "current_input_revision IS NOT NULL" in sql
    assert "run_state NOT IN" in sql


def test_the_story_lane_twin_for_a_locked_row() -> None:
    def row(**override: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "actor_scope_kind": "PARENT_ACCOUNT",
            "occurrence_ref": None,
            "current_input_revision": 2,
            "run_state": "INPUT_PROCESSING",
        }
        base.update(override)
        return base

    in_lane = reaper_module._in_story_lane
    assert in_lane(row())  # type: ignore[arg-type]
    assert in_lane(row(actor_scope_kind="ORGANIZATION", occurrence_ref="occ-1"))  # type: ignore[arg-type]
    # a fixture row of a Teacher test has no pin and is not a product run
    assert not in_lane(row(actor_scope_kind="ORGANIZATION"))  # type: ignore[arg-type]
    # the demo lane never sets the input revision; a purged run is nobody's
    assert not in_lane(row(current_input_revision=None))  # type: ignore[arg-type]
    assert not in_lane(row(run_state="DELETE_PENDING"))  # type: ignore[arg-type]
    assert not in_lane(row(actor_scope_kind="SOMETHING_ELSE"))  # type: ignore[arg-type]


def test_receipts_of_a_teacher_run_are_matched_by_kind_and_of_a_parent_run_by_owner() -> None:
    teacher = _sql(
        reaper_module.select(reaper_module._RECEIPTS).where(  # type: ignore[attr-defined]
            *reaper_module._receipt_owner(
                cast(Any, {"actor_scope_kind": "ORGANIZATION", "actor_scope_ref": ORG})
            )
        )
    )
    parent = _sql(
        reaper_module.select(reaper_module._RECEIPTS).where(  # type: ignore[attr-defined]
            *reaper_module._receipt_owner(
                cast(Any, {"actor_scope_kind": "PARENT_ACCOUNT", "actor_scope_ref": "p"})
            )
        )
    )
    assert "actor_scope_kind = 'ORGANIZATION'" in teacher
    assert "actor_scope_ref" not in teacher.split("WHERE", 1)[1]
    assert "actor_scope_kind = 'PARENT_ACCOUNT'" in parent and "actor_scope_ref = 'p'" in parent


def test_the_reaper_has_no_literal_parent_only_predicate_left() -> None:
    source = inspect.getsource(reaper_module)
    assert "_parent_lane" not in source
    assert source.count("actor_scope_kind == _OWNER_SCOPE_KIND") == 2  # lane and receipt owner
    assert "story_task_audit_scope(run)" in source


# ------------------------------------------------------------------------ the receipt finalizer
def _finalize(run: dict[str, Any]) -> tuple[str, list[Any]]:
    """The WHERE text of the receipt update and the values bound in it (the SET holds a JSONB
    body that has no literal renderer, so the statement is compiled with bind parameters)."""
    session = _Recorder()
    repository = SqlStoryVideoRepository(session)  # type: ignore[arg-type]
    gen = {"request_idempotency_key_hash": "k" * 64}
    repository._finalize_receipt(
        cast(Any, run), cast(Any, gen), status=202, body={"ok": True}, now=datetime.now(UTC)
    )
    compiled = session.statements[0].compile(dialect=_DIALECT)
    where = str(compiled).split("WHERE", 1)[1]
    bound = [compiled.params[name] for name in compiled.params if name in where]
    return where, bound


def test_a_teacher_receipt_is_finalized_by_its_command_kind_not_by_the_run_owner_pair() -> None:
    run = {
        "actor_scope_kind": "ORGANIZATION",
        "actor_scope_ref": ORG,  # the organization id: NOT the receipt's digest
        "run_id": RUN_ID,
        "version": 3,
    }
    where, bound = _finalize(run)
    assert "actor_scope_kind =" in where and "actor_scope_ref" not in where
    assert "ORGANIZATION" in bound and ORG not in bound
    assert OPERATION in bound and RUN_ID in bound and "k" * 64 in bound and "PENDING" in bound
    assert "operation =" in where and "idempotency_key_sha256 =" in where and "state =" in where


def test_a_parent_receipt_is_finalized_by_the_same_row_as_before() -> None:
    run = {
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": "p",
        "run_id": RUN_ID,
        "version": 1,
    }
    where, bound = _finalize(run)
    assert "actor_scope_kind =" in where and "PARENT_ACCOUNT" in bound
    assert OPERATION in bound and "PENDING" in bound


# ----------------------------------------------------------------------- the upload policy (D4a)
def test_the_run_purposes_are_open_to_a_teacher_and_the_document_one_is_not_widened() -> None:
    for purpose in (RUN_ARTWORK, RUN_AUDIO):
        policy = POLICIES[purpose]
        assert policy.account_role == "parent"  # every existing assertion stays true
        assert policy.also_roles == frozenset({"teacher"})
        assert policy.roles == frozenset({"parent", "teacher"})
    document = POLICIES[OCCURRENCE_DOCUMENT]
    assert document.also_roles == frozenset() and document.roles == frozenset({"teacher"})


def test_a_policy_built_without_also_roles_admits_its_own_role_only() -> None:
    from sketch2life.infrastructure.uploads.purposes import UploadPurposePolicy

    policy = UploadPurposePolicy(
        purpose="X",
        account_role="parent",
        media_types=frozenset({"image/png"}),
        max_bytes=1,
        too_large_code="A",
        unsupported_code="B",
        needs_file_name=False,
        enabled=True,
    )
    assert policy.also_roles == frozenset() and policy.roles == frozenset({"parent"})


def test_the_upload_service_admits_a_role_by_the_policy_roles() -> None:
    from sketch2life.infrastructure.uploads import service as service_module

    source = inspect.getsource(service_module.UploadSessionService._policy_for)
    assert "identity.account_role not in policy.roles" in source


# ----------------------------------------------------------------------- the resolvers (D4b)
class _ResolverSession:
    """Answers the identity row and one run row; records every statement."""

    def __init__(self, role: str, run: tuple[str, str | None, str | None] | None) -> None:
        self.identity = SimpleNamespace(
            account_id="account-1", issuer="issuer-1", account_role=role, state="active"
        )
        self.run = run
        self.statements: list[Any] = []

    def get(self, _model: object, _key: object) -> Any:
        return self.identity

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        return SimpleNamespace(first=lambda: self.run)


def test_a_teacher_resolves_a_pinned_run_to_the_organization_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.infrastructure.uploads.resolvers import RunArtworkResolver

    resolver = RunArtworkResolver(_ResolverSession("teacher", (ORG, "child-1", "occ-1")))  # type: ignore[arg-type]
    calls: list[dict[str, Any]] = []

    def resolve(self: Any, **kwargs: Any) -> TeacherRunAccess:
        calls.append(kwargs)
        return TeacherRunAccess("class-a", "active")

    monkeypatch.setattr(SqlTeacherRunAccess, "resolve", resolve)
    scope = resolver.resolve(PRINCIPAL, RUN_ID)
    assert scope is not None
    assert (scope.owner_scope_kind, scope.owner_scope_ref) == ("ORGANIZATION", ORG)
    assert scope.organization_id == ORG and scope.object_prefix == f"parent/{RUN_ID}/"
    assert calls[0]["occurrence_ref"] == "occ-1" and calls[0]["lock"] is False


def test_a_teacher_gets_no_scope_for_a_missing_run_a_fixture_row_or_a_bad_id() -> None:
    from sketch2life.infrastructure.uploads.resolvers import RunArtworkResolver

    assert RunArtworkResolver(_ResolverSession("teacher", None)).resolve(PRINCIPAL, RUN_ID) is None  # type: ignore[arg-type]
    session = _ResolverSession("teacher", (ORG, "child", "occ"))
    assert RunArtworkResolver(session).resolve(PRINCIPAL, "not-a-uuid") is None  # type: ignore[arg-type]
    shouting = "ABCDEF01-2345-4678-8ABC-DEF012345678"  # a UUID that is not in its canonical form
    assert RunArtworkResolver(session).resolve(PRINCIPAL, shouting) is None  # type: ignore[arg-type]
    assert session.statements == []
    sql = _sql(
        (
            lambda s: (RunArtworkResolver(s).resolve(PRINCIPAL, RUN_ID), s.statements[0])[1]  # type: ignore[arg-type]
        )(_ResolverSession("teacher", None))
    )
    assert "occurrence_ref IS NOT NULL" in sql and "actor_scope_kind = 'ORGANIZATION'" in sql


def test_a_parent_keeps_the_parent_resolver_and_its_scope() -> None:
    from sketch2life.infrastructure.uploads.resolvers import RunArtworkResolver, parent_scope_ref

    session = _ResolverSession("parent", (ORG, None, None))
    scope = RunArtworkResolver(session).resolve(PRINCIPAL, RUN_ID)  # type: ignore[arg-type]
    assert scope is not None
    assert scope.owner_scope_kind == "PARENT_ACCOUNT"
    assert scope.owner_scope_ref == parent_scope_ref(PRINCIPAL) and scope.organization_id is None
    assert scope.object_prefix == f"parent/{RUN_ID}/"
    assert "PARENT_ACCOUNT" in _sql(session.statements[0])


def test_the_resolver_refuses_an_unassigned_teacher_before_it_returns_a_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.infrastructure.uploads.resolvers import RunArtworkResolver

    resolver = RunArtworkResolver(_ResolverSession("teacher", (ORG, "child-1", "occ-1")))  # type: ignore[arg-type]
    monkeypatch.setattr(SqlTeacherRunAccess, "resolve", lambda self, **kw: None)
    assert resolver.resolve(PRINCIPAL, RUN_ID) is None


def test_a_closed_run_class_makes_the_teacher_target_not_accepting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.application.ports.upload_sessions import UploadTargetNotAccepting
    from sketch2life.infrastructure.uploads.resolvers import RunArtworkResolver, RunAudioResolver

    for resolver_class, method in (
        (RunArtworkResolver, "ensure_accepting_artwork"),
        (RunAudioResolver, "ensure_accepting_audio"),
    ):
        resolver = resolver_class(_ResolverSession("teacher", (ORG, "c", "o")))  # type: ignore[arg-type]

        def refuse(self: Any, **_kw: Any) -> None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

        monkeypatch.setattr(SqlParentStoryRunRepository, method, refuse)
        with pytest.raises(UploadTargetNotAccepting):
            resolver.ensure_accepting(PRINCIPAL, RUN_ID)
