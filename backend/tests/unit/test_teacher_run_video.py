"""FEAT-066 T-4b3b: the Teacher side of the video repository, the sweeper and the output asset,
offline (statement-recording sessions, no database).

Plan section 10 (T-4b3b unit): the ``story_video_repository`` helper and the constructor defaults,
the site table of the video repository (the methods that take an actor and the methods that do
not), the access rule of the Teacher steps (pinned run, current assignment, read-only class after
the replay), the playback resolution of a Teacher, the closeout predicate of the overdue sweep and
the output asset scope by generation scope. The PostgreSQL modules under
``tests/integration/story_teacher`` run the same rules against real rows.
"""

from __future__ import annotations

import ast
import inspect
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import (
    RunActor,
    RunActorKind,
    TeacherRunAccess,
)
from sketch2life.application.ports.story_video import GenerationRecord, PlaybackStatus
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_video import closeout_store as closeout_module
from sketch2life.infrastructure.story_video import repository as repository_module
from sketch2life.infrastructure.story_video.fixture_runner import (
    FixtureVideoRunner,
    output_asset_organization,
)
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.story_run_actor import story_video_repository

PRINCIPAL = VerifiedPrincipal("adult-1", "issuer-1", frozenset())
ORG = "org-1"
RUN_ID = "22222222-2222-4222-8222-222222222222"
OCCURRENCE = "33333333-3333-4333-8333-333333333333"
TEACHER = RunActor(RunActorKind.TEACHER, "account-1")
PARENT = RunActor(RunActorKind.PARENT, "account-2")
_DIALECT = postgresql.dialect()  # type: ignore[no-untyped-call]
DIGEST = parent_scope_ref(PRINCIPAL)


def _sql(statement: Any) -> str:
    return str(statement.compile(dialect=_DIALECT, compile_kwargs={"literal_binds": True}))


class _Mappings:
    def __init__(self, value: Any) -> None:
        self._value = value

    def one_or_none(self) -> Any:
        return self._value


class _Result:
    def __init__(self, value: Any) -> None:
        self._value = value

    def mappings(self) -> _Mappings:
        return _Mappings(self._value)


class _Session:
    """Records the statements and answers each ``execute`` from a queue of rows."""

    def __init__(self, *rows: Any) -> None:
        self.statements: list[Any] = []
        self.rows = list(rows)
        self.rolled_back = False

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> _Result:
        self.statements.append(statement)
        return _Result(self.rows.pop(0) if self.rows else None)

    def rollback(self) -> None:
        self.rolled_back = True


class _Access:
    def __init__(self, answer: TeacherRunAccess | None) -> None:
        self.answer = answer
        self.calls: list[dict[str, Any]] = []

    def resolve(self, **kwargs: Any) -> TeacherRunAccess | None:
        self.calls.append(kwargs)
        return self.answer


def _teacher_run(**changes: Any) -> dict[str, Any]:
    run: dict[str, Any] = {
        "run_id": RUN_ID,
        "actor_scope_kind": "ORGANIZATION",
        "actor_scope_ref": ORG,
        "profile_ref": "child-1",
        "occurrence_ref": OCCURRENCE,
        "run_state": "SCRIPT_REVIEW",
    }
    run.update(changes)
    return run


# ------------------------------------------------------------------------------ the helper (D1)
def test_a_parent_actor_builds_the_video_repository_exactly_as_before() -> None:
    repository = story_video_repository(_Session(), PARENT)  # type: ignore[arg-type]
    assert isinstance(repository, SqlStoryVideoRepository)
    assert repository._actor is None and repository._teacher_access is None


def test_a_teacher_actor_builds_it_with_the_actor_and_the_access_port() -> None:
    repository = story_video_repository(_Session(), TEACHER)  # type: ignore[arg-type]
    assert repository._actor == TEACHER
    assert isinstance(repository._teacher_access, SqlTeacherRunAccess)


def test_the_constructor_defaults_keep_every_existing_caller_a_parent_repository() -> None:
    repository = SqlStoryVideoRepository(_Session())  # type: ignore[arg-type]
    assert repository._is_teacher is False
    assert repository._command_scope(PRINCIPAL) == ("PARENT_ACCOUNT", DIGEST)
    teacher = SqlStoryVideoRepository(_Session(), TEACHER, _Access(None))  # type: ignore[arg-type]
    assert teacher._command_scope(PRINCIPAL) == ("ORGANIZATION", DIGEST)


