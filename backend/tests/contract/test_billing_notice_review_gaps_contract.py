# ruff: noqa: E501, F811, SIM117, B023
"""Missing contract tests for E4 T-BILLN1 named in IMPL_REVIEW_E_E4_R1_20261125.md."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import get_type_hints

from sketch2life.domain import billing_notice as domain_billing_notice
from sketch2life.infrastructure.notifications import billing_notice_store

_BACKEND = Path(__file__).resolve().parents[2]
_DOMAIN_PATH = _BACKEND / "src/sketch2life/domain/billing_notice.py"
_PORT_PATH = _BACKEND / "src/sketch2life/application/ports/billing_notice.py"
_SERVICE_PATH = _BACKEND / "src/sketch2life/application/services/billing_notice.py"
_STORE_PATH = _BACKEND / "src/sketch2life/infrastructure/notifications/billing_notice_store.py"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_billing_notice_store_type_hints_resolve_without_name_errors() -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md P2-1 & P3-1 (NotificationCommandV1 annotation & domain export)"""
    assert "BillingNoticeSource" in domain_billing_notice.__all__
    for target in (
        billing_notice_store._command,
        billing_notice_store.SqlBillingNoticeStore.scan_candidates,
        billing_notice_store.SqlBillingNoticeStore.enqueue_if_due,
        billing_notice_store.build_billing_notice_sweep,
    ):
        hints = get_type_hints(target)
        assert hints


def test_billing_notice_layers_stay_decoupled_and_read_only_on_billing_services() -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (layering & no Billing writer/HTTP imports)"""
    domain_imports = _imported_modules(_DOMAIN_PATH)
    s2l_domain_imports = {m for m in domain_imports if m.startswith("sketch2life.")}
    assert s2l_domain_imports <= {"sketch2life.domain.billing_capacity"}

    for app_path in (_PORT_PATH, _SERVICE_PATH):
        app_imports = _imported_modules(app_path)
        assert not any(
            m.startswith(("sketch2life.infrastructure", "sketch2life.interfaces", "fastapi", "sqlalchemy"))
            for m in app_imports
        )

    all_imports = domain_imports | _imported_modules(_PORT_PATH) | _imported_modules(_SERVICE_PATH) | _imported_modules(_STORE_PATH)
    forbidden_prefixes = (
        "fastapi",
        "sketch2life.interfaces",
        "sketch2life.infrastructure.billing.quota_commerce",
        "sketch2life.infrastructure.platform_admin.sandbox_billing",
        "sketch2life.infrastructure.platform_admin.sandbox_capacity",
    )
    assert not any(m == p or m.startswith(p + ".") for m in all_imports for p in forbidden_prefixes)
