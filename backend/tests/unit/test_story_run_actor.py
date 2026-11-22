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
    # a fixture row has no occurrence pin: the port gets ``occurrence_ref`` None and the child rule
    assert port.calls == [
        {
            "principal": PRINCIPAL,
            "organization_id": ORG,
            "child_id": CHILD,
            "lock": True,
            "occurrence_ref": None,
        }
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
        # T-4b3a: the upload-accepting checks are Teacher steps now; the legacy artwork writer is
        # not (a Teacher drawing arrives through ``attach_uploaded_drawing``)
        lambda: repository.attach_artwork(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            original_asset_ref="k",
            original_sha256="a" * 64,
            original_media_type="image/png",
            original_size_bytes=1,
            derived_asset_ref="d",
            derived_sha256="b" * 64,
            derived_size_bytes=1,
            scanner_name="s",
            scanner_version="1",
        ),
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


# ---------------------------------- the typed profile ref (T-4a1-DEC-7 retired by T-4b2 D10)
def test_the_parent_view_still_types_the_profile_ref_and_the_teacher_view_never_calls_it() -> None:
    run = {"profile_ref": "synthetic-1f2e3d4c"}
    row = {"source_profile_revision_ref": str(uuid4())}
    # the Parent helper keeps its old behaviour for every actor: a non-UUID ref is an error ...
    with pytest.raises(ValueError):
        _repository(_Session())._typed_profile_refs(run, row)
    profile_id, revision_id = _repository(_Session())._typed_profile_refs(
        {"profile_ref": CHILD}, row
    )
    assert str(profile_id) == CHILD and str(revision_id) == row["source_profile_revision_ref"]
    # ... and the Teacher branch of ``get_run`` builds the string-typed Teacher record instead
    source = _function_source("_read_run_view")
    teacher_branch = source[source.index("if self._is_teacher:") :]
    assert "TeacherStoryRunRecord(" in teacher_branch
    assert teacher_branch.index("TeacherStoryRunRecord(") < teacher_branch.index(
        "_typed_profile_refs("
    )


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
    # T-4b3a: the SUBJECT decision lookup, the attempt count and the audit writer follow the
    # command KIND (a Teacher run counts by kind, the Parent by its own scope)
    "_story_generation_basis": "BY_KIND",
    "reserve_story_rewrite": "TEACHER_STEP",
    "fail_story_revision": "JOB_SIDE",
    "_rewrite_attempts_used": "BY_KIND",
    "confirm_transcript": "TEACHER_STEP",
    # T-13a: the lifecycle commands run for a Teacher too; the owner scope comes from the run row
    "_accept_lifecycle_command": "LIFECYCLE_OWNER_ROW",
    "write_story_task_audit": "BY_KIND",
    "attach_artwork": "ASSET_FAIL_CLOSED",
    # T-4b3a D4: the Core rows of a run take their owner triple from one helper
    "_asset_owner": "ASSET_OWNER_TRIPLE",
}
# The methods that find a run for a Teacher (``teacher_capable=True``), the T-4b3a input steps among
# them (``pinned=True``), and the methods a job-side repository may run (``job_side_ok=True``).
TEACHER_CAPABLE_T4A1 = {
    "_read_run_view",
    "confirm_context",
    "confirm_subject",
    "confirm_story_revision",
    "_accept_lifecycle_command",
}
TEACHER_STEP = {
    "ensure_accepting_artwork",
    "ensure_accepting_audio",
    "prepare_drawing_attach",
    "attach_uploaded_drawing",
    "prepare_idea",
    "submit_idea",
    "get_transcript",
    "confirm_transcript",
    "reserve_story_rewrite",
    "asset_owner",
}
TEACHER_CAPABLE = TEACHER_CAPABLE_T4A1 | TEACHER_STEP
JOB_SIDE = {
    "read_current_input",
    "start_drawing_analysis",
    "fail_drawing_analysis_recoverable",
    "record_understanding",
    "read_subject_rerun_hint",
    "start_story_generation",
    "complete_story_revision",
    "fail_story_revision",
    "fail_drawing_analysis",
    "read_pending_transcription",
    "_finish_transcript",
}
# JOB_SIDE methods that take the run row from their caller and look nothing up
JOB_SIDE_NO_LOOKUP = {"recover_failed_rewrite", "settle_run_state"}
PARENT_ONLY_LOOKUP = {"attach_artwork", "reserve_story_revision"}


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
        "ASSET_OWNER_TRIPLE",
        "BY_KIND",
        "TEACHER_STEP",
        "JOB_SIDE",
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


