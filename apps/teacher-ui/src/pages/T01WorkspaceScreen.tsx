import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTeacher } from "../context/TeacherContext";
import { TeacherLessonCard } from "../data/mockTeacherData";
import { Icon, IconName } from "../components/Icon";
import { topicIconName, topicTone } from "../components/PublicLibraryModal";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  isLocalPreview,
  type Be1Class,
  type LessonSummary,
} from "../../../shared/backendApi";

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
    useLessonForOccurrence,
    teacherNotifications,
    markTeacherNotifRead,
    markAllTeacherNotifsRead,
    pinnedLessonTitle,
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
  const [apiSnapshot, setApiSnapshot] = useState<{ classes: Be1Class[]; lessons: LessonSummary[] } | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(false);
  const [apiReload, setApiReload] = useState(0);

  useEffect(() => {
    if (isLocalPreview()) return;
    let active = true;
    const organizationId = configuredOrganizationId();
    if (!hasFirebaseAuthBridge()) {
      setApiError("Chưa có Firebase ID token để gọi API.");
      return () => { active = false; };
    }
    if (!organizationId) {
      setApiError("Chưa cấu hình organization_id để gọi các API theo phạm vi trường.");
      return () => { active = false; };
    }
    setApiLoading(true);
    setApiError(null);
    Promise.all([
      backendApi.assignments(organizationId),
      backendApi.classes(organizationId),
      backendApi.lessons(organizationId),
    ])
      .then(([identity, classPage, lessonPage]) => {
        if (!active) return;
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản không có assignment Teacher trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        setApiSnapshot({ classes: classPage.items, lessons: lessonPage.items });
      })
      .catch((cause: unknown) => { if (active) setApiError(backendMessage(cause)); })
      .finally(() => { if (active) setApiLoading(false); });
    return () => { active = false; };
  }, [apiReload]);

  const view = new URLSearchParams(location.search).get("view");
  const activeClass = assignedClasses.find((c) => c.id === activeClassId) || assignedClasses[0];
  const unread = teacherNotifications.filter((n) => n.unread).length;
  const quota = orgIncludedQuota + orgTopupQuota;

  if (!isLocalPreview()) {
    return (
      <div className="tw-page">
        <PageHead title="Không gian giáo viên" hint="Lớp và giáo án trong phạm vi được backend cấp cho tài khoản." right={<button type="button" className="tw-btn" onClick={() => setApiReload((value) => value + 1)}>Tải lại</button>} />
        <BackendModeNotice roleLabel="Giáo viên" />
        {apiLoading && <BackendNotice title="Đang tải dữ liệu">Đang xác thực assignment và tải lớp, giáo án.</BackendNotice>}
        {apiError && <BackendNotice title="Không tải được dữ liệu" tone="error">{apiError}</BackendNotice>}
        {apiSnapshot && <>
          <div className="tw-grid-2">
            <section className="tw-card">
              <h2 className="tw-h2">Lớp được phân công</h2>
              {apiSnapshot.classes.length === 0 && <p className="tw-sub">Tài khoản chưa có lớp trong phạm vi này.</p>}
              {apiSnapshot.classes.map((item) => <div className="tw-item" key={item.class_id}>
                <strong>{item.display_name}</strong><span className="tw-meta">{item.state}</span>
              </div>)}
            </section>
            <section className="tw-card">
              <h2 className="tw-h2">Giáo án</h2>
              {apiSnapshot.lessons.length === 0 && <p className="tw-sub">Chưa có giáo án trong tổ chức.</p>}
              {apiSnapshot.lessons.map((item) => <div className="tw-item" key={item.lesson_id}>
                <strong>{item.title}</strong>
                <span className="tw-meta">{item.topic} · bản {item.current_version_no} · {item.review_state} · {item.activity_count} hoạt động</span>
              </div>)}
            </section>
          </div>
          <BackendNotice title="Một số màn Teacher chưa có API sản phẩm tương ứng" tone="warn">
            Story/video, AI Sketch Deck và thao tác upload chưa được nối vào API bền vững. BE1 có session lớp, nhưng luồng lobby/canvas không thuộc SRS hiện hành.
          </BackendNotice>
        </>}
      </div>
    );
  }

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
          hint="Giáo án mẫu đã kiểm duyệt · xem chi tiết hoặc dùng làm bài mới."
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
            placeholder="Tìm giáo án mẫu"
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
            Giáo án mẫu ({filteredLessons.length})
          </h2>
          <span className="tw-chip is-mint">
            <Icon name="shield" size={14} /> Đã kiểm duyệt
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

                  </div>
                </div>
              </div>

              <div className="tw-row tw-wrap" style={{ gap: 8 }}>
                <span className="tw-chip">{tpl.topic}</span>
                <span className="tw-chip is-mint">{tpl.ageBand}</span>
                <span className="tw-chip is-amber">{tpl.activities.length} hoạt động</span>
              </div>

              <p
                className="tw-sub"
                style={{
                  margin: 0,
                  display: "-webkit-box",
                  WebkitBoxOrient: "vertical",
                  WebkitLineClamp: 2,
                  overflow: "hidden",
                }}
              >
                {tpl.description}
              </p>

              <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 6 }}>
                <button
                  type="button"
                  className="tw-btn is-ghost is-sm"
                  onClick={() => setPreviewTemplate(tpl)}
                >
                  <Icon name="eye" size={16} /> Chi tiết
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
                  <Icon name="plus" size={16} /> Dùng mẫu
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
                <h2 style={{ margin: 0, fontSize: 19, fontWeight: 700 }}>Lịch sử trình chiếu tại lớp</h2>
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
                  <span className="tw-chip is-mint">Tài khoản trường độc lập</span>
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
    num: number;
    label: string;
  }[] = [
    { num: assignedClasses.length, label: "Lớp phụ trách" },
    {
      num: roster.filter((r) => r.enrollmentStatus === "ACTIVE").length,
      label: "Trẻ đang học",
    },
    { num: lessons.length, label: "Giáo án" },
    { num: quota, label: "Lượt video còn lại" },
  ];
  const featuredLesson = lessons.find((lesson) => lesson.title === pinnedLessonTitle) || lessons[0];

  return (
    <div className="tw-page s2l-dashboard">
      <header className="s2l-dashboard-head">
        <div className="s2l-dashboard-heading">
          <h1>Chào Cô Thảo!</h1>
          <p>Quản lý lớp và chuẩn bị bài dạy từ một nơi.</p>
          <div className="s2l-dashboard-context">
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
            <Icon name="plus" size={18} /> Tạo giáo án
          </button>
          <button
            type="button"
            className="tw-btn is-ghost"
            onClick={() =>
              navigate("/t02-lesson-authoring", { state: { openUploadModal: true } })
            }
          >
            <Icon name="upload" size={18} /> Nhập tài liệu
          </button>
        </div>
      </header>

      <section className="s2l-dashboard-summary" aria-label="Tổng quan lớp và giáo án">
        {kpis.map((k) => (
          <div key={k.label} className="s2l-dashboard-summary-item">
            <span className="s2l-dashboard-summary-value">{k.num}</span>
            <span className="s2l-dashboard-summary-label">{k.label}</span>
          </div>
        ))}
      </section>

      {featuredLesson && (
        <section className="s2l-dashboard-feature">
          <div>
            <h2>Bài giảng đang chuẩn bị</h2>
            <strong>{featuredLesson.title}</strong>
            <p>{featuredLesson.version} · {featuredLesson.activities.length} hoạt động · Ghim cho {activeClass.className}</p>
          </div>
          <button
            type="button"
            className="tw-btn"
            onClick={() => {
              useLessonForOccurrence(featuredLesson.id);
              navigate("/t02-lesson-authoring");
            }}
          >
            Mở giáo án <Icon name="arrow-right" size={16} />
          </button>
        </section>
      )}

      <div className="s2l-dashboard-grid is-main">
        <section className="s2l-dashboard-panel">
          <div className="s2l-dashboard-panel-head">
            <div>
              <h2>Lớp của tôi</h2>
              <p>Mở lớp để xem học sinh và hoạt động.</p>
            </div>
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() => navigate("/t05-classes-and-children")}
            >
              Tất cả lớp
            </button>
          </div>
          <div className="s2l-dashboard-list">
          {assignedClasses.length === 0 && <div className="s2l-dashboard-empty">Chưa có lớp được phân công.</div>}
          {assignedClasses.slice(0, 4).map((c) => (
            <button
              key={c.id}
              type="button"
              className="s2l-dashboard-row"
              onClick={() => {
                setActiveClassId(c.id);
                navigate(`/t05-classes-and-children/${c.id}`);
              }}
            >
              <span className="s2l-dashboard-row-icon is-mint" aria-hidden="true"><Icon name="users" size={16} /></span>
              <span className="s2l-dashboard-row-main">
                <span className="s2l-dashboard-row-title">{c.className}</span>
                <span className="s2l-dashboard-row-sub">{c.studentCount} học sinh · {c.ageRangeLabel}</span>
              </span>
              <span className="s2l-dashboard-row-value">Mở lớp <Icon name="arrow-right" size={13} /></span>
            </button>
          ))}
          </div>
        </section>

        <section className="s2l-dashboard-panel">
          <div className="s2l-dashboard-panel-head">
            <div>
              <h2>Hoạt động gần đây</h2>
              <p>{unread > 0 ? `${unread} thông báo chưa xem` : "Cập nhật lớp và giáo án"}</p>
            </div>
            <button type="button" className="tw-btn is-ghost is-sm" onClick={() => navigate("/t01-lesson-workspace?view=history")}>
              Lịch sử
            </button>
          </div>
          <div className="s2l-dashboard-list">
          {teacherNotifications.length === 0 && <div className="s2l-dashboard-empty">Chưa có hoạt động mới.</div>}
          {teacherNotifications.slice(0, 4).map((n) => (
            <button
              key={n.id}
              type="button"
              className="s2l-dashboard-row"
              onClick={() => { markTeacherNotifRead(n.id); navigate(n.targetRoute); }}
            >
              <span className="s2l-dashboard-row-icon" aria-hidden="true"><Icon name={n.unread ? "sparkle" : "check"} size={16} /></span>
              <span className="s2l-dashboard-row-main">
                <span className="s2l-dashboard-row-title">{n.title}</span>
                <span className="s2l-dashboard-row-sub">
                  {n.category === "FEEDBACK" ? "Có phản hồi mới" : n.category === "GRANT_CONSENT" ? "Cập nhật quyền chia sẻ" : n.category === "VIDEO_JOB" ? "Trạng thái video mẫu" : n.category === "CLASS_RBAC" ? "Cập nhật phân công lớp" : "Cập nhật bài dạy"}
                </span>
              </span>
              <span className="s2l-dashboard-row-value">{n.timestamp}</span>
            </button>
          ))}
          </div>
        </section>
      </div>

      <section className="s2l-dashboard-panel">
        <div className="s2l-dashboard-panel-head">
          <div>
            <h2>Giáo án gần đây</h2>
            <p>Bản nháp và giáo án đã chia sẻ.</p>
          </div>
          <button type="button" className="tw-btn is-ghost is-sm" onClick={() => navigate("/t02-lesson-authoring")}>
            Quản lý giáo án
          </button>
        </div>
        <div className="s2l-dashboard-list">
          {lessons.length === 0 && <div className="s2l-dashboard-empty">Chưa có giáo án. Tạo giáo án để bắt đầu.</div>}
          {lessons.filter((lesson) => lesson.id !== featuredLesson?.id).slice(0, 3).map((lesson) => (
            <button
              key={lesson.id}
              type="button"
              className="s2l-dashboard-row"
              onClick={() => { useLessonForOccurrence(lesson.id); navigate("/t02-lesson-authoring"); }}
            >
              <span className="s2l-dashboard-row-icon" aria-hidden="true"><Icon name={topicIconName(lesson.topic)} size={16} /></span>
              <span className="s2l-dashboard-row-main">
                <span className="s2l-dashboard-row-title">{lesson.title}</span>
                <span className="s2l-dashboard-row-sub">{lesson.version} · {lesson.activities.length} hoạt động · {lesson.updatedAt}</span>
              </span>
              <span className="s2l-dashboard-row-value">{lesson.visibility === "Riêng tư" ? "Bản nháp" : lesson.visibility} <Icon name="arrow-right" size={13} /></span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
