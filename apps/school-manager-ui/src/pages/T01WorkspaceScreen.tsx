import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTeacher } from "../context/TeacherContext";
import { TeacherLessonCard } from "../data/mockTeacherData";
import { Icon, IconName } from "../components/Icon";
import { topicIconName, topicTone } from "../components/PublicLibraryModal";

export function PageHead({
  title,
  hint,
  right,
}: {
  title: string;
  hint?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="tw-row tw-between tw-wrap">
      <div>
        <h1 className="tw-title">{title}</h1>
        {hint && (
          <p className="tw-sub" style={{ marginTop: 4 }}>
            {hint}
          </p>
        )}
      </div>
      {right}
    </div>
  );
}

export function IconTile({
  name,
  tone = "",
}: {
  name: IconName;
  tone?: "" | "is-amber" | "is-mint" | "is-rose";
}) {
  return (
    <span className={`tw-ico ${tone}`} aria-hidden="true">
      <Icon name={name} size={22} />
    </span>
  );
}

export function Stepper({
  steps,
  current,
  onPick,
}: {
  steps: string[];
  current: number;
  onPick: (i: number) => void;
}) {
  return (
    <div className="tw-steps" role="tablist" aria-label="Các bước">
      {steps.map((s, i) => (
        <button
          key={s}
          type="button"
          role="tab"
          aria-selected={i === current}
          className={"tw-step" + (i === current ? " is-on" : i < current ? " is-done" : "")}
          onClick={() => onPick(i)}
        >
          <b>{i < current ? <Icon name="check" size={14} /> : i + 1}</b>
          {s}
        </button>
      ))}
    </div>
  );
}

export function Toggle({
  on,
  onChange,
  label,
}: {
  on: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      className={"tw-switch" + (on ? " is-on" : "")}
      onClick={() => onChange(!on)}
    />
  );
}

