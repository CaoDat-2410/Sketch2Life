"""Core Asset purge and upload-close adapters for FR-C-08 (port design Draft 6 §5-§6).

``CoreRunAssetPurge`` implements ``RunAssetPurgePort``: reference closure over
``core_asset_metadata`` and ``core_asset_lineage``, the all-or-nothing plan (any retained
asset means nothing is deleted), the pre-checked object delete, the orphan sweep of
``parent/{run_ref}/``, the locked row delete and the verification. Core never reads
``story.*``; Story's answer arrives as ``referenced_elsewhere``. Results carry counts and
digests only: no key appears in an error, a response or a log line (SRS line 2145).

The data access is split into a small reader interface so the same planning, sweep and
verification code runs over PostgreSQL (``SqlCoreRunAssetPurge``) and, in the unit tests,
over an in-memory store.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from sqlalchemy import Table, and_, delete, or_, select, tuple_, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.core_foundation import (
    AssetCandidate,
    AssetKey,
    CandidateSet,
    CoreAssetPurgeError,
    LifecycleScope,
    ObjectPurgeResult,
    RetainedAsset,
    ReviewReport,
    RowPurgeResult,
    RunAssetPurgePlan,
    RunAssetPurgeVerification,
    SweepResult,
    run_object_prefix,
    validate_run_ref,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.story_run_lifecycle import canonical_json, sha256_hex
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS as _GENERIC_UPLOADS
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

MAX_CLOSURE_ASSETS = 256
_REASON_ORDER = {"SCOPE_MISMATCH": 0, "KEY_UNKNOWN": 1, "SHARED_REFERENCE": 2, "LINEAGE_KEPT": 3}
_OPEN_UPLOAD_STATES = ("RECEIVING", "PENDING", "PROCESSING")
# T-2a: purposes of the generic upload sessions whose target is a Parent run.
_RUN_UPLOAD_PURPOSES = ("RUN_ARTWORK", "RUN_AUDIO")


class AssetReader(Protocol):
    """Read access the plan needs; one reader is bound to one transaction."""

    def seed_rows(self, scope: LifecycleScope, run_ref: str) -> list[AssetCandidate]: ...

    def neighbours(
        self, frontier: list[AssetCandidate]
    ) -> tuple[list[AssetCandidate], list[tuple[str, str]]]:
        """Rows linked to the frontier by ``derived_from_ref`` (both directions) or by a
        lineage edge (both directions), across any scope, and the edges found."""
        ...

    def refs_with_rows(self, refs: Iterable[str]) -> frozenset[str]: ...

    def remaining_row_count(self, scope: LifecycleScope, run_ref: str) -> int: ...


def build_closure(
    reader: AssetReader, scope: LifecycleScope, run_ref: str
) -> CandidateSet:
    """Port design §6.1 item 1: scope-seeded rows, then the closure across any scope."""

    seeds = reader.seed_rows(scope, run_ref)
    known: dict[tuple[str, int], AssetCandidate] = {
        (row.asset_ref, row.asset_version): row for row in seeds
    }
    edges: set[tuple[str, str]] = set()
    frontier = list(known.values())
    while frontier:
        rows, found_edges = reader.neighbours(frontier)
        edges.update(found_edges)
        frontier = []
        for row in rows:
            key = (row.asset_ref, row.asset_version)
            if key not in known:
                known[key] = row
                frontier.append(row)
        if len(known) > MAX_CLOSURE_ASSETS:
            raise CoreAssetPurgeError("CLOSURE_TOO_LARGE")
    assets = tuple(sorted(known.values(), key=lambda row: (row.asset_ref, row.asset_version)))
    return CandidateSet(scope=scope, run_ref=run_ref, assets=assets, edges=tuple(sorted(edges)))


def build_plan(
    candidates: CandidateSet, referenced_elsewhere: frozenset[str]
) -> RunAssetPurgePlan:
    """Port design §6.1 items 3-5: classify, then all or nothing."""

    run_ref = validate_run_ref(candidates.run_ref)
    scope = candidates.scope
    prefix = run_object_prefix(run_ref)
    candidate_refs = {row.asset_ref for row in candidates.assets}
    allowed_sources = candidate_refs | {run_ref}
    referenced = frozenset(referenced_elsewhere)
    primary: dict[tuple[str, int], str] = {}
    for row in candidates.assets:
        key = (row.asset_ref, row.asset_version)
        if row.owner_scope_kind != scope.kind or row.owner_scope_ref != scope.ref:
            primary[key] = "SCOPE_MISMATCH"
        elif not row.asset_ref.startswith(prefix) or row.asset_version != 1:
            primary[key] = "KEY_UNKNOWN"
        elif row.asset_ref in referenced or any(
            source not in allowed_sources for source in row.source_refs
        ):
            primary[key] = "SHARED_REFERENCE"
    removable: tuple[AssetKey, ...]
    retained: tuple[RetainedAsset, ...]
    if primary:
        retained_rows = [
            RetainedAsset(
                AssetKey(row.asset_ref, row.asset_version),
                primary.get((row.asset_ref, row.asset_version), "LINEAGE_KEPT"),
            )
            for row in candidates.assets
        ]
        retained = tuple(
            sorted(
                retained_rows,
                key=lambda item: (_REASON_ORDER[item.reason_code], item.key),
            )
        )
        removable = ()
    else:
        retained = ()
        removable = tuple(sorted(row.key for row in candidates.assets))
    classification = [
        [row.asset_ref, row.asset_version, primary.get((row.asset_ref, row.asset_version))]
        for row in candidates.assets
    ]
    if primary:
        classification = [
            [ref, version, reason or "LINEAGE_KEPT"] for ref, version, reason in classification
        ]
    else:
        classification = [[ref, version, "REMOVABLE"] for ref, version, _reason in classification]
    removable_refs = sorted(key.asset_ref for key in removable)
    plan_sha256 = sha256_hex(
        canonical_json(
            {
                "scope": [scope.kind, scope.ref],
                "run_ref": run_ref,
                "candidates": sorted(classification),
                "referenced_elsewhere": sorted(referenced),
            }
        )
    )
    return RunAssetPurgePlan(
        scope=scope,
        run_ref=run_ref,
        referenced_elsewhere=tuple(sorted(referenced)),
        removable=removable,
        retained=retained,
        removable_key_count=len(removable),
        removable_digest=sha256_hex(canonical_json(removable_refs)),
        plan_sha256=plan_sha256,
        candidate_count=len(candidates.assets),
    )


class CoreRunAssetPurge:
    """``RunAssetPurgePort`` over a reader factory and an object-storage port."""

    def __init__(
        self,
        storage: ObjectStoragePort,
        reader: Callable[[], AbstractContextManager[AssetReader]],
    ) -> None:
        self._storage = storage
        self._reader = reader

    # ---------------------------------------------------------------- plan
    def closure_candidates(self, scope: LifecycleScope, run_ref: str) -> CandidateSet:
        run_ref = validate_run_ref(run_ref)
        with self._reader() as reader:
            return build_closure(reader, scope, run_ref)

    def plan_run_purge(
        self, candidates: CandidateSet, referenced_elsewhere: frozenset[str]
    ) -> RunAssetPurgePlan:
        return build_plan(candidates, referenced_elsewhere)

    # ---------------------------------------------------------------- act
    def purge_objects(self, plan: RunAssetPurgePlan) -> ObjectPurgeResult:
        validate_run_ref(plan.run_ref)
        if plan.retained:
            raise CoreAssetPurgeError("PLAN_RETAINED")
        if not plan.removable:
            return ObjectPurgeResult(0)
        current = build_plan(
            self.closure_candidates(plan.scope, plan.run_ref),
            frozenset(plan.referenced_elsewhere),
        )
        if current.plan_sha256 != plan.plan_sha256:
            raise CoreAssetPurgeError("PLAN_CHANGED")
        deleted = 0
        for key in plan.removable:
            self._delete_object(key.asset_ref)
            deleted += 1
        return ObjectPurgeResult(deleted)

    def sweep_run_prefix(self, scope: LifecycleScope, run_ref: str) -> SweepResult:
        """Delete every listed key with no metadata row in any scope, then list again.

        Precondition (port design §5.1): only for a run in DELETE_PENDING or DELETED.
        """

        del scope
        prefix = run_object_prefix(run_ref)
        keys = self._list(prefix)
        with self._reader() as reader:
            with_rows = reader.refs_with_rows(keys)
        orphans = [key for key in keys if key not in with_rows]
        for key in orphans:
            self._delete_object(key)
        if self._list(prefix):
            raise CoreAssetPurgeError("PREFIX_NOT_CLEAN")
        return SweepResult(len(orphans))

    def delete_rows(
        self, plan: RunAssetPurgePlan, referenced_elsewhere_now: frozenset[str]
    ) -> RowPurgeResult:
        validate_run_ref(plan.run_ref)
        if plan.retained:
            raise CoreAssetPurgeError("PLAN_RETAINED")
        if not plan.removable:
            return RowPurgeResult(0, 0)
        return self._delete_rows_locked(plan, referenced_elsewhere_now)

    def _delete_rows_locked(
        self, plan: RunAssetPurgePlan, referenced_elsewhere_now: frozenset[str]
    ) -> RowPurgeResult:
        raise NotImplementedError

    # ---------------------------------------------------------------- verify
    def verify_run_purged(
        self, scope: LifecycleScope, run_ref: str
    ) -> RunAssetPurgeVerification:
        prefix = run_object_prefix(run_ref)
        with self._reader() as reader:
            remaining = reader.remaining_row_count(scope, run_ref)
        objects = self._list(prefix)
        return RunAssetPurgeVerification(
            complete=remaining == 0 and not objects,
            remaining_row_count=remaining,
            unexpected_object_count=len(objects),
        )

    def review_report(
        self, scope: LifecycleScope, run_ref: str, referenced_elsewhere: frozenset[str]
    ) -> ReviewReport:
        """Operator-side only: keys and reasons for the owner review, never for a client."""

        candidates = self.closure_candidates(scope, run_ref)
        plan = build_plan(candidates, referenced_elsewhere)
        keys = self._list(run_object_prefix(run_ref))
        candidate_refs = {row.asset_ref for row in candidates.assets}
        with self._reader() as reader:
            with_rows = reader.refs_with_rows(keys)
        return ReviewReport(
            retained=plan.retained,
            unclean_keys=tuple(
                sorted(key for key in keys if key in with_rows and key not in candidate_refs)
            ),
            listed_candidate_keys=tuple(sorted(key for key in keys if key in candidate_refs)),
        )

    # ---------------------------------------------------------------- storage
    def _list(self, prefix: str) -> tuple[str, ...]:
        try:
            return tuple(self._storage.list_keys(prefix))
        except ObjectStorageFailure:
            raise CoreAssetPurgeError("STORAGE_UNAVAILABLE") from None

    def _delete_object(self, key: str) -> None:
        try:
            self._storage.delete_object(key)
        except ObjectStorageFailure:
            raise CoreAssetPurgeError("STORAGE_UNAVAILABLE") from None


# ------------------------------------------------------------------------- PostgreSQL
_ASSETS = cast(Table, CoreAssetMetadataModel.__table__)
_LINEAGE = story_tables.asset_lineage


def _candidate(row: Any) -> AssetCandidate:
    sources = row.source_refs if isinstance(row.source_refs, list) else []
    return AssetCandidate(
        asset_ref=str(row.asset_ref),
        asset_version=int(row.asset_version),
        owner_scope_kind=str(row.owner_scope_kind),
        owner_scope_ref=None if row.owner_scope_ref is None else str(row.owner_scope_ref),
        source_refs=tuple(str(value) for value in sources),
        derived_from_ref=None if row.derived_from_ref is None else str(row.derived_from_ref),
    )


class _SqlAssetReader:
    def __init__(self, session: Session, *, lock: bool = False) -> None:
        self._session = session
        self._lock = lock

    def _rows(self, predicate: Any) -> list[AssetCandidate]:
        query = select(
            _ASSETS.c.asset_ref,
            _ASSETS.c.asset_version,
            _ASSETS.c.owner_scope_kind,
            _ASSETS.c.owner_scope_ref,
            _ASSETS.c.source_refs,
            _ASSETS.c.derived_from_ref,
        ).where(predicate)
        if self._lock:
            query = query.with_for_update()
        return [_candidate(row) for row in self._session.execute(query).all()]

    def seed_rows(self, scope: LifecycleScope, run_ref: str) -> list[AssetCandidate]:
        return self._rows(
            and_(
                _ASSETS.c.owner_scope_kind == scope.kind,
                _ASSETS.c.owner_scope_ref == scope.ref,
                _ASSETS.c.source_refs.contains([run_ref]),
            )
        )

    def neighbours(
        self, frontier: list[AssetCandidate]
    ) -> tuple[list[AssetCandidate], list[tuple[str, str]]]:
        refs = sorted({row.asset_ref for row in frontier})
        parents = sorted({row.derived_from_ref for row in frontier if row.derived_from_ref})
        edges = [
            (str(source), str(derived))
            for source, derived in self._session.execute(
                select(_LINEAGE.c.source_asset_ref, _LINEAGE.c.derived_asset_ref).where(
                    or_(
                        _LINEAGE.c.source_asset_ref.in_(refs),
                        _LINEAGE.c.derived_asset_ref.in_(refs),
                    )
                )
            ).all()
        ]
        linked = sorted({ref for edge in edges for ref in edge} | set(parents))
        predicate: Any = _ASSETS.c.derived_from_ref.in_(refs)
        if linked:
            predicate = or_(predicate, _ASSETS.c.asset_ref.in_(linked))
        return self._rows(predicate), edges

    def refs_with_rows(self, refs: Iterable[str]) -> frozenset[str]:
        wanted = sorted(set(refs))
        if not wanted:
            return frozenset()
        return frozenset(
            str(value)
            for value in self._session.scalars(
                select(_ASSETS.c.asset_ref).where(_ASSETS.c.asset_ref.in_(wanted))
            )
        )

    def remaining_row_count(self, scope: LifecycleScope, run_ref: str) -> int:
        return len(self.seed_rows(scope, run_ref))


class _SessionReader(AbstractContextManager[AssetReader]):
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions
        self._session: Session | None = None

    def __enter__(self) -> AssetReader:
        self._session = self._sessions()
        return _SqlAssetReader(self._session)

    def __exit__(self, *_exc: object) -> None:
        if self._session is not None:
            self._session.close()


class SqlCoreRunAssetPurge(CoreRunAssetPurge):
    """``RunAssetPurgePort`` over PostgreSQL and the application object store."""

    def __init__(self, sessions: sessionmaker[Session], storage: ObjectStoragePort) -> None:
        super().__init__(storage, lambda: _SessionReader(sessions))
        self._sessions = sessions

    def _delete_rows_locked(
        self, plan: RunAssetPurgePlan, referenced_elsewhere_now: frozenset[str]
    ) -> RowPurgeResult:
        with self._sessions.begin() as session:
            reader = _SqlAssetReader(session, lock=True)
            current = build_plan(
                build_closure(reader, plan.scope, plan.run_ref), referenced_elsewhere_now
            )
            if (current.removable, current.retained) != (plan.removable, plan.retained):
                raise CoreAssetPurgeError("PLAN_CHANGED")
            refs = sorted(key.asset_ref for key in plan.removable)
            lineage = cast(
                CursorResult[Any],
                session.execute(
                    delete(_LINEAGE).where(
                        or_(
                            _LINEAGE.c.source_asset_ref.in_(refs),
                            _LINEAGE.c.derived_asset_ref.in_(refs),
                        )
                    )
                ),
            )
            # The RESTRICT lineage FKs (C3) are cleared above; the rows go in one statement.
            keys = [(key.asset_ref, key.asset_version) for key in plan.removable]
            rows = cast(
                CursorResult[Any],
                session.execute(
                    delete(_ASSETS).where(
                        tuple_(_ASSETS.c.asset_ref, _ASSETS.c.asset_version).in_(keys)
                    )
                ),
            )
            if rows.rowcount != len(keys):
                raise CoreAssetPurgeError("PLAN_CHANGED")
            return RowPurgeResult(int(rows.rowcount), int(lineage.rowcount))


class SqlCoreRunUploadClose:
    """``RunUploadClosePort``: open upload sessions that name the run (DTR step 1).

    Two tables hold such sessions: the StoryRun-lite demo tables (``story_tables.upload_sessions``)
    and, since T-2a, the generic ``core_upload_sessions`` (``RUN_ARTWORK`` and ``RUN_AUDIO``
    sessions of a Parent run). The plan is the union of both id lists and the close count is their
    sum. A generic session goes to ``ABORTED`` with ``error_code = 'RUN_DELETED'``; its chunk
    objects live under ``parent/{run_ref}/`` and are removed by the run-prefix sweep, and its
    completed-but-unattached assets are ``core_asset_metadata`` rows seeded by ``source_refs``.
    """

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    @staticmethod
    def _predicate(scope: LifecycleScope, run_ref: str) -> Any:
        uploads = story_tables.upload_sessions
        return and_(
            uploads.c.actor_scope_kind == scope.kind,
            uploads.c.actor_scope_ref == scope.ref,
            uploads.c.target_ref == run_ref,
            uploads.c.state.in_(_OPEN_UPLOAD_STATES),
        )

    @staticmethod
    def _generic_predicate(scope: LifecycleScope, run_ref: str) -> Any:
        return and_(
            _GENERIC_UPLOADS.c.owner_scope_kind == scope.kind,
            _GENERIC_UPLOADS.c.owner_scope_ref == scope.ref,
            _GENERIC_UPLOADS.c.target_ref == run_ref,
            _GENERIC_UPLOADS.c.purpose.in_(_RUN_UPLOAD_PURPOSES),
            _GENERIC_UPLOADS.c.state == "OPEN",
        )

    def plan_close_run_uploads(self, scope: LifecycleScope, run_ref: str) -> tuple[str, ...]:
        run_ref = validate_run_ref(run_ref)
        uploads = story_tables.upload_sessions
        with self._sessions() as session:
            lite = [
                str(value)
                for value in session.scalars(
                    select(uploads.c.upload_session_id)
                    .where(self._predicate(scope, run_ref))
                    .order_by(uploads.c.upload_session_id)
                )
            ]
            generic = [
                str(value)
                for value in session.scalars(
                    select(_GENERIC_UPLOADS.c.upload_session_id)
                    .where(self._generic_predicate(scope, run_ref))
                    .order_by(_GENERIC_UPLOADS.c.upload_session_id)
                )
            ]
            return tuple(sorted({*lite, *generic}))

    def close_run_uploads(self, scope: LifecycleScope, run_ref: str) -> int:
        run_ref = validate_run_ref(run_ref)
        uploads = story_tables.upload_sessions
        with self._sessions.begin() as session:
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(uploads)
                    .where(self._predicate(scope, run_ref))
                    .values(
                        state="ABORTED",
                        error_code="RUN_DELETED",
                        state_version=uploads.c.state_version + 1,
                        updated_at=datetime.now(UTC),
                    )
                ),
            )
            generic = cast(
                CursorResult[Any],
                session.execute(
                    update(_GENERIC_UPLOADS)
                    .where(self._generic_predicate(scope, run_ref))
                    .values(
                        state="ABORTED",
                        error_code="RUN_DELETED",
                        aborted_at=datetime.now(UTC),
                    )
                ),
            )
            return int(result.rowcount) + int(generic.rowcount)


__all__ = [
    "AssetReader",
    "CoreRunAssetPurge",
    "MAX_CLOSURE_ASSETS",
    "SqlCoreRunAssetPurge",
    "SqlCoreRunUploadClose",
    "build_closure",
    "build_plan",
]
