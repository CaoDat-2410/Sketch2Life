import React, { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  ClipboardList,
  CreditCard,
  FileClock,
  FileUp,
  Gauge,
  GraduationCap,
  History,
  Inbox,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Menu,
  Presentation,
  School,
  Settings2,
  ShieldCheck,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import { BrandWordmark } from "./BrandMark";
import { AccessibleDialog } from "./ui";
import { authService } from "../modules/school-manager/be1/services/authService";

export type PortalNavigationItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  state?: "available" | "waiting";
  matchPrefix?: boolean;
};

export type PortalNavigationGroup = {
  label: string;
  items: PortalNavigationItem[];
};

export const TEACHER_NAVIGATION: PortalNavigationGroup[] = [
  {
    label: "Dạy học",
    items: [
      { href: "/teacher/t01-lesson-workspace", label: "Tổng quan", icon: LayoutDashboard, state: "available" },
      { href: "/teacher/t05-classes-and-children", label: "Lớp được phân công", icon: Users, state: "available", matchPrefix: true },
      { href: "/teacher/t02-lesson-authoring", label: "Giáo án", icon: BookOpen, state: "available" },
      { href: "/teacher/t03-document-import-review", label: "Nhập tài liệu", icon: FileUp, state: "available" },
      { href: "/teacher/t04-session-sketch-deck", label: "Buổi dạy", icon: CalendarDays, state: "waiting" },
      { href: "/teacher/t02-presentation", label: "Trình bày giáo án", icon: Presentation, state: "waiting" },
      { href: "/teacher/t12-activities", label: "Hoạt động", icon: ClipboardList, state: "waiting" },
      { href: "/teacher/t13-ai-lesson-workflow", label: "Gợi ý giáo án AI", icon: BookOpen, state: "available" },
    ],
  },
  {
    label: "Tài khoản",
    items: [
      { href: "/teacher/t09-history", label: "Lịch sử", icon: History, state: "waiting" },
      { href: "/teacher/t10-inbox", label: "Hộp thư", icon: Inbox, state: "waiting" },
      { href: "/teacher/t11-profile", label: "Hồ sơ cá nhân", icon: GraduationCap, state: "waiting" },
      { href: "/teacher/t08-settings", label: "Cài đặt", icon: Settings2, state: "waiting" },
    ],
  },
];

export const SCHOOL_MANAGER_NAVIGATION: PortalNavigationGroup[] = [
  {
    label: "Nhà trường",
    items: [
      { href: "/school", label: "Tổng quan", icon: LayoutDashboard, state: "available" },
      { href: "/school/classes", label: "Lớp học", icon: School, state: "available" },
      { href: "/school/review-content", label: "Duyệt học liệu", icon: BookOpen, state: "available" },
      { href: "/school/teachers", label: "Giáo viên & roster", icon: Users, state: "waiting" },
    ],
  },
  {
    label: "Dịch vụ",
    items: [
      { href: "/school/capacity", label: "Sức chứa", icon: Gauge, state: "waiting" },
      { href: "/school/billing", label: "Thanh toán", icon: CreditCard, state: "waiting" },
      { href: "/school/quota", label: "Hạn mức", icon: Activity, state: "waiting" },
      { href: "/school/inbox", label: "Hộp thư", icon: Inbox, state: "waiting" },
    ],
  },
];

export const PLATFORM_ADMIN_NAVIGATION: PortalNavigationGroup[] = [
  {
    label: "Vận hành",
    items: [
      { href: "/platform/a02-platform-operations", label: "Tổng quan", icon: LayoutDashboard, state: "available" },
      { href: "/platform/a02-platform-operations?panel=queues", label: "Queue & jobs", icon: Activity, state: "waiting" },
      { href: "/platform/a02-platform-operations?panel=lifecycle", label: "Vòng đời dữ liệu", icon: FileClock, state: "waiting" },
      { href: "/platform/a02-platform-operations?panel=billing", label: "Đối soát thanh toán", icon: CreditCard, state: "waiting" },
      { href: "/platform/a02-platform-operations?panel=audit", label: "Nhật ký kiểm toán", icon: History, state: "waiting" },
    ],
  },
  {
    label: "Nội dung & quyền",
    items: [
      { href: "/platform/a01-content-moderation", label: "Duyệt học liệu", icon: ShieldCheck, state: "waiting" },
      { href: "/platform/a02-platform-operations?panel=catalog", label: "Danh mục hoạt động", icon: BookOpen, state: "waiting" },
      { href: "/platform/a02-platform-operations?panel=permissions", label: "Vai trò & quyền", icon: Users, state: "waiting" },
      { href: "/platform/accounts", label: "Tài khoản & vai trò", icon: Users, state: "available" },
      { href: "/platform/a02-platform-operations?panel=quota", label: "Quota & chính sách", icon: Gauge, state: "waiting" },
    ],
  },
];

