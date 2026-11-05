"""Scoped synthetic-only BE1 member facts for the assistance owner port."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Connection, select
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.ports.assistance import CanvasFacts, GroupRoster
from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1
from sketch2life.domain.assistance import Contributor, MemberFact
from sketch2life.domain.eligibility import EligibilityScope
from sketch2life.domain.vision_analysis import ProviderContextMode
from sketch2life.infrastructure.assistance.be1_fact_reader import (
    BE1FactReader,
    BE1FactRequest,
)
from sketch2life.infrastructure.assistance.context_revision import context_revision
from sketch2life.infrastructure.assistance.pilot_policy import PILOT_SYNTHETIC_POLICY_V1
from sketch2life.infrastructure.assistance.postgres_fact_source import PostgresBE1FactSource
from sketch2life.infrastructure.persistence.be1_models import (
    ChildTurnModel,
    ClassroomSessionModel,
    SessionGroupModel,
    SessionMembershipModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAggregateRevisionModel

Clock = Callable[[], datetime]


class PostgresAssistanceMemberAdapter:
    """Fail-closed member adapter for one explicitly bound synthetic pilot session."""

    def __init__(
        self,
        connection: Connection,
        *,
        session_id: str,
        environment: str,
        pilot_enabled: bool,
        clock: Clock = lambda: datetime.now(UTC),
    ) -> None:
        self._session_id = session_id
        self._reader = BE1FactReader(
            PostgresBE1FactSource(
                connection,
                environment=environment,
                pilot_enabled=pilot_enabled,
                clock=clock,
            )
        )

    def members(
        self,
        organization_id: str,
        participant_ids: tuple[str, ...],
        purpose_code: str,
        *,
        scope: EligibilityScope | None = None,
    ) -> tuple[MemberFact, ...]:
        if (
            scope is None
            or len(participant_ids) != 1
            or participant_ids != (scope.child_id,)
            or organization_id != scope.organization_id
            or purpose_code != scope.purpose_ref
            or not self._session_id
        ):
            return ()
        result = self._reader.read(
            BE1FactRequest(
                organization_id=scope.organization_id,
                class_id=scope.class_id,
                session_id=self._session_id,
                child_id=scope.child_id,
                purpose_ref=scope.purpose_ref,
                audience_participant_ids=participant_ids,
                context_mode=ProviderContextMode.IMAGE_ONLY,
            )
        )
        return (result.member,) if result.member is not None else ()


class PostgresAssistanceOwnerAdapter(PostgresAssistanceMemberAdapter):
    """Read scoped pilot canvas/roster/turn facts on the caller's connection.

    Each owner projection is one SQL statement. The adapter never creates or ends a
    transaction; an atomic acceptance caller retains the same connection and owner fence.
    An injected T4 export supplies the authoritative operations binding, never checkpoint
    payloads. BE1 currently identifies its group canvas by the group id.
    """

    def __init__(
        self,
        connection: Connection,
        *,
        organization_id: str,
        class_id: str,
        session_id: str,
        environment: str,
        pilot_enabled: bool,
        export_source: Callable[[str, str], CanvasSourceExportV1 | None],
        clock: Clock = lambda: datetime.now(UTC),
    ) -> None:
        super().__init__(
            connection,
            session_id=session_id,
            environment=environment,
            pilot_enabled=pilot_enabled,
            clock=clock,
        )
        self._connection = connection
        self._organization_id = organization_id
        self._class_id = class_id
        self._allowed = environment in {"local", "test"} and pilot_enabled is True
        self._export_source = export_source

    def _projection(self, canvas_id: str) -> list[dict[str, Any]]:
        if not self._allowed or not all(
            (self._organization_id, self._class_id, self._session_id, canvas_id)
        ):
            return []
        session, group, member, turn, aggregate = (
            ClassroomSessionModel,
            SessionGroupModel,
            SessionMembershipModel,
            ChildTurnModel,
            CoreAggregateRevisionModel,
        )
        statement = (
            select(
                session.state.label("session_state"),
                session.revision.label("session_revision"),
                session.configuration.label("configuration"),
                group.group_id.label("group_id"),
                group.state.label("group_state"),
                aggregate.revision.label("aggregate_revision"),
                member.membership_id.label("membership_id"),
                member.child_id.label("child_id"),
                member.state.label("membership_state"),
                member.device_grant_id.label("device_grant_id"),
                turn.turn_id.label("turn_id"),
                turn.child_id.label("turn_child_id"),
                turn.document_epoch.label("turn_epoch"),
                turn.device_grant_id.label("turn_grant_id"),
            )
            .select_from(session)
            .join(
                group,
                (group.organization_id == session.organization_id)
                & (group.session_id == session.session_id)
                & (group.group_id == canvas_id),
            )
            .join(
                aggregate,
                (aggregate.organization_id == session.organization_id)
                & (aggregate.aggregate_id == canvas_id),
            )
            .join(
                member,
                (member.organization_id == session.organization_id)
                & (member.class_id == session.class_id)
                & (member.session_id == session.session_id)
                & (member.group_id == group.group_id)
                & (member.state == "admitted"),
            )
            .outerjoin(
                turn,
                (turn.organization_id == session.organization_id)
                & (turn.session_id == session.session_id)
                & (turn.group_id == group.group_id)
                & (turn.canvas_id == canvas_id)
                & (turn.state == "active"),
            )
            .where(
                session.organization_id == self._organization_id,
                session.class_id == self._class_id,
                session.session_id == self._session_id,
            )
            .order_by(member.membership_id, turn.turn_id)
        )
        try:
            rows = [dict(row) for row in self._connection.execute(statement).mappings()]
        except SQLAlchemyError:
            return []
        if not rows:
            return []
        row = rows[0]
        configuration = row["configuration"]
        if (
            row["session_state"] != "active"
            or row["group_state"] not in {"active", "locked"}
            or not isinstance(configuration, dict)
            or configuration.get("purpose_ref") != PILOT_SYNTHETIC_POLICY_V1.purpose_code
            or not isinstance(configuration.get("pilot_run_ref"), str)
            or not configuration["pilot_run_ref"]
        ):
            return []
        return rows

    @staticmethod
    def _roster(rows: list[dict[str, Any]]) -> GroupRoster | None:
        if not rows:
            return None
        memberships = {
            row["membership_id"]: (row["child_id"], row["membership_state"], row["device_grant_id"])
            for row in rows
        }
        children = tuple(sorted(value[0] for value in memberships.values()))
        if len(children) != len(set(children)):
            return None
        revision = context_revision(
            {
                "schema_version": "be1-pilot-roster-v1",
                "memberships": json.dumps(sorted(memberships.items()), separators=(",", ":")),
            }
        )
        return GroupRoster(rows[0]["group_id"], children, revision)

    def canvas(self, organization_id: str, canvas_id: str) -> CanvasFacts | None:
        if organization_id != self._organization_id:
            return None
        rows = self._projection(canvas_id)
        roster = self._roster(rows)
        if roster is None:
            return None
        try:
            candidate = self._export_source(organization_id, canvas_id)
            source = (
                CanvasSourceExportV1.model_validate(candidate.model_dump())
                if candidate is not None
                else None
            )
        except Exception:
            # An unavailable or malformed owner export cannot authorize a canvas.
            return None
        if (
            source is None
            or source.organization_id != organization_id
            or source.session_id != self._session_id
            or source.canvas_id != canvas_id
            or source.document_revision != rows[0]["aggregate_revision"]
            or any(
                row["turn_id"] is not None and row["turn_epoch"] != source.document_epoch
                for row in rows
            )
        ):
            return None
        revision = context_revision(
            {
                "schema_version": "be1-pilot-canvas-context-v1",
                "organization_id": organization_id,
                "class_id": self._class_id,
                "session_id": self._session_id,
                "session_revision": rows[0]["session_revision"],
                "run_ref": rows[0]["configuration"]["pilot_run_ref"],
                "source_sha256": source.source_sha256,
                "roster_revision": roster.revision,
            }
        )
        return CanvasFacts(
            organization_id=organization_id,
            class_id=self._class_id,
            session_id=self._session_id,
            canvas_id=canvas_id,
            mode="collaborative",
            group_id=roster.group_id,
            personal_participant_id=None,
            session_active=True,
            document_epoch=source.document_epoch,
            context_revision=revision,
            region_policy_revision=PILOT_SYNTHETIC_POLICY_V1.region_policy_revision,
            regions=PILOT_SYNTHETIC_POLICY_V1.regions,
            age_policy_ref=PILOT_SYNTHETIC_POLICY_V1.age_policy_ref,
        )

    def roster(self, session_id: str, group_id: str) -> GroupRoster | None:
        if session_id != self._session_id:
            return None
        return self._roster(self._projection(group_id))

    def current_turn(self, canvas_id: str) -> Contributor | None:
        rows = self._projection(canvas_id)
        roster = self._roster(rows)
        turns = {row["turn_id"]: row for row in rows if row["turn_id"] is not None}
        if roster is None or len(turns) != 1:
            return None
        turn = next(iter(turns.values()))
        if turn["turn_child_id"] not in roster.members:
            return None
        matching_member = next(row for row in rows if row["child_id"] == turn["turn_child_id"])
        if matching_member["device_grant_id"] != turn["turn_grant_id"]:
            return None
        revision = context_revision(
            {
                "schema_version": "be1-pilot-turn-v1",
                "turn_id": turn["turn_id"],
                "child_id": turn["turn_child_id"],
                "document_epoch": turn["turn_epoch"],
                "device_grant_id": turn["turn_grant_id"],
            }
        )
        return Contributor(turn["turn_child_id"], turn["turn_id"], revision)

    def members(
        self,
        organization_id: str,
        participant_ids: tuple[str, ...],
        purpose_code: str,
        *,
        scope: EligibilityScope | None = None,
    ) -> tuple[MemberFact, ...]:
        if (
            organization_id != self._organization_id
            or scope is None
            or scope.class_id != self._class_id
        ):
            return ()
        return super().members(organization_id, participant_ids, purpose_code, scope=scope)


__all__ = ["PostgresAssistanceMemberAdapter", "PostgresAssistanceOwnerAdapter"]
