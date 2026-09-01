"""Replaceable content-policy boundary for P2-T3 declared vision text fields.

Phase A implementations are a deterministic known-violation lexical regression layer only,
never a semantic-safety guarantee.
"""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.vision import ObservedTextV1, VisionProhibitedClaimCategory


class ObservableContentPolicyV1(Protocol):
    @property
    def content_policy_version(self) -> str: ...

    @property
    def policy_match_view_version(self) -> str: ...

    def evaluate(self, texts: tuple[ObservedTextV1, ...]) -> VisionProhibitedClaimCategory | None:
        """Return the first matched category, or None when no known violation is found."""
        ...
