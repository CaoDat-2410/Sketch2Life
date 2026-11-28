"""One bounded email-outbox delivery pass. Never log or persist Firebase action links."""

import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.database import create_core_engine
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel

# Mail clients need tables and inline styles; no remote images or web fonts are loaded.
_INK, _VIOLET, _MUTED = "#2a1458", "#6d28d9", "#6f6787"
_CRAYONS = ("#6d28d9", "#ff7a59", "#ffc83d", "#4fb3ee")
_DISPLAY = "'Trebuchet MS','Segoe UI',Arial,sans-serif"
_BODY = "'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


def _step(
    number: str, colour: str, title: str, hint: str, label: str, url: str, *, primary: bool
) -> str:
    href = escape(url, quote=True)
    face = (
        f"background:{_VIOLET};color:#ffffff;border:2px solid {_VIOLET}"
        if primary
        else f"background:#ffffff;color:{_VIOLET};border:2px solid {_VIOLET}"
    )
    badge = (
        f'<td width="48" valign="top" style="width:48px">'
        f'<div style="width:34px;height:34px;line-height:34px;border-radius:17px;'
        f'background:{colour};color:{_INK};text-align:center;font:700 16px/34px {_DISPLAY}">'
        f"{number}</div></td>"
        if number
        else ""
    )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="margin:0 0 22px"><tr>{badge}<td valign="top">'
        f'<div style="font:700 17px {_DISPLAY};color:{_INK}">{escape(title)}</div>'
        f'<div style="margin:3px 0 12px;font:400 14px/1.55 {_BODY};color:{_MUTED}">'
        f"{escape(hint)}</div>"
        f'<a href="{href}" style="display:inline-block;{face};text-decoration:none;'
        f'font:700 15px {_BODY};padding:11px 26px;border-radius:999px">{escape(label)}</a>'
        "</td></tr></table>"
    )


def _action_html(
    recipient: str,
    title: str,
    intro: str,
    action: str,
    outro: str,
    link: str,
    verification: str | None,
) -> str:
    stripe = "".join(
        f'<td height="10" style="height:10px;background:{colour};font-size:0">&nbsp;</td>'
        for colour in _CRAYONS
    )
    if verification:
        steps = _step(
            "1", "#ffc83d", action, "Chọn một mật khẩu chỉ bạn biết.", action, link, primary=True
        )
        steps += _step(
            "2",
            "#ffb3a1",
            "Xác minh email",
            "Xác nhận đây là hộp thư của bạn để kích hoạt tài khoản.",
            "Xác minh email",
            verification,
            primary=False,
        )
    else:
        steps = _step(
            "", _CRAYONS[0], action, "Chọn một mật khẩu chỉ bạn biết.", action, link, primary=True
        )
    fallback = "".join(
        f'<div style="margin:6px 0 0;word-break:break-all"><a href="{escape(url, quote=True)}" '
        f'style="color:{_MUTED}">{escape(url)}</a></div>'
        for url in (link, verification)
        if url
    )
    return (
        '<!doctype html><html lang="vi"><body style="margin:0;padding:0;background:#f1ecfb">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#f1ecfb"><tr><td align="center" style="padding:28px 14px">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0" '
        'style="width:100%;max-width:560px;background:#fffdf7;border-radius:22px;'
        'overflow:hidden">'
        f'<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f"<tr>{stripe}</tr></table></td></tr>"
        '<tr><td style="padding:30px 34px 8px">'
        f'<div style="font:700 20px {_DISPLAY};color:{_VIOLET}">Sketch2Life</div>'
        f'<h1 style="margin:18px 0 8px;font:700 28px/1.25 {_DISPLAY};color:{_INK}">'
        f"{escape(title)}</h1>"
        f'<p style="margin:0 0 14px;font:400 15px/1.6 {_BODY};color:{_INK}">{escape(intro)}</p>'
        f'<p style="margin:0 0 26px"><span style="display:inline-block;background:#efe8fd;'
        f'border-radius:999px;padding:6px 14px;font:600 13px {_BODY};color:{_INK}">'
        f"{escape(recipient)}</span></p>"
        f"{steps}"
        "</td></tr>"
        '<tr><td style="padding:18px 34px 28px;border-top:2px dashed #ded5f4;'
        f'font:400 12px/1.6 {_BODY};color:{_MUTED}">'
        f"<div>{escape(outro)}</div>"
        '<div style="margin-top:12px">Nút không bấm được? Chép liên kết vào trình duyệt:</div>'
        f'<div style="font-size:11px">{fallback}</div>'
        "</td></tr></table></td></tr></table></body></html>"
    )


def build_action_message(
    sender: str, recipient: str, *, recovery: bool, link: str, verification: str | None
) -> EmailMessage:
    """Password setup or recovery mail: a plain text body plus an HTML body with buttons."""
    subject = "Đặt lại mật khẩu Sketch2Life" if recovery else "Thiết lập mật khẩu Sketch2Life"
    title = "Đặt lại mật khẩu của bạn" if recovery else "Tài khoản của bạn đã sẵn sàng"
    action = "Đặt lại mật khẩu" if recovery else "Đặt mật khẩu"
    intro = (
        "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản này."
        if recovery
        else "Một tài khoản Sketch2Life vừa được tạo cho bạn. Làm theo bên dưới để bắt đầu."
    )
    outro = "Nếu bạn không yêu cầu, hãy bỏ qua email này. Không chuyển tiếp email cho người khác."

    lines = [subject, "", intro, "", f"{action}:", link]
    if verification:
        lines += ["", "Sau đó xác minh email để kích hoạt tài khoản:", verification]
    text = "\n".join([*lines, "", outro, ""])

    message = EmailMessage()
    message["Subject"] = subject
    message["From"], message["To"] = sender, recipient
    message.set_content(text)
    message.add_alternative(
        _action_html(recipient, title, intro, action, outro, link, verification), subtype="html"
    )
    return message


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
            send(
                build_action_message(
                    settings.smtp_from,
                    user.email,
                    recovery=row.template == "password_recovery",
                    link=link,
                    verification=verification,
                )
            )
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
