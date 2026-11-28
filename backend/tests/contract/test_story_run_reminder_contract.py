"""T-1d2 adds an internal producer and preserves the existing notification HTTP contract."""

from __future__ import annotations

from sketch2life.contracts.schemas.notifications import (
    NotificationPageV1,
    NotificationReadAllV1,
    NotificationV1,
)
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.routers.notifications import router as notification_router

EXPECTED_NOTIFICATION_OPERATIONS = {
    ("get", "/v1/notifications"),
    ("post", "/v1/notifications/{inbox_item_id}/read"),
    ("post", "/v1/notifications/read-all"),
    ("post", "/v1/notifications/push-endpoints"),
    ("delete", "/v1/notifications/push-endpoints/{endpoint_id}"),
}


def test_no_reminder_http_route_or_catalog_entry_is_added() -> None:
    mounted = {
        (method.lower(), route.path)
        for route in notification_router.routes
        for method in (route.methods or set())
        if method.upper() not in {"HEAD", "OPTIONS"}
    }
    catalog = {
        key
        for key in MOUNTED_OPERATIONS
        if key[1].startswith("/v1/notifications")
    }
    assert mounted == EXPECTED_NOTIFICATION_OPERATIONS
    assert catalog == EXPECTED_NOTIFICATION_OPERATIONS
    assert not any(
        "reminder" in path
        for _, path in MOUNTED_OPERATIONS
        if path.startswith("/v1/notifications")
    )


def test_existing_inbox_route_and_response_contracts_remain_unchanged() -> None:
    assert MOUNTED_OPERATIONS[("get", "/v1/notifications")]["handler"] == (
        "notifications.py::list_notifications"
    )
    assert MOUNTED_OPERATIONS[("post", "/v1/notifications/{inbox_item_id}/read")]["handler"] == (
        "notifications.py::mark_notification_read"
    )
    assert MOUNTED_OPERATIONS[("post", "/v1/notifications/read-all")]["handler"] == (
        "notifications.py::mark_all_notifications_read"
    )
    assert set(NotificationPageV1.model_fields) == {
        "contract",
        "items",
        "next_cursor",
        "unread_count",
    }
    assert set(NotificationV1.model_fields) == {
        "contract",
        "inbox_item_id",
        "notification_type",
        "template_version",
        "safe_parameters",
        "created_at",
        "read_at",
        "expires_at",
    }
    assert set(NotificationReadAllV1.model_fields) == {"contract", "marked_count"}


def test_mark_read_key_and_existing_inbox_cursor_inputs_stay_catalogued() -> None:
    inbox = MOUNTED_OPERATIONS[("get", "/v1/notifications")]
    read_one = MOUNTED_OPERATIONS[("post", "/v1/notifications/{inbox_item_id}/read")]
    read_all = MOUNTED_OPERATIONS[("post", "/v1/notifications/read-all")]
    assert inbox["request_inputs"] == "query `limit`: integer; query `cursor`: string"
    assert "header `Idempotency-Key*`: string" in read_one["request_inputs"]
    assert "header `Idempotency-Key*`: string" in read_all["request_inputs"]