def _lookup_sites(keyword: str) -> set[str]:
    """The functions that pass ``keyword=True`` to ``_owned_run`` or ``_owned_run_access``."""

    found: set[str] = set()
    for function in ast.walk(ast.parse(_SOURCE)):
        if not isinstance(function, ast.FunctionDef):
            continue
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"_owned_run", "_owned_run_access"}
                and any(
                    kw.arg == keyword
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                    for kw in node.keywords
                )
            ):
                found.add(function.name)
    return found


def test_the_teacher_capable_sites_are_the_closed_list() -> None:
    # T-4b3a (plan review P3-7c): the old list of the run read and the three confirmations is now
    # the T-4a1 set plus the ten input steps; any other method that finds a run for a Teacher
    # fails this test.
    assert _lookup_sites("teacher_capable") == TEACHER_CAPABLE
    # the class state is refused exactly where a state changes, and AFTER the replay lookup
    # (SRS l.1697; T4A1-I-06): the helper follows the replay lookup in each writing step
    for name in (
        "confirm_context",
        "confirm_subject",
        "confirm_story_revision",
        "prepare_drawing_attach",
        "attach_uploaded_drawing",
        "prepare_idea",
        "submit_idea",
        "confirm_transcript",
        "reserve_story_rewrite",
    ):
        source = _function_source(name)
        assert "write=True" not in source, name
        assert "_refuse_read_only_class(access)" in source, name
        assert source.index("_find_idempotency_receipt(") < source.index(
            "_refuse_read_only_class(access)"
        ), name
    # the reads keep working in a read-only class; the two upload checks have no replay and ask
    # for an active class in the lookup itself
    assert "_refuse_read_only_class" not in _function_source("_read_run_view")
    assert "_refuse_read_only_class" not in _function_source("get_transcript")
    for name in ("ensure_accepting_artwork", "ensure_accepting_audio"):
        assert "write=True" in _function_source(name), name


def test_the_pinned_sites_are_exactly_the_t4b3a_steps() -> None:
    assert _lookup_sites("pinned") == TEACHER_STEP
    assert not _lookup_sites("pinned") & {
        "_read_run_view",
        "confirm_context",
        "confirm_subject",
        "confirm_story_revision",
    }


def test_the_job_side_sites_are_the_closed_list_and_no_other_method_accepts_it() -> None:
    assert _lookup_sites("job_side_ok") == JOB_SIDE
    # no method of the two other roles accepts a job-side repository
    assert not (_lookup_sites("job_side_ok") & (TEACHER_STEP | PARENT_ONLY_LOOKUP))
    # the two methods that take the run row from their caller look nothing up
    for name in JOB_SIDE_NO_LOOKUP:
        source = _function_source(name)
        assert "_owned_run" not in source, name
    # the job-side lookup is one function that needs an organization and the pin (D6)
    lookup = _function_source("_job_side_run")
    assert "not job_side_ok" in lookup and "not organization" in lookup
    assert "occurrence_ref.is_not(None)" in lookup
    assert "actor_scope_ref == organization" in lookup
    # and it never reads the assignment
    assert "_teacher_run_access" not in lookup and "teacher_access" not in lookup