export function T01LessonWorkspacePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    assignedClasses,
    activeClassId,
    setActiveClassId,
    lessons,
    publicTemplates,
    roster,
    createNewLessonVersion,
    useLessonForOccurrence,
    setArchiveModalTarget,
    teacherNotifications,
    markTeacherNotifRead,
    markAllTeacherNotifsRead,
    orgIncludedQuota,
    orgTopupQuota,
    orgQuotaLedger,
    presentationAuditLog,
    baseClassSlots,
    addonClassSlots,
    usedClassSlots,
    purchaseAddonClassSlot,
    theme,
    logout,
  } = useTeacher();

  const [libSearch, setLibSearch] = useState("");
  const [libAgeFilter, setLibAgeFilter] = useState("Tất cả độ tuổi");
  const [libTopicFilter, setLibTopicFilter] = useState("Tất cả chủ đề");
  const [previewTemplate, setPreviewTemplate] = useState<TeacherLessonCard | null>(null);

  const view = new URLSearchParams(location.search).get("view");
  const activeClass = assignedClasses.find((c) => c.id === activeClassId) || assignedClasses[0];
  const unread = teacherNotifications.filter((n) => n.unread).length;
  const quota = orgIncludedQuota + orgTopupQuota;

  /* ── Mục: Thư viện giáo án công khai (?view=library) ── */
  if (view === "library") {
    const mergedMap = new Map<string, TeacherLessonCard>();
    publicTemplates.forEach((t) => mergedMap.set(t.title, t));
    lessons
      .filter((l) => l.visibility === "Công khai")
      .forEach((l) => {
        if (!mergedMap.has(l.title)) mergedMap.set(l.title, l);
      });
    const libraryItems = Array.from(mergedMap.values());
    const allTopics = Array.from(new Set(libraryItems.map((l) => l.topic)));

    const filteredLessons = libraryItems.filter((l) => {
      const q = libSearch.trim().toLowerCase();
      const matchText =
        !q ||
        l.title.toLowerCase().includes(q) ||
        l.topic.toLowerCase().includes(q) ||
        l.description.toLowerCase().includes(q) ||
        l.objectives.toLowerCase().includes(q);
      const matchTopic = libTopicFilter === "Tất cả chủ đề" || l.topic === libTopicFilter;
      const matchAge =
        libAgeFilter === "Tất cả độ tuổi" ||
        l.ageBand.toLowerCase().includes(libAgeFilter.slice(0, 3).toLowerCase());
      return matchText && matchTopic && matchAge;
    });

    return (
      <div className="tw-page">
        <PageHead
          title="Thư viện giáo án công khai"
          hint="Khám phá các giáo án mẫu đã được kiểm duyệt an toàn sư phạm, xem chi tiết hoạt động và nạp trực tiếp vào trình soạn thảo của cô."
          right={
            <button
              type="button"
              className="tw-btn"
              onClick={() => navigate("/t02-lesson-authoring")}
            >
              <Icon name="book" size={18} /> Mở Quản lý giáo án
            </button>
          }
        />

        <div className="tw-card tw-row tw-wrap" style={{ padding: 16, gap: 12 }}>
          <input
            className="tw-input"
            style={{ flex: 2, minWidth: 220 }}
            placeholder="Tìm kiếm giáo án mẫu theo tên, chủ đề, mục tiêu..."
            value={libSearch}
            onChange={(e) => setLibSearch(e.target.value)}
            aria-label="Tìm kiếm giáo án mẫu"
          />
          <select
            className="tw-input"
            style={{ width: 195 }}
            value={libAgeFilter}
            onChange={(e) => setLibAgeFilter(e.target.value)}
            aria-label="Lọc theo độ tuổi"
          >
            <option>Tất cả độ tuổi</option>
            <option>3–4 tuổi (36–47 tháng)</option>
            <option>4–5 tuổi (48–59 tháng)</option>
            <option>5–6 tuổi (60–83 tháng)</option>
          </select>
          <select
            className="tw-input"
            style={{ width: 185 }}
            value={libTopicFilter}
            onChange={(e) => setLibTopicFilter(e.target.value)}
            aria-label="Lọc theo chủ đề"
          >
            <option>Tất cả chủ đề</option>
            {allTopics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="tw-row tw-between tw-wrap">
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
            Danh mục giáo án mẫu đã kiểm duyệt ({filteredLessons.length})
          </h2>
          <span className="tw-chip is-mint">
            <Icon name="shield" size={14} /> Đạt chuẩn an toàn nội dung mầm non
          </span>
        </div>

        <div className="tw-grid-2">
          {filteredLessons.map((tpl) => (
            <div
              key={tpl.id}
              className="tw-card"
              style={{ display: "flex", flexDirection: "column", gap: 14 }}
            >
              <div className="tw-row tw-between">
                <div className="tw-row" style={{ gap: 12 }}>
                  <IconTile name={topicIconName(tpl.topic)} tone={topicTone(tpl.topic)} />
                  <div>
                    <h3 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>{tpl.title}</h3>
                    <div className="tw-meta" style={{ fontSize: 13 }}>
                      {tpl.authorName ?? "Thư viện Sketch2Life"} · {tpl.version}
                    </div>
                  </div>
                </div>
                <span className="tw-chip is-mint">Đã duyệt công khai</span>
              </div>

              <div className="tw-row tw-wrap" style={{ gap: 8 }}>
                <span className="tw-chip">{tpl.topic}</span>
                <span className="tw-chip is-mint">{tpl.ageBand}</span>
                <span className="tw-chip is-amber">{tpl.activities.length} hoạt động</span>
              </div>

              <p style={{ fontSize: 15, lineHeight: 1.55 }}>{tpl.description}</p>

              <div className="tw-item is-sky" style={{ padding: "11px 14px" }}>
                <div style={{ fontSize: 14, lineHeight: 1.5 }}>
                  <strong className="tw-strong">Mục tiêu bài học:</strong> {tpl.objectives}
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div className="tw-strong" style={{ fontSize: 13.5 }}>
                  Danh sách hoạt động ({tpl.activities.length}):
                </div>
                {tpl.activities.map((act, idx) => (
                  <div key={act + idx} className="tw-meta" style={{ fontSize: 13.5 }}>
                    • {act}
                  </div>
                ))}
              </div>

              <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 6 }}>
                <button
                  type="button"
                  className="tw-btn is-ghost is-sm"
                  onClick={() => setPreviewTemplate(tpl)}
                >
                  <Icon name="eye" size={16} /> Xem chi tiết
                </button>
                <button
                  type="button"
                  className="tw-btn is-sm"
                  onClick={() =>
                    navigate("/t02-lesson-authoring", {
                      state: { preloadTemplate: tpl },
                    })
                  }
                >
                  <Icon name="plus" size={16} /> Nạp mẫu vào Giáo án
                </button>
              </div>
            </div>
          ))}
        </div>

        {filteredLessons.length === 0 && (
          <div className="tw-card" style={{ textAlign: "center", padding: 32 }}>
            <p className="tw-sub" style={{ margin: "0 auto" }}>
              Không tìm thấy giáo án mẫu khớp bộ lọc hiện tại.
            </p>
          </div>
        )}

        {previewTemplate && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="tpl-preview-title"
            className="tw-modal-backdrop"
            onClick={() => setPreviewTemplate(null)}
          >
            <div className="tw-modal is-lg" onClick={(e) => e.stopPropagation()}>
              <div className="tw-row tw-between">
                <div className="tw-row">
                  <IconTile
                    name={topicIconName(previewTemplate.topic)}
                    tone={topicTone(previewTemplate.topic)}
                  />
                  <div>
                    <h2 id="tpl-preview-title" style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>
                      {previewTemplate.title}
                    </h2>
                    <div className="tw-meta">
                      {previewTemplate.authorName ?? "Thư viện Sketch2Life"} · {previewTemplate.version}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  className="tw-btn is-ghost is-sm"
                  onClick={() => setPreviewTemplate(null)}
                >
                  <Icon name="close" size={16} /> Đóng
                </button>
              </div>

              <div className="tw-row tw-wrap">
                <span className="tw-chip">{previewTemplate.topic}</span>
                <span className="tw-chip is-mint">{previewTemplate.ageBand}</span>
                <span className="tw-chip is-amber">{previewTemplate.activities.length} hoạt động</span>
              </div>

              <div className="tw-item is-sky" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Mô tả chi tiết bài học</h3>
                <p style={{ fontSize: 15, lineHeight: 1.55 }}>{previewTemplate.description}</p>
              </div>

              <div className="tw-item is-mint" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Mục tiêu sư phạm</h3>
                <p style={{ fontSize: 15, lineHeight: 1.55 }}>{previewTemplate.objectives}</p>
              </div>

              <div className="tw-item" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
                  Danh sách hoạt động ({previewTemplate.activities.length})
                </h3>
                {previewTemplate.activities.map((a, idx) => (
                  <div key={a + idx} className="tw-row" style={{ alignItems: "flex-start" }}>
                    <span className="tw-chip is-mint">Hoạt động {idx + 1}</span>
                    <span style={{ fontSize: 15 }}>{a}</span>
                  </div>
                ))}
              </div>

              <div className="tw-row tw-between tw-wrap">
                <button
                  type="button"
                  className="tw-btn is-ghost"
                  onClick={() => setPreviewTemplate(null)}
                >
                  Đóng xem trước
                </button>
                <button
                  type="button"
                  className="tw-btn"
                  onClick={() => {
                    const chosen = previewTemplate;
                    setPreviewTemplate(null);
                    navigate("/t02-lesson-authoring", { state: { preloadTemplate: chosen } });
                  }}
                >
                  <Icon name="plus" size={18} /> Nạp mẫu vào Giáo án để chỉnh sửa
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  /* ── Mục: Lịch sử & Báo cáo (?view=history) ── */
  if (view === "history") {
    return (
      <div className="tw-page">
        <PageHead
          title="Lịch sử & Báo cáo lớp học"
          hint="Theo dõi sổ cái lượt tạo video mẫu của trường và nhật ký xác nhận trình chiếu tại lớp."
        />
        <div className="tw-grid-2">
          <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile name="video" tone="is-mint" />
                <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>Sổ cái lượt tạo video mẫu</h2>
              </div>
              <span className="tw-chip is-mint">Tỷ lệ thành công 96%</span>
            </div>
            {orgQuotaLedger.map((q) => (
              <div key={q.id} className="tw-row tw-between tw-item is-sky" style={{ padding: 14 }}>
                <div>
                  <div className="tw-strong" style={{ fontSize: 14.5 }}>{q.runTitle}</div>
                  <div className="tw-meta" style={{ fontSize: 13 }}>
                    {q.bucket} · {q.date}
                  </div>
                  <div className="tw-meta" style={{ fontSize: 12.5, marginTop: 2 }}>{q.note}</div>
                </div>
                <span className={"tw-chip " + (q.delta.startsWith("0") ? "is-gray" : "is-amber")}>
                  {q.delta}
                </span>
              </div>
            ))}
          </div>

          <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile name="play" tone="is-amber" />
                <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>Nhật ký trình chiếu tại lớp (BR-37)</h2>
              </div>
              <span className="tw-chip">{presentationAuditLog.length} buổi chiếu</span>
            </div>
            {presentationAuditLog.length === 0 && (
              <p className="tw-sub">Chưa có buổi chiếu nào được ghi nhận.</p>
            )}
            {presentationAuditLog.map((a) => (
              <div key={a.id} className="tw-row tw-between tw-item is-mint" style={{ padding: 14 }}>
                <div>
                  <div className="tw-strong" style={{ fontSize: 14.5 }}>{a.className}</div>
                  <div className="tw-meta" style={{ fontSize: 13 }}>
                    {a.teacherName} · Phiên {a.occurrenceId} · Kịch bản #{a.scriptRevision}
                  </div>
                </div>
                <span className="tw-chip">{a.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  /* ── Mục: Thông báo hệ thống (?view=feedback) ── */
  if (view === "feedback") {
    return (
      <div className="tw-page">
        <PageHead
          title="Thông báo & Nhắc việc hệ thống"
          hint="Cập nhật trạng thái duyệt giáo án, quyền chia sẻ nội bộ và tiến trình tạo video mẫu."
          right={
            unread > 0 ? (
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={markAllTeacherNotifsRead}
              >
                <Icon name="check" size={16} /> Đánh dấu tất cả đã đọc
              </button>
            ) : undefined
          }
        />
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="tw-row tw-between">
            <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>
              Hộp thư thông báo ({teacherNotifications.length})
            </h2>
            {unread > 0 && <span className="tw-chip is-rose">{unread} chưa đọc</span>}
          </div>
          {teacherNotifications.map((n) => (
            <button
              key={n.id}
              type="button"
              className={"tw-item is-lift tw-row tw-between" + (n.unread ? " is-sky" : "")}
              style={{
                textAlign: "left",
                padding: 16,
                borderRadius: 18,
                fontFamily: "inherit",
              }}
              onClick={() => {
                markTeacherNotifRead(n.id);
                navigate(n.targetRoute);
              }}
            >
              <div className="tw-row" style={{ gap: 14 }}>
                <IconTile
                  name={
                    n.category === "VIDEO_JOB"
                      ? "video"
                      : n.category === "OCCURRENCE"
                      ? "book"
                      : "sparkle"
                  }
                  tone={n.unread ? "is-amber" : "is-mint"}
                />
                <div>
                  <div className="tw-strong" style={{ fontSize: 15 }}>{n.title}</div>
                  <div className="tw-meta" style={{ marginTop: 2 }}>{n.body}</div>
                </div>
              </div>
              <div className="tw-row" style={{ gap: 8 }}>
                <span className="tw-chip is-gray">{n.timestamp}</span>
                {n.unread && <span className="tw-chip is-rose">Mới</span>}
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  /* ── Mục: Hồ sơ cá nhân (?view=settings) ── */
  if (view === "settings") {
    return (
      <div className="tw-page">
        <PageHead
          title="Hồ sơ cá nhân"
          hint={"Thông tin giáo viên, hạn mức slot lớp học và các lớp đang phụ\u00A0trách."}
          right={
            <button
              type="button"
              className="tw-btn"
              onClick={() => navigate("/t08-settings")}
            >
              <Icon name="settings" size={18} /> Mở Cài đặt tài khoản &amp; Giao diện
            </button>
          }
        />

        <div className="tw-grid-2">
          <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="tw-row" style={{ gap: 16 }}>
              <span className="tw-avatar is-sky" style={{ width: 72, height: 72 }} aria-hidden="true">
                <Icon name="user" size={34} />
              </span>
              <div>
                <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Cô Nguyễn Phương Thảo</h2>
                <div className="tw-meta" style={{ marginTop: 2 }}>
                  Giáo viên chủ nhiệm · Trường Mầm non Ánh Dương
                </div>
                <div className="tw-row tw-wrap" style={{ marginTop: 8, gap: 8 }}>
                  <span className="tw-chip is-mint">Tài khoản Tổ chức độc lập (BR-03)</span>
                  <span className="tw-chip is-gray">
                    Giao diện: {theme === "dark" ? "Chế độ Tối" : "Chế độ Sáng"}
                  </span>
                </div>
              </div>
            </div>

            <div className="tw-item is-sky tw-row tw-between tw-wrap" style={{ padding: 14 }}>
              <div>
                <div className="tw-strong" style={{ fontSize: 15 }}>Slot lớp học của trường</div>
                <div className="tw-meta" style={{ fontSize: 13 }}>
                  Gói cơ bản {baseClassSlots} slot + Mua thêm {addonClassSlots} slot
                </div>
              </div>
              <div className="tw-row">
                <span className="tw-chip">
                  Đang dùng {usedClassSlots}/{baseClassSlots + addonClassSlots} slot
                </span>
                <button
                  type="button"
                  className="tw-btn is-amber is-sm"
                  onClick={purchaseAddonClassSlot}
                >
                  <Icon name="plus" size={15} /> Mua thêm slot
                </button>
              </div>
            </div>

            <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 4 }}>
              <button
                type="button"
                className="tw-btn is-ghost"
                onClick={() => navigate("/t08-settings")}
              >
                <Icon name="settings" size={18} /> Cài đặt tài khoản &amp; Giao diện
              </button>
              <button
                type="button"
                className="tw-btn is-danger"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
              >
                <Icon name="log-out" size={18} /> Đăng xuất
              </button>
            </div>
          </div>

          <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile name="users" tone="is-mint" />
                <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>
                  Danh sách lớp được phân công (RBAC)
                </h2>
              </div>
              <span className="tw-chip">{assignedClasses.length} lớp</span>
            </div>

            {assignedClasses.map((c) => (
              <div key={c.id} className="tw-row tw-between tw-item" style={{ padding: 14 }}>
                <div>
                  <div className="tw-strong" style={{ fontSize: 15.5 }}>{c.className}</div>
                  <div className="tw-meta" style={{ fontSize: 13 }}>
                    {c.studentCount} học sinh · {c.ageRangeLabel} · Phụ trách: {c.ownerTeacher}
                  </div>
                </div>
                <div className="tw-row" style={{ gap: 8 }}>
                  <span
                    className={
                      "tw-chip " +
                      (c.rbacState === "ACTIVE"
                        ? "is-mint"
                        : c.rbacState === "UNASSIGNED_403"
                        ? "is-rose"
                        : "is-amber")
                    }
                  >
                    {c.rbacState === "ACTIVE"
                      ? "Đang phụ trách"
                      : c.rbacState === "TRANSFER_PENDING"
                      ? "Chờ bàn giao"
                      : c.rbacState === "SUSPENDED_READONLY"
                      ? "Chỉ xem"
                      : "Không có quyền"}
                  </span>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    onClick={() => {
                      setActiveClassId(c.id);
                      navigate(`/t05-classes-and-children/${c.id}`);
                    }}
                  >
                    Mở lớp <Icon name="arrow-right" size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  /* ── Mục mặc định: Dashboard Tổng quan ── */
  const kpis: {
    icon: IconName;
    tone: "" | "is-amber" | "is-mint" | "is-rose";
    num: number;
    label: string;
  }[] = [
    { icon: "users", tone: "", num: assignedClasses.length, label: "Lớp học phụ trách" },
    {
      icon: "heart",
      tone: "is-rose",
      num: roster.filter((r) => r.enrollmentStatus === "ACTIVE").length,
      label: "Học sinh đang học",
    },
    { icon: "book", tone: "is-amber", num: lessons.length, label: "Giáo án của tôi" },
    { icon: "video", tone: "is-mint", num: quota, label: "Lượt video mẫu còn lại" },
  ];

  return (
    <div className="tw-page">
      <div className="tw-card is-sky tw-row" style={{ gap: 20, padding: 26, flexWrap: "wrap" }}>
        <span
          className="tw-avatar tw-float"
          style={{
            width: 84,
            height: 84,
            background: "linear-gradient(145deg, #1F2DE6, #1B25C5)",
            color: "#FFFFFF",
          }}
          aria-hidden="true"
        >
          <Icon name="palette" size={40} color="#FFFFFF" />
        </span>
        <div style={{ flex: 1, minWidth: 240 }}>
          <h1 className="tw-title" style={{ fontSize: 32 }}>
            Xin chào, Cô Thảo!
          </h1>
          <p className="tw-sub" style={{ marginTop: 4 }}>
            Quản lý lớp học, biên soạn giáo án, trình chiếu bảng vẽ AI Assisted 16:9 và tạo video mẫu cho lớp.
          </p>
          <div className="tw-row tw-wrap" style={{ gap: 8, marginTop: 10 }}>
            <span className="tw-chip is-mint">Trường Mầm non Ánh Dương</span>
            <span className="tw-chip">{activeClass.className}</span>
          </div>
        </div>
        <div className="tw-row tw-wrap">
          <button
            type="button"
            className="tw-btn"
            onClick={() =>
              navigate("/t02-lesson-authoring", { state: { openCreateModal: true } })
            }
          >
            <Icon name="plus" size={18} /> Tạo giáo án mới
          </button>
          <button
            type="button"
            className="tw-btn is-ghost"
            onClick={() =>
              navigate("/t02-lesson-authoring", { state: { openUploadModal: true } })
            }
          >
            <Icon name="upload" size={18} /> Import tài liệu
          </button>
        </div>
      </div>

      <div className="tw-grid-4">
        {kpis.map((k) => (
          <div key={k.label} className="tw-kpi">
            <IconTile name={k.icon} tone={k.tone} />
            <div>
              <div className="tw-kpi-num">{k.num}</div>
              <div className="tw-kpi-lbl">{k.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="tw-grid-2" style={{ gridTemplateColumns: "1.2fr 1fr" }}>
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="tw-row tw-between">
            <div className="tw-row">
              <IconTile name="sparkle" tone="is-amber" />
              <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>Hoạt động gần đây</h2>
            </div>
            {unread > 0 && <span className="tw-chip is-rose">{unread} thông báo mới</span>}
          </div>
          {teacherNotifications.slice(0, 4).map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => {
                markTeacherNotifRead(n.id);
                navigate(n.targetRoute);
              }}
              className={"tw-item is-lift tw-row" + (n.unread ? " is-sky" : "")}
              style={{
                textAlign: "left",
                padding: "11px 14px",
                borderRadius: 16,
                fontFamily: "inherit",
              }}
            >
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: n.unread ? "#1F2DE6" : "#94A3B8",
                  flexShrink: 0,
                }}
              />
              <span className="tw-strong" style={{ flex: 1, fontSize: 14 }}>
                {n.title}
              </span>
              <span className="tw-chip is-gray">{n.timestamp}</span>
            </button>
          ))}
        </div>

        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="tw-row tw-between">
            <div className="tw-row">
              <IconTile name="users" tone="is-mint" />
              <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>Lớp học của tôi</h2>
            </div>
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() => navigate("/t05-classes-and-children")}
            >
              Xem tất cả lớp
            </button>
          </div>
          {assignedClasses.map((c) => (
            <button
              key={c.id}
              type="button"
              className={"tw-item is-mint is-lift tw-row tw-between" + (c.id === activeClass.id ? " is-selected" : "")}
              style={{
                padding: 14,
                borderRadius: 18,
                fontFamily: "inherit",
                textAlign: "left",
              }}
              onClick={() => {
                setActiveClassId(c.id);
                navigate(`/t05-classes-and-children/${c.id}`);
              }}
            >
              <div>
                <div className="tw-strong" style={{ fontSize: 16 }}>{c.className}</div>
                <div className="tw-meta" style={{ fontSize: 13 }}>
                  {c.studentCount} học sinh · {c.ageRangeLabel}
                </div>
              </div>
              <span className="tw-chip is-mint">
                Học sinh <Icon name="arrow-right" size={14} />
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div className="tw-row tw-between tw-wrap">
          <div className="tw-row">
            <IconTile name="book" />
            <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>Danh sách giáo án của tôi</h2>
          </div>
          <div className="tw-row tw-wrap">
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() => navigate("/t02-lesson-authoring")}
            >
              Quản lý tất cả
            </button>
            <button
              type="button"
              className="tw-btn is-sm"
              onClick={() =>
                navigate("/t02-lesson-authoring", { state: { openCreateModal: true } })
              }
            >
              <Icon name="plus" size={16} /> Tạo giáo án
            </button>
          </div>
        </div>

        <div className="tw-grid-2">
          {lessons.map((l) => (
            <div
              key={l.id}
              className="tw-item tw-row"
              style={{ padding: 16, borderRadius: 20, gap: 14, alignItems: "flex-start" }}
            >
              <IconTile name={topicIconName(l.topic)} tone={topicTone(l.topic)} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>{l.title}</h3>
                <div className="tw-meta" style={{ fontSize: 13, marginTop: 3 }}>
                  {l.version} · {l.activities.length} hoạt động · Cập nhật {l.updatedAt}
                </div>
                <div className="tw-row tw-wrap" style={{ gap: 6, marginTop: 8 }}>
                  <span
                    className={
                      "tw-chip " +
                      (l.visibility === "Công khai"
                        ? "is-mint"
                        : l.visibility === "Trong trường"
                        ? ""
                        : "is-amber")
                    }
                  >
                    {l.visibility === "Riêng tư" ? "Bản nháp riêng tư" : l.visibility}
                  </span>
                  <span className="tw-chip is-gray">{l.ageBand}</span>
                </div>
              </div>
              <div className="tw-row" style={{ flexDirection: "column", gap: 6, alignItems: "stretch" }}>
                <button
                  type="button"
                  className="tw-btn is-sm"
                  onClick={() => {
                    useLessonForOccurrence(l.id);
                    navigate("/t02-lesson-authoring");
                  }}
                >
                  Mở giáo án
                </button>
                <div className="tw-row" style={{ gap: 6, justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    title="Tạo phiên bản mới"
                    aria-label={`Tạo phiên bản mới cho ${l.title}`}
                    onClick={() => createNewLessonVersion(l.id)}
                  >
                    <Icon name="refresh" size={15} />
                  </button>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    title="Xóa giáo án"
                    aria-label={`Xóa giáo án ${l.title}`}
                    onClick={() => setArchiveModalTarget(l)}
                  >
                    <Icon name="trash" size={15} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
