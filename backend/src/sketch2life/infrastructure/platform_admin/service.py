"""Transactional Admin foundation; only metadata crosses owner boundaries."""

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.platform_admin import AdminError, require_revision
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel, OrganizationModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.platform_models import (
    AccountPreferenceModel,
    AdminCommandReceiptModel,
    AuditRetentionPolicyModel,
    EmailDeliveryModel,
    InboxItemModel,
    PermissionGrantModel,
)
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)


def begin_receipt(db, actor, operation, key, payload):
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": json.dumps((actor, operation, key))},
        )
    receipt = db.get(AdminCommandReceiptModel, (actor, operation, key))
    if receipt is not None and receipt.fingerprint != fingerprint:
        raise AdminError("IDEMPOTENCY_CONFLICT")
    return receipt, fingerprint


class PlatformAdminService:
    def __init__(self, db: Session, principal: VerifiedPrincipal):
        self.db, self.principal = db, principal

    def identity(self, *, admin: bool = True, content: bool = False):
        row = (
            self.db.scalar(
                select(AdultIdentityModel)
                .where(AdultIdentityModel.subject == self.principal.subject)
                .with_for_update()
            )
            if content
            else self.db.get(AdultIdentityModel, self.principal.subject)
        )
        if (
            row is None
            or row.state != "active"
            or row.account_role is None
            or row.issuer != self.principal.issuer
            or (admin and row.account_role != "platform_admin")
        ):
            raise AdminError("FORBIDDEN", 403)
        if content:
            grant = self.db.scalar(
                select(PermissionGrantModel)
                .where(
                    PermissionGrantModel.subject == row.subject,
                    PermissionGrantModel.permission == "content_admin",
                )
                .with_for_update()
            )
            if grant is None or not grant.active:
                raise AdminError("CONTENT_PERMISSION_REQUIRED", 403)
        return row

    def audit(self, action: str, resource_type: str, resource_id: str, org: str = "platform"):
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=org,
                actor_ref=self.principal.subject,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                decision="allowed",
            )
        )

    def notify(self, recipient: str, kind: str, resource: str):
        self.db.add(
            InboxItemModel(
                item_id=str(uuid4()),
                recipient_ref=recipient,
                kind=kind,
                resource_ref=resource,
                is_read=False,
            )
        )

    def command(self, operation: str, key: str, payload: dict, execute: Callable[[], dict]):
        """Serialize duplicate requests and persist the response with the business transaction."""
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        pk = (self.principal.subject, operation, key)
        if self.db.get_bind().dialect.name == "postgresql":
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": json.dumps(pk)},
            )
        receipt = self.db.get(AdminCommandReceiptModel, pk)
        if receipt:
            if receipt.fingerprint != fingerprint:
                raise AdminError("IDEMPOTENCY_CONFLICT")
            return receipt.response_json
        result = execute()
        self.db.add(
            AdminCommandReceiptModel(
                actor_ref=pk[0],
                operation=operation,
                key=key,
                fingerprint=fingerprint,
                response_json=result,
            )
        )
        self.db.commit()
        return result

    def list_organizations(
        self, search: str | None, state: str | None, limit: int, cursor: str | None
    ):
        self.identity()
        query = select(OrganizationModel)
        if search:
            escaped = search.replace("%", "\\%").replace("_", "\\_")
            query = query.where(
                or_(
                    OrganizationModel.display_name.ilike("%" + escaped + "%", escape="\\"),
                    OrganizationModel.organization_id.ilike("%" + escaped + "%", escape="\\"),
                )
            )
        if state:
            states = {
                "active": ("active",),
                "paused": ("paused", "suspended"),
                "disabled": ("disabled", "inactive"),
            }[state]
            query = query.where(func.lower(OrganizationModel.state).in_(states))
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("organizations", search or "", state or "")
        page_query = apply_datetime_cursor(
            query,
            created_at_column=OrganizationModel.created_at,
            reference_column=OrganizationModel.organization_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                page_query.order_by(
                    OrganizationModel.created_at.desc(), OrganizationModel.organization_id
                ).limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.organization_id,
        )
        return {
            "items": [
                {
                    "organization_id": r.organization_id,
                    "display_name": r.display_name,
                    "state": r.state,
                    "revision": r.revision,
                }
                for r in rows[:limit]
            ],
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
        }

    def organization_summary(self):
        self.identity()
        counts = {
            str(state).lower(): count
            for state, count in self.db.execute(
                select(OrganizationModel.state, func.count()).group_by(OrganizationModel.state)
            )
        }
        active = counts.get("active", 0)
        paused = counts.get("paused", 0) + counts.get("suspended", 0)
        disabled = counts.get("disabled", 0) + counts.get("inactive", 0)
        total = sum(counts.values())
        return {
            "total": total,
            "active": active,
            "paused": paused,
            "disabled": disabled,
            "other": total - active - paused - disabled,
        }

    def create_organization(self, name: str, key: str):
        self.identity()

        def execute():
            ref = str(uuid4())
            self.db.add(OrganizationModel(organization_id=ref, display_name=name, state="active"))
            self.audit("ORGANIZATION_CREATED", "organization", ref, ref)
            return {
                "organization_id": ref,
                "display_name": name,
                "state": "active",
                "revision": 1,
            }

        return self.command("organization.create", key, {"display_name": name}, execute)

    def organization(self, ref):
        self.identity()
        row = self.db.get(OrganizationModel, ref)
        if row is None:
            raise AdminError("NOT_FOUND", 404)
        return {
            "organization_id": row.organization_id,
            "display_name": row.display_name,
            "state": row.state,
            "revision": row.revision,
            "created_at": row.created_at.isoformat(),
        }

    def update_organization(self, ref: str, payload: dict, expected_revision: int, key: str):
        self.identity()

        def execute():
            row = self.db.scalar(
                select(OrganizationModel)
                .where(OrganizationModel.organization_id == ref)
                .with_for_update()
            )
            if row is None:
                raise AdminError("NOT_FOUND", 404)
            require_revision(row.revision, expected_revision)

            changed = False
            if (
                payload.get("display_name") is not None
                and payload["display_name"] != row.display_name
            ):
                row.display_name = payload["display_name"]
                changed = True
            if payload.get("state") is not None and payload["state"] != row.state:
                row.state = payload["state"]
                changed = True
            if changed:
                row.revision += 1
                self.audit("ORGANIZATION_UPDATED", "organization", ref, ref)
            return {
                "organization_id": row.organization_id,
                "display_name": row.display_name,
                "state": row.state,
                "revision": row.revision,
            }

        command_payload = {
            "organization_id": ref,
            **payload,
            "expected_revision": expected_revision,
        }
        return self.command("organization.update:" + ref, key, command_payload, execute)

    def _audit_retention_policy(self, *, lock: bool = False):
        query = select(AuditRetentionPolicyModel).where(
            AuditRetentionPolicyModel.policy_key == "platform"
        )
        if lock:
            query = query.with_for_update()
        policy = self.db.scalar(query)
        if policy is None:
            # The migration seeds this singleton. Fail closed if schema/data is incomplete.
            raise AdminError("AUDIT_RETENTION_POLICY_UNAVAILABLE", 503)
        return policy

    def audit_retention(self):
        self.identity()
        policy = self._audit_retention_policy()
        total = self.db.scalar(select(func.count()).select_from(CoreAuditEntryModel)) or 0
        oldest = self.db.scalar(select(func.min(CoreAuditEntryModel.created_at)))
        newest = self.db.scalar(select(func.max(CoreAuditEntryModel.created_at)))
        cutoff = (
            datetime.now(UTC) - timedelta(days=policy.retention_days)
            if policy.retention_days is not None
            else None
        )
        eligible = (
            self.db.scalar(
                select(func.count())
                .select_from(CoreAuditEntryModel)
                .where(CoreAuditEntryModel.created_at < cutoff)
            )
            if cutoff is not None
            else 0
        )
        return {
            "retention_days": policy.retention_days,
            "revision": policy.revision,
            "updated_by": policy.updated_by,
            "updated_at": policy.updated_at.isoformat(),
            "total_entries": total,
            "eligible_count": eligible,
            "oldest_entry_at": oldest.isoformat() if oldest else None,
            "newest_entry_at": newest.isoformat() if newest else None,
            "last_purged_at": policy.last_purged_at.isoformat() if policy.last_purged_at else None,
            "last_purged_count": policy.last_purged_count,
        }

    def update_audit_retention(self, retention_days: int | None, expected_revision: int, key: str):
        self.identity()
        payload = {"retention_days": retention_days, "expected_revision": expected_revision}

        def execute():
            policy = self._audit_retention_policy(lock=True)
            require_revision(policy.revision, expected_revision)
            if policy.retention_days != retention_days:
                policy.retention_days = retention_days
                policy.revision += 1
                policy.updated_by = self.principal.subject
                policy.updated_at = datetime.now(UTC)
                self.audit("AUDIT_RETENTION_POLICY_CHANGED", "audit_policy", "platform")
            return {
                "retention_days": policy.retention_days,
                "revision": policy.revision,
                "updated_by": policy.updated_by,
                "updated_at": policy.updated_at.isoformat(),
            }

        return self.command("audit.retention.update", key, payload, execute)

    def audit_retention_preview(self):
        self.identity()
        policy = self._audit_retention_policy()
        cutoff = (
            datetime.now(UTC) - timedelta(days=policy.retention_days)
            if policy.retention_days is not None
            else None
        )
        query = select(func.count()).select_from(CoreAuditEntryModel)
        oldest_query = select(func.min(CoreAuditEntryModel.created_at))
        if cutoff is not None:
            query = query.where(CoreAuditEntryModel.created_at < cutoff)
            oldest_query = oldest_query.where(CoreAuditEntryModel.created_at < cutoff)
        candidate_count = self.db.scalar(query) if cutoff is not None else 0
        oldest = self.db.scalar(oldest_query) if cutoff is not None else None
        candidate_count = candidate_count or 0
        return {
            "retention_days": policy.retention_days,
            "policy_revision": policy.revision,
            "cutoff": cutoff.isoformat() if cutoff else None,
            "candidate_count": candidate_count,
            "batch_count": min(candidate_count, 500),
            "batch_limit": 500,
            "oldest_candidate_at": oldest.isoformat() if oldest else None,
        }

    def purge_audit(self, cutoff: datetime, expected_count: int, expected_revision: int, key: str):
        self.identity()
        if cutoff.tzinfo is None or cutoff.utcoffset() is None:
            raise AdminError("INVALID_RETENTION_CUTOFF", 422)
        payload = {
            "cutoff": cutoff.astimezone(UTC).isoformat(),
            "expected_count": expected_count,
            "expected_revision": expected_revision,
        }

        def execute():
            policy = self._audit_retention_policy(lock=True)
            require_revision(policy.revision, expected_revision)
            if policy.retention_days is None:
                raise AdminError("AUDIT_RETENTION_INDEFINITE", 409)
            if cutoff > datetime.now(UTC) - timedelta(days=policy.retention_days):
                raise AdminError("AUDIT_RETENTION_CUTOFF_TOO_RECENT", 409)
            ids = list(
                self.db.scalars(
                    select(CoreAuditEntryModel.audit_id)
                    .where(CoreAuditEntryModel.created_at < cutoff)
                    .order_by(CoreAuditEntryModel.created_at, CoreAuditEntryModel.audit_id)
                    .limit(500)
                    .with_for_update(skip_locked=True)
                )
            )
            if len(ids) != expected_count:
                raise AdminError("AUDIT_RETENTION_PREVIEW_STALE", 409)
            removed = self.db.execute(
                delete(CoreAuditEntryModel).where(CoreAuditEntryModel.audit_id.in_(ids))
            ).rowcount or 0
            if removed != expected_count:
                raise AdminError("AUDIT_RETENTION_PREVIEW_STALE", 409)
            now = datetime.now(UTC)
            policy.last_purged_at = now
            policy.last_purged_count = removed
            self.audit("AUDIT_RETENTION_PURGED", "audit_policy", "platform")
            return {
                "deleted_count": removed,
                "cutoff": cutoff.astimezone(UTC).isoformat(),
                "revision": policy.revision,
                "purged_at": now.isoformat(),
            }

        return self.command("audit.retention.purge", key, payload, execute)

    def permissions(self, account_id: str):
        self.identity()
        target = self.db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.account_id == account_id)
        )
        if target is None:
            raise AdminError("ACCOUNT_NOT_FOUND", 404)
        grants = self.db.scalars(
            select(PermissionGrantModel).where(PermissionGrantModel.subject == target.subject)
        )
        return {
            "account_id": account_id,
            "items": [
                {
                    "permission": g.permission,
                    "active": g.active,
                    "effective": g.active
                    and target.account_role == "platform_admin"
                    and target.state == "active",
                    "revision": g.revision,
                }
                for g in grants
            ],
        }

    def set_permission(self, account_id: str, payload: dict, key: str):
        self.identity()
        target = self.db.scalar(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.account_id == account_id)
            .with_for_update()
        )
        if target is None:
            raise AdminError("ACCOUNT_NOT_FOUND", 404)
        if target.subject == self.principal.subject:
            raise AdminError("SELF_PERMISSION_CHANGE_DENIED", 403)
        if target.account_role != "platform_admin" or target.state != "active":
            raise AdminError("ACTIVE_PLATFORM_ADMIN_REQUIRED", 422)

        def execute():
            grant = self.db.get(PermissionGrantModel, (target.subject, "content_admin"))
            require_revision(grant.revision if grant else 0, payload["expected_revision"])
            if grant is None:
                grant = PermissionGrantModel(
                    subject=target.subject, permission="content_admin", revision=0
                )
                self.db.add(grant)
            grant.active = payload["active"]
            grant.revision += 1
            grant.granted_by = self.principal.subject
            grant.updated_at = datetime.now(UTC)
            target.role_revision += 1
            self.audit(
                "CONTENT_PERMISSION_GRANTED" if grant.active else "CONTENT_PERMISSION_REVOKED",
                "adult_account",
                account_id,
            )
            self.notify(target.subject, "PERMISSION_CHANGED", account_id)
            return {
                "account_id": account_id,
                "permission": "content_admin",
                "active": grant.active,
                "revision": grant.revision,
            }

        return self.command("permission:" + account_id, key, payload, execute)

    def audit_feed(
        self, action: str | None, organization_id: str | None, limit: int, cursor: str | None
    ):
        self.identity()
        query = select(CoreAuditEntryModel)
        if action:
            query = query.where(CoreAuditEntryModel.action == action)
        if organization_id:
            query = query.where(CoreAuditEntryModel.organization_id == organization_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("audit", action or "", organization_id or "")
        page_query = apply_datetime_cursor(
            query,
            created_at_column=CoreAuditEntryModel.created_at,
            reference_column=CoreAuditEntryModel.audit_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                page_query.order_by(
                    CoreAuditEntryModel.created_at.desc(), CoreAuditEntryModel.audit_id
                ).limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.audit_id,
        )
        # Child identifiers, free text, provider payloads and signed URLs are deliberately excluded.
        return {
            "total": total,
            "items": [
                {
                    "audit_id": r.audit_id,
                    "action": r.action,
                    "decision": r.decision,
                    "resource_type": r.resource_type,
                    "created_at": r.created_at.isoformat(),
                    "organization_id": r.organization_id,
                    **(
                        {"resource_id": r.resource_id, "actor_ref": r.actor_ref}
                        if r.resource_type
                        in {"adult_account", "organization", "platform_lesson", "catalog"}
                        else {}
                    ),
                }
                for r in rows[:limit]
            ],
            "limit": limit,
            "next_cursor": next_cursor,
        }

    def inbox(self, limit: int, cursor: str | None):
        self.identity(admin=False)
        unread = self.db.scalar(
            select(func.count())
            .select_from(InboxItemModel)
            .where(
                InboxItemModel.recipient_ref == self.principal.subject,
                InboxItemModel.is_read.is_(False),
            )
        )
        scope = cursor_scope("inbox", self.principal.subject)
        query = select(InboxItemModel).where(
            InboxItemModel.recipient_ref == self.principal.subject
        )
        page_query = apply_datetime_cursor(
            query,
            created_at_column=InboxItemModel.created_at,
            reference_column=InboxItemModel.item_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                page_query.order_by(
                    InboxItemModel.created_at.desc(), InboxItemModel.item_id
                ).limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.item_id,
        )
        return {
            "unread_count": unread,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "item_id": r.item_id,
                    "kind": r.kind,
                    "is_read": r.is_read,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows[:limit]
            ],
        }

    def mark_read(self, item_id: str, key: str):
        self.identity(admin=False)

        def execute():
            row = self.db.get(InboxItemModel, item_id)
            if row is None or row.recipient_ref != self.principal.subject:
                raise AdminError("NOT_FOUND", 404)
            row.is_read = True
            return {"item_id": item_id, "is_read": True}

        return self.command("inbox.read:" + item_id, key, {}, execute)

    def preferences(self):
        self.identity(admin=False)
        row = self.db.get(AccountPreferenceModel, self.principal.subject)
        return {
            "locale": row.locale if row else "vi-VN",
            "email_notifications": row.email_notifications if row else True,
            "revision": row.revision if row else 0,
        }

    def update_preferences(self, payload: dict, key: str):
        self.identity(admin=False)

        def execute():
            row = self.db.get(AccountPreferenceModel, self.principal.subject)
            require_revision(row.revision if row else 0, payload["expected_revision"])
            if row is None:
                row = AccountPreferenceModel(subject=self.principal.subject, revision=0)
                self.db.add(row)
            row.locale, row.email_notifications = payload["locale"], payload["email_notifications"]
            row.revision += 1
            self.audit(
                "ACCOUNT_PREFERENCES_CHANGED",
                "adult_account",
                self.identity(admin=False).account_id,
            )
            return {
                "locale": row.locale,
                "email_notifications": row.email_notifications,
                "revision": row.revision,
            }

        return self.command("preferences.update", key, payload, execute)

    def request_account_email(self, account_id: str, key: str):
        self.identity()
        target = self.db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.account_id == account_id)
        )
        if target is None or target.state not in {"active", "pending_verification"}:
            raise AdminError("ACCOUNT_NOT_FOUND", 404)

        def execute():
            ref = str(uuid4())
            self.db.add(
                EmailDeliveryModel(
                    delivery_id=ref,
                    recipient_ref=target.subject,
                    template="password_setup",
                    state="pending",
                    attempts=0,
                )
            )
            self.audit("ACCOUNT_SETUP_EMAIL_REQUESTED", "adult_account", account_id)
            return {"delivery_id": ref, "state": "pending"}

        return self.command("account.email:" + account_id, key, {}, execute)

    def require_billing_scope(self, kind, ref):
        self.identity()
        if kind == "ORGANIZATION":
            row = self.db.get(OrganizationModel, ref)
            valid = row is not None and row.state == "active"
        else:
            row = self.db.scalar(
                select(AdultIdentityModel).where(AdultIdentityModel.account_id == ref)
            )
            valid = row is not None and row.state == "active" and row.account_role == "parent"
        if not valid:
            raise AdminError("OWNER_SCOPE_UNAVAILABLE", 404)