def test_a_non_job_method_under_job_side_and_a_missing_or_wrong_organization_are_404() -> None:
    for organization in (None, ""):
        session = _Session(run=_teacher_run(occurrence_ref="occ-1"))
        repository = SqlParentStoryRunRepository(
            session,  # type: ignore[arg-type]
            actor=TEACHER,
            job_side=True,
            job_side_organization=organization,
        )
        with pytest.raises(ParentStoryRunError) as caught:
            repository._owned_run(PRINCIPAL, RUN_ID, job_side_ok=True)
        assert caught.value.status_code == 404
        assert session.statements == []
    # a method that is not marked job-side is refused before any read
    session = _Session(run=_teacher_run(occurrence_ref="occ-1"))
    repository = SqlParentStoryRunRepository(
        session,  # type: ignore[arg-type]
        actor=TEACHER,
        job_side=True,
        job_side_organization=ORG,
    )
    for call in (
        lambda: repository._owned_run(PRINCIPAL, RUN_ID),
        lambda: repository._owned_run(PRINCIPAL, RUN_ID, teacher_capable=True),
        lambda: repository.get_run(principal=PRINCIPAL, run_id=RUN_ID),
        lambda: repository.get_transcript(principal=PRINCIPAL, run_id=RUN_ID),
        lambda: repository.confirm_transcript(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            idempotency_key="k",
            expected_transcript_revision=1,
            transcript_sha256="a" * 64,
        ),
    ):
        with pytest.raises(ParentStoryRunError) as caught:
            call()
        assert (caught.value.status_code, caught.value.code) == (404, "RESOURCE_NOT_FOUND")
    assert session.statements == []


def test_the_job_side_lookup_is_by_id_kind_pin_and_organization_with_no_assignment_read() -> None:
    session = _Session(run=_teacher_run(occurrence_ref="occ-1"))
    repository = SqlParentStoryRunRepository(
        session,  # type: ignore[arg-type]
        actor=TEACHER,
        job_side=True,
        job_side_organization=ORG,
    )
    row = repository._owned_run(PRINCIPAL, RUN_ID, lock=True, job_side_ok=True)
    assert row["run_id"] == RUN_ID
    assert len(session.statements) == 1
    sql = _sql(session.statements[0])
    assert f"run_id = '{RUN_ID}'" in sql
    assert "actor_scope_kind = 'ORGANIZATION'" in sql
    assert f"actor_scope_ref = '{ORG}'" in sql
    assert "occurrence_ref IS NOT NULL" in sql
    assert "FOR UPDATE" in sql
    assert DIGEST not in sql
    # a run of another organization (or no run) is the uniform 404
    empty = _Session(run=None)
    with pytest.raises(ParentStoryRunError) as caught:
        SqlParentStoryRunRepository(
            empty,  # type: ignore[arg-type]
            actor=TEACHER,
            job_side=True,
            job_side_organization="org-other",
        )._owned_run(PRINCIPAL, RUN_ID, job_side_ok=True)
    assert caught.value.status_code == 404
    assert "actor_scope_ref = 'org-other'" in _sql(empty.statements[0])
    # a job-side repository without a Teacher actor finds nothing either
    no_actor = _Session(run=_teacher_run(occurrence_ref="occ-1"))
    with pytest.raises(ParentStoryRunError):
        SqlParentStoryRunRepository(
            no_actor,  # type: ignore[arg-type]
            job_side=True,
            job_side_organization=ORG,
        )._owned_run(PRINCIPAL, RUN_ID, job_side_ok=True)
    assert no_actor.statements == []


def test_the_pinned_flag_adds_the_occurrence_predicate_for_a_teacher_only() -> None:
    teacher = _Session(run=_teacher_run(occurrence_ref="occ-1"))
    port = _Port(TeacherRunAccess("class-a", "active"))
    _repository(teacher, TEACHER, port)._owned_run(
        PRINCIPAL, RUN_ID, teacher_capable=True, pinned=True
    )
    assert "occurrence_ref IS NOT NULL" in _sql(teacher.statements[0])
    assert port.calls[0]["occurrence_ref"] == "occ-1"
    unpinned = _Session(run=_teacher_run())
    _repository(unpinned, TEACHER, _Port(TeacherRunAccess("class-a", "active")))._owned_run(
        PRINCIPAL, RUN_ID, teacher_capable=True
    )
    assert "occurrence_ref IS NOT NULL" not in _sql(unpinned.statements[0])
    # a Parent is never narrowed by the flag
    parent = _Session(run=_teacher_run())
    _repository(parent)._owned_run(PRINCIPAL, RUN_ID, pinned=True)
    assert "occurrence_ref IS NOT NULL" not in _sql(parent.statements[0])
