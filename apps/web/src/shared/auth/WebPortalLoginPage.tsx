import { useState, type FormEvent } from "react";
import { ArrowRight, Eye, EyeOff, GraduationCap, LoaderCircle, School, ShieldCheck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import "./WebPortalLoginPage.css";
import { backendMessage } from "../api/backendApi";
import { Alert, FormField } from "../ui";
import sketch2lifeLogo from "../assets/sketch2life-logo-mark-256.png";

export type WebPortalAppRole = "TEACHER" | "MANAGER" | "ADMIN";

type PortalDetails = {
  label: string;
  code: string;
  heading: string;
  description: string;
  icon: typeof GraduationCap;
};

type LoginFieldState = {
  role: WebPortalAppRole;
  password: string;
  showPassword: boolean;
  error: string | null;
  errorFields: { email?: boolean; password?: boolean };
};

const PORTALS: Record<WebPortalAppRole, PortalDetails> = {
  TEACHER: {
    label: "Giáo viên",
    code: "CỔNG GIÁO VIÊN",
    heading: "Chuẩn bị buổi học",
    description: "Mở các lớp được phân công, giáo án và tài liệu của bạn.",
    icon: GraduationCap,
  },
  MANAGER: {
    label: "Quản lý trường",
    code: "CỔNG NHÀ TRƯỜNG",
    heading: "Quản lý hoạt động trường",
    description: "Quản lý lớp học, giáo viên và học liệu của trường.",
    icon: School,
  },
  ADMIN: {
    label: "Quản trị nền tảng",
    code: "CỔNG NỀN TẢNG",
    heading: "Vận hành nền tảng",
    description: "Quản lý tài khoản và hoạt động nền tảng.",
    icon: ShieldCheck,
  },
};

const ROLE_ORDER: WebPortalAppRole[] = ["TEACHER", "MANAGER", "ADMIN"];

export function WebPortalLoginPage({
  portalRole,
  onRoleChange,
  onAuthenticate,
  onResetPassword,
}: {
  portalRole: WebPortalAppRole;
  onRoleChange: (role: WebPortalAppRole) => void;
  onAuthenticate: (role: WebPortalAppRole, email: string, password: string) => Promise<void>;
  onResetPassword: (email: string) => Promise<void>;
}) {
  const location = useLocation();
  const portal = PORTALS[portalRole];
  const Icon = portal.icon;
  const roleQuery = portalRole === "TEACHER" ? "teacher" : portalRole === "MANAGER" ? "manager" : "admin";
  const [email, setEmail] = useState("");
  const [formState, setFormState] = useState<LoginFieldState>({
    role: portalRole,
    password: "",
    showPassword: false,
    error: null,
    errorFields: {},
  });
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState("");
  const [recovering, setRecovering] = useState(false);
  const fields = formState.role === portalRole
    ? formState
    : { role: portalRole, password: "", showPassword: false, error: null, errorFields: {} };

  const updateFields = (updates: Partial<Omit<LoginFieldState, "role">>) => {
    setFormState((current) => ({
      ...(current.role === portalRole
        ? current
        : { role: portalRole, password: "", showPassword: false, error: null, errorFields: {} }),
      ...updates,
    }));
  };

  const changeRole = (role: WebPortalAppRole) => {
    setFormState({ role, password: "", showPassword: false, error: null, errorFields: {} });
    onRoleChange(role);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (pending) return;
    setNotice("");
    updateFields({ error: null, errorFields: {} });
    setPending(true);
    try {
      await onAuthenticate(portalRole, email.trim(), fields.password);
    } catch (cause) {
      const code = (cause as { code?: string }).code;
      const errorFields = !email.trim() || code === "auth/invalid-email" || code === "auth/user-not-found"
        ? { email: true }
        : !fields.password || code === "auth/wrong-password"
          ? { password: true }
          : {};
      updateFields({ error: backendMessage(cause), errorFields });
    } finally {
      setPending(false);
    }
  };

  const resetPassword = async () => {
    if (pending) return;
    updateFields({ error: null, errorFields: {} });
    setNotice("");
    if (!email.trim()) {
      updateFields({ error: "Nhập email để nhận hướng dẫn đặt lại mật khẩu.", errorFields: { email: true } });
      return;
    }

    setPending(true);
    try {
      await onResetPassword(email.trim());
    } catch (cause) {
      const code = (cause as { code?: string }).code;
      if (code !== "auth/user-not-found") {
        updateFields({
          error: code === "auth/too-many-requests" || code === "RATE_LIMITED"
            ? "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau."
            : "Chưa thể gửi hướng dẫn. Kiểm tra kết nối và thử lại.",
          errorFields: code === "auth/invalid-email" ? { email: true } : {},
        });
        return;
      }
    } finally {
      setPending(false);
    }
    setNotice("Nếu email đã được đăng ký, bạn sẽ nhận được liên kết đặt lại mật khẩu. Kiểm tra cả thư mục spam.");
  };
  return (
    <main className="s2l-login-shell">
      <div className="s2l-login-card">
        <section className="s2l-login-intro">
          <div className="s2l-login-message">
            <p className="s2l-login-eyebrow">{portal.code}</p>
            <h1>{portal.heading}</h1>
            <p>{portal.description}</p>
          </div>
          <img className="s2l-login-illustration" src="/images/sketch2life-login-learning.png" alt="" aria-hidden="true" />
        </section>

        <section className="s2l-login-form-panel" aria-labelledby="s2l-login-title">
          <Link className="s2l-login-brand" to={`/login?role=${roleQuery}`} state={location.state} aria-label="Sketch2Life, đăng nhập">
            <img src={sketch2lifeLogo} alt="" aria-hidden="true" />
            <span className="s2l-login-brand-copy">
              <span className="s2l-login-brand-name">Sketch2Life</span>
              <span className="s2l-login-brand-context">Không gian làm việc giáo dục</span>
            </span>
          </Link>
          <div className="s2l-login-role"><Icon size={19} aria-hidden="true" /><span>{portal.label}</span></div>
          <h2 id="s2l-login-title">{recovering ? "Quên mật khẩu?" : "Đăng nhập"}</h2>
          <p>{recovering ? "Nhập email tài khoản để nhận liên kết đặt lại mật khẩu." : "Chào mừng bạn trở lại Sketch2Life."}</p>

          {!recovering && <div className="s2l-login-role-switch" role="group" aria-label="Chọn vai trò đăng nhập">
            {ROLE_ORDER.map((role) => {
              const target = PORTALS[role];
              const RoleIcon = target.icon;
              const current = role === portalRole;
              return (
                <button
                  key={role}
                  type="button"
                  className={"s2l-login-role-link" + (current ? " is-current" : "")}
                  aria-pressed={current}
                  disabled={pending}
                  onClick={() => changeRole(role)}
                >
                  <RoleIcon size={16} aria-hidden="true" /><span>{target.label}</span>
                </button>
              );
            })}
          </div>}

          <form className="s2l-login-form" onSubmit={(event) => { if (recovering) { event.preventDefault(); void resetPassword(); } else { void submit(event); } }} aria-busy={pending}>
            <FormField label="Email tài khoản" htmlFor="s2l-login-email" required className="s2l-login-field">
              <input
                id="s2l-login-email"
                type="email"
                autoComplete="username"
                inputMode="email"
                required
                value={email}
                onChange={(event) => { setEmail(event.target.value); setNotice(""); updateFields({ error: null, errorFields: {} }); }}
                aria-invalid={fields.errorFields.email || undefined}
                aria-describedby={fields.error ? "s2l-login-error" : undefined}
              />
            </FormField>
            {!recovering && (
              <FormField label="Mật khẩu" htmlFor="s2l-login-password" required className="s2l-login-field">
                <span className="s2l-password-input">
                  <input
                    id="s2l-login-password"
                    type={fields.showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={fields.password}
                    onChange={(event) => updateFields({ password: event.target.value, errorFields: {} })}
                    aria-invalid={fields.errorFields.password || undefined}
                    aria-describedby={fields.error ? "s2l-login-error" : undefined}
                  />
                  <button type="button" className="s2l-password-toggle" aria-label={fields.showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-pressed={fields.showPassword} onClick={() => updateFields({ showPassword: !fields.showPassword })}><span aria-hidden="true">{fields.showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</span></button>
                </span>
              </FormField>
            )}
            {fields.error && <div id="s2l-login-error" className="s2l-alert" role="alert">{fields.error}</div>}
            {notice && <Alert tone="success" role="status" className="s2l-reset-notice">{notice}</Alert>}
            <button className="s2l-login-submit" type="submit" disabled={pending || (recovering && Boolean(notice))}>
              <span>{pending ? "Đang xử lý…" : recovering ? "Gửi liên kết đặt lại" : "Đăng nhập"}</span>
              <span className="s2l-login-submit-icon">{pending ? <LoaderCircle size={17} aria-hidden="true" /> : <ArrowRight size={16} aria-hidden="true" />}</span>
            </button>
          </form>
          <div className="s2l-login-recovery">
            <button type="button" onClick={() => { setRecovering(!recovering); setNotice(""); updateFields({ error: null, errorFields: {}, password: "" }); }} disabled={pending}>
              {recovering ? "← Quay lại đăng nhập" : "Quên mật khẩu?"}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
