"""Firebase Admin account provisioning adapter."""

from __future__ import annotations

from sketch2life.application.ports.identity import (
    IdentityAccountProfile,
    IdentityAccountConflict,
    IdentityAccountProvisioningUnavailable,
    ProvisionedIdentity,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.identity.firebase_admin_app import (
    FirebaseAdminUnavailable,
    get_firebase_admin_app,
)


class FirebaseAdminAccountProvisioner:
    """Create and manage Firebase identities without embedding application roles."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        return self._create_user(email=email, password=password, email_verified=False)

    def create_account(
        self, *, email: str, display_name: str | None = None
    ) -> ProvisionedIdentity:
        return self._create_user(email=email, display_name=display_name, email_verified=False)

    def _create_user(
        self,
        *,
        email: str,
        email_verified: bool,
        password: str | None = None,
        display_name: str | None = None,
    ) -> ProvisionedIdentity:
        try:
            from firebase_admin import auth

            app = get_firebase_admin_app(self._settings)
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=email_verified,
                disabled=False,
                app=app,
            )
            return ProvisionedIdentity(
                subject=user.uid,
                issuer=f"https://securetoken.google.com/{self._settings.firebase_project_id}",
            )
        except FirebaseAdminUnavailable:
            raise IdentityAccountProvisioningUnavailable from None
        except ImportError:
            raise IdentityAccountProvisioningUnavailable from None
        except Exception as exc:
            try:
                from firebase_admin import auth

                if isinstance(exc, auth.EmailAlreadyExistsError):
                    raise IdentityAccountConflict from None
            except ImportError:
                pass
            raise IdentityAccountProvisioningUnavailable from None

    def delete_account(self, subject: str) -> None:
        try:
            from firebase_admin import auth

            auth.delete_user(subject, app=get_firebase_admin_app(self._settings))
        except FirebaseAdminUnavailable:
            raise IdentityAccountProvisioningUnavailable from None
        except ImportError:
            raise IdentityAccountProvisioningUnavailable from None
        except Exception as exc:
            try:
                from firebase_admin import auth

                if isinstance(exc, auth.UserNotFoundError):
                    return
            except ImportError:
                pass
            raise IdentityAccountProvisioningUnavailable from None

    def set_account_disabled(self, subject: str, disabled: bool) -> None:
        try:
            from firebase_admin import auth

            app = get_firebase_admin_app(self._settings)
            auth.update_user(subject, disabled=disabled, app=app)
            if disabled:
                try:
                    auth.revoke_refresh_tokens(subject, app=app)
                except Exception:
                    # Keep provider state aligned with the still-active database row if token
                    # revocation cannot be completed.
                    try:
                        auth.update_user(subject, disabled=False, app=app)
                    except Exception:
                        pass
                    raise
        except FirebaseAdminUnavailable:
            raise IdentityAccountProvisioningUnavailable from None
        except ImportError:
            raise IdentityAccountProvisioningUnavailable from None
        except Exception:
            raise IdentityAccountProvisioningUnavailable from None

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        if len(subjects) > 100:
            raise IdentityAccountProvisioningUnavailable
        if not subjects:
            return {}
        try:
            from firebase_admin import auth

            result = auth.get_users(
                [auth.UidIdentifier(subject) for subject in subjects],
                app=get_firebase_admin_app(self._settings),
            )
            return {
                user.uid: IdentityAccountProfile(
                    subject=user.uid,
                    email=user.email,
                    display_name=user.display_name,
                )
                for user in result.users
            }
        except FirebaseAdminUnavailable:
            raise IdentityAccountProvisioningUnavailable from None
        except ImportError:
            raise IdentityAccountProvisioningUnavailable from None
        except Exception:
            raise IdentityAccountProvisioningUnavailable from None

    def find_account_by_email(self, email: str) -> ProvisionedIdentity | None:
        try:
            from firebase_admin import auth

            user = auth.get_user_by_email(email, app=get_firebase_admin_app(self._settings))
            return ProvisionedIdentity(
                subject=user.uid,
                issuer=f"https://securetoken.google.com/{self._settings.firebase_project_id}",
            )
        except FirebaseAdminUnavailable:
            raise IdentityAccountProvisioningUnavailable from None
        except ImportError:
            raise IdentityAccountProvisioningUnavailable from None
        except Exception as exc:
            try:
                from firebase_admin import auth

                if isinstance(exc, auth.UserNotFoundError):
                    return None
            except ImportError:
                pass
            raise IdentityAccountProvisioningUnavailable from None


__all__ = ["FirebaseAdminAccountProvisioner"]
