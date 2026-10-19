"""Immutable assignments and exact execution proofs. Actual owners authenticate facts."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import NoReturn

from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    VideoError,
    canonical_digest,
    require_hash,
    require_id,
    require_revision,
    require_time,
)


def fail(code: str) -> NoReturn:
    raise VideoError("ACTIVITY_" + code)


def text(value: str, maximum: int = 2000) -> None:
    if type(value) is not str or not value.strip() or len(value) > maximum:
        fail("INVALID_TEXT")


def exact(value: ExactRef) -> None:
    if type(value) is not ExactRef:
        fail("INVALID_REF")
    replace(value)


def ids(values: tuple[str, ...], *, nonempty: bool = False) -> None:
    if (
        type(values) is not tuple
        or len(values) > 64
        or len(set(values)) != len(values)
        or (nonempty and not values)
    ):
        fail("INVALID_IDS")
    for value in values:
        require_id(value)


def material(value: object) -> object:
    """Typed native canonical tree; no provider JSON/type names or inferred authority."""
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [material(item) for item in value]
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) in TYPES and is_dataclass(value):
        return {field.name: material(getattr(value, field.name)) for field in fields(value)}
    fail("INVALID_MATERIAL")


def digest(value: object) -> str:
    return canonical_digest({"schema": "BE2-11.Native/0.1-candidate", "value": material(value)})


class State(StrEnum):
    PROPOSED = "proposed"
    SELECTED = "teacher_selected"
    PREPARATION = "preparation_required"
    READY = "ready"
    RUNNING = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    INTERRUPTED = "interrupted"


class Action(StrEnum):
    SELECT = "select"
    CONFIRM = "confirm_ready"
    START = "start"
    FINISH = "finish"
    SKIP = "skip"
    INTERRUPT = "interrupt"


PRESTART = frozenset({State.PROPOSED, State.SELECTED, State.PREPARATION, State.READY})
TERMINAL = frozenset({State.COMPLETED, State.SKIPPED, State.INTERRUPTED})


@dataclass(frozen=True, slots=True)
class ChildAge:
    child_id: str
    age_months: int

    def __post_init__(self) -> None:
        require_id(self.child_id)
        require_revision(self.age_months, minimum=0)


@dataclass(frozen=True, slots=True)
class Audience:
    session_id: str
    revision: int
    group_ids: tuple[str, ...]
    children: tuple[ChildAge, ...]

    def __post_init__(self) -> None:
        require_id(self.session_id)
        require_revision(self.revision, minimum=0)
        ids(self.group_ids)
        if type(self.children) is not tuple or not 1 <= len(self.children) <= 64:
            fail("INVALID_AUDIENCE")
        for child in self.children:
            if type(child) is not ChildAge:
                fail("INVALID_AUDIENCE")
            replace(child)
        ids(tuple(c.child_id for c in self.children), nonempty=True)
        object.__setattr__(self, "group_ids", tuple(sorted(self.group_ids)))
        object.__setattr__(self, "children", tuple(sorted(self.children, key=lambda c: c.child_id)))


@dataclass(frozen=True, slots=True)
class Definition:
    source_ref: ExactRef
    definition_ref: ExactRef
    objective_refs: tuple[ExactRef, ...]
    title: str
    topic_ids: tuple[str, ...]
    age_min_months: int
    age_max_months: int
    materials: tuple[str, ...]
    instructions: str
    safety: str
    duration_note: str
    form: str
    observation_prompts: tuple[str, ...]

    def __post_init__(self) -> None:
        for ref in (self.source_ref, self.definition_ref):
            exact(ref)
        if type(self.objective_refs) is not tuple or not 1 <= len(self.objective_refs) <= 64:
            fail("INVALID_OBJECTIVES")
        for ref in self.objective_refs:
            exact(ref)
        if len({(r.ref, r.version) for r in self.objective_refs}) != len(self.objective_refs):
            fail("INVALID_OBJECTIVES")
        ids(self.topic_ids, nonempty=True)
        for value in (self.title, self.instructions, self.safety, self.duration_note, self.form):
            text(value)
        for values in (self.materials, self.observation_prompts):
            if type(values) is not tuple or len(values) > 64:
                fail("INVALID_DEFINITION")
            for value in values:
                text(value)
        for revision in (self.age_min_months, self.age_max_months):
            require_revision(revision, minimum=0)
        if self.age_min_months > self.age_max_months:
            fail("INVALID_AGE_RANGE")


@dataclass(frozen=True, slots=True)
class Adaptations:
    instructions: str | None = None
    materials: tuple[str, ...] | None = None
    duration_note: str | None = None
    safety_note: str | None = None

    def __post_init__(self) -> None:
        for value in (self.instructions, self.duration_note, self.safety_note):
            if value is not None:
                text(value)
        if self.materials is not None:
            if type(self.materials) is not tuple or len(self.materials) > 64:
                fail("INVALID_ADAPTATION")
            for value in self.materials:
                text(value)


def effective(source: Definition, edits: Adaptations) -> Definition:
    source, edits = replace(source), replace(edits)
    return replace(
        source,
        instructions=edits.instructions if edits.instructions is not None else source.instructions,
        materials=edits.materials if edits.materials is not None else source.materials,
        duration_note=edits.duration_note
        if edits.duration_note is not None
        else source.duration_note,
        safety=edits.safety_note if edits.safety_note is not None else source.safety,
    )


@dataclass(frozen=True, slots=True)
class Confirmation:
    materials_available: bool
    safety_checked: bool
    note: str | None = None

    def __post_init__(self) -> None:
        if type(self.materials_available) is not bool or type(self.safety_checked) is not bool:
            fail("INVALID_CONFIRMATION")
        if self.note is not None:
            text(self.note, 200)


@dataclass(frozen=True, slots=True)
class ExecutionProof:
    binding_digest: str
    policy: ExactRef
    child_ids: tuple[str, ...]
    adaptation_review: ExactRef

    def __post_init__(self) -> None:
        require_hash(self.binding_digest)
        exact(self.policy)
        exact(self.adaptation_review)
        ids(self.child_ids, nonempty=True)
        object.__setattr__(self, "child_ids", tuple(sorted(self.child_ids)))


@dataclass(frozen=True, slots=True)
class Assignment:
    assignment_id: str
    organization_id: str
    selected_by: str
    revision: int
    source: Definition
    edits: Adaptations
    audience: Audience
    policy: ExactRef
    state: State
    created_at: datetime
    updated_at: datetime
    confirmation: Confirmation | None = None
    proof: ExecutionProof | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    reason: str | None = None
    evidence_refs: tuple[ExactRef, ...] = ()
    invalidated: str | None = None

    def __post_init__(self) -> None:
        for value in (self.assignment_id, self.organization_id, self.selected_by):
            require_id(value)
        require_revision(self.revision)
        for obj, cls in (
            (self.source, Definition),
            (self.edits, Adaptations),
            (self.audience, Audience),
        ):
            if type(obj) is not cls:
                fail("INVALID_ASSIGNMENT")
            replace(obj)
        exact(self.policy)
        for time in (self.created_at, self.updated_at):
            require_time(time)
        if type(self.state) is not State or self.updated_at < self.created_at:
            fail("INVALID_ASSIGNMENT")
        for optional, optional_cls in (
            (self.confirmation, Confirmation),
            (self.proof, ExecutionProof),
        ):
            if optional is not None:
                if type(optional) is not optional_cls:
                    fail("INVALID_PREPARATION")
                replace(optional)
        if (self.confirmation is None) != (self.proof is None):
            fail("INVALID_PREPARATION")
        if self.confirmation is not None:
            if not self.confirmation.materials_available or not self.confirmation.safety_checked:
                fail("NOT_READY")
            if (
                self.proof is None
                or self.proof.binding_digest != self.binding_digest()
                or (
                    self.proof.policy != self.policy
                    or self.proof.child_ids
                    != tuple(child.child_id for child in self.audience.children)
                )
            ):
                fail("PREPARATION_STALE")
        if self.state in {State.READY, State.RUNNING, State.COMPLETED} and self.proof is None:
            fail("NOT_READY")
        if self.state in PRESTART and self.started_at is not None:
            fail("INVALID_TIME")
        if (
            self.state in {State.RUNNING, State.COMPLETED, State.INTERRUPTED}
            and self.started_at is None
        ):
            fail("INVALID_TIME")
        if (self.state in TERMINAL) != (self.finished_at is not None):
            fail("INVALID_TIME")
        for optional_time in (self.started_at, self.finished_at):
            if optional_time is not None:
                require_time(optional_time)
                if optional_time < self.created_at or optional_time > self.updated_at:
                    fail("INVALID_TIME")
        if (
            self.started_at is not None
            and self.finished_at is not None
            and (self.finished_at < self.started_at)
        ):
            fail("INVALID_TIME")
        if self.state in {State.SKIPPED, State.INTERRUPTED} and self.reason is None:
            fail("REASON_REQUIRED")
        if self.reason is not None:
            text(self.reason, 200)
        if type(self.evidence_refs) is not tuple or len(self.evidence_refs) > 64:
            fail("INVALID_EVIDENCE")
        for ref in self.evidence_refs:
            exact(ref)
        if self.invalidated is not None:
            require_id(self.invalidated)
            if self.state is State.READY:
                fail("PREPARATION_STALE")

    def binding_digest(self) -> str:
        return digest((self.organization_id, self.source, self.edits, self.audience, self.policy))

    def expect(self, revision: int, now: datetime) -> None:
        replace(self)
        require_revision(revision)
        require_time(now)
        if revision != self.revision:
            fail("STALE_REVISION")
        if now < self.updated_at:
            fail("INVALID_TIME")

    def reselect(
        self,
        expected: int,
        source: Definition,
        edits: Adaptations,
        audience: Audience,
        policy: ExactRef,
        now: datetime,
    ) -> Assignment:
        self.expect(expected, now)
        if self.state not in PRESTART:
            fail("INVALID_TRANSITION")
        if audience.session_id != self.audience.session_id:
            fail("SCOPE_MISMATCH")
        return replace(
            self,
            revision=self.revision + 1,
            source=source,
            edits=edits,
            audience=audience,
            policy=policy,
            state=State.PREPARATION,
            updated_at=now,
            proof=None,
            confirmation=None,
            invalidated=None,
        )

    def transition(
        self,
        action: Action,
        expected: int,
        now: datetime,
        *,
        confirmation: Confirmation | None = None,
        proof: ExecutionProof | None = None,
        reason: str | None = None,
        evidence_refs: tuple[ExactRef, ...] = (),
    ) -> Assignment:
        self.expect(expected, now)
        if type(action) is not Action:
            fail("INVALID_ACTION")
        if action in {Action.CONFIRM, Action.START}:
            if self.invalidated is not None or (
                action is Action.CONFIRM
                and self.state not in PRESTART
                or action is Action.START
                and self.state is not State.READY
            ):
                fail("INVALID_TRANSITION")
            if confirmation is None or proof is None:
                fail("NOT_READY")
            return replace(
                self,
                revision=self.revision + 1,
                updated_at=now,
                state=State.READY if action is Action.CONFIRM else State.RUNNING,
                confirmation=confirmation,
                proof=proof,
                started_at=now if action is Action.START else None,
            )
        allowed = {
            Action.FINISH: ({State.RUNNING}, State.COMPLETED),
            Action.SKIP: (PRESTART, State.SKIPPED),
            Action.INTERRUPT: ({State.RUNNING}, State.INTERRUPTED),
        }
        if action not in allowed or self.state not in allowed[action][0]:
            fail("INVALID_TRANSITION")
        if action in {Action.SKIP, Action.INTERRUPT} and reason is None:
            fail("REASON_REQUIRED")
        return replace(
            self,
            revision=self.revision + 1,
            updated_at=now,
            state=allowed[action][1],
            finished_at=now,
            reason=reason,
            evidence_refs=evidence_refs,
        )

    def invalidate(self, expected: int, cause: str, now: datetime) -> Assignment:
        self.expect(expected, now)
        require_id(cause)
        if self.state in TERMINAL:
            fail("INVALID_TRANSITION")
        # Running is NOT automatically stopped. Actual owner policy determines
        # intervention; history/status carry invalidation, no outbox-as-stop claim.
        running = self.state is State.RUNNING
        return replace(
            self,
            revision=self.revision + 1,
            updated_at=now,
            invalidated=cause,
            state=self.state if running else State.PREPARATION,
            confirmation=self.confirmation if running else None,
            proof=self.proof if running else None,
        )


TYPES = (
    ExactRef,
    ChildAge,
    Audience,
    Definition,
    Adaptations,
    Confirmation,
    ExecutionProof,
    Assignment,
)
