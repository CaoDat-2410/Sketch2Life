import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Ui05LibraryState, useParent } from "../context/ParentContext";
import { UI07_VIDEO_JOBS } from "../data/mockParentData";
import { Logo } from "../components/Logo";
import { Icon, IconBadge } from "../components/Icon";
import type { IconName } from "../components/Icon";

const COVER_BG: Record<"butterfly" | "tree", string> = {
  butterfly: "linear-gradient(135deg, #DBEAFE 0%, #FEF3C7 100%)",
  tree: "linear-gradient(135deg, #D1FAE5 0%, #DBEAFE 100%)",
};

function Cover({ kind }: { kind: "butterfly" | "tree" }) {
  return (
    <div
      aria-hidden="true"
      style={{
        height: 128,
        background: COVER_BG[kind],
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <span style={{ position: "absolute", top: -26, right: -20, width: 90, height: 90, borderRadius: "50%", background: "rgba(255,255,255,0.45)" }} />
      <span style={{ position: "absolute", bottom: -34, left: -14, width: 80, height: 80, borderRadius: "50%", background: "rgba(255,255,255,0.35)" }} />
      {kind === "butterfly" ? (
        <svg width="92" height="92" viewBox="0 0 48 48" style={{ position: "relative" }}>
          <path d="M22 18 C9 6, 6 28, 22 26" fill="#93C5FD" stroke="#2563EB" strokeWidth="2" />
          <path d="M26 18 C39 6, 42 28, 26 26" fill="#FDE68A" stroke="#D97706" strokeWidth="2" />
          <path d="M22 26 C11 29, 13 42, 23 35" fill="#A7F3D0" stroke="#059669" strokeWidth="2" />
          <path d="M26 26 C37 29, 35 42, 25 35" fill="#FDE68A" stroke="#D97706" strokeWidth="2" />
          <ellipse cx="24" cy="26" rx="2.6" ry="11" fill="#0F172A" />
          <path d="M23 15 Q19 9 15 11 M25 15 Q29 9 33 11" fill="none" stroke="#0F172A" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      ) : (
        <svg width="92" height="92" viewBox="0 0 48 48" style={{ position: "relative" }}>
          <rect x="21" y="27" width="6" height="14" rx="2" fill="#B45309" />
          <circle cx="24" cy="19" r="11" fill="#34D399" stroke="#047857" strokeWidth="2" />
          <circle cx="17" cy="23" r="7" fill="#6EE7B7" stroke="#047857" strokeWidth="1.8" />
          <circle cx="31" cy="23" r="7" fill="#6EE7B7" stroke="#047857" strokeWidth="1.8" />
        </svg>
      )}
    </div>
  );
}

const STATE_OPTIONS: { id: Ui05LibraryState; label: string; icon: IconName }[] = [
  { id: "NORMAL", label: "Mặc định", icon: "book" },
  { id: "LOADING", label: "Đang tải", icon: "clock" },
  { id: "EMPTY", label: "Trống", icon: "image" },
  { id: "STALE_409", label: "409", icon: "refresh" },
  { id: "FORBIDDEN_403", label: "403", icon: "lock" },
];

function StateCard({
  icon,
  tone,
  title,
  note,
  action,
}: {
  icon: IconName;
  tone: "primary" | "accent" | "mint" | "danger" | "neutral";
  title: string;
  note: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card col" style={{ alignItems: "center", textAlign: "center", padding: 28, gap: 10 }}>
      <IconBadge name={icon} tone={tone} size={64} />
      <h3>{title}</h3>
      <p className="muted small">{note}</p>
      {action}
    </div>
  );
}

/* P01 — Lesson Library (p01-lesson-library + UI05 States) */
export function P01LessonLibraryPage() {
  const navigate = useNavigate();
  const {
    profiles,
    selectedProfileId,
    setSelectedProfileId,
    lessons,
    setSelectedLessonId,
    libraryState,
    setLibraryState,
    quotaRemaining,
    hasActiveRun,
    setActiveSheet,
    showToast,
  } = useParent();
  const [search, setSearch] = useState("");
  const [age, setAge] = useState("Tất cả");

  const activeProfiles = profiles.filter((p) => !p.archived);
  const activeChild = activeProfiles.find((p) => p.id === selectedProfileId) || activeProfiles[0];
  const initial = activeChild ? activeChild.displayName.replace(/^Bé\s+/, "").charAt(0).toUpperCase() : "B";
  const ageBands = ["Tất cả", ...Array.from(new Set(lessons.map((l) => l.ageBand)))];

  const filteredLessons = lessons.filter(
    (l) =>
      l.title.toLowerCase().includes(search.trim().toLowerCase()) &&
      (age === "Tất cả" || l.ageBand === age)
  );

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* Greeting row */}
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <div
            style={{
              width: 46,
              height: 46,
              borderRadius: 16,
              background: "linear-gradient(135deg, #FDE68A, #FBBF24)",
              color: "#78350F",
              fontWeight: 800,
              fontSize: 20,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 10px rgba(251,191,36,0.4)",
            }}
          >
            {initial}
          </div>
          <div className="col" style={{ gap: 0 }}>
            <span className="tiny muted">Xin chào</span>
            <label style={{ position: "relative", display: "inline-flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
              <span style={{ fontWeight: 800, fontSize: 17 }}>
                {activeChild ? `${activeChild.displayName} · ${activeChild.ageLabel}` : "Chọn hồ sơ"}
              </span>
              <Icon name="chevron-down" size={16} color="#64748B" />
              <select
                aria-label="Chọn hồ sơ bé"
                value={selectedProfileId}
                onChange={(e) => setSelectedProfileId(e.target.value)}
                style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer", width: "100%" }}
              >
                {activeProfiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.displayName} · {p.ageLabel}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button
            type="button"
            aria-label="Quyền chia sẻ"
            title="Quyền chia sẻ"
            className="icon-btn"
            onClick={() => setActiveSheet("ACCESS_GRANTS")}
          >
            <Icon name="users" size={20} />
          </button>
        </div>
      </div>

      {/* Hero: quota + resume */}
      <div
        style={{
          borderRadius: 24,
          padding: 18,
          color: "#FFFFFF",
          background: "linear-gradient(135deg, #3B82F6 0%, #2563EB 55%, #1E40AF 100%)",
          position: "relative",
          overflow: "hidden",
          boxShadow: "0 12px 28px rgba(37,99,235,0.3)",
        }}
      >
        <span style={{ position: "absolute", right: -30, top: -30, width: 130, height: 130, borderRadius: "50%", background: "rgba(255,255,255,0.12)" }} />
        <span style={{ position: "absolute", right: 36, bottom: -44, width: 90, height: 90, borderRadius: "50%", background: "rgba(251,191,36,0.35)" }} />
        <div className="row" style={{ justifyContent: "space-between", position: "relative" }}>
          <div className="col" style={{ gap: 4 }}>
            <span style={{ fontSize: 20, fontWeight: 800, lineHeight: 1.2 }}>Vẽ một nét,<br />hiện một câu chuyện</span>
          </div>
          <button
            type="button"
            onClick={() => navigate("/p12-video-quota")}
            style={{
              border: "none",
              cursor: "pointer",
              background: "rgba(255,255,255,0.2)",
              color: "#FFFFFF",
              borderRadius: 999,
              padding: "6px 12px",
              fontWeight: 800,
              fontSize: 13,
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              backdropFilter: "blur(4px)",
            }}
            title="Xem lượt tạo video"
          >
            <Icon name="sparkle" size={15} color="#FDE68A" />
            {quotaRemaining}
          </button>
        </div>

        {hasActiveRun && libraryState === "NORMAL" && (
          <button
            type="button"
            onClick={() => navigate("/p06-story-review")}
            style={{
              position: "relative",
              marginTop: 14,
              width: "100%",
              border: "none",
              cursor: "pointer",
              background: "#FFFFFF",
              color: "#0F172A",
              borderRadius: 16,
              padding: "10px 12px",
              display: "flex",
              alignItems: "center",
              gap: 10,
              textAlign: "left",
            }}
          >
            <IconBadge name="video" tone="accent" size={38} />
            <span style={{ flex: 1 }}>
              <span style={{ display: "block", fontWeight: 800, fontSize: 14 }}>Vòng đời bướm</span>
              <span style={{ display: "block", height: 6, borderRadius: 999, background: "#E2E8F0", marginTop: 6, overflow: "hidden" }}>
                <span style={{ display: "block", width: "68%", height: "100%", background: "var(--primary)", borderRadius: 999 }} />
              </span>
            </span>
            <span style={{ color: "var(--primary)", fontWeight: 800, fontSize: 13, display: "inline-flex", alignItems: "center", gap: 4 }}>
              Tiếp tục <Icon name="arrow-right" size={15} />
            </span>
          </button>
        )}
      </div>

      {/* Search + age chips */}
      <div className="col" style={{ gap: 10 }}>
        <div style={{ position: "relative" }}>
          <span style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "#94A3B8", display: "flex" }}>
            <Icon name="search" size={18} />
          </span>
          <input
            id="lesson-search"
            aria-label="Tìm bài học"
            className="input"
            style={{ paddingLeft: 42, borderRadius: 999 }}
            placeholder="Tìm bài học"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          {ageBands.map((b) => (
            <button
              key={b}
              type="button"
              className={`chip${age === b ? " on" : ""}`}
              onClick={() => setAge(b)}
            >
              {b}
            </button>
          ))}
        </div>
      </div>

      {/* UI05 state switcher (review aid, collapsed) */}
      <details className="card" style={{ padding: "8px 12px", background: "#F8FAFC", boxShadow: "none" }}>
        <summary className="tiny muted" style={{ fontWeight: 700, cursor: "pointer" }}>
          Xem các trạng thái (UI05)
        </summary>
        <div className="row" style={{ gap: 6, flexWrap: "wrap", marginTop: 8 }}>
          {STATE_OPTIONS.map((o) => (
            <button
              key={o.id}
              type="button"
              className={`chip${libraryState === o.id ? " on" : ""}`}
              onClick={() => setLibraryState(o.id)}
            >
              <Icon name={o.icon} size={14} /> {o.label}
            </button>
          ))}
        </div>
      </details>

      {libraryState === "LOADING" && (
        <div className="col" style={{ gap: 12 }}>
          {[1, 2].map((n) => (
            <div key={n} className="card" style={{ padding: 0, overflow: "hidden" }}>
              <div className="skeleton" style={{ height: 128 }} />
              <div className="col" style={{ padding: 14, gap: 8 }}>
                <div className="skeleton" style={{ height: 16, width: "60%", borderRadius: 8 }} />
                <div className="skeleton" style={{ height: 12, width: "35%", borderRadius: 8 }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {libraryState === "EMPTY" && (
        <StateCard
          icon="image"
          tone="primary"
          title="Chưa có bài học"
          note="Giáo viên sẽ chia sẻ bài học cho bé sớm thôi."
          action={
            <button type="button" className="btn secondary small" onClick={() => setLibraryState("NORMAL")}>
              <Icon name="refresh" size={15} /> Tải lại
            </button>
          }
        />
      )}

      {libraryState === "STALE_409" && (
        <StateCard
          icon="refresh"
          tone="accent"
          title="Bài học vừa được cập nhật"
          note="Làm mới để xem bản mới nhất."
          action={
            <button
              type="button"
              className="btn accent small"
              onClick={() => {
                setLibraryState("NORMAL");
                showToast("Đã làm mới phiên bản bài học mới nhất.", "ok");
              }}
            >
              <Icon name="refresh" size={15} /> Làm mới
            </button>
          }
        />
      )}

      {libraryState === "FORBIDDEN_403" && (
        <StateCard
          icon="lock"
          tone="danger"
          title="Chưa có quyền xem"
          note="Hãy liên hệ giáo viên để được cấp quyền."
          action={
            <button type="button" className="btn secondary small" onClick={() => setLibraryState("NORMAL")}>
              <Icon name="arrow-left" size={15} /> Quay lại
            </button>
          }
        />
      )}

      {libraryState === "NORMAL" &&
        (filteredLessons.length === 0 ? (
          <StateCard
            icon="search"
            tone="neutral"
            title="Không tìm thấy bài học"
            note="Thử từ khóa khác nhé."
            action={
              <button
                type="button"
                className="btn secondary small"
                onClick={() => {
                  setSearch("");
                  setAge("Tất cả");
                }}
              >
                Xem tất cả
              </button>
            }
          />
        ) : (
          <div className="col" style={{ gap: 14 }}>
            {filteredLessons.map((lesson) => (
              <button
                key={lesson.id}
                type="button"
                className="card lesson-card"
                onClick={() => {
                  setSelectedLessonId(lesson.id);
                  navigate("/p02-lesson-detail");
                }}
                style={{ padding: 0, overflow: "hidden", textAlign: "left", cursor: "pointer", width: "100%" }}
              >
                <div style={{ position: "relative" }}>
                  <Cover kind={lesson.coverKind} />
                  <span
                    className="pill"
                    style={{ position: "absolute", top: 10, left: 10, background: "rgba(255,255,255,0.92)" }}
                  >
                    <Icon name="user" size={13} /> {lesson.ageBand}
                  </span>
                </div>
                <div className="row" style={{ padding: "14px 16px", justifyContent: "space-between" }}>
                  <div className="col" style={{ gap: 8, minWidth: 0 }}>
                    <h2>{lesson.title}</h2>
                    <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                      {lesson.tags.slice(0, 2).map((tag, i) => (
                        <span key={tag} className={`pill ${i === 0 ? "ok" : "warn"}`} style={{ fontSize: 11.5 }}>
                          <Icon name={i === 0 ? "leaf" : "sparkle"} size={12} /> {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className="go-btn">
                    <Icon name="arrow-right" size={20} color="#FFFFFF" />
                  </span>
                </div>
              </button>
            ))}
          </div>
        ))}
    </div>
  );
}

/* P02 — Lesson Detail (p02-lesson-detail) */
export function P02LessonDetailPage() {
  const navigate = useNavigate();
  const { lessons, selectedLessonId, profiles, selectedProfileId } = useParent();
  const lesson = lessons.find((l) => l.id === selectedLessonId) || lessons[0];
  const child = profiles.find((p) => p.id === selectedProfileId && !p.archived) || profiles.find((p) => !p.archived);
  const childName = child ? child.displayName.replace(/^Bé\s+/, "") : "bé";
  const stages = [
    { icon: "🥚", label: "Trứng", bg: "#FEF3C7" },
    { icon: "🐛", label: "Sâu", bg: "#D1FAE5" },
    { icon: "🌿", label: "Nhộng", bg: "#DBEAFE" },
    { icon: "🦋", label: "Bướm", bg: "#EFF6FF" },
  ];

  return (
    <div className="col" style={{ gap: 16, paddingBottom: 76 }}>
      {/* Hero */}
      <div
        style={{
          borderRadius: 24,
          padding: 18,
          background: "linear-gradient(135deg, #DBEAFE 0%, #D1FAE5 55%, #FEF3C7 100%)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <span style={{ position: "absolute", right: -24, top: -24, width: 100, height: 100, borderRadius: "50%", background: "rgba(255,255,255,0.5)" }} />
        <div className="row" style={{ gap: 8, position: "relative", flexWrap: "wrap" }}>
          <span className="pill ok"><Icon name="leaf" size={13} /> {lesson.topic}</span>
          <span className="pill"><Icon name="user" size={13} /> {lesson.ageBand}</span>
        </div>
        <h1 style={{ marginTop: 12, position: "relative", fontSize: 26 }}>{lesson.title}</h1>
        <p
          className="muted small"
          style={{
            marginTop: 6,
            position: "relative",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {lesson.summary}
        </p>

        {/* Lifecycle path */}
        <div className="row" style={{ marginTop: 16, gap: 0, position: "relative", justifyContent: "space-between" }}>
          {stages.map((st, i) => (
            <React.Fragment key={st.label}>
              <div className="col" style={{ alignItems: "center", gap: 4 }}>
                <span
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 18,
                    background: st.bg,
                    border: "3px solid #FFFFFF",
                    boxShadow: "0 4px 10px rgba(15,23,42,0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 26,
                  }}
                >
                  {st.icon}
                </span>
                <span className="tiny" style={{ fontWeight: 700 }}>{st.label}</span>
              </div>
              {i < stages.length - 1 && <Icon name="arrow-right" size={14} color="#94A3B8" />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Drawing steps */}
      <div className="col" style={{ gap: 10 }}>
        <div className="row" style={{ gap: 8 }}>
          <IconBadge name="palette" tone="primary" size={32} />
          <h2>Các bước vẽ</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
          {lesson.drawingSteps.map((st) => (
            <div key={st.step} className="card col" style={{ padding: 12, gap: 6 }}>
              <span
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 10,
                  background: "var(--grad-primary)",
                  color: "#FFFFFF",
                  fontWeight: 800,
                  fontSize: 14,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {st.step}
              </span>
              <span style={{ fontWeight: 700, fontSize: 14 }}>{st.title}</span>
              <span className="tiny muted">{st.hint}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Knowledge */}
      <div className="col" style={{ gap: 10 }}>
        <div className="row" style={{ gap: 8 }}>
          <IconBadge name="sparkle" tone="accent" size={32} />
          <h2>Khám phá</h2>
        </div>
        <div className="col" style={{ gap: 8 }}>
          {lesson.knowledgePoints.map((kp, i) => (
            <details key={i} className="card" style={{ padding: "10px 14px" }}>
              <summary style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", listStyle: "none" }}>
                <span style={{ fontSize: 22 }}>{kp.icon}</span>
                <span style={{ fontWeight: 700, fontSize: 14, flex: 1 }}>{kp.title}</span>
                <Icon name="chevron-down" size={16} color="#94A3B8" />
              </summary>
              <p className="small muted" style={{ marginTop: 8 }}>{kp.text}</p>
            </details>
          ))}
        </div>
      </div>

      {/* Outdoor activity teaser */}
      <div
        className="card row"
        style={{ gap: 12, background: "var(--accent-50)", borderColor: "var(--warn-100)" }}
      >
        <IconBadge name="sun" tone="accent" />
        <div className="col" style={{ gap: 2, flex: 1 }}>
          <h3>Hoạt động ngoài trời</h3>
          <span className="tiny muted">Mở sau khi xem video</span>
        </div>
        <Icon name="lock" size={18} color="#B45309" />
      </div>

      {/* Sticky CTA */}
      <div
        style={{
          position: "sticky",
          bottom: 8,
          marginTop: 4,
        }}
      >
        <button
          type="button"
          className="btn block"
          style={{ padding: "15px 20px", fontSize: 16 }}
          onClick={() => navigate("/p03-drawing-line-guide")}
        >
          <Icon name="camera" size={20} color="#FFFFFF" />
          Bắt đầu cùng {childName}
        </button>
      </div>
    </div>
  );
}



/* ──────────────────────────────────────────────
   P03 — Drawing with Optional Generic Line-Sketch Guide
   ────────────────────────────────────────────── */
export function P03DrawingLineGuidePage() {
  const navigate = useNavigate();
  const { guideEnabled, setGuideEnabled, guideTopic, setActiveSheet } = useParent();

  const steps = [
    {
      label: "Thân nhỏ",
      svg: (
        <svg viewBox="0 0 80 60" width="100%" height="50">
          <ellipse cx="40" cy="32" rx="5" ry="18" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <circle cx="40" cy="11" r="4" fill="none" stroke="#0F172A" strokeWidth="2.5" />
        </svg>
      ),
    },
    {
      label: "Hai cánh lớn",
      svg: (
        <svg viewBox="0 0 80 60" width="100%" height="50">
          <ellipse cx="40" cy="32" rx="5" ry="18" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <path d="M35 22 C12 6, 10 38, 35 34" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <path d="M45 22 C68 6, 70 38, 45 34" fill="none" stroke="#0F172A" strokeWidth="2.5" />
        </svg>
      ),
    },
    {
      label: "Cánh dưới & râu",
      svg: (
        <svg viewBox="0 0 80 60" width="100%" height="50">
          <ellipse cx="40" cy="32" rx="5" ry="18" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <path d="M35 22 C12 6, 10 38, 35 34" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <path d="M45 22 C68 6, 70 38, 45 34" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <path d="M35 34 C18 38, 20 54, 36 46" fill="none" stroke="#0F172A" strokeWidth="2.5" />
          <path d="M45 34 C62 38, 60 54, 44 46" fill="none" stroke="#0F172A" strokeWidth="2.5" />
        </svg>
      ),
    },
  ];

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* Header */}
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="image" tone="primary" size={40} />
          <div>
            <h1>Bé đang vẽ</h1>
            <p className="tiny muted">{guideTopic}</p>
          </div>
        </div>
        <button
          type="button"
          className={`chip${guideEnabled ? " on" : ""}`}
          onClick={() => setGuideEnabled(!guideEnabled)}
        >
          <Icon name={guideEnabled ? "check" : "palette"} size={14} />
          {guideEnabled ? "Tắt gợi ý" : "Bật gợi ý"}
        </button>
      </div>

      {/* Drawing viewfinder */}
      <div
        style={{
          borderRadius: 24,
          overflow: "hidden",
          background: "linear-gradient(180deg, #F5EBE1 0%, #EFE2D3 100%)",
          position: "relative",
          aspectRatio: "4/3",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "2px dashed #CBD5E1",
        }}
      >
        <img
          src="/child-butterfly-art.png"
          alt="Tranh con bướm bé đang vẽ trên giấy"
          style={{ width: "90%", height: "90%", objectFit: "contain", borderRadius: 16, background: "#FFFFFF" }}
        />
        {/* Dashed overlay guide */}
        {guideEnabled && (
          <div
            style={{
              position: "absolute",
              right: 12,
              bottom: 12,
              background: "rgba(255,255,255,0.95)",
              borderRadius: 14,
              border: "1.5px dashed #2563EB",
              padding: 6,
            }}
          >
            <svg viewBox="0 0 120 100" width="80" height="66" aria-label="Nét đứt gợi ý">
              <ellipse cx="60" cy="54" rx="6" ry="24" fill="none" stroke="#2563EB" strokeWidth="2.2" strokeDasharray="4 3" />
              <path d="M54 38 C20 14, 18 62, 54 56 M66 38 C100 14, 102 62, 66 56" fill="none" stroke="#2563EB" strokeWidth="2.2" strokeDasharray="4 3" />
            </svg>
            <p className="tiny" style={{ textAlign: "center", color: "#2563EB", fontWeight: 700, margin: 0 }}>Gợi ý</p>
          </div>
        )}
      </div>

      {/* Step cards when guide on */}
      {guideEnabled && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
          {steps.map((s, i) => (
            <div key={i} className="card col" style={{ padding: 10, gap: 4, textAlign: "center" }}>
              {s.svg}
              <span style={{ fontSize: 12, fontWeight: 700 }}>{s.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* CTA row — secondary "Chọn ảnh" left, primary "Chụp tranh" right */}
      <div className="row" style={{ gap: 10 }}>
        <button
          type="button"
          className="btn secondary"
          style={{ flex: 1 }}
          onClick={() => navigate("/p04-capture-subject-confirmation")}
        >
          <Icon name="image" size={18} /> Chọn ảnh
        </button>
        <button
          type="button"
          className="btn"
          style={{ flex: 1.6 }}
          onClick={() => setActiveSheet("CAMERA_PERMISSION")}
        >
          <Icon name="camera" size={18} color="#FFFFFF" /> Chụp tranh
        </button>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   P04 — Capture & Subject Confirmation
   ────────────────────────────────────────────── */
export function P04CaptureSubjectConfirmationPage() {
  const navigate = useNavigate();
  const { detectedSubject, setSubjectConfirmed, setActiveSheet, showToast } = useParent();

  return (
    <div className="col" style={{ gap: 16 }}>
      <h1>Xác nhận chủ thể</h1>

      {/* Photo on warm desk */}
      <div
        style={{
          borderRadius: 24,
          overflow: "hidden",
          background: "linear-gradient(180deg, #F5EBE1 0%, #EFE2D3 100%)",
          padding: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <img
          src="/child-butterfly-art.png"
          alt="Ảnh chụp tranh con bướm của bé"
          style={{
            width: "100%",
            maxHeight: 220,
            objectFit: "contain",
            borderRadius: 16,
            border: "3px solid #FFFFFF",
            boxShadow: "0 8px 22px rgba(15,23,42,0.14)",
            background: "#FFFFFF",
          }}
        />
      </div>

      {/* AI suggestion */}
      <div
        className="card row"
        style={{ gap: 14, background: "var(--primary-50)", borderColor: "var(--primary-100)" }}
      >
        <span style={{ fontSize: 36 }}>🦋</span>
        <div className="col" style={{ gap: 3, flex: 1 }}>
          <span style={{ fontSize: 18, fontWeight: 800, color: "var(--primary)" }}>
            Có thể là {detectedSubject.toLowerCase()}
          </span>
          <span className="tiny muted">Hệ thống nhận diện — hãy xác nhận trước khi tiếp tục</span>
        </div>
        <Icon name="wand" size={22} color="var(--primary)" />
      </div>

      <div className="col" style={{ gap: 10 }}>
        <button
          type="button"
          className="btn block"
          style={{ padding: "14px 20px" }}
          onClick={() => {
            setSubjectConfirmed(true);
            showToast("Đã xác nhận chủ thể bức tranh.", "ok");
            navigate("/p05-context-idea-confirmation");
          }}
        >
          <Icon name="check" size={20} color="#FFFFFF" /> Đúng rồi
        </button>
        <button
          type="button"
          className="btn secondary block"
          onClick={() => setActiveSheet("EDIT_SUBJECT")}
        >
          <Icon name="settings" size={18} /> Chỉnh chủ thể
        </button>
        <button
          type="button"
          className="btn ghost block small"
          onClick={() => navigate("/p03-drawing-line-guide")}
        >
          <Icon name="arrow-left" size={16} /> Chọn ảnh khác
        </button>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   P05 — Context & Idea Confirmation
   ────────────────────────────────────────────── */
export function P05ContextIdeaConfirmationPage() {
  const navigate = useNavigate();
  const { ideaTranscript, setIdeaTranscript, detectedSubject, setContextConfirmed, showToast } = useParent();
  const [editing, setEditing] = useState(false);

  const tags = [
    { label: "5 tuổi", icon: "user" as const, tone: "primary" as const },
    { label: detectedSubject, icon: "sparkle" as const, tone: "accent" as const },
    { label: "Khám phá thiên nhiên", icon: "leaf" as const, tone: "mint" as const },
  ];

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* Child + drawing mini-card */}
      <div className="card row" style={{ gap: 12 }}>
        <img
          src="/child-butterfly-art.png"
          alt="Tranh thu nhỏ"
          style={{ width: 60, height: 60, objectFit: "cover", borderRadius: 14, border: "2px solid var(--line)", background: "#FFFFFF" }}
        />
        <div className="col" style={{ gap: 5, flex: 1 }}>
          <span style={{ fontWeight: 800, fontSize: 17 }}>Minh · 5 tuổi</span>
          <span className="tiny muted">Vòng đời bướm</span>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            {tags.map((t) => (
              <span key={t.label} className={`pill${t.tone === "mint" ? " ok" : t.tone === "accent" ? " warn" : ""}`} style={{ fontSize: 11.5 }}>
                <Icon name={t.icon} size={12} /> {t.label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Idea block */}
      <div className="card col" style={{ gap: 10 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="message" tone="primary" size={32} />
            <h2>Ý tưởng của con</h2>
          </div>
          <button
            type="button"
            className="icon-btn"
            aria-label={editing ? "Lưu" : "Sửa"}
            onClick={() => setEditing(!editing)}
          >
            <Icon name={editing ? "check" : "settings"} size={18} />
          </button>
        </div>
        {editing ? (
          <textarea
            className="input"
            rows={3}
            value={ideaTranscript}
            onChange={(e) => setIdeaTranscript(e.target.value)}
          />
        ) : (
          <div
            style={{
              padding: "14px 16px",
              borderRadius: 16,
              background: "linear-gradient(135deg, var(--primary-50), #F0FDF4)",
              border: "1px solid var(--primary-100)",
              fontStyle: "italic",
              fontWeight: 600,
              fontSize: 15,
              lineHeight: 1.55,
            }}
          >
            "{ideaTranscript}"
          </div>
        )}
        <span className="tiny muted">
          <Icon name="info" size={13} /> Chỉ chủ đề, nhóm tuổi và hoạt động được dùng trong kịch bản — không có thông tin cá nhân của bé.
        </span>
      </div>

      <button
        type="button"
        className="btn block"
        style={{ padding: "14px 20px" }}
        onClick={() => {
          setContextConfirmed(true);
          showToast("Đã xác nhận thông tin và ý tưởng của con.", "ok");
          navigate("/p06-story-review");
        }}
      >
        <Icon name="arrow-right" size={18} color="#FFFFFF" /> Tiếp tục đến kịch bản
      </button>
    </div>
  );
}

/* scene sketch mini SVGs */
function SceneSketch({ index }: { index: number }) {
  const sketches: Record<number, React.ReactNode> = {
    1: (
      <svg viewBox="0 0 56 42" width="100%" height="100%">
        <path d="M6 32 Q28 14 50 28" fill="none" stroke="#475569" strokeWidth="1.8" />
        <circle cx="20" cy="22" r="3.5" fill="none" stroke="#0F172A" strokeWidth="1.8" />
        <circle cx="28" cy="20" r="3.5" fill="none" stroke="#0F172A" strokeWidth="1.8" />
        <circle cx="36" cy="22" r="3.8" fill="none" stroke="#0F172A" strokeWidth="1.8" />
      </svg>
    ),
    2: (
      <svg viewBox="0 0 56 42" width="100%" height="100%">
        <line x1="10" y1="8" x2="46" y2="8" stroke="#0F172A" strokeWidth="2" />
        <line x1="28" y1="8" x2="28" y2="14" stroke="#0F172A" strokeWidth="1.8" />
        <ellipse cx="28" cy="25" rx="6" ry="10" fill="none" stroke="#0F172A" strokeWidth="2" />
      </svg>
    ),
    3: (
      <svg viewBox="0 0 56 42" width="100%" height="100%">
        <ellipse cx="28" cy="22" rx="2.5" ry="10" fill="none" stroke="#0F172A" strokeWidth="1.8" />
        <path d="M25 16 C10 8, 10 30, 25 26" fill="none" stroke="#0F172A" strokeWidth="1.8" />
        <path d="M31 16 C46 8, 46 30, 31 26" fill="none" stroke="#0F172A" strokeWidth="1.8" />
      </svg>
    ),
    4: (
      <svg viewBox="0 0 56 42" width="100%" height="100%">
        <circle cx="16" cy="28" r="5" fill="none" stroke="#475569" strokeWidth="1.6" />
        <line x1="16" y1="33" x2="16" y2="38" stroke="#475569" strokeWidth="1.6" />
        <path d="M32 15 C24 9, 24 24, 32 20 M34 15 C42 9, 42 24, 34 20" fill="none" stroke="#0F172A" strokeWidth="1.8" />
      </svg>
    ),
    5: (
      <svg viewBox="0 0 56 42" width="100%" height="100%">
        <circle cx="44" cy="9" r="4" fill="none" stroke="#475569" strokeWidth="1.6" />
        <path d="M22 20 C13 13, 13 28, 22 24 M26 20 C35 13, 35 28, 26 24" fill="none" stroke="#0F172A" strokeWidth="1.8" />
        <path d="M6 36 Q28 30 50 36" fill="none" stroke="#475569" strokeWidth="1.5" />
      </svg>
    ),
  };
  return <div style={{ width: 60, height: 46, borderRadius: 10, border: "1px solid #E2E8F0", background: "#FFFFFF", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, overflow: "hidden", padding: 4 }}>{sketches[index] ?? sketches[5]}</div>;
}

/* ──────────────────────────────────────────────
   P06 — Story Review
   ────────────────────────────────────────────── */
export function P06StoryReviewPage() {
  const { scenes, scriptRevision, rewriteCount, rewriteSuggestion, setRewriteSuggestion, requestAiRewrite, setActiveSheet } = useParent();

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* header */}
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <img
            src="/child-butterfly-art.png"
            alt="Tranh tham chiếu"
            style={{ width: 42, height: 42, borderRadius: 12, objectFit: "cover", border: "2px solid #FFFFFF", boxShadow: "0 4px 10px rgba(15,23,42,0.12)", background: "#FFFFFF" }}
          />
          <div>
            <h1>Kịch bản</h1>
            <p className="tiny muted">Vòng đời bướm · Minh</p>
          </div>
        </div>
        <span className="pill">
          <Icon name="book" size={13} /> Bản {scriptRevision}
        </span>
      </div>

      {/* Read-only notice */}
      <div className="row" style={{ gap: 8, padding: "8px 12px", borderRadius: 12, background: "var(--warn-50)", border: "1px solid var(--warn-100)" }}>
        <Icon name="lock" size={16} color="#B45309" />
        <span className="tiny" style={{ color: "#B45309", fontWeight: 700 }}>
          Kịch bản do AI tạo — chỉ xem trước, không chỉnh sửa từng cảnh
        </span>
      </div>

      {/* Scene cards */}
      <div className="col" style={{ gap: 10 }}>
        {scenes.map((scene) => (
          <div key={scene.index} className="card row" style={{ alignItems: "flex-start", gap: 12, padding: 12 }}>
            <div className="col" style={{ gap: 4, alignItems: "center" }}>
              <SceneSketch index={scene.index} />
              <span className="tiny muted" style={{ fontWeight: 800 }}>Cảnh {scene.index}</span>
            </div>
            <div className="col" style={{ gap: 4, flex: 1 }}>
              <span style={{ fontWeight: 800, fontSize: 14 }}>{scene.title}</span>
              <p className="small muted" style={{ lineHeight: 1.45 }}>{scene.narration}</p>
            </div>
          </div>
        ))}
      </div>

      {/* AI rewrite box */}
      <div className="card col" style={{ gap: 10 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="wand" tone="accent" size={30} />
            <label htmlFor="rewrite-box" style={{ fontWeight: 800, fontSize: 14 }}>Gợi ý viết lại</label>
          </div>
          <span className={`pill ${rewriteCount >= 3 ? "err" : "warn"}`}>
            {rewriteCount}/3 lần
          </span>
        </div>
        <input
          id="rewrite-box"
          className="input"
          value={rewriteSuggestion}
          onChange={(e) => setRewriteSuggestion(e.target.value)}
          placeholder="Ví dụ: thêm cảnh bướm ghé một bông hoa"
        />
        <button
          type="button"
          className="btn secondary block"
          disabled={rewriteCount >= 3}
          onClick={requestAiRewrite}
        >
          <Icon name="refresh" size={16} /> Gửi gợi ý
        </button>
      </div>

      <button
        type="button"
        className="btn block"
        style={{ padding: "14px 20px" }}
        onClick={() => setActiveSheet("CONFIRM_SCRIPT")}
      >
        <Icon name="check" size={20} color="#FFFFFF" /> Xác nhận kịch bản
      </button>
    </div>
  );
}

/* P07 — Video Job Status (p07-video-job-status + UI05/UI07 states) */
export function P07VideoJobStatusPage() {
  const navigate = useNavigate();
  const { videoJobMode, setVideoJobMode, setActiveSheet } = useParent();

  const stages = [
    { label: "Phân tích tranh", icon: "image" as const, done: true, current: false },
    {
      label: "Tạo các cảnh",
      icon: "wand" as const,
      done: videoJobMode !== "RUNNING",
      current: videoJobMode === "RUNNING",
    },
    {
      label: "Lồng tiếng và phụ đề",
      icon: "message" as const,
      done: videoJobMode === "READY" || videoJobMode === "SAFETY_BLOCKED",
      current: false,
    },
    {
      label: "Kiểm tra an toàn",
      icon: "lock" as const,
      done: videoJobMode === "READY",
      current: videoJobMode === "SAFETY_BLOCKED",
    },
  ];
  const blocked = videoJobMode === "SAFETY_BLOCKED";
  const busy = videoJobMode === "SERVICE_ERROR";
  const running = videoJobMode === "RUNNING";

  return (
    <div className="col" style={{ gap: 16 }}>
      {/* Magic hero */}
      <div
        style={{
          borderRadius: 24,
          padding: "22px 18px",
          background: "linear-gradient(160deg, #DBEAFE 0%, #FFFBF7 55%, #FEF3C7 100%)",
          textAlign: "center",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div style={{ position: "relative", width: 132, height: 132, margin: "0 auto" }}>
          <span
            className={running ? "orbit" : undefined}
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "50%",
              border: "4px dashed " + (blocked || busy ? "#FCA5A5" : "#93C5FD"),
            }}
          />
          <img
            src="/child-butterfly-art.png"
            alt="Tranh của bé"
            style={{
              position: "absolute",
              inset: 14,
              width: 104,
              height: 104,
              borderRadius: "50%",
              objectFit: "cover",
              border: "4px solid #FFFFFF",
              boxShadow: "0 8px 20px rgba(37,99,235,0.2)",
              background: "#FFFFFF",
            }}
          />
          <span
            style={{
              position: "absolute",
              right: -2,
              bottom: 4,
              width: 38,
              height: 38,
              borderRadius: 14,
              background: blocked || busy ? "#FEE2E2" : "#FBBF24",
              color: blocked || busy ? "#DC2626" : "#78350F",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 10px rgba(15,23,42,0.18)",
            }}
          >
            <Icon name={blocked ? "lock" : busy ? "wifi-off" : "sparkle"} size={20} />
          </span>
        </div>
        <h1 style={{ marginTop: 14 }}>
          {blocked ? "Video chưa thể hiển thị" : busy ? "Dịch vụ đang bận" : "Đang tạo video"}
        </h1>
        <p className="muted small" style={{ marginTop: 4 }}>
          {blocked || busy ? "Lượt đã nhận vẫn được tính" : "Bạn có thể rời màn hình và quay lại sau"}
        </p>
      </div>

      {/* Stepper — discrete stages only (no percentage / ETA) */}
      <div className="card" style={{ padding: "16px 8px" }}>
        <div className="row" style={{ alignItems: "flex-start", justifyContent: "space-between", gap: 0 }}>
          {stages.map((st, idx) => {
            const bad = st.current && blocked;
            return (
              <React.Fragment key={st.label}>
                <div className="col" style={{ alignItems: "center", gap: 6, width: 70, textAlign: "center" }}>
                  <span
                    className={st.current && !bad ? "pulse" : undefined}
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 16,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: bad ? "var(--danger-100)" : st.done ? "var(--mint-100)" : st.current ? "var(--primary)" : "var(--surface-2)",
                      color: bad ? "var(--danger)" : st.done ? "var(--mint-700)" : st.current ? "#FFFFFF" : "var(--ink-3)",
                    }}
                  >
                    <Icon name={st.done ? "check" : st.icon} size={20} />
                  </span>
                  <span className="tiny" style={{ fontWeight: st.current ? 800 : 600, lineHeight: 1.25 }}>{st.label}</span>
                </div>
                {idx < stages.length - 1 && (
                  <span style={{ flex: 1, height: 3, borderRadius: 2, marginTop: 20, background: st.done ? "var(--mint)" : "var(--line)" }} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {(blocked || busy) && (
        <div className="card row" style={{ borderColor: "#FECACA", background: "var(--danger-50)", gap: 12 }}>
          <IconBadge name={blocked ? "lock" : "wifi-off"} tone="danger" />
          <div className="col" style={{ gap: 4, flex: 1 }}>
            <h3 style={{ color: "var(--danger)" }}>
              {blocked ? "Nội dung chưa phù hợp" : "Hệ thống quá tải"}
            </h3>
            <span className="tiny muted">
              {blocked ? "Hãy thử lại với một bức tranh khác." : "Vui lòng thử lại sau ít phút."}
            </span>
          </div>
          {blocked ? (
            <button type="button" className="icon-btn" aria-label="Quay lại bài học" onClick={() => navigate("/p02-lesson-detail")}>
              <Icon name="arrow-left" />
            </button>
          ) : (
            <button type="button" className="icon-btn" aria-label="Thử lại" onClick={() => setVideoJobMode("RUNNING")}>
              <Icon name="refresh" />
            </button>
          )}
        </div>
      )}

      <div className="col" style={{ gap: 10 }}>
        <button type="button" className="btn block" style={{ padding: "14px 20px" }} onClick={() => navigate("/p08-video-and-activities")}>
          <Icon name="play" size={18} color="#FFFFFF" fill="#FFFFFF" /> Xem video
        </button>
        <div className="row" style={{ gap: 10 }}>
          <button type="button" className="btn secondary" style={{ flex: 1 }} onClick={() => navigate("/p01-lesson-library")}>
            <Icon name="book" size={18} /> Thư viện
          </button>
          <button type="button" className="btn ghost" style={{ flex: 1 }} onClick={() => setActiveSheet("CANCEL_VIDEO")}>
            <Icon name="close" size={18} /> Hủy video
          </button>
        </div>
      </div>

      {/* Review aid: UI05 / UI07 states */}
      <details className="card" style={{ padding: "8px 12px", background: "#F8FAFC", boxShadow: "none" }}>
        <summary className="tiny muted" style={{ fontWeight: 700, cursor: "pointer" }}>Xem các trạng thái (UI05 / UI07)</summary>
        <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 8 }}>
          <button type="button" className={"chip" + (running ? " on" : "")} onClick={() => setVideoJobMode("RUNNING")}>
            <Icon name="wand" size={14} /> Đang tạo cảnh
          </button>
          <button type="button" className={"chip" + (blocked ? " on" : "")} onClick={() => setVideoJobMode("SAFETY_BLOCKED")}>
            <Icon name="lock" size={14} /> Video chưa thể hiển thị
          </button>
          <button type="button" className={"chip" + (busy ? " on" : "")} onClick={() => setVideoJobMode("SERVICE_ERROR")}>
            <Icon name="wifi-off" size={14} /> Dịch vụ đang bận
          </button>
        </div>
      </details>
    </div>
  );
}

/* P08 — Video & Outdoor Activities (p08-video-and-activities) */
export function P08VideoAndActivitiesPage() {
  const navigate = useNavigate();
  const { lessons, selectedLessonId, captionsEnabled, setCaptionsEnabled, setHasActiveRun, showToast } =
    useParent();
  const lesson = lessons.find((l) => l.id === selectedLessonId) || lessons[0];

  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>Chuyến bay của bướm</h1>
        <span className="pill ok"><Icon name="check" size={13} /> An toàn</span>
      </div>

      {/* 16:9 private video player */}
      <div style={{ borderRadius: 24, overflow: "hidden", background: "#0F172A", boxShadow: "0 14px 30px rgba(15,23,42,0.28)" }}>
        <div
          style={{
            position: "relative",
            background: "linear-gradient(135deg, #DBEAFE, #FFFBF7 60%, #FEF3C7)",
            aspectRatio: "16 / 9",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <img
            src="/child-butterfly-art.png"
            alt="Khung hình mở đầu từ bức tranh con bướm của bé"
            style={{ width: "86%", height: "86%", objectFit: "contain" }}
          />
          <span
            style={{
              position: "absolute",
              width: 58,
              height: 58,
              borderRadius: "50%",
              background: "rgba(37,99,235,0.92)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 8px 20px rgba(37,99,235,0.45)",
            }}
          >
            <Icon name="play" size={26} color="#FFFFFF" fill="#FFFFFF" />
          </span>
          {captionsEnabled && (
            <div
              style={{
                position: "absolute",
                bottom: 8,
                left: 12,
                right: 12,
                background: "rgba(15, 23, 42, 0.82)",
                color: "#FFFFFF",
                padding: "6px 10px",
                borderRadius: 10,
                fontSize: 12,
                textAlign: "center",
              }}
            >
              “Chú bướm vươn đôi cánh bay lên bầu trời xanh...”
            </div>
          )}
        </div>
        <div className="row" style={{ padding: "10px 14px", gap: 10, color: "#FFFFFF" }}>
          <span style={{ fontSize: 12, fontWeight: 700 }}>0:00</span>
          <span style={{ flex: 1, height: 5, borderRadius: 999, background: "#334155", position: "relative" }}>
            <span style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: "6%", borderRadius: 999, background: "#FBBF24" }} />
          </span>
          <span style={{ fontSize: 12, fontWeight: 700 }}>1:24</span>
          <button
            type="button"
            aria-label={"Phụ đề " + (captionsEnabled ? "đang bật" : "đang tắt")}
            onClick={() => setCaptionsEnabled(!captionsEnabled)}
            style={{
              border: "none",
              cursor: "pointer",
              borderRadius: 8,
              padding: "3px 9px",
              fontWeight: 800,
              fontSize: 12,
              background: captionsEnabled ? "var(--primary)" : "#334155",
              color: "#FFFFFF",
            }}
          >
            CC
          </button>
        </div>
      </div>

      {/* Outdoor activities */}
      <div className="col" style={{ gap: 10 }}>
        <div className="row" style={{ gap: 8 }}>
          <IconBadge name="sun" tone="accent" size={32} />
          <h2>Hoạt động ngoài trời</h2>
        </div>
        {lesson.outdoorActivities.map((act) => (
          <div key={act.id} className="card row" style={{ gap: 12, padding: 14, alignItems: "flex-start" }}>
            <IconBadge name="leaf" tone="mint" />
            <div className="col" style={{ gap: 4, flex: 1 }}>
              <h3>{act.title}</h3>
              <span className="tiny" style={{ color: "var(--mint-700)", fontWeight: 700 }}>{act.materials}</span>
              <span className="small muted">{act.firstStep}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Actions in exact P08 order: left "Tạo lại video" (secondary), right "Hoàn tất" (primary) */}
      <div className="row" style={{ gap: 10 }}>
        <button
          type="button"
          className="btn secondary"
          style={{ flex: 1 }}
          onClick={() => {
            showToast("Đã ẩn video cũ và quay lại rà soát kịch bản.", "info");
            navigate("/p06-story-review");
          }}
        >
          <Icon name="refresh" size={18} /> Tạo lại video
        </button>
        <button
          type="button"
          className="btn"
          style={{ flex: 1 }}
          onClick={() => {
            setHasActiveRun(false);
            showToast("Đã hoàn tất buổi học Vòng đời bướm của Minh.", "ok");
            navigate("/p09-history-feedback");
          }}
        >
          <Icon name="check" size={18} color="#FFFFFF" /> Hoàn tất
        </button>
      </div>
    </div>
  );
}



/* ──────────────────────────────────────────────
   P09 — Lesson History & Lesson-Scoped Feedback
   ────────────────────────────────────────────── */
export function P09HistoryFeedbackPage() {
  const {
    historyDeleted,
    setHistoryDeleted,
    feedbackMessages,
    sendFeedback,
    clearFeedbackForDemo,
    restoreFeedbackForDemo,
    showToast,
  } = useParent();
  const [draft, setDraft] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row" style={{ gap: 10 }}>
          <IconBadge name="clock" tone="primary" size={40} />
          <h1>Lịch sử học</h1>
        </div>
      </div>

      {/* History item */}
      {!historyDeleted ? (
        <div className="card col" style={{ gap: 12 }}>
          <div className="row" style={{ gap: 12 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                background: "linear-gradient(135deg, #DBEAFE, #FEF3C7)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 28,
                flexShrink: 0,
              }}
            >
              🦋
            </div>
            <div className="col" style={{ gap: 4, flex: 1 }}>
              <span style={{ fontWeight: 800, fontSize: 16 }}>Vòng đời bướm</span>
              <span className="tiny muted">30/10/2026 · Minh · 5 tuổi</span>
              <span className="pill ok" style={{ alignSelf: "flex-start", fontSize: 11.5 }}>
                <Icon name="check" size={12} /> Đã gửi cho giáo viên
              </span>
            </div>
            <button
              type="button"
              className="icon-btn"
              aria-label="Tùy chọn"
              onClick={() => setConfirmOpen(!confirmOpen)}
            >
              <Icon name="settings" size={18} />
            </button>
          </div>
          {confirmOpen && (
            <div className="row" style={{ gap: 8, padding: "10px 12px", borderRadius: 14, background: "var(--danger-50)", border: "1px solid #FECACA" }}>
              <Icon name="alert" size={18} color="var(--danger)" />
              <span className="tiny" style={{ color: "var(--danger)", fontWeight: 700, flex: 1 }}>
                Xóa buổi học và ảnh/video? Lượt đã dùng không hoàn lại.
              </span>
              <button
                type="button"
                className="btn danger small"
                onClick={() => {
                  setHistoryDeleted(true);
                  setConfirmOpen(false);
                  showToast("Đã xóa buổi học khỏi lịch sử.", "info");
                }}
              >
                <Icon name="trash" size={14} /> Xóa
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="card col" style={{ alignItems: "center", textAlign: "center", padding: 24, gap: 10 }}>
          <IconBadge name="clock" tone="neutral" size={52} />
          <h3>Chưa có lịch sử</h3>
          <button type="button" className="btn secondary small" onClick={() => setHistoryDeleted(false)}>
            <Icon name="refresh" size={15} /> Khôi phục dữ liệu mẫu
          </button>
        </div>
      )}

      {/* Feedback section */}
      <div className="card col" style={{ gap: 12 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="message" tone="mint" size={32} />
            <h2>Phản hồi bài học</h2>
          </div>
          <button
            type="button"
            className="icon-btn"
            aria-label={feedbackMessages.length > 0 ? "Xem mẫu trống" : "Xem mẫu có phản hồi"}
            title={feedbackMessages.length > 0 ? "Xem mẫu trống (UI09)" : "Xem mẫu có phản hồi"}
            onClick={() => feedbackMessages.length > 0 ? clearFeedbackForDemo() : restoreFeedbackForDemo()}
          >
            <Icon name={feedbackMessages.length > 0 ? "close" : "message"} size={18} />
          </button>
        </div>
        <span className="tiny muted">
          <Icon name="lock" size={13} /> Chỉ văn bản · Gắn bài "Vòng đời bướm" · Trường Mầm non Ánh Dương
        </span>

        {feedbackMessages.length === 0 ? (
          <div className="card col" style={{ padding: 20, alignItems: "center", textAlign: "center", gap: 8, background: "var(--bg)" }}>
            <IconBadge name="message" tone="neutral" size={48} />
            <h3>Chưa có phản hồi</h3>
            <p className="tiny muted">Chia sẻ cảm nhận của bé sau bài học nhé.</p>
          </div>
        ) : (
          <div className="col" style={{ gap: 8 }}>
            {feedbackMessages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  padding: "10px 14px",
                  borderRadius: 14,
                  background: msg.sender === "Phụ huynh" ? "var(--primary-50)" : "var(--mint-50)",
                  border: "1px solid var(--line)",
                }}
              >
                <div className="row" style={{ justifyContent: "space-between", marginBottom: 5 }}>
                  <span style={{ fontWeight: 800, fontSize: 13 }}>{msg.sender}</span>
                  <span className="tiny muted">{msg.date}</span>
                </div>
                <p className="small">{msg.text}</p>
              </div>
            ))}
          </div>
        )}

        <div className="field">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <label htmlFor="feedback-input">Gửi phản hồi</label>
            <span className="tiny muted">{draft.length}/300</span>
          </div>
          <textarea
            id="feedback-input"
            className="input"
            maxLength={300}
            rows={2}
            placeholder="Ví dụ: Bé thích phần quan sát cánh bướm..."
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="btn block"
          disabled={!draft.trim()}
          onClick={() => {
            sendFeedback(draft);
            setDraft("");
            showToast("Đã gửi phản hồi cho giáo viên.", "ok");
          }}
        >
          <Icon name="share" size={18} color="#FFFFFF" /> Gửi cho giáo viên
        </button>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   P10 — Child Profiles Management
   ────────────────────────────────────────────── */
export function P10ChildProfilesPage() {
  const navigate = useNavigate();
  const { profiles, selectedProfileId, setSelectedProfileId, addProfile, archiveProfile, restoreProfile, showToast } = useParent();
  const [formOpen, setFormOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newAge, setNewAge] = useState("");
  const [nameError, setNameError] = useState("");
  const [ageError, setAgeError] = useState("");

  const active = profiles.filter((p) => !p.archived);
  const archived = profiles.filter((p) => p.archived);

  const toneColors = ["#3B82F6", "#F59E0B", "#10B981", "#EF4444", "#0EA5E9"];

  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1>Hồ sơ bé</h1>
        <button
          type="button"
          className="icon-btn"
          aria-label="Thêm hồ sơ mới"
          onClick={() => { setFormOpen(!formOpen); setNameError(""); setAgeError(""); }}
        >
          <Icon name="plus" size={20} />
        </button>
      </div>

      {/* Active profiles */}
      <div className="col" style={{ gap: 10 }}>
        {active.map((p, i) => {
          const color = toneColors[i % toneColors.length];
          const initial = p.displayName.replace(/^Bé\s+/, "").charAt(0).toUpperCase();
          const isSelected = p.id === selectedProfileId;
          return (
            <div
              key={p.id}
              className="card row"
              style={{
                gap: 14,
                padding: 14,
                borderColor: isSelected ? "var(--primary)" : "var(--line)",
                background: isSelected ? "var(--primary-50)" : "#FFFFFF",
                cursor: "pointer",
              }}
              onClick={() => setSelectedProfileId(p.id)}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 18,
                  background: color,
                  color: "#FFFFFF",
                  fontWeight: 800,
                  fontSize: 22,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  boxShadow: `0 6px 14px ${color}55`,
                }}
              >
                {initial}
              </div>
              <div className="col" style={{ gap: 3, flex: 1 }}>
                <span style={{ fontWeight: 800, fontSize: 16 }}>{p.displayName}</span>
                <span className="tiny muted">{p.ageLabel} · Đã kết nối lớp</span>
              </div>
              {isSelected && <Icon name="check" size={20} color="var(--primary)" />}
              <button
                type="button"
                className="icon-btn"
                aria-label={`Lưu trữ hồ sơ ${p.displayName}`}
                onClick={(e) => {
                  e.stopPropagation();
                  archiveProfile(p.id);
                  showToast(`Đã lưu trữ hồ sơ ${p.displayName}.`, "info");
                }}
              >
                <Icon name="trash" size={16} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Add form */}
      {formOpen && (
        <div className="card col" style={{ gap: 12, borderColor: "var(--primary-100)", background: "var(--primary-50)" }}>
          <div className="row" style={{ gap: 8 }}>
            <IconBadge name="plus" tone="primary" size={30} />
            <h2>Thêm hồ sơ mới</h2>
          </div>
          <div className="field">
            <label htmlFor="new-name">Tên bé</label>
            <input
              id="new-name"
              className={`input${nameError ? " error" : ""}`}
              placeholder="Ví dụ: Bé Hoa"
              value={newName}
              onChange={(e) => { setNewName(e.target.value); setNameError(""); }}
            />
            {nameError && <span className="tiny" style={{ color: "var(--danger)" }}>{nameError}</span>}
          </div>
          <div className="field">
            <label htmlFor="new-age">Tuổi (tháng)</label>
            <input
              id="new-age"
              type="number"
              min={24}
              max={155}
              className={`input${ageError ? " error" : ""}`}
              placeholder="36 – 155 tháng"
              value={newAge}
              onChange={(e) => { setNewAge(e.target.value); setAgeError(""); }}
            />
            {ageError && (
              <span className="tiny" style={{ color: "var(--danger)" }}>
                <Icon name="alert" size={13} /> {ageError}
              </span>
            )}
          </div>
          <div className="row" style={{ gap: 10 }}>
            <button type="button" className="btn ghost" style={{ flex: 1 }} onClick={() => setFormOpen(false)}>
              Hủy
            </button>
            <button
              type="button"
              className="btn"
              style={{ flex: 1 }}
              onClick={() => {
                let valid = true;
                if (!newName.trim()) { setNameError("Vui lòng nhập tên bé."); valid = false; }
                const months = parseInt(newAge);
                if (isNaN(months) || months < 24 || months > 155) {
                  setAgeError("Vui lòng nhập số tháng tuổi hợp lệ (24–155 tháng).");
                  valid = false;
                }
                if (!valid) return;
                addProfile(newName.trim(), months, []);
                showToast(`Đã tạo hồ sơ cho ${newName.trim()}.`, "ok");
                setNewName(""); setNewAge(""); setFormOpen(false);
              }}
            >
              <Icon name="check" size={18} color="#FFFFFF" /> Lưu
            </button>
          </div>
        </div>
      )}

      {/* Archived */}
      {archived.length > 0 && (
        <div className="col" style={{ gap: 8 }}>
          <span className="tiny muted" style={{ fontWeight: 800 }}>Hồ sơ đã lưu trữ</span>
          {archived.map((p) => (
            <div key={p.id} className="card row" style={{ gap: 12, padding: 12, opacity: 0.7 }}>
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 14,
                  background: "#E2E8F0",
                  color: "#64748B",
                  fontWeight: 800,
                  fontSize: 18,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                {p.displayName.replace(/^Bé\s+/, "").charAt(0).toUpperCase()}
              </div>
              <div className="col" style={{ gap: 2, flex: 1 }}>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{p.displayName}</span>
                <span className="tiny muted">{p.ageLabel} · Đã lưu trữ</span>
              </div>
              <button
                type="button"
                className="btn secondary small"
                onClick={() => {
                  restoreProfile(p.id);
                  showToast(`Đã khôi phục hồ sơ ${p.displayName}.`, "ok");
                }}
              >
                <Icon name="refresh" size={14} /> Khôi phục
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        className="btn ghost block"
        onClick={() => navigate("/p01-lesson-library")}
      >
        <Icon name="book" size={17} /> Về thư viện bài học
      </button>
    </div>
  );
}

/* ──────────────────────────────────────────────
   P11 — Authentication
   ────────────────────────────────────────────── */
export function P11AuthenticationPage() {
  const navigate = useNavigate();
  const { setIsAuthenticated, showToast } = useParent();
  const [authMode, setAuthMode] = useState<"LOGIN" | "REGISTER" | "FORGOT">("LOGIN");
  const [email, setEmail] = useState("phuhuynh.minh@example.vn");
  const [password, setPassword] = useState("••••••••");
  const [fullName, setFullName] = useState("Nguyễn Thị Lan");

  const modeLabel = { LOGIN: "Đăng nhập", REGISTER: "Tạo tài khoản", FORGOT: "Quên mật khẩu" };

  return (
    <div className="col" style={{ gap: 20, paddingTop: 20 }}>
      {/* Hero brand */}
      <div className="col" style={{ alignItems: "center", textAlign: "center", gap: 12 }}>
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: 28,
            background: "linear-gradient(135deg, #3B82F6, #2563EB)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 14px 30px rgba(37,99,235,0.35)",
          }}
        >
          <Logo height={44} />
        </div>
        <div>
          <h1>Sketch2Life</h1>
          <p className="muted small">Dành cho phụ huynh · Biến tranh vẽ thành video</p>
        </div>
      </div>

      {/* Mode switcher */}
      <div className="row" style={{ gap: 4, background: "#F1F5F9", borderRadius: 999, padding: 4 }}>
        {(["LOGIN", "REGISTER", "FORGOT"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setAuthMode(m)}
            style={{
              flex: 1,
              border: "none",
              borderRadius: 999,
              padding: "9px 4px",
              fontWeight: 800,
              fontSize: 13,
              cursor: "pointer",
              background: authMode === m ? "#FFFFFF" : "transparent",
              color: authMode === m ? "var(--primary)" : "var(--ink-2)",
              boxShadow: authMode === m ? "0 2px 8px rgba(15,23,42,0.1)" : "none",
            }}
          >
            {modeLabel[m]}
          </button>
        ))}
      </div>

      <div className="card col" style={{ gap: 14 }}>
        {authMode === "REGISTER" && (
          <div className="field">
            <label htmlFor="auth-name">Họ tên</label>
            <input id="auth-name" className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
        )}
        <div className="field">
          <label htmlFor="auth-email">Email</label>
          <input id="auth-email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        {authMode !== "FORGOT" && (
          <div className="field">
            <label htmlFor="auth-password">Mật khẩu</label>
            <input id="auth-password" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
        )}

        {authMode === "LOGIN" && (
          <button
            type="button"
            className="btn block"
            style={{ padding: "14px 20px" }}
            onClick={() => {
              setIsAuthenticated(true);
              showToast("Đã đăng nhập tài khoản phụ huynh.", "ok");
              navigate("/p01-lesson-library");
            }}
          >
            <Icon name="arrow-right" size={18} color="#FFFFFF" /> Đăng nhập
          </button>
        )}
        {authMode === "REGISTER" && (
          <button
            type="button"
            className="btn block"
            style={{ padding: "14px 20px" }}
            onClick={() => {
              setIsAuthenticated(true);
              showToast("Đã tạo tài khoản phụ huynh thành công.", "ok");
              navigate("/p10-child-profiles");
            }}
          >
            <Icon name="check" size={18} color="#FFFFFF" /> Tạo tài khoản
          </button>
        )}
        {authMode === "FORGOT" && (
          <button
            type="button"
            className="btn block"
            style={{ padding: "14px 20px" }}
            onClick={() => {
              showToast("Đã gửi hướng dẫn đặt lại mật khẩu tới email đã xác minh.", "info");
              setAuthMode("LOGIN");
            }}
          >
            <Icon name="share" size={18} color="#FFFFFF" /> Gửi liên kết đặt lại
          </button>
        )}
      </div>

      <p className="tiny muted" style={{ textAlign: "center" }}>
        Bằng cách tiếp tục, bạn đồng ý với Điều khoản dịch vụ và Chính sách quyền riêng tư của Sketch2Life.
      </p>
    </div>
  );
}

/* ──────────────────────────────────────────────
   P12 — Video Quota & Optional Top-Up
   ────────────────────────────────────────────── */
export function P12VideoQuotaPage() {
  const navigate = useNavigate();
  const { quotaRemaining, quotaUsed, quotaTotal, showToast } = useParent();
  const [selectedPlan, setSelectedPlan] = useState<"ADDON" | "MONTHLY">("ADDON");
  const [selectedMethod, setSelectedMethod] = useState<"MoMo" | "VNPAY">("MoMo");

  const r = 38;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - quotaUsed / quotaTotal);

  const jobIconMap: Record<string, { icon: Parameters<typeof Icon>[0]["name"]; tone: Parameters<typeof IconBadge>[0]["tone"] }> = {
    ok: { icon: "video", tone: "mint" },
    warn: { icon: "clock", tone: "accent" },
    err: { icon: "alert", tone: "danger" },
    off: { icon: "lock", tone: "neutral" },
    "": { icon: "wand", tone: "primary" },
  };

  return (
    <div className="col" style={{ gap: 16 }}>
      <h1>Lượt tạo video</h1>

      {/* Quota donut hero */}
      <div
        style={{
          borderRadius: 24,
          padding: "22px 18px",
          background: "linear-gradient(135deg, #EFF6FF 0%, #FFFBF7 60%, #ECFDF5 100%)",
          display: "flex",
          alignItems: "center",
          gap: 20,
        }}
      >
        <svg width="92" height="92" viewBox="0 0 92 92" style={{ flexShrink: 0 }} aria-label={`Đã dùng ${quotaUsed} trong tổng ${quotaTotal} lượt`}>
          <circle cx="46" cy="46" r={r} fill="none" stroke="#DBEAFE" strokeWidth="10" />
          <circle
            cx="46"
            cy="46"
            r={r}
            fill="none"
            stroke="url(#qGrad)"
            strokeWidth="10"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 46 46)"
          />
          <defs>
            <linearGradient id="qGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#2563EB" />
            </linearGradient>
          </defs>
          <text x="46" y="42" textAnchor="middle" fontSize="18" fontWeight="800" fill="#0F172A">{quotaUsed}</text>
          <text x="46" y="56" textAnchor="middle" fontSize="11" fontWeight="700" fill="#64748B">/ {quotaTotal}</text>
        </svg>

        <div className="col" style={{ gap: 6, flex: 1 }}>
          <span style={{ fontSize: 22, fontWeight: 800, color: "var(--primary)" }}>Còn {quotaRemaining} lượt</span>
          <span className="small muted">trong kỳ tháng dương lịch</span>
          <span className="pill ok" style={{ alignSelf: "flex-start" }}>
            <Icon name="check" size={12} /> Video đã tạo vẫn xem được
          </span>
        </div>
      </div>

      {/* Top-up */}
      <div className="card col" style={{ gap: 12 }}>
        <div className="row" style={{ gap: 8 }}>
          <IconBadge name="sparkle" tone="accent" size={32} />
          <h2>Mua thêm lượt</h2>
        </div>
        <div className="col" style={{ gap: 8 }}>
          {(["ADDON", "MONTHLY"] as const).map((plan) => (
            <button
              key={plan}
              type="button"
              className="card row"
              style={{
                justifyContent: "space-between",
                padding: "12px 14px",
                borderColor: selectedPlan === plan ? "var(--primary)" : "var(--line)",
                background: selectedPlan === plan ? "var(--primary-50)" : "#FFFFFF",
                cursor: "pointer",
                textAlign: "left",
                boxShadow: selectedPlan === plan ? "0 0 0 3px var(--primary-100)" : "none",
              }}
              onClick={() => setSelectedPlan(plan)}
            >
              <div className="col" style={{ gap: 3 }}>
                <span style={{ fontWeight: 800, fontSize: 15 }}>{plan === "ADDON" ? "Gói bổ sung" : "Gói theo tháng"}</span>
                <span className="tiny muted">{plan === "ADDON" ? "Lượt mua thêm giữ qua kỳ đến khi dùng hết" : "Lượt định kỳ theo tháng dương lịch"}</span>
              </div>
              {selectedPlan === plan ? (
                <Icon name="check" size={20} color="var(--primary)" />
              ) : (
                <Icon name="arrow-right" size={18} color="#94A3B8" />
              )}
            </button>
          ))}
        </div>

        <div className="field">
          <label>Thanh toán qua</label>
          <div className="row" style={{ gap: 8 }}>
            {(["MoMo", "VNPAY"] as const).map((m) => (
              <button
                key={m}
                type="button"
                className={`btn${selectedMethod === m ? "" : " secondary"}`}
                style={{ flex: 1 }}
                onClick={() => setSelectedMethod(m)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          className="btn block"
          onClick={() => showToast(`Đã mở lựa chọn ${selectedPlan === "ADDON" ? "Gói bổ sung" : "Gói theo tháng"} qua ${selectedMethod}.`, "info")}
        >
          <Icon name="arrow-right" size={18} color="#FFFFFF" /> Xem lựa chọn
        </button>
      </div>

      {/* UI07 video job list */}
      <div className="card col" style={{ gap: 12 }}>
        <div className="row" style={{ gap: 8 }}>
          <IconBadge name="video" tone="primary" size={32} />
          <h2>Danh sách video</h2>
        </div>
        <div className="col" style={{ gap: 8 }}>
          {UI07_VIDEO_JOBS.map((job) => {
            const meta = jobIconMap[job.badgeTone ?? ""] ?? jobIconMap[""];
            return (
              <div key={job.id} className="card row" style={{ padding: 12, gap: 12, alignItems: "flex-start" }}>
                <IconBadge name={meta.icon} tone={meta.tone} size={40} />
                <div className="col" style={{ gap: 4, flex: 1, minWidth: 0 }}>
                  <span style={{ fontWeight: 800, fontSize: 14, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{job.title}</span>
                  <span className="tiny muted">{job.date}</span>
                  <span className={`pill ${job.badgeTone ?? ""}`} style={{ alignSelf: "flex-start", fontSize: 11.5 }}>
                    {job.status}
                  </span>
                </div>
                {job.actionLabel && (
                  <button
                    type="button"
                    className={`btn small${job.actionLabel === "Xem video" ? "" : " secondary"}`}
                    onClick={() => job.actionLabel === "Xem video" ? navigate("/p08-video-and-activities") : navigate("/p06-story-review")}
                  >
                    {job.actionLabel}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
