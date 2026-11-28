"""Persistence boundary for immutable Parent activity suggestion sets."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentActivityContext,
    ParentActivityPin,
    ParentStoryRevisionReservation,
)


@dataclass(frozen=True, slots=True)
class ActivitySuggestionSetReservation:
    receipt_id: str
    suggestion_set_id: str
    set_revision: int
    context: ParentActivityContext | None = None
    input_revision: int | None = None
    context_revision: int | None = None
    excluded_candidate_keys: tuple[str, ...] = ()
    excluded_activities: tuple[Mapping[str, Any], ...] = ()
    replay_body: Mapping[str, Any] | None = None

    @property
    def replayed(self) -> bool:
        return self.replay_body is not None


@dataclass(frozen=True, slots=True)
class ActivitySelectionOutcome:
    receipt_body: dict[str, Any]
    story_reservation: ParentStoryRevisionReservation | None = None


CatalogActivityResolver = Callable[
    [ParentActivityContext, Mapping[str, Any]], ParentActivityPin
]


class ParentActivitySuggestionSetsRepositoryPort(Protocol):
    def reserve_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        idempotency_key: str,
    ) -> ActivitySuggestionSetReservation:
        """Reserve an idempotent generation receipt and capture current run context."""
        ...

    def complete_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ActivitySuggestionSetReservation,
        response: Mapping[str, Any],
        provider_call_id: str | None,
    ) -> dict[str, Any]:
        """Append the immutable set and finalize its generation receipt."""
        ...

    def fail_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ActivitySuggestionSetReservation,
        error_code: str,
        response_status: int,
        request_id: str,
        cache_failure: bool = False,
        current_version: int | None = None,
    ) -> None:
        """Cache deterministic failures and release the receipt for retry after transient ones."""
        ...

    def select_suggestion_set_activity(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        suggestion_set_id: str,
        expected_understanding_revision: int,
        activity_index: int,
        idempotency_key: str,
        resolve_catalog: CatalogActivityResolver,
    ) -> ActivitySelectionOutcome:
        """Validate a stored set and append the selected Phase A activity row."""
        ...


__all__ = [
    "ActivitySelectionOutcome",
    "ActivitySuggestionSetReservation",
    "CatalogActivityResolver",
    "ParentActivitySuggestionSetsRepositoryPort",
]
