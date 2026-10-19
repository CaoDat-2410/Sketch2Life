"""Framework-free, participant/version-local Child response rules (BE2-06)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_REF = re.compile(r"[A-Za-z0-9_.:-]{1,120}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ChildResponseRuleViolation(ValueError):
    """A response invariant was violated."""


class ResponseTerminal(ChildResponseRuleViolation):
    """A declined participant/version cannot be restored by another action."""


class ResponseAction(StrEnum):
    VIEWED = "viewed"
    HIDDEN = "hidden"
    DECLINED = "declined"


def _reference(value: str, name: str) -> None:
    if not isinstance(value, str) or _REF.fullmatch(value) is None:
        raise ChildResponseRuleViolation(f"invalid {name}")


def _revision(value: int, name: str) -> None:
    if type(value) is not int or value < 1:
        raise ChildResponseRuleViolation(f"invalid {name}")


def _hash(value: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ChildResponseRuleViolation("invalid content_sha256")


@dataclass(frozen=True, slots=True)
class ViewerKey:
    organization_id: str
    participant_id: str
    proposal_id: str
    proposal_version: int

    def __post_init__(self) -> None:
        for name in ("organization_id", "participant_id", "proposal_id"):
            _reference(getattr(self, name), name)
        _revision(self.proposal_version, "proposal_version")


@dataclass(frozen=True, slots=True)
class ResponseEntry:
    response_id: str
    operation_id: str
    key: ViewerKey
    response_revision: int
    class_id: str
    session_id: str
    canvas_id: str
    content_sha256: str
    review_ref: str
    turn_id: str
    turn_revision: int | None
    action: ResponseAction
    responded_at: datetime

    def __post_init__(self) -> None:
        for name in ("response_id", "operation_id", "class_id", "session_id", "canvas_id",
                     "review_ref", "turn_id"):
            _reference(getattr(self, name), name)
        _revision(self.response_revision, "response_revision")
        if self.response_revision < 2:
            raise ChildResponseRuleViolation("revision 1 is the virtual initial state")
        if self.turn_revision is not None:
            _revision(self.turn_revision, "turn_revision")
        _hash(self.content_sha256)
        if not isinstance(self.action, ResponseAction):
            raise ChildResponseRuleViolation("invalid response action")
        if self.responded_at.tzinfo is None or self.responded_at.utcoffset() is None:
            raise ChildResponseRuleViolation("responded_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ViewerState:
    key: ViewerKey
    revision: int = 1
    latest: ResponseEntry | None = None

    def __post_init__(self) -> None:
        _revision(self.revision, "revision")
        if self.latest is None:
            if self.revision != 1:
                raise ChildResponseRuleViolation("empty state must have virtual revision 1")
        elif self.latest.key != self.key or self.latest.response_revision != self.revision:
            raise ChildResponseRuleViolation("latest response must match viewer and revision")

    def with_entry(self, entry: ResponseEntry) -> ViewerState:
        if entry.key != self.key or entry.response_revision != self.revision + 1:
            raise ChildResponseRuleViolation("response must advance this viewer by one revision")
        if not transition(self, entry.action):
            raise ChildResponseRuleViolation("semantic no-op cannot append response history")
        return ViewerState(self.key, entry.response_revision, entry)


def transition(state: ViewerState, action: ResponseAction) -> bool:
    """Return whether this action changes state; decline survives turn/review changes."""

    if not isinstance(action, ResponseAction):
        raise ChildResponseRuleViolation("invalid response action")
    if state.latest is None:
        return True
    if state.latest.action is action:
        return False
    if state.latest.action is ResponseAction.DECLINED:
        raise ResponseTerminal("participant has declined this proposal version")
    return True


def viewer_etag(
    key: ViewerKey, content_sha256: str, review_ref: str, revision: int,
) -> str:
    """Strong family-qualified tag for one viewer state and observed exact review."""

    _hash(content_sha256)
    _reference(review_ref, "review_ref")
    _revision(revision, "revision")
    identity = [key.organization_id, key.participant_id, key.proposal_id,
                key.proposal_version, content_sha256, review_ref, revision]
    digest = hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()
    return f'"child-response:{digest}:{revision}"'
