from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.routers import be1_billing


def _principal() -> VerifiedPrincipal:
    return VerifiedPrincipal(
        subject="school-manager-1",
        issuer="test-issuer",
        roles=frozenset(),
        token_id="test-token",
    )


def test_school_manager_can_reconcile_only_an_invoice_owned_by_their_school(monkeypatch):
    principal = _principal()
    db = object()
    invoice = SimpleNamespace(owner_kind="ORGANIZATION", owner_ref="school-1")
    commerce = Mock()
    commerce.invoice.return_value = invoice
    commerce.reconcile_invoice.return_value = {
        "invoice_id": "invoice-1",
        "state": "PAID",
        "reconciled": True,
    }
    assignment_check = Mock()
    monkeypatch.setattr(be1_billing, "require_assignment", assignment_check)
    monkeypatch.setattr(be1_billing, "_commerce", lambda _db, _principal: commerce)

    result = be1_billing.reconcile_school_invoice(
        "school-1", "invoice-1", principal=principal, db=db
    )

    assert result == {"invoice_id": "invoice-1", "state": "PAID", "reconciled": True}
    assignment_check.assert_called_once_with(db, principal, "school-1", roles={"school_admin"})
    commerce.reconcile_invoice.assert_called_once_with("invoice-1")


def test_school_manager_cannot_reconcile_another_schools_invoice(monkeypatch):
    commerce = Mock()
    commerce.invoice.return_value = SimpleNamespace(owner_kind="ORGANIZATION", owner_ref="school-2")
    monkeypatch.setattr(be1_billing, "require_assignment", Mock())
    monkeypatch.setattr(be1_billing, "_commerce", lambda _db, _principal: commerce)

    with pytest.raises(HTTPException) as error:
        be1_billing.reconcile_school_invoice(
            "school-1", "invoice-1", principal=_principal(), db=object()
        )

    assert error.value.detail["code"] == "INVOICE_NOT_FOUND"
    commerce.reconcile_invoice.assert_not_called()


def test_school_manager_can_cancel_only_their_own_expired_payment(monkeypatch):
    principal = _principal()
    db = object()
    commerce = Mock()
    commerce.invoice.return_value = SimpleNamespace(owner_kind="ORGANIZATION", owner_ref="school-1")
    commerce.cancel_expired_vnpay_invoice.return_value = {
        "invoice_id": "invoice-1",
        "state": "CANCELED",
        "canceled": True,
        "reconciled": True,
    }
    assignment_check = Mock()
    monkeypatch.setattr(be1_billing, "require_assignment", assignment_check)
    monkeypatch.setattr(be1_billing, "_commerce", lambda _db, _principal: commerce)

    result = be1_billing.cancel_school_invoice(
        "school-1", "invoice-1", principal=principal, db=db
    )

    assert result["state"] == "CANCELED"
    assignment_check.assert_called_once_with(db, principal, "school-1", roles={"school_admin"})
    commerce.cancel_expired_vnpay_invoice.assert_called_once_with("invoice-1")


def test_school_manager_cannot_cancel_another_schools_payment(monkeypatch):
    commerce = Mock()
    commerce.invoice.return_value = SimpleNamespace(owner_kind="ORGANIZATION", owner_ref="school-2")
    monkeypatch.setattr(be1_billing, "require_assignment", Mock())
    monkeypatch.setattr(be1_billing, "_commerce", lambda _db, _principal: commerce)

    with pytest.raises(HTTPException) as error:
        be1_billing.cancel_school_invoice(
            "school-1", "invoice-1", principal=_principal(), db=object()
        )

    assert error.value.detail["code"] == "INVOICE_NOT_FOUND"
    commerce.cancel_expired_vnpay_invoice.assert_not_called()