# -------------------------------------------------------------------------------- the site table
_SOURCE = inspect.getsource(repository_module)
# the methods a caller reaches with a principal: the actor decides which run is found
TEACHER_STEPS = {"begin_intent", "mark_unsuitable", "complete_run", "resolve_playback"}
# the methods that take no principal: the saga, the sweepers and the progress steps
OWNER_AGNOSTIC = {
    "finish_admission",
    "advance",
    "fail_for_cancelled_run",
    "mark_compute_closed",
    "get_generation",
    "pending_intents",
    "pending_compute_closures",
    "open_generations",
    "orphaned_in_flight",
}


def _public_methods() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(_SOURCE)
    (cls,) = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SqlStoryVideoRepository"
    ]
    return {
        node.name: node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }


def test_every_public_method_is_a_declared_teacher_step_or_owner_agnostic() -> None:
    methods = _public_methods()
    assert set(methods) == TEACHER_STEPS | OWNER_AGNOSTIC
    for name, node in methods.items():
        takes_principal = "principal" in {argument.arg for argument in node.args.kwonlyargs}
        assert takes_principal is (name in TEACHER_STEPS), name


def test_the_owner_pair_is_read_only_where_the_declared_sites_say() -> None:
    sites: dict[str, set[str]] = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Name(self, node: ast.Name) -> None:
            if node.id in {"_OWNER_SCOPE_KIND", "parent_scope_ref"} and isinstance(
                node.ctx, ast.Load
            ):
                sites.setdefault(self.stack[-1] if self.stack else "<module>", set()).add(node.id)

    Visitor().visit(ast.parse(_SOURCE))
    # the Parent owner predicate, the command scope, and the Teacher playback guard are the only
    # readers; the four steps reach them through ``_owned_run`` and ``_command_scope``
    assert set(sites) == {"_command_scope", "_owned_run", "resolve_playback"}


def test_the_four_steps_use_the_actor_for_the_run_and_the_command_scope_for_receipts() -> None:
    for name in ("begin_intent", "mark_unsuitable", "complete_run"):
        source = inspect.getsource(getattr(SqlStoryVideoRepository, name))
        assert "self._command_scope(principal)" in source, name
        assert "self._owned_run(principal, run_id)" in source, name
        assert "_OWNER_SCOPE_KIND" not in source and "parent_scope_ref" not in source, name
    # a read-only class refuses AFTER the replay lookup (SRS l.1697)
    begin = inspect.getsource(SqlStoryVideoRepository.begin_intent)
    assert begin.index("_by_key(") < begin.index("_refuse_read_only_class(access)")
    assert begin.index("_refuse_read_only_class(access)") < begin.index("_insert_intent(")
    for name in ("mark_unsuitable", "complete_run"):
        source = inspect.getsource(getattr(SqlStoryVideoRepository, name))
        assert source.index("_command_replay(") < source.index("_refuse_read_only_class(access)")
        assert source.index("_refuse_read_only_class(access)") < source.index(
            "_require_video_ready("
        )


# ------------------------------------------------------------------------- the access rule (D2)
def test_a_parent_finds_the_run_by_its_own_scope_and_never_asks_the_access_port() -> None:
    session = _Session({"run_id": RUN_ID})
    access = _Access(TeacherRunAccess("class-a", "active"))
    repository = SqlStoryVideoRepository(session, PARENT, None)  # type: ignore[arg-type]
    row, granted = repository._owned_run(PRINCIPAL, RUN_ID)
    assert row["run_id"] == RUN_ID and granted is None and access.calls == []
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'PARENT_ACCOUNT'" in sql and f"actor_scope_ref = '{DIGEST}'" in sql
    assert "FOR UPDATE" in sql and "occurrence_ref" not in sql.split("WHERE", 1)[1]


def test_a_teacher_finds_only_a_pinned_organization_run_and_asks_for_the_current_assignment() -> (
    None
):
    session = _Session(_teacher_run())
    access = _Access(TeacherRunAccess("class-a", "active"))
    repository = SqlStoryVideoRepository(session, TEACHER, access)  # type: ignore[arg-type]
    row, granted = repository._owned_run(PRINCIPAL, RUN_ID)
    assert granted == TeacherRunAccess("class-a", "active") and row["run_id"] == RUN_ID
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'ORGANIZATION'" in sql and "occurrence_ref IS NOT NULL" in sql
    assert (
        "FOR UPDATE" in sql and "actor_scope_ref =" not in sql
    )  # the organization is read, not given
    (call,) = access.calls
    assert call["organization_id"] == ORG and call["occurrence_ref"] == OCCURRENCE
    assert call["lock"] is True and call["principal"] == PRINCIPAL


