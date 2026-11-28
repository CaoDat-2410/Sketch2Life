"""Offline contract checks for the manager's explicit placement routes."""

import inspect

import pytest
from fastapi import HTTPException

from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_contract_amendments import SYNTHETIC_RESPONSE_EXAMPLES
from sketch2life.interfaces.http.routers import be1_registry as routes
from sketch2life.interfaces.http.routers.be1_common import failure

LIST = ("get", "/api/be1/v1/organizations/{organization_id}/unplaced-profile-refs")
PLACE = ("post", "/api/be1/v1/classes/{class_id}/profiles/{child_id}/place")


def test_catalog_and_privacy_contract():
    assert MOUNTED_OPERATIONS[LIST]["handler"] == "be1_registry.py::list_unplaced_profile_refs"
    assert MOUNTED_OPERATIONS[PLACE]["handler"] == "be1_registry.py::place_profile"
    assert set(SYNTHETIC_RESPONSE_EXAMPLES[LIST]["items"][0]) == {"child_id"}
    assert set(SYNTHETIC_RESPONSE_EXAMPLES[PLACE]) == {
        "contract",
        "child_id",
        "class_id",
        "enrollment_id",
        "class_revision",
    }
    assert "payload" not in inspect.signature(routes.place_profile).parameters


@pytest.mark.parametrize(
    "role,status", [("teacher", 403), ("guide", 403), ("observer", 403), ("outside", 404)]
)
def test_role_and_scope_refusals_precede_reads(monkeypatch, role, status):
    def refuse(*args, **kwargs):
        assert kwargs["roles"] == {"school_admin"}
        raise failure(
            status, "ACTION_NOT_ALLOWED" if status == 403 else "RESOURCE_NOT_FOUND", "refused"
        )

    monkeypatch.setattr(routes, "require_assignment", refuse)
    with pytest.raises(HTTPException) as caught:
        routes.list_unplaced_profile_refs("org", 10, None, object(), object())
    assert caught.value.status_code == status
    if role == "outside":
        assert caught.value.detail["code"] == "RESOURCE_NOT_FOUND"
