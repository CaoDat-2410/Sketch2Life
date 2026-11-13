"""Offline contract tests for the BE1-backed Parent-role adapter."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import ParentRoleStoreUnavailable
from sketch2life.infrastructure.persistence.be1_parent_role_adapter import (
    Be1ParentRoleAdapter,
)


class _Result:
    def __init__(self, row: tuple[str, str, str | None] | None) -> None:
        self._row = row

    def one_or_none(self) -> tuple[str, str, str | None] | None:
        return self._row


class _Session:
    def __init__(self, row: tuple[str, str, str | None] | None = None) -> None:
        self.row = row
        self.closed = False
        self.failure: SQLAlchemyError | None = None

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def execute(self, _statement: object) -> _Result:
        if self.failure is not None:
            raise self.failure
        return _Result(self.row)

    def close(self) -> None:
        self.closed = True


def _adapter_for(session: _Session) -> Be1ParentRoleAdapter:
    return Be1ParentRoleAdapter(lambda: session)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (None, False),
        (("issuer-1", "active", "parent"), True),
        (("issuer-1", "active", "teacher"), False),
        (("issuer-1", "active", "school_manager"), False),
        (("issuer-1", "active", "platform_admin"), False),
        (("issuer-1", "inactive", "parent"), False),
        (("issuer-2", "active", "parent"), False),
        (("issuer-1", "active", None), False),
    ],
)
def test_adapter_only_accepts_the_matching_active_parent_identity(
    row: tuple[str, str, str | None] | None, expected: bool
) -> None:
    session = _Session(row)
    adapter = _adapter_for(session)

    actual = adapter.has_active_parent_role(
        principal=VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    )

    assert actual is expected
    assert session.closed


def test_adapter_fails_closed_on_role_store_error() -> None:
    session = _Session()
    session.failure = SQLAlchemyError("synthetic database failure")
    adapter = _adapter_for(session)

    with pytest.raises(ParentRoleStoreUnavailable):
        adapter.has_active_parent_role(
            principal=VerifiedPrincipal("subject-1", "issuer-1", frozenset())
        )

    assert session.closed
