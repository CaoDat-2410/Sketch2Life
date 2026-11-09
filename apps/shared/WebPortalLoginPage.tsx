import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BrandWordmark } from "./BrandMark";
import {
  backendMessage,
  isLocalPreview,
  signInAndResolveRole,
  type PortalRole,
} from "./backendApi";

export type WebPortalAppRole = "TEACHER" | "MANAGER" | "ADMIN";

const PORTALS: Record<WebPortalAppRole, {
  apiRole: PortalRole;
  label: string;
  description: string;
  home: string;
}> = {
  TEACHER: {
    apiRole: "teacher",
    label: "Giáo viên",
    description: "Lớp được phân công và giáo án trong tổ chức của bạn.",
    home: "/t01-lesson-workspace",
  },
  MANAGER: {
    apiRole: "school_manager",
    label: "Quản lý trường",
    description: "Lớp học và yêu cầu giáo án công khai trong tổ chức.",
    home: "/m02-organization-management",
  },
  ADMIN: {
    apiRole: "platform_admin",
    label: "Quản trị nền tảng",
    description: "Cổng vận hành chỉ mở sau khi backend xác nhận quyền quản trị.",
    home: "/a02-platform-operations",
  },
};

function PortalMark({ role }: { role: WebPortalAppRole }) {
  const paths: Record<WebPortalAppRole, React.ReactNode> = {
    TEACHER: <><path d="m5 16.5 8.8-8.8 3.5 3.5-8.8 8.8-4.3.8.8-4.3Z" /><path d="m12.5 9 3.5 3.5M4 22h16" /></>,
    MANAGER: <><path d="m3.5 10 8.5-6 8.5 6" /><path d="M5.5 9.5v10h13v-10M9 19.5v-5h6v5" /></>,
    ADMIN: <><path d="M12 3.5 20 7v5.5c0 4.2-3.2 7.2-8 9-4.8-1.8-8-4.8-8-9V7l8-3.5Z" /><path d="m8.5 12 2.3 2.3 4.8-5" /></>,
  };
  return <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[role]}</svg>;
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

  const submit = async (event: React.FormEvent) => {
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
    <main className="tw-hero-bg" style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <div className="tw-grid-2 s2l-login-grid" style={{ maxWidth: 920, width: "100%", gap: 24, alignItems: "stretch" }}>
        <section className="tw-card is-sky" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 28, padding: 34 }}>
          <div className="tw-row tw-between">
            <BrandWordmark size={30} />
            <span className="tw-chip">Cổng Web</span>
          </div>
          <div>
            <span className="tw-avatar is-sky" style={{ width: 62, height: 62 }}><PortalMark role={portalRole} /></span>
            <h1 className="tw-title" style={{ marginTop: 18, fontSize: 32, lineHeight: 1.15 }}>{portal.label}</h1>
            <p className="tw-sub" style={{ maxWidth: "42ch", lineHeight: 1.6 }}>{portal.description}</p>
          </div>
          <p className="tw-meta" style={{ margin: 0, lineHeight: 1.5 }}>
            {preview
              ? "Xem thử cục bộ · Không lưu dữ liệu."
              : "Đăng nhập qua Firebase. Vai trò sẽ được đối chiếu với assignment hoặc quyền do backend xác nhận."}
          </p>
        </section>

        <form onSubmit={(event) => void submit(event)} className="tw-card" style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 18, padding: 32 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 25, fontWeight: 800 }}>Đăng nhập</h2>
            <p className="tw-sub" style={{ marginTop: 6 }}>Dùng tài khoản được cấp cho {portal.label.toLowerCase()}.</p>
          </div>
          <label className="tw-label">Email tài khoản
            <input className="tw-input" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="ten@truong.edu.vn" />
          </label>
          {!preview && <label className="tw-label">Mật khẩu
            <input className="tw-input" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Mật khẩu Firebase" />
          </label>}
          {portalRole === "ADMIN" && !preview && <div className="tw-item is-amber" role="note" style={{ lineHeight: 1.5 }}>
            BE hiện chưa có API xác nhận role Platform Admin. Đăng nhập thật sẽ bị từ chối sau bước xác thực cho đến khi BE bổ sung role discovery.
          </div>}
          {error && <div className="tw-item is-rose" role="alert" style={{ lineHeight: 1.5 }}>{error}</div>}
          <button type="submit" className="tw-btn" disabled={pending} style={{ width: "100%", justifyContent: "center", marginTop: 2 }}>
            {pending ? "Đang xác nhận tài khoản…" : preview ? "Vào bản xem thử" : "Đăng nhập bằng Firebase"}
          </button>
          {!preview && <p className="tw-meta" style={{ margin: 0, lineHeight: 1.5 }}>
            Nếu role không khớp, phiên Firebase sẽ được đóng và không thể mở màn hình của cổng này.
          </p>}
        </form>
      </div>
    </main>
  );
}

