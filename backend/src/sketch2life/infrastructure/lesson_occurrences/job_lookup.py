"""Class of a source document for the job read rule (FEAT-066 goal v3, T-3b; SRS l.865, l.1675).

``GET /v1/jobs/{job_id}`` authorises a job of kind ``LESSON_SOURCE_DOCUMENT`` by the class of the
occurrence the document belongs to. The job row only stores the document id, so the rule asks this
lookup (one short read on its own connection, no row lock). The organization of the job must equal
the organization of the occurrence, so a job id can never be paired with another organization.
"""

from __future__ import annotations

from sqlalchemy import Engine, select

from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES, SOURCE_DOCUMENTS


class SqlSourceDocumentClassLookup:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def class_for(self, organization_id: str, source_document_id: str) -> str | None:
        statement = (
            select(OCCURRENCES.c.class_ref)
            .join(SOURCE_DOCUMENTS, SOURCE_DOCUMENTS.c.occurrence_id == OCCURRENCES.c.occurrence_id)
            .where(
                SOURCE_DOCUMENTS.c.source_document_id == source_document_id,
                OCCURRENCES.c.organization_ref == organization_id,
            )
        )
        with self._engine.connect() as connection:
            value = connection.execute(statement).scalar_one_or_none()
        return None if value is None else str(value)


__all__ = ["SqlSourceDocumentClassLookup"]
