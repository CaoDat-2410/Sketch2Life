import React, { useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Logo } from "./Logo";
import { useParent } from "../context/ParentContext";

const SCREEN_LINKS = [
  { id: "P01", path: "/p01-lesson-library", label: "P01 · Thư viện" },
  { id: "P02", path: "/p02-lesson-detail", label: "P02 · Chi tiết bài" },
  { id: "P03", path: "/p03-drawing-line-guide", label: "P03 · Bé đang vẽ" },
  { id: "P04", path: "/p04-capture-subject-confirmation", label: "P04 · Chủ thể" },
  { id: "P05", path: "/p05-context-idea-confirmation", label: "P05 · Thông tin & Ý tưởng" },
  { id: "P06", path: "/p06-story-review", label: "P06 · Kịch bản" },
  { id: "P07", path: "/p07-video-job-status", label: "P07 · Tiến trình" },
  { id: "P08", path: "/p08-video-and-activities", label: "P08 · Video & Hoạt động" },
  { id: "P09", path: "/p09-history-feedback", label: "P09 · Lịch sử & Phản hồi" },
  { id: "P10", path: "/p10-child-profiles", label: "P10 · Hồ sơ bé" },
  { id: "P11", path: "/p11-authentication", label: "P11 · Đăng nhập" },
  { id: "P12", path: "/p12-video-quota", label: "P12 · Lượt tạo" },
];

