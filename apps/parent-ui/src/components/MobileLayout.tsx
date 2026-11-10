import React, { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useParent } from "../context/ParentContext";
import type { ChildGender } from "../data/mockParentData";
import { isLocalPreview } from "../../../shared/backendApi";
import { Icon } from "./Icon";
import type { IconName } from "./Icon";
import { Btn, ChildGenderField, Note, Sheet, Soft, StatusBarIcons } from "./Kit";

const TABS: { path: string; label: string; icon: IconName }[] = [
  { path: "/p01-lesson-library", label: "Trang chủ", icon: "nav-home" },
  { path: "/p09-history-feedback", label: "Lịch sử", icon: "nav-history" },
  { path: "/p12-video-quota", label: "Lượt tạo", icon: "nav-credits" },
  { path: "/p13-settings", label: "Cài đặt", icon: "nav-settings" },
];

const CAT_ICON: Record<string, { icon: IconName; tone: string }> = {
  REMINDER_144H: { icon: "clock", tone: "amber" },
  AUTOCLOSE_168H: { icon: "folder", tone: "" },
  TEACHER_INVITE: { icon: "shield", tone: "mint" },
  VIDEO_JOB: { icon: "video", tone: "violet" },
  QUOTA_PAYMENT: { icon: "star", tone: "amber" },
};

const QUICK_AGE_CHIPS = [
  { label: "3–4 tuổi", months: 42 },
  { label: "5–6 tuổi", months: 60 },
  { label: "7–8 tuổi", months: 90 },
  { label: "9–10 tuổi", months: 114 },
];

