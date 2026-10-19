"""Synthetic 04 -> 05 -> 06 composition using the unchanged accepted producer harness."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.services.child_response import (
    ChildResponseDependencies,
    ChildResponseService,
    ResponseCommand,
    ResponseResult,
)
from sketch2life.application.services.sketch_generation import ReviseLevelCommand
from sketch2life.contracts.schemas.child_responses import (
    ChildResponseCommandV1,
    ChildResponseProjectionV1,
    ChildResponseReadV1,
    TeacherResponseEventV1,
)
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    CLASS,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    LEVEL_2,
    ORG,
    OTHER_CLASS_TEACHER,
    SESSION,
    TEACHER,
)
from sketch2life.infrastructure.child_response.adapters import (
    DisclosureBinding,
    FixtureChildResponseAuthority,
    PublicSketchReviewAccess,
    TeacherBinding,
)
from sketch2life.infrastructure.child_response.fakes import InMemoryChildResponseStore
from sketch2life.infrastructure.sketch_review.fakes import DeviceBinding as ReviewDeviceBinding
from sketch2life.infrastructure.sketch_review.harness import (
    SketchReviewHarness,
    build_sketch_review_harness,
)


@dataclass
class ChildResponseHarness:
    review: SketchReviewHarness
    access: PublicSketchReviewAccess
    authority: FixtureChildResponseAuthority
    store: InMemoryChildResponseStore
    service: ChildResponseService
    keys: int = 0

    @property
    def repository(self) -> InMemoryChildResponseStore:
        return self.store

    def key(self) -> str:
        self.keys += 1
        return f"key_fx_be206_{self.keys:04d}"

    def pending(self, *, level: str = LEVEL_2, group: bool = False,
                unsafe: bool = False) -> str:
        return self.review.pending(level=level, group=group, unsafe=unsafe)

    def approved(self, *, level: str = LEVEL_2, group: bool = False,
                 participants: tuple[str, ...] | None = None) -> str:
        proposal_id = self.pending(level=level, group=group)
        self.review.moderate(proposal_id)
        self.review.review(proposal_id, participants=participants)
        return proposal_id

    def projection(self, proposal_id: str, principal: Principal = DEVICE_A,
                   **preconditions: Any) -> ChildResponseProjectionV1:
        return self.service.projection(principal, proposal_id, **preconditions)

    def read(self, proposal_id: str, principal: Principal = DEVICE_A, *,
             explicit_reveal: bool = False, **preconditions: Any) -> ChildResponseReadV1:
        return self.service.read(principal, proposal_id, explicit_reveal=explicit_reveal,
                                 **preconditions)

    def command(
        self, proposal_id: str, action: str = "viewed", *, principal: Principal = DEVICE_A,
        key: str | None = None, etag: str | None = "auto",
        body: ChildResponseCommandV1 | str | bytes | None = None,
        **fields: object,
    ) -> ResponseCommand:
        projection = self.projection(proposal_id, principal)
        if body is None:
            payload: dict[str, object] = {
                "action": action, "expected_proposal_version": projection.access.proposal_version,
                "review_ref": projection.access.review_ref, "turn_id": projection.turn_id,
                **fields,
            }
            body = ChildResponseCommandV1.model_validate(payload)
        return ResponseCommand(
            principal, proposal_id, key if key is not None else self.key(),
            projection.etag if etag == "auto" else etag, body)

    def respond(self, proposal_id: str, action: str = "viewed", **command: Any) -> ResponseResult:
        return self.service.record_response(self.command(proposal_id, action, **command))

    # Owner fixture publications; the production equivalents remain integration gates.
    def close_turn(self, principal: Principal = DEVICE_A) -> None:
        self.review.chain.h.authority.devices[principal.principal_id].turn_open = False

    def rebind(self, principal: Principal, participant: str, turn_id: str, *,
               canvas_id: str | None = None) -> None:
        current = self.review.chain.h.authority.devices[principal.principal_id]
        canvas_id = canvas_id or current.canvas_id
        current.participant_id, current.turn_id = participant, turn_id
        current.canvas_id, current.turn_open = canvas_id, True
        current.turn_revision = (current.turn_revision or 0) + 1
        self.review.authority.devices[principal.principal_id] = ReviewDeviceBinding(
            current.organization_id, current.session_id, participant)
        self.authority.bindings[principal.principal_id] = DisclosureBinding(
            current.organization_id, current.session_id, canvas_id, participant)

    def revoke_grant(self, principal: Principal = DEVICE_A) -> None:
        self.review.chain.h.authority.revoked.add(principal.principal_id)
        self.review.chain.h.authority.disclosure_revoked.add(principal.principal_id)
        self.authority.revoked.add(principal.principal_id)
        self.review.authority.devices.pop(principal.principal_id, None)

    def revoke_review(self, proposal_id: str) -> None:
        self.review.review(proposal_id, "reject")

    def set_session_active(self, active: bool) -> None:
        owner = self.review.chain.h.owner
        for canvas_id, canvas in tuple(owner.canvases.items()):
            owner.canvases[canvas_id] = replace(canvas, session_active=active)

    def new_version(self, proposal_id: str, level: str) -> None:
        producer = self.review.chain.proposal(proposal_id)
        self.review.chain.service.revise_level(ReviseLevelCommand(
            TEACHER, proposal_id, self.key(), producer.etag(), level))
        self.review.chain.run_sketch(proposal_id)
        self.review.moderate(proposal_id)
        self.review.review(proposal_id)

    def teacher_events(self, principal: Principal = TEACHER) -> tuple[TeacherResponseEventV1, ...]:
        return self.service.teacher_events(principal)


def build_child_response_harness(**chain_options: Any) -> ChildResponseHarness:
    review = build_sketch_review_harness(**chain_options)
    access = PublicSketchReviewAccess(review.service)
    authority = FixtureChildResponseAuthority(review.chain.h.owner, review.chain.h.authority)
    for principal in (DEVICE_A, DEVICE_GA, DEVICE_GB):
        device = review.chain.h.authority.devices[principal.principal_id]
        authority.bindings[principal.principal_id] = DisclosureBinding(
            device.organization_id, device.session_id, device.canvas_id, device.participant_id)
    authority.teachers[TEACHER.principal_id] = TeacherBinding(
        ORG, frozenset({CLASS}), frozenset({SESSION}))
    authority.teachers[OTHER_CLASS_TEACHER.principal_id] = TeacherBinding(
        ORG, frozenset({"class_fx_b"}), frozenset({SESSION}))
    store = InMemoryChildResponseStore()
    service = ChildResponseService(ChildResponseDependencies(
        access=access, authority=authority, repository=store,
        clock=review.chain.h.clock, ids=review.chain.h.ids))
    return ChildResponseHarness(review, access, authority, store, service)


__all__ = [
    "CHILD_A", "CHILD_B", "DEVICE_A", "DEVICE_GA", "DEVICE_GB", "TEACHER",
    "ChildResponseHarness", "build_child_response_harness",
]
