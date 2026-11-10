import React, { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Logo } from "./Logo";
import { useTeacher } from "../context/TeacherContext";
import { Icon, IconName } from "./Icon";
import { RoleHelp } from "../../../shared/RoleHelp";
import { BackendModeNotice, isLocalPreview } from "../../../shared/backendApi";
import { AccessibleDialog } from "../../../shared/ui";

type NavItem = { to: string; label: string; icon: IconName; matchView?: string | null };

const TEACHER_TOP_NAV: NavItem[] = [
  { to: "/t01-lesson-workspace", label: "Tổng quan", icon: "home", matchView: null },
  { to: "/t05-classes-and-children", label: "Lớp & Học sinh", icon: "users", matchView: null },
];

const TEACHER_TEACHING_GROUP: NavItem[] = [
  { to: "/t02-lesson-authoring", label: "Quản lý giáo án", icon: "book" },
  { to: "/t04-session-sketch-deck", label: "AI Assisted", icon: "palette" },
  { to: "/t06-sample-story-run", label: "Tạo video mẫu", icon: "video" },
  { to: "/t07-video-presentation-confirmation", label: "Chiếu trên lớp", icon: "play" },
];

const TEACHER_BOTTOM_NAV: NavItem[] = [
  { to: "/t01-lesson-workspace?view=library", label: "Thư viện công khai", icon: "star", matchView: "library" },
  { to: "/t01-lesson-workspace?view=history", label: "Lịch sử & Báo cáo", icon: "clock", matchView: "history" },
  { to: "/t01-lesson-workspace?view=settings", label: "Hồ sơ cá nhân", icon: "user", matchView: "settings" },
  { to: "/t08-settings", label: "Cài đặt", icon: "settings", matchView: null },
];

const MANAGER_NAV_ITEMS: { to: string; label: string; icon: IconName; matchSection?: string }[] = [
  { to: "/m02-organization-management", label: "Tổng quan", icon: "home" },
  { to: "/m02-organization-management?section=teachers", label: "Giáo viên & nhóm", icon: "users", matchSection: "teachers" },
  { to: "/m02-organization-management?section=classes", label: "Lớp & slot", icon: "book", matchSection: "classes" },
  { to: "/m02-organization-management?section=quota", label: "Quota", icon: "video", matchSection: "quota" },
  { to: "/m01-publication-review", label: "Duyệt công khai", icon: "check" },
  { to: "/m02-organization-management?section=settings", label: "Cài đặt", icon: "settings", matchSection: "settings" },
];

const ADMIN_NAV_ITEMS: { to: string; label: string; icon: IconName; matchPanel?: string }[] = [
  { to: "/a02-platform-operations", label: "Tổng quan", icon: "home" },
  { to: "/a02-platform-operations?panel=orgs", label: "Tổ chức", icon: "users", matchPanel: "orgs" },
  { to: "/a01-content-moderation", label: "Thư viện bài học", icon: "book" },
  { to: "/a02-platform-operations?panel=catalog", label: "Danh mục hoạt động", icon: "leaf", matchPanel: "catalog" },
  { to: "/a02-platform-operations?panel=quota", label: "Quota & chính sách", icon: "lock", matchPanel: "quota" },
  { to: "/a02-platform-operations?panel=audit", label: "Nhật ký", icon: "clock", matchPanel: "audit" },
];

const SCREEN_NAMES: Record<string, string> = {
  "/t01-lesson-workspace": "Tổng quan",
  "/t02-lesson-authoring": "Quản lý giáo án",
  "/t03-document-import-review": "Nhập tài liệu giáo án",
  "/t04-session-sketch-deck": "AI Assisted · Bảng vẽ lớp học",
  "/t05-classes-and-children": "Lớp & Học sinh",
  "/t06-sample-story-run": "Tạo video mẫu",
  "/t07-video-presentation-confirmation": "Chiếu trên lớp",
  "/t08-settings": "Cài đặt",
  "/m01-publication-review": "Duyệt giáo án công khai",
  "/m02-organization-management": "Quản lý trường học",
  "/a01-content-moderation": "Kiểm duyệt nội dung",
  "/a02-platform-operations": "Vận hành nền tảng",
};

