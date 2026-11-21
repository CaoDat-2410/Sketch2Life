"""Upload target resolvers (T-2a, T-2c): the Parent run for ``RUN_ARTWORK`` and ``RUN_AUDIO``.

A resolver answers two questions for one verified principal: which owner scope a target has (or
``None`` for absent and out-of-scope targets alike, so the route answers the uniform 404), and
whether the target still accepts bytes. ``OCCURRENCE_DOCUMENT`` has no default resolver: no
occurrence table exists at this commit, so T-3a/T-3b register a factory under that purpose in
``app.state.upload_target_resolver_factories``. Until then the purpose answers 404.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.upload_sessions import (
    PARENT_ACCOUNT_SCOPE,
    UploadScope,
    UploadTargetNotAccepting,
    UploadTargetResolver,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.purposes import RUN_ARTWORK, RUN_AUDIO

ResolverFactory = Callable[[Session], UploadTargetResolver]


def parent_scope_ref(principal: VerifiedPrincipal) -> str:
    """SHA-256 of the canonical ``{issuer, subject}``: the Parent owner scope reference.

    Same formula as the Parent StoryRun repository (a unit test pins the equality), so a run and
    its uploads share one typed scope (FR-C-08).
    """
    claims = {"issuer": principal.issuer, "subject": principal.subject}
    canonical = json.dumps(claims, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ParentRunArtworkResolver:
    """``RUN_ARTWORK``: the target is a StoryRun owned by the verified Parent."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def resolve(self, principal: VerifiedPrincipal, target_ref: str) -> UploadScope | None:
        try:
            canonical = str(UUID(target_ref))
        except ValueError:
            return None
        if canonical != target_ref:
            return None
        scope_ref = parent_scope_ref(principal)
        runs = story_tables.story_runs
        found = self._db.execute(
            select(runs.c.run_id).where(
                runs.c.run_id == canonical,
                runs.c.actor_scope_kind == PARENT_ACCOUNT_SCOPE,
                runs.c.actor_scope_ref == scope_ref,
            )
        ).first()
        if found is None:
            return None
        return UploadScope(
            owner_scope_kind=PARENT_ACCOUNT_SCOPE,
            owner_scope_ref=scope_ref,
            organization_id=None,
            object_prefix=f"parent/{canonical}/",
        )

    def ensure_accepting(self, principal: VerifiedPrincipal, target_ref: str) -> None:
        """Port design §7: re-check the run state before bytes are written."""
        try:
            SqlParentStoryRunRepository(self._db).ensure_accepting_artwork(
                principal=principal, run_id=target_ref
            )
        except ParentStoryRunError as exc:
            raise UploadTargetNotAccepting(exc.code) from None


class ParentRunAudioResolver(ParentRunArtworkResolver):
    """``RUN_AUDIO``: the same run scope; the run must still accept an idea (T-2c)."""

    def ensure_accepting(self, principal: VerifiedPrincipal, target_ref: str) -> None:
        try:
            SqlParentStoryRunRepository(self._db).ensure_accepting_audio(
                principal=principal, run_id=target_ref
            )
        except ParentStoryRunError as exc:
            raise UploadTargetNotAccepting(exc.code) from None


def default_resolver_factories() -> dict[str, ResolverFactory]:
    return {RUN_ARTWORK: ParentRunArtworkResolver, RUN_AUDIO: ParentRunAudioResolver}


def merged_resolver_factories(registered: Mapping[str, Any] | None) -> dict[str, ResolverFactory]:
    """Defaults plus the factories a later task registered on ``app.state``."""
    factories = default_resolver_factories()
    if registered:
        factories.update(registered)
    return factories


__all__ = [
    "ParentRunArtworkResolver",
    "ParentRunAudioResolver",
    "ResolverFactory",
    "default_resolver_factories",
    "merged_resolver_factories",
    "parent_scope_ref",
]
