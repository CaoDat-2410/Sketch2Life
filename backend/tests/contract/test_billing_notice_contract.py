from __future__ import annotations

import ast
from pathlib import Path

from sketch2life.application.ports.billing_notice import (
    BillingNoticeScanPort,
    BillingNoticeTransactionPort,
)
from sketch2life.infrastructure.notifications.billing_notice_store import SqlBillingNoticeStore
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS

_BACKEND = Path(__file__).resolve().parents[2]
_MODULES = (
    _BACKEND / "src/sketch2life/domain/billing_notice.py",
    _BACKEND / "src/sketch2life/application/ports/billing_notice.py",
    _BACKEND / "src/sketch2life/application/services/billing_notice.py",
    _BACKEND / "src/sketch2life/infrastructure/notifications/billing_notice_store.py",
    _BACKEND / "src/sketch2life/infrastructure/notifications/notification_worker.py",
    _BACKEND / "src/sketch2life/application/services/notification_templates.py",
)
_PROVIDER_MODULES = {"firebase_admin", "pywebpush", "apns2", "aioapns", "fcm_django"}


def test_sql_store_exposes_both_billing_notice_ports() -> None:
    for method in ("scan_candidates",):
        assert callable(getattr(SqlBillingNoticeStore, method))
        assert method in BillingNoticeScanPort.__dict__
    assert callable(SqlBillingNoticeStore.enqueue_if_due)
    assert "enqueue_if_due" in BillingNoticeTransactionPort.__dict__


def test_openapi_catalog_has_no_billing_notice_route() -> None:
    assert not any("billing-notice" in path for _, path in MOUNTED_OPERATIONS)


def test_billing_notice_modules_import_no_provider_sdk_or_provider_adapter() -> None:
    imported_modules: set[str] = set()
    for source_path in _MODULES:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    imported_roots = {module.split(".")[0] for module in imported_modules}
    assert imported_roots.isdisjoint(_PROVIDER_MODULES)
    assert not any(
        module == "sketch2life.infrastructure.billing.providers"
        or module.startswith("sketch2life.infrastructure.billing.providers.")
        for module in imported_modules
    )


def test_billing_notice_worker_refuses_outside_local_test(
    monkeypatch,
) -> None:
    from sketch2life.infrastructure.notifications import notification_worker as worker

    monkeypatch.setattr(
        worker,
        "create_core_engine",
        lambda: (_ for _ in ()).throw(AssertionError("engine must not be created")),
    )

    for environment in (None, "production", "staging"):
        if environment is None:
            monkeypatch.delenv("SKETCH2LIFE_ENV", raising=False)
        else:
            monkeypatch.setenv("SKETCH2LIFE_ENV", environment)
        assert worker.main(["billing-notices", "--once"]) == 2
