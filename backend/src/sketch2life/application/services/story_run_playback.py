"""Playback authorization of the Parent video stream (FEAT-066 T-1c; SRS l.575-576, l.1676, l.1691).

Two steps, both fail closed:

* ``issue``: the owner asks for a short-lived grant. The run must be the caller's, at
  ``VIDEO_READY``, with its current generation ``READY``, every validation ``PASSED`` and an output
  (run state and generation state together, never the generation pointer alone: after
  ``video-unsuitable`` the pointer stays on the rejected row). A foreign or missing run, or a run
  being deleted, is 404; an own run that cannot be played is 409 ``INVALID_STATE_TRANSITION``; with
  no signing secret composed the answer is 503 ``PROVIDER_UNAVAILABLE`` after those checks.
* ``check_token`` then ``authorize``: every stream request verifies the token and rechecks the
  current owner, run state, generation identity and visibility. A wrong owner, a stolen token, a
  revoked grant (cancel, delete, complete, unsuitable, closeout) and a token for another run or
  generation are all the same uniform 404; only a malformed or expired token is 401.

The service holds no storage and no quota logic and never logs or returns the token.
"""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass, field
from typing import Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_video import (
    PlaybackGrant,
    PlaybackResolution,
    PlaybackStatus,
    PlaybackTarget,
    PlaybackTokenError,
    PlaybackTokenPort,
)

_NOT_FOUND = "RESOURCE_NOT_FOUND"


class PlaybackReader(Protocol):
    """The one read the service needs from the Story repository."""

    def resolve_playback(
        self, *, principal: VerifiedPrincipal, run_id: str, generation_id: str | None
    ) -> PlaybackResolution: ...


class RangeNotSatisfiable(Exception):
    """A ``Range`` header that is malformed, multiple, or outside the object (416)."""


_RANGE = re.compile(r"bytes=(\d{0,12})-(\d{0,12})")


def parse_byte_range(header: str | None, size: int) -> tuple[int, int] | None:
    """``None`` for the whole object, else an inclusive ``(first, last)`` byte range.

    One range only: ``bytes=a-b``, ``bytes=a-`` and ``bytes=-n``. A malformed header, several
    ranges, a range that starts at or after the end, or any range of an empty object raises
    ``RangeNotSatisfiable`` (the route answers 416 with ``Content-Range: bytes */size``).
    """

    if header is None or not header.strip():
        return None
    match = _RANGE.fullmatch(header.strip())
    if match is None:
        raise RangeNotSatisfiable
    first_text, last_text = match.groups()
    if size <= 0 or (not first_text and not last_text):
        raise RangeNotSatisfiable
    if not first_text:  # suffix: the last n bytes
        suffix = int(last_text)
        if suffix == 0:
            raise RangeNotSatisfiable
        return max(size - suffix, 0), size - 1
    first = int(first_text)
    last = int(last_text) if last_text else size - 1
    if first >= size or last < first:
        raise RangeNotSatisfiable
    return first, min(last, size - 1)


def check_playback_token(tokens: PlaybackTokenPort | None, token: str | None) -> PlaybackGrant:
    """Shape, signature and expiry only (no store read): 401 ``INVALID_TOKEN`` or ``TOKEN_EXPIRED``;
    503 ``PROVIDER_UNAVAILABLE`` when no signing secret is composed."""

    if tokens is None:
        raise ParentStoryRunError(503, "PROVIDER_UNAVAILABLE")
    try:
        return tokens.verify(token or "")
    except PlaybackTokenError as exc:
        raise ParentStoryRunError(401, exc.code) from None


@dataclass(frozen=True, slots=True)
class IssuedPlayback:
    """A grant for the response: the token is a secret and is excluded from ``repr``."""

    run_id: str
    generation_id: str
    expires_at: int
    token: str = field(repr=False)


class StoryPlaybackService:
    def __init__(self, repository: PlaybackReader, tokens: PlaybackTokenPort | None) -> None:
        self._repository = repository
        self._tokens = tokens

    def issue(self, *, principal: VerifiedPrincipal, run_id: str) -> IssuedPlayback:
        resolution = self._repository.resolve_playback(
            principal=principal, run_id=run_id, generation_id=None
        )
        if resolution.status is PlaybackStatus.NOT_PLAYABLE:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
        if resolution.status is not PlaybackStatus.PLAYABLE or resolution.target is None:
            raise ParentStoryRunError(404, _NOT_FOUND)
        if self._tokens is None:
            raise ParentStoryRunError(503, "PROVIDER_UNAVAILABLE")
        target = resolution.target
        token, expires_at = self._tokens.issue(
            run_id=target.run_id,
            generation_id=target.generation_id,
            actor_digest=self._tokens.actor_binding(target.scope_ref),
        )
        return IssuedPlayback(target.run_id, target.generation_id, expires_at, token)

    def check_token(self, token: str | None) -> PlaybackGrant:
        return check_playback_token(self._tokens, token)

    def authorize(
        self, *, principal: VerifiedPrincipal, run_id: str, grant: PlaybackGrant
    ) -> PlaybackTarget:
        """The current owner, run, generation and visibility, or the uniform 404."""

        if self._tokens is None:
            raise ParentStoryRunError(503, "PROVIDER_UNAVAILABLE")
        if run_id != grant.run_id:
            raise ParentStoryRunError(404, _NOT_FOUND)
        resolution = self._repository.resolve_playback(
            principal=principal, run_id=run_id, generation_id=grant.generation_id
        )
        target = resolution.target
        if resolution.status is not PlaybackStatus.PLAYABLE or target is None:
            raise ParentStoryRunError(404, _NOT_FOUND)
        # The token names the actor it was issued to; a valid token in other hands is useless.
        # Defence in depth: today the owner-scoped run lookup already rejects another caller, but a
        # shared-run model (Teacher assignment, T-4a1) makes this comparison load-bearing; keep it.
        if not hmac.compare_digest(
            grant.actor_digest, self._tokens.actor_binding(target.scope_ref)
        ):
            raise ParentStoryRunError(404, _NOT_FOUND)
        return target


__all__ = [
    "IssuedPlayback",
    "PlaybackReader",
    "RangeNotSatisfiable",
    "StoryPlaybackService",
    "check_playback_token",
    "parse_byte_range",
]
