import React, { lazy, Suspense, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BrandWordmark } from "./BrandMark";
import {
  backendMessage,
  isLocalPreview,
  signInAndResolveRole,
  type PortalRole,
} from "./backendApi";
import "./portal-login.css";

const PortalLoginScene = lazy(() => import("./PortalLoginScene"));

export type WebPortalAppRole = "TEACHER" | "MANAGER" | "ADMIN";

type PortalDetails = {
  apiRole: PortalRole;
  label: string;
  englishLabel: string;
  code: string;
  headline: string;
  headlineAccent: string;
  description: string;
  home: string;
};

type PortalUrlEnvironment = {
  DEV: boolean;
  VITE_S2L_TEACHER_LOGIN_URL?: string;
  VITE_S2L_SCHOOL_MANAGER_LOGIN_URL?: string;
  VITE_S2L_PLATFORM_ADMIN_LOGIN_URL?: string;
};

const portalEnvironment = (import.meta as unknown as { env: PortalUrlEnvironment }).env;

const PORTALS: Record<WebPortalAppRole, PortalDetails> = {
  TEACHER: {
    apiRole: "teacher",
    label: "Giáo viên",
    englishLabel: "Teacher",
    code: "01 / TEACHER PORTAL",
    headline: "Dạy học",
    headlineAccent: "mở lối mới.",
    description: "Lớp được phân công và giáo án trong tổ chức của bạn.",
    home: "/t01-lesson-workspace",
  },
  MANAGER: {
    apiRole: "school_manager",
    label: "Quản lý trường",
    englishLabel: "School Manager",
    code: "02 / SCHOOL MANAGER",
    headline: "Điều phối",
    headlineAccent: "để sáng tạo.",
    description: "Lớp học và yêu cầu giáo án công khai trong tổ chức.",
    home: "/m02-organization-management",
  },
  ADMIN: {
    apiRole: "platform_admin",
    label: "Quản trị nền tảng",
    englishLabel: "Platform Admin",
    code: "03 / PLATFORM ADMIN",
    headline: "Vận hành",
    headlineAccent: "đáng tin cậy.",
    description: "Cổng nền tảng chỉ mở sau khi backend xác nhận quyền quản trị.",
    home: "/a02-platform-operations",
  },
};

const PORTAL_ORDER: WebPortalAppRole[] = ["TEACHER", "MANAGER", "ADMIN"];

const LOCAL_PORTAL_URLS: Record<WebPortalAppRole, string> = {
  TEACHER: "http://127.0.0.1:5172/login",
  MANAGER: "http://127.0.0.1:5173/login",
  ADMIN: "http://127.0.0.1:5174/login",
};

const PRODUCTION_PORTAL_URLS: Record<WebPortalAppRole, string | undefined> = {
  TEACHER: portalEnvironment.VITE_S2L_TEACHER_LOGIN_URL,
  MANAGER: portalEnvironment.VITE_S2L_SCHOOL_MANAGER_LOGIN_URL,
  ADMIN: portalEnvironment.VITE_S2L_PLATFORM_ADMIN_LOGIN_URL,
};

function portalLoginUrl(role: WebPortalAppRole, currentRole: WebPortalAppRole): string | null {
  if (role === currentRole) return new URL("/login", window.location.origin).toString();
  if (portalEnvironment.DEV) return LOCAL_PORTAL_URLS[role];

  const configuredUrl = PRODUCTION_PORTAL_URLS[role]?.trim();
  if (!configuredUrl) return null;

  try {
    const url = new URL(configuredUrl);
    if (url.protocol !== "https:" || url.pathname !== "/login") return null;
    return url.toString();
  } catch {
    return null;
  }
}

