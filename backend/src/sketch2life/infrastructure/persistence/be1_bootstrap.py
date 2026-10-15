"""Provision the first real school administrator from a verified Firebase ID token."""

from __future__ import annotations

import getpass
import sys
from uuid import uuid4

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_token_verifier import FirebaseTokenVerifier
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)


async def _provision(display_name: str, id_token: str) -> tuple[str, str]:
    settings = get_settings()
    if settings.auth_provider != "firebase" or not settings.firebase_project_id:
        raise RuntimeError("Set Firebase Authentication project configuration before provisioning")
    principal = await FirebaseTokenVerifier(settings).verify(id_token)
    engine = create_core_engine()
    factory = create_core_session_factory(engine)
    organization_id = str(uuid4())
    try:
        with factory.begin() as session:
            if session.get(AdultIdentityModel, principal.subject) is not None:
                raise RuntimeError("This Firebase adult already has an identity record")
            session.add(
                OrganizationModel(
                    organization_id=organization_id,
                    display_name=display_name,
                    state="active",
                )
            )
            session.add(
                AdultIdentityModel(
                    subject=principal.subject,
                    issuer=principal.issuer,
                    state="active",
                )
            )
            session.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=principal.subject,
                    class_id=None,
                    role="school_admin",
                    active=True,
                )
            )
        return organization_id, principal.subject
    finally:
        engine.dispose()


def main() -> int:
    if len(sys.argv) > 2:
        print(
            "Usage: python -m sketch2life.infrastructure.persistence.be1_bootstrap "
            "[organization name]"
        )
        return 2
    display_name = (
        sys.argv[1].strip() if len(sys.argv) == 2 else input("Organization name: ").strip()
    )
    if not display_name or len(display_name) > 200:
        print("Organization name must contain 1–200 characters")
        return 2
    token = getpass.getpass("Verified Firebase ID token (input hidden): ").strip()
    if not token:
        print("A verified Firebase ID token is required")
        return 2
    try:
        import asyncio

        organization_id, subject = asyncio.run(_provision(display_name, token))
    except Exception as exc:
        # Provider and database details may contain sensitive information; keep output bounded.
        print(f"Provisioning failed: {type(exc).__name__}")
        return 1
    print(
        f"Created organization {organization_id} and school_admin assignment "
        f"for verified subject {subject}."
    )
    print("The token was used for verification only and was not stored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
