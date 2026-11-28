import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  BookOpenCheck,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  CreditCard,
  DatabaseBackup,
  Eye,
  EyeOff,
  FileClock,
  FileUp,
  Gauge,
  GraduationCap,
  History,
  Inbox,
  KeyRound,
  LayoutDashboard,
  LoaderCircle,
  LogOut,
  MailCheck,
  Menu,
  MessageSquareText,
  Puzzle,
  School,
  ScrollText,
  Shapes,
  ShieldCheck,
  TriangleAlert,
  UserRound,
  Users,
  Video,
  WandSparkles,
  X,
  type LucideIcon,
} from "lucide-react";
import platformAdminLogo from "../assets/sketch2life-logo-mark-128.png";
import { useUnreadCount } from "../notifications/useUnreadCount";
import { AccessibleDialog } from "../components/ui";
import { Alert, Button, FormField } from "../ui";
import { authService } from "../../modules/school-manager/be1/services/authService";

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

type PortalNavigationStatus = "pending" | "done" | "failed";

const NAV_STATUS_LABELS: Record<PortalNavigationStatus, string> = {
  pending: "Đang xử lý yêu cầu AI",
  done: "Yêu cầu AI đã xong",
  failed: "Yêu cầu AI chưa thành công",
};

export const TEACHER_NAVIGATION: PortalNavigationGroup[] = [
  {
    label: "",
    items: [
      { href: "/teacher/t01-lesson-workspace", label: "Tổng quan", icon: LayoutDashboard, state: "available" },
    ],
  },
  {
    label: "Học liệu",
    items: [
      { href: "/teacher/t02-lesson-authoring", label: "Giáo án", icon: BookOpen, state: "available" },
      { href: "/teacher/t13-ai-lesson-workflow", label: "Gợi ý giáo án AI", icon: WandSparkles, state: "available" },
      { href: "/teacher/t03-document-import-review", label: "Nhập tài liệu", icon: FileUp, state: "available" },
      { href: "/teacher/t12-activities", label: "Hoạt động", icon: Puzzle, state: "available" },
      { href: "/teacher/svg-catalog", label: "Danh mục SVG", icon: Shapes, state: "available" },
      { href: "/teacher/t14-feedback", label: "Phản hồi giáo án", icon: MessageSquareText, state: "available" },
    ],
  },
  {
    label: "Lên lớp",
    items: [
      { href: "/teacher/t05-classes-and-children", label: "Lớp được phân công", icon: Users, state: "available", matchPrefix: true },
      { href: "/teacher/t04-session-sketch-deck", label: "Buổi dạy", icon: CalendarDays, state: "available" },
      { href: "/teacher/t09-history", label: "Lịch sử buổi dạy", icon: History, state: "available" },
    ],
  },
  {
    label: "Tài khoản",
    items: [
      { href: "/teacher/t10-inbox", label: "Hộp thư", icon: Inbox, state: "available" },
      { href: "/teacher/t11-profile", label: "Hồ sơ cá nhân", icon: UserRound, state: "available" },
    ],
  },
];