const TEACHING_GROUP_PATHS = new Set([
  "/t02-lesson-authoring",
  "/t03-document-import-review",
  "/t04-session-sketch-deck",
  "/t06-sample-story-run",
  "/t07-video-presentation-confirmation",
]);

export function TeacherLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    currentRole,
    isAuthenticated,
    logout,
    assignedClasses,
    activeClassId,
    setActiveClassId,
    orgIncludedQuota,
    orgTopupQuota,
    teacherNotifications,
    toast,
    archiveModalTarget,
    setArchiveModalTarget,
    deleteLesson,
    showToast,
  } = useTeacher();

  const [teachingOpen, setTeachingOpen] = useState(true);
  const previewMode = isLocalPreview();

  const isInTeachingGroup = TEACHING_GROUP_PATHS.has(location.pathname);

  useEffect(() => {
    if (isInTeachingGroup) {
      setTeachingOpen(true);
    }
  }, [isInTeachingGroup]);

  if (location.pathname === "/login" || !isAuthenticated) {
    return <main>{children}</main>;
  }

  const activeRole = currentRole;

  const searchParams = new URLSearchParams(location.search);
  const currentView = searchParams.get("view");
  const currentSection = searchParams.get("section");
  const currentPanel = searchParams.get("panel");

  let currentTitle = SCREEN_NAMES[location.pathname] ?? "Sketch2Life";
  if (location.pathname.startsWith("/t05-classes-and-children/")) {
    const classIdParam = location.pathname.replace("/t05-classes-and-children/", "");
    const foundCls = assignedClasses.find((c) => c.id === classIdParam);
    currentTitle = foundCls ? `${foundCls.className} · Danh sách học sinh` : "Chi tiết lớp học";
  } else if (location.pathname === "/t01-lesson-workspace") {
    if (currentView === "library") currentTitle = "Thư viện công khai";
    else if (currentView === "history") currentTitle = "Lịch sử & Báo cáo";
    else if (currentView === "settings") currentTitle = "Hồ sơ cá nhân";
    else if (currentView === "feedback") currentTitle = "Thông báo hệ thống";
  }

  const unreadCount = teacherNotifications.filter((n) => n.unread).length;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isTeacherItemActive = (item: NavItem): boolean => {
    if (item.matchView) {
      return location.pathname === "/t01-lesson-workspace" && currentView === item.matchView;
    }
    if (item.to === "/t01-lesson-workspace") {
      return location.pathname === "/t01-lesson-workspace" && !currentView;
    }
    if (item.to === "/t05-classes-and-children") {
      return (
        location.pathname === "/t05-classes-and-children" ||
        location.pathname.startsWith("/t05-classes-and-children/")
      );
    }
    if (item.to === "/t02-lesson-authoring") {
      return (
        location.pathname === "/t02-lesson-authoring" ||
        location.pathname === "/t03-document-import-review"
      );
    }
    return location.pathname === item.to;
  };

  const navLink = (key: string, to: string, label: string, icon: IconName, active: boolean) => (
    <NavLink key={key} to={to} aria-label={label} className={"tw-nav-item" + (active ? " is-on" : "")}>
      <span className="mg-nav-ico" aria-hidden="true"><Icon name={icon} size={19} /></span>
      <span className="tw-lbl">{label}</span>
    </NavLink>
  );

  const roleName = previewMode
    ? activeRole === "TEACHER" ? "Cô Thảo" : activeRole === "MANAGER" ? "Hiệu trưởng Minh" : "Quản trị viên"
    : "Tài khoản đã xác thực";
  const roleLabel = activeRole === "TEACHER" ? "Giáo viên" : activeRole === "MANAGER" ? "Quản lý trường" : "Quản trị nền tảng";
  const roleIcon: IconName = activeRole === "TEACHER" ? "palette" : activeRole === "MANAGER" ? "users" : "lock";
  const roleTone = activeRole === "TEACHER" ? "is-sky" : activeRole === "MANAGER" ? "is-mint" : "is-amber";

  return (
    <div className="tw-shell">
      <aside className="tw-side">
        <div className="s2l-side-brand">
          <Logo height={30} />
          <span className="s2l-role-chip">
            <span aria-hidden="true"><Icon name={roleIcon} size={14} /></span>
            {roleLabel}
          </span>
        </div>

        <nav className="tw-nav" aria-label="Điều hướng cổng web">
          {activeRole === "TEACHER" && (
            <>
              {TEACHER_TOP_NAV.map((item) =>
                navLink(item.label, item.to, item.label, item.icon, isTeacherItemActive(item))
              )}

              <div className="tw-nav-group">
                <button
                  type="button"
                  className={"tw-nav-group-btn" + (isInTeachingGroup ? " has-active" : "")}
                  aria-label="Bài giảng trên lớp"
                  aria-expanded={teachingOpen}
                  onClick={() => setTeachingOpen((open) => !open)}
                >
                  <span className="tw-row" style={{ gap: 10 }}>
                    <span className="mg-nav-ico" aria-hidden="true"><Icon name="sparkle" size={18} /></span>
                    <span className="tw-lbl">Bài giảng trên lớp</span>
                  </span>
                  <span className={"tw-nav-group-chev" + (teachingOpen ? " is-open" : "")}>
                    <Icon name="chevron-down" size={16} />
                  </span>
                </button>

                {teachingOpen && (
                  <div className="tw-nav-group-list">
              {(previewMode ? TEACHER_TEACHING_GROUP : TEACHER_TEACHING_GROUP.filter((item) => item.to === "/t02-lesson-authoring" || item.to === "/t03-document-import-review")).map((item) =>
                navLink(item.label, item.to, item.label, item.icon, isTeacherItemActive(item))
              )}
                  </div>
                )}
              </div>

              <div className="tw-nav-divider" role="separator" />

              {previewMode && TEACHER_BOTTOM_NAV.map((item) =>
                navLink(item.label, item.to, item.label, item.icon, isTeacherItemActive(item))
              )}
            </>
          )}

          {activeRole === "MANAGER" &&
            MANAGER_NAV_ITEMS.map((item) => {
              const active =
                item.to === "/m01-publication-review"
                  ? location.pathname === "/m01-publication-review"
                  : location.pathname === "/m02-organization-management" &&
                    (item.matchSection ? currentSection === item.matchSection : !currentSection);
              return navLink(item.label, item.to, item.label, item.icon, active);
            })}

          {activeRole === "ADMIN" &&
            ADMIN_NAV_ITEMS.map((item) => {
              const active =
                item.to === "/a01-content-moderation"
                  ? location.pathname === "/a01-content-moderation"
                  : location.pathname === "/a02-platform-operations" &&
                    (item.matchPanel ? currentPanel === item.matchPanel : !currentPanel);
              return navLink(item.label, item.to, item.label, item.icon, active);
            })}
        </nav>

        <div className="tw-item tw-row" style={{ padding: 10, borderRadius: 18, gap: 10, marginTop: 8 }}>
          <span className={`tw-avatar is-sm ${roleTone}`} aria-hidden="true">
            <Icon name={roleIcon} size={18} />
          </span>
          <div className="tw-lbl" style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{roleName}</div>
            <div className="tw-meta" style={{ fontSize: 12 }} title={previewMode ? "Dữ liệu minh họa, không lưu vào backend." : undefined}>{previewMode && activeRole === "TEACHER" ? "Xem thử · không lưu" : previewMode ? "Trường Ánh Dương · dữ liệu mẫu" : "Quyền theo phiên backend"}</div>
          </div>
        </div>
        <button
          type="button"
          className="tw-side-logout"
          onClick={handleLogout}
          aria-label="Đăng xuất khỏi cổng Giáo viên"
          title="Đăng xuất khỏi cổng Giáo viên"
        >
          <span aria-hidden="true"><Icon name="log-out" size={18} /></span>
          <span className="tw-side-logout-label">Đăng xuất</span>
        </button>
      </aside>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header className="tw-top">
          <div className="tw-row">
            <div className="tw-top-title">{currentTitle}</div>
          </div>

          <div className="tw-row" style={{ gap: 10 }}>
            <RoleHelp role="TEACHER" />
            {activeRole === "TEACHER" && previewMode && (
              <select
                aria-label="Chọn lớp phụ trách"
                className="tw-input"
                style={{ width: 148, padding: "7px 12px", fontSize: 13.5, fontWeight: 600, borderRadius: 9999 }}
                value={activeClassId}
                onChange={(e) => {
                  const nextId = e.target.value;
                  setActiveClassId(nextId);
                  const found = assignedClasses.find((c) => c.id === nextId);
                  if (found) {
                    showToast(
                      `Đã chuyển sang ${found.className}.`,
                      found.rbacState === "UNASSIGNED_403" ? "err" : "info"
                    );
                  }
                  if (location.pathname.startsWith("/t05-classes-and-children/")) {
                    navigate(`/t05-classes-and-children/${nextId}`);
                  }
                }}
              >
                {assignedClasses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.className}
                  </option>
                ))}
              </select>
            )}

            {activeRole !== "ADMIN" && previewMode && (
              <button
                type="button"
                className="tw-chip is-amber"
                style={{ cursor: "pointer", fontFamily: "inherit" }}
                title="Lượt tạo video còn lại"
                onClick={() => {
                  if (activeRole === "TEACHER") navigate("/t07-video-presentation-confirmation");
                  else navigate("/m02-organization-management?section=quota");
                }}
              >
                <Icon name="sparkle" size={14} /> {orgIncludedQuota + orgTopupQuota} lượt
              </button>
            )}

            {activeRole === "TEACHER" && previewMode && (
              <button
                type="button"
                aria-label={`Thông báo hệ thống (${unreadCount} chưa đọc)`}
                className="tw-ico"
                style={{ width: 40, height: 40, border: 0, cursor: "pointer", position: "relative", borderRadius: 14 }}
                onClick={() => navigate("/t01-lesson-workspace?view=feedback")}
              >
                <Icon name="message" size={18} />
                {unreadCount > 0 && (
                  <span
                    style={{
                      position: "absolute",
                      top: -3,
                      right: -3,
                      minWidth: 18,
                      height: 18,
                      padding: "0 4px",
                      borderRadius: 9,
                      background: "#DC2626",
                      color: "#FFFFFF",
                      fontSize: 11,
                      fontWeight: 700,
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {unreadCount}
                  </span>
                )}
              </button>
            )}


          </div>
        </header>

        {toast && (
          <div
            role="status"
            aria-live="polite"
            className={`tw-row tw-toast is-${toast.kind}`}
          >
            <Icon
              name={
                toast.kind === "ok"
                  ? "check"
                  : toast.kind === "warn"
                  ? "alert"
                  : toast.kind === "err"
                  ? "close"
                  : "info"
              }
              size={18}
            />
            <span>{toast.text}</span>
          </div>
        )}

        <main className="tw-main">{previewMode && activeRole !== "TEACHER" && <BackendModeNotice roleLabel="Giáo viên" />}{children}</main>
      </div>

      <AccessibleDialog
        open={Boolean(archiveModalTarget)}
        onOpenChange={(open) => !open && setArchiveModalTarget(null)}
        title="Xóa & lưu trữ giáo án?"
        description="Xác nhận chuyển giáo án khỏi danh sách đang hoạt động vào kho lưu trữ."
        className="tw-modal"
        showClose={false}
      >
        {archiveModalTarget && (
          <>
            <div className="tw-row">
              <span className="tw-ico is-rose" aria-hidden="true">
                <Icon name="trash" size={22} />
              </span>
              <h2 style={{ margin: 0, fontSize: 19, fontWeight: 650 }}>
                Xóa & lưu trữ giáo án?
              </h2>
            </div>
            <p className="tw-sub">
              Giáo án <strong>“{archiveModalTarget.title}”</strong> ({archiveModalTarget.version}) sẽ được xóa khỏi danh sách đang hoạt động và chuyển vào kho lưu trữ. Các buổi học đã lên lịch trước đó vẫn giữ nguyên bản chụp hiện tại.
            </p>
            <div className="tw-row" style={{ justifyContent: "flex-end", gap: 10 }}>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setArchiveModalTarget(null)}
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                className="tw-btn is-danger is-sm"
                onClick={() => {
                  deleteLesson(archiveModalTarget.id);
                }}
              >
                <Icon name="trash" size={16} /> Xác nhận xóa
              </button>
            </div>
          </>
        )}
      </AccessibleDialog>
    </div>
  );
}
