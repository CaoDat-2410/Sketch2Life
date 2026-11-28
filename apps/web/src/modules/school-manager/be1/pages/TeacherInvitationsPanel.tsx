import { useRef, useState, type FormEvent } from "react";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { Alert, Button, FormField } from "../../../../shared/ui";
import {
  isValidTeacherEmail,
  teacherInvitationOutcomeMessage,
  teacherInvitationService,
  type TeacherInvitationResponse,
} from "../services/teacherInvitationService";

interface SessionInvitation {
  accountRef: string;
  maskedEmail: string;
}

interface ResultNotice {
  message: string;
  tone: "success" | "alert";
  invitation?: SessionInvitation;
}

const MAX_SESSION_INVITATIONS = 5;
const INVITATION_PENDING_MESSAGE = "Giáo viên cần đăng nhập một lần trước khi được phân công lớp.";

function maskedEmail(email: string): string {
  const atIndex = email.lastIndexOf("@");
  return `${email.slice(0, 1)}…@${email.slice(atIndex + 1)}`;
}

function shortenedAccountRef(accountRef: string): string {
  if (accountRef.length <= 12) return `${accountRef.slice(0, Math.min(4, accountRef.length))}…`;
  return `${accountRef.slice(0, 8)}…${accountRef.slice(-4)}`;
}

function successInvitation(
  response: TeacherInvitationResponse,
  email: string,
): SessionInvitation {
  return { accountRef: response.account_ref, maskedEmail: maskedEmail(email) };
}

function saveSessionInvitation(
  current: SessionInvitation[],
  invitation: SessionInvitation,
): SessionInvitation[] {
  return [invitation, ...current.filter((item) => item.accountRef !== invitation.accountRef)]
    .slice(0, MAX_SESSION_INVITATIONS);
}

export function TeacherInvitationsPanel() {
  const [email, setEmail] = useState("");
  const [emailTouched, setEmailTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<ResultNotice | null>(null);
  const [sentInvitations, setSentInvitations] = useState<SessionInvitation[]>([]);
  const busyRef = useRef(false);
  const pendingKeysRef = useRef(new Map<string, string>());

  const keyForCommand = (signature: string): string => {
    const pendingKey = pendingKeysRef.current.get(signature);
    if (pendingKey) return pendingKey;
    const key = createIdempotencyKey();
    pendingKeysRef.current.set(signature, key);
    return key;
  };

  const handleInvite = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busyRef.current) return;
    setEmailTouched(true);
    if (!isValidTeacherEmail(email)) return;

    const submittedEmail = email;
    const signature = JSON.stringify(["invite", submittedEmail]);
    busyRef.current = true;
    setBusy(true);
    setNotice(null);
    try {
      const response = await teacherInvitationService.invite(submittedEmail, keyForCommand(signature));
      pendingKeysRef.current.delete(signature);
      setEmail("");
      setEmailTouched(false);
      const invitation = successInvitation(response, submittedEmail);
      setSentInvitations((current) => saveSessionInvitation(current, invitation));
      setNotice({
        tone: "success",
        message: `Đã gửi lời mời. Trạng thái: chờ xác minh. ${INVITATION_PENDING_MESSAGE}`,
        invitation,
      });
    } catch (cause) {
      const outcome = teacherInvitationOutcomeMessage(cause);
      if (!outcome.keepIdempotencyKey) pendingKeysRef.current.delete(signature);
      setNotice({ tone: "alert", message: outcome.message });
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };

  const handleResend = async (invitation: SessionInvitation) => {
    if (busyRef.current) return;
    const signature = JSON.stringify(["resend", invitation.accountRef]);
    busyRef.current = true;
    setBusy(true);
    setNotice(null);
    try {
      const response = await teacherInvitationService.resend(invitation.accountRef, keyForCommand(signature));
      pendingKeysRef.current.delete(signature);
      const resentInvitation = { ...invitation, accountRef: response.account_ref };
      setSentInvitations((current) => saveSessionInvitation(current, resentInvitation));
      setNotice({
        tone: "success",
        message: `Đã gửi lại lời mời. Trạng thái: chờ xác minh. ${INVITATION_PENDING_MESSAGE}`,
        invitation: resentInvitation,
      });
    } catch (cause) {
      const outcome = teacherInvitationOutcomeMessage(cause);
      if (!outcome.keepIdempotencyKey) pendingKeysRef.current.delete(signature);
      setNotice({ tone: "alert", message: outcome.message });
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };

  const emailError = emailTouched && !isValidTeacherEmail(email)
    ? "Nhập email hợp lệ, từ 3 đến 254 ký tự."
    : undefined;
  const otherInvitations = sentInvitations.filter(
    (invitation) => invitation.accountRef !== notice?.invitation?.accountRef,
  );

  return (
    <section
      className="manager-business-card cozy-form-card cozy-form-card--wide"
      aria-labelledby="teacher-invitations-title"
    >
      <div className="cozy-form-stack">
        <h2 id="teacher-invitations-title" style={{ margin: 0 }}>Mời giáo viên mới</h2>
        <form className="cozy-form-stack" onSubmit={(event) => void handleInvite(event)} noValidate>
          <FormField
            label="Email giáo viên"
            htmlFor="teacher-invitation-email"
            required
            error={emailError}
            help="Lời mời đang chờ xác minh. Giáo viên cần đăng nhập một lần trước khi được phân công lớp."
          >
            <input
              id="teacher-invitation-email"
              type="email"
              inputMode="email"
              autoComplete="email"
              maxLength={254}
              pattern="^[^\s@]+@[^\s@]+\.[^\s@]+$"
              required
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                setEmailTouched(true);
              }}
              disabled={busy}
              className="w-full rounded-control border border-rule bg-paper px-3 py-2 font-ui text-sm text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            />
          </FormField>
          <div className="cozy-form-actions" style={{ justifyContent: "flex-start" }}>
            <Button type="submit" variant="primary" loading={busy} disabled={busy}>
              Gửi lời mời
            </Button>
          </div>
        </form>

        {notice && (
          <Alert role={notice.tone === "alert" ? "alert" : "status"} tone={notice.tone === "alert" ? "danger" : "success"}>
            <div className="cozy-form-stack">
              <p style={{ margin: 0 }}>{notice.message}</p>
              {notice.invitation && (
                <div className="cozy-form-actions" style={{ justifyContent: "flex-start" }}>
                  <span>Email: {notice.invitation.maskedEmail}</span>
                  <span>Mã lời mời: <code>{shortenedAccountRef(notice.invitation.accountRef)}</code></span>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => void handleResend(notice.invitation!)}
                    disabled={busy}
                  >
                    Gửi lại lời mời
                  </Button>
                </div>
              )}
            </div>
          </Alert>
        )}

        {otherInvitations.length > 0 && (
          <div className="cozy-form-stack" aria-label="Lời mời đã gửi trong phiên này">
            <h3 style={{ margin: 0 }}>Lời mời trong phiên này</h3>
            {otherInvitations.map((invitation) => (
              <div
                key={invitation.accountRef}
                className="cozy-form-actions"
                style={{ justifyContent: "flex-start" }}
              >
                <span>{invitation.maskedEmail}</span>
                <span>Mã lời mời: <code>{shortenedAccountRef(invitation.accountRef)}</code></span>
                <Button
                  type="button"
                  size="sm"
                  onClick={() => void handleResend(invitation)}
                  disabled={busy}
                >
                  Gửi lại lời mời
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