function PortalMark({ role }: { role: WebPortalAppRole }) {
  const paths: Record<WebPortalAppRole, React.ReactNode> = {
    TEACHER: <><path d="m5 16.5 8.8-8.8 3.5 3.5-8.8 8.8-4.3.8.8-4.3Z" /><path d="m12.5 9 3.5 3.5M4 22h16" /></>,
    MANAGER: <><path d="m3.5 10 8.5-6 8.5 6" /><path d="M5.5 9.5v10h13v-10M9 19.5v-5h6v5" /></>,
    ADMIN: <><path d="M12 3.5 20 7v5.5c0 4.2-3.2 7.2-8 9-4.8-1.8-8-4.8-8-9V7l8-3.5Z" /><path d="m8.5 12 2.3 2.3 4.8-5" /></>,
  };

  return (
    <svg
      viewBox="0 0 24 24"
      width="22"
      height="22"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[role]}
    </svg>
  );
}

function PortalArtFallback() {
  return (
    <div className="s2l-auth-art-fallback" aria-hidden="true">
      <span className="s2l-auth-art-orbit s2l-auth-art-orbit--one" />
      <span className="s2l-auth-art-orbit s2l-auth-art-orbit--two" />
      <span className="s2l-auth-book s2l-auth-book--back" />
      <span className="s2l-auth-book s2l-auth-book--middle" />
      <span className="s2l-auth-book s2l-auth-book--front" />
      <span className="s2l-auth-school">
        <span className="s2l-auth-school-roof" />
        <span className="s2l-auth-school-body" />
      </span>
      <span className="s2l-auth-art-ground" />
    </div>
  );
}