@pytest.mark.parametrize("case", ["no_row", "no_access_port", "no_assignment"])
def test_a_teacher_without_a_pinned_run_or_a_current_assignment_gets_the_uniform_404(
    case: str,
) -> None:
    session = _Session(None if case == "no_row" else _teacher_run())
    port = None if case == "no_access_port" else _Access(None)
    repository = SqlStoryVideoRepository(session, TEACHER, port)  # type: ignore[arg-type]
    with pytest.raises(ParentStoryRunError) as caught:
        repository._owned_run(PRINCIPAL, RUN_ID)
    assert (caught.value.status_code, caught.value.code) == (404, "RESOURCE_NOT_FOUND")


def test_a_read_only_class_refuses_a_write_with_409_and_an_active_class_does_not() -> None:
    refuse = SqlStoryVideoRepository._refuse_read_only_class
    refuse(None)
    refuse(TeacherRunAccess("class-a", "active"))
    for state in ("suspended", "archived"):
        with pytest.raises(ParentStoryRunError) as caught:
            refuse(TeacherRunAccess("class-a", state))
        assert (caught.value.status_code, caught.value.code) == (409, "INVALID_STATE_TRANSITION")


# ----------------------------------------------------------------------- the playback (D10)
def _playback_row(**changes: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "run_state": "VIDEO_READY",
        "current_video_generation_id": "gen-1",
        "video_generation_id": "gen-1",
        "generation_state": "READY",
        "output_asset_ref": f"parent/{RUN_ID}/video/gen-1/output.mp4",
        "technical_validation_state": "PASSED",
        "consistency_validation_state": "PASSED",
        "safety_validation_state": "PASSED",
        "actor_scope_ref": ORG,
        "profile_ref": "child-1",
        "occurrence_ref": OCCURRENCE,
    }
    row.update(changes)
    return row


def test_a_teacher_playback_reads_the_pinned_run_without_a_lock_and_binds_the_caller_digest() -> (
    None
):
    session = _Session(_playback_row())
    access = _Access(TeacherRunAccess("class-a", "suspended"))  # a read-only class still plays
    repository = SqlStoryVideoRepository(session, TEACHER, access)  # type: ignore[arg-type]
    resolution = repository.resolve_playback(principal=PRINCIPAL, run_id=RUN_ID, generation_id=None)
    assert resolution.status is PlaybackStatus.PLAYABLE and resolution.target is not None
    assert resolution.target.scope_ref == DIGEST  # one Teacher, not the organization
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'ORGANIZATION'" in sql and "occurrence_ref IS NOT NULL" in sql
    assert "FOR UPDATE" not in sql and "FOR SHARE" not in sql
    (call,) = access.calls
    assert call["lock"] is False and call["occurrence_ref"] == OCCURRENCE


def test_a_teacher_playback_without_the_current_assignment_or_a_pinned_run_is_not_found() -> None:
    for session, port in (
        (_Session(_playback_row()), _Access(None)),
        (_Session(_playback_row()), None),
        (_Session(None), _Access(TeacherRunAccess("class-a", "active"))),
    ):
        repository = SqlStoryVideoRepository(session, TEACHER, port)  # type: ignore[arg-type]
        resolution = repository.resolve_playback(
            principal=PRINCIPAL, run_id=RUN_ID, generation_id=None
        )
        assert resolution.status is PlaybackStatus.NOT_FOUND and resolution.target is None


def test_a_teacher_playback_still_needs_a_playable_run_and_the_token_generation() -> None:
    access = _Access(TeacherRunAccess("class-a", "active"))
    completed = SqlStoryVideoRepository(
        _Session(_playback_row(run_state="COMPLETED")),  # type: ignore[arg-type]
        TEACHER,
        access,
    ).resolve_playback(principal=PRINCIPAL, run_id=RUN_ID, generation_id=None)
    assert completed.status is PlaybackStatus.NOT_PLAYABLE  # a COMPLETED run gets no token
    other_generation = SqlStoryVideoRepository(
        _Session(_playback_row()),  # type: ignore[arg-type]
        TEACHER,
        access,
    ).resolve_playback(principal=PRINCIPAL, run_id=RUN_ID, generation_id="gen-2")
    assert other_generation.status is PlaybackStatus.NOT_PLAYABLE
    purged = SqlStoryVideoRepository(
        _Session(_playback_row(run_state="DELETE_PENDING")),  # type: ignore[arg-type]
        TEACHER,
        access,
    ).resolve_playback(principal=PRINCIPAL, run_id=RUN_ID, generation_id=None)
    assert purged.status is PlaybackStatus.NOT_FOUND


