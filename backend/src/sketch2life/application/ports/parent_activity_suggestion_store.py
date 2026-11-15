"""Short-lived application boundary for Parent AI activity snapshots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class ParentActivitySuggestionStorePort(Protocol):
    def record_response(
        self,
        *,
        owner_subject: str,
        story_run_id: str,
        understanding_revision: int,
        request_id: str,
        activities: Sequence[Mapping[str, Any]],
    ) -> None: ...

    def select_primary(
        self,
        *,
        owner_subject: str,
        story_run_id: str,
        understanding_revision: int,
        request_id: str,
        activity_ref: str,
    ) -> dict[str, Any] | None: ...

    def get_selected_primary(
        self,
        *,
        owner_subject: str,
        story_run_id: str,
        understanding_revision: int,
    ) -> dict[str, Any] | None: ...