export function MobileLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    profiles,
    selectedProfileId,
    activeSheet,
    setActiveSheet,
    scriptRevision,
    scenes,
    confirmScriptAndStartVideo,
    detectedSubject,
    setDetectedSubject,
    setSubjectConfirmed,
    grants,
    revokeGrant,
    quotaRemaining,
    toast,
    showToast,
  } = useParent();
  const [subjectDraft, setSubjectDraft] = useState(detectedSubject);

  const activeChild =
    profiles.find((p) => p.id === selectedProfileId && !p.archived) ||
    profiles.find((p) => !p.archived) ||
    profiles[0];

  const isAuthScreen = location.pathname === "/p11-authentication";
  const isMainTabScreen =
    location.pathname === "/p01-lesson-library" ||
    location.pathname === "/p09-history-feedback" ||
    location.pathname === "/p10-child-profiles" ||
    location.pathname === "/p12-video-quota";

  const lessonGrants = grants.filter((g) => g.kind === "LESSON");
  const profileGrants = grants.filter((g) => g.kind === "CHILD_PROFILE");

  return (
    <div style={{ minHeight: "100vh", background: "#F1F5F9", padding: "12px 12px 36px" }}>
      {/* Top Quick Navigation & Component Board Bar for Review */}
      <details
        className="card dev-bar"
        style={{
          maxWidth: 420,
          margin: "0 auto 14px",
          padding: "10px 14px",
          background: "#FFFFFF",
        }}
      >
        <summary className="small" style={{ fontWeight: 800, cursor: "pointer" }}>
          Điều hướng nhanh · 12 màn hình &amp; hộp thoại
        </summary>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center", marginTop: 10 }}>
          <span className="small" style={{ fontWeight: 800, color: "#0F172A", marginRight: 4 }}>
            Phụ huynh (P01–P12):
          </span>
          {SCREEN_LINKS.map((s) => {
            const active = location.pathname === s.path;
            return (
              <NavLink
                key={s.id}
                to={s.path}
                style={{
                  padding: "4px 9px",
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 700,
                  background: active ? "var(--primary)" : "var(--primary-50)",
                  color: active ? "#FFFFFF" : "var(--primary)",
                  border: active ? "1px solid var(--primary)" : "1px solid var(--primary-100)",
                }}
              >
                {s.label}
              </NavLink>
            );
          })}
        </div>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
            alignItems: "center",
            paddingTop: 6,
            borderTop: "1px dashed var(--line)",
          }}
        >
          <span className="tiny muted" style={{ fontWeight: 700, marginRight: 4 }}>
            Mẫu hộp thoại (UI02 & UI08):
          </span>
          <button
            type="button"
            className="btn secondary small"
            style={{ padding: "3px 9px", fontSize: 11.5 }}
            onClick={() => setActiveSheet("CONFIRM_SCRIPT")}
          >
            UI02 · Xác nhận kịch bản
          </button>
          <button
            type="button"
            className="btn secondary small"
            style={{ padding: "3px 9px", fontSize: 11.5 }}
            onClick={() => {
              setSubjectDraft(detectedSubject);
              setActiveSheet("EDIT_SUBJECT");
            }}
          >
            UI02 · Chỉnh chủ thể
          </button>
          <button
            type="button"
            className="btn secondary small"
            style={{ padding: "3px 9px", fontSize: 11.5 }}
            onClick={() => setActiveSheet("CANCEL_VIDEO")}
          >
            UI02 · Hủy yêu cầu video
          </button>
          <button
            type="button"
            className="btn secondary small"
            style={{ padding: "3px 9px", fontSize: 11.5 }}
            onClick={() => setActiveSheet("CAMERA_PERMISSION")}
          >
            UI02 · Cho phép máy ảnh
          </button>
          <button
            type="button"
            className="btn secondary small"
            style={{ padding: "3px 9px", fontSize: 11.5 }}
            onClick={() => setActiveSheet("ACCESS_GRANTS")}
          >
            UI08 · Chia sẻ giáo án & hồ sơ trẻ
          </button>
        </div>
      </details>

      {/* Centered Android 9:19 Mobile Frame */}
      <div
        style={{
          maxWidth: 420,
          margin: "0 auto",
          minHeight: 840,
          background: "var(--bg)",
          borderRadius: 40,
          border: "8px solid #0F172A",
          boxShadow: "0 30px 70px rgba(15, 23, 42, 0.28)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Android Status Bar (9:41) */}
        <div
          style={{
            padding: "8px 18px 4px",
            background: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: 12,
            fontWeight: 800,
            color: "#0F172A",
          }}
          aria-hidden="true"
        >
          <span>9:41</span>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <svg width="14" height="12" viewBox="0 0 14 12">
              <rect x="1" y="8" width="2" height="3" rx="0.5" fill="#0F172A" />
              <rect x="4" y="6" width="2" height="5" rx="0.5" fill="#0F172A" />
              <rect x="7" y="4" width="2" height="7" rx="0.5" fill="#0F172A" />
              <rect x="10" y="1" width="2" height="10" rx="0.5" fill="#0F172A" />
            </svg>
            <svg width="14" height="12" viewBox="0 0 16 12">
              <path
                d="M1 4.5C5 1 11 1 15 4.5M3.5 7C6.2 4.6 9.8 4.6 12.5 7M6.5 9.5C7.4 8.7 8.6 8.7 9.5 9.5"
                fill="none"
                stroke="#0F172A"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
            <svg width="18" height="11" viewBox="0 0 20 11">
              <rect
                x="1"
                y="1.5"
                width="15"
                height="8"
                rx="2"
                fill="none"
                stroke="#0F172A"
                strokeWidth="1.4"
              />
              <rect x="3" y="3.2" width="11" height="4.6" rx="1" fill="#0F172A" />
              <rect x="17" y="3.8" width="1.8" height="3.4" rx="0.8" fill="#0F172A" />
            </svg>
          </div>
        </div>

        {/* Top App Bar */}
        {!isAuthScreen && (
          <header
            style={{
              padding: "10px 16px 10px",
              background: "#FFFFFF",
              borderBottom: "1px solid var(--line)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 8,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {!isMainTabScreen && (
                <button
                  type="button"
                  aria-label="Quay lại"
                  onClick={() => navigate("/p01-lesson-library")}
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 8,
                    border: "1px solid var(--line)",
                    background: "#F8FAFC",
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    fontWeight: 800,
                  }}
                >
                  ←
                </button>
              )}
              <Logo height={24} />
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <button
                type="button"
                onClick={() => navigate("/p12-video-quota")}
                className="pill ok"
                style={{ cursor: "pointer", padding: "4px 10px", fontSize: 12.5 }}
                title={`Còn ${quotaRemaining} lượt tạo video`}
                aria-label={`Còn ${quotaRemaining} lượt tạo video`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" />
                </svg>
                {quotaRemaining}
              </button>
              <button
                type="button"
                onClick={() => navigate("/p10-child-profiles")}
                title={`${activeChild.displayName} · ${activeChild.ageLabel}`}
                aria-label={`Hồ sơ ${activeChild.displayName} · ${activeChild.ageLabel}`}
                style={{
                  cursor: "pointer",
                  width: 32,
                  height: 32,
                  borderRadius: 11,
                  border: "none",
                  background: "linear-gradient(135deg, #FDE68A, #FBBF24)",
                  color: "#78350F",
                  fontWeight: 800,
                  fontSize: 14,
                }}
              >
                {activeChild.displayName.replace(/^Bé\s+/, "").charAt(0).toUpperCase()}
              </button>
            </div>
          </header>
        )}

        {/* Toast Banner (UI04) */}
        {toast && (
          <div
            role="status"
            style={{
              margin: "10px 14px 0",
              padding: "10px 12px",
              borderRadius: 10,
              fontSize: 13,
              fontWeight: 600,
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
            <span>
              {toast.kind === "ok"
                ? "✓"
                : toast.kind === "warn"
                ? "!"
                : toast.kind === "err"
                ? "✕"
                : "ℹ"}
            </span>
            <span>{toast.text}</span>
          </div>
        )}

        {/* Main Screen Content */}
        <main style={{ flex: 1, padding: "16px", overflowY: "auto" }}>{children}</main>

        {/* Standardized 3-Tab Bottom Navigation Bar: Bài học / Lịch sử / Hồ sơ (Per P01 & P12 PROMPT.md) */}
        {!isAuthScreen && (
          <nav
            aria-label="Điều hướng chính"
            style={{
              background: "#FFFFFF",
              borderTop: "1px solid var(--line)",
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              padding: "7px 10px 10px",
              gap: 6,
            }}
          >
            {[
              {
                to: "/p01-lesson-library",
                label: "Bài học",
                matchPaths: [
                  "/p01-lesson-library",
                  "/p02-lesson-detail",
                  "/p03-drawing-line-guide",
                  "/p04-capture-subject-confirmation",
                  "/p05-context-idea-confirmation",
                  "/p06-story-review",
                  "/p07-video-job-status",
                  "/p08-video-and-activities",
                  "/p12-video-quota",
                ],
                icon: (active: boolean) => (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5V5.5Z"
                      stroke={active ? "#2563EB" : "#64748B"}
                      strokeWidth="2"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M8 7h8M8 11h6"
                      stroke={active ? "#2563EB" : "#64748B"}
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                ),
              },
              {
                to: "/p09-history-feedback",
                label: "Lịch sử",
                matchPaths: ["/p09-history-feedback"],
                icon: (active: boolean) => (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <circle
                      cx="12"
                      cy="12"
                      r="8.5"
                      stroke={active ? "#2563EB" : "#64748B"}
                      strokeWidth="2"
                    />
                    <path
                      d="M12 7.5V12l3 2"
                      stroke={active ? "#2563EB" : "#64748B"}
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                ),
              },
              {
                to: "/p10-child-profiles",
                label: "Hồ sơ",
                matchPaths: ["/p10-child-profiles"],
                icon: (active: boolean) => (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <circle
                      cx="12"
                      cy="8.5"
                      r="3.5"
                      stroke={active ? "#2563EB" : "#64748B"}
                      strokeWidth="2"
                    />
                    <path
                      d="M5.5 19.5c1.5-3.2 4-4.5 6.5-4.5s5 1.3 6.5 4.5"
                      stroke={active ? "#2563EB" : "#64748B"}
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                ),
              },
            ].map((tab) => {
              const active = tab.matchPaths.includes(location.pathname);
              return (
                <NavLink
                  key={tab.to}
                  to={tab.to}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 3,
                    padding: "5px 4px",
                    borderRadius: 10,
                    fontSize: 12,
                    fontWeight: active ? 800 : 600,
                    color: active ? "var(--primary)" : "var(--ink-2)",
                    background: active ? "var(--primary-50)" : "transparent",
                  }}
                >
                  {tab.icon(active)}
                  <span>{tab.label}</span>
                </NavLink>
              );
            })}
          </nav>
        )}

        {/* UI02 & UI08 Bottom Sheets / Modal Specimens */}
        {activeSheet && (
          <div
            role="dialog"
            aria-modal="true"
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(15, 23, 42, 0.45)",
              display: "flex",
              alignItems: "flex-end",
              zIndex: 30,
            }}
          >
            <div
              style={{
                width: "100%",
                background: "#FFFFFF",
                borderTopLeftRadius: 24,
                borderTopRightRadius: 24,
                padding: "16px 16px 22px",
                boxShadow: "0 -8px 28px rgba(15,23,42,0.18)",
                maxHeight: "86%",
                overflowY: "auto",
              }}
            >
              {/* Grabber Handle */}
              <div
                style={{
                  width: 40,
                  height: 4,
                  borderRadius: 999,
                  background: "#CBD5E1",
                  margin: "0 auto 14px",
                }}
              />

              {/* UI02 Specimen 1: Xác nhận kịch bản */}
              {activeSheet === "CONFIRM_SCRIPT" && (
                <div className="col" style={{ gap: 12 }}>
                  <div className="row" style={{ justifyContent: "space-between" }}>
                    <h2>Xác nhận kịch bản</h2>
                    <span className="pill">
                      Bản {scriptRevision} · {scenes.length} cảnh
                    </span>
                  </div>
                  <div
                    className="card col"
                    style={{
                      padding: 12,
                      background: "var(--primary-50)",
                      borderColor: "var(--primary-100)",
                      gap: 4,
                    }}
                  >
                    <div className="small muted">Bạn đang xác nhận kịch bản sau:</div>
                    <div style={{ fontWeight: 800, fontSize: 15, color: "var(--primary)" }}>
                      Vòng đời bướm · Bản {scriptRevision} · {scenes.length} cảnh
                    </div>
                    <div className="tiny muted">Hồ sơ bé: {activeChild.displayName} · {activeChild.ageLabel}</div>
                  </div>
                  <p className="muted small">
                    Sau khi xác nhận, hệ thống sẽ giữ 1 lượt tạo video trong kỳ và bắt đầu dựng các cảnh từ bức tranh của bé.
                  </p>
                  <div className="col" style={{ gap: 8, marginTop: 4 }}>
                    <button
                      type="button"
                      className="btn block"
                      onClick={() => {
                        confirmScriptAndStartVideo();
                        navigate("/p07-video-job-status");
                      }}
                    >
                      Xác nhận kịch bản
                    </button>
                    <button
                      type="button"
                      className="btn secondary block"
                      onClick={() => setActiveSheet(null)}
                    >
                      Gửi gợi ý viết lại
                    </button>
                  </div>
                </div>
              )}

              {/* UI02 Specimen 2: Chỉnh chủ thể */}
              {activeSheet === "EDIT_SUBJECT" && (
                <div className="col" style={{ gap: 12 }}>
                  <div className="row" style={{ justifyContent: "space-between" }}>
                    <h2>Chỉnh chủ thể</h2>
                    <span className="pill ok">Gợi ý: Con bướm</span>
                  </div>
                  <p className="muted small">
                    Chủ thể sẽ xuất hiện trong video là: <strong>{subjectDraft || "Con bướm"}</strong>
                  </p>
                  <div className="field">
                    <label htmlFor="subject-input">Tên chủ thể bức tranh</label>
                    <input
                      id="subject-input"
                      className="input"
                      value={subjectDraft}
                      onChange={(e) => setSubjectDraft(e.target.value)}
                    />
                  </div>
                  <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                    {["Con bướm", "Chú sâu nhỏ", "Bông hoa vàng"].map((chip) => (
                      <button
                        key={chip}
                        type="button"
                        className="pill"
                        style={{ cursor: "pointer" }}
                        onClick={() => setSubjectDraft(chip)}
                      >
                        {chip}
                      </button>
                    ))}
                  </div>
                  <div className="row" style={{ gap: 10, marginTop: 4 }}>
                    <button
                      type="button"
                      className="btn"
                      style={{ flex: 1 }}
                      onClick={() => {
                        setDetectedSubject(subjectDraft.trim() || "Con bướm");
                        setSubjectConfirmed(true);
                        setActiveSheet(null);
                        showToast("Đã cập nhật chủ thể bức tranh.", "ok");
                      }}
                    >
                      Xác nhận
                    </button>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ flex: 1 }}
                      onClick={() => {
                        setSubjectDraft("Con bướm");
                        setActiveSheet(null);
                      }}
                    >
                      Chọn lại
                    </button>
                  </div>
                </div>
              )}

              {/* UI02 Specimen 3: Hủy yêu cầu tạo video */}
              {activeSheet === "CANCEL_VIDEO" && (
                <div className="col" style={{ gap: 12 }}>
                  <h2>Hủy yêu cầu tạo video</h2>
                  <div
                    style={{
                      padding: 12,
                      borderRadius: 10,
                      background: "var(--danger-50)",
                      border: "1px solid #FECACA",
                      color: "var(--danger)",
                      fontSize: 13.5,
                      fontWeight: 700,
                    }}
                  >
                    Lượt đã được nhận sẽ không được hoàn lại.
                  </div>
                  <p className="muted small">
                    Nếu hủy lúc này, yêu cầu tạo video đang xử lý sẽ dừng lại. Bạn vẫn có thể tiếp tục chờ hệ thống hoàn tất ở chế độ nền.
                  </p>
                  <div className="row" style={{ gap: 10, marginTop: 4 }}>
                    <button
                      type="button"
                      className="btn accent"
                      style={{ flex: 1 }}
                      onClick={() => setActiveSheet(null)}
                    >
                      Tiếp tục chờ
                    </button>
                    <button
                      type="button"
                      className="btn danger"
                      style={{ flex: 1 }}
                      onClick={() => {
                        setActiveSheet(null);
                        showToast("Đã hủy yêu cầu tạo video. Lượt đã nhận vẫn được tính.", "info");
                        navigate("/p01-lesson-library");
                      }}
                    >
                      Hủy yêu cầu
                    </button>
                  </div>
                </div>
              )}

              {/* UI02 Specimen 4: Cho phép máy ảnh */}
              {activeSheet === "CAMERA_PERMISSION" && (
                <div className="col" style={{ gap: 12 }}>
                  <h2>Cho phép máy ảnh</h2>
                  <p className="muted small">
                    Cho phép ứng dụng truy cập máy ảnh để chụp bức tranh giấy của bé, hoặc chọn ảnh có sẵn từ thư viện.
                  </p>
                  <div className="col" style={{ gap: 8, marginTop: 4 }}>
                    <button
                      type="button"
                      className="btn block"
                      onClick={() => {
                        setActiveSheet(null);
                        navigate("/p04-capture-subject-confirmation");
                      }}
                    >
                      Cho phép máy ảnh
                    </button>
                    <button
                      type="button"
                      className="btn secondary block"
                      onClick={() => {
                        setActiveSheet(null);
                        navigate("/p04-capture-subject-confirmation");
                      }}
                    >
                      Chọn ảnh từ thư viện
                    </button>
                  </div>
                </div>
              )}

              {/* UI08 Specimen: Separate Lesson Grants & Child-Profile Grants */}
              {activeSheet === "ACCESS_GRANTS" && (
                <div className="col" style={{ gap: 14 }}>
                  <div className="row" style={{ justifyContent: "space-between" }}>
                    <h2>Chia sẻ giáo án & hồ sơ trẻ (UI08)</h2>
                    <button
                      type="button"
                      className="btn ghost small"
                      onClick={() => setActiveSheet(null)}
                    >
                      Đóng
                    </button>
                  </div>
                  <p className="muted small">
                    Quyền chia sẻ giáo án và quyền chia sẻ hồ sơ trẻ tách biệt nhau. Chỉ bản ghi <strong>Đang hiệu lực</strong> mới có nút thu hồi.
                  </p>

                  {/* Section 1: Chia sẻ giáo án */}
                  <div className="col" style={{ gap: 8 }}>
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <h3>1. Chia sẻ giáo án</h3>
                      <span className="pill">{lessonGrants.length} bản ghi</span>
                    </div>
                    {lessonGrants.map((g) => (
                      <div key={g.id} className="card col" style={{ padding: 12, gap: 6 }}>
                        <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div>
                            <div style={{ fontWeight: 700, fontSize: 13.5 }}>{g.recipient}</div>
                            <div className="small muted">{g.scope}</div>
                            <div className="tiny muted">Hết hạn: {g.expiresAt}</div>
                          </div>
                          <span
                            className={`pill ${
                              g.status === "Đang hiệu lực"
                                ? "ok"
                                : g.status === "Đang chờ"
                                ? "warn"
                                : "off"
                            }`}
                          >
                            {g.status}
                          </span>
                        </div>
                        {g.status === "Đang hiệu lực" && (
                          <div style={{ display: "flex", justifyContent: "flex-end" }}>
                            <button
                              type="button"
                              className="btn danger small"
                              onClick={() => revokeGrant(g.id)}
                            >
                              Thu hồi
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Section 2: Chia sẻ hồ sơ trẻ */}
                  <div className="col" style={{ gap: 8 }}>
                    <div className="row" style={{ justifyContent: "space-between" }}>
                      <h3>2. Chia sẻ hồ sơ trẻ</h3>
                      <span className="pill">{profileGrants.length} bản ghi</span>
                    </div>
                    {profileGrants.map((g) => (
                      <div key={g.id} className="card col" style={{ padding: 12, gap: 6 }}>
                        <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div>
                            <div style={{ fontWeight: 700, fontSize: 13.5 }}>{g.recipient}</div>
                            <div className="small muted">{g.scope}</div>
                            <div className="tiny muted">Hết hạn: {g.expiresAt}</div>
                          </div>
                          <span
                            className={`pill ${
                              g.status === "Đang hiệu lực"
                                ? "ok"
                                : g.status === "Đang chờ"
                                ? "warn"
                                : "off"
                            }`}
                          >
                            {g.status}
                          </span>
                        </div>
                        {g.status === "Đang hiệu lực" && (
                          <div style={{ display: "flex", justifyContent: "flex-end" }}>
                            <button
                              type="button"
                              className="btn danger small"
                              onClick={() => revokeGrant(g.id)}
                            >
                              Thu hồi
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
