import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Logo } from "./Logo";
import { MgIcon, MgIconName } from "./MgIcon";
import { BackendModeNotice, isLocalPreview } from "../../../shared/backendApi";
import { RoleHelp } from "../../../shared/RoleHelp";
import "../styles/mg-manage.css";

const SIDEBAR_ITEMS: { to: string; label: string; icon: MgIconName; matchPanel?: string }[] = [
  { to: "/a02-platform-operations", label: "Tổng quan", icon: "home" },
  { to: "/a02-platform-operations?panel=orgs", label: "Tổ chức", icon: "building", matchPanel: "orgs" },
  { to: "/a01-content-moderation", label: "Thư viện bài học", icon: "book" },
  { to: "/a02-platform-operations?panel=catalog", label: "Danh mục hoạt động", icon: "grid", matchPanel: "catalog" },
  { to: "/a02-platform-operations?panel=quota", label: "Hạn mức & chính sách", icon: "shield", matchPanel: "quota" },
  { to: "/a02-platform-operations?panel=audit", label: "Nhật ký", icon: "doc", matchPanel: "audit" },
];

export function AdminLayout({
  children,
  toast,
}: {
  children: React.ReactNode;
  toast: { kind: "ok" | "info" | "warn" | "err"; text: string } | null;
}) {
  const location = useLocation();
  const currentPanel = new URLSearchParams(location.search).get("panel");
  const previewMode = isLocalPreview();
  const visibleItems = previewMode
    ? SIDEBAR_ITEMS
    : SIDEBAR_ITEMS.filter((item) => item.to === "/a02-platform-operations" || item.to === "/a01-content-moderation");

  return (
    <div className="mg-shell">
      <aside className="mg-side">
        <div className="mg-side-brand s2l-side-brand">
          <Logo height={28} />
          <span className="mg-role-chip s2l-role-chip">
            <MgIcon name="shield" size={13} /> Quản trị nền tảng
          </span>
        </div>

        <nav className="mg-nav" aria-label="Điều hướng Quản trị nền tảng">
          {visibleItems.map((item) => {
            const active =
              item.to === "/a01-content-moderation"
                ? location.pathname === "/a01-content-moderation"
                : location.pathname === "/a02-platform-operations" &&
                  (item.matchPanel ? currentPanel === item.matchPanel : !currentPanel);
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`mg-nav-item${active ? " is-active" : ""}`}
                aria-current={active ? "page" : undefined}
                aria-label={item.label}
                title={item.label}
              >
                <span className="mg-nav-ico">
                  <MgIcon name={item.icon} size={18} />
                </span>
                <span className="mg-label">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mg-profile">
          <span className="mg-avatar" style={{ background: "#FEF3C7", color: "#B45309" }}>QT</span>
          <div className="mg-profile-text">
            <div className="mg-profile-name">Quản trị viên</div>
            <div className="mg-profile-sub">{previewMode ? "Dữ liệu xem thử" : "Role chưa xác minh từ BE"}</div>
          </div>
        </div>
      </aside>

      <div className="mg-main-wrap">
        <header className="mg-top">
          <RoleHelp role="ADMIN" />
          <button type="button" className="mg-top-btn" aria-label="Thông báo">
            <MgIcon name="bell" size={18} />
            <span className="mg-dot" />
          </button>
          <span className="mg-org-pill">
            <span className="mg-avatar" style={{ width: 28, height: 28, background: "#DBEAFE", color: "#2563EB", fontSize: 12 }}>A</span>
            {previewMode ? "Quản trị viên" : "Phiên chưa xác minh role"}
            <MgIcon name="chevdown" size={14} />
          </span>
        </header>

        {toast && (
          <div role="status" className={`mg-toast ${toast.kind}`}>
            <MgIcon name={toast.kind === "ok" ? "check" : "bell"} size={18} />
            {toast.text}
          </div>
        )}

        <main className="mg-main">{previewMode && <BackendModeNotice roleLabel="Quản trị nền tảng" />}{children}</main>
      </div>
    </div>
  );
}
