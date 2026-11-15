from __future__ import annotations

from sketch2life.infrastructure.local_demo.parent_activity_suggestion_store import (
    InMemoryParentActivitySuggestionStore,
)


def _activity(activity_ref: str, title: str = "Quan sát ngoài trời") -> dict[str, object]:
    return {"activity_ref": activity_ref, "title": title, "source": "AI_GENERATED_DRAFT"}


def _record(store: InMemoryParentActivitySuggestionStore, *, request_id: str = "request-1") -> None:
    store.record_response(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id=request_id,
        activities=[_activity("draft-activity-1"), _activity("draft-activity-2")],
    )


def test_primary_selection_is_bound_to_owner_run_revision_request_and_ref() -> None:
    store = InMemoryParentActivitySuggestionStore()
    _record(store)

    selected = store.select_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-1",
        activity_ref="draft-activity-2",
    )

    assert selected == _activity("draft-activity-2")
    assert store.select_primary(
        owner_subject="parent-2",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-1",
        activity_ref="draft-activity-2",
    ) is None
    assert store.select_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=1,
        request_id="request-1",
        activity_ref="draft-activity-2",
    ) is None
    assert store.select_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-old",
        activity_ref="draft-activity-2",
    ) is None
    assert store.get_selected_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
    ) == _activity("draft-activity-2")


def test_new_suggestion_invalidates_previous_refs_and_selection() -> None:
    store = InMemoryParentActivitySuggestionStore()
    _record(store)
    store.select_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-1",
        activity_ref="draft-activity-1",
    )
    store.record_response(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-2",
        activities=[_activity("draft-activity-3")],
    )

    assert store.get_selected_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
    ) is None
    assert store.select_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-1",
        activity_ref="draft-activity-1",
    ) is None


def test_snapshot_expires_within_configured_local_ttl(monkeypatch) -> None:
    now = [100.0]
    monkeypatch.setattr(
        "sketch2life.infrastructure.local_demo.parent_activity_suggestion_store.time.monotonic",
        lambda: now[0],
    )
    store = InMemoryParentActivitySuggestionStore(ttl_seconds=10)
    _record(store)
    store.select_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
        request_id="request-1",
        activity_ref="draft-activity-1",
    )
    now[0] = 111.0

    assert store.get_selected_primary(
        owner_subject="parent-1",
        story_run_id="run-1",
        understanding_revision=2,
    ) is None
