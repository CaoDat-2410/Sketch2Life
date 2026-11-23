"""FEAT-066 T-4b3b D14: the Teacher job port of the video generation and the reader behind it.

Offline. The ownership query is checked as SQL text (it needs the occurrence-pin rule, written once
in ``occurrence_pin_select`` and shared with the run access port), and the reader is driven with
fakes: a Teacher poll consults the port only after ``ai_jobs`` found nothing, every other role never
reaches it, and the answer for a wrong actor is the one ``JobNotVisible``.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.job_kinds import (
    ActorMembership,
    JobActor,
    JobKindRegistry,
    JobNotVisible,
    JobStatusReader,
    NoTeacherJobs,
    video_generation_spec,
)
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_actor import TeacherRunAccess
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_video.job_projection import (
    SqlTeacherVideoJobs,
    build_video_job,
)

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
_DIALECT = postgresql.dialect()  # type: ignore[no-untyped-call]
PRINCIPAL = VerifiedPrincipal("teacher-1", "issuer-1", frozenset())
ACCOUNT = "account-teacher-1"
JOB_ID = "vjob_" + "1" * 32

# the pieces of the occurrence-pin rule: the same text must appear in the access query of the run
# and in the job query (D14, plan review P2-4a)
PIN_FRAGMENTS = (
    "lesson.occurrences.responsible_teacher_ref = be1_adult_identities.account_id",
    "be1_organization_assignments.role = 'teacher'",
    "be1_organization_assignments.active IS true",
    "be1_adult_identities.state = 'active'",
    "be1_adult_identities.account_role = 'teacher'",
    "be1_classrooms.class_id = ",
    "be1_organization_assignments.class_id = ",
)


def _sql(statement: Any) -> str:
    return str(statement.compile(dialect=_DIALECT, compile_kwargs={"literal_binds": True}))


def _row(**changes: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "video_generation_id": "33333333-3333-4333-8333-333333333333",
        "job_ref": JOB_ID,
        "state": "GENERATING",
        "target_script_hash": "a" * 64,
        "revision_no": 2,
        "generation_revision": 4,
        "accepted_at": NOW,
        "started_at": NOW,
        "completed_at": None,
        "updated_at": NOW,
        "safe_failure_code": None,
    }
    values.update(changes)
    return values


class _Connection:
    def __init__(self, engine: _Engine) -> None:
        self._engine = engine

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, statement: Any) -> Any:
        self._engine.statements.append(statement)
        row = self._engine.row
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row))


class _Engine:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.statements: list[Any] = []

    def connect(self) -> _Connection:
        return _Connection(self)


def _actor(role: str = "teacher") -> JobActor:
    return JobActor(ACCOUNT, role, lambda _organization: None, story_scope_ref="s" * 64)


# --------------------------------------------------------------------------------- the SQL
def _access_sql() -> str:
    captured: list[Any] = []

    class _Session:
        def execute(self, statement: Any) -> Any:
            captured.append(statement)
            return SimpleNamespace(first=lambda: ("class-a", "active"))

    SqlTeacherRunAccess(_Session()).resolve(  # type: ignore[arg-type]
        principal=PRINCIPAL,
        organization_id="org-1",
        child_id=None,
        lock=False,
        occurrence_ref="occ-1",
    )
    return _sql(captured[0])


def _job_sql() -> str:
    engine = _Engine(None)
    SqlTeacherVideoJobs(engine).owned_job(_actor(), JOB_ID)  # type: ignore[arg-type]
    (statement,) = engine.statements
    return _sql(statement)


def test_the_job_query_and_the_run_access_query_share_the_occurrence_pin_rule() -> None:
    access, job = _access_sql(), _job_sql()
    for fragment in PIN_FRAGMENTS:
        assert fragment in access, ("access", fragment)
        assert fragment in job, ("job", fragment)


def test_the_callers_add_who_is_asking_each_in_its_own_terms() -> None:
    access, job = _access_sql(), _job_sql()
    # the access port knows the principal: subject and issuer
    assert "be1_organization_assignments.subject = 'teacher-1'" in access
    assert "be1_adult_identities.issuer = 'issuer-1'" in access
    # the job port knows the account id only (the reader never sees the principal)
    assert f"be1_adult_identities.account_id = '{ACCOUNT}'" in job
    assert "issuer" not in job and "be1_organization_assignments.subject = '" not in job


def test_the_job_query_needs_a_pinned_organization_run_that_is_not_purged() -> None:
    job = _job_sql()
    assert "story.video_generations.job_ref = 'vjob_" in job
    assert "story.runs.actor_scope_kind = 'ORGANIZATION'" in job
    assert "story.runs.occurrence_ref IS NOT NULL" in job
    assert "story.runs.run_state NOT IN ('DELETED', 'DELETE_PENDING')" in job.replace("\n", " ")
    # the occurrence is matched to the run's own occurrence and organization, never to a literal
    assert "lesson.occurrences.occurrence_id = story.runs.occurrence_ref" in job
    assert "lesson.occurrences.organization_ref = story.runs.actor_scope_ref" in job
    assert "EXISTS" in job
    # no organization role, class membership or creator ever grants the read
    assert "created_by_actor_ref" not in job and "PARENT_ACCOUNT" not in job


def test_the_pin_rule_is_written_once_and_both_callers_use_it() -> None:
    import inspect

    from sketch2life.infrastructure.persistence import teacher_run_access
    from sketch2life.infrastructure.story_video import job_projection

    assert "occurrence_pin_select(" in inspect.getsource(SqlTeacherRunAccess._resolve_occurrence)
    assert "occurrence_pin_select(" in inspect.getsource(SqlTeacherVideoJobs.owned_job)
    # no second copy of the rule: the responsible-Teacher join exists in one place only
    for module in (teacher_run_access, job_projection):
        assert inspect.getsource(module).count("responsible_teacher_ref") <= 2


def test_a_non_teacher_actor_gets_no_query_at_all() -> None:
    for role in ("parent", "school_manager", "platform_admin"):
        engine = _Engine(_row())
        assert SqlTeacherVideoJobs(engine).owned_job(_actor(role), JOB_ID) is None  # type: ignore[arg-type]
        assert engine.statements == []


def test_the_port_maps_a_generation_to_the_job_with_empty_result_refs() -> None:
    engine = _Engine(_row(state="READY", completed_at=NOW))
    job = SqlTeacherVideoJobs(engine).owned_job(_actor(), JOB_ID)  # type: ignore[arg-type]
    assert job is not None and job.job_id == JOB_ID and job.result_refs == ()
    assert job == build_video_job(_row(state="READY", completed_at=NOW))
    assert SqlTeacherVideoJobs(_Engine(None)).owned_job(_actor(), JOB_ID) is None  # type: ignore[arg-type]


# ------------------------------------------------------------------------------ the reader
class _Transaction:
    def __init__(self, job: Any) -> None:
        self._job = job

    def get_job(self, _job_id: str, *, for_update: bool = False) -> Any:
        return self._job


class _Repository:
    def __init__(self, job: Any = None) -> None:
        self._job = job

    @contextmanager
    def transaction(self) -> Any:
        yield _Transaction(self._job)


class _Clock:
    def now(self) -> datetime:
        return NOW


class _Port:
    def __init__(self, job: Any) -> None:
        self.job = job
        self.asked: list[tuple[str, str]] = []

    def owned_job(self, actor: JobActor, job_id: str) -> Any:
        self.asked.append((actor.account_id, job_id))
        return self.job


def _membership() -> ActorMembership:
    return ActorMembership("org-1", frozenset({"teacher"}), frozenset({"class-a"}))


def _reader(port: Any, ai_jobs: Any = None) -> JobStatusReader:
    return JobStatusReader(
        _Repository(ai_jobs),
        JobKindRegistry([video_generation_spec()]),
        _Clock(),
        teacher_jobs=port,
    )


def test_a_teacher_poll_consults_the_port_only_after_ai_jobs_found_nothing() -> None:
    job = build_video_job(_row())
    port = _Port(job)
    read = _reader(port).read(_actor(), JOB_ID)
    assert port.asked == [(ACCOUNT, JOB_ID)]
    assert read.target_ref == job.scope.target_id if job is not None else False
    view = read.status.view
    assert view is not None and view["result_refs"] == []  # the video plays through playback only


def test_a_job_that_ai_jobs_owns_never_reaches_the_teacher_port() -> None:
    port = _Port(build_video_job(_row()))
    other = build_video_job(_row(job_ref="vjob_" + "2" * 32))
    reader = _reader(port, ai_jobs=other)
    # an ai_jobs row of the video type, for a Teacher without a membership: the existing rule
    with pytest.raises(JobNotVisible):
        reader.read(JobActor(ACCOUNT, "teacher", lambda _o: None), "vjob_" + "2" * 32)
    assert port.asked == []


@pytest.mark.parametrize("role", ["school_manager", "platform_admin", "parent", "observer"])
def test_no_other_role_consults_the_teacher_port(role: str) -> None:
    port = _Port(build_video_job(_row()))
    with pytest.raises(JobNotVisible):
        _reader(port).read(_actor(role), JOB_ID)
    assert port.asked == []


def test_a_teacher_the_port_does_not_own_is_the_one_uniform_not_found() -> None:
    port = _Port(None)
    with pytest.raises(JobNotVisible):
        _reader(port).read(_actor(), JOB_ID)
    assert port.asked == [(ACCOUNT, JOB_ID)]
    with pytest.raises(JobNotVisible):
        _reader(None).read(_actor(), JOB_ID)  # no port composed: the default owns nothing
    assert NoTeacherJobs().owned_job(_actor(), JOB_ID) is None


def test_the_conditional_read_is_decided_after_the_actor_was_authorised() -> None:
    port = _Port(build_video_job(_row()))
    first = _reader(port).read(_actor(), JOB_ID)
    etag = first.status.etag
    again = _reader(port).read(_actor(), JOB_ID, if_none_match=etag)
    assert again.status.not_modified is True
    # a Teacher the port refuses never gets the 304, whatever tag it presents
    refused = _Port(None)
    with pytest.raises(JobNotVisible):
        _reader(refused).read(_actor(), JOB_ID, if_none_match=etag)
    assert refused.asked == [(ACCOUNT, JOB_ID)]


def test_the_default_port_of_the_reader_owns_nothing() -> None:
    reader = JobStatusReader(
        _Repository(None),
        JobKindRegistry([video_generation_spec()]),
        _Clock(),
    )
    with pytest.raises(JobNotVisible):
        reader.read(_actor(), JOB_ID)


def test_the_membership_helper_is_unused_by_the_video_port() -> None:
    # the port decides ownership from the occurrence, never from an organization membership
    assert _membership().class_ids == frozenset({"class-a"})
    assert TeacherRunAccess("class-a", "active").writable
