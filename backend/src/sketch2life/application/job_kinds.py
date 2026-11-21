"""AI job target kinds and the registry-aware status reader (FEAT-066 T0.4; SRS l.779, l.1675).

``GET /v1/jobs/{job_id}`` serves one resource shape for eight target kinds. A kind is only
readable once its producer task registers a ``job_type`` for it together with an explicit scope
rule and result eligibility; everything that is not registered answers the same not-found as a
missing id (SRS l.865), so the BE2 pilot jobs (``vision_analysis`` and others) never leak.

Fail-closed defaults (plan review R1 F-4): a spec with job types must name its own
``scope_rule`` and ``eligibility``; the module defaults deny every read and withhold every result
ref. There is deliberately no generic "organization manager may read" rule here: SRS l.1675 limits
the read to the actor of the run, and l.1602/l.1620 give a School Manager no run-content read.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.ai_jobs import AiJobRepository, ClockPort, PrincipalRole
from sketch2life.application.services.ai_jobs import JobStatusResult, render_job_status
from sketch2life.domain.ai_jobs.model import AiJob, JobPollPolicy

# SRS l.786: poll starts at 2 s and backs off to 10 s.
SRS_JOB_POLL_POLICY = JobPollPolicy(
    policy_id="srs.job_poll.v1",
    min_interval_ms=2000,
    max_interval_ms=10000,
    backoff_step_seconds=10,
    status="SRS_L786",
)


class JobTargetKind(StrEnum):
    """The exactly-one target kinds of ``AiJobStatusV1`` (SRS l.779)."""

    STORY_RUN = "STORY_RUN"
    VIDEO_GENERATION = "VIDEO_GENERATION"
    VIDEO_GENERATION_SCENE = "VIDEO_GENERATION_SCENE"
    LESSON_SOURCE_DOCUMENT = "LESSON_SOURCE_DOCUMENT"
    LESSON_LIBRARY_VERSION = "LESSON_LIBRARY_VERSION"
    LESSON_VERSION_VISUAL_ASSET = "LESSON_VERSION_VISUAL_ASSET"
    LESSON_SKETCH_DECK_REVISION = "LESSON_SKETCH_DECK_REVISION"
    PARENT_SKETCH_GUIDE = "PARENT_SKETCH_GUIDE"


@dataclass(frozen=True, slots=True)
class ActorMembership:
    """Active assignments of the actor in ONE organization (from the T0.2 scope loader)."""

    organization_id: str
    roles: frozenset[str]
    class_ids: frozenset[str]
    # Role names held per class (``class_ids`` are its keys). ``roles`` is the union over the
    # whole organization, so a rule that grants result refs must read this instead (T0.4-DEBT-1).
    class_roles: Mapping[str, frozenset[str]] = field(default_factory=dict)


MembershipLookup = Callable[[str], ActorMembership | None]


@dataclass(frozen=True, slots=True)
class JobActor:
    """Verified adult account as the job reader sees it; memberships are read lazily."""

    account_id: str
    account_role: str
    membership_for: MembershipLookup
    # SHA-256 of the canonical issuer and subject: the owner scope of a Parent StoryRun (T-1a). A
    # Parent job is proven by ``actor_scope_ref`` of its run, so it works once the run is closed.
    story_scope_ref: str | None = None


ScopeRule = Callable[[ActorMembership, AiJob], bool]
ResultEligibility = Callable[[AiJob], bool]


def deny_scope(membership: ActorMembership, job: AiJob) -> bool:
    """Default scope rule: nothing is readable until a producer defines its rule."""

    return False


def withhold_results(job: AiJob) -> bool:
    """Default eligibility: result refs are withheld (fail closed)."""

    return False


@dataclass(frozen=True, slots=True)
class JobKindSpec:
    """One target kind: the internal job types that map to it, its read rule and eligibility."""

    target_kind: JobTargetKind
    job_types: tuple[str, ...] = ()
    scope_rule: ScopeRule = deny_scope
    eligibility: ResultEligibility = withhold_results
    # True when the scope rule itself proves a per-class ``teacher`` assignment of a Teacher
    # account (the reader also requires ``account_role == teacher``): an actor the rule
    # accepts is then read as TEACHER whatever the union of organization roles says, and an actor
    # it refuses is never read (T0.4-DEBT-1: a School Manager or an observer of another class must
    # not inherit the TEACHER projection of a class they do not teach).
    rule_grants_teacher_role: bool = False

    def __post_init__(self) -> None:
        if len(set(self.job_types)) != len(self.job_types) or not all(
            isinstance(job_type, str) and job_type for job_type in self.job_types
        ):
            raise ValueError("job_types must be distinct non-empty strings")
        if self.job_types and (
            self.scope_rule is deny_scope or self.eligibility is withhold_results
        ):
            raise ValueError(
                "a kind with job types must define its own scope_rule and eligibility"
            )


class JobKindRegistry:
    """Exactly one spec per target kind; a job type maps to at most one kind."""

    def __init__(self, specs: Iterable[JobKindSpec] = ()) -> None:
        by_kind: dict[JobTargetKind, JobKindSpec] = {}
        for spec in specs:
            if spec.target_kind in by_kind:
                raise ValueError(f"duplicate spec for {spec.target_kind}")
            by_kind[spec.target_kind] = spec
        for kind in JobTargetKind:
            by_kind.setdefault(kind, JobKindSpec(kind))
        by_type: dict[str, JobKindSpec] = {}
        for spec in by_kind.values():
            for job_type in spec.job_types:
                if job_type in by_type:
                    raise ValueError(f"job type {job_type!r} is registered twice")
                by_type[job_type] = spec
        self._by_kind: Mapping[JobTargetKind, JobKindSpec] = by_kind
        self._by_type: Mapping[str, JobKindSpec] = by_type

    @property
    def specs(self) -> tuple[JobKindSpec, ...]:
        return tuple(self._by_kind[kind] for kind in JobTargetKind)

    def for_job_type(self, job_type: str) -> JobKindSpec | None:
        return self._by_type.get(job_type)


# HEAD registry: the eight kinds, no job type yet (each producer task adds its own).
DEFAULT_JOB_KIND_REGISTRY = JobKindRegistry()


# ----------------------------------------------------------------------- lesson source documents
# FEAT-066 T-3b (SRS l.779, l.1653). The extraction of an attached occurrence document is a job of
# the kind ``LESSON_SOURCE_DOCUMENT``; it is written already finished (TD-15) in the attach
# transaction. ``succeeded`` and disposition ``accepted`` mean "text extracted", never "plan
# approved": UC-04 review of the text comes later and is a separate resource.
LESSON_SOURCE_EXTRACTION_JOB_TYPE = "lesson_source_document_extraction"
TEACHER_ROLE = "teacher"


class SourceDocumentClassLookup(Protocol):
    """Which class owns the occurrence of a source document (read at poll time, short query)."""

    def class_for(self, organization_id: str, source_document_id: str) -> str | None:
        """The class id, or ``None`` when the document is unknown or in another organization."""
        ...


def lesson_source_document_spec(classes: SourceDocumentClassLookup) -> JobKindSpec:
    """Registry entry of the extraction job: readable by a Teacher assigned to the document's class.

    The rule needs the ``teacher`` role for exactly that class (``class_roles``): a guide, an
    observer, a School Manager, a Teacher of another class and anyone whose assignment was revoked
    get the uniform 404. Result refs (the revision id and text hash, no text and no child data) are
    eligible whenever the job is ``succeeded`` and ``accepted``.
    """

    def scope_rule(membership: ActorMembership, job: AiJob) -> bool:
        class_id = classes.class_for(job.organization_id, job.scope.target_id)
        return class_id is not None and TEACHER_ROLE in membership.class_roles.get(
            class_id, frozenset()
        )

    def eligibility(job: AiJob) -> bool:
        return job.job_type == LESSON_SOURCE_EXTRACTION_JOB_TYPE

    return JobKindSpec(
        JobTargetKind.LESSON_SOURCE_DOCUMENT,
        (LESSON_SOURCE_EXTRACTION_JOB_TYPE,),
        scope_rule=scope_rule,
        eligibility=eligibility,
        rule_grants_teacher_role=True,
    )


# ------------------------------------------------------------------------------ video generation
# FEAT-066 T-1a (SRS l.779, l.1670, l.1675). The video job of a Parent run is the generation row
# (D9, plan Q2: no ``ai_jobs`` row before the first real worker). It is read only through the
# Parent seam below, never through an organization membership.
VIDEO_GENERATION_JOB_TYPE = "story.video_generation"


def deny_organization_actors(membership: ActorMembership, job: AiJob) -> bool:
    """A Parent video job has no organization: no membership, role or class ever grants a read."""

    return False


def withhold_video_results(job: AiJob) -> bool:
    """Result refs stay empty: the video plays through the playback route only (SRS l.1692)."""

    return False


def video_generation_spec() -> JobKindSpec:
    return JobKindSpec(
        JobTargetKind.VIDEO_GENERATION,
        (VIDEO_GENERATION_JOB_TYPE,),
        scope_rule=deny_organization_actors,
        eligibility=withhold_video_results,
    )


def build_job_kind_registry(source_documents: SourceDocumentClassLookup) -> JobKindRegistry:
    """The production registry: the module default plus the kinds that have a producer."""
    return JobKindRegistry([lesson_source_document_spec(source_documents), video_generation_spec()])


class ParentJobScopePort(Protocol):
    """Seam for Parent-owned jobs. ``owned_job`` returns the job only when it belongs to the
    Parent actor (the actor carries ``story_scope_ref``, the owner scope of its StoryRuns); an
    implementation that owns none answers ``None``. T-1a registers the video generation producer;
    the other Parent producers add theirs through ``FirstOwnedParentJobs``."""

    def owned_job(self, actor: JobActor, job_id: str) -> AiJob | None: ...


class NoParentJobs:
    def owned_job(self, actor: JobActor, job_id: str) -> AiJob | None:
        return None


class FirstOwnedParentJobs:
    """Several Parent producers behind the one port the reader takes: the first owner wins."""

    def __init__(self, *ports: ParentJobScopePort) -> None:
        self._ports = ports

    def owned_job(self, actor: JobActor, job_id: str) -> AiJob | None:
        for port in self._ports:
            job = port.owned_job(actor, job_id)
            if job is not None:
                return job
        return None


class JobNotVisible(Exception):
    """One outcome for missing, unregistered, out-of-scope and unreadable jobs (SRS l.865)."""


@dataclass(frozen=True, slots=True)
class JobStatusRead:
    status: JobStatusResult
    target_kind: JobTargetKind
    target_ref: str
    job_type: str


# organization assignment role (be1_organization_assignments) to the projection role.
_ASSIGNMENT_PROJECTION = (
    ("teacher", PrincipalRole.TEACHER),
    ("school_admin", PrincipalRole.ADMIN),
)


class JobStatusReader:
    """Read one job on behalf of an adult actor: registry, membership, scope rule, then ETag.

    Order matters: the 404 decisions come first, the 304 decision last, so a conditional
    request is never answered before the actor is authorised.
    """

    def __init__(
        self,
        repository: AiJobRepository,
        registry: JobKindRegistry,
        clock: ClockPort,
        *,
        poll_policy: JobPollPolicy = SRS_JOB_POLL_POLICY,
        parent_jobs: ParentJobScopePort | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._clock = clock
        self._poll_policy = poll_policy
        self._parent_jobs: ParentJobScopePort = parent_jobs or NoParentJobs()

    def read(
        self, actor: JobActor, job_id: str, if_none_match: str | None = None
    ) -> JobStatusRead:
        if actor.account_role == "parent":
            return self._read_parent(actor, job_id, if_none_match)
        if actor.account_role not in {"teacher", "school_manager"}:
            raise JobNotVisible  # Platform Admin and unknown roles: fail closed (OPEN, DEC-3)
        with self._repository.transaction() as tx:
            job = tx.get_job(job_id)
        if job is None:
            raise JobNotVisible
        spec = self._registry.for_job_type(job.job_type)
        membership = actor.membership_for(job.organization_id)
        if spec is None or membership is None:
            raise JobNotVisible
        if spec.rule_grants_teacher_role:
            # A School Manager account that also teaches the class is not read as a Teacher: the
            # document routes of the same occurrence refuse that account too (T-3b-DEC-8).
            if actor.account_role != "teacher" or not spec.scope_rule(membership, job):
                raise JobNotVisible
            return self._render(job, spec, PrincipalRole.TEACHER, if_none_match)
        role = next(
            (role for name, role in _ASSIGNMENT_PROJECTION if name in membership.roles), None
        )
        if role is None or not spec.scope_rule(membership, job):
            raise JobNotVisible
        return self._render(job, spec, role, if_none_match)

    def _read_parent(
        self, actor: JobActor, job_id: str, if_none_match: str | None
    ) -> JobStatusRead:
        job = self._parent_jobs.owned_job(actor, job_id)
        spec = None if job is None else self._registry.for_job_type(job.job_type)
        if job is None or spec is None:
            raise JobNotVisible
        # Ownership is the port's decision; the Parent sees the full projection of its own job.
        return self._render(job, spec, PrincipalRole.TEACHER, if_none_match)

    def _render(
        self, job: AiJob, spec: JobKindSpec, role: PrincipalRole, if_none_match: str | None
    ) -> JobStatusRead:
        status = render_job_status(
            job,
            role,
            eligible=lambda: spec.eligibility(job),
            poll_policy=self._poll_policy,
            now=self._clock.now(),
            if_none_match=if_none_match,
        )
        return JobStatusRead(status, spec.target_kind, job.scope.target_id, job.job_type)


__all__ = [
    "DEFAULT_JOB_KIND_REGISTRY",
    "SRS_JOB_POLL_POLICY",
    "VIDEO_GENERATION_JOB_TYPE",
    "ActorMembership",
    "FirstOwnedParentJobs",
    "JobActor",
    "JobKindRegistry",
    "JobKindSpec",
    "JobNotVisible",
    "JobStatusRead",
    "JobStatusReader",
    "JobTargetKind",
    "LESSON_SOURCE_EXTRACTION_JOB_TYPE",
    "NoParentJobs",
    "ParentJobScopePort",
    "ResultEligibility",
    "ScopeRule",
    "SourceDocumentClassLookup",
    "build_job_kind_registry",
    "deny_organization_actors",
    "deny_scope",
    "lesson_source_document_spec",
    "video_generation_spec",
    "withhold_results",
    "withhold_video_results",
]