export const SCHOOL_MANAGER_NAVIGATION: PortalNavigationGroup[] = [
  {
    label: "Nhà trường",
    items: [
      { href: "/school", label: "Tổng quan", icon: LayoutDashboard, state: "available" },
      { href: "/school/classes", label: "Lớp học", icon: School, state: "available" },
      { href: "/school/teachers", label: "Hồ sơ & đồng ý", icon: ClipboardCheck, state: "available" },
      { href: "/school/teacher-assignments", label: "Phân công giáo viên", icon: GraduationCap, state: "available" },
      { href: "/school/parent-groups", label: "Nhóm phụ huynh", icon: Users, state: "available" },
      { href: "/school/data-requests", label: "Yêu cầu dữ liệu", icon: FileClock, state: "available" },
    ],
  },
  {
    label: "Học liệu & phản hồi",
    items: [
      { href: "/school/review-content", label: "Duyệt học liệu", icon: BookOpenCheck, state: "available" },
      { href: "/school/feedback", label: "Phản hồi trong trường", icon: MessageSquareText, state: "available" },
    ],
  },
  {
    label: "Nguồn lực",
    items: [
      { href: "/school/capacity", label: "Sức chứa", icon: Gauge, state: "available" },
      { href: "/school/quota", label: "Hạn mức video", icon: Video, state: "available" },
      { href: "/school/billing", label: "Thanh toán", icon: CreditCard, state: "available" },
    ],
  },
  {
    label: "Thông báo",
    items: [
      { href: "/school/inbox", label: "Hộp thư", icon: Inbox, state: "available" },
    ],
  },
  {
    label: "Tài khoản",
    items: [
      { href: "/school/account", label: "Thông tin tài khoản", icon: UserRound, state: "available" },
    ],
  },
];
export const PLATFORM_ADMIN_NAVIGATION: PortalNavigationGroup[] = [
  { label: "", items: [
    { href: "/platform/a02-platform-operations", label: "Tổng quan", icon: LayoutDashboard, state: "available" },
  ] },
  { label: "Quản lý", items: [
    { href: "/platform/a02-platform-operations?panel=orgs", label: "Trường học", icon: School, state: "available" },
    { href: "/platform/accounts", label: "Tài khoản & vai trò", icon: Users, state: "available" },
    { href: "/platform/a02-platform-operations?panel=permissions", label: "Phân quyền duyệt", icon: ShieldCheck, state: "available" },
  ] },
  { label: "Nội dung", items: [
    { href: "/platform/a01-content-moderation", label: "Học liệu", icon: BookOpen, state: "available" },
    { href: "/platform/a02-platform-operations?panel=catalog", label: "Hoạt động", icon: Puzzle, state: "available" },
    { href: "/platform/a02-platform-operations?panel=feedback", label: "Phản hồi", icon: MessageSquareText, state: "available" },
    { href: "/platform/a02-platform-operations?panel=svgcatalog", label: "Danh mục SVG", icon: Shapes, state: "available" },
  ] },
  { label: "Tài chính & hạn mức", items: [
    { href: "/platform/a02-platform-operations?panel=billing", label: "Thanh toán", icon: CreditCard, state: "available" },
    { href: "/platform/a02-platform-operations?panel=quota", label: "Hạn mức video", icon: Video, state: "available" },
    { href: "/platform/a02-platform-operations?panel=capacity", label: "Sức chứa lớp", icon: Gauge, state: "available" },
  ] },
  { label: "Hệ thống", items: [
    { href: "/platform/a02-platform-operations?panel=queues", label: "Giám sát vận hành", icon: Activity, state: "available" },
    { href: "/platform/a02-platform-operations?panel=lifecycle", label: "Dữ liệu & lưu trữ", icon: DatabaseBackup, state: "available" },
    { href: "/platform/a02-platform-operations?panel=audit", label: "Nhật ký kiểm toán", icon: ScrollText, state: "available" },
    { href: "/platform/a02-platform-operations?panel=settings", label: "Email hệ thống", icon: MailCheck, state: "available" },
  ] },
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
  if (itemPath.startsWith("/platform/")) {
    return itemParams.has("panel") || !currentParams.has("panel");
  }
  if (!query) return true;
  return itemParams.toString() === currentParams.toString();
}

function pageTitle(groups: PortalNavigationGroup[], pathname: string, search: string) {
  for (const group of groups) {
    for (const item of group.items) {
      if (navigationMatches(item.href, pathname, search, item.matchPrefix)) return item.label;
    }
  }
  if (pathname.startsWith("/teacher/t02-presentation")) return "Trình bày giáo án";
  if (pathname.startsWith("/teacher/t06-sample-story-run")) return "Video mẫu";
  if (pathname.startsWith("/teacher/t07-video-presentation-confirmation")) return "Chiếu cho lớp";
  return "Không gian làm việc";
}

