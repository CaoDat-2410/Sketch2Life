import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Logo } from "./Logo";
import { useTeacher } from "../context/TeacherContext";
import { Icon } from "../components/Icon";

const SIDEBAR_ITEMS: {
  to: string;
  label: string;
  icon: Parameters<typeof Icon>[0]["name"];
  matchView: string | null;
}[] = [
  { to: "/t01-lesson-workspace", label: "Tổng quan", icon: "sun", matchView: null },
  { to: "/t05-classes-and-children", label: "Lớp học", icon: "users", matchView: null },
  { to: "/t02-lesson-authoring", label: "Giáo án", icon: "book", matchView: null },
  { to: "/t04-session-sketch-deck", label: "Buổi học", icon: "palette", matchView: null },
  { to: "/t01-lesson-workspace?view=feedback", label: "Phản hồi", icon: "message", matchView: "feedback" },
  { to: "/t01-lesson-workspace?view=settings", label: "Cài đặt", icon: "settings", matchView: "settings" },
];

const QUICK_SCREENS = [
  { id: "T01", to: "/t01-lesson-workspace", label: "T01" },
  { id: "T02", to: "/t02-lesson-authoring", label: "T02" },
  { id: "T03", to: "/t03-document-import-review", label: "T03" },
  { id: "T04", to: "/t04-session-sketch-deck", label: "T04" },
  { id: "T05", to: "/t05-classes-and-children", label: "T05" },
  { id: "T06", to: "/t06-sample-story-run", label: "T06" },
  { id: "T07", to: "/t07-video-presentation-confirmation", label: "T07" },
];

const SCREEN_NAMES: Record<string, string> = {
  "/t01-lesson-workspace": "Tổng quan",
  "/t02-lesson-authoring": "Tạo giáo án",
  "/t03-document-import-review": "Nhập giáo án",
  "/t04-session-sketch-deck": "Chuẩn bị buổi học",
  "/t05-classes-and-children": "Lớp học & Trẻ",
  "/t06-sample-story-run": "Video mẫu",
  "/t07-video-presentation-confirmation": "Trình chiếu lớp",
};

export function TeacherLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { toast, archiveModalTarget, setArchiveModalTarget, archiveLesson } = useTeacher();
  const searchParams = new URLSearchParams(location.search);
  const currentView = searchParams.get("view");
  const currentTitle = SCREEN_NAMES[location.pathname] ?? "Giáo viên";

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
        {/* Logo */}
        <div style={{ padding: "0 8px 18px", borderBottom: "1px solid var(--line)" }}>
          <Logo height={28} />
        </div>

        {/* Nav */}
        <nav className="col" style={{ gap: 4, marginTop: 14, flex: 1 }} aria-label="Điều hướng Giáo viên">
          {SIDEBAR_ITEMS.map((item) => {
            let active = false;
            if (item.matchView) {
              active = location.pathname === "/t01-lesson-workspace" && currentView === item.matchView;
            } else if (item.to === "/t01-lesson-workspace") {
              active = location.pathname === "/t01-lesson-workspace" && !currentView;
            } else if (item.to === "/t02-lesson-authoring") {
              active =
                location.pathname === "/t02-lesson-authoring" ||
                location.pathname === "/t03-document-import-review";
            } else if (item.to === "/t04-session-sketch-deck") {
              active =
                location.pathname === "/t04-session-sketch-deck" ||
                location.pathname === "/t06-sample-story-run" ||
                location.pathname === "/t07-video-presentation-confirmation";
            } else {
              active = location.pathname === item.to;
            }

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
                <Icon
                  name={item.icon}
                  size={18}
                  color={active ? "var(--primary)" : "var(--ink-3)"}
                />
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

        {/* Teacher profile card */}
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
            T
          </div>
          <div style={{ fontWeight: 800, fontSize: 14, color: "var(--ink)" }}>Cô Thảo</div>
          <div className="muted small">Trường Mầm non Ánh Dương</div>
          <div
            className="small"
            style={{ color: "var(--primary)", fontWeight: 700, marginTop: 2 }}
          >
            Lớp Mầm 2
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Top Header */}
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
          {/* Page title */}
          <div style={{ fontWeight: 800, fontSize: 16, color: "var(--ink)", minWidth: 0 }}>
            {currentTitle}
          </div>

          {/* Screen switcher pills */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginLeft: 8 }}>
            {QUICK_SCREENS.map((s) => {
              const active = location.pathname === s.to && !currentView;
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
          <span className="pill ok" style={{ fontSize: 12 }}>
            Ánh Dương · Lớp Mầm 2
          </span>
        </header>

        {/* Toast (UI04) */}
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
                toast.kind === "ok"
                  ? "check"
                  : toast.kind === "warn"
                  ? "alert"
                  : toast.kind === "err"
                  ? "close"
                  : "info"
              }
              size={16}
            />
            {toast.text}
          </div>
        )}

        <main style={{ padding: "24px", maxWidth: 1280, width: "100%" }}>{children}</main>
      </div>

      {/* UI03 Specimen 2: Archive Dialog */}
      {archiveModalTarget && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
        >
          <div className="card col" style={{ width: 460, padding: 24, gap: 16 }}>
            <div className="row" style={{ gap: 10 }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 12,
                  background: "var(--warn-50)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <Icon name="download" size={20} color="var(--warn-700)" />
              </div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 16 }}>Lưu trữ giáo án</div>
                <div className="small muted">
                  {archiveModalTarget.title} · {archiveModalTarget.version}
                </div>
              </div>
            </div>
            <div
              style={{
                padding: "12px 14px",
                borderRadius: 10,
                background: "var(--warn-50)",
                border: "1px solid var(--warn-100)",
                color: "var(--warn-700)",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Sau khi lưu trữ, bài học sẽ không còn hiển thị trong danh sách đang dùng. Bạn vẫn có thể khôi phục từ mục Đã lưu trữ.
            </div>
            <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
              <button
                type="button"
                className="btn ghost"
                onClick={() => setArchiveModalTarget(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className="btn danger-solid"
                onClick={() => archiveLesson(archiveModalTarget.id)}
              >
                <Icon name="download" size={16} color="#FFF" /> Lưu trữ
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
