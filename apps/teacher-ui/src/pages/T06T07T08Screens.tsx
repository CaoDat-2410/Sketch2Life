import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTeacher } from "../context/TeacherContext";
import { Icon, IconName } from "../components/Icon";
import { ClassroomStoryStageSvg } from "../components/SketchWhiteboardArt";
import { IconTile, PageHead, Toggle } from "./T01WorkspaceScreen";

/* ───────────── T06: Tạo video mẫu 1 trẻ / 1 buổi học (BR-10..17, UC-05) ───────────── */
export function T06SampleStoryRunPage() {
  const navigate = useNavigate();
  const {
    assignedClasses,
    activeClassId,
    pinnedLessonTitle,
    pinnedActivities,
    roster,
    selectedSampleChildId,
    setSelectedSampleChildId,
    selectedSampleActivity,
    setSelectedSampleActivity,
    sampleArtworkName,
    setSampleArtworkName,
    sampleDetectedSubject,
    setSampleDetectedSubject,
    sampleSubjectRevision,
    sampleContextConfirmed,
    confirmSampleContextSnapshot,
    sampleRawTranscript,
    sampleEditedTranscript,
    setSampleEditedTranscript,
    sampleTranscriptConfirmed,
    confirmSampleTranscript,
    followLessonDirection,
    setFollowLessonDirection,
    sampleScenes,
    sampleScriptRevision,
    sampleRewriteCount,
    sampleRewriteHint,
    setSampleRewriteHint,
    requestSampleRewrite,
    sampleVideoConfirmed,
    confirmSampleScript,
    sampleVideoJobStatus,
    orgIncludedQuota,
    orgTopupQuota,
    showToast,
  } = useTeacher();

  const cls = assignedClasses.find((c) => c.id === activeClassId) || assignedClasses[0];
  const classRoster = roster.filter(
    (r) => r.enrollmentStatus === "ACTIVE" && r.className === cls.className
  );
  const eligible =
    classRoster.length > 0
      ? classRoster
      : roster.filter((r) => r.enrollmentStatus === "ACTIVE");
  const child = eligible.find((r) => r.id === selectedSampleChildId) || eligible[0];
  const quota = orgIncludedQuota + orgTopupQuota;
  const ready = sampleContextConfirmed && sampleTranscriptConfirmed && !!child;
  const rewriteLeft = 3 - sampleRewriteCount;
  const [storyTab, setStoryTab] = useState<"story" | "storyboard">("story");
  const [subjectInput, setSubjectInput] = useState(sampleDetectedSubject);
  const [editingSubj, setEditingSubj] = useState(false);

  const activityOptions =
    pinnedActivities.length > 0
      ? pinnedActivities
      : ["Quan sát vòng đời bướm ngoài vườn trường", "Vẽ đôi cánh bướm mùa xuân trên giấy A4"];

  const subjectCandidates: { name: string; conf: string; icon: IconName; tone: "" | "is-amber" | "is-rose" }[] = [
    { name: sampleDetectedSubject, conf: "95%", icon: "palette", tone: "is-rose" },
    { name: "Bông hoa nhỏ", conf: "87%", icon: "star", tone: "is-amber" },
  ];

  return (
    <div className="tw-page">
      <PageHead
        title="Tạo video mẫu cho buổi học"
        hint="Chọn một học sinh và một hoạt động để tạo video mẫu cho lớp."
      />

      <div className="tw-card is-sky tw-row tw-wrap" style={{ gap: 24, padding: 18 }}>
        <div className="tw-row">
          <IconTile name="book" />
          <div>
            <div className="tw-kpi-lbl">Giáo án đã duyệt</div>
            <div className="tw-strong">{pinnedLessonTitle}</div>
          </div>
        </div>
        <div className="tw-row">
          <IconTile name="users" tone="is-mint" />
          <div>
            <div className="tw-kpi-lbl">Lớp học</div>
            <div className="tw-strong">{cls.className}</div>
          </div>
        </div>
        <div className="tw-row">
          <IconTile name="heart" tone="is-amber" />
          <div>
            <div className="tw-kpi-lbl">Học sinh đại diện · 1 trẻ mỗi buổi</div>
            <div className="tw-strong">{child ? child.displayLabel : "Chưa chọn"}</div>
          </div>
        </div>
        <span
          className={"tw-chip " + (quota > 0 ? "is-amber" : "is-rose")}
          style={{ marginLeft: "auto" }}
        >
          Lượt video của trường còn {quota}
        </span>
      </div>

      {/* Hàng 1: Bước 1 + Bước 2 + Bước 3 */}
      <div className="tw-grid-3">
        {/* Bước 1: Chọn học sinh và hoạt động */}
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="tw-row tw-between">
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>1. Học sinh &amp; hoạt động</h2>
            <span className="tw-chip is-mint">1 suất / buổi</span>
          </div>

          <label className="tw-label">
            Chọn 1 học sinh trong lớp
            <select
              className="tw-input"
              value={child?.id ?? ""}
              onChange={(e) => setSelectedSampleChildId(e.target.value)}
            >
              {eligible.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.displayLabel} ({r.ageText})
                </option>
              ))}
            </select>
          </label>

          <label className="tw-label">
            Chọn 1 hoạt động từ giáo án
            <select
              className="tw-input"
              value={selectedSampleActivity}
              onChange={(e) => setSelectedSampleActivity(e.target.value)}
            >
              {activityOptions.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>

          {child && (
            <div className="tw-item is-mint" style={{ padding: 12 }}>
              <div className="tw-row tw-between">
                <strong style={{ fontSize: 13.5 }}>Thông tin gửi AI</strong>
                {sampleContextConfirmed ? (
                  <span className="tw-chip is-mint">
                    <Icon name="check" size={13} /> Đã duyệt
                  </span>
                ) : (
                  <button
                    type="button"
                    className="tw-btn is-mint is-sm"
                    onClick={confirmSampleContextSnapshot}
                  >
                    Duyệt Context
                  </button>
                )}
              </div>
              <div className="tw-meta" style={{ fontSize: 12.5, marginTop: 4 }}>
                Chỉ gửi độ tuổi ({child.ageText}) và sở thích ({child.interests.join(", ")}). Tên thật và ghi chú riêng không được gửi.
              </div>
            </div>
          )}
        </div>

        {/* Bước 2: Chụp tranh của bé */}
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="tw-row tw-between">
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>2. Chụp tranh của bé</h2>
            <span className="tw-chip is-gray">{sampleArtworkName}</span>
          </div>

          <div
            style={{
              aspectRatio: "16 / 10",
              background: "#FFFDF7",
              border: "2px dashed #4652ED",
              borderRadius: 18,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              overflow: "hidden",
            }}
            role="img"
            aria-label="Ảnh chụp tranh vẽ sáp màu chú bướm trên giấy A4 của bé"
          >
            <svg viewBox="0 0 260 150" width="88%" height="88%" aria-hidden="true">
              <path d="M124 62 C 62 12, 36 86, 124 98" fill="#4652ED" stroke="#1B25C5" strokeWidth="4.5" strokeLinecap="round" />
              <path d="M136 62 C 198 12, 224 86, 136 98" fill="#4652ED" stroke="#1B25C5" strokeWidth="4.5" strokeLinecap="round" />
              <path d="M124 98 C 72 108, 84 144, 126 118" fill="#FDE68A" stroke="#D97706" strokeWidth="4.5" strokeLinecap="round" />
              <path d="M136 98 C 188 108, 176 144, 134 118" fill="#FDE68A" stroke="#D97706" strokeWidth="4.5" strokeLinecap="round" />
              <ellipse cx="130" cy="92" rx="9" ry="34" fill="#1E293B" />
              <circle cx="130" cy="48" r="12" fill="#1E293B" />
              <path d="M125 38 C 116 20, 102 22, 100 30" stroke="#1E293B" strokeWidth="3.5" fill="none" strokeLinecap="round" />
              <path d="M135 38 C 144 20, 158 22, 160 30" stroke="#1E293B" strokeWidth="3.5" fill="none" strokeLinecap="round" />
            </svg>
          </div>

          <p className="tw-meta" style={{ fontSize: 12.5 }}>
            Chỉ chụp trang giấy có nét vẽ. Tránh khuôn mặt và thông tin định danh của trẻ.
          </p>

          <div className="tw-row" style={{ marginTop: "auto", gap: 8 }}>
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() => {
                setSampleArtworkName(`tranh-${child?.id ?? "be"}-${Date.now().toString().slice(-3)}.png`);
                showToast("Đã chụp lại bức tranh của bé qua camera trình duyệt.", "info");
              }}
            >
              <Icon name="camera" size={16} /> Chụp lại
            </button>
            <button
              type="button"
              className="tw-btn is-sm"
              onClick={() => showToast("Đã xác nhận sử dụng ảnh bức vẽ này.", "ok")}
            >
              <Icon name="check" size={16} /> Dùng ảnh này
            </button>
          </div>
        </div>

        {/* Bước 3: Nhập ý tưởng của bé */}
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="tw-row tw-between">
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>3. Lời kể của bé</h2>
            <span className="tw-chip">≤ 2 phút · 20 MB</span>
          </div>

          <div className="tw-meta" style={{ fontSize: 12.5 }}>
            Lời kể đã nhận diện: <em>“{sampleRawTranscript}”</em>
          </div>

          <textarea
            className="tw-input"
            rows={3}
            value={sampleEditedTranscript}
            onChange={(e) => setSampleEditedTranscript(e.target.value)}
            aria-label="Ý tưởng lời kể của bé"
          />

          <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto" }}>
            {sampleTranscriptConfirmed ? (
              <span className="tw-chip is-mint">
                <Icon name="check" size={14} /> Đã xác nhận văn bản
              </span>
            ) : (
              <button
                type="button"
                className="tw-btn is-mint is-sm"
                onClick={confirmSampleTranscript}
              >
                <Icon name="check" size={14} /> Xác nhận lời kể
              </button>
            )}
            <button
              type="button"
              className="tw-btn is-ghost is-sm"
              onClick={() =>
                showToast("Đã thu âm giọng kể của bé và chuyển thành văn bản.", "info")
              }
            >
              <Icon name="sparkle" size={14} /> Ghi âm giọng bé
            </button>
          </div>
        </div>
      </div>

      {/* Hàng 2: Bước 4 (Xác nhận chủ thể AI VLM) + Bước 5 (Duyệt kịch bản) */}
      <div className="tw-grid-2" style={{ gridTemplateColumns: "0.95fr 1.45fr" }}>
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="tw-row tw-between">
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>4. Chủ thể bức vẽ</h2>
            <span className="tw-chip">Nhân vật đã nhận diện</span>
          </div>

          <div className="tw-grid-2" style={{ gap: 10 }}>
            {subjectCandidates.map((item, idx) => {
              const active = sampleDetectedSubject === item.name;
              return (
                <button
                  key={item.name + idx}
                  type="button"
                  onClick={() => setSampleDetectedSubject(item.name)}
                  className={"tw-item is-lift" + (active ? " is-selected" : "")}
                  style={{
                    padding: 14,
                    borderRadius: 16,
                    textAlign: "center",
                    fontFamily: "inherit",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <IconTile name={item.icon} tone={item.tone} />
                  <strong style={{ fontSize: 14.5 }}>{item.name}</strong>
                  <span className="tw-meta" style={{ fontSize: 12 }}>
                    Độ tin cậy {item.conf}
                  </span>
                </button>
              );
            })}
          </div>

          {editingSubj ? (
            <div className="tw-row">
              <input
                className="tw-input"
                value={subjectInput}
                onChange={(e) => setSubjectInput(e.target.value)}
                aria-label="Tên chủ thể chỉnh sửa"
              />
              <button
                type="button"
                className="tw-btn is-sm"
                onClick={() => {
                  if (subjectInput.trim()) setSampleDetectedSubject(subjectInput.trim());
                  setEditingSubj(false);
                }}
              >
                Lưu
              </button>
            </div>
          ) : (
            <div className="tw-row tw-between" style={{ marginTop: "auto" }}>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setEditingSubj(true)}
              >
                <Icon name="edit" size={14} /> Sửa chủ thể
              </button>
              <button
                type="button"
                className="tw-btn is-mint is-sm"
                onClick={() => {
                  confirmSampleContextSnapshot();
                  showToast("Đã xác nhận nhân vật và thông tin gửi AI.", "ok");
                }}
              >
                <Icon name="check" size={14} /> Xác nhận chủ thể
              </button>
            </div>
          )}
        </div>

        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="tw-row tw-between tw-wrap">
            <div>
              <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>
                5. Duyệt kịch bản mẫu (Bản #{sampleScriptRevision})
              </h2>
              <div className="tw-meta" style={{ fontSize: 12.5 }}>
                Duyệt nội dung phù hợp lứa tuổi trước khi tạo video.
              </div>
            </div>
            <div className="tw-row" style={{ gap: 6 }}>
              <button
                type="button"
                className={"tw-chip " + (storyTab === "story" ? "" : "is-gray")}
                style={{ cursor: "pointer", fontFamily: "inherit" }}
                onClick={() => setStoryTab("story")}
              >
                Cốt truyện
              </button>
              <button
                type="button"
                className={"tw-chip " + (storyTab === "storyboard" ? "" : "is-gray")}
                style={{ cursor: "pointer", fontFamily: "inherit" }}
                onClick={() => setStoryTab("storyboard")}
              >
                Storyboard ({sampleScenes.length} cảnh)
              </button>
            </div>
          </div>

          <div className="tw-row tw-between tw-wrap">
            <div className="tw-row">
              <Toggle
                on={followLessonDirection}
                onChange={setFollowLessonDirection}
                label="Đi theo hướng giáo án"
              />
              <span style={{ fontWeight: 600, fontSize: 13.5 }}>
                Bám sát mục tiêu giáo án “{pinnedLessonTitle}”
              </span>
            </div>
            <span className={"tw-chip " + (rewriteLeft > 0 ? "is-amber" : "is-rose")}>
              Viết lại bằng AI: còn {rewriteLeft}/3 lần
            </span>
          </div>

          {storyTab === "story" ? (
            <div
              className="tw-item is-sky"
              style={{ padding: 14, display: "flex", flexDirection: "column", gap: 8 }}
            >
              {sampleScenes.map((s) => (
                <div key={s.index} style={{ fontSize: 14 }}>
                  <strong className="tw-strong">{s.title}:</strong> {s.narration}
                </div>
              ))}
            </div>
          ) : (
            <div
              className="tw-grid-4"
              style={{ gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))" }}
            >
              {sampleScenes.map((s) => (
                <div key={s.index} className="tw-scene">
                  <div className="tw-scene-pic">
                    <b>{s.index}</b>
                  </div>
                  <strong style={{ fontSize: 13.5 }}>
                    {s.title.replace(/^Cảnh \d+ · /, "")}
                  </strong>
                  <span className="tw-meta" style={{ fontSize: 12.5 }}>
                    {s.narration}
                  </span>
                </div>
              ))}
            </div>
          )}

          <div className="tw-row">
            <input
              className="tw-input"
              placeholder="Nhập gợi ý để AI viết lại kịch bản..."
              value={sampleRewriteHint}
              onChange={(e) => setSampleRewriteHint(e.target.value)}
              aria-label="Gợi ý viết lại kịch bản"
            />
            <button
              type="button"
              className="tw-btn is-ghost"
              disabled={rewriteLeft <= 0}
              onClick={requestSampleRewrite}
            >
              <Icon name="refresh" size={16} /> Viết lại ({rewriteLeft})
            </button>
          </div>
        </div>
      </div>

      {/* Bước 6: Tiến trình & Chuyển sang Chiếu trên lớp */}
      <div className="tw-card is-sky tw-row tw-between tw-wrap" style={{ padding: 18 }}>
        <div className="tw-row tw-wrap" style={{ gap: 10 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>6. Tiến trình tạo video mẫu:</h2>
          <span className="tw-chip is-mint">
            <Icon name="check" size={13} /> Xử lý tranh vẽ (1/4)
          </span>
          <span className="tw-chip is-mint">
            <Icon name="check" size={13} /> Hồ sơ nhân vật (2/4)
          </span>
          <span className="tw-chip is-mint">
            <Icon name="check" size={13} /> Dựng cảnh 16:9 (3/4)
          </span>
          <span className="tw-chip is-mint">
            <Icon name="check" size={13} /> Kiểm tra an toàn (4/4)
          </span>
        </div>

        {sampleVideoConfirmed || sampleVideoJobStatus === "VIDEO_READY" ? (
          <button
            type="button"
            className="tw-btn is-mint"
            onClick={() => navigate("/t07-video-presentation-confirmation")}
          >
            <Icon name="play" size={18} /> Mở màn hình Chiếu trên lớp
          </button>
        ) : (
          <button
            type="button"
            className="tw-btn"
            disabled={quota <= 0}
            onClick={() => {
              if (!ready) {
                showToast("Hãy xác nhận chủ thể và lời kể của bé trước.", "warn");
                return;
              }
              confirmSampleScript();
            }}
          >
            <Icon name="video" size={18} /> Xác nhận kịch bản &amp; Tạo video mẫu
          </button>
        )}
      </div>

      {quota <= 0 && (
        <div className="tw-card is-amber tw-row" role="alert">
          <IconTile name="lock" tone="is-rose" />
          <strong>
            Trường đã hết lượt tạo video mẫu. Hãy liên hệ Quản lý trường để mua thêm gói Top-up.
          </strong>
        </div>
      )}
    </div>
  );
}

/* ───────────── T07: Chiếu trên lớp — Màn hình trình chiếu lớn từng cảnh (BR-16, BR-25, BR-37) ───────────── */
export function T07VideoPresentationConfirmationPage() {
  const navigate = useNavigate();
  const {
    assignedClasses,
    activeClassId,
    pinnedLessonTitle,
    sampleVideoJobStatus,
    sampleVideoConfirmed,
    sampleScenes,
    sampleRegenCount,
    markSampleVideoUnsuitable,
    presentationConfirmed,
    playbackTokenIssued,
    presentationAuditLog,
    confirmClassroomPresentation,
    captionsOn,
    setCaptionsOn,
    completeSampleRun,
    cancelOrDeleteSampleRun,
    orgIncludedQuota,
    orgTopupQuota,
    showToast,
  } = useTeacher();

  const cls = assignedClasses.find((c) => c.id === activeClassId) || assignedClasses[0];
  const [sceneIdx, setSceneIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [bgmOn, setBgmOn] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const quota = orgIncludedQuota + orgTopupQuota;
  const ready =
    sampleVideoConfirmed ||
    sampleVideoJobStatus === "VIDEO_READY" ||
    sampleVideoJobStatus === "COMPLETED";
  const current = sampleScenes[sceneIdx] ?? sampleScenes[0];

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setSceneIdx((prev) => (prev + 1) % sampleScenes.length);
    }, 4200);
    return () => window.clearInterval(timer);
  }, [playing, sampleScenes.length]);

  useEffect(() => {
    if (!fullscreen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setFullscreen(false);
      else if (e.key === "ArrowRight")
        setSceneIdx((i) => Math.min(sampleScenes.length - 1, i + 1));
      else if (e.key === "ArrowLeft") setSceneIdx((i) => Math.max(0, i - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullscreen, sampleScenes.length]);

  if (!ready) {
    return (
      <div className="tw-page">
        <PageHead
          title="Chiếu trên lớp"
          hint="Xem trước video mẫu 720p 16:9 và xác nhận đạt yêu cầu sư phạm trước khi chiếu cho cả lớp."
        />
        <div className="tw-card is-amber tw-row tw-between tw-wrap">
          <div className="tw-row">
            <IconTile name="video" tone="is-amber" />
            <div>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
                Chưa có video mẫu sẵn sàng để trình chiếu
              </h2>
              <p className="tw-meta" style={{ marginTop: 2 }}>
                Cô hãy xác nhận kịch bản ở trang Tạo video mẫu trước khi mở màn hình trình chiếu.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="tw-btn is-amber"
            onClick={() => navigate("/t06-sample-story-run")}
          >
            Quay lại Tạo video mẫu
          </button>
        </div>
      </div>
    );
  }

  const stageBody = (
    <div className="tw-stage-wrap" style={fullscreen ? { maxWidth: 1120 } : undefined}>
      {/* Banner bắt buộc: Xác nhận để chiếu cho lớp (BR-37) */}
      <div
        className={
          fullscreen
            ? "tw-row tw-between tw-wrap"
            : "tw-card is-mint tw-row tw-between tw-wrap"
        }
        style={
          fullscreen
            ? {
                background: "#0F2E28",
                border: "1px solid #1F5C4B",
                padding: "14px 20px",
                borderRadius: 18,
              }
            : { padding: "16px 22px" }
        }
      >
        <div className="tw-row" style={{ gap: 14 }}>
          <IconTile name="shield" tone="is-mint" />
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: 18,
                fontWeight: 800,
                color: fullscreen ? "#ECFDF5" : undefined,
              }}
            >
              Xác nhận để chiếu cho {cls.className}
            </h2>
            <div
              className="tw-meta"
              style={{ fontSize: 13.5, color: fullscreen ? "#A7F3D0" : undefined }}
            >
              {presentationConfirmed && playbackTokenIssued
                ? `Đã cấp quyền phát nội bộ: ${playbackTokenIssued}`
                : "Giáo viên kiểm tra nội dung video 16:9 trước khi bấm xác nhận trình chiếu lên màn hình lớp."}
            </div>
          </div>
        </div>

        <div className="tw-row tw-wrap" style={{ gap: 10 }}>
          {presentationConfirmed ? (
            <span className="tw-chip is-mint">
              <Icon name="check" size={14} /> Đã xác nhận chiếu cho lớp
            </span>
          ) : (
            <button
              type="button"
              className="tw-btn is-mint"
              onClick={confirmClassroomPresentation}
            >
              <Icon name="check" size={18} /> Xác nhận để chiếu cho lớp
            </button>
          )}
          <button
            type="button"
            className={fullscreen ? "tw-btn is-amber is-sm" : "tw-btn is-ghost is-sm"}
            onClick={() => setFullscreen((f) => !f)}
          >
            <Icon name={fullscreen ? "minimize" : "maximize"} size={16} />{" "}
            {fullscreen ? "Thu nhỏ" : "Toàn màn hình"}
          </button>
        </div>
      </div>

      {/* Khung trình chiếu 16:9 lớn cho máy chiếu lớp học */}
      <div className="tw-player" aria-label="Màn hình trình chiếu câu chuyện 16:9">
        <ClassroomStoryStageSvg sceneIndex={sceneIdx} playing={playing} />

        <div
          className="tw-row tw-between"
          style={{
            position: "absolute",
            top: 16,
            left: 20,
            right: 20,
            zIndex: 2,
          }}
        >
          <span
            style={{
              padding: "7px 14px",
              borderRadius: 9999,
              background: "rgba(15, 23, 42, 0.76)",
              color: "#FFFFFF",
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            {pinnedLessonTitle} · {current?.title} ({sceneIdx + 1}/{sampleScenes.length})
          </span>
          <span
            style={{
              padding: "6px 12px",
              borderRadius: 9999,
              background: "rgba(15, 23, 42, 0.72)",
              color: "#CBD0D8",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            HD 16:9 · Phát trong trường
          </span>
        </div>

        <button
          type="button"
          className="tw-play"
          aria-label={playing ? "Tạm dừng trình chiếu" : "Phát câu chuyện"}
          style={{ position: "relative", zIndex: 2 }}
          onClick={() => setPlaying((p) => !p)}
        >
          <Icon name={playing ? "pause" : "play"} size={30} />
        </button>

        {captionsOn && current && (
          <div className="tw-cc" style={{ zIndex: 2 }}>
            {current.narration}
          </div>
        )}
      </div>

      {/* Chấm chọn từng cảnh lớn + Nút Cảnh trước / Cảnh tiếp theo + BGM / CC */}
      <div
        className={fullscreen ? "" : "tw-card"}
        style={
          fullscreen
            ? {
                background: "#142035",
                padding: 20,
                borderRadius: 20,
                display: "flex",
                flexDirection: "column",
                gap: 16,
              }
            : { display: "flex", flexDirection: "column", gap: 16, padding: 20 }
        }
      >
        <div className="tw-row tw-between tw-wrap" style={{ gap: 12 }}>
          <div className="tw-row tw-wrap" role="tablist" aria-label="Danh sách cảnh">
            {sampleScenes.map((s, i) => (
              <button
                key={s.index}
                type="button"
                role="tab"
                aria-selected={i === sceneIdx}
                className={"tw-step-dot" + (i === sceneIdx ? " is-on" : "")}
                onClick={() => {
                  setPlaying(false);
                  setSceneIdx(i);
                }}
              >
                <b>{s.index}</b> Cảnh {s.index}
              </button>
            ))}
          </div>

          <div className="tw-row tw-wrap" style={{ gap: 16 }}>
            <div className="tw-row" style={{ gap: 8 }}>
              <span style={{ fontWeight: 600, fontSize: 14 }}>Nhạc nền</span>
              <Toggle on={bgmOn} onChange={setBgmOn} label="Bật nhạc nền" />
            </div>
            <div className="tw-row" style={{ gap: 8 }}>
              <span style={{ fontWeight: 600, fontSize: 14 }}>Phụ đề CC</span>
              <Toggle on={captionsOn} onChange={setCaptionsOn} label="Bật phụ đề CC" />
            </div>
          </div>
        </div>

        <div className="tw-row tw-between tw-wrap">
          <button
            type="button"
            className="tw-btn is-ghost"
            disabled={sceneIdx <= 0}
            onClick={() => {
              setPlaying(false);
              setSceneIdx((i) => Math.max(0, i - 1));
            }}
          >
            <Icon name="arrow-left" size={18} /> Cảnh trước
          </button>

          <div style={{ textAlign: "center" }}>
            <div className="tw-strong" style={{ fontSize: 16 }}>
              {current?.title}
            </div>
          </div>

          <button
            type="button"
            className="tw-btn"
            disabled={sceneIdx >= sampleScenes.length - 1}
            onClick={() => {
              setPlaying(false);
              setSceneIdx((i) => Math.min(sampleScenes.length - 1, i + 1));
            }}
          >
            Cảnh tiếp theo <Icon name="arrow-right" size={18} />
          </button>
        </div>
      </div>

      {/* Ngăn kéo phụ (Collapsible Drawer): Nhật ký Audit & Tác vụ Tạo lại / Xóa (BR-16, BR-37) */}
      {!fullscreen && (
        <div className="tw-card" style={{ padding: "14px 20px" }}>
          <button
            type="button"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen((o) => !o)}
            className="tw-row tw-between"
            style={{
              width: "100%",
              border: 0,
              background: "transparent",
              cursor: "pointer",
              fontFamily: "inherit",
              padding: 4,
              color: "inherit",
            }}
          >
            <div className="tw-row">
              <Icon name="clock" size={18} />
              <span className="tw-strong" style={{ fontSize: 15 }}>
                Lịch sử trình chiếu &amp; Quản lý video mẫu
              </span>
            </div>
            <span className="tw-row" style={{ gap: 8 }}>
              <span className="tw-chip is-gray">{presentationAuditLog.length} bản ghi</span>
              <span className={"tw-nav-group-chev" + (drawerOpen ? " is-open" : "")}>
                <Icon name="chevron-down" size={18} />
              </span>
            </span>
          </button>

          {drawerOpen && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 14,
                marginTop: 14,
                paddingTop: 14,
                borderTop: "1px solid var(--tw-border)",
              }}
            >
              <div className="tw-row tw-wrap" style={{ gap: 10 }}>
                <button
                  type="button"
                  className="tw-btn is-ghost is-sm"
                  onClick={() => {
                    if (
                      markSampleVideoUnsuitable(
                        "Nội dung chưa phù hợp với mục tiêu sư phạm của lớp"
                      )
                    ) {
                      navigate("/t06-sample-story-run");
                    }
                  }}
                >
                  <Icon name="refresh" size={16} /> Video chưa phù hợp · Tạo lại (
                  {2 - sampleRegenCount}/2 lần)
                </button>
                <button
                  type="button"
                  className="tw-btn is-mint is-sm"
                  disabled={!presentationConfirmed}
                  onClick={completeSampleRun}
                >
                  <Icon name="check" size={16} /> Hoàn tất buổi chiếu (Nhả khóa phiên)
                </button>
                <button
                  type="button"
                  className="tw-btn is-danger is-sm"
                  onClick={() => {
                    cancelOrDeleteSampleRun();
                    showToast(
                      "Đang thu hồi và xóa video mẫu của lớp (DELETE_PENDING → DELETED).",
                      "warn"
                    );
                  }}
                >
                  <Icon name="trash" size={16} /> Hủy / Xóa video mẫu
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {presentationAuditLog.map((a) => (
                  <div key={a.id} className="tw-item tw-row tw-between tw-wrap">
                    <span style={{ fontSize: 14 }}>
                      <strong>{a.teacherName}</strong> xác nhận chiếu cho{" "}
                      <strong>{a.className}</strong> ({a.occurrenceId} · {a.tokenSummary})
                    </span>
                    <span className="tw-chip is-gray">{a.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  if (fullscreen) {
    return <div className="tw-fullscreen-stage">{stageBody}</div>;
  }

  return (
    <div className="tw-page">
      <div className="tw-stage-wrap">
        <PageHead
          title="Chiếu trên lớp"
          hint="Video 16:9 dành cho máy chiếu lớp học. Không tải xuống hoặc chia sẻ công khai."
          right={
            <div className="tw-row tw-wrap">
              <span className="tw-chip is-gray">
                <Icon name="lock" size={14} /> Phát riêng tư
              </span>
              <span className={"tw-chip " + (quota > 0 ? "is-amber" : "is-rose")}>
                Lượt video còn lại: {quota}
              </span>
            </div>
          }
        />
      </div>
      {stageBody}
    </div>
  );
}

/* ───────────── T08: Trang Cài đặt riêng (/t08-settings) ───────────── */
export function T08TeacherSettingsPage() {
  const navigate = useNavigate();
  const { theme, setTheme, logout, showToast } = useTeacher();

  // Account & Notification Preferences
  const [notifVideoReady, setNotifVideoReady] = useState(true);
  const [notifPublicReview, setNotifPublicReview] = useState(true);
  const [notifRetention144h, setNotifRetention144h] = useState(true);

  // Change Password & Forgot Password
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [resetEmail, setResetEmail] = useState("colan@anhduong.edu.vn");

  // 2FA State
  const [twoFactorOn, setTwoFactorOn] = useState(true);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([
    "S2L-8492-K7M1",
    "S2L-3109-P4X8",
    "S2L-6724-Q9N3",
    "S2L-5580-W2C6",
  ]);

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPw || !newPw) {
      showToast("Vui lòng nhập mật khẩu hiện tại và mật khẩu mới.", "warn");
      return;
    }
    if (newPw.length < 8) {
      showToast("Mật khẩu mới cần tối thiểu 8 ký tự.", "err");
      return;
    }
    if (newPw !== confirmPw) {
      showToast("Mật khẩu xác nhận chưa khớp với mật khẩu mới.", "err");
      return;
    }
    setCurrentPw("");
    setNewPw("");
    setConfirmPw("");
    showToast("Đã cập nhật mật khẩu tài khoản Giáo viên thành công.", "ok");
  };

  const handleSendResetLink = (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetEmail.trim()) {
      showToast("Vui lòng nhập email nhận liên kết khôi phục.", "warn");
      return;
    }
    showToast(`Đã gửi liên kết đặt lại mật khẩu tới ${resetEmail.trim()}.`, "info");
  };

  const regenerateRecoveryCodes = () => {
    const rand = () => Math.floor(1000 + Math.random() * 9000);
    setRecoveryCodes([
      `S2L-${rand()}-A9F2`,
      `S2L-${rand()}-M3D7`,
      `S2L-${rand()}-T6K4`,
      `S2L-${rand()}-R8V1`,
    ]);
    showToast("Đã sinh bộ mã khôi phục 2FA mới.", "ok");
  };

  const copyRecoveryCodes = () => {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(recoveryCodes.join("\n")).catch(() => {});
    }
    showToast("Đã sao chép mã khôi phục 2FA vào bộ nhớ tạm.", "ok");
  };

  return (
    <div className="tw-page">
      <PageHead
        title="Cài đặt tài khoản & Giao diện"
        hint="Tùy chỉnh chế độ hiển thị Sáng / Tối, quyền riêng tư tài khoản tổ chức, bảo mật mật khẩu và xác thực 2 lớp (2FA)."
        right={
          <button
            type="button"
            className="tw-btn is-ghost"
            onClick={() => navigate("/t01-lesson-workspace?view=settings")}
          >
            <Icon name="user" size={18} /> Xem Hồ sơ cá nhân
          </button>
        }
      />

      {/* 1. Chế độ Sáng / Tối (Light / Dark Mode) */}
      <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="tw-row tw-between tw-wrap">
          <div className="tw-row">
            <IconTile name={theme === "dark" ? "moon" : "sun"} tone="is-amber" />
            <div>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>
                Chế độ Sáng / Tối (Giao diện hiển thị)
              </h2>
              <p className="tw-meta" style={{ marginTop: 2 }}>
                Chọn Chế độ Sáng khi soạn bài ban ngày hoặc Chế độ Tối dịu mắt khi trình chiếu máy chiếu trong phòng học.
              </p>
            </div>
          </div>

          <div className="tw-tabs-seg" role="radiogroup" aria-label="Chế độ giao diện">
            <button
              type="button"
              role="radio"
              aria-checked={theme === "light"}
              className={"tw-tab-seg" + (theme === "light" ? " is-on" : "")}
              onClick={() => {
                setTheme("light");
                showToast("Đã chuyển sang Chế độ Sáng.", "info");
              }}
            >
              <Icon name="sun" size={17} /> Sáng (Light)
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={theme === "dark"}
              className={"tw-tab-seg" + (theme === "dark" ? " is-on" : "")}
              onClick={() => {
                setTheme("dark");
                showToast("Đã chuyển sang Chế độ Tối (WCAG AA).", "info");
              }}
            >
              <Icon name="moon" size={17} /> Tối (Dark)
            </button>
          </div>
        </div>
      </div>

      {/* 2. Tài khoản & Quyền riêng tư */}
      <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div className="tw-row">
          <IconTile name="shield" tone="is-mint" />
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>
              Tài khoản &amp; Quyền riêng tư
            </h2>
            <p className="tw-meta" style={{ marginTop: 2 }}>
              Tài khoản Giáo viên thuộc quản lý độc lập của Trường Mầm non Ánh Dương, tách biệt hoàn toàn với ứng dụng Phụ huynh.
            </p>
          </div>
        </div>

        <div className="tw-grid-2">
          <div className="tw-item is-sky">
            <div className="tw-meta" style={{ fontSize: 13 }}>Email đăng nhập tổ chức</div>
            <div className="tw-strong" style={{ fontSize: 16, marginTop: 2 }}>
              colan@anhduong.edu.vn
            </div>
          </div>
          <div className="tw-item is-mint">
            <div className="tw-meta" style={{ fontSize: 13 }}>Đơn vị công tác &amp; Phân quyền</div>
            <div className="tw-strong" style={{ fontSize: 16, marginTop: 2 }}>
              Trường Mầm non Ánh Dương · Giáo viên chủ nhiệm
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="tw-item tw-row tw-between">
            <div>
              <div className="tw-strong" style={{ fontSize: 14.5 }}>
                Thông báo khi Video mẫu của lớp hoàn tất (VIDEO_READY)
              </div>
              <div className="tw-meta" style={{ fontSize: 13 }}>
                Hiển thị chuông báo trên thanh tiêu đề ngay khi qua cổng kiểm duyệt an toàn.
              </div>
            </div>
            <Toggle
              on={notifVideoReady}
              onChange={setNotifVideoReady}
              label="Thông báo khi video mẫu hoàn tất"
            />
          </div>

          <div className="tw-item tw-row tw-between">
            <div>
              <div className="tw-strong" style={{ fontSize: 14.5 }}>
                Thông báo kết quả duyệt giáo án công khai
              </div>
              <div className="tw-meta" style={{ fontSize: 13 }}>
                Nhận phản hồi từ Quản lý trường khi gửi giáo án lên thư viện chung.
              </div>
            </div>
            <Toggle
              on={notifPublicReview}
              onChange={setNotifPublicReview}
              label="Thông báo kết quả duyệt giáo án"
            />
          </div>

          <div className="tw-item tw-row tw-between">
            <div>
              <div className="tw-strong" style={{ fontSize: 14.5 }}>
                Nhắc hạn lưu trữ dữ liệu tạm thời 144h / 168h
              </div>
              <div className="tw-meta" style={{ fontSize: 13 }}>
                Tự động nhắc trước khi hệ thống dọn tệp nháp hết hạn lưu trữ.
              </div>
            </div>
            <Toggle
              on={notifRetention144h}
              onChange={setNotifRetention144h}
              label="Nhắc hạn lưu trữ 144h/168h"
            />
          </div>
        </div>
      </div>

      {/* 3. Đổi mật khẩu & Quên mật khẩu */}
      <div className="tw-grid-2">
        <form
          onSubmit={handlePasswordChange}
          className="tw-card"
          style={{ display: "flex", flexDirection: "column", gap: 14 }}
        >
          <div className="tw-row">
            <IconTile name="lock" />
            <div>
              <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Đổi mật khẩu</h2>
              <p className="tw-meta" style={{ fontSize: 13 }}>
                Sử dụng mật khẩu tối thiểu 8 ký tự để bảo vệ tài khoản lớp học.
              </p>
            </div>
          </div>

          <label className="tw-label">
            Mật khẩu hiện tại
            <input
              className="tw-input"
              type="password"
              placeholder="Nhập mật khẩu hiện tại"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
            />
          </label>

          <label className="tw-label">
            Mật khẩu mới
            <input
              className="tw-input"
              type="password"
              placeholder="Tối thiểu 8 ký tự"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
            />
          </label>

          <label className="tw-label">
            Xác nhận mật khẩu mới
            <input
              className="tw-input"
              type="password"
              placeholder="Nhập lại mật khẩu mới"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
            />
          </label>

          <button type="submit" className="tw-btn" style={{ alignSelf: "flex-start" }}>
            <Icon name="check" size={18} /> Cập nhật mật khẩu
          </button>
        </form>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* Quên mật khẩu */}
          <form
            onSubmit={handleSendResetLink}
            className="tw-card"
            style={{ display: "flex", flexDirection: "column", gap: 12 }}
          >
            <div className="tw-row">
              <IconTile name="refresh" tone="is-amber" />
              <div>
                <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Quên mật khẩu</h2>
                <p className="tw-meta" style={{ fontSize: 13 }}>
                  Gửi liên kết khôi phục mật khẩu qua email trường học của cô.
                </p>
              </div>
            </div>

            <div className="tw-row tw-wrap">
              <input
                className="tw-input"
                type="email"
                style={{ flex: 1, minWidth: 200 }}
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
                aria-label="Email khôi phục mật khẩu"
              />
              <button type="submit" className="tw-btn is-ghost">
                Gửi liên kết đặt lại
              </button>
            </div>
          </form>

          {/* 4. Xác thực 2 lớp (2FA) */}
          <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile name="shield" tone="is-mint" />
                <div>
                  <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>
                    Xác thực 2 lớp (2FA)
                  </h2>
                  <p className="tw-meta" style={{ fontSize: 13 }}>
                    Bảo vệ quyền truy cập danh sách lớp và trình chiếu nội bộ.
                  </p>
                </div>
              </div>
              <Toggle
                on={twoFactorOn}
                onChange={(next) => {
                  setTwoFactorOn(next);
                  showToast(
                    next ? "Đã bật Xác thực 2 lớp (2FA)." : "Đã tạm tắt Xác thực 2 lớp (2FA).",
                    next ? "ok" : "warn"
                  );
                }}
                label="Bật xác thực 2 lớp"
              />
            </div>

            {twoFactorOn && (
              <>
                <div className="tw-item is-sky">
                  <div className="tw-row tw-between tw-wrap" style={{ marginBottom: 8 }}>
                    <strong style={{ fontSize: 13.5 }}>Mã khôi phục dự phòng (Recovery Codes)</strong>
                    <span className="tw-chip is-mint">Đang kích hoạt</span>
                  </div>
                  <div className="tw-grid-2" style={{ gap: 8 }}>
                    {recoveryCodes.map((code) => (
                      <code
                        key={code}
                        style={{
                          fontFamily: "var(--font-code)",
                          fontSize: 13.5,
                          fontWeight: 700,
                          padding: "6px 10px",
                          borderRadius: 10,
                          background: "var(--tw-surface)",
                          border: "1px solid var(--tw-border)",
                        }}
                      >
                        {code}
                      </code>
                    ))}
                  </div>
                </div>

                <div className="tw-row tw-wrap" style={{ gap: 8 }}>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    onClick={copyRecoveryCodes}
                  >
                    <Icon name="copy" size={15} /> Sao chép mã
                  </button>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    onClick={regenerateRecoveryCodes}
                  >
                    <Icon name="refresh" size={15} /> Tạo mã mới
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 5. Đăng xuất */}
      <div className="tw-card tw-row tw-between tw-wrap" style={{ padding: "18px 24px" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Đăng xuất phiên làm việc</h2>
          <p className="tw-meta" style={{ marginTop: 2 }}>
            Kết thúc phiên đăng nhập trên thiết bị lớp học sau khi hoàn tất giờ dạy.
          </p>
        </div>
        <button
          type="button"
          className="tw-btn is-danger"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          <Icon name="log-out" size={18} /> Đăng xuất khỏi hệ thống
        </button>
      </div>
    </div>
  );
}
