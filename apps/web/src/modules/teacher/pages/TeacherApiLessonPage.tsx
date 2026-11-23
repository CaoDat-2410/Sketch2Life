import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  createIdempotencyKey,
  hasFirebaseAuthBridge,
  type LessonActivity,
  type LessonContent,
  type LessonSummary,
  type TeacherLessonDetail,
} from "../../../shared/api/backendApi";
import { usePortalSession } from "../../../shared/auth/PortalSessionContext";
import { Icon } from "../components/Icon";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Button, FormField, Select } from "../../../shared/ui";
import { commandSignature, isStaleRevision, keyForCommand } from "../services/commandKeys";

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
  target_age_band_ref: "",
  target_age_band_version: 0,
  objectives: [""],
  drawing_subject: "",
  drawing_steps_text: "",
  subject_learning_notes: "",
  script_direction: null,
  script_following_allowed: false,
  activities: [blankActivity()],
});

export function TeacherApiLessonPage() {
  const navigate = useNavigate();
  const { showToast } = usePortalSession();
  const [items, setItems] = useState<LessonSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TeacherLessonDetail | null>(null);
  const [content, setContent] = useState<LessonContent>(blankContent);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [moreError, setMoreError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  // FEAT-066 C4: set after a 409 STALE_REVISION; the Teacher chooses when to load the current version.
  const [staleRevision, setStaleRevision] = useState(false);
  const [reload, setReload] = useState(0);
  const mutationKeys = useRef(new Map<string, string>());
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
    setMoreError(null);
    setNextCursor(null);
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản không có assignment teacher trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.lessons(organizationId);
      })
      .then((page) => { if (active) { setItems(page.items); setNextCursor(page.next_cursor); } })
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
    setStaleRevision(false);
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

  const loadMoreLessons = async () => {
    const cursor = nextCursor;
    if (!cursor || !organizationId || loadingMore) return;
    setLoadingMore(true);
    setMoreError(null);
    try {
      const page = await backendApi.lessons(organizationId, { cursor });
      setItems((current) => {
        const byId = new Map<string, LessonSummary>(current.map((item) => [item.lesson_id, item] as const));
        page.items.forEach((item) => byId.set(item.lesson_id, item));
        return Array.from(byId.values());
      });
      setNextCursor(page.next_cursor);
    } catch (cause) {
      setMoreError(backendMessage(cause));
    } finally {
      setLoadingMore(false);
    }
  };

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
    const createSignature = JSON.stringify(["create-lesson", organizationId, payload]);
    let createKey = mutationKeys.current.get(createSignature);
    if (!detail && !createKey) {
      createKey = createIdempotencyKey();
      mutationKeys.current.set(createSignature, createKey);
    }
    // FEAT-066 C4: the update key belongs to this lesson, revision and payload (retry reuses it).
    const updateSignature = detail
      ? commandSignature("update-lesson", organizationId, detail.lesson_id, detail.revision, payload)
      : null;
    try {
      const result = detail && updateSignature
        ? await backendApi.updateLesson(organizationId, detail, payload, keyForCommand(mutationKeys.current, updateSignature))
        : await backendApi.createLesson(organizationId, payload, createKey);
      setSelectedId(result.lesson_id);
      setDetail(result);
      if (result.current_version.content) setContent(result.current_version.content);
      setItems((current) => [
        { contract: "LessonSummaryV1", lesson_id: result.lesson_id, title: payload.title, topic: payload.topic, current_version_no: result.current_version.version_no, review_state: result.current_version.review_state, visibility: result.visibility, activity_count: payload.activities.length, updated_at: result.updated_at },
        ...current.filter((item) => item.lesson_id !== result.lesson_id),
      ]);
      if (!detail) mutationKeys.current.delete(createSignature);
      if (updateSignature) mutationKeys.current.delete(updateSignature);
      showToast(detail ? "Đã cập nhật giáo án qua API." : "Đã tạo giáo án riêng tư qua API.", "ok");
    } catch (cause) {
      setDetailError(backendMessage(cause));
      setStaleRevision(isStaleRevision(cause));
    } finally {
      setSaving(false);
    }
  };

  const requestPublic = async () => {
    if (!detail) return;
    setSaving(true);
    setDetailError(null);
    const requestSignature = JSON.stringify(["request-public-review", organizationId, detail.lesson_id, detail.current_version.version_id]);
    let requestKey = mutationKeys.current.get(requestSignature);
    if (!requestKey) {
      requestKey = createIdempotencyKey();
      mutationKeys.current.set(requestSignature, requestKey);
    }
    try {
      await backendApi.requestPublicReview(organizationId, detail, requestKey);
      mutationKeys.current.delete(requestSignature);
      const updated = await backendApi.teacherLesson(organizationId, detail.lesson_id);
      setDetail(updated);
      if (updated.current_version.content) setContent(updated.current_version.content);
      showToast("Đã gửi grant PUBLIC để School Manager duyệt.", "ok");
      setReload((value) => value + 1);
    } catch (cause) {
      setDetailError(backendMessage(cause));
      setStaleRevision(isStaleRevision(cause));
    } finally {
      setSaving(false);
    }
  };

  const archive = async () => {
    if (!detail || !window.confirm(`Lưu trữ “${detail.current_version.content?.title ?? detail.lesson_id}”?`)) return;
    setSaving(true);
    setDetailError(null);
    const archiveSignature = commandSignature("archive-lesson", organizationId, detail.lesson_id, detail.revision);
    try {
      await backendApi.archiveLesson(organizationId, detail, keyForCommand(mutationKeys.current, archiveSignature));
      mutationKeys.current.delete(archiveSignature);
      showToast("Đã lưu trữ giáo án.", "ok");
      setItems((current) => current.filter((item) => item.lesson_id !== detail.lesson_id));
      newLesson();
      setReload((value) => value + 1);
    } catch (cause) {
      setDetailError(backendMessage(cause));
      setStaleRevision(isStaleRevision(cause));
    } finally {
      setSaving(false);
    }
  };

  // FEAT-066 C4 (review C4-IMPL-R1-01): load the current version on request only. The form text is
  // replaced only by this click, so a stale save never overwrites another change (SRS 21.4).
  const reloadCurrentVersion = async () => {
    if (!detail) return;
    setSaving(true);
    try {
      const current = await backendApi.teacherLesson(organizationId, detail.lesson_id);
      setDetail(current);
      if (current.current_version.content) setContent(current.current_version.content);
      setDetailError(null);
      setStaleRevision(false);
    } catch (cause) {
      setDetailError(backendMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="tw-page">
      <PageHeading eyebrow="Teacher · Học liệu" title="Giáo án" description="Giáo án, mục tiêu học tập và hoạt động trong phạm vi tổ chức." action={<div className="teacher-page-actions"><button type="button" className="tw-btn is-ghost" onClick={() => navigate("/teacher/t03-document-import-review")}><Icon name="upload" size={16} /> Nhập tài liệu</button><button type="button" className="tw-btn" onClick={newLesson}><Icon name="plus" size={16} /> Giáo án mới</button></div>} />
      <BackendModeNotice roleLabel="Giáo viên" />
      {pageError && <BackendNotice title="Không tải được danh sách giáo án" tone="error">{pageError}</BackendNotice>}
      <div className="teacher-lesson-layout">
        <section className="tw-card">
          <div className="tw-row tw-between"><h2 className="tw-h2">Giáo án</h2><button type="button" className="tw-btn is-ghost is-sm" disabled={loading} onClick={() => setReload((value) => value + 1)}>Tải lại</button></div>
          {loading && <p className="tw-sub">Đang tải danh sách…</p>}
          {!loading && items.length === 0 && <p className="tw-sub">Chưa có giáo án trong phạm vi tài khoản.</p>}
          <div style={{ display: "grid", gap: 8 }}>{items.map((item) => <button key={item.lesson_id} type="button" className={`tw-item tw-row tw-between${item.lesson_id === selectedId ? " is-selected" : ""}`} style={{ width: "100%", textAlign: "left" }} onClick={() => setSelectedId(item.lesson_id)} aria-pressed={selectedId === item.lesson_id}>
            <span style={{ minWidth: 0 }}><strong style={{ display: "block" }}>{item.title}</strong><span className="tw-meta">{item.topic} · bản {item.current_version_no} · {item.review_state}</span></span><span className="tw-chip is-gray">{item.visibility}</span>
          </button>)}</div>
          {moreError && <BackendNotice title="Không tải được giáo án tiếp theo" tone="error">{moreError}</BackendNotice>}
          {nextCursor && <button type="button" className="tw-btn is-ghost is-sm" style={{ width: "100%", marginTop: 10 }} disabled={loadingMore} onClick={() => void loadMoreLessons()}>{loadingMore ? "Đang tải…" : "Tải thêm giáo án"}</button>}
          <BackendNotice title="Trạng thái quyền công khai" tone="info">Gửi grant PUBLIC sẽ tạo PENDING_REVIEW. Chỉ Manager mới duyệt được; thao tác này không tự phát hành bài học.</BackendNotice>
        </section>

        <form className="tw-card cozy-form-card cozy-form-card--wide cozy-form-stack teacher-lesson-form" onSubmit={(event) => void save(event)}>
          <div className="tw-row tw-between tw-wrap"><h2 className="tw-h2" style={{ margin: 0 }}>{detail ? "Cập nhật giáo án" : "Tạo giáo án"}</h2>{detail && <span className="tw-chip is-gray">Revision {detail.revision} · {detail.current_version.review_state}</span>}</div>
          {selectedId && !detail && !detailError && <p className="tw-sub">Đang tải nội dung có revision hiện tại…</p>}

          <div className="cozy-form-grid">
            <FormField className="cozy-span-3" label="Tiêu đề" htmlFor="lesson-title" required>
              <input id="lesson-title" className="cozy-input" maxLength={160} required value={content.title} onChange={(event) => updateContent({ title: event.target.value })} />
            </FormField>
            <FormField className="cozy-span-3" label="Chủ đề" htmlFor="lesson-topic" required>
              <input id="lesson-topic" className="cozy-input" maxLength={120} required value={content.topic} onChange={(event) => updateContent({ topic: event.target.value })} />
            </FormField>
            <FormField className="cozy-span-2" label="Mã nhóm tuổi theo hợp đồng" htmlFor="lesson-age-band" required>
              <input id="lesson-age-band" className="cozy-input" maxLength={256} required value={content.target_age_band_ref} onChange={(event) => updateContent({ target_age_band_ref: event.target.value })} />
            </FormField>
            <FormField className="cozy-span-2" label="Phiên bản nhóm tuổi" htmlFor="lesson-age-version" required>
              <input id="lesson-age-version" className="cozy-input" type="number" min={1} step={1} required value={content.target_age_band_version || ""} onChange={(event) => updateContent({ target_age_band_version: event.target.value ? Number(event.target.value) : 0 })} />
            </FormField>
            <FormField className="cozy-span-2" label="Đối tượng cần vẽ" htmlFor="lesson-drawing-subject" required>
              <input id="lesson-drawing-subject" className="cozy-input" maxLength={160} required value={content.drawing_subject} onChange={(event) => updateContent({ drawing_subject: event.target.value })} />
            </FormField>
            <FormField className="cozy-span-3" label="Mục tiêu học tập (mỗi dòng một mục)" htmlFor="lesson-objectives" required help="Tối đa 12 mục tiêu, mỗi mục tiêu tối đa 1.000 ký tự.">
              <textarea id="lesson-objectives" className="cozy-textarea" rows={3} maxLength={12000} value={content.objectives.join("\n")} onChange={(event) => updateContent({ objectives: event.target.value.split("\n") })} />
            </FormField>
            <FormField className="cozy-span-3" label="Các bước hướng dẫn vẽ" htmlFor="lesson-drawing-steps" required>
              <textarea id="lesson-drawing-steps" className="cozy-textarea" rows={3} maxLength={4000} required value={content.drawing_steps_text} onChange={(event) => updateContent({ drawing_steps_text: event.target.value })} />
            </FormField>
            <FormField className="cozy-span-3" label="Ghi chú kiến thức" htmlFor="lesson-learning-notes" required>
              <textarea id="lesson-learning-notes" className="cozy-textarea" rows={2} maxLength={5000} required value={content.subject_learning_notes} onChange={(event) => updateContent({ subject_learning_notes: event.target.value })} />
            </FormField>
            <FormField className="cozy-span-3" label="Định hướng kịch bản (tùy chọn)" htmlFor="lesson-script-direction">
              <textarea id="lesson-script-direction" className="cozy-textarea" rows={2} maxLength={2000} value={content.script_direction ?? ""} onChange={(event) => updateContent({ script_direction: event.target.value || null })} />
            </FormField>
            <label className="cozy-form-checkbox-card"><input type="checkbox" checked={content.script_following_allowed} onChange={(event) => updateContent({ script_following_allowed: event.target.checked })} /><span>Cho phép bám theo định hướng kịch bản</span></label>
          </div>

          <div className="teacher-lesson-activities">
            <div className="tw-row tw-between">
              <h3 className="tw-h2" style={{ fontSize: 17 }}>Hoạt động thực hành</h3>
              <Button type="button" variant="secondary" size="sm" disabled={content.activities.length >= 24} iconLeft={<Icon name="plus" size={15} />} onClick={() => updateContent({ activities: [...content.activities, blankActivity()] })}>
                Thêm hoạt động
              </Button>
            </div>
            {content.activities.map((activity, index) => (
              <section key={index} className="cozy-form-section cozy-form-grid">
                <div className="cozy-form-section-head">
                  <h4>Hoạt động {index + 1}</h4>
                  {content.activities.length > 1 && (
                    <Button type="button" variant="secondary" size="sm" onClick={() => updateContent({ activities: content.activities.filter((_, i) => i !== index) })}>
                      Xóa hoạt động này
                    </Button>
                  )}
                </div>
                <FormField className="cozy-span-4" label="Tên hoạt động" htmlFor={`lesson-activity-title-${index}`} required>
                  <input id={`lesson-activity-title-${index}`} className="cozy-input" maxLength={160} required value={activity.title} onChange={(event) => updateActivity(index, { title: event.target.value })} />
                </FormField>
                <FormField className="cozy-span-2" label="Loại hoạt động" htmlFor={`lesson-activity-kind-${index}`} required>
                  <Select id={`lesson-activity-kind-${index}`} aria-label="Loại hoạt động" value={activity.activity_kind} onChange={(event) => updateActivity(index, { activity_kind: event.target.value as LessonActivity["activity_kind"] })}>
                    <option value="outdoor">Ngoài trời</option><option value="indoor">Trong lớp</option><option value="mixed">Kết hợp</option>
                  </Select>
                </FormField>
                <FormField className="cozy-span-3" label="Mục tiêu" htmlFor={`lesson-activity-objective-${index}`} required>
                  <textarea id={`lesson-activity-objective-${index}`} className="cozy-textarea" rows={2} maxLength={1000} required value={activity.objective} onChange={(event) => updateActivity(index, { objective: event.target.value })} />
                </FormField>
                <FormField className="cozy-span-3" label="Hướng dẫn" htmlFor={`lesson-activity-instructions-${index}`} required>
                  <textarea id={`lesson-activity-instructions-${index}`} className="cozy-textarea" rows={2} maxLength={5000} required value={activity.instructions_text} onChange={(event) => updateActivity(index, { instructions_text: event.target.value })} />
                </FormField>
                <FormField className="cozy-span-3" label="Vật liệu" htmlFor={`lesson-activity-materials-${index}`}>
                  <textarea id={`lesson-activity-materials-${index}`} className="cozy-textarea" rows={2} maxLength={2000} value={activity.materials_text} onChange={(event) => updateActivity(index, { materials_text: event.target.value })} />
                </FormField>
                <FormField className="cozy-span-3" label="Chuẩn bị" htmlFor={`lesson-activity-prep-${index}`}>
                  <textarea id={`lesson-activity-prep-${index}`} className="cozy-textarea" rows={2} maxLength={2000} value={activity.preparation_text} onChange={(event) => updateActivity(index, { preparation_text: event.target.value })} />
                </FormField>
                <FormField className="cozy-span-3" label="Lưu ý quan sát" htmlFor={`lesson-activity-observation-${index}`}>
                  <textarea id={`lesson-activity-observation-${index}`} className="cozy-textarea" rows={2} maxLength={3000} value={activity.observation_notes} onChange={(event) => updateActivity(index, { observation_notes: event.target.value })} />
                </FormField>
                <FormField className="cozy-span-3" label="An toàn" htmlFor={`lesson-activity-safety-${index}`}>
                  <textarea id={`lesson-activity-safety-${index}`} className="cozy-textarea" rows={2} maxLength={3000} value={activity.safety_notes} onChange={(event) => updateActivity(index, { safety_notes: event.target.value })} />
                </FormField>
              </section>
            ))}
          </div>

          {detailError && <BackendNotice title="Không thể lưu hoặc tải phiên bản" tone="error">{detailError}{staleRevision && detail && <> <Button type="button" variant="secondary" size="sm" disabled={saving} onClick={() => void reloadCurrentVersion()}>Tải lại bản hiện tại (bỏ chỉnh sửa chưa lưu)</Button></>}</BackendNotice>}
          {!saving && selectedId && !detail && (
            <p className="cozy-form-disabled-hint">Đang tải dữ liệu giáo án để bật nút lưu.</p>
          )}

          <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            {detail && <Button type="button" variant="danger" className="cozy-form-action-danger" disabled={saving} onClick={() => void archive()}>Lưu trữ</Button>}
            {detail && detail.current_version.review_state !== "PENDING_REVIEW" && detail.visibility !== "PUBLIC" && <Button type="button" variant="secondary" disabled={saving} iconLeft={<Icon name="share" size={16} />} onClick={() => void requestPublic()}>Gửi duyệt công khai</Button>}
            <Button type="submit" variant="primary" loading={saving} disabled={saving || Boolean(selectedId && !detail)} iconLeft={<Icon name="check" size={16} />}>
              {saving ? "Đang lưu…" : detail ? "Lưu cập nhật" : "Tạo giáo án"}
            </Button>
          </div>
        </form>
      </div>
      <BackendNotice title="API không tự phát hành bài học" tone="info">Giáo án mới được tạo với visibility PRIVATE. Chỉ khi gửi grant PUBLIC, lesson sẽ vào trạng thái PENDING_REVIEW để School Manager quyết định.</BackendNotice>
    </div>
  );
}
