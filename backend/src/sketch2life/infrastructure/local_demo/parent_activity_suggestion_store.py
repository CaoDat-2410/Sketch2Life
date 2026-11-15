"""Bounded process-local activity selection bridge for the local Modal pilot."""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

_Scope = tuple[str, str, int]
_Key = tuple[str, str, int, str]


@dataclass(slots=True)
class _Entry:
    activities_by_ref: dict[str, dict[str, Any]]
    expires_at: float
    selected_ref: str | None = None


@dataclass(slots=True)
class InMemoryParentActivitySuggestionStore:
    """Keep current suggestion results only in the API process, for at most 30 minutes."""

    ttl_seconds: int = 1_800
    max_entries: int = 256
    _entries: OrderedDict[_Key, _Entry] = field(default_factory=OrderedDict, init=False)
    _selected_by_scope: dict[_Scope, _Key] = field(default_factory=dict, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def __post_init__(self) -> None:
        if not 0 < self.ttl_seconds <= 1_800:
            raise ValueError("Parent activity snapshots must expire within 30 minutes")
        if not 1 <= self.max_entries <= 1_024:
            raise ValueError("Parent activity snapshot capacity is outside the local bound")

    def record_response(
        self,
        *,
        owner_subject: str,
        story_run_id: str,
        understanding_revision: int,
        request_id: str,
        activities: Sequence[Mapping[str, Any]],
    ) -> None:
        scope = _scope(owner_subject, story_run_id, understanding_revision)
        if not request_id.strip() or not activities:
            raise ValueError("activity response snapshot is empty")
        by_ref: dict[str, dict[str, Any]] = {}
        for activity in activities:
            activity_ref = activity.get("activity_ref")
            if (
                not isinstance(activity_ref, str)
                or not activity_ref.strip()
                or activity_ref in by_ref
            ):
                raise ValueError("activity response refs must be unique non-empty strings")
            by_ref[activity_ref] = json.loads(
                json.dumps(dict(activity), ensure_ascii=False, separators=(",", ":"))
            )
        key = (*scope, request_id)
        with self._lock:
            self._purge_expired(time.monotonic())
            self._remove_scope(scope)
            self._entries[key] = _Entry(
                activities_by_ref=by_ref,
                expires_at=time.monotonic() + self.ttl_seconds,
            )
            while len(self._entries) > self.max_entries:
                evicted_key, _ = self._entries.popitem(last=False)
                self._drop_selection_for_key(evicted_key)

    def select_primary(
        self,
        *,
        owner_subject: str,
        story_run_id: str,
        understanding_revision: int,
        request_id: str,
        activity_ref: str,
    ) -> dict[str, Any] | None:
        scope = _scope(owner_subject, story_run_id, understanding_revision)
        key = (*scope, request_id)
        with self._lock:
            self._purge_expired(time.monotonic())
            entry = self._entries.get(key)
            activity = entry.activities_by_ref.get(activity_ref) if entry else None
            if activity is None:
                return None
            entry.selected_ref = activity_ref
            self._selected_by_scope[scope] = key
            self._entries.move_to_end(key)
            return json.loads(json.dumps(activity, ensure_ascii=False, separators=(",", ":")))

    def get_selected_primary(
        self,
        *,
        owner_subject: str,
        story_run_id: str,
        understanding_revision: int,
    ) -> dict[str, Any] | None:
        scope = _scope(owner_subject, story_run_id, understanding_revision)
        with self._lock:
            self._purge_expired(time.monotonic())
            key = self._selected_by_scope.get(scope)
            entry = self._entries.get(key) if key else None
            activity = entry.activities_by_ref.get(entry.selected_ref or "") if entry else None
            if activity is None:
                return None
            self._entries.move_to_end(key)
            return json.loads(json.dumps(activity, ensure_ascii=False, separators=(",", ":")))

    def _purge_expired(self, now: float) -> None:
        expired = [key for key, entry in self._entries.items() if entry.expires_at <= now]
        for key in expired:
            self._entries.pop(key, None)
            self._drop_selection_for_key(key)

    def _remove_scope(self, scope: _Scope) -> None:
        for key in [key for key in self._entries if key[:3] == scope]:
            self._entries.pop(key, None)
        self._selected_by_scope.pop(scope, None)

    def _drop_selection_for_key(self, key: _Key) -> None:
        if self._selected_by_scope.get(key[:3]) == key:
            self._selected_by_scope.pop(key[:3], None)


def _scope(owner_subject: str, story_run_id: str, revision: int) -> _Scope:
    if not owner_subject.strip() or not story_run_id.strip() or revision < 1:
        raise ValueError("Parent activity snapshot scope is invalid")
    return owner_subject, story_run_id, revision
