import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ImportErrorMode, useTeacher } from "../context/TeacherContext";
import { TeacherLessonCard } from "../data/mockTeacherData";
import { Icon } from "../components/Icon";
import { PublicLibraryModal, topicIconName, topicTone } from "../components/PublicLibraryModal";
import { IconTile, PageHead } from "./T01WorkspaceScreen";

const IMPORT_ERRORS: Record<Exclude<ImportErrorMode, "NONE">, string> = {
  TOO_LARGE: "Tệp vượt quá giới hạn 25 MB. Hãy chọn tệp nhỏ hơn.",
  TOO_MANY_PAGES: "Tệp vượt quá 100 trang hoặc slide. Hãy tách tệp rồi tải lại.",
  SCANNED_PDF:
    "Tệp PDF chỉ chứa ảnh scan. Hãy dùng tệp có thể chọn văn bản.",
  PASSWORD_PROTECTED:
    "Tệp đang khóa mật khẩu hoặc chứa macro. Hãy gỡ khóa rồi tải lại.",
};

const TOPIC_OPTIONS = [
  "Con bướm",
  "Cây xanh",
  "Mây và mưa",
  "Đại dương",
  "Bông hoa",
  "Động vật",
  "Thiên nhiên",
];

const AGE_BAND_OPTIONS = [
  "3–4 tuổi (36–47 tháng)",
  "4–5 tuổi (48–59 tháng)",
  "5–6 tuổi (60–83 tháng)",
  "7–8 tuổi (84–107 tháng)",
  "9+ tuổi (108–155 tháng)",
];

interface LessonLocationState {
  openCreateModal?: boolean;
  openUploadModal?: boolean;
  preloadTemplate?: TeacherLessonCard;
  tab?: "lessons" | "grants";
}

