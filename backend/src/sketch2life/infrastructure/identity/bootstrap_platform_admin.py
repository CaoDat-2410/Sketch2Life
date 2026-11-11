"""One-time operator bootstrap for the first Platform Admin account."""

from __future__ import annotations

import sys
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_admin_account_provisioner import (
    FirebaseAdminAccountProvisioner,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)


def provision_platform_admin() -> str:
    settings = get_settings()
    email = settings.platform_admin_bootstrap_email.strip().lower()
    if not email:
        raise RuntimeError("Set SKETCH2LIFE_PLATFORM_ADMIN_BOOTSTRAP_EMAIL in the root .env")
    if settings.auth_provider != "firebase" or not settings.firebase_project_id:
        raise RuntimeError("Configure Firebase Authentication before bootstrapping Platform Admin")

    engine = create_core_engine()
    factory = create_core_session_factory(engine)
    provisioner = FirebaseAdminAccountProvisioner(settings)
    try:
        existing_provider_account = provisioner.find_account_by_email(email)
        with factory() as db:
            if existing_provider_account is not None:
                existing = db.get(AdultIdentityModel, existing_provider_account.subject)
                if (
                    existing is not None
                    and existing.account_role == "platform_admin"
                    and existing.state == "active"
                    and existing.issuer == existing_provider_account.issuer
                ):
                    return existing.account_id
                raise RuntimeError(
                    "The bootstrap Firebase identity is not an active Platform Admin"
                )
            active_admin = db.scalar(
                select(AdultIdentityModel.subject)
                .where(
                    AdultIdentityModel.account_role == "platform_admin",
                    AdultIdentityModel.state == "active",
                )
                .limit(1)
            )
            if active_admin is not None:
                raise RuntimeError("A Platform Admin already exists; create further admins in Admin Web")

        provisioned = provisioner.create_account(email=email, display_name="Quản trị nền tảng")
        account_id = str(uuid4())
        try:
            with factory.begin() as db:
                active_admin = db.scalar(
                    select(AdultIdentityModel.subject)
                    .where(
                        AdultIdentityModel.account_role == "platform_admin",
                        AdultIdentityModel.state == "active",
                    )
                    .limit(1)
                )
                if active_admin is not None:
                    raise RuntimeError("A Platform Admin was created concurrently")
                identity = AdultIdentityModel(
                    account_id=account_id,
                    subject=provisioned.subject,
                    issuer=provisioned.issuer,
                    state="active",
                    account_role="platform_admin",
                    role_revision=1,
                )
                db.add(identity)
                db.add(
                    CoreAuditEntryModel(
                        audit_id=str(uuid4()),
                        organization_id="platform",
                        actor_ref=None,
                        action="PLATFORM_ADMIN_BOOTSTRAPPED",
                        resource_type="adult_account",
                        resource_id=account_id,
                        decision="allowed",
                    )
                )
        except (IntegrityError, SQLAlchemyError, RuntimeError):
            try:
                provisioner.delete_account(provisioned.subject)
            except Exception:
                pass
            raise
        return account_id
    finally:
        engine.dispose()


def main() -> int:
    try:
        account_id = provision_platform_admin()
    except Exception as exc:
        print(f"Platform Admin bootstrap failed: {type(exc).__name__}")
        return 1
    print(f"Platform Admin is ready (account reference: {account_id}).")
    print("Use Firebase password recovery to set the account password.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
