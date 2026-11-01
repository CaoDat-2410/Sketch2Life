import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Logo } from "./Logo";
import { Icon, IconName } from "../components/Icon";

const SIDEBAR_ITEMS: { to: string; label: string; icon: IconName }[] = [
  { to: "/a02-platform-operations", label: "Tổng quan", icon: "sun" },
  { to: "/a02-platform-operations?panel=organizations", label: "Tổ chức", icon: "users" },
  { to: "/a01-content-moderation", label: "Thư viện bài học", icon: "book" },
  { to: "/a02-platform-operations?panel=activities", label: "Hoạt động", icon: "leaf" },
  { to: "/a02-platform-operations?panel=policy", label: "Quota & chính sách", icon: "lock" },
  { to: "/a02-platform-operations?panel=audit", label: "Nhật ký", icon: "clock" },
];

const QUICK_SCREENS = [
  { id: "A01", to: "/a01-content-moderation", label: "A01" },
  { id: "A02", to: "/a02-platform-operations", label: "A02" },
];

const SCREEN_NAMES: Record<string, string> = {
  "/a01-content-moderation": "Thư viện bài học",
  "/a02-platform-operations": "Vận hành nền tảng",
};

export function AdminLayout({
  children,
  toast,
}: {
  children: React.ReactNode;
  toast: { kind: "ok" | "info" | "warn" | "err"; text: string } | null;
}) {
  const location = useLocation();
  const currentTitle = SCREEN_NAMES[location.pathname] ?? "Quản trị nền tảng";

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)" }}>
      {/* ── Left Sidebar ── */}
      <aside
        style={{
          width: 240,
          background: "#FFFFFF",
          borderRight: "1px solid var(--line)",
          display: "flex",
          flexDirection: "column",
          padding: "20px 12px",
          flexShrink: 0,
          position: "sticky",
          top: 0,
          height: "100vh",
        }}
      >
        <div style={{ padding: "0 8px 18px", borderBottom: "1px solid var(--line)" }}>
          <Logo height={28} />
        </div>

        <nav className="col" style={{ gap: 4, marginTop: 14, flex: 1 }} aria-label="Điều hướng Quản trị nền tảng">
          {SIDEBAR_ITEMS.map((item) => {
            const active =
              item.to === "/a01-content-moderation"
                ? location.pathname === "/a01-content-moderation"
                : location.pathname === "/a02-platform-operations" &&
                  (item.to.includes(location.search) || (!location.search && item.label === "Tổng quan"));

            return (
              <NavLink
                key={item.label}
                to={item.to}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 12px",
                  borderRadius: 12,
                  fontWeight: active ? 800 : 600,
                  fontSize: 14,
                  color: active ? "var(--primary)" : "var(--ink-2)",
                  background: active
                    ? "linear-gradient(135deg, var(--primary-50) 0%, #EFF6FF 100%)"
                    : "transparent",
                  boxShadow: active ? "0 1px 4px rgba(37,99,235,0.10)" : "none",
                  transition: "all 120ms cubic-bezier(0.2,0,0,1)",
                }}
              >
                <Icon name={item.icon} size={18} color={active ? "var(--primary)" : "var(--ink-3)"} />
                <span>{item.label}</span>
                {active && (
                  <span
                    style={{
                      marginLeft: "auto",
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: "var(--primary)",
                    }}
                  />
                )}
              </NavLink>
            );
          })}
        </nav>

        <div
          style={{
            padding: "12px 14px",
            borderRadius: 14,
            background: "linear-gradient(135deg, var(--primary-50) 0%, #EFF6FF 100%)",
            border: "1px solid var(--primary-100)",
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              background: "var(--primary)",
              color: "#FFF",
              fontWeight: 800,
              fontSize: 16,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 8,
            }}
          >
            A
          </div>
          <div style={{ fontWeight: 800, fontSize: 14 }}>Quản trị nền tảng</div>
          <div className="muted small">Toàn hệ thống Sketch2Life</div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header
          style={{
            background: "#FFFFFF",
            borderBottom: "1px solid var(--line)",
            padding: "12px 24px",
            display: "flex",
            alignItems: "center",
            gap: 12,
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <div style={{ fontWeight: 800, fontSize: 16, color: "var(--ink)" }}>{currentTitle}</div>

          <div style={{ display: "flex", gap: 6, marginLeft: 8 }}>
            {QUICK_SCREENS.map((s) => {
              const active = location.pathname === s.to;
              return (
                <NavLink
                  key={s.id}
                  to={s.to}
                  style={{
                    padding: "4px 12px",
                    borderRadius: 999,
                    fontSize: 12,
                    fontWeight: 700,
                    background: active ? "var(--primary)" : "var(--primary-50)",
                    color: active ? "#FFFFFF" : "var(--primary)",
                    transition: "all 120ms cubic-bezier(0.2,0,0,1)",
                  }}
                >
                  {s.label}
                </NavLink>
              );
            })}
          </div>

          <span className="spacer" />
          <span className="pill ok" style={{ fontSize: 12 }}>Chỉ siêu dữ liệu · Không media trẻ</span>
        </header>

        {toast && (
          <div
            role="status"
            style={{
              margin: "14px 24px 0",
              padding: "11px 16px",
              borderRadius: 12,
              fontWeight: 600,
              fontSize: 14,
              display: "flex",
              alignItems: "center",
              gap: 8,
              background:
                toast.kind === "ok"
                  ? "var(--mint-50)"
                  : toast.kind === "warn"
                  ? "var(--warn-50)"
                  : toast.kind === "err"
                  ? "var(--danger-50)"
                  : "var(--primary-50)",
              color:
                toast.kind === "ok"
                  ? "var(--mint-700)"
                  : toast.kind === "warn"
                  ? "var(--warn-700)"
                  : toast.kind === "err"
                  ? "var(--danger)"
                  : "var(--primary)",
              border: "1px solid var(--line)",
            }}
          >
            <Icon
              name={
                toast.kind === "ok" ? "check" : toast.kind === "err" ? "close" : "alert"
              }
              size={16}
            />
            {toast.text}
          </div>
        )}

        <main style={{ padding: 24, maxWidth: 1280, width: "100%" }}>{children}</main>
      </div>
    </div>
  );
}
