"""BE1 identity-backed Parent role reader; PostgreSQL coverage is not included in S1a-P2."""

from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import ParentRoleStoreUnavailable
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel


class Be1ParentRoleAdapter:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        try:
            with self._session_factory() as session:
                row = session.execute(
                    select(
                        AdultIdentityModel.issuer,
                        AdultIdentityModel.state,
                        AdultIdentityModel.account_role,
                    ).where(AdultIdentityModel.subject == principal.subject)
                ).one_or_none()
        except SQLAlchemyError as exc:
            raise ParentRoleStoreUnavailable from exc
        if row is None:
            return False
        issuer, state, account_role = cast(tuple[str, str, str | None], tuple(row))
        return (
            issuer == principal.issuer
            and state == "active"
            and account_role == "parent"
        )
