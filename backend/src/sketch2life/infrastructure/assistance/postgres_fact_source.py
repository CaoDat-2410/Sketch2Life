"""One-statement, synthetic-only reader for current BE1 facts on a supplied connection."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import Connection, select
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.domain.eligibility import EligibilityScope, ProvisionalDataOrigin
from sketch2life.domain.vision_analysis import ProviderContextMode
from sketch2life.infrastructure.assistance.be1_fact_reader import (
    BE1FactRequest,
    BE1FactSnapshot,
    BE1FactSource,
    BE1SyntheticProofFact,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomSessionModel,
    ManagedProfileModel,
    SessionGroupModel,
    SessionMembershipModel,
    SyntheticEligibilityProofModel,
)

Clock = Callable[[], datetime]


class PostgresBE1FactSource(BE1FactSource):
    """Read the exact profile/session/membership/group/proof projection in one statement.

    The supplied SQLAlchemy connection is never opened, committed, or closed here. Duplicate
    matching proof rows remain visible in the result and make the projection unavailable.
    """

    def __init__(
        self,
        connection: Connection,
        *,
        environment: str,
        pilot_enabled: bool,
        clock: Clock = lambda: datetime.now(UTC),
    ) -> None:
        self._connection = connection
        self._environment = environment
        self._pilot_enabled = pilot_enabled
        self._clock = clock
        self.statements = 0

    def current_facts(self, request: BE1FactRequest) -> BE1FactSnapshot | None:
        if (
            self._environment not in {"local", "test"}
            or self._pilot_enabled is not True
            or request.context_mode is not ProviderContextMode.IMAGE_ONLY
            or request.audience_participant_ids != (request.child_id,)
            or not all(
                (
                    request.organization_id,
                    request.class_id,
                    request.session_id,
                    request.child_id,
                    request.purpose_ref,
                )
            )
        ):
            return None

        profile = ManagedProfileModel
        session = ClassroomSessionModel
        membership = SessionMembershipModel
        group = SessionGroupModel
        proof = SyntheticEligibilityProofModel
        statement = (
            select(
                profile.child_id.label("profile_child_id"),
                profile.organization_id.label("profile_organization_id"),
                profile.class_id.label("profile_class_id"),
                profile.data_origin.label("profile_data_origin"),
                profile.state.label("profile_state"),
                profile.age_months.label("profile_age_months"),
                profile.age_revision.label("profile_age_revision"),
                profile.age_source.label("profile_age_source"),
                profile.consent_id.label("profile_consent_id"),
                profile.consent_purpose_ref.label("profile_consent_purpose_ref"),
                session.session_id.label("session_id"),
                session.organization_id.label("session_organization_id"),
                session.class_id.label("session_class_id"),
                session.state.label("session_state"),
                session.configuration.label("session_configuration"),
                membership.membership_id.label("membership_id"),
                membership.organization_id.label("membership_organization_id"),
                membership.session_id.label("membership_session_id"),
                membership.class_id.label("membership_class_id"),
                membership.child_id.label("membership_child_id"),
                membership.state.label("membership_state"),
                membership.group_id.label("membership_group_id"),
                group.group_id.label("group_id"),
                group.organization_id.label("group_organization_id"),
                group.session_id.label("group_session_id"),
                group.state.label("group_state"),
                proof.evidence_id.label("proof_evidence_id"),
                proof.schema_version.label("proof_schema_version"),
                proof.data_origin.label("proof_data_origin"),
                proof.organization_id.label("proof_organization_id"),
                proof.class_id.label("proof_class_id"),
                proof.child_profile_id.label("proof_child_id"),
                proof.purpose_ref.label("proof_purpose_ref"),
                proof.run_ref.label("proof_run_ref"),
                proof.session_id.label("proof_session_id"),
                proof.issued_at.label("proof_issued_at"),
                proof.expires_at.label("proof_expires_at"),
                proof.revoked_at.label("proof_revoked_at"),
                proof.revocation_revision.label("proof_revocation_revision"),
            )
            .select_from(profile)
            .join(
                session,
                (session.organization_id == profile.organization_id)
                & (session.class_id == profile.class_id)
                & (session.session_id == request.session_id),
            )
            .join(
                membership,
                (membership.organization_id == session.organization_id)
                & (membership.class_id == session.class_id)
                & (membership.session_id == session.session_id)
                & (membership.child_id == profile.child_id),
            )
            .outerjoin(
                group,
                (group.organization_id == membership.organization_id)
                & (group.session_id == membership.session_id)
                & (group.group_id == membership.group_id),
            )
            .outerjoin(
                proof,
                (proof.organization_id == profile.organization_id)
                & (proof.class_id == profile.class_id)
                & (proof.child_profile_id == profile.child_id)
                & (proof.purpose_ref == request.purpose_ref)
                & (proof.session_id == session.session_id)
                & (proof.run_ref == session.configuration["pilot_run_ref"].as_string()),
            )
            .where(
                profile.organization_id == request.organization_id,
                profile.class_id == request.class_id,
                profile.child_id == request.child_id,
                membership.organization_id == request.organization_id,
                membership.session_id == request.session_id,
            )
        )

        try:
            self.statements += 1
            rows = self._connection.execute(statement).mappings().all()
        except SQLAlchemyError:
            return None
        if len(rows) != 1:
            return None

        row = rows[0]
        configuration = row["session_configuration"]
        purpose_ref = configuration.get("purpose_ref") if isinstance(configuration, dict) else None
        group_id = row["membership_group_id"]
        if (
            row["profile_organization_id"] != request.organization_id
            or row["profile_class_id"] != request.class_id
            or row["profile_child_id"] != request.child_id
            or row["session_organization_id"] != request.organization_id
            or row["session_class_id"] != request.class_id
            or row["session_id"] != request.session_id
            or row["membership_organization_id"] != request.organization_id
            or row["membership_class_id"] != request.class_id
            or row["membership_session_id"] != request.session_id
            or row["membership_child_id"] != request.child_id
            or not isinstance(purpose_ref, str)
            or purpose_ref != request.purpose_ref
            or not isinstance(group_id, str)
            or not group_id
            or row["group_id"] != group_id
            or row["group_organization_id"] != request.organization_id
            or row["group_session_id"] != request.session_id
            or row["group_state"] not in {"active", "locked"}
            or row["profile_consent_id"] is not None
            or row["profile_consent_purpose_ref"] is not None
        ):
            return None

        age_months = row["profile_age_months"]
        age_revision = row["profile_age_revision"]
        if type(age_months) is not int or type(age_revision) is not int:
            return None

        proof_fact = self._proof_fact(row)
        if row["proof_evidence_id"] is not None and proof_fact is None:
            return None

        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            return None
        origin = row["profile_data_origin"]
        try:
            profile_origin: ProvisionalDataOrigin | str | None = ProvisionalDataOrigin(origin)
        except (TypeError, ValueError):
            profile_origin = origin if isinstance(origin, str) else None

        run_ref = configuration.get("pilot_run_ref")
        return BE1FactSnapshot(
            organization_id=request.organization_id,
            class_id=request.class_id,
            session_id=request.session_id,
            session_state=str(row["session_state"]),
            session_run_ref=run_ref if isinstance(run_ref, str) else None,
            environment=self._environment,
            pilot_enabled=self._pilot_enabled,
            purpose_ref=purpose_ref,
            child_id=request.child_id,
            profile_origin=profile_origin,
            profile_state=str(row["profile_state"]),
            age_months=age_months,
            age_revision=age_revision,
            age_source=row["profile_age_source"]
            if isinstance(row["profile_age_source"], str)
            else None,
            consent_record_ref=None,
            consent_revision=None,
            consent_state=None,
            legal_consent_effective=False,
            purpose_granted=False,
            membership_state=str(row["membership_state"]),
            group_id=group_id,
            proof=proof_fact,
            evaluated_at=now.astimezone(UTC),
        )

    @staticmethod
    def _proof_fact(row: object) -> BE1SyntheticProofFact | None:
        try:
            values = row  # SQLAlchemy RowMapping supports string-key access.
            evidence_id = values["proof_evidence_id"]  # type: ignore[index]
            if evidence_id is None:
                return None
            schema_version = values["proof_schema_version"]  # type: ignore[index]
            data_origin = values["proof_data_origin"]  # type: ignore[index]
            organization_id = values["proof_organization_id"]  # type: ignore[index]
            class_id = values["proof_class_id"]  # type: ignore[index]
            child_id = values["proof_child_id"]  # type: ignore[index]
            purpose_ref = values["proof_purpose_ref"]  # type: ignore[index]
            run_ref = values["proof_run_ref"]  # type: ignore[index]
            issued_at = values["proof_issued_at"]  # type: ignore[index]
            expires_at = values["proof_expires_at"]  # type: ignore[index]
            session_id = values["proof_session_id"]  # type: ignore[index]
            revoked_at = values["proof_revoked_at"]  # type: ignore[index]
            revision = values["proof_revocation_revision"]  # type: ignore[index]
            if (
                not all(
                    isinstance(value, str) and value
                    for value in (
                        evidence_id,
                        schema_version,
                        data_origin,
                        organization_id,
                        class_id,
                        child_id,
                        purpose_ref,
                        run_ref,
                    )
                )
                or not isinstance(issued_at, datetime)
                or not isinstance(expires_at, datetime)
                or (session_id is not None and not isinstance(session_id, str))
                or (revoked_at is not None and not isinstance(revoked_at, datetime))
                or type(revision) is not int
            ):
                return None
            return BE1SyntheticProofFact(
                evidence_id=evidence_id,
                schema_version=schema_version,
                data_origin=data_origin,
                scope=EligibilityScope(
                    organization_id=organization_id,
                    class_id=class_id,
                    child_id=child_id,
                    purpose_ref=purpose_ref,
                ),
                run_ref=run_ref,
                session_id=session_id,
                issued_at=issued_at,
                expires_at=expires_at,
                revoked_at=revoked_at,
                revocation_revision=revision,
            )
        except (KeyError, TypeError, ValueError):
            return None


__all__ = ["PostgresBE1FactSource"]
