"""Provider-neutral boundary for bounded source-region localization.

Semantic understanding and geometry localization are intentionally separate.  An
adapter may call a local model or a supervised runtime, but it can only return
normalized regions for the already-confirmed subject refs supplied in the
request.  The application service remains responsible for validating the
regions before they reach Pixi.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from sketch2life.contracts.schemas.p1_experience import VersionedRefV1


@dataclass(frozen=True, slots=True)
class SceneLocalizationRequest:
    session_id: str
    experience_spec_ref: VersionedRefV1
    source_artifact_ref: str
    source_artifact_sha256: str
    target_refs: tuple[str, ...]
    attempt_id: str


class SceneLocalizationPort(Protocol):
    """Locate only confirmed subjects in the immutable source image."""

    def localize(
        self, request: SceneLocalizationRequest
    ) -> Mapping[str, Mapping[str, float]] | None: ...


__all__ = ["SceneLocalizationPort", "SceneLocalizationRequest"]
