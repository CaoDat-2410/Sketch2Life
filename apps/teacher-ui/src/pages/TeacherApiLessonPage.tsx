import React, { useEffect, useState } from "react";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  type LessonActivity,
  type LessonContent,
  type LessonSummary,
  type TeacherLessonDetail,
} from "../../../shared/backendApi";
import { useTeacher } from "../context/TeacherContext";
import { Icon } from "../components/Icon";
import { PageHead } from "./T01WorkspaceScreen";

const blankActivity = (): LessonActivity => ({
  title: "",
  objective: "",
  materials_text: "",
  preparation_text: "",
  instructions_text: "",
  observation_notes: "",
  safety_notes: "",
  activity_kind: "outdoor",
});

const blankContent = (): LessonContent => ({
  locale: "vi-VN",
  title: "",
  topic: "",
  target_age_band_ref: "age-3-6",
  target_age_band_version: 1,
  objectives: [""],
  drawing_subject: "",
  drawing_steps_text: "",
  subject_learning_notes: "",
  script_direction: null,
  script_following_allowed: false,
  activities: [blankActivity()],
});

const fieldStyle: React.CSSProperties = { display: "grid", gap: 6, fontWeight: 700, fontSize: 13.5 };
const inputStyle: React.CSSProperties = { width: "100%", boxSizing: "border-box" };

