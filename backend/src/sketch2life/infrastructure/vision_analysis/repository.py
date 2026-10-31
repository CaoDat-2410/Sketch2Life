"""PostgreSQL persistence for selected immutable pilot analysis records."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, Engine, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.vision_analysis import (
    AnalysisRevisionConflict,
    AnalysisUniqueConflict,
    CorrectionReceipt,
    CorrectionScopeKey,
)
from sketch2life.domain.vision_analysis import (
    AnalysisHead,
    InvalidationIntent,
    MeaningCorrection,
    ProviderResultRecord,
    VisionObservation,
)
from sketch2life.infrastructure.vision_analysis import tables
from sketch2life.infrastructure.vision_analysis.codec import from_payload, to_payload


def _require_org(actual: str, expected: str) -> None:
    if not actual or actual != expected:
        raise ValueError("organization scope mismatch")


class SqlAnalysisUnitOfWork:
    """Organization-bound analysis unit; corrections and other unselected writes fail closed."""

    def __init__(self, connection: Connection, organization_id: str) -> None:
        self._connection = connection
        self._organization_id = organization_id
        self._dirty = False

    def get_head(self, analysis_id: str) -> AnalysisHead | None:
        payload = self._connection.execute(
            select(tables.analysis_heads.c.payload).where(
                tables.analysis_heads.c.organization_id == self._organization_id,
                tables.analysis_heads.c.analysis_id == analysis_id,
            )
        ).scalar_one_or_none()
        return None if payload is None else from_payload(payload, AnalysisHead)

    def find_by_attempt(self, job_id: str, attempt_id: str) -> str | None:
        return self._connection.execute(
            select(tables.analysis_heads.c.analysis_id).where(
                tables.analysis_heads.c.organization_id == self._organization_id,
                tables.analysis_heads.c.job_id == job_id,
                tables.analysis_heads.c.attempt_id == attempt_id,
            )
        ).scalar_one_or_none()

    def insert_head(self, head: AnalysisHead) -> None:
        _require_org(head.organization_id, self._organization_id)
        try:
            self._connection.execute(
                insert(tables.analysis_heads).values(
                    organization_id=self._organization_id,
                    analysis_id=head.analysis_id,
                    analysis_revision=head.analysis_revision,
                    job_id=head.lineage.job_id,
                    attempt_id=head.lineage.job_attempt_id,
                    payload=to_payload(head),
                )
            )
        except IntegrityError as exc:
            raise AnalysisUniqueConflict("analysis identity already exists") from exc
        self._dirty = True

    def cas_head(self, *, expected_revision: int, head: AnalysisHead) -> None:
        _require_org(head.organization_id, self._organization_id)
        current = self.get_head(head.analysis_id)
        if current is None or current.analysis_revision != expected_revision:
            raise AnalysisRevisionConflict("analysis revision changed")
        if head.analysis_revision != expected_revision + 1:
            raise AnalysisRevisionConflict("analysis revision must advance by one")
        immutable_current = (
            current.scope,
            current.lineage,
            current.source,
            current.admission,
            current.context_revision,
            current.observation_sha256,
            current.created_at,
            current.typed_binding,
            current.context_digest,
        )
        immutable_next = (
            head.scope,
            head.lineage,
            head.source,
            head.admission,
            head.context_revision,
            head.observation_sha256,
            head.created_at,
            head.typed_binding,
            head.context_digest,
        )
        if immutable_next != immutable_current:
            raise ValueError("analysis source and request bindings are immutable")
        result = self._connection.execute(
            update(tables.analysis_heads)
            .where(
                tables.analysis_heads.c.organization_id == self._organization_id,
                tables.analysis_heads.c.analysis_id == head.analysis_id,
                tables.analysis_heads.c.analysis_revision == expected_revision,
            )
            .values(analysis_revision=head.analysis_revision, payload=to_payload(head))
        )
        if result.rowcount != 1:
            raise AnalysisRevisionConflict("analysis revision changed")
        self._dirty = True

    def insert_observation(self, observation: VisionObservation) -> None:
        _require_org(observation.organization_id, self._organization_id)
        head = self.get_head(observation.analysis_id)
        if head is None or head.observation_sha256 != observation.observation_sha256:
            raise ValueError("observation does not match the immutable analysis binding")
        try:
            self._connection.execute(
                insert(tables.observations).values(
                    organization_id=self._organization_id,
                    analysis_id=observation.analysis_id,
                    payload=to_payload(observation),
                )
            )
        except IntegrityError as exc:
            raise AnalysisUniqueConflict("observation is immutable and already exists") from exc
        self._dirty = True

    def get_observation(self, analysis_id: str) -> VisionObservation | None:
        payload = self._connection.execute(
            select(tables.observations.c.payload).where(
                tables.observations.c.organization_id == self._organization_id,
                tables.observations.c.analysis_id == analysis_id,
            )
        ).scalar_one_or_none()
        return None if payload is None else from_payload(payload, VisionObservation)

    def insert_provider_result(self, record: ProviderResultRecord) -> None:
        _require_org(record.organization_id, self._organization_id)
        observation = self.get_observation(record.analysis_id)
        if observation is None or observation.evidence.result_sha256 != record.result_sha256:
            raise ValueError("provider result does not match the immutable observation evidence")
        try:
            self._connection.execute(
                insert(tables.provider_results).values(
                    organization_id=self._organization_id,
                    result_ref=record.result_ref,
                    analysis_id=record.analysis_id,
                    result_sha256=record.result_sha256,
                    payload=to_payload(record),
                )
            )
        except IntegrityError as exc:
            raise AnalysisUniqueConflict("provider result is immutable and already exists") from exc
        self._dirty = True

    def get_provider_result(self, result_ref: str) -> ProviderResultRecord | None:
        payload = self._connection.execute(
            select(tables.provider_results.c.payload).where(
                tables.provider_results.c.organization_id == self._organization_id,
                tables.provider_results.c.result_ref == result_ref,
            )
        ).scalar_one_or_none()
        return None if payload is None else from_payload(payload, ProviderResultRecord)

    def append_correction(self, correction: MeaningCorrection) -> None:
        raise NotImplementedError("corrections are outside this pilot")

    def get_correction(self, correction_id: str) -> MeaningCorrection | None:
        raise NotImplementedError("corrections are outside this pilot")

    def list_corrections(self, analysis_id: str) -> tuple[MeaningCorrection, ...]:
        raise NotImplementedError("corrections are outside this pilot")

    def get_receipt(self, key: CorrectionScopeKey) -> CorrectionReceipt | None:
        raise NotImplementedError("correction receipts are outside this pilot")

    def put_receipt(self, receipt: CorrectionReceipt) -> None:
        raise NotImplementedError("correction receipts are outside this pilot")

    def add_invalidation(self, intent: InvalidationIntent) -> None:
        raise NotImplementedError("analysis invalidation is outside this pilot")

    def notice_seen(self, notice_id: str) -> bool:
        raise NotImplementedError("analysis notices are outside this pilot")

    def record_notice(self, notice_id: str) -> None:
        raise NotImplementedError("analysis notices are outside this pilot")


class SqlAnalysisRepository:
    def __init__(self, engine: Engine, organization_id: str) -> None:
        if not organization_id:
            raise ValueError("organization scope is required")
        self._engine = engine
        self._organization_id = organization_id

    @contextmanager
    def transaction(self) -> Iterator[SqlAnalysisUnitOfWork]:
        with self._engine.begin() as connection:
            if connection.dialect.name != "postgresql":
                raise RuntimeError("PostgreSQL is required for pilot persistence")
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                {"scope": "feat064-pilot:" + self._organization_id},
            )
            unit = SqlAnalysisUnitOfWork(connection, self._organization_id)
            yield unit
            if unit._dirty:
                epoch_insert = pg_insert(tables.epochs).values(
                    organization_id=self._organization_id,
                    request_epoch=0,
                    analysis_epoch=1,
                )
                connection.execute(
                    epoch_insert.on_conflict_do_update(
                        index_elements=[tables.epochs.c.organization_id],
                        set_={"analysis_epoch": tables.epochs.c.analysis_epoch + 1},
                    )
                )


__all__ = ["SqlAnalysisRepository", "SqlAnalysisUnitOfWork"]
