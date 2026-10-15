"""Framework and storage independent BE1 authorization and state policies."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from sketch2life.application.ports.identity import VerifiedPrincipal


class Be1PolicyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class AdultAssignment:
    organization_id: str
    subject: str
    class_id: str | None
    role: str
    active: bool
    assignment_id: str


class SessionAction(StrEnum):
    OPEN_LOBBY = "lobby"
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    FINISH = "finish"


class Be1RuntimePolicy:
    """Pure use-case rules shared by HTTP and future worker entry points."""

    @staticmethod
    def authorize_adult(
        *,
        principal: VerifiedPrincipal,
        identity_active: bool,
        identity_issuer: str | None,
        assignments: Iterable[AdultAssignment],
        organization_id: str,
        roles: set[str] | frozenset[str] | None = None,
        class_id: str | None = None,
    ) -> tuple[AdultAssignment, ...]:
        if not principal.subject or not principal.issuer or not identity_active:
            raise Be1PolicyError(
                "ADULT_NOT_ASSIGNED", "verified adult has no active identity record"
            )
        if identity_issuer != principal.issuer:
            raise Be1PolicyError(
                "IDENTITY_ISSUER_MISMATCH", "identity issuer does not match verified token"
            )
        scoped = tuple(
            item
            for item in assignments
            if item.active
            and item.organization_id == organization_id
            and item.subject == principal.subject
            and (class_id is None or item.class_id is None or item.class_id == class_id)
            and (roles is None or item.role in roles)
        )
        if not scoped:
            raise Be1PolicyError(
                "SCOPE_DENIED", "adult assignment does not cover this organization or class"
            )
        return scoped

    @staticmethod
    def next_session_state(
        current: str, action: SessionAction, *, consent_ready: bool = True
    ) -> str:
        allowed = {
            ("configured", SessionAction.OPEN_LOBBY): "lobby",
            ("lobby", SessionAction.START): "active",
            ("active", SessionAction.PAUSE): "paused",
            ("paused", SessionAction.RESUME): "active",
            ("lobby", SessionAction.FINISH): "finished",
            ("active", SessionAction.FINISH): "finished",
            ("paused", SessionAction.FINISH): "finished",
        }
        if action is SessionAction.START and not consent_ready:
            raise Be1PolicyError(
                "CONSENT_NOT_EFFECTIVE",
                "consent verification and purpose approval are pending; child data is blocked",
            )
        next_state = allowed.get((current, action))
        if next_state is None:
            raise Be1PolicyError(
                "INVALID_SESSION_TRANSITION", "session cannot apply this transition"
            )
        return next_state


__all__ = ["AdultAssignment", "Be1PolicyError", "Be1RuntimePolicy", "SessionAction"]