export function TeacherApiLessonPage() {
  const { showToast } = useTeacher();
  const [items, setItems] = useState<LessonSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TeacherLessonDetail | null>(null);
  const [content, setContent] = useState<LessonContent>(blankContent);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const organizationId = configuredOrganizationId();

  useEffect(() => {
    let active = true;
    if (!hasFirebaseAuthBridge()) {
      setPageError("Chưa có Firebase ID token để tải giáo án.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setPageError("Chưa cấu hình organization_id cho API Lesson Library.");
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    setPageError(null);
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản không có assignment teacher trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.lessons(organizationId);
      })
      .then((page) => { if (active) setItems(page.items); })
      .catch((cause: unknown) => { if (active) setPageError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [organizationId, reload]);

  useEffect(() => {
    let active = true;
    if (!selectedId) {
      setDetail(null);
      setDetailError(null);
      return () => { active = false; };
    }
    setDetail(null);
    setContent(blankContent());
    setDetailError(null);
    backendApi.teacherLesson(organizationId, selectedId)
      .then((result) => {
        if (!active) return;
        setDetail(result);
        if (result.current_version.content) setContent(result.current_version.content);
        else setDetailError("Phiên bản hiện tại không có structured content để sửa.");
      })
      .catch((cause: unknown) => { if (active) setDetailError(backendMessage(cause)); })
      .finally(() => { if (active) setSaving(false); });
    return () => { active = false; };
  }, [organizationId, selectedId]);

  const updateContent = (change: Partial<LessonContent>) => setContent((current) => ({ ...current, ...change }));
  const updateActivity = (index: number, change: Partial<LessonActivity>) => updateContent({
    activities: content.activities.map((activity, i) => i === index ? { ...activity, ...change } : activity),
  });

  const newLesson = () => {
    setSelectedId(null);
    setDetail(null);
    setContent(blankContent());
    setDetailError(null);
  };

  const normalizedContent = (): LessonContent => ({
    ...content,
    title: content.title.trim(),
    topic: content.topic.trim(),
    target_age_band_ref: content.target_age_band_ref.trim(),
    objectives: content.objectives.map((objective) => objective.trim()).filter(Boolean),
    drawing_subject: content.drawing_subject.trim(),
    drawing_steps_text: content.drawing_steps_text.trim(),
    subject_learning_notes: content.subject_learning_notes.trim(),
    script_direction: content.script_direction?.trim() || null,
    activities: content.activities.map((activity) => ({
      ...activity,
      title: activity.title.trim(),
      objective: activity.objective.trim(),
      materials_text: activity.materials_text.trim(),
      preparation_text: activity.preparation_text.trim(),
      instructions_text: activity.instructions_text.trim(),
      observation_notes: activity.observation_notes.trim(),
      safety_notes: activity.safety_notes.trim(),
    })),
  });

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    const payload = normalizedContent();
    if (!payload.title || !payload.topic || !payload.target_age_band_ref || !payload.drawing_subject || !payload.drawing_steps_text || !payload.subject_learning_notes || payload.objectives.length === 0 || payload.activities.length === 0 || payload.activities.some((activity) => !activity.title || !activity.objective || !activity.instructions_text)) {
      setDetailError("Điền tiêu đề, chủ đề, nhóm tuổi, mục tiêu, nội dung vẽ và các trường bắt buộc của ít nhất một hoạt động.");
      return;
    }
    if (!/^[A-Za-z0-9._:-]{1,256}$/.test(payload.target_age_band_ref) || payload.objectives.length > 12 || payload.objectives.some((objective) => objective.length > 1000)) {
      setDetailError("Nhóm tuổi phải là mã API hợp lệ; số mục tiêu tối đa 12 và mỗi mục tiêu tối đa 1.000 ký tự.");
      return;
    }
    if (!Number.isInteger(payload.target_age_band_version) || payload.target_age_band_version < 1) {
      setDetailError("target_age_band_version phải là số nguyên từ 1 trở lên.");
      return;
    }
    setSaving(true);
    setDetailError(null);
    try {
      const result = detail
        ? await backendApi.updateLesson(organizationId, detail, payload)
        : await backendApi.createLesson(organizationId, payload);
      setSelectedId(result.lesson_id);
      setDetail(result);
      if (result.current_version.content) setContent(result.current_version.content);
      setItems((current) => [
        { contract: "LessonSummaryV1", lesson_id: result.lesson_id, title: payload.title, topic: payload.topic, current_version_no: result.current_version.version_no, review_state: result.current_version.review_state, visibility: result.visibility, activity_count: payload.activities.length, updated_at: result.updated_at },
        ...current.filter((item) => item.lesson_id !== result.lesson_id),
      ]);
      showToast(detail ? "Đã cập nhật giáo án qua API." : "Đã tạo giáo án riêng tư qua API.", "ok");
    } catch (cause) {
      setDetailError(backendMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  const requestPublic = async () => {
    if (!detail) return;
    setSaving(true);
    setDetailError(null);
    try {
      await backendApi.requestPublicReview(organizationId, detail);
      const updated = await backendApi.teacherLesson(organizationId, detail.lesson_id);
      setDetail(updated);
      if (updated.current_version.content) setContent(updated.current_version.content);
      showToast("Đã gửi grant PUBLIC để School Manager duyệt.", "ok");
      setReload((value) => value + 1);
    } catch (cause) {
      setDetailError(backendMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  const archive = async () => {
    if (!detail || !window.confirm(`Lưu trữ “${detail.current_version.content?.title ?? detail.lesson_id}”?`)) return;
    setSaving(true);
    setDetailError(null);
    try {
      await backendApi.archiveLesson(organizationId, detail);
      showToast("Đã lưu trữ giáo án.", "ok");
      setItems((current) => current.filter((item) => item.lesson_id !== detail.lesson_id));
      newLesson();
      setReload((value) => value + 1);
    } catch (cause) {
      setDetailError(backendMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="tw-page">
      <PageHead title="Giáo án của tổ chức" hint="Tạo và cập nhật theo LessonContentInputV1; giáo án mới luôn là PRIVATE cho đến khi gửi grant công khai." right={<button type="button" className="tw-btn" onClick={newLesson}><Icon name="plus" size={16} /> Giáo án mới</button>} />
      <BackendModeNotice roleLabel="Giáo viên" />
      {pageError && <BackendNotice title="Không tải được danh sách giáo án" tone="error">{pageError}</BackendNotice>}
      <div className="tw-grid-2" style={{ alignItems: "start", gap: 18 }}>
        <section className="tw-card">
          <div className="tw-row tw-between"><h2 className="tw-h2">Giáo án</h2><button type="button" className="tw-btn is-ghost is-sm" disabled={loading} onClick={() => setReload((value) => value + 1)}>Tải lại</button></div>
          {loading && <p className="tw-sub">Đang tải danh sách…</p>}
          {!loading && items.length === 0 && <p className="tw-sub">Chưa có giáo án trong phạm vi tài khoản.</p>}
          <div style={{ display: "grid", gap: 8 }}>{items.map((item) => <button key={item.lesson_id} type="button" className={`tw-item tw-row tw-between${item.lesson_id === selectedId ? " is-selected" : ""}`} style={{ width: "100%", textAlign: "left" }} onClick={() => setSelectedId(item.lesson_id)} aria-pressed={selectedId === item.lesson_id}>
            <span style={{ minWidth: 0 }}><strong style={{ display: "block" }}>{item.title}</strong><span className="tw-meta">{item.topic} · bản {item.current_version_no} · {item.review_state}</span></span><span className="tw-chip is-gray">{item.visibility}</span>
          </button>)}</div>
          <BackendNotice title="Trạng thái quyền công khai" tone="info">Gửi grant PUBLIC sẽ tạo PENDING_REVIEW. Chỉ Manager mới duyệt được; thao tác này không tự phát hành bài học.</BackendNotice>
        </section>

        <form className="tw-card" onSubmit={(event) => void save(event)}>
          <div className="tw-row tw-between tw-wrap"><h2 className="tw-h2" style={{ margin: 0 }}>{detail ? "Cập nhật giáo án" : "Tạo giáo án"}</h2>{detail && <span className="tw-chip is-gray">Revision {detail.revision} · {detail.current_version.review_state}</span>}</div>
          {detailError && <BackendNotice title="Không thể lưu hoặc tải phiên bản" tone="error">{detailError}</BackendNotice>}
          {selectedId && !detail && !detailError && <p className="tw-sub">Đang tải nội dung có revision hiện tại…</p>}

          <div style={{ display: "grid", gap: 12, marginTop: 14 }}>
            <label className="tw-label" style={fieldStyle}>Tiêu đề
              <input className="tw-input" style={inputStyle} maxLength={160} required value={content.title} onChange={(event) => updateContent({ title: event.target.value })} />
            </label>
            <label className="tw-label" style={fieldStyle}>Chủ đề
              <input className="tw-input" style={inputStyle} maxLength={120} required value={content.topic} onChange={(event) => updateContent({ topic: event.target.value })} />
            </label>
            <div className="tw-grid-2">
              <label className="tw-label" style={fieldStyle}>target_age_band_ref
                <input className="tw-input" style={inputStyle} maxLength={256} required value={content.target_age_band_ref} onChange={(event) => updateContent({ target_age_band_ref: event.target.value })} />
              </label>
              <label className="tw-label" style={fieldStyle}>Phiên bản nhóm tuổi
                <input className="tw-input" style={inputStyle} type="number" min={1} step={1} required value={content.target_age_band_version} onChange={(event) => updateContent({ target_age_band_version: Number(event.target.value) })} />
              </label>
            </div>
            <label className="tw-label" style={fieldStyle}>Mục tiêu học tập (mỗi dòng một mục)
              <textarea className="tw-input" style={inputStyle} rows={3} maxLength={12000} value={content.objectives.join("\n")} onChange={(event) => updateContent({ objectives: event.target.value.split("\n") })} />
            </label>
            <label className="tw-label" style={fieldStyle}>Đối tượng cần vẽ
              <input className="tw-input" style={inputStyle} maxLength={160} required value={content.drawing_subject} onChange={(event) => updateContent({ drawing_subject: event.target.value })} />
            </label>
            <label className="tw-label" style={fieldStyle}>Các bước hướng dẫn vẽ
              <textarea className="tw-input" style={inputStyle} rows={4} maxLength={4000} required value={content.drawing_steps_text} onChange={(event) => updateContent({ drawing_steps_text: event.target.value })} />
            </label>
            <label className="tw-label" style={fieldStyle}>Ghi chú kiến thức
              <textarea className="tw-input" style={inputStyle} rows={3} maxLength={5000} required value={content.subject_learning_notes} onChange={(event) => updateContent({ subject_learning_notes: event.target.value })} />
            </label>
            <label className="tw-label" style={fieldStyle}>Định hướng kịch bản (tùy chọn)
              <textarea className="tw-input" style={inputStyle} rows={2} maxLength={2000} value={content.script_direction ?? ""} onChange={(event) => updateContent({ script_direction: event.target.value || null })} />
            </label>
            <label className="tw-row" style={{ gap: 8, fontWeight: 650 }}><input type="checkbox" checked={content.script_following_allowed} onChange={(event) => updateContent({ script_following_allowed: event.target.checked })} /> Cho phép bám theo định hướng kịch bản</label>
          </div>

          <div className="tw-card" style={{ marginTop: 18, padding: 16, background: "#F6F7F9" }}>
            <div className="tw-row tw-between"><h3 className="tw-h2" style={{ fontSize: 17 }}>Hoạt động thực hành</h3><button type="button" className="tw-btn is-ghost is-sm" disabled={content.activities.length >= 24} onClick={() => updateContent({ activities: [...content.activities, blankActivity()] })}><Icon name="plus" size={15} /> Thêm hoạt động</button></div>
            {content.activities.map((activity, index) => <fieldset key={index} style={{ border: "1px solid #B9C0CC", borderRadius: 14, padding: 14, margin: "12px 0" }}>
              <legend style={{ padding: "0 6px", fontWeight: 750 }}>Hoạt động {index + 1}</legend>
              <div style={{ display: "grid", gap: 10 }}>
                <label className="tw-label" style={fieldStyle}>Tên hoạt động<input className="tw-input" style={inputStyle} maxLength={160} required value={activity.title} onChange={(event) => updateActivity(index, { title: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>Mục tiêu<input className="tw-input" style={inputStyle} maxLength={1000} required value={activity.objective} onChange={(event) => updateActivity(index, { objective: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>Hướng dẫn<textarea className="tw-input" style={inputStyle} rows={3} maxLength={5000} required value={activity.instructions_text} onChange={(event) => updateActivity(index, { instructions_text: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>Vật liệu<textarea className="tw-input" style={inputStyle} rows={2} maxLength={2000} value={activity.materials_text} onChange={(event) => updateActivity(index, { materials_text: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>Chuẩn bị<textarea className="tw-input" style={inputStyle} rows={2} maxLength={2000} value={activity.preparation_text} onChange={(event) => updateActivity(index, { preparation_text: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>Lưu ý quan sát<textarea className="tw-input" style={inputStyle} rows={2} maxLength={3000} value={activity.observation_notes} onChange={(event) => updateActivity(index, { observation_notes: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>An toàn<textarea className="tw-input" style={inputStyle} rows={2} maxLength={3000} value={activity.safety_notes} onChange={(event) => updateActivity(index, { safety_notes: event.target.value })} /></label>
                <label className="tw-label" style={fieldStyle}>Loại hoạt động<select className="tw-input" style={inputStyle} value={activity.activity_kind} onChange={(event) => updateActivity(index, { activity_kind: event.target.value as LessonActivity["activity_kind"] })}><option value="outdoor">Ngoài trời</option><option value="indoor">Trong lớp</option><option value="mixed">Kết hợp</option></select></label>
                {content.activities.length > 1 && <button type="button" className="tw-btn is-ghost is-sm" onClick={() => updateContent({ activities: content.activities.filter((_, i) => i !== index) })}>Xóa hoạt động này</button>}
              </div>
            </fieldset>)}
          </div>

          <div className="tw-row tw-wrap" style={{ justifyContent: "flex-end", marginTop: 16 }}>
            {detail && <button type="button" className="tw-btn is-ghost" disabled={saving} onClick={() => void archive()}>Lưu trữ</button>}
            {detail && detail.current_version.review_state !== "PENDING_REVIEW" && detail.visibility !== "PUBLIC" && <button type="button" className="tw-btn is-ghost" disabled={saving} onClick={() => void requestPublic()}><Icon name="share" size={16} /> Gửi duyệt công khai</button>}
            <button type="submit" className="tw-btn" disabled={saving || Boolean(selectedId && !detail)}><Icon name="check" size={16} />{saving ? "Đang lưu…" : detail ? "Lưu cập nhật" : "Tạo giáo án"}</button>
          </div>
        </form>
      </div>
      <BackendNotice title="API không tự phát hành bài học" tone="info">Giáo án mới được tạo với visibility PRIVATE. Chỉ khi gửi grant PUBLIC, lesson sẽ vào trạng thái PENDING_REVIEW để School Manager quyết định.</BackendNotice>
    </div>
  );
}