export function T02LessonAuthoringPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    lessons,
    publicTemplates,
    createLesson,
    updateLesson,
    approveLessonForSession,
    setArchiveModalTarget,
    pinnedLessonTitle,
    pinnedPlanRevision,
    occurrenceStatus,
    safetyChecklistConfirmed,
    setSafetyChecklistConfirmed,
    uploadedFileName,
    uploadedFileSizeMb,
    uploadedSha256,
    documentRevision,
    importErrorMode,
    setImportErrorMode,
    handleRealDocumentUpload,
    grants,
    revokeTeacherGrant,
    addLessonGrant,
    restoreDefaultLessons,
    showToast,
  } = useTeacher();

  const [activeTab, setActiveTab] = useState<"lessons" | "grants">("lessons");
  const [search, setSearch] = useState("");
  const [visFilter, setVisFilter] = useState<"Tất cả" | TeacherLessonCard["visibility"]>("Tất cả");

  // Modals
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingLessonId, setEditingLessonId] = useState<string | null>(null);
  const [showUploadPanelInModal, setShowUploadPanelInModal] = useState(false);
  const [detailLesson, setDetailLesson] = useState<TeacherLessonCard | null>(null);
  const [shareModalOpen, setShareModalOpen] = useState(false);

  // Create / Edit Form State
  const [formTitle, setFormTitle] = useState("");
  const [formTopic, setFormTopic] = useState("Con bướm");
  const [formAgeBand, setFormAgeBand] = useState(AGE_BAND_OPTIONS[1]);
  const [formVisibility, setFormVisibility] = useState<TeacherLessonCard["visibility"]>("Trong trường");
  const [formDescription, setFormDescription] = useState("");
  const [formObjectives, setFormObjectives] = useState("");
  const [formActivities, setFormActivities] = useState<string[]>([
    "Hoạt động 1: Quan sát tranh minh họa và trò chuyện mở đầu",
    "Hoạt động 2: Thực hành vẽ sáng tạo trên giấy A4 theo bảng 16:9",
  ]);
  const [newActInput, setNewActInput] = useState("");
  const [formApproveNow, setFormApproveNow] = useState(true);
  const [formRemixedFrom, setFormRemixedFrom] = useState<string | undefined>(undefined);

  // Share Grant Form State
  const [shareLessonTitle, setShareLessonTitle] = useState(lessons[0]?.title ?? "Vòng đời bướm");
  const [shareRecipient, setShareRecipient] = useState("Nhóm giáo viên Khối Mẫu giáo");
  const [sharePermission, setSharePermission] = useState("Quyền xem & Remix nội bộ trường");
  const [shareExpiry, setShareExpiry] = useState("31/12/2026");

  const modalFileRef = useRef<HTMLInputElement>(null);

  const openBlankCreateModal = (withUploadExpanded = false) => {
    setEditingLessonId(null);
    setFormTitle("");
    setFormTopic("Con bướm");
    setFormAgeBand(AGE_BAND_OPTIONS[1]);
    setFormVisibility("Trong trường");
    setFormDescription("");
    setFormObjectives("");
    setFormActivities([
      "Hoạt động 1: Quan sát trực quan và đặt câu hỏi khám phá chủ đề",
      "Hoạt động 2: Vẽ từng bước trên giấy A4 cùng bảng hướng dẫn 16:9",
    ]);
    setNewActInput("");
    setFormApproveNow(true);
    setFormRemixedFrom(undefined);
    setImportErrorMode("NONE");
    setShowUploadPanelInModal(withUploadExpanded);
    setEditorOpen(true);
  };

  const openEditModal = (lesson: TeacherLessonCard) => {
    setEditingLessonId(lesson.id);
    setFormTitle(lesson.title);
    setFormTopic(lesson.topic);
    setFormAgeBand(lesson.ageBand);
    setFormVisibility(lesson.visibility);
    setFormDescription(lesson.description);
    setFormObjectives(lesson.objectives);
    setFormActivities(lesson.activities.length > 0 ? [...lesson.activities] : [""]);
    setNewActInput("");
    setFormApproveNow(Boolean(lesson.approvedForSession || lesson.title === pinnedLessonTitle));
    setFormRemixedFrom(lesson.remixedFrom);
    setImportErrorMode("NONE");
    setShowUploadPanelInModal(false);
    setEditorOpen(true);
  };

  const populateFormFromTemplate = (tpl: TeacherLessonCard) => {
    setEditingLessonId(null);
    setFormTitle(tpl.title);
    setFormTopic(tpl.topic);
    setFormAgeBand(tpl.ageBand);
    setFormVisibility("Trong trường");
    setFormDescription(tpl.description);
    setFormObjectives(tpl.objectives);
    setFormActivities([...tpl.activities]);
    setNewActInput("");
    setFormApproveNow(true);
    setFormRemixedFrom(`${tpl.title} (${tpl.version})`);
    setLibraryOpen(false);
    setEditorOpen(true);
    showToast(`Đã nạp toàn bộ nội dung mẫu "${tpl.title}" vào biểu mẫu giáo án.`, "ok");
  };

  useEffect(() => {
    const st = location.state as LessonLocationState | null;
    if (!st) return;
    if (st.tab === "grants") {
      setActiveTab("grants");
    }
    if (st.preloadTemplate) {
      populateFormFromTemplate(st.preloadTemplate);
      navigate(location.pathname, { replace: true, state: null });
      return;
    }
    if (st.openUploadModal) {
      openBlankCreateModal(true);
      navigate(location.pathname, { replace: true, state: null });
      return;
    }
    if (st.openCreateModal) {
      openBlankCreateModal(false);
      navigate(location.pathname, { replace: true, state: null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (libraryOpen) return; // handled by PublicLibraryModal
      if (editorOpen) setEditorOpen(false);
      else if (detailLesson) setDetailLesson(null);
      else if (shareModalOpen) setShareModalOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [libraryOpen, editorOpen, detailLesson, shareModalOpen]);

  const handleModalFileExtract = (file: File | undefined) => {
    if (!file) return;
    if (!/\.(pdf|pptx|docx)$/i.test(file.name)) {
      showToast("Chỉ hỗ trợ tệp PDF, PPTX hoặc DOCX có lớp văn bản.", "err");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setImportErrorMode("TOO_LARGE");
      return;
    }
    handleRealDocumentUpload(file.name, file.size);
    const baseName = file.name.replace(/\.(pdf|pptx|docx)$/i, "").replace(/[_-]+/g, " ").trim();
    setFormTitle(baseName || "Khám phá khu vườn mùa xuân");
    setFormTopic("Thiên nhiên");
    setFormDescription(
      `Giáo án được trích xuất tự động từ tệp "${file.name}". Bao gồm hoạt động quan sát trực quan, thảo luận nhóm và thực hành vẽ sáng tạo trên giấy A4.`
    );
    setFormObjectives(
      "Giúp trẻ nhận biết đặc điểm hình dáng, màu sắc chủ thể trong bài học và tự tin thể hiện ý tưởng qua bức vẽ cá nhân."
    );
    setFormActivities([
      "Hoạt động 1: Quan sát hình ảnh trực quan và trò chuyện mở đầu theo tài liệu",
      "Hoạt động 2: Thực hành vẽ từng nét cơ bản theo bảng hướng dẫn 16:9",
      "Hoạt động 3: Tô màu sáng tạo và kể lại câu chuyện của bức tranh",
    ]);
  };

  const handleQuickExtractDemo = () => {
    handleRealDocumentUpload("Giao_an_Kham_pha_mua_xuan.docx", 1840000);
    setFormTitle("Khám phá khu vườn mùa xuân");
    setFormTopic("Bông hoa");
    setFormAgeBand(AGE_BAND_OPTIONS[1]);
    setFormDescription(
      "Trích xuất từ tài liệu chuẩn của tổ chuyên môn: Trẻ quan sát cây cối đâm chồi, hoa nở và những chú bướm bay lượn trong vườn trường mùa xuân."
    );
    setFormObjectives(
      "Phát triển khả năng quan sát thiên nhiên, phối hợp nét cong – nét thẳng để vẽ bông hoa, tán lá và chia sẻ câu chuyện trước lớp."
    );
    setFormActivities([
      "Hoạt động 1: Dạo quanh sân trường quan sát chồi non và khóm hoa mùa xuân",
      "Hoạt động 2: Vẽ bông hoa và chiếc lá xanh theo từng bước trên bảng 16:9",
      "Hoạt động 3: Trưng bày tranh vẽ và chọn 1 bức tranh tiêu biểu tạo video mẫu",
    ]);
  };

  const handleSaveLesson = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) {
      showToast("Vui lòng nhập tiêu đề giáo án.", "warn");
      return;
    }
    const cleanedActs = formActivities.map((a) => a.trim()).filter(Boolean);
    if (cleanedActs.length === 0) {
      showToast("Vui lòng giữ ít nhất 1 hoạt động trong giáo án.", "warn");
      return;
    }

    if (editingLessonId) {
      updateLesson(editingLessonId, {
        title: formTitle,
        topic: formTopic,
        ageBand: formAgeBand,
        visibility: formVisibility,
        description: formDescription,
        objectives: formObjectives,
        activities: cleanedActs,
        approvedForSession: formApproveNow,
      });
      if (formApproveNow) {
        approveLessonForSession(editingLessonId);
      }
    } else {
      createLesson({
        title: formTitle,
        topic: formTopic,
        ageBand: formAgeBand,
        visibility: formVisibility,
        description: formDescription,
        objectives: formObjectives,
        activities: cleanedActs,
        approvedForSession: formApproveNow,
        remixedFrom: formRemixedFrom,
      });
    }
    setEditorOpen(false);
  };

  const handleCreateGrant = (e: React.FormEvent) => {
    e.preventDefault();
    if (!shareRecipient.trim()) {
      showToast("Vui lòng nhập tên giáo viên hoặc nhóm nhận chia sẻ.", "warn");
      return;
    }
    addLessonGrant(
      shareRecipient.trim(),
      `Giáo án: ${shareLessonTitle} (${sharePermission})`,
      shareExpiry
    );
    setShareModalOpen(false);
  };

  const q = search.trim().toLowerCase();
  const filteredLessons = lessons.filter((l) => {
    const matchVis = visFilter === "Tất cả" || l.visibility === visFilter;
    const matchText =
      !q ||
      l.title.toLowerCase().includes(q) ||
      l.topic.toLowerCase().includes(q) ||
      l.description.toLowerCase().includes(q) ||
      l.objectives.toLowerCase().includes(q);
    return matchVis && matchText;
  });

  const sessionApproved =
    occurrenceStatus === "APPROVED" ||
    occurrenceStatus === "SAMPLE_AVAILABLE" ||
    occurrenceStatus === "SAMPLE_USED";

  return (
    <div className="tw-page">
      <PageHead
        title="Quản lý giáo án"
        hint="Tạo, sửa và chia sẻ giáo án."
        right={
          <div className="tw-row tw-wrap">
            <button
              type="button"
              className="tw-btn is-ghost"
              onClick={() => setLibraryOpen(true)}
            >
              <Icon name="star" size={18} /> Thư viện công khai
            </button>
            <button
              type="button"
              className="tw-btn"
              onClick={() => openBlankCreateModal(false)}
            >
              <Icon name="plus" size={18} /> Tạo giáo án
            </button>
          </div>
        }
      />

      {/* Thanh trạng thái giáo án đang ghim cho buổi học */}
      <div className="tw-card is-mint tw-row tw-between tw-wrap" style={{ padding: "16px 22px" }}>
        <div className="tw-row" style={{ gap: 14 }}>
          <IconTile name="shield" tone="is-mint" />
          <div>
            <div className="tw-strong" style={{ fontSize: 16 }}>
              Đang dùng: “{pinnedLessonTitle}”
            </div>
            <div className="tw-meta" style={{ fontSize: 13.5 }}>
              Bản #{pinnedPlanRevision} ·{" "}
              {sessionApproved ? "Đã duyệt" : "Chờ duyệt"}
            </div>
          </div>
        </div>
        <div className="tw-row tw-wrap">
          <button
            type="button"
            className="tw-btn is-mint is-sm"
            disabled={!sessionApproved || !safetyChecklistConfirmed}
            title={!sessionApproved || !safetyChecklistConfirmed ? "Duyệt kế hoạch và checklist an toàn trước khi tiếp tục." : undefined}
            onClick={() => navigate("/t04-session-sketch-deck")}
          >
            <Icon name="palette" size={16} /> Mở AI Assisted
          </button>
          <button
            type="button"
            className="tw-btn is-ghost is-sm"
            disabled={!sessionApproved || !safetyChecklistConfirmed}
            title={!sessionApproved || !safetyChecklistConfirmed ? "Duyệt kế hoạch và checklist an toàn trước khi tiếp tục." : undefined}
            onClick={() => navigate("/t06-sample-story-run")}
          >
            <Icon name="video" size={16} /> Tạo video mẫu
          </button>
        </div>
      </div>

      {/* Segmented Tabs: Danh sách giáo án (CRUD) | Quyền chia sẻ giáo án */}
      <div className="tw-row tw-between tw-wrap">
        <div className="tw-tabs-seg" role="tablist" aria-label="Chế độ quản lý giáo án">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "lessons"}
            className={"tw-tab-seg" + (activeTab === "lessons" ? " is-on" : "")}
            onClick={() => setActiveTab("lessons")}
          >
            <Icon name="book" size={17} /> Giáo án ({lessons.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "grants"}
            className={"tw-tab-seg" + (activeTab === "grants" ? " is-on" : "")}
            onClick={() => setActiveTab("grants")}
          >
            <Icon name="share" size={17} /> Chia sẻ ({grants.length})
          </button>
        </div>

        {activeTab === "grants" && (
          <button
            type="button"
            className="tw-btn is-sm"
            onClick={() => {
              if (lessons[0]) setShareLessonTitle(lessons[0].title);
              setShareModalOpen(true);
            }}
          >
            <Icon name="plus" size={16} /> Chia sẻ giáo án
          </button>
        )}
      </div>

      {activeTab === "lessons" ? (
        <>
          {/* Thanh tìm kiếm & Lọc phạm vi */}
          <div className="tw-card tw-row tw-between tw-wrap" style={{ padding: 16, gap: 12 }}>
            <input
              className="tw-input"
              style={{ flex: 1, minWidth: 240 }}
              placeholder="Tìm theo tên hoặc chủ đề"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Tìm kiếm giáo án"
            />
            <div className="tw-row tw-wrap" style={{ gap: 6 }}>
              {(["Tất cả", "Trong trường", "Công khai", "Riêng tư"] as const).map((pill) => (
                <button
                  key={pill}
                  type="button"
                  className={"tw-chip " + (visFilter === pill ? "" : "is-gray")}
                  style={{ cursor: "pointer", fontFamily: "inherit" }}
                  onClick={() => setVisFilter(pill)}
                >
                  {pill}
                </button>
              ))}
            </div>
          </div>

          {/* Danh sách thẻ giáo án đầy đủ CRUD */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {filteredLessons.map((l) => {
              const isPinned = l.title === pinnedLessonTitle;
              return (
                <div
                  key={l.id}
                  className="tw-card"
                  style={{ display: "flex", flexDirection: "column", gap: 14 }}
                >
                  <div className="tw-row tw-between tw-wrap" style={{ alignItems: "flex-start" }}>
                    <div className="tw-row" style={{ gap: 14, alignItems: "flex-start" }}>
                      <IconTile name={topicIconName(l.topic)} tone={topicTone(l.topic)} />
                      <div>
                        <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800 }}>{l.title}</h2>
                        <div className="tw-meta" style={{ marginTop: 3 }}>
                          {l.version} · Cập nhật {l.updatedAt}
                          {l.remixedFrom ? ` · Nguồn mẫu: ${l.remixedFrom}` : ""}
                        </div>
                        <div className="tw-row tw-wrap" style={{ gap: 8, marginTop: 8 }}>
                          <span className="tw-chip">{l.topic}</span>
                          <span className="tw-chip is-gray">{l.ageBand}</span>
                          <span className="tw-chip is-amber">{l.activities.length} hoạt động</span>
                          <span
                            className={
                              "tw-chip " +
                              (l.visibility === "Công khai"
                                ? "is-mint"
                                : l.visibility === "Trong trường"
                                ? ""
                                : "is-gray")
                            }
                          >
                            {l.visibility}
                          </span>
                          {(isPinned || l.approvedForSession) && (
                            <span className="tw-chip is-mint">
                              <Icon name="check" size={13} /> {isPinned ? "Đang ghim cho buổi học" : "Đã duyệt an toàn"}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="tw-row tw-wrap" style={{ gap: 8 }}>
                      <button
                        type="button"
                        className="tw-btn is-mint is-sm"
                        onClick={() => {
                          setSafetyChecklistConfirmed(true);
                          setDetailLesson(l);
                        }}
                      >
                        <Icon name="eye" size={16} /> Xem
                      </button>
                      <button
                        type="button"
                        className="tw-btn is-ghost is-sm"
                        title="Chỉnh sửa giáo án"
                        aria-label="Chỉnh sửa giáo án"
                        onClick={() => openEditModal(l)}
                      >
                        <Icon name="edit" size={16} />
                      </button>
                      <button
                        type="button"
                        className="tw-btn is-ghost is-sm"
                        title="Chia sẻ giáo án"
                        aria-label="Chia sẻ giáo án"
                        onClick={() => {
                          setShareLessonTitle(l.title);
                          setShareModalOpen(true);
                        }}
                      >
                        <Icon name="share" size={16} />
                      </button>
                      <button
                        type="button"
                        className="tw-btn is-danger is-sm"
                        aria-label={`Xóa giáo án ${l.title}`} title="Xóa giáo án"
                        onClick={() => setArchiveModalTarget(l)}
                      >
                        <Icon name="trash" size={16} />
                      </button>
                    </div>
                  </div>

                </div>
              );
            })}

            {filteredLessons.length === 0 && (
              <div className="tw-card" style={{ textAlign: "center", padding: 32 }}>
                <h2 style={{ fontSize: 19, fontWeight: 700 }}>Không tìm thấy giáo án phù hợp</h2>
                <p className="tw-sub" style={{ margin: "6px auto 16px" }}>
                  Cô có thể tạo giáo án mới, nạp mẫu từ Thư viện công khai hoặc khôi phục danh sách mẫu mặc định.
                </p>
                <div className="tw-row" style={{ justifyContent: "center", gap: 10 }}>
                  <button type="button" className="tw-btn" onClick={() => openBlankCreateModal(false)}>
                    <Icon name="plus" size={16} /> Tạo giáo án mới
                  </button>
                  <button type="button" className="tw-btn is-ghost" onClick={restoreDefaultLessons}>
                    Khôi phục giáo án mặc định
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        /* Tab 2: Quyền chia sẻ giáo án (Access Grants) */
        <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="tw-row tw-between tw-wrap">
            <div className="tw-row">
              <IconTile name="share" tone="is-mint" />
              <div>
                <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>
                  Quyền chia sẻ giáo án trong trường (Access Grants)
                </h2>
                <p className="tw-meta" style={{ marginTop: 2 }}>
                  Cho phép tổ chuyên môn hoặc giáo viên dạy thay xem và sử dụng giáo án nội bộ trường.
                </p>
              </div>
            </div>
          </div>

          {grants.map((g) => (
            <div key={g.id} className="tw-row tw-between tw-wrap tw-item is-mint" style={{ padding: 16 }}>
              <div>
                <div className="tw-strong" style={{ fontSize: 15.5 }}>{g.recipient}</div>
                <div className="tw-meta" style={{ fontSize: 14, marginTop: 2 }}>{g.scope}</div>
                <div className="tw-meta" style={{ fontSize: 12.5, marginTop: 3 }}>
                  Thời hạn: {g.expiresAt} · Trạng thái: {g.status}
                </div>
              </div>
              <div className="tw-row" style={{ gap: 8 }}>
                {g.status === "Đã thu hồi" ? (
                  <span className="tw-chip is-gray">Đã thu hồi</span>
                ) : (
                  <>
                    <span className="tw-chip is-mint">Đang hiệu lực</span>
                    <button
                      type="button"
                      className="tw-btn is-danger is-sm"
                      onClick={() => revokeTeacherGrant(g.id)}
                    >
                      Thu hồi quyền
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── MODAL 1: Tạo mới / Chỉnh sửa & Upload Giáo án ── */}
      {editorOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="lesson-editor-title"
          className="tw-modal-backdrop"
          onClick={() => setEditorOpen(false)}
        >
          <form
            onSubmit={handleSaveLesson}
            className="tw-modal is-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="tw-row tw-between tw-wrap">
              <div className="tw-row">
                <IconTile name={editingLessonId ? "edit" : "plus"} tone={editingLessonId ? "is-amber" : ""} />
                <div>
                  <h2 id="lesson-editor-title" style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>
                    {editingLessonId ? "Chỉnh sửa toàn bộ giáo án" : "Tạo giáo án mới"}
                  </h2>
                  <div className="tw-meta">
                    Nhập trực tiếp, tải tệp PDF/PPTX/DOCX hoặc nạp nhanh từ Thư viện mẫu công khai.
                  </div>
                </div>
              </div>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setEditorOpen(false)}
              >
                <Icon name="close" size={16} /> Đóng
              </button>
            </div>

            {/* Thanh công cụ nhanh ngay trong Modal: Upload tài liệu + Chọn từ Thư viện */}
            <div className="tw-item is-sky" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div className="tw-row tw-between tw-wrap">
                <div className="tw-row" style={{ gap: 8 }}>
                  <Icon name="upload" size={18} />
                  <span className="tw-strong" style={{ fontSize: 14 }}>
                    Tệp PDF / PPTX / DOCX · tối đa 25 MB
                  </span>
                </div>
                <div className="tw-row tw-wrap" style={{ gap: 8 }}>
                  <input
                    ref={modalFileRef}
                    type="file"
                    accept=".pdf,.pptx,.docx"
                    hidden
                    onChange={(e) => handleModalFileExtract(e.target.files?.[0])}
                  />
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    onClick={() => {
                      setShowUploadPanelInModal(true);
                      modalFileRef.current?.click();
                    }}
                  >
                    <Icon name="upload" size={15} /> Chọn tệp từ máy
                  </button>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    onClick={handleQuickExtractDemo}
                  >
                    <Icon name="wand" size={15} /> Trích xuất tệp mẫu
                  </button>
                  <button
                    type="button"
                    className="tw-btn is-amber is-sm"
                    onClick={() => setLibraryOpen(true)}
                  >
                    <Icon name="star" size={15} /> Nạp từ Thư viện mẫu
                  </button>
                </div>
              </div>

              {showUploadPanelInModal && (
                <div className="tw-row tw-between tw-wrap" style={{ paddingTop: 4 }}>
                  <span className="tw-meta" style={{ fontSize: 12.5 }}>
                    Tệp gần nhất: <strong>{uploadedFileName}</strong> ({uploadedFileSizeMb} · Rev #{documentRevision})
                  </span>
                  <div className="tw-row tw-wrap" style={{ gap: 6 }}>
                    <span className="tw-meta" style={{ fontSize: 12 }}>Mô phỏng lỗi tải tệp:</span>
                    {(Object.keys(IMPORT_ERRORS) as Exclude<ImportErrorMode, "NONE">[]).map((m) => (
                      <button
                        key={m}
                        type="button"
                        className="tw-chip is-gray"
                        style={{ cursor: "pointer", fontFamily: "inherit", fontSize: 12, padding: "4px 9px" }}
                        onClick={() => setImportErrorMode(m)}
                      >
                        {m === "TOO_LARGE"
                          ? "> 25 MB"
                          : m === "TOO_MANY_PAGES"
                          ? "> 100 trang"
                          : m === "SCANNED_PDF"
                          ? "PDF scan"
                          : "Khóa mật khẩu"}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {importErrorMode !== "NONE" && (
                <div className="tw-item is-rose tw-row tw-between" role="alert">
                  <div className="tw-row">
                    <Icon name="alert" size={18} />
                    <span className="tw-strong" style={{ fontSize: 13.5 }}>
                      {IMPORT_ERRORS[importErrorMode]}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    onClick={() => setImportErrorMode("NONE")}
                  >
                    Đã hiểu
                  </button>
                </div>
              )}
            </div>

            <div className="tw-grid-2">
              <label className="tw-label">
                Tiêu đề giáo án
                <input
                  className="tw-input"
                  placeholder="Ví dụ: Vòng đời bướm mùa xuân"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  required
                />
              </label>

              <label className="tw-label">
                Chủ đề bài học
                <select
                  className="tw-input"
                  value={formTopic}
                  onChange={(e) => setFormTopic(e.target.value)}
                >
                  {TOPIC_OPTIONS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="tw-grid-2">
              <label className="tw-label">
                Độ tuổi mục tiêu (36–155 tháng)
                <select
                  className="tw-input"
                  value={formAgeBand}
                  onChange={(e) => setFormAgeBand(e.target.value)}
                >
                  {AGE_BAND_OPTIONS.map((age) => (
                    <option key={age} value={age}>
                      {age}
                    </option>
                  ))}
                </select>
              </label>

              <label className="tw-label">
                Phạm vi hiển thị
                <select
                  className="tw-input"
                  value={formVisibility}
                  onChange={(e) =>
                    setFormVisibility(e.target.value as TeacherLessonCard["visibility"])
                  }
                >
                  <option value="Riêng tư">Riêng tư (Bản nháp cá nhân)</option>
                  <option value="Trong trường">Trong trường (Chia sẻ nội bộ)</option>
                  <option value="Công khai">Công khai (Gửi duyệt thư viện chung)</option>
                </select>
              </label>
            </div>

            <label className="tw-label">
              Mô tả bài học
              <textarea
                className="tw-input"
                rows={2}
                placeholder="Tóm tắt nội dung và bối cảnh tổ chức tiết học..."
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
              />
            </label>

            <label className="tw-label">
              Mục tiêu sư phạm
              <textarea
                className="tw-input"
                rows={2}
                placeholder="Kiến thức, kỹ năng quan sát, mỹ thuật và thái độ trẻ đạt được..."
                value={formObjectives}
                onChange={(e) => setFormObjectives(e.target.value)}
              />
            </label>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div className="tw-row tw-between">
                <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>
                  Danh sách hoạt động trên lớp ({formActivities.length})
                </h3>
                <span className="tw-meta" style={{ fontSize: 12.5 }}>
                  Cô có thể sửa trực tiếp từng dòng hoặc thêm hoạt động mới
                </span>
              </div>

              {formActivities.map((act, idx) => (
                <div key={idx} className="tw-row" style={{ gap: 8 }}>
                  <span className="tw-chip is-mint">#{idx + 1}</span>
                  <input
                    className="tw-input"
                    value={act}
                    aria-label={`Hoạt động ${idx + 1}`}
                    onChange={(e) => {
                      const next = [...formActivities];
                      next[idx] = e.target.value;
                      setFormActivities(next);
                    }}
                  />
                  <button
                    type="button"
                    className="tw-btn is-ghost is-sm"
                    aria-label={`Xóa hoạt động ${idx + 1}`}
                    disabled={formActivities.length <= 1}
                    onClick={() =>
                      setFormActivities(formActivities.filter((_, j) => j !== idx))
                    }
                  >
                    <Icon name="trash" size={15} />
                  </button>
                </div>
              ))}

              <div className="tw-row" style={{ gap: 8, marginTop: 4 }}>
                <input
                  className="tw-input"
                  placeholder="Nhập hoạt động mới rồi nhấn + Thêm..."
                  value={newActInput}
                  onChange={(e) => setNewActInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      if (newActInput.trim()) {
                        setFormActivities([...formActivities, newActInput.trim()]);
                        setNewActInput("");
                      }
                    }
                  }}
                />
                <button
                  type="button"
                  className="tw-btn is-ghost is-sm"
                  disabled={!newActInput.trim()}
                  onClick={() => {
                    setFormActivities([...formActivities, newActInput.trim()]);
                    setNewActInput("");
                  }}
                >
                  <Icon name="plus" size={16} /> Thêm hoạt động
                </button>
              </div>
            </div>

            <label className="tw-item is-amber tw-row" style={{ cursor: "pointer", gap: 12 }}>
              <input
                type="checkbox"
                checked={formApproveNow}
                onChange={(e) => setFormApproveNow(e.target.checked)}
                style={{ width: 20, height: 20 }}
              />
              <span style={{ fontSize: 14, fontWeight: 600 }}>
                Xác nhận giáo án phù hợp lứa tuổi và ghim cho buổi học hiện tại
              </span>
            </label>

            <div className="tw-row tw-between tw-wrap">
              <button
                type="button"
                className="tw-btn is-ghost"
                onClick={() => setEditorOpen(false)}
              >
                Hủy bỏ
              </button>
              <button type="submit" className="tw-btn">
                <Icon name="check" size={18} />{" "}
                {editingLessonId ? "Lưu cập nhật giáo án" : "Tạo & Lưu giáo án"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── MODAL 2: Xem chi tiết & Duyệt an toàn cho buổi học (BR-14) ── */}
      {detailLesson && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="lesson-detail-title"
          className="tw-modal-backdrop"
          onClick={() => setDetailLesson(null)}
        >
          <div className="tw-modal is-lg" onClick={(e) => e.stopPropagation()}>
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile
                  name={topicIconName(detailLesson.topic)}
                  tone={topicTone(detailLesson.topic)}
                />
                <div>
                  <h2 id="lesson-detail-title" style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>
                    {detailLesson.title}
                  </h2>
                  <div className="tw-meta">
                    {detailLesson.version} · Cập nhật {detailLesson.updatedAt} · {detailLesson.visibility}
                  </div>
                </div>
              </div>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setDetailLesson(null)}
              >
                <Icon name="close" size={16} /> Đóng
              </button>
            </div>

            <div className="tw-row tw-wrap">
              <span className="tw-chip">{detailLesson.topic}</span>
              <span className="tw-chip is-mint">{detailLesson.ageBand}</span>
              <span className="tw-chip is-amber">{detailLesson.activities.length} hoạt động</span>
            </div>

            <div className="tw-item is-sky" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <h3 style={{ margin: 0, fontSize: 15.5, fontWeight: 700 }}>Mô tả tổng quan</h3>
              <p style={{ fontSize: 15, lineHeight: 1.55 }}>{detailLesson.description}</p>
            </div>

            <div className="tw-item is-mint" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <h3 style={{ margin: 0, fontSize: 15.5, fontWeight: 700 }}>Mục tiêu sư phạm</h3>
              <p style={{ fontSize: 15, lineHeight: 1.55 }}>{detailLesson.objectives}</p>
            </div>

            <div className="tw-item" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: 15.5, fontWeight: 700 }}>
                Danh sách hoạt động ({detailLesson.activities.length})
              </h3>
              {detailLesson.activities.map((a, idx) => (
                <div key={a + idx} className="tw-row" style={{ alignItems: "flex-start" }}>
                  <span className="tw-chip is-mint">Bước {idx + 1}</span>
                  <span style={{ fontSize: 15 }}>{a}</span>
                </div>
              ))}
            </div>

            <div className="tw-item" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <h3 style={{ margin: 0, fontSize: 15.5, fontWeight: 700 }}>Lịch sử phiên bản bất biến</h3>
              {detailLesson.versionHistory.map((vh) => (
                <div key={vh} className="tw-meta" style={{ fontSize: 13.5 }}>
                  • {vh}
                </div>
              ))}
            </div>

            <label className="tw-item is-amber tw-row" style={{ cursor: "pointer", gap: 12 }}>
              <input
                type="checkbox"
                checked={safetyChecklistConfirmed}
                onChange={(e) => setSafetyChecklistConfirmed(e.target.checked)}
                style={{ width: 20, height: 20 }}
              />
              <span style={{ fontWeight: 600, fontSize: 14 }}>
                Xác nhận giáo án và hoạt động phù hợp lứa tuổi trước khi mở AI Assisted hoặc tạo video mẫu.
              </span>
            </label>

            <div className="tw-row tw-between tw-wrap">
              <button
                type="button"
                className="tw-btn is-ghost"
                onClick={() => {
                  const target = detailLesson;
                  setDetailLesson(null);
                  openEditModal(target);
                }}
              >
                <Icon name="edit" size={16} /> giáo án này
              </button>
              <button
                type="button"
                className="tw-btn is-mint"
                disabled={!safetyChecklistConfirmed}
                onClick={() => {
                  approveLessonForSession(detailLesson.id);
                  setDetailLesson(null);
                }}
              >
                <Icon name="check" size={18} /> Duyệt &amp; Ghim cho buổi học
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL 3: Chia sẻ giáo án nội bộ trường (Access Grant) ── */}
      {shareModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="share-modal-title"
          className="tw-modal-backdrop"
          onClick={() => setShareModalOpen(false)}
        >
          <form
            onSubmit={handleCreateGrant}
            className="tw-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="tw-row tw-between">
              <div className="tw-row">
                <IconTile name="share" tone="is-mint" />
                <h2 id="share-modal-title" style={{ margin: 0, fontSize: 21, fontWeight: 800 }}>
                  Chia sẻ giáo án trong trường
                </h2>
              </div>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setShareModalOpen(false)}
              >
                <Icon name="close" size={16} />
              </button>
            </div>

            <label className="tw-label">
              Chọn giáo án cần chia sẻ
              <select
                className="tw-input"
                value={shareLessonTitle}
                onChange={(e) => setShareLessonTitle(e.target.value)}
              >
                {lessons.map((l) => (
                  <option key={l.id} value={l.title}>
                    {l.title} ({l.version})
                  </option>
                ))}
              </select>
            </label>

            <label className="tw-label">
              Giáo viên hoặc Tổ chuyên môn nhận quyền
              <input
                className="tw-input"
                placeholder="Ví dụ: Cô Mai · Lớp Chồi 1 hoặc Tổ Khối Lá"
                value={shareRecipient}
                onChange={(e) => setShareRecipient(e.target.value)}
                required
              />
            </label>

            <div className="tw-grid-2">
              <label className="tw-label">
                Phạm vi quyền
                <select
                  className="tw-input"
                  value={sharePermission}
                  onChange={(e) => setSharePermission(e.target.value)}
                >
                  <option>Quyền xem &amp; Remix nội bộ trường</option>
                  <option>Quyền dạy thay buổi học</option>
                  <option>Chỉ xem tham khảo chuyên môn</option>
                </select>
              </label>

              <label className="tw-label">
                Ngày hết hạn
                <input
                  className="tw-input"
                  value={shareExpiry}
                  onChange={(e) => setShareExpiry(e.target.value)}
                />
              </label>
            </div>

            <div className="tw-row tw-between" style={{ marginTop: 4 }}>
              <button
                type="button"
                className="tw-btn is-ghost"
                onClick={() => setShareModalOpen(false)}
              >
                Hủy
              </button>
              <button type="submit" className="tw-btn is-mint">
                <Icon name="share" size={17} /> Cấp quyền chia sẻ
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── MODAL 4: Thư viện công khai ── */}
      <PublicLibraryModal
        open={libraryOpen}
        onClose={() => setLibraryOpen(false)}
        templates={publicTemplates}
        onSelectTemplate={populateFormFromTemplate}
        primaryActionLabel="Nạp mẫu vào Giáo án"
      />
    </div>
  );
}

/* ───────────── T03: Trình Import tài liệu chuyên sâu (Giữ tương thích nếu truy cập trực tiếp) ───────────── */
export function T03DocumentImportReviewPage() {
  const navigate = useNavigate();
  const {
    importErrorMode,
    setImportErrorMode,
    uploadedFileName,
    uploadedFileSizeMb,
    uploadedSha256,
    documentRevision,
    handleRealDocumentUpload,
    approveExtractedDocumentRevision,
    createLesson,
    lessons,
    showToast,
  } = useTeacher();

  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [uploaded, setUploaded] = useState(true);
  const base = lessons[0];
  const [fields, setFields] = useState({
    title: base?.title ?? "Vòng đời bướm",
    objectives: base?.objectives ?? "",
    activities:
      "Hoạt động 1: Quan sát hình ảnh, đặc điểm cánh bướm ngoài vườn trường\nHoạt động 2: Vẽ con bướm đối xứng trên giấy A4",
  });

  const accept = (file: File | undefined) => {
    if (!file) return;
    if (!/\.(pdf|pptx|docx)$/i.test(file.name)) {
      showToast("Chỉ nhận tệp PDF, PPTX hoặc DOCX.", "err");
      return;
    }
    handleRealDocumentUpload(file.name, file.size);
    setUploaded(true);
  };

  return (
    <div className="tw-page">
      <PageHead
        title="Nhập tài liệu & Chỉnh sửa nội dung trích xuất"
        hint="Hỗ trợ PDF, PPTX, DOCX có thể chọn văn bản · tối đa 25 MB, 100 trang hoặc slide."
        right={
          <button
            type="button"
            className="tw-btn is-ghost"
            onClick={() => navigate("/t02-lesson-authoring")}
          >
            <Icon name="arrow-left" size={16} /> Quay lại Quản lý giáo án
          </button>
        }
      />

      <div className="tw-grid-2">
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div
            className={"tw-drop" + (over ? " is-over" : "")}
            onDragOver={(e) => {
              e.preventDefault();
              setOver(true);
            }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setOver(false);
              accept(e.dataTransfer.files?.[0]);
            }}
          >
            <div className="tw-row" style={{ justifyContent: "center", gap: 10 }}>
              <Icon name="upload" size={24} color="#2563EB" />
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Kéo thả tệp giáo án vào đây</h2>
            </div>
            <p className="tw-sub" style={{ fontSize: 13.5 }}>
              Hỗ trợ PDF, PPTX, DOCX (Tối đa 25 MB · 100&nbsp;trang)
            </p>
            <div className="tw-row tw-wrap" style={{ justifyContent: "center" }}>
              <span className="tw-chip is-rose">PDF</span>
              <span className="tw-chip is-amber">PPTX</span>
              <span className="tw-chip">DOCX</span>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.pptx,.docx"
              hidden
              onChange={(e) => accept(e.target.files?.[0] ?? undefined)}
            />
            <button type="button" className="tw-btn" onClick={() => inputRef.current?.click()}>
              <Icon name="upload" size={18} /> Chọn tệp từ máy
            </button>
          </div>

          <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
              Tệp đã tải lên (Provenance SHA-256)
            </h2>
            <div className="tw-row tw-between tw-item is-sky" style={{ padding: 12 }}>
              <div>
                <div className="tw-strong" style={{ fontSize: 13.5 }}>{uploadedFileName}</div>
                <div className="tw-meta" style={{ fontSize: 12.5 }}>
                  {uploadedFileSizeMb} · {uploadedSha256}
                </div>
              </div>
              <span className="tw-chip is-mint">Hợp lệ</span>
            </div>
          </div>

          <div className="tw-row tw-wrap" style={{ gap: 8 }}>
            <span className="tw-meta" style={{ fontSize: 12.5 }}>
              Mô phỏng lỗi tải tệp:
            </span>
            {(Object.keys(IMPORT_ERRORS) as Exclude<ImportErrorMode, "NONE">[]).map((m) => (
              <button
                key={m}
                type="button"
                className="tw-chip is-gray"
                style={{ cursor: "pointer", fontFamily: "inherit" }}
                onClick={() => setImportErrorMode(m)}
              >
                {m === "TOO_LARGE"
                  ? "> 25 MB"
                  : m === "TOO_MANY_PAGES"
                  ? "> 100 trang"
                  : m === "SCANNED_PDF"
                  ? "PDF ảnh scan"
                  : "Khóa mật khẩu"}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {importErrorMode !== "NONE" && (
            <div className="tw-card is-amber tw-row" role="alert">
              <IconTile name="alert" tone="is-rose" />
              <strong style={{ flex: 1 }}>{IMPORT_ERRORS[importErrorMode]}</strong>
              <button
                type="button"
                className="tw-btn is-ghost is-sm"
                onClick={() => setImportErrorMode("NONE")}
              >
                Đã hiểu
              </button>
            </div>
          )}

          {uploaded && importErrorMode === "NONE" && (
            <div className="tw-card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div className="tw-row tw-between tw-wrap">
                <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
                  Nội dung trích xuất từ tài liệu
                </h2>
                <span className="tw-chip is-mint">Revision #{documentRevision}</span>
              </div>
              <label className="tw-label">
                Tiêu đề giáo án
                <input
                  className="tw-input"
                  value={fields.title}
                  onChange={(e) => setFields({ ...fields, title: e.target.value })}
                />
              </label>
              <label className="tw-label">
                Mục tiêu &amp; Ghi chú sư phạm
                <textarea
                  className="tw-input"
                  rows={3}
                  value={fields.objectives}
                  onChange={(e) => setFields({ ...fields, objectives: e.target.value })}
                />
              </label>
              <label className="tw-label">
                Danh sách hoạt động trích xuất (mỗi dòng 1 hoạt động)
                <textarea
                  className="tw-input"
                  rows={4}
                  value={fields.activities}
                  onChange={(e) => setFields({ ...fields, activities: e.target.value })}
                />
              </label>
              <div className="tw-row tw-between tw-wrap">
                <button
                  type="button"
                  className="tw-btn is-ghost"
                  onClick={() => inputRef.current?.click()}
                >
                  Chọn tệp khác
                </button>
                <button
                  type="button"
                  className="tw-btn is-mint"
                  onClick={() => {
                    approveExtractedDocumentRevision();
                    createLesson({
                      title: fields.title,
                      topic: "Thiên nhiên",
                      ageBand: "4–5 tuổi (48–59 tháng)",
                      visibility: "Trong trường",
                      description: `Trích xuất từ tài liệu ${uploadedFileName}.`,
                      objectives: fields.objectives,
                      activities: fields.activities.split("\n").filter(Boolean),
                      approvedForSession: true,
                    });
                    navigate("/t02-lesson-authoring");
                  }}
                >
                  <Icon name="check" size={18} /> Lưu vào Quản lý giáo án
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