type SessionToast = { kind: "ok" | "info" | "warn" | "err"; text: string };

function navigationMatches(href: string, pathname: string, search: string, matchPrefix?: boolean) {
  const [itemPath, query = ""] = href.split("?");
  if (matchPrefix && pathname.startsWith(itemPath)) return true;
  if (pathname !== itemPath) return false;
  const itemParams = new URLSearchParams(query);
  const currentParams = new URLSearchParams(search);
  for (const [key, value] of itemParams.entries()) {
    if (currentParams.get(key) !== value) return false;
  }
  return itemParams.toString() === currentParams.toString();
}

function pageTitle(groups: PortalNavigationGroup[], pathname: string, search: string) {
  for (const group of groups) {
    for (const item of group.items) {
      if (navigationMatches(item.href, pathname, search, item.matchPrefix)) return item.label;
    }
  }
  return "Không gian làm việc";
}

export function WebAppShell({
  roleLabel,
  roleSubtitle,
  navigation,
  loginHref,
  modeLabel,
  toast,
  onLogout,
  children,
}: {
  roleLabel: string;
  roleSubtitle: string;
  navigation: PortalNavigationGroup[];
  loginHref: string;
  modeLabel: string;
  toast?: SessionToast | null;
  onLogout: () => void;
  children: React.ReactNode;
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const firstLink = useRef<HTMLAnchorElement>(null);
  const heading = pageTitle(navigation, location.pathname, location.search);

  useEffect(() => {
    if (menuOpen) firstLink.current?.focus();
  }, [menuOpen]);

  useEffect(() => setMenuOpen(false), [location.pathname, location.search]);

  const closeMenu = () => {
    setMenuOpen(false);
    menuButton.current?.focus();
  };

  const logout = () => {
    setMenuOpen(false);
    onLogout();
    navigate(loginHref);
  };

  const changePassword = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordMessage("");
    if (newPassword.length < 6 || newPassword !== passwordConfirmation) {
      setPasswordMessage("Mật khẩu mới cần ít nhất 6 ký tự và hai ô phải trùng nhau.");
      return;
    }
    setPasswordBusy(true);
    try {
      await authService.changePassword(currentPassword, newPassword);
      setPasswordMessage("Đã đổi mật khẩu.");
      setCurrentPassword("");
      setNewPassword("");
      setPasswordConfirmation("");
    } catch {
      setPasswordMessage("Không thể đổi mật khẩu. Kiểm tra mật khẩu hiện tại rồi thử lại.");
    } finally {
      setPasswordBusy(false);
    }
  };

  return (
    <div className={"s2l-app-shell" + (menuOpen ? " is-menu-open" : "")} onKeyDown={(event) => {
      if (event.key === "Escape" && menuOpen) closeMenu();
    }}>
      <a className="s2l-skip-link" href="#s2l-main">Bỏ qua điều hướng</a>
      <aside className="s2l-sidebar" id="s2l-navigation" aria-label={"Cổng " + roleLabel}>
        <div className="s2l-brand-lockup">
          <BrandWordmark size={30} />
          <div><strong>Sketch2Life</strong><span>{roleLabel}</span></div>
          <button type="button" className="s2l-close-menu" aria-label="Đóng điều hướng" onClick={closeMenu}><X size={19} /></button>
        </div>
        <div className="s2l-sidebar-caption">{roleSubtitle}</div>
        <nav className="s2l-nav" aria-label={"Điều hướng " + roleLabel}>
          {navigation.map((group) => (
            <section className="s2l-nav-group" key={group.label} aria-label={group.label}>
              <h2>{group.label}</h2>
              {group.items.map((item, index) => {
                const active = navigationMatches(item.href, location.pathname, location.search, item.matchPrefix);
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.href}
                    ref={group === navigation[0] && index === 0 ? firstLink : undefined}
                    to={item.href}
                    className={"s2l-nav-link" + (active ? " is-active" : "")}
                    aria-current={active ? "page" : undefined}
                    onClick={() => { if (menuOpen) menuButton.current?.focus(); setMenuOpen(false); }}
                  >
                    <Icon size={18} strokeWidth={1.85} aria-hidden="true" />
                    <span>{item.label}</span>
                    {item.state === "waiting" && <span className="s2l-nav-state" title="Đang chờ API">Chờ API</span>}
                  </NavLink>
                );
              })}
            </section>
          ))}
        </nav>
        <div className="s2l-sidebar-bottom">
          <div className="s2l-session-status"><span aria-hidden="true" /><div><strong>{modeLabel}</strong><span>Quyền được kiểm tra theo phiên</span></div></div>
          <button className="s2l-password-button" type="button" onClick={() => { setPasswordMessage(""); setPasswordDialogOpen(true); }}><KeyRound size={17} aria-hidden="true" />Đổi mật khẩu</button>
          <button className="s2l-logout-button" type="button" onClick={logout}><LogOut size={17} aria-hidden="true" />Đăng xuất</button>
        </div>
      </aside>
      <button className="s2l-nav-scrim" type="button" aria-label="Đóng điều hướng" tabIndex={menuOpen ? 0 : -1} onClick={closeMenu} />
      <div className="s2l-workspace">
        <header className="s2l-topbar">
          <div className="s2l-topbar-title">
            <button ref={menuButton} className="s2l-menu-button" type="button" aria-label={menuOpen ? "Đóng điều hướng" : "Mở điều hướng"} aria-controls="s2l-navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div><span>Sketch2Life <span aria-hidden="true">/</span> {roleLabel}</span><strong>{heading}</strong></div>
          </div>
          <div className="s2l-topbar-tools">
            <span className="s2l-mode-chip"><span aria-hidden="true" />{modeLabel}</span>
            <button type="button" className="s2l-account-button" onClick={() => navigate(roleLabel === "Giáo viên" ? "/teacher/t11-profile" : roleLabel === "School Manager" ? "/school/teachers" : "/platform/a02-platform-operations?panel=permissions")}>
              <span className="s2l-account-avatar" aria-hidden="true">{roleLabel === "Giáo viên" ? "GV" : roleLabel === "School Manager" ? "SM" : "PA"}</span>
              <span>{roleLabel}</span><ArrowUpRight size={15} aria-hidden="true" />
            </button>
          </div>
        </header>
        {toast && <div className={"s2l-toast is-" + toast.kind} role="status" aria-live="polite">{toast.text}</div>}
        <main className="s2l-main" id="s2l-main" tabIndex={-1} key={location.pathname + location.search}>
          {children}
        </main>
      </div>
      <AccessibleDialog
        open={passwordDialogOpen}
        onOpenChange={setPasswordDialogOpen}
        title="Đổi mật khẩu"
        description="Xác minh mật khẩu hiện tại và đặt mật khẩu mới cho tài khoản."
        className="s2l-password-dialog"
      >
        <form className="s2l-password-form" onSubmit={(event) => void changePassword(event)} aria-busy={passwordBusy}>
          <h2>Đổi mật khẩu</h2>
          <label>Mật khẩu hiện tại<input type="password" autoComplete="current-password" required value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /></label>
          <label>Mật khẩu mới<input type="password" autoComplete="new-password" minLength={6} required value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></label>
          <label>Xác nhận mật khẩu mới<input type="password" autoComplete="new-password" minLength={6} required value={passwordConfirmation} onChange={(event) => setPasswordConfirmation(event.target.value)} /></label>
          {passwordMessage && <p role="status" aria-live="polite">{passwordMessage}</p>}
          <button type="submit" disabled={passwordBusy}>{passwordBusy ? "Đang lưu…" : "Cập nhật"}</button>
        </form>
      </AccessibleDialog>
    </div>
  );
}