export function MobileLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    theme,
    profiles,
    storyProfileId,
    addProfile,
    ideaTranscript,
    activeSheet,
    setActiveSheet,
    startStoryDraft,
    scriptRevision,
    scenes,
    confirmScriptAndStartVideo,
    detectedSubject,
    setDetectedSubject,
    setSubjectConfirmed,
    quotaRemaining,
    hasActiveRun,
    videoJobMode,
    contextConfirmed,
    subjectConfirmed,
    scriptConfirmed,
    videoRegenCount,
    reportVideoUnsuitableAndRegenerate,
    triggerCancelIncompleteRun,
    landscapeVideo,
    setLandscapeVideo,
    notifications,
    markNotificationRead,
    markAllNotificationsRead,
    toast,
    showToast,
  } = useParent();

  const [subjectDraft, setSubjectDraft] = useState(detectedSubject);
  const [reason, setReason] = useState("Hình ảnh chưa giống bức vẽ của bé");
  const [newName, setNewName] = useState("");
  const [newGender, setNewGender] = useState<ChildGender | "">("");
  const [newMonths, setNewMonths] = useState("60");
  const [newAgeError, setNewAgeError] = useState("");
  const [newInterests, setNewInterests] = useState("Vẽ tranh, Khám phá thiên nhiên");
  const ageMonths = Number(newMonths);
  const isNewAgeValid = Number.isInteger(ageMonths) && ageMonths >= 36 && ageMonths <= 120;

  useEffect(() => {
    if (activeSheet === "EDIT_SUBJECT") {
      setSubjectDraft(detectedSubject);
    }
  }, [activeSheet, detectedSubject]);

  const path = location.pathname;

  useEffect(() => {
    if (path !== "/p08-video-and-activities" && landscapeVideo) {
      setLandscapeVideo(false);
    }
  }, [path, landscapeVideo, setLandscapeVideo]);

  const activeChild =
    profiles.find((p) => p.id === storyProfileId && !p.archived && p.deletionStatus !== "DELETED") ||
    profiles.find((p) => !p.archived && p.deletionStatus !== "DELETED") ||
    profiles[0];
  const hasContinuableRun = hasActiveRun && videoJobMode !== "DELETED" && videoJobMode !== "DELETE_PENDING";
  const acceptedJobInProgress = hasActiveRun && [
    "ADMISSION_PENDING",
    "QUEUED",
    "RUNNING",
    "SAFETY_VALIDATING",
    "RECONCILING",
  ].includes(videoJobMode);

  const isAuth = [
    "/p11-authentication",
    "/login",
    "/p14-password-recovery",
    "/p15-parent-registration",
  ].includes(path);
  const visibleTabs = isLocalPreview() ? TABS : TABS.filter((t) => t.path === "/p01-lesson-library" || t.path === "/p13-settings");
  const showTabs = !landscapeVideo && visibleTabs.some((t) => t.path === path);
  const createShortcutIndex = Math.floor(visibleTabs.length / 2);
  const close = () => setActiveSheet(null);
  const openStoryCapture = () => {
    if (hasContinuableRun) {
      showToast("Hãy hoàn tất câu chuyện đang thực hiện trước khi bắt đầu câu chuyện mới.", "info");
      navigate(videoJobMode === "READY" ? "/p08-video-and-activities" : "/p07-video-job-status");
      return;
    }
    if (quotaRemaining <= 0) {
      showToast("Bạn đã hết lượt tạo video. Bạn vẫn có thể chụp tranh và mua thêm lượt sau.", "warn");
    }
    startStoryDraft(true);
    navigate("/p04-capture-subject-confirmation");
  };

  const renderTab = (tab: (typeof TABS)[number]) => (
    <NavLink key={tab.path} to={tab.path} className={({ isActive }) => `tab ${isActive ? "on" : ""}`}>
      <span className="tab-ico">
        <Icon name={tab.icon} size={20} />
      </span>
      {tab.label}
    </NavLink>
  );

  const REASONS = [
    "Hình ảnh chưa giống bức vẽ của bé",
    "Nội dung chưa phù hợp với bé",
    "Giọng đọc hoặc phụ đề chưa đúng",
  ];

  return (
    <div className="stage" data-theme={theme}>
      <div
        className={`phone ${landscapeVideo ? "is-landscape" : ""}`}
        data-theme={theme}
        data-route={path.slice(1)}
        data-safe-area={isAuth ? "page" : "shell"}
      >
        <div className="phone-frame-bg" aria-hidden="true" />
        {/* Desktop phone mock only; the OS owns the status bar on a real mobile viewport. */}
        {!isAuth && !landscapeVideo && (
          <div className="statusbar" aria-hidden="true">
            <span>9:41</span>
            <StatusBarIcons />
          </div>
        )}
        <div className="scroll" key={path}>
          {!isAuth && !landscapeVideo && isLocalPreview() && (
            <div
              role="status"
              title="Dữ liệu minh họa; thao tác không ghi vào backend."
              style={{ margin: "10px 14px 0", padding: "7px 10px", border: "1px solid #f5d08a", borderRadius: 12, background: "#fff8e8", color: "#6b4800", fontSize: 12, lineHeight: 1.4, display: "flex", alignItems: "center", gap: 6 }}
            >
              <Icon name="info" size={14} /> Xem thử · không lưu dữ liệu
            </div>
          )}
          {children}
        </div>

        {showTabs && (
          <nav className="tabbar" aria-label="Điều hướng chính" data-tab-count={visibleTabs.length + 1}>
            {visibleTabs.slice(0, createShortcutIndex).map(renderTab)}
            <div className="tab-create-slot">
              <button
                type="button"
                className="tab-create-action"
                aria-label={hasContinuableRun ? "Tiếp tục câu chuyện đang thực hiện" : "Tạo câu chuyện mới bằng cách chụp tranh"}
                onClick={openStoryCapture}
              >
                <span className="tab-create-action__orb">
                  <Icon name={hasContinuableRun ? "video" : "nav-create"} size={25} strokeWidth={2.2} />
                </span>
                <span className="tab-create-action__label">{hasContinuableRun ? "Tiếp tục" : "Tạo"}</span>
              </button>
            </div>
            {visibleTabs.slice(createShortcutIndex).map(renderTab)}
          </nav>
        )}

        {toast && (
          <div className={`toast ${toast.kind}`} role="status" aria-live="polite">
            <Icon name={toast.kind === "ok" ? "check" : toast.kind === "err" || toast.kind === "warn" ? "alert" : "sparkle"} size={17} />
            {toast.text}
          </div>
        )}

        {activeSheet === "CONFIRM_SCRIPT" && (
          <Sheet title="Kiểm tra trước khi tạo video" onClose={close}>
            <div className="checklist" style={{ marginBottom: 4 }}>
              <div className="check done">
                <span className="ck"><Icon name="check" size={15} strokeWidth={3} /></span>
                <span>Bức tranh của bé ({activeChild?.displayName ?? "Bé"})</span>
              </div>
              <div className="check done">
                <span className="ck"><Icon name="check" size={15} strokeWidth={3} /></span>
                <span>Nhân vật chính: <strong>{detectedSubject}</strong></span>
              </div>
              <div className="check done">
                <span className="ck"><Icon name="check" size={15} strokeWidth={3} /></span>
                <span>Ý tưởng câu chuyện: {ideaTranscript.trim() ? "Đã nhập ý tưởng" : "AI tự sáng tạo từ tranh"}</span>
              </div>
              <div className={contextConfirmed ? "check done" : "check fail"}>
                <span className="ck">
                  {contextConfirmed && <Icon name="check" size={15} strokeWidth={3} />}
                </span>
                <span>Ngữ cảnh cá nhân hóa {contextConfirmed ? "đã được duyệt" : "chưa được duyệt"}</span>
              </div>
              <div className="check done">
                <span className="ck"><Icon name="check" size={15} strokeWidth={3} /></span>
                <span>Kịch bản {scenes.length} cảnh đã duyệt (Bản #{scriptRevision})</span>
              </div>
            </div>
            <Note tone={acceptedJobInProgress || scriptConfirmed ? "mint" : "blue"} icon={acceptedJobInProgress || scriptConfirmed ? "check" : "video"}>
              {acceptedJobInProgress || scriptConfirmed
                ? "Yêu cầu tạo video cho câu chuyện này đã được nhận. Tiếp tục theo dõi tiến trình, không dùng thêm lượt."
                : <>Dùng <strong>1 lượt video</strong> từ tài khoản của bạn. Sau khi yêu cầu được chấp nhận, còn <strong>{Math.max(0, quotaRemaining - 1)} lượt</strong>. Lượt đã dùng không thể hoàn lại.</>}
            </Note>
            <Btn
              tone="mint"
              disabled={quotaRemaining <= 0 || !contextConfirmed || !subjectConfirmed || scriptConfirmed || acceptedJobInProgress}
              onClick={() => {
                const accepted = confirmScriptAndStartVideo();
                if (accepted) navigate("/p07-video-job-status");
              }}
            >
              <Icon name="video" size={18} /> Tạo video ngay
            </Btn>
            {quotaRemaining <= 0 && (
              <Soft
                onClick={() => {
                  close();
                  navigate("/p12-video-quota");
                }}
              >
                Mua thêm lượt tạo
              </Soft>
            )}
            <Soft onClick={close}>Xem lại kịch bản</Soft>
          </Sheet>
        )}

        {activeSheet === "EDIT_SUBJECT" && (
          <Sheet title="Bé đã vẽ gì nhỉ?" onClose={close}>
            <div>
              <label className="field-label" htmlFor="edit-subject-input">Tên nhân vật hoặc chủ thể chính</label>
              <input
                id="edit-subject-input"
                className="input"
                value={subjectDraft}
                onChange={(e) => setSubjectDraft(e.target.value)}
              />
            </div>
            <div className="row wrap">
              {["Con bướm", "Cái cây", "Chú mèo", "Con cá", "Ngôi nhà"].map((s) => (
                <button key={s} type="button" className={`chip ${subjectDraft === s ? "on" : "line"}`} onClick={() => setSubjectDraft(s)}>
                  {s}
                </button>
              ))}
            </div>
            <Btn
              onClick={() => {
                if (subjectDraft.trim()) {
                  setDetectedSubject(subjectDraft.trim());
                  setSubjectConfirmed(false);
                  showToast("Đã cập nhật nhân vật chính. Bố mẹ hãy xác nhận nhé.", "info");
                }
                close();
              }}
            >
              Lưu chủ thể
            </Btn>
          </Sheet>
        )}

        {activeSheet === "ADD_CHILD" && (
          <Sheet title="Thêm hồ sơ của bé" onClose={close}>
            <div>
              <label className="field-label" htmlFor="new-child-name">Tên hiển thị của bé *</label>
              <input
                id="new-child-name"
                className="input"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Ví dụ: Bé Bông"
              />
            </div>
            <ChildGenderField
              idPrefix="new-child-gender"
              value={newGender}
              onChange={setNewGender}
            />
            <div>
              <label className="field-label" htmlFor="new-child-months">Độ tuổi (36–120 tháng)</label>
              <div className="row">
                <input
                  id="new-child-months"
                  className="input"
                  type="number"
                  required
                  min={36}
                  max={120}
                  step={1}
                  aria-invalid={!!newAgeError}
                  aria-describedby="new-child-age-help"
                  aria-errormessage={newAgeError ? "new-child-age-error" : undefined}
                  value={newMonths}
                  onChange={(e) => {
                    const value = e.target.value;
                    const months = Number(value);
                    setNewMonths(value);
                    setNewAgeError(Number.isInteger(months) && months >= 36 && months <= 120
                      ? ""
                      : "Nhập độ tuổi từ 36 đến 120 tháng bằng số nguyên.");
                  }}
                />
                <span className="chip line">{Math.max(3, Math.floor((Number(newMonths) || 60) / 12))} tuổi</span>
              </div>
              <p id="new-child-age-help" className="tiny">Nhập số tháng tuổi từ 36 đến 120.</p>
              {newAgeError && <p id="new-child-age-error" className="sub" role="alert" style={{ color: "var(--danger)" }}>{newAgeError}</p>}
            </div>
            <div className="row wrap">
              {QUICK_AGE_CHIPS.map((b) => (
                <button
                  key={b.label}
                  type="button"
                  className={`chip ${Number(newMonths) === b.months ? "on" : "line"}`}
                  aria-pressed={Number(newMonths) === b.months}
                  onClick={() => {
                    setNewMonths(String(b.months));
                    setNewAgeError("");
                  }}
                >
                  {b.label}
                </button>
              ))}
            </div>
            <div>
              <label className="field-label" htmlFor="new-child-interests">Sở thích của bé</label>
              <input
                id="new-child-interests"
                className="input"
                value={newInterests}
                onChange={(e) => setNewInterests(e.target.value)}
                placeholder="Vẽ tranh, Động vật, Thiên nhiên"
              />
            </div>
            <Btn
              disabled={!newName.trim() || !newGender || !isNewAgeValid}
              onClick={() => {
                if (!newGender) return;
                const m = ageMonths;
                if (!Number.isInteger(m) || m < 36 || m > 120) {
                  setNewAgeError("Nhập độ tuổi từ 36 đến 120 tháng bằng số nguyên.");
                  return;
                }
                const ints = newInterests
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean);
                if (!addProfile(newName.trim(), m, ints, newGender)) {
                  setNewAgeError("Nhập độ tuổi từ 36 đến 120 tháng bằng số nguyên.");
                  return;
                }
                setNewName("");
                setNewGender("");
                setNewMonths("60");
                setNewAgeError("");
                close();
              }}
            >
              Lưu hồ sơ mới
            </Btn>
            <Soft onClick={close}>Đóng</Soft>
          </Sheet>
        )}

        {activeSheet === "CANCEL_VIDEO" && (
          <Sheet title="Dừng tạo video?" onClose={close}>
            <Note tone="red" icon="alert">
              Video đang tạo sẽ bị xóa. Lượt đã dùng không được hoàn lại.
            </Note>
            <Btn
              tone="danger"
              onClick={() => {
                triggerCancelIncompleteRun();
                close();
              }}
            >
              Dừng và xóa
            </Btn>
            <Soft onClick={close}>Tiếp tục tạo</Soft>
          </Sheet>
        )}

        {activeSheet === "CAMERA_PERMISSION" && (
          <Sheet title="Cho phép dùng máy ảnh" onClose={close}>
            <div className="row" style={{ justifyContent: "center" }}>
              <span className="tile3d lg" aria-hidden="true">
                <Icon name="camera" size={34} />
              </span>
            </div>
            <Note tone="amber" icon="shield">
              Chỉ chụp bức vẽ trên giấy. Tránh khuôn mặt trẻ em và không gian riêng tư.
            </Note>
            <Btn
              onClick={() => {
                close();
                window.dispatchEvent(new CustomEvent("s2l-captured"));
              }}
            >
              Cho phép và chụp
            </Btn>
            <Soft onClick={close}>Để sau</Soft>
          </Sheet>
        )}

        {activeSheet === "REPORT_UNSUITABLE" && (
          <Sheet title="Video chưa phù hợp?" onClose={close}>
            <div className="row wrap">
              <span className="chip amber">Đã tạo lại {videoRegenCount}/2 lần</span>
            </div>
            <div className="stack">
              {REASONS.map((r) => (
                <button key={r} type="button" className={`age-opt ${reason === r ? "on" : ""}`} onClick={() => setReason(r)}>
                  <span className="h3">{r}</span>
                  <span className="rd">{reason === r && <Icon name="check" size={12} />}</span>
                </button>
              ))}
            </div>
            <Btn
              tone="amber"
              disabled={videoRegenCount >= 2}
              onClick={() => {
                if (reportVideoUnsuitableAndRegenerate(reason)) navigate("/p06-story-review");
              }}
            >
              Ẩn video & Sửa kịch bản
            </Btn>
          </Sheet>
        )}

        {activeSheet === "NOTIFICATIONS" && (
          <Sheet title="Thông báo" onClose={close}>
            <div className="row between">
              <span className="tiny">{notifications.filter((n) => n.unread).length} chưa đọc</span>
              <button type="button" className="ghost-link" onClick={markAllNotificationsRead}>Đọc hết</button>
            </div>
            {notifications.map((n) => {
              const cat = CAT_ICON[n.category] ?? { icon: "bell" as IconName, tone: "" };
              return (
                <div key={n.id} className="flat-box stack" style={{ opacity: n.unread ? 1 : 0.72 }}>
                  <div className="row">
                    <span className={`tile3d ${cat.tone}`} style={{ width: 42, height: 42 }} aria-hidden="true">
                      <Icon name={cat.icon} size={20} />
                    </span>
                    <div className="grow">
                      <div className="h3">{n.title}</div>
                      <div className="sub">{n.body}</div>
                      <div className="tiny">{n.timestamp}</div>
                    </div>
                  </div>
                  <div>
                    <Soft
                      small
                      onClick={() => {
                        markNotificationRead(n.id);
                        close();
                        navigate(n.targetPath);
                      }}
                    >
                      {n.actionLabel}
                    </Soft>
                  </div>
                </div>
              );
            })}
          </Sheet>
        )}

        {activeSheet === "ACCESS_GRANTS" && (
          <Sheet title="Quyền riêng tư & Dữ liệu AI" onClose={close}>
            <Note tone="blue" icon="shield">
              Tài khoản Phụ huynh tách biệt với Trường học và Giáo viên. Hồ sơ trẻ không tự động chia sẻ ra ngoài.
            </Note>
            <div className="flat-box stack">
              <div className="row between">
                <span className="h3">Ẩn tên thật của bé khỏi AI</span>
                <span className="chip mint">Luôn bật</span>
              </div>
              <div className="sub">Hệ thống chỉ dùng độ tuổi (tháng) và sở thích chung khi tạo câu chuyện.</div>
            </div>
            <div className="flat-box stack">
              <div className="row between">
                <span className="h3">Ghi chú nhu cầu hỗ trợ</span>
                <span className="chip amber">Không gửi cho AI</span>
              </div>
              <div className="sub">Chỉ phụ huynh xem; không dùng để suy diễn chẩn đoán.</div>
            </div>
            <Btn small onClick={close}>Đã hiểu</Btn>
          </Sheet>
        )}
      </div>
    </div>
  );
}