export function WebPortalLoginPage({
  portalRole,
  onLogin,
}: {
  portalRole: WebPortalAppRole;
  onLogin: (role: WebPortalAppRole, email?: string) => void;
}) {
  const navigate = useNavigate();
  const portal = PORTALS[portalRole];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const preview = isLocalPreview();

  const enter = () => {
    onLogin(portalRole, email.trim());
    navigate(portal.home, { replace: true });
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    if (preview) {
      enter();
      return;
    }
    setPending(true);
    try {
      await signInAndResolveRole(portal.apiRole, email.trim(), password);
      enter();
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="s2l-auth-shell">
      <div className="s2l-auth-frame">
        <header className="s2l-auth-header">
          <a className="s2l-auth-brand" href="/login" aria-label="Sketch2Life — đăng nhập">
            <BrandWordmark size={34} />
            <span className="s2l-auth-brand-caption">WEB PORTALS</span>
          </a>

          <nav className="s2l-auth-portals" aria-label="Chọn cổng đăng nhập">
            {PORTAL_ORDER.map((role, index) => {
              const target = PORTALS[role];
              const active = role === portalRole;
              const url = portalLoginUrl(role, portalRole);

              return url ? (
                <a
                  key={role}
                  href={url}
                  className={"s2l-auth-portal" + (active ? " is-current" : "")}
                  aria-current={active ? "page" : undefined}
                >
                  <span className="s2l-auth-portal-index">0{index + 1}</span>
                  <span className="s2l-auth-portal-copy">
                    <span className="s2l-auth-portal-label">{target.englishLabel}</span>
                    <span className="s2l-auth-portal-state">{active ? "ĐANG MỞ" : "MỞ CỔNG"}</span>
                  </span>
                  <span className="s2l-auth-portal-mark"><PortalMark role={role} /></span>
                </a>
              ) : (
                <span
                  key={role}
                  className="s2l-auth-portal is-unavailable"
                  aria-disabled="true"
                  title={"Chưa cấu hình URL đăng nhập cho " + target.englishLabel}
                >
                  <span className="s2l-auth-portal-index">0{index + 1}</span>
                  <span className="s2l-auth-portal-copy">
                    <span className="s2l-auth-portal-label">{target.englishLabel}</span>
                    <span className="s2l-auth-portal-state">URL CHƯA CẤU HÌNH</span>
                  </span>
                  <span className="s2l-auth-portal-mark"><PortalMark role={role} /></span>
                </span>
              );
            })}
          </nav>
        </header>

        <div className="s2l-auth-main">
          <section className="s2l-auth-intro" aria-labelledby="s2l-auth-title">
            <p className="s2l-auth-eyebrow">
              <span className="s2l-auth-eyebrow-rule" />
              {portal.code}
            </p>
            <span className="s2l-auth-role">
              <span className="s2l-auth-role-icon"><PortalMark role={portalRole} /></span>
              <span>{portal.label}</span>
            </span>
            <h1 id="s2l-auth-title" className="s2l-auth-title">
              {portal.headline}<br />
              <em>{portal.headlineAccent}</em>
            </h1>
            <p className="s2l-auth-description">{portal.description}</p>


          </section>

          <section className="s2l-auth-panel" aria-labelledby="s2l-auth-form-title">
            <div className="s2l-auth-panel-heading">
              <p className="s2l-auth-panel-kicker">SECURE ACCESS <span>·</span> {portal.code.split(" / ")[0]}</p>
              <h2 id="s2l-auth-form-title">Chào mừng trở lại.</h2>
              <p className="s2l-auth-panel-subtitle">
                Đăng nhập bằng tài khoản được cấp cho {portal.label.toLowerCase()}.
              </p>
            </div>

            {preview && (
              <p className="s2l-auth-notice is-preview" role="status">
                <span className="s2l-auth-notice-icon" aria-hidden="true">i</span>
                Xem thử cục bộ · Không lưu dữ liệu.
              </p>
            )}

            <form
              className="s2l-auth-form"
              onSubmit={(event) => void submit(event)}
              aria-busy={pending}
              noValidate={false}
            >
              <label className="s2l-auth-field">
                <span>Email tài khoản</span>
                <input
                  type="email"
                  autoComplete="username"
                  inputMode="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="ten@truong.edu.vn"
                  aria-describedby={error ? "s2l-auth-error" : undefined}
                />
              </label>

              {!preview && (
                <label className="s2l-auth-field">
                  <span>Mật khẩu</span>
                  <input
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Nhập mật khẩu"
                    aria-describedby={portalRole === "ADMIN" ? "s2l-auth-admin-note" : undefined}
                  />
                </label>
              )}

              {portalRole === "ADMIN" && !preview && (
                <div className="s2l-auth-notice is-warning" id="s2l-auth-admin-note" role="note">
                  Backend hiện chưa có API xác nhận role Platform Admin. Đăng nhập thật sẽ bị từ chối sau bước xác thực cho đến khi backend bổ sung role discovery.
                </div>
              )}

              {error && <div className="s2l-auth-error" id="s2l-auth-error" role="alert">{error}</div>}

              <button className="s2l-auth-submit" type="submit" disabled={pending}>
                <span>{pending ? "Đang xác nhận tài khoản…" : preview ? "Vào bản xem thử" : "Đăng nhập bằng Firebase"}</span>
                {!pending && <span className="s2l-auth-submit-arrow" aria-hidden="true">↗</span>}
              </button>
            </form>

            {!preview && (
              <p className="s2l-auth-security-note">
                Vai trò sẽ được đối chiếu với assignment hoặc quyền do backend xác nhận. Nếu role không khớp, phiên xác thực sẽ không mở được cổng này.
              </p>
            )}
          </section>
          <figure className="s2l-auth-art" aria-hidden="true">
            <div className="s2l-auth-art-scene">
              <PortalArtFallback />
              <Suspense fallback={null}>
                <PortalLoginScene />
              </Suspense>
            </div>
            <figcaption className="s2l-auth-art-caption">
              <span>SKETCH2LIFE · LEARNING SPACE</span>
              <span>HỌC TẬP / SÁNG TẠO</span>
            </figcaption>
          </figure>
        </div>

        <footer className="s2l-auth-footer">
          <span>SKETCH2LIFE / WEB AUTHENTICATION</span>
          <span><span className="s2l-auth-footer-dot" /> Cổng truy cập theo vai trò</span>
        </footer>
      </div>
    </main>
  );
}
