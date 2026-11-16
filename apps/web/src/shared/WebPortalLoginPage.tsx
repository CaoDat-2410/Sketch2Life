import { useState, type FormEvent } from "react";
import { ArrowRight, Eye, EyeOff, GraduationCap, LockKeyhole, School, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { BrandWordmark } from "./BrandMark";
import { backendMessage } from "./backendApi";

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
    description: "Xem lớp học và yêu cầu duyệt học liệu trong phạm vi tổ chức.",
    icon: School,
  },
  ADMIN: {
    label: "Quản trị nền tảng",
    code: "CỔNG NỀN TẢNG",
    heading: "Vận hành nền tảng",
    description: "Truy cập chức năng theo capability được backend xác nhận.",
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
  const portal = PORTALS[portalRole];
  const Icon = portal.icon;
  const [email, setEmail] = useState("");
  const [formState, setFormState] = useState<LoginFieldState>({
    role: portalRole,
    password: "",
    showPassword: false,
    error: null,
  });
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState("");
  const fields = formState.role === portalRole
    ? formState
    : { role: portalRole, password: "", showPassword: false, error: null };

  const updateFields = (updates: Partial<Omit<LoginFieldState, "role">>) => {
    setFormState((current) => ({
      ...(current.role === portalRole
        ? current
        : { role: portalRole, password: "", showPassword: false, error: null }),
      ...updates,
    }));
  };

  const changeRole = (role: WebPortalAppRole) => {
    setFormState({ role, password: "", showPassword: false, error: null });
    onRoleChange(role);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (pending) return;
    setNotice("");
    updateFields({ error: null });
    setPending(true);
    try {
      await onAuthenticate(portalRole, email.trim(), fields.password);
    } catch (cause) {
      updateFields({ error: backendMessage(cause) });
    } finally {
      setPending(false);
    }
  };

  const resetPassword = async () => {
    if (pending) return;
    updateFields({ error: null });
    setNotice("");
    if (!email.trim()) {
      updateFields({ error: "Nhập email để nhận hướng dẫn đặt lại mật khẩu." });
      return;
    }

    setPending(true);
    try {
      await onResetPassword(email.trim());
    } catch {
      // Keep the response neutral so login recovery does not reveal account existence.
    } finally {
      setNotice("Nếu email thuộc tài khoản đã đăng ký, hướng dẫn đặt lại mật khẩu sẽ được gửi.");
      setPending(false);
    }
  };

  return (
    <main className="s2l-login-shell">
      <div className="s2l-login-card">
        <section className="s2l-login-intro">
          <Link className="s2l-login-brand" to="/login" aria-label="Sketch2Life — đăng nhập">
            <BrandWordmark size={30} />
            <span><strong>Sketch2Life</strong><span>Cổng làm việc theo vai trò</span></span>
          </Link>
          <div className="s2l-login-message">
            <p className="s2l-login-eyebrow">{portal.code}</p>
            <h1>{portal.heading}</h1>
            <p>{portal.description}</p>
          </div>
          <div className="s2l-login-note">
            <LockKeyhole size={16} aria-hidden="true" />
            <span>
              {portalRole === "MANAGER"
                ? "Quyền school_admin được kiểm tra qua phân công BE1 sau khi đăng nhập."
                : "Quyền truy cập và phạm vi dữ liệu được xác minh theo tài khoản."}
            </span>
          </div>
        </section>

        <section className="s2l-login-form-panel" aria-labelledby="s2l-login-title">
          <div className="s2l-login-role"><Icon size={19} aria-hidden="true" /><span>{portal.label}</span></div>
          <h2 id="s2l-login-title">Đăng nhập</h2>
          <p>Dùng tài khoản được cấp cho cổng {portal.label.toLowerCase()}.</p>

          <div className="s2l-login-role-switch" role="group" aria-label="Chọn vai trò đăng nhập">
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
          </div>

          <form className="s2l-login-form" onSubmit={(event) => void submit(event)} aria-busy={pending}>
            <label className="s2l-login-field" htmlFor="s2l-login-email">Email tài khoản
              <input id="s2l-login-email" type="email" autoComplete="username" inputMode="email" required value={email} onChange={(event) => setEmail(event.target.value)} aria-describedby={fields.error ? "s2l-login-error" : undefined} />
            </label>
            <label className="s2l-login-field" htmlFor="s2l-login-password">Mật khẩu
              <span className="s2l-password-input">
                <input id="s2l-login-password" type={fields.showPassword ? "text" : "password"} autoComplete="current-password" required value={fields.password} onChange={(event) => updateFields({ password: event.target.value })} aria-describedby={fields.error ? "s2l-login-error" : undefined} />
                <button type="button" className="s2l-password-toggle" aria-label={fields.showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-pressed={fields.showPassword} onClick={() => updateFields({ showPassword: !fields.showPassword })}><span aria-hidden="true">{fields.showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</span></button>
              </span>
            </label>
            {fields.error && <div id="s2l-login-error" className="s2l-alert" role="alert">{fields.error}</div>}
            <button className="s2l-login-submit" type="submit" disabled={pending}>
              {pending ? "Đang xác minh…" : "Đăng nhập"}
              <ArrowRight size={17} aria-hidden="true" />
            </button>
          </form>
          <div className="s2l-login-recovery">
            <button type="button" onClick={() => void resetPassword()} disabled={pending}>
              {pending ? "Đang xử lý…" : "Quên mật khẩu?"}
            </button>
            {notice && <p role="status" aria-live="polite">{notice}</p>}
          </div>
          <p className="s2l-login-footer">
            {portalRole === "MANAGER"
              ? "School Manager không xem story hoặc media của trẻ theo mặc định."
              : "Phiên chỉ mở sau khi xác thực thành công và vai trò được xác minh."}
          </p>
        </section>
      </div>
    </main>
  );
}