def test_the_parent_playback_statement_is_the_one_it_always_was() -> None:
    session = _Session(None)
    SqlStoryVideoRepository(session).resolve_playback(  # type: ignore[arg-type]
        principal=PRINCIPAL, run_id=RUN_ID, generation_id=None
    )
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'PARENT_ACCOUNT'" in sql and f"actor_scope_ref = '{DIGEST}'" in sql
    assert "occurrence_ref" not in sql and "profile_ref" not in sql


# ------------------------------------------------------------------ the overdue sweep (D12)
def test_the_overdue_listing_reads_parent_runs_and_runs_holding_the_teacher_lock_only() -> None:
    from datetime import UTC, datetime

    captured: list[Any] = []

    class _Recording:
        def execute(self, statement: Any) -> Any:
            captured.append(statement)
            return SimpleNamespace(all=lambda: [])

        def rollback(self) -> None:
            pass

    store = closeout_module.SqlStoryRunCloseoutStore(_Recording())  # type: ignore[arg-type]
    store.overdue_generations(datetime(2026, 11, 22, tzinfo=UTC), 10)
    sql = _sql(captured[0])
    assert "actor_scope_kind = 'PARENT_ACCOUNT' OR" in sql
    assert "active_owner_teacher_id IS NOT NULL" in sql  # a fixture row has no lock: untouched
    assert "run_state NOT IN" in sql and "accepted_at <=" in sql
    # the same predicate as the idle listing (one rule for the two sweeps)
    idle = _sql(store.idle_statement(datetime(2026, 11, 22, tzinfo=UTC), 10))
    assert "actor_scope_kind = 'PARENT_ACCOUNT' OR" in idle
    assert "active_owner_teacher_id IS NOT NULL" in idle


# --------------------------------------------------------------- the output asset scope (D16)
def _record(scope_kind: str, scope_ref: str) -> GenerationRecord:
    return GenerationRecord(
        generation_id="gen-1",
        run_id=RUN_ID,
        scope_kind=scope_kind,
        scope_ref=scope_ref,
        state="SAFETY_VALIDATING",
        kind="INITIAL",
        generation_no=1,
        job_ref="vjob_1",
        key_hash="k" * 64,
        fingerprint="f" * 64,
        script_hash="a" * 64,
        story_revision_id="rev-1",
        review_id="review-1",
        quality_reason_code=None,
        compute_reservation_ref="res-1",
        compute_released_at=None,
        billing_quota_usage_ref="usage-1",
        safe_failure_code=None,
        started=True,
        generation_revision=4,
        run_state="VIDEO_SAFETY_VALIDATING",
        run_revision=6,
    )


class _AssetSession:
    def __init__(self) -> None:
        self.added: list[Any] = []

    def __enter__(self) -> _AssetSession:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def add(self, row: Any) -> None:
        self.added.append(row)

    def commit(self) -> None:
        return None


def _written_asset(record: GenerationRecord) -> Any:
    session = _AssetSession()
    runner = FixtureVideoRunner(lambda: session, object(), None)  # type: ignore[arg-type,return-value]
    runner._write_asset(
        record,
        f"parent/{RUN_ID}/video/gen-1/output.mp4",
        SimpleNamespace(content=b"x", media_type="video/mp4"),  # type: ignore[arg-type]
    )
    (row,) = session.added
    return row


def test_the_output_asset_of_a_parent_run_is_a_parent_row_as_before() -> None:
    row = _written_asset(_record("PARENT_ACCOUNT", "p" * 64))
    assert (row.owner_scope_kind, row.owner_scope_ref, row.organization_id) == (
        "PARENT_ACCOUNT",
        "p" * 64,
        None,
    )
    assert row.source_refs == [RUN_ID] and row.asset_ref.startswith(f"parent/{RUN_ID}/video/")


def test_the_output_asset_of_a_teacher_run_is_an_organization_row_with_the_org_as_ref() -> None:
    row = _written_asset(_record("ORGANIZATION", ORG))
    assert (row.owner_scope_kind, row.owner_scope_ref, row.organization_id) == (
        "ORGANIZATION",
        ORG,
        ORG,
    )
    # the key prefix is part of the purge contract (T-4b2 OPEN-4): it stays ``parent/{run}/``
    assert row.asset_ref == f"parent/{RUN_ID}/video/gen-1/output.mp4"
    assert row.source_refs == [RUN_ID] and row.asset_version == 1


def test_the_organization_of_an_output_asset_follows_the_generation_scope() -> None:
    assert output_asset_organization(_record("ORGANIZATION", ORG)) == ORG
    assert output_asset_organization(_record("PARENT_ACCOUNT", "p" * 64)) is None
