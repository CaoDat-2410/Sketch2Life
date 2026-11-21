"""FEAT-066 T-4a1: the StoryRun actor guard, the Teacher owner and command scopes, the site table.

No database is used. The repository is driven with a statement-recording session and a fake
Teacher access port; the SQL of the owner lookup and of the receipts is compiled and read, so the
"owner scope and command scope are two things" rule (plan review T4A1-01) is pinned in text.
"""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import (
    PARENT_COMMAND_SCOPE_KIND,
    TEACHER_COMMAND_SCOPE_KIND,
    RunActor,
    RunActorKind,
    TeacherRunAccess,
)
from sketch2life.infrastructure.persistence import parent_story_repository as repository_module
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.interfaces.http.story_run_actor import require_story_run_actor

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
ORG = "org-1"
CHILD = "33333333-3333-4333-8333-333333333333"
RUN_ID = "22222222-2222-4222-8222-222222222222"


def _digest(principal: VerifiedPrincipal) -> str:
    claims = {"issuer": principal.issuer, "subject": principal.subject}
    text = json.dumps(claims, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


DIGEST = _digest(PRINCIPAL)
_DIALECT = postgresql.dialect()  # type: ignore[no-untyped-call]
PARENT = RunActor(RunActorKind.PARENT, "account-1")
TEACHER = RunActor(RunActorKind.TEACHER, "account-1")


def _sql(statement: Any) -> str:
    return str(statement.compile(dialect=_DIALECT, compile_kwargs={"literal_binds": True}))


# ---------------------------------------------------------------------------- the role guard
class _Db:
    def __init__(self, identity: Any) -> None:
        self._identity = identity

    def get(self, _model: object, _key: object) -> Any:
        return self._identity


def _identity(role: str | None, *, state: str = "active", issuer: str = ISSUER) -> Any:
    return SimpleNamespace(account_id="account-1", issuer=issuer, account_role=role, state=state)


@pytest.mark.parametrize(
    ("role", "kind"), [("parent", RunActorKind.PARENT), ("teacher", RunActorKind.TEACHER)]
)
def test_an_active_parent_or_teacher_is_a_run_actor(role: str, kind: RunActorKind) -> None:
    actor = require_story_run_actor(_Db(_identity(role)), PRINCIPAL)  # type: ignore[arg-type]
    assert actor == RunActor(kind, "account-1")
    assert actor.is_teacher is (kind is RunActorKind.TEACHER)


@pytest.mark.parametrize(
    "identity",
    [
        None,
        _identity("school_manager"),
        _identity("platform_admin"),
        _identity(None),
        _identity("parent", state="suspended"),
        _identity("teacher", state="suspended"),
        _identity("parent", issuer="another-issuer"),
        _identity("teacher", issuer="another-issuer"),
    ],
    ids=[
        "no-identity",
        "manager",
        "platform-admin",
        "no-role",
        "inactive-parent",
        "inactive-teacher",
        "issuer-mismatch-parent",
        "issuer-mismatch-teacher",
    ],
)
def test_every_other_caller_gets_the_one_uniform_404(identity: Any) -> None:
    with pytest.raises(HTTPException) as caught:
        require_story_run_actor(_Db(identity), PRINCIPAL)  # type: ignore[arg-type]
    assert caught.value.status_code == 404
    assert cast(Any, caught.value).detail == {"code": "RESOURCE_NOT_FOUND"}


def test_the_command_scope_kinds() -> None:
    assert PARENT.command_scope_kind == PARENT_COMMAND_SCOPE_KIND == "PARENT_ACCOUNT"
    assert TEACHER.command_scope_kind == TEACHER_COMMAND_SCOPE_KIND == "ORGANIZATION"
    assert TeacherRunAccess("class-a", "active").writable
    assert not TeacherRunAccess("class-a", "suspended").writable
    assert not TeacherRunAccess("class-a", "archived").writable


# ---------------------------------------------------------------------- a recording session
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
    def __init__(self, *, run: Any = None, receipt: Any = None, scalar: Any = None) -> None:
        self.run = run
        self.receipt = receipt
        self.scalar_value = scalar
        self.statements: list[Any] = []
        self.rollbacks = 0

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> _Result:
        self.statements.append(statement)
        table = ""
        froms = list(getattr(statement, "get_final_froms", lambda: [])())
        if froms:
            table = getattr(froms[0], "name", "")
        if table == "command_receipts":
            return _Result(self.receipt)
        return _Result(self.run)

    def scalar(self, statement: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.statements.append(statement)
        return self.scalar_value

    def rollback(self) -> None:
        self.rollbacks += 1


class _Port:
    def __init__(self, access: TeacherRunAccess | None) -> None:
        self.access = access
        self.calls: list[dict[str, Any]] = []

    def resolve(self, **kwargs: Any) -> TeacherRunAccess | None:
        self.calls.append(kwargs)
        return self.access


def _teacher_run(**override: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "run_id": RUN_ID,
        "actor_scope_kind": "ORGANIZATION",
        "actor_scope_ref": ORG,
        "profile_ref": CHILD,
        "run_state": "PREPARATION_REVIEW",
    }
    row.update(override)
    return row


def _repository(
    session: _Session, actor: RunActor | None = None, port: _Port | None = None
) -> SqlParentStoryRunRepository:
    return SqlParentStoryRunRepository(
        session,  # type: ignore[arg-type]
        actor=actor,
        teacher_access=port,
    )


# --------------------------------------------------------------- owner scope (the run lookup)
def test_the_parent_lookup_is_the_unchanged_kind_and_digest_filter() -> None:
    session = _Session(run=_teacher_run())
    repository = _repository(session)
    repository._owned_run(PRINCIPAL, RUN_ID, lock=True)
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'PARENT_ACCOUNT'" in sql
    assert f"actor_scope_ref = '{DIGEST}'" in sql
    assert "FOR UPDATE" in sql
    # an explicit Parent actor behaves the same
    explicit = _Session(run=_teacher_run())
    _repository(explicit, PARENT)._owned_run(PRINCIPAL, RUN_ID)
    assert f"actor_scope_ref = '{DIGEST}'" in _sql(explicit.statements[0])


def test_the_teacher_lookup_is_the_organization_kind_then_the_port() -> None:
    session = _Session(run=_teacher_run())
    port = _Port(TeacherRunAccess("class-a", "active"))
    row = _repository(session, TEACHER, port)._owned_run(
        PRINCIPAL, RUN_ID, lock=True, teacher_capable=True
    )
    assert row["run_id"] == RUN_ID
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'ORGANIZATION'" in sql
    assert DIGEST not in sql  # the owner is the organization, never the Teacher's digest
    assert port.calls == [
        {"principal": PRINCIPAL, "organization_id": ORG, "child_id": CHILD, "lock": True}
    ]


def test_a_teacher_without_current_access_gets_the_uniform_404() -> None:
    for session, port in (
        (_Session(run=_teacher_run()), _Port(None)),  # former Teacher, org-wide, guide, ...
        (_Session(run=None), _Port(TeacherRunAccess("class-a", "active"))),  # no such run
        (_Session(run=_teacher_run()), None),  # no port composed: fail closed
        (_Session(run=_teacher_run(profile_ref=None)), _Port(None)),  # a DELETED tombstone
    ):
        with pytest.raises(ParentStoryRunError) as caught:
            _repository(session, TEACHER, port)._owned_run(PRINCIPAL, RUN_ID, teacher_capable=True)
        assert (caught.value.status_code, caught.value.code) == (404, "RESOURCE_NOT_FOUND")


def test_the_port_gets_no_child_for_a_tombstone() -> None:
    port = _Port(None)
    with pytest.raises(ParentStoryRunError):
        _repository(_Session(run=_teacher_run(profile_ref=None)), TEACHER, port)._owned_run(
            PRINCIPAL, RUN_ID, teacher_capable=True
        )
    assert port.calls[0]["child_id"] is None


def test_a_method_that_is_not_teacher_capable_never_reaches_the_database() -> None:
    session = _Session(run=_teacher_run())
    port = _Port(TeacherRunAccess("class-a", "active"))
    with pytest.raises(ParentStoryRunError) as caught:
        _repository(session, TEACHER, port)._owned_run(PRINCIPAL, RUN_ID)
    assert caught.value.status_code == 404
    assert session.statements == [] and port.calls == []


@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_read_only_class_allows_reads_and_refuses_writes_with_409(class_state: str) -> None:
    access = TeacherRunAccess("class-a", class_state)
    read_session = _Session(run=_teacher_run())
    row = _repository(read_session, TEACHER, _Port(access))._owned_run(
        PRINCIPAL, RUN_ID, teacher_capable=True
    )
    assert row["run_id"] == RUN_ID and read_session.rollbacks == 0
    write_session = _Session(run=_teacher_run())
    with pytest.raises(ParentStoryRunError) as caught:
        _repository(write_session, TEACHER, _Port(access))._owned_run(
            PRINCIPAL, RUN_ID, lock=True, teacher_capable=True, write=True
        )
    assert (caught.value.status_code, caught.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert write_session.rollbacks == 1  # the run lock is released


def test_the_read_only_class_refusal_releases_the_run_lock_and_passes_the_others() -> None:
    session = _Session(run=_teacher_run())
    repository = _repository(session, TEACHER, _Port(TeacherRunAccess("class-a", "suspended")))
    with pytest.raises(ParentStoryRunError) as caught:
        repository._refuse_read_only_class(TeacherRunAccess("class-a", "suspended"))
    assert (caught.value.status_code, caught.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert session.rollbacks == 1
    repository._refuse_read_only_class(TeacherRunAccess("class-a", "active"))
    repository._refuse_read_only_class(None)  # a Parent run has no class state
    assert session.rollbacks == 1


def test_an_active_class_allows_a_teacher_write() -> None:
    port = _Port(TeacherRunAccess("a", "active"))
    row = _repository(_Session(run=_teacher_run()), TEACHER, port)._owned_run(
        PRINCIPAL, RUN_ID, lock=True, teacher_capable=True, write=True
    )
    assert row["run_id"] == RUN_ID


# ------------------------------------------- command scope (receipts) and the purged replay
def test_a_teacher_receipt_lookup_uses_the_organization_kind_and_the_principal_digest() -> None:
    receipt = {
        "request_fingerprint_sha256": "f" * 64,
        "resource_ref": RUN_ID,
        "response_body": {},
    }
    session = _Session(receipt=receipt, scalar="DELETE_PENDING")
    found = _repository(session, TEACHER)._find_idempotency_receipt(
        principal=PRINCIPAL,
        operation="CONFIRM_CONTEXT",
        scope_kind="STORY_RUN",
        scope_ref=RUN_ID,
        key_hash="k" * 64,
        fingerprint="0" * 64,  # a different payload on the same key
    )
    # DTR 6.5 A-3: the receipt of a purged run is replayed without the fingerprint check.
    assert found is not None and found["resource_ref"] == RUN_ID
    receipt_sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'ORGANIZATION'" in receipt_sql
    assert f"actor_scope_ref = '{DIGEST}'" in receipt_sql


def test_the_purged_run_check_uses_the_run_owner_predicate_not_the_principal_digest() -> None:
    session = _Session(scalar="DELETE_PENDING")
    assert _repository(session, TEACHER)._receipt_run_purged(
        PRINCIPAL,
        {"resource_ref": RUN_ID},  # type: ignore[arg-type]
    )
    sql = _sql(session.statements[0])
    assert "actor_scope_kind = 'ORGANIZATION'" in sql
    assert DIGEST not in sql  # the Teacher run's ref is the organization id
    parent_session = _Session(scalar="DELETE_PENDING")
    assert _repository(parent_session)._receipt_run_purged(
        PRINCIPAL,
        {"resource_ref": RUN_ID},  # type: ignore[arg-type]
    )
    parent_sql = _sql(parent_session.statements[0])
    assert "actor_scope_kind = 'PARENT_ACCOUNT'" in parent_sql and DIGEST in parent_sql
    live = _Session(scalar="SCRIPT_REVIEW")
    assert not _repository(live, TEACHER)._receipt_run_purged(
        PRINCIPAL,
        {"resource_ref": RUN_ID},  # type: ignore[arg-type]
    )
    assert not _repository(_Session(), TEACHER)._receipt_run_purged(
        PRINCIPAL,
        {"resource_ref": None},  # type: ignore[arg-type]
    )


def test_a_teacher_with_a_changed_payload_on_a_live_run_is_the_400() -> None:
    receipt = {"request_fingerprint_sha256": "f" * 64, "resource_ref": RUN_ID}
    session = _Session(receipt=receipt, scalar="SCRIPT_REVIEW")
    with pytest.raises(ParentStoryRunError) as caught:
        _repository(session, TEACHER)._find_idempotency_receipt(
            principal=PRINCIPAL,
            operation="CONFIRM_CONTEXT",
            scope_kind="STORY_RUN",
            scope_ref=RUN_ID,
            key_hash="k" * 64,
            fingerprint="0" * 64,
        )
    assert (caught.value.status_code, caught.value.code) == (400, "INVALID_IDEMPOTENCY_KEY")


def test_the_command_scope_of_each_actor() -> None:
    assert _repository(_Session())._command_scope(PRINCIPAL) == ("PARENT_ACCOUNT", DIGEST)
    assert _repository(_Session(), PARENT)._command_scope(PRINCIPAL) == ("PARENT_ACCOUNT", DIGEST)
    assert _repository(_Session(), TEACHER)._command_scope(PRINCIPAL) == ("ORGANIZATION", DIGEST)
    other = VerifiedPrincipal("adult-2", ISSUER, frozenset())
    # one key, two actors: the receipt scope differs per principal
    assert _repository(_Session(), TEACHER)._command_scope(other)[1] != DIGEST


def test_a_stored_teacher_receipt_carries_the_organization_command_scope() -> None:
    session = _Session()
    _repository(session, TEACHER)._store_idempotency_receipt(
        principal=PRINCIPAL,
        operation="CONFIRM_CONTEXT",
        scope_kind="STORY_RUN",
        scope_ref=RUN_ID,
        key_hash="k" * 64,
        fingerprint="f" * 64,
        run_id=RUN_ID,
        resource_version=2,
        response_body={},
        now=datetime.now(UTC),
        response_status=200,
    )
    params = session.statements[0].compile(dialect=_DIALECT).params
    assert params["actor_scope_kind"] == "ORGANIZATION"
    assert params["actor_scope_ref"] == DIGEST


# --------------------------------------------------------------------------- fail closed
def test_the_parent_only_methods_answer_404_for_a_teacher_before_any_read() -> None:
    session = _Session()
    repository = _repository(session, TEACHER, _Port(TeacherRunAccess("a", "active")))
    calls = (
        lambda: repository.list_runs(principal=PRINCIPAL, profile_id=None, limit=1, after=None),
        lambda: repository.get_active_run(principal=PRINCIPAL, account_id="account-1"),
        lambda: repository.ensure_accepting_audio(principal=PRINCIPAL, run_id=RUN_ID),
        lambda: repository.replay_create_run(
            principal=PRINCIPAL,
            account_id="account-1",
            parent_profile_id=uuid4(),
            idempotency_key="k",
            topic="t",
            adult_confirmed_idea="i",
        ),
    )
    for call in calls:
        with pytest.raises(ParentStoryRunError) as caught:
            call()
        assert (caught.value.status_code, caught.value.code) == (404, "RESOURCE_NOT_FOUND")
    assert session.statements == []


# -------------------------------------------------- the typed profile ref (T-4a1-DEC-7)
def test_a_non_uuid_profile_ref_is_a_non_retryable_409_for_a_teacher_never_a_500() -> None:
    run = {"profile_ref": "synthetic-1f2e3d4c"}
    row = {"source_profile_revision_ref": str(uuid4())}
    with pytest.raises(ParentStoryRunError) as caught:
        _repository(_Session(), TEACHER)._typed_profile_refs(run, row)
    assert (caught.value.status_code, caught.value.code) == (409, "INVALID_STATE_TRANSITION")
    # a Parent run keeps the old behaviour (its ref is always a UUID)
    with pytest.raises(ValueError):
        _repository(_Session())._typed_profile_refs(run, row)
    profile_id, revision_id = _repository(_Session(), TEACHER)._typed_profile_refs(
        {"profile_ref": CHILD}, row
    )
    assert str(profile_id) == CHILD and str(revision_id) == row["source_profile_revision_ref"]


# ------------------------------------------------------------------ the access adapter's SQL
def test_the_access_query_reads_only_be1_tables_and_locks_the_assignment_for_share() -> None:
    captured: list[Any] = []

    class _Executed:
        def first(self) -> Any:
            return ("class-a", "suspended")

    class _CaptureSession:
        def execute(self, statement: Any) -> _Executed:
            captured.append(statement)
            return _Executed()

    adapter = SqlTeacherRunAccess(_CaptureSession())  # type: ignore[arg-type]
    access = adapter.resolve(principal=PRINCIPAL, organization_id=ORG, child_id=CHILD, lock=True)
    assert access == TeacherRunAccess("class-a", "suspended")
    sql = _sql(captured[0])
    for table in (
        "be1_managed_profiles",
        "be1_classrooms",
        "be1_organization_assignments",
        "be1_adult_identities",
    ):
        assert table in sql
    assert "story." not in sql
    assert "role = 'teacher'" in sql and "IS true" in sql
    assert "FOR SHARE OF be1_organization_assignments" in sql
    unlocked = adapter.resolve(principal=PRINCIPAL, organization_id=ORG, child_id=CHILD, lock=False)
    assert unlocked is not None and "FOR SHARE" not in _sql(captured[1])
    # no child, no organization: no query at all
    no_child = adapter.resolve(principal=PRINCIPAL, organization_id=ORG, child_id=None, lock=False)
    assert no_child is None
    assert len(captured) == 2


# -------------------------------------------------------------------------- the site table
_SOURCE = Path(repository_module.__file__).read_text(encoding="utf-8")

# Every function that reads ``_OWNER_SCOPE_KIND`` or ``_principal_scope_ref`` declares its role
# (plan review T4A1-01). A new site without a declaration fails this test, so nobody can add an
# owner or command scope literal the Teacher treatment silently misses.
SITE_ROLES = {
    "_owner_clauses": "OWNER_PREDICATE",
    "_command_scope": "COMMAND_SCOPE",
    "confirm_context": "ACTOR_STAMP",
    "create_run": "PARENT_ONLY",
    "list_runs": "PARENT_ONLY",
    "get_active_run": "PARENT_ONLY",
    "_story_generation_basis": "PARENT_ONLY",
    "reserve_story_rewrite": "PARENT_ONLY",
    "fail_story_revision": "PARENT_ONLY",
    "_rewrite_attempts_used": "PARENT_ONLY",
    "confirm_transcript": "PARENT_ONLY",
    # T-13a: the lifecycle commands run for a Teacher too; the owner scope comes from the run row
    "_accept_lifecycle_command": "LIFECYCLE_OWNER_ROW",
    "write_story_task_audit": "PARENT_ONLY",
    "attach_artwork": "ASSET_FAIL_CLOSED",
    "attach_uploaded_drawing": "ASSET_FAIL_CLOSED",
}
TEACHER_CAPABLE = {
    "get_run",
    "confirm_context",
    "confirm_subject",
    "confirm_story_revision",
    "_accept_lifecycle_command",
}


def _scope_sites() -> dict[str, set[str]]:
    sites: dict[str, set[str]] = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Name(self, node: ast.Name) -> None:
            if node.id in {"_OWNER_SCOPE_KIND", "_principal_scope_ref"} and isinstance(
                node.ctx, ast.Load
            ):
                sites.setdefault(self.stack[-1] if self.stack else "<module>", set()).add(node.id)

    Visitor().visit(ast.parse(_SOURCE))
    return sites


def test_every_owner_or_command_scope_site_has_a_declared_role() -> None:
    assert set(_scope_sites()) == set(SITE_ROLES)
    assert set(SITE_ROLES.values()) <= {
        "OWNER_PREDICATE",
        "COMMAND_SCOPE",
        "ACTOR_STAMP",
        "PARENT_ONLY",
        "LIFECYCLE_OWNER_ROW",
        "ASSET_FAIL_CLOSED",
    }


def _function_source(name: str) -> str:
    for node in ast.walk(ast.parse(_SOURCE)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(_SOURCE, node) or ""
    raise AssertionError(name)


def test_the_helpers_are_the_only_readers_of_the_two_scopes_in_the_teacher_paths() -> None:
    # receipts and review decisions go through the command scope; the run lookup through the owner
    for name in (
        "_find_idempotency_receipt",
        "_store_idempotency_receipt",
        "_store_pending_idempotency_receipt",
        "confirm_subject",
        "confirm_story_revision",
    ):
        assert "self._command_scope(" in _function_source(name), name
    for name in ("_owned_run_access", "_receipt_run_purged"):
        assert "self._owner_clauses(" in _function_source(name), name
    for name in ("_find_idempotency_receipt", "_store_idempotency_receipt", "_owned_run_access"):
        assert "_OWNER_SCOPE_KIND" not in _function_source(name), name


def test_only_the_run_read_and_the_three_confirmations_are_teacher_capable() -> None:
    capable: set[str] = set()
    for function in ast.walk(ast.parse(_SOURCE)):
        if not isinstance(function, ast.FunctionDef):
            continue
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"_owned_run", "_owned_run_access"}
                and any(
                    keyword.arg == "teacher_capable"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords
                )
            ):
                capable.add(function.name)
    assert capable == TEACHER_CAPABLE
    # the class state is refused exactly where a state changes, and AFTER the replay lookup
    # (SRS l.1697; T4A1-I-06): the helper follows the replay lookup in the three confirmations
    for name in ("confirm_context", "confirm_subject", "confirm_story_revision"):
        source = _function_source(name)
        assert "write=True" not in source, name
        assert "_refuse_read_only_class(access)" in source, name
        assert source.index("_find_idempotency_receipt(") < source.index(
            "_refuse_read_only_class(access)"
        ), name
    assert "_refuse_read_only_class" not in _function_source("get_run")
