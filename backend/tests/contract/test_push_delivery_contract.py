from __future__ import annotations

import ast
from pathlib import Path

from sketch2life.application.ports.push_delivery import PushDeliveryStore
from sketch2life.infrastructure.notifications.push_delivery_repository import SqlPushDeliveryStore
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS

_BACKEND = Path(__file__).resolve().parents[2]
_PROVIDER_MODULES = {
    "firebase_admin",
    "pywebpush",
    "apns2",
    "aioapns",
    "fcm_django",
}


def test_sql_store_exposes_the_delivery_store_protocol() -> None:
    for method in ("enroll", "claim_due", "record_outcome"):
        assert callable(getattr(SqlPushDeliveryStore, method))
        assert method in PushDeliveryStore.__dict__


def test_build_sender_has_no_production_composition(monkeypatch) -> None:
    from sketch2life.application.ports.push_delivery import PushSenderUnavailable
    from sketch2life.infrastructure.notifications.notification_worker import build_push_sender

    for environment in (None, "production", "staging"):
        if environment is None:
            monkeypatch.delenv("SKETCH2LIFE_ENV", raising=False)
        else:
            monkeypatch.setenv("SKETCH2LIFE_ENV", environment)
        try:
            build_push_sender()
        except PushSenderUnavailable:
            pass
        else:
            raise AssertionError("production sender composition must fail closed")


def test_openapi_catalog_has_no_push_delivery_route() -> None:
    paths = [key[1] for key in MOUNTED_OPERATIONS]
    assert not any("push-deliver" in path for path in paths)


def test_delivery_composition_imports_no_provider_sdk() -> None:
    source_paths = (
        _BACKEND / "src/sketch2life/application/services/push_delivery.py",
        _BACKEND / "src/sketch2life/infrastructure/notifications/push_delivery_fakes.py",
        _BACKEND / "src/sketch2life/infrastructure/notifications/push_delivery_repository.py",
        _BACKEND / "src/sketch2life/infrastructure/notifications/notification_worker.py",
    )
    imported_roots: set[str] = set()
    for source_path in source_paths:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(_PROVIDER_MODULES)
