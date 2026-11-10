import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Logo } from "./Logo";
import { MgIcon, MgIconName } from "./MgIcon";
import { BackendModeNotice, isLocalPreview } from "../../../shared/backendApi";
import { RoleHelp } from "../../../shared/RoleHelp";

const SIDEBAR_ITEMS: { to: string; label: string; icon: MgIconName; matchSection?: string }[] = [
  { to: "/m02-organization-management", label: "Tổng quan", icon: "home" },
  { to: "/m02-organization-management?section=teachers", label: "Giáo viên & nhóm", icon: "users", matchSection: "teachers" },
  { to: "/m02-organization-management?section=classes", label: "Lớp & suất học", icon: "calendar", matchSection: "classes" },
  { to: "/m02-organization-management?section=quota", label: "Lượt video", icon: "chart", matchSection: "quota" },
  { to: "/m01-publication-review", label: "Duyệt công khai", icon: "shield" },
  { to: "/m02-organization-management?section=settings", label: "Cài đặt", icon: "gear", matchSection: "settings" },
];

const SCREEN_NAMES: Record<string, string> = {
  "/m01-publication-review": "Duyệt công khai",
  "/m02-organization-management": "Quản lý trường",
};

export function ManagerLayout({
  children,
  toast,
  onLogout,
}: {
  children: React.ReactNode;
  toast: { kind: "ok" | "info" | "warn" | "err"; text: string } | null;
  onLogout: () => void;
}) {
  const location = useLocation();
  const currentTitle = SCREEN_NAMES[location.pathname] ?? "Quản lý trường";
  const currentSection = new URLSearchParams(location.search).get("section");
  const previewMode = isLocalPreview();
  const visibleItems = previewMode
    ? SIDEBAR_ITEMS
    : SIDEBAR_ITEMS.filter((item) => item.to === "/m02-organization-management" || item.to === "/m01-publication-review");

  return (
    <div className="mg-shell">
      <aside className="mg-side">
        <div className="mg-side-brand s2l-side-brand">
          <Logo height={28} />
          <span className="mg-role-chip s2l-role-chip">
            <MgIcon name="school" size={13} /> Quản lý trường
          </span>
        </div>

        <nav className="mg-nav" aria-label="Điều hướng Quản lý trường">
          {visibleItems.map((item) => {
            const active =
              item.to === "/m01-publication-review"
                ? location.pathname === "/m01-publication-review"
                : location.pathname === "/m02-organization-management" &&
                  (item.matchSection ? currentSection === item.matchSection : !currentSection);
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
          <span className="mg-avatar mg-avatar--profile">HT</span>
          <div className="mg-profile-text">
            <div className="mg-profile-name">{previewMode ? "Hiệu trưởng Minh" : "Quản lý trường"}</div>
            <div className="mg-profile-sub">{previewMode ? "Dữ liệu xem thử" : "Role được backend xác nhận"}</div>
          </div>
        </div>
        <button
          type="button"
          className="mg-logout-btn"
          onClick={onLogout}
          aria-label="Đăng xuất"
          title="Đăng xuất khỏi cổng Quản lý trường"
        >
          <MgIcon name="logout" size={18} />
          <span className="mg-logout-label">Đăng xuất</span>
        </button>
      </aside>

      <div className="mg-main-wrap">
        <header className="mg-top">
          <span className="sr-only" style={{ position: "absolute", left: -9999 }}>{currentTitle}</span>
          <RoleHelp role="MANAGER" />
          <div className="mg-inbox-unavailable" role="status" aria-label="Hộp thư thông báo chưa khả dụng" title="API hộp thư thông báo chưa được cung cấp">
            <MgIcon name="bell" size={17} />
            <span>Hộp thư chưa khả dụng</span>
          </div>
          <div className="mg-org-context">
            <span className="mg-avatar mg-avatar--organization">
              <MgIcon name="school" size={14} />
            </span>
            {previewMode ? "Trường Mầm non Ánh Dương" : "Tổ chức theo assignment"}
          </div>
        </header>

        {toast && (
          <div role="status" className={`mg-toast ${toast.kind}`}>
            <MgIcon name={toast.kind === "ok" ? "check" : "bell"} size={18} />
            {toast.text}
          </div>
        )}

        <main className="mg-main">{previewMode && <BackendModeNotice roleLabel="Quản lý trường" />}{children}</main>
      </div>
    </div>
  );
}
