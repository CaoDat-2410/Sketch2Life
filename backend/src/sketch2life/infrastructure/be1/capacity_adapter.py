"""BE1-facing read and command adapter for organization class capacity."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import OrganizationModel
from sketch2life.infrastructure.persistence.billing_models import (
    SubscriptionEventModel,
    SubscriptionModel,
)
from sketch2life.infrastructure.platform_admin.sandbox_billing import SandboxBillingService
from sketch2life.infrastructure.platform_admin.sandbox_capacity import SandboxCapacityService


class CapacityDependencyUnavailable(RuntimeError):
    """The adapter cannot safely establish an organization capacity view or lock."""


class _CommitControlledSession:
    """Delegate Billing work to the BE1 Session but hold its commit for the outer command.

    Billing's current public command method always calls ``commit``. BE1 has to commit the
    Billing receipt, class projection, audit event, and its own receipt together, so this small
    session proxy changes only that transaction boundary. Query, lock, fingerprint, receipt,
    and response behavior still come from ``SandboxBillingService.command`` itself.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


class _CapacityViewContext:
    """Minimal context required by Billing's public capacity view implementation."""

    def __init__(self, db: Session, actor: str, clock: Callable[[], datetime]) -> None:
        self.db = db
        self.actor = actor
        self.clock = clock


class Be1CapacityAdapter:
    """Resolve capacity by organization and delegate all subscription rules to Billing."""

    def __init__(
        self,
        db: Session,
        actor: str,
        settings: Settings | None,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.db = db
        self.actor = actor
        self.settings = settings
        self.clock = clock
        self._view_service = SandboxCapacityService(  # type: ignore[no-untyped-call]
            _CapacityViewContext(db, actor, clock)
        )

    @staticmethod
    def _included_capacity_view(organization_id: str) -> dict[str, Any]:
        return {
            "subscription_id": None,
            "organization_ref": organization_id,
            "price_id": None,
            "addon_slots": 0,
            "capacity": 10,
            "state": "NONE",
            "revision": 0,
            "period_start": None,
            "period_end": None,
            "scheduled_addon_slots": None,
            "suspended_class_refs": [],
            "provider": "BILLING",
        }

    def view_for_organization(
        self, organization_id: str, *, lock: bool = False
    ) -> tuple[SubscriptionModel | None, dict[str, Any]]:
        query = select(SubscriptionModel).where(
            SubscriptionModel.organization_ref == organization_id
        )
        if lock:
            query = query.with_for_update()
        row = self.db.scalar(query)
        if row is None:
            if lock:
                organization = self.db.scalar(
                    select(OrganizationModel)
                    .where(OrganizationModel.organization_id == organization_id)
                    .with_for_update()
                )
                if organization is None:
                    raise AdminError("NOT_FOUND", 404)
            return None, self._included_capacity_view(organization_id)
        return row, self._view_service.view(row)  # type: ignore[no-untyped-call]

    def _command_service(self) -> SandboxBillingService:
        if self.settings is None:
            raise AdminError("BILLING_SANDBOX_DISABLED", 403)
        return SandboxBillingService(  # type: ignore[no-untyped-call]
            _CommitControlledSession(self.db),
            self.actor,
            self.settings,
            clock=self.clock,
        )

    def command_service(self) -> SandboxCapacityService:
        """Build Billing's gated command service for a PATCH write."""
        return SandboxCapacityService(self._command_service())  # type: ignore[no-untyped-call]

    def scheduled_change(
        self,
        row: SubscriptionModel | None,
        view: dict[str, Any],
    ) -> dict[str, Any] | None:
        if row is None or view.get("scheduled_addon_slots") is None:
            return None
        plan = self._view_service.plan(row)  # type: ignore[no-untyped-call]
        if plan is None:
            return None
        class_refs = list(
            self.db.scalars(
                select(SubscriptionEventModel.class_ref)
                .where(
                    SubscriptionEventModel.group_ref == plan.group_ref,
                    SubscriptionEventModel.class_ref.is_not(None),
                )
                .order_by(SubscriptionEventModel.created_at, SubscriptionEventModel.event_id)
            )
        )
        addon_slots = int(view["scheduled_addon_slots"])
        return {
            "addon_slots": addon_slots,
            "capacity": 10 + addon_slots,
            "effective_at": plan.effective_at,
            "suspend_class_refs": [str(class_ref) for class_ref in class_refs],
        }


def effective_active_class_count(active_class_refs: set[str], due_suspended_refs: set[str]) -> int:
    """Count active classes after applying Billing's due scheduled suspensions."""
    return len(active_class_refs - due_suspended_refs)
