"""Core reference-closure purge, all or nothing (port design Draft 6 §5-§6, checks of §12).

The real ``CoreRunAssetPurge`` planning, sweep and verification code runs over an in-memory
asset reader and object store; only the SQL statements are replaced. No database or storage.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, BinaryIO

import pytest

from sketch2life.application.ports.core_foundation import (
    AssetCandidate,
    CoreAssetPurgeError,
    LifecycleScope,
    RowPurgeResult,
    RunAssetPurgePlan,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.story_run_lifecycle import canonical_json, sha256_hex
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    CoreRunAssetPurge,
    build_closure,
    build_plan,
)

RUN = "22222222-2222-4222-8222-222222222222"
OTHER_RUN = "33333333-3333-4333-8333-333333333333"
SCOPE = LifecycleScope("PARENT_ACCOUNT", "a" * 64)
FOREIGN = LifecycleScope("PARENT_ACCOUNT", "b" * 64)
ORIGINAL = f"parent/{RUN}/0001/original"
DERIVED = f"parent/{RUN}/0001/normalized.png"


@dataclass
class MemoryStorage:
    objects: set[str] = field(default_factory=set)
    fail_list: bool = False
    stuck: set[str] = field(default_factory=set)  # deletes of these keys have no effect
    deleted: list[str] = field(default_factory=list)

    def put_object(
        self,
        key: str,
        body: BinaryIO,
        *,
        content_type: str,
        content_length: int,
        metadata: Mapping[str, str],
    ) -> None:
        self.objects.add(key)

    def get_object(self, key: str) -> StoredObject | None:
        return None

    def delete_object(self, key: str) -> None:
        self.deleted.append(key)
        if key not in self.stuck:
            self.objects.discard(key)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        if self.fail_list:
            raise ObjectStorageFailure("listing failed")
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


@dataclass
class MemoryAssets:
    rows: dict[tuple[str, int], AssetCandidate] = field(default_factory=dict)
    lineage: set[tuple[str, str]] = field(default_factory=set)

    def add(
        self,
        ref: str,
        *,
        scope: LifecycleScope = SCOPE,
        sources: Iterable[str] = (RUN,),
        derived_from: str | None = None,
        version: int = 1,
    ) -> None:
        self.rows[(ref, version)] = AssetCandidate(
            asset_ref=ref,
            asset_version=version,
            owner_scope_kind=scope.kind,
            owner_scope_ref=scope.ref,
            source_refs=tuple(sources),
            derived_from_ref=derived_from,
        )


class MemoryReader:
    def __init__(self, assets: MemoryAssets) -> None:
        self._assets = assets

    def seed_rows(self, scope: LifecycleScope, run_ref: str) -> list[AssetCandidate]:
        return [
            row
            for row in self._assets.rows.values()
            if row.owner_scope_kind == scope.kind
            and row.owner_scope_ref == scope.ref
            and run_ref in row.source_refs
        ]

    def neighbours(
        self, frontier: list[AssetCandidate]
    ) -> tuple[list[AssetCandidate], list[tuple[str, str]]]:
        refs = {row.asset_ref for row in frontier}
        parents = {row.derived_from_ref for row in frontier if row.derived_from_ref}
        edges = [edge for edge in self._assets.lineage if edge[0] in refs or edge[1] in refs]
        linked = {ref for edge in edges for ref in edge} | parents
        rows = [
            row
            for row in self._assets.rows.values()
            if row.derived_from_ref in refs or row.asset_ref in linked
        ]
        return rows, edges

    def refs_with_rows(self, refs: Iterable[str]) -> frozenset[str]:
        present = {ref for ref, _version in self._assets.rows}
        return frozenset(ref for ref in refs if ref in present)

    def remaining_row_count(self, scope: LifecycleScope, run_ref: str) -> int:
        return len(self.seed_rows(scope, run_ref))


class MemoryCore(CoreRunAssetPurge):
    """The production purge logic over the in-memory reader; rows deleted like the SQL."""

    def __init__(self, assets: MemoryAssets, storage: MemoryStorage) -> None:
        self.assets = assets
        self.storage = storage

        @contextmanager
        def reader() -> Iterator[MemoryReader]:
            yield MemoryReader(assets)

        super().__init__(storage, reader)

    def _delete_rows_locked(
        self, plan: RunAssetPurgePlan, referenced_elsewhere_now: frozenset[str]
    ) -> RowPurgeResult:
        current = build_plan(
            build_closure(MemoryReader(self.assets), plan.scope, plan.run_ref),
            referenced_elsewhere_now,
        )
        if (current.removable, current.retained) != (plan.removable, plan.retained):
            raise CoreAssetPurgeError("PLAN_CHANGED")
        refs = {key.asset_ref for key in plan.removable}
        edges = {edge for edge in self.assets.lineage if edge[0] in refs or edge[1] in refs}
        self.assets.lineage -= edges
        for key in plan.removable:
            del self.assets.rows[(key.asset_ref, key.asset_version)]
        return RowPurgeResult(len(plan.removable), len(edges))


def artwork_world() -> tuple[MemoryAssets, MemoryStorage]:
    assets = MemoryAssets()
    assets.add(ORIGINAL)
    assets.add(DERIVED, derived_from=ORIGINAL)
    assets.lineage.add((ORIGINAL, DERIVED))
    return assets, MemoryStorage({ORIGINAL, DERIVED})


def _plan(core: MemoryCore, elsewhere: frozenset[str] = frozenset()) -> RunAssetPurgePlan:
    return core.plan_run_purge(core.closure_candidates(SCOPE, RUN), elsewhere)


def _full_purge(core: MemoryCore, plan: RunAssetPurgePlan) -> None:
    core.purge_objects(plan)
    core.sweep_run_prefix(SCOPE, RUN)
    core.delete_rows(plan, frozenset())


def test_the_two_artwork_assets_of_a_run_are_removable_and_purged() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    plan = _plan(core)
    assert not plan.retained and not plan.empty
    assert [key.asset_ref for key in plan.removable] == sorted([ORIGINAL, DERIVED])
    assert plan.removable_key_count == 2
    assert plan.removable_digest == sha256_hex(canonical_json(sorted([ORIGINAL, DERIVED])))
    _full_purge(core, plan)
    assert assets.rows == {} and assets.lineage == set() and storage.objects == set()
    verification = core.verify_run_purged(SCOPE, RUN)
    assert verification.complete
    assert (verification.remaining_row_count, verification.unexpected_object_count) == (0, 0)


@pytest.mark.parametrize(
    ("mutate", "reason"),
    (
        (
            lambda a: a.add(f"parent/{RUN}/x/foreign", scope=FOREIGN, derived_from=ORIGINAL),
            "SCOPE_MISMATCH",
        ),
        (lambda a: a.add("lesson-library/x/source", derived_from=ORIGINAL), "KEY_UNKNOWN"),
        (lambda a: a.add(f"parent/{RUN}/x/shared", sources=(RUN, OTHER_RUN)), "SHARED_REFERENCE"),
    ),
)
def test_any_retained_asset_retains_the_whole_group_and_deletes_nothing(
    mutate: Any, reason: str
) -> None:
    assets, storage = artwork_world()
    mutate(assets)
    storage.objects.add(f"parent/{RUN}/orphan/without-row")
    core = MemoryCore(assets, storage)
    plan = _plan(core)
    assert plan.removable == () and plan.removable_key_count == 0
    assert plan.retained and not plan.empty  # a retained plan is never empty
    assert plan.retained[0].reason_code == reason  # primary reasons first
    assert {item.reason_code for item in plan.retained[1:]} <= {reason, "LINEAGE_KEPT"}
    rows_before, objects_before = dict(assets.rows), set(storage.objects)
    for call in (lambda: core.purge_objects(plan), lambda: core.delete_rows(plan, frozenset())):
        with pytest.raises(CoreAssetPurgeError, match="PLAN_RETAINED"):
            call()
    assert assets.rows == rows_before and storage.objects == objects_before  # orphan survives
    assert not core.verify_run_purged(SCOPE, RUN).complete
    report = core.review_report(SCOPE, RUN, frozenset())
    assert report.retained == plan.retained


def test_a_story_side_reference_retains_the_group_and_is_reported() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    plan = _plan(core, frozenset({DERIVED}))
    assert [(item.key.asset_ref, item.reason_code) for item in plan.retained] == [
        (DERIVED, "SHARED_REFERENCE"),
        (ORIGINAL, "LINEAGE_KEPT"),
    ]
    assert core.review_report(SCOPE, RUN, frozenset({DERIVED})).retained == plan.retained


def test_review_report_shows_unclean_and_listed_candidate_keys() -> None:
    assets, storage = artwork_world()
    stranger = f"parent/{RUN}/zzzz/other-row"
    assets.add(stranger, sources=(OTHER_RUN,))  # a row under the prefix, not a candidate
    storage.objects.add(stranger)
    core = MemoryCore(assets, storage)
    report = core.review_report(SCOPE, RUN, frozenset())
    assert report.unclean_keys == (stranger,)
    assert report.listed_candidate_keys == tuple(sorted([ORIGINAL, DERIVED]))
    with pytest.raises(CoreAssetPurgeError, match="PREFIX_NOT_CLEAN"):
        core.sweep_run_prefix(SCOPE, RUN)  # it never deletes a key that has a row
    assert stranger in storage.objects


def test_a_stuck_delete_makes_the_sweep_raise_and_is_listed_for_review() -> None:
    assets, storage = artwork_world()
    storage.stuck.add(DERIVED)
    core = MemoryCore(assets, storage)
    plan = _plan(core)
    core.purge_objects(plan)
    with pytest.raises(CoreAssetPurgeError, match="PREFIX_NOT_CLEAN"):
        core.sweep_run_prefix(SCOPE, RUN)
    assert core.review_report(SCOPE, RUN, frozenset()).listed_candidate_keys == (DERIVED,)


def test_clearing_source_refs_alone_leaves_the_group_retained_but_detaching_releases_it() -> None:
    assets, storage = artwork_world()
    assets.add(f"parent/{RUN}/x/shared", sources=(RUN, OTHER_RUN), derived_from=ORIGINAL)
    core = MemoryCore(assets, storage)
    assert _plan(core).retained
    shared = assets.rows[(f"parent/{RUN}/x/shared", 1)]
    assets.rows[(shared.asset_ref, 1)] = AssetCandidate(
        shared.asset_ref, 1, SCOPE.kind, SCOPE.ref, (OTHER_RUN,), ORIGINAL
    )
    assert _plan(core).retained  # still a closure neighbour with a foreign entry
    assets.rows[(shared.asset_ref, 1)] = AssetCandidate(
        shared.asset_ref, 1, SCOPE.kind, SCOPE.ref, (OTHER_RUN,), None
    )
    plan = _plan(core)
    assert not plan.retained and plan.removable_key_count == 2


def test_manual_removal_of_rows_and_objects_gives_an_empty_plan() -> None:
    assets, storage = artwork_world()
    assets.rows.clear()
    assets.lineage.clear()
    storage.objects.clear()
    plan = _plan(MemoryCore(assets, storage))
    assert plan.empty and not plan.retained and plan.removable_key_count == 0
    assert plan.removable_digest == sha256_hex("[]")


@pytest.mark.parametrize(
    "bad",
    (
        "story_run:" + RUN,
        RUN[:9] + "ABCD" + RUN[13:],  # upper-case
        "",
        RUN + "/",
        "2222222-22222-4222-8222-222222222222",  # 36 characters, misplaced hyphens
    ),
)
def test_a_malformed_run_ref_raises_at_every_entry_and_is_never_complete(bad: str) -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    plan = _plan(core)
    calls = (
        lambda: core.closure_candidates(SCOPE, bad),
        lambda: core.sweep_run_prefix(SCOPE, bad),
        lambda: core.verify_run_purged(SCOPE, bad),
        lambda: core.review_report(SCOPE, bad, frozenset()),
        lambda: core.purge_objects(_replace_run(plan, bad)),
        lambda: core.delete_rows(_replace_run(plan, bad), frozenset()),
    )
    for call in calls:
        with pytest.raises(CoreAssetPurgeError, match="RUN_REF_INVALID"):
            call()
    assert storage.deleted == []


def _replace_run(plan: RunAssetPurgePlan, run_ref: str) -> RunAssetPurgePlan:
    from dataclasses import replace

    return replace(plan, run_ref=run_ref)


def test_a_core_reference_added_after_planning_stops_before_any_delete() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    plan = _plan(core)
    assets.add(f"parent/{RUN}/late/derived", derived_from=DERIVED, sources=(OTHER_RUN,))
    with pytest.raises(CoreAssetPurgeError, match="PLAN_CHANGED"):
        core.purge_objects(plan)
    assert storage.deleted == []


def test_a_changed_story_answer_stops_before_the_row_delete() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    plan = _plan(core)
    core.purge_objects(plan)
    core.sweep_run_prefix(SCOPE, RUN)
    with pytest.raises(CoreAssetPurgeError, match="PLAN_CHANGED"):
        core.delete_rows(plan, frozenset({ORIGINAL}))
    assert len(assets.rows) == 2


def test_an_orphan_written_after_the_rows_are_gone_is_swept_and_verification_completes() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    _full_purge(core, _plan(core))
    storage.objects.add(f"parent/{RUN}/late/original")
    assert not core.verify_run_purged(SCOPE, RUN).complete
    assert core.sweep_run_prefix(SCOPE, RUN).swept_count == 1
    assert core.verify_run_purged(SCOPE, RUN).complete


def test_a_rerun_after_success_has_an_empty_plan_and_a_sweep_finds_nothing() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    _full_purge(core, _plan(core))
    plan = _plan(core)
    assert plan.empty
    assert core.purge_objects(plan).deleted_object_count == 0
    assert core.delete_rows(plan, frozenset()) == RowPurgeResult(0, 0)
    assert core.sweep_run_prefix(SCOPE, RUN).swept_count == 0


def test_storage_errors_raise_typed_codes_and_are_never_read_as_absence() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    storage.fail_list = True
    for call in (
        lambda: core.verify_run_purged(SCOPE, RUN),
        lambda: core.sweep_run_prefix(SCOPE, RUN),
    ):
        with pytest.raises(CoreAssetPurgeError) as failed:
            call()
        assert failed.value.code == "STORAGE_UNAVAILABLE"
        assert RUN not in str(failed.value) and "parent/" not in str(failed.value)


def test_plan_hash_covers_candidates_classification_and_the_story_answer() -> None:
    assets, storage = artwork_world()
    core = MemoryCore(assets, storage)
    first = _plan(core)
    assert _plan(core).plan_sha256 == first.plan_sha256
    assert _plan(core, frozenset({"unrelated"})).plan_sha256 != first.plan_sha256
    assets.rows.clear()
    assert _plan(core).plan_sha256 != first.plan_sha256
