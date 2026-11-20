"""One bounded email-outbox delivery pass. Never log or persist Firebase action links."""

import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.database import create_core_engine
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel


def deliver_pending(db: Session, settings, identity_provider, send, limit: int = 25) -> dict:
    sent = failed = 0
    for _ in range(limit):
        row = db.scalar(
            select(EmailDeliveryModel)
            .where(EmailDeliveryModel.state == "pending")
            .order_by(EmailDeliveryModel.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if row is None:
            break
        row.attempts += 1
        row.updated_at = datetime.now(UTC)
        account = db.get(AdultIdentityModel, row.recipient_ref)
        try:
            if account is None or account.state not in {"active", "pending_verification"}:
                raise ValueError("Recipient unavailable")
            user = identity_provider.get_user(row.recipient_ref)
            if user.disabled or not user.email:
                raise ValueError("Recipient unavailable")
            link = identity_provider.password_link(user.email)
            verification = (
                identity_provider.verification_link(user.email)
                if account.email_verification_required
                else None
            )
            message = EmailMessage()
            message["Subject"] = (
                "Đặt lại mật khẩu Sketch2Life"
                if row.template == "password_recovery"
                else "Thiết lập mật khẩu Sketch2Life"
            )
            message["From"], message["To"] = settings.smtp_from, user.email
            message.set_content(
                "Bạn đã yêu cầu thiết lập hoặc đặt lại mật khẩu Sketch2Life.\n\n"
                "Mở liên kết sau để tiếp tục:\n"
                + link
                + (
                    ("\n\nXác minh email để kích hoạt tài khoản:\n" + verification)
                    if verification
                    else ""
                )
                + "\n\nNếu bạn không yêu cầu, hãy bỏ qua email này.\n"
            )
            send(message)
            row.state, row.failure_code = "sent", None
            sent += 1
        except Exception:
            # Delivery can be ambiguous; a failed row requires an explicit new request.
            row.state, row.failure_code = "failed", "EMAIL_DELIVERY_UNAVAILABLE"
            failed += 1
        db.commit()
    return {"sent": sent, "failed": failed}


class FirebaseActionLinks:
    def __init__(self, settings):
        self.app = get_firebase_admin_app(settings)

    def get_user(self, subject):
        from firebase_admin import auth

        return auth.get_user(subject, app=self.app)

    def password_link(self, email):
        from firebase_admin import auth

        return auth.generate_password_reset_link(email, app=self.app)

    def verification_link(self, email):
        from firebase_admin import auth

        return auth.generate_email_verification_link(email, app=self.app)


def main():
    settings = get_settings()
    if not settings.smtp_host:
        raise RuntimeError("SMTP is not configured")
    if settings.env == "production" and not settings.smtp_starttls:
        raise RuntimeError("Production email requires encrypted SMTP")

    def send(message):
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(
                    settings.smtp_username,
                    settings.smtp_password.get_secret_value() if settings.smtp_password else "",
                )
            smtp.send_message(message)

    engine = create_core_engine()
    try:
        with Session(engine) as db:
            result = deliver_pending(db, settings, FirebaseActionLinks(settings), send)
            if result["sent"] or result["failed"]:
                print(result, flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    import sys
    import time

    if "--loop" in sys.argv:
        while True:
            try:
                main()
            except Exception:
                print("Email worker unavailable; retrying on the next pass", flush=True)
            time.sleep(5)
    else:
        main()