export function WebAppShell({
  portal,
  roleLabel,
  navigation,
  navStatus,
  loginHref,
  modeLabel,
  toast,
  onLogout,
  children,
}: {
  portal: "teacher" | "manager" | "platform";
  roleLabel: string;
  /** Kept for callers; the shared shell no longer shows a caption under the brand. */
  roleSubtitle?: string;
  navigation: PortalNavigationGroup[];
  navStatus?: Partial<Record<string, PortalNavigationStatus | undefined>>;
  loginHref: string;
  modeLabel: string;
  toast?: SessionToast | null;
  onLogout: () => void;
  children: React.ReactNode;
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const hasInbox = navigation.some((group) => group.items.some((item) => item.href === "/teacher/t10-inbox" || item.href === "/school/inbox"));
  const unreadCount = useUnreadCount(hasInbox, location.pathname + location.search + location.hash);
  const unreadLabel = unreadCount === null ? null : unreadCount > 99 ? "hơn 99 thông báo chưa đọc" : `${unreadCount} thông báo chưa đọc`;
  const badge = unreadCount === null ? null : <span className="s2l-nav-unread" aria-hidden="true">{unreadCount > 99 ? "99+" : unreadCount}</span>;
  const [menuOpen, setMenuOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [visiblePasswords, setVisiblePasswords] = useState([false, false, false]);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const isPlatformAdmin = portal === "platform";
  const isSchoolManager = portal === "manager";
  const [account, setAccount] = useState({ displayName: "", email: "" });
  useEffect(() => {
    if (!isPlatformAdmin) return;
    return authService.observe((user) => setAccount({ displayName: user?.displayName ?? "", email: user?.email ?? "" }));
  }, [isPlatformAdmin]);
  const accountDisplayName = account.displayName || "Quản trị viên";
  const activeGroup = navigation.find((group) =>
    group.items.some((item) => navigationMatches(item.href, location.pathname, location.search, item.matchPrefix)),
  )?.label ?? navigation[0]?.label;
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const topAccountDetails = useRef<HTMLDetailsElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const firstLink = useRef<HTMLAnchorElement>(null);
  const heading = isPlatformAdmin && new URLSearchParams(location.search).get("panel") === "inbox"
    ? "Hộp thư"
    : pageTitle(navigation, location.pathname, location.search);
  const homePath = navigation[0]?.items[0]?.href.split("?")[0] ?? "/";
  const portalBreadcrumb = isPlatformAdmin
    ? "Không gian quản trị"
    : isSchoolManager
      ? "Không gian quản lý"
      : "Không gian giáo viên";
  const navStatusAnnouncement = navigation
    .flatMap((group) => group.items)
    .flatMap((item) => {
      const status = navStatus?.[item.href];
      return status ? [item.label + ": " + NAV_STATUS_LABELS[status]] : [];
    })
    .join(". ");

  useEffect(() => {
    const closeAccount = (event: PointerEvent) => {
      if (!topAccountDetails.current?.contains(event.target as Node) && topAccountDetails.current) topAccountDetails.current.open = false;
    };
    document.addEventListener("pointerdown", closeAccount);
    return () => document.removeEventListener("pointerdown", closeAccount);
  }, []);

  useEffect(() => {
    if (menuOpen) firstLink.current?.focus();
  }, [menuOpen]);

  useEffect(() => {
    setMenuOpen(false);
    if (topAccountDetails.current) topAccountDetails.current.open = false;
  }, [location.pathname, location.search]);

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
    <div className={"s2l-app-shell s2l-shell-v9" + (isSchoolManager ? " is-school-manager" : "") + (menuOpen ? " is-menu-open" : "")} onKeyDown={(event) => {
      if (event.key === "Escape" && menuOpen) closeMenu();
      if (event.key === "Escape" && topAccountDetails.current?.open) {
        topAccountDetails.current.open = false;
        topAccountDetails.current.querySelector("summary")?.focus();
      }
    }}>
      <a className="s2l-skip-link" href="#s2l-main">Bỏ qua điều hướng</a>
      <div className="s2l-visually-hidden" role="status" aria-live="polite" aria-atomic="true">{navStatusAnnouncement}</div>
      <aside className="s2l-sidebar" id="s2l-navigation" aria-label={"Cổng " + roleLabel}>
        <div className="s2l-brand-lockup">
          <span className="s2l-brand-logo-chip"><img src={platformAdminLogo} alt="Sketch2Life" /></span>
          <div className="s2l-brand-wordmark"><strong>Sketch2Life</strong><span>{roleLabel}</span></div>
          <button type="button" className="s2l-close-menu" aria-label="Đóng điều hướng" onClick={closeMenu}><X size={19} /></button>
        </div>
        <nav className="s2l-nav" aria-label={"Điều hướng " + roleLabel}>
          {navigation.map((group, groupIndex) => {
            const groupId = `s2l-nav-group-${groupIndex}`;
            const preference = expandedGroups[group.label];
            const defaultOpen = group.label === "Quản lý" || group.label === "Nội dung"
              || (portal === "teacher" && (group.label === "Học liệu" || group.label === "Lên lớp"))
              || activeGroup === group.label;
            const isActiveGroup = activeGroup === group.label;
            const groupHasInbox = group.items.some((item) => item.href === "/teacher/t10-inbox" || item.href === "/school/inbox");
            const isCollapsed = !!group.label && !isActiveGroup && !(preference ?? defaultOpen);
            return (
            <section className={"s2l-nav-group" + (group.label ? " is-collapsible" : "") + (isCollapsed ? " is-collapsed" : "")} key={group.label || groupIndex} aria-label={group.label || undefined}>
              {group.label ? (
                <button
                  className="s2l-nav-group-toggle"
                  type="button"
                  aria-expanded={!isCollapsed}
                  aria-label={isCollapsed && groupHasInbox && unreadLabel ? `${group.label}, ${unreadLabel}` : undefined}
                  aria-controls={groupId}
                  onClick={() => {
                    if (isActiveGroup) return;
                    setExpandedGroups((current) => ({ ...current, [group.label]: isCollapsed }));
                  }}
                >
                  <span>{group.label}</span>
                  {isCollapsed && groupHasInbox && badge}
                  <ChevronDown size={15} strokeWidth={1.8} aria-hidden="true" />
                </button>
              ) : null}
              <div className="s2l-nav-group-items" id={groupId} hidden={isCollapsed}>
              {group.items.map((item, index) => {
                const active = navigationMatches(item.href, location.pathname, location.search, item.matchPrefix);
                const Icon = item.icon;
                const isInbox = item.href === "/teacher/t10-inbox" || item.href === "/school/inbox";
                const hasNavStatus = navStatus !== undefined && Object.prototype.hasOwnProperty.call(navStatus, item.href);
                const taskStatus = navStatus?.[item.href];
                const statusText = taskStatus ? NAV_STATUS_LABELS[taskStatus] : undefined;
                const StatusIcon = taskStatus === "pending" ? LoaderCircle : taskStatus === "done" ? Check : taskStatus === "failed" ? TriangleAlert : null;
                return (
                  <NavLink
                    key={item.href}
                    ref={group === navigation[0] && index === 0 ? firstLink : undefined}
                    to={item.href}
                    className={"s2l-nav-link" + (active ? " is-active" : "") + (hasNavStatus ? " has-ai-status" : "")}
                    aria-current={active ? "page" : false}
                    aria-label={isInbox && unreadLabel ? `${item.label}, ${unreadLabel}` : statusText ? item.label + " " + statusText : undefined}
                    title={statusText}
                    onClick={() => { if (menuOpen) menuButton.current?.focus(); setMenuOpen(false); }}
                  >
                    <Icon size={18} strokeWidth={1.85} aria-hidden="true" />
                    <span>{item.label}</span>
                    {isInbox && badge}
                    {item.state === "waiting" && <span className="s2l-nav-state" title="Đang chờ dịch vụ">Chờ dịch vụ</span>}
                    {statusText && <span className="s2l-visually-hidden"> {statusText}</span>}
                    {hasNavStatus && (
                      <span className={"s2l-nav-ai-status" + (taskStatus ? " is-" + taskStatus : "")} aria-hidden="true">
                        {StatusIcon && <StatusIcon size={18} strokeWidth={2} aria-hidden="true" />}
                      </span>
                    )}
                  </NavLink>
                );
              })}
              </div>
            </section>
          );})}
        </nav>
        <div className="s2l-sidebar-bottom">
          {modeLabel && <div className="s2l-session-status"><span aria-hidden="true" /><div><strong>{modeLabel}</strong></div></div>}
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
            <nav className="s2l-topbar-breadcrumb" aria-label="Đường dẫn trang">
              <Link to={homePath}>{portalBreadcrumb}</Link>
              <ChevronRight size={15} aria-hidden="true" />
              <span aria-current="page">{heading}</span>
            </nav>
          </div>
          <div className="s2l-topbar-tools">
            {isPlatformAdmin ? <details className="s2l-topbar-account" ref={topAccountDetails}>
              <summary aria-label="Mở tài khoản quản trị viên">
                <span className="s2l-account-avatar" aria-hidden="true">PA</span>
                <span className="s2l-topbar-account-name">{accountDisplayName}</span>
                <ChevronDown size={15} aria-hidden="true" />
              </summary>
              <div className="s2l-account-popover s2l-topbar-popover">
                <div className="s2l-topbar-account-info">
                  <strong>{accountDisplayName}</strong>
                  <span>{account.email || "Tài khoản của tôi"}</span>
                  {accountDisplayName !== "Quản trị viên" && <span>Quản trị viên</span>}
                </div>
              </div>
            </details> : isSchoolManager ? (
              <span className="s2l-account-indicator" role="group" aria-label="Vai trò hiện tại: Quản lý trường">
                <span className="s2l-account-avatar" aria-hidden="true">QL</span>
                <span>Quản lý trường</span>
                <ShieldCheck size={16} aria-hidden="true" />
              </span>
            ) : (
              <button type="button" className="s2l-account-button" onClick={() => navigate("/teacher/t11-profile")}>
                <span className="s2l-account-avatar" aria-hidden="true">GV</span>
                <span>{roleLabel}</span><ArrowUpRight size={15} aria-hidden="true" />
              </button>
            )}
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
        showTitle
        showDescription
        titleIcon={<span className="s2l-password-icon"><KeyRound size={19} aria-hidden="true" /></span>}
        className="s2l-password-dialog"
      >
        <form className="s2l-password-form cozy-form-stack" onSubmit={(event) => void changePassword(event)} aria-busy={passwordBusy}>
          <FormField label="Mật khẩu hiện tại" htmlFor="s2l-current-password" required>
            <div className="s2l-password-control">
            <input id="s2l-current-password" className="cozy-input" type={visiblePasswords[0] ? "text" : "password"} autoComplete="current-password" required value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} />
              <button type="button" className="s2l-password-visibility" aria-label={visiblePasswords[0] ? "\u1ea8n m\u1eadt kh\u1ea9u hi\u1ec7n t\u1ea1i" : "Hi\u1ec7n m\u1eadt kh\u1ea9u hi\u1ec7n t\u1ea1i"} aria-pressed={visiblePasswords[0]} aria-controls="s2l-current-password" onClick={() => setVisiblePasswords((values) => values.map((value, index) => index === 0 ? !value : value))}>{visiblePasswords[0] ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}</button>
            </div>
          </FormField>
          <FormField label="Mật khẩu mới" htmlFor="s2l-new-password" required>
            <div className="s2l-password-control">
            <input id="s2l-new-password" className="cozy-input" type={visiblePasswords[1] ? "text" : "password"} autoComplete="new-password" minLength={6} required value={newPassword} onChange={(event) => setNewPassword(event.target.value)} />
              <button type="button" className="s2l-password-visibility" aria-label={visiblePasswords[1] ? "\u1ea8n m\u1eadt kh\u1ea9u m\u1edbi" : "Hi\u1ec7n m\u1eadt kh\u1ea9u m\u1edbi"} aria-pressed={visiblePasswords[1]} aria-controls="s2l-new-password" onClick={() => setVisiblePasswords((values) => values.map((value, index) => index === 1 ? !value : value))}>{visiblePasswords[1] ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}</button>
            </div>
          </FormField>
          <FormField label="Xác nhận mật khẩu mới" htmlFor="s2l-confirm-password" required>
            <div className="s2l-password-control">
            <input id="s2l-confirm-password" className="cozy-input" type={visiblePasswords[2] ? "text" : "password"} autoComplete="new-password" minLength={6} required value={passwordConfirmation} onChange={(event) => setPasswordConfirmation(event.target.value)} />
              <button type="button" className="s2l-password-visibility" aria-label={visiblePasswords[2] ? "\u1ea8n m\u1eadt kh\u1ea9u x\u00e1c nh\u1eadn" : "Hi\u1ec7n m\u1eadt kh\u1ea9u x\u00e1c nh\u1eadn"} aria-pressed={visiblePasswords[2]} aria-controls="s2l-confirm-password" onClick={() => setVisiblePasswords((values) => values.map((value, index) => index === 2 ? !value : value))}>{visiblePasswords[2] ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}</button>
            </div>
          </FormField>
          {passwordMessage && (
            <Alert
              tone={passwordMessage === "Đã đổi mật khẩu." ? "success" : "danger"}
              role={passwordMessage === "Đã đổi mật khẩu." ? "status" : "alert"}
            >
              {passwordMessage}
            </Alert>
          )}
          <div className="cozy-form-actions">
            <Button type="button" variant="secondary" disabled={passwordBusy} onClick={() => setPasswordDialogOpen(false)}>
              Hủy
            </Button>
            <Button type="submit" variant="primary" loading={passwordBusy} disabled={passwordBusy}>
              {passwordBusy ? "Đang lưu…" : "Cập nhật"}
            </Button>
          </div>
        </form>
      </AccessibleDialog>
    </div>
  );
}
