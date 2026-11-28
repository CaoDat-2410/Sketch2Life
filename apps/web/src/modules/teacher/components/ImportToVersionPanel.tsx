import { useEffect, useMemo, useRef, useState } from "react";
import {
  BackendApiError,
  BackendNotice,
  backendApi,
  createIdempotencyKey,
  type LessonContent,
  type LessonDocumentRevisionPreview,
  type LessonSourceDocumentStatus,
  type LessonVersion,
  type TeacherLessonDetail,
} from "../../../shared/api/backendApi";
import { Button, FormField, StatusBadge } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";
import { teacherAgeBandLabel } from "../services/ageBands";

type EditableField = "title" | "topic" | "objectives" | "drawing_subject" | "drawing_steps_text" | "subject_learning_notes" | "script_direction";

interface ImportToVersionPanelProps {
  organizationId: string;
  lessonId: string;
  sourceDocument: LessonSourceDocumentStatus;
  revision: LessonDocumentRevisionPreview;
  onRevisionConfirmed?: () => void;
  onVersionCreated?: () => void;
}

const FIELD_LABELS: Record<EditableField, string> = {
  title: "Tên giáo án",
  topic: "Chủ đề",
  objectives: "Mục tiêu",
  drawing_subject: "Đối tượng vẽ",
  drawing_steps_text: "Các bước vẽ",
  subject_learning_notes: "Ghi chú kiến thức",
  script_direction: "Định hướng lời dẫn",
};

function mergeExtractedFields(content: LessonContent, fields: Record<string, unknown>): LessonContent {
  const merged = { ...content };
  const textFields = ["title", "topic", "drawing_subject", "drawing_steps_text", "subject_learning_notes"] as const;
  for (const field of textFields) {
    if (typeof fields[field] === "string") merged[field] = fields[field] as never;
  }
  if (Array.isArray(fields.objectives)) {
    merged.objectives = fields.objectives.filter((item): item is string => typeof item === "string");
  }
  if (fields.script_direction === null || typeof fields.script_direction === "string") {
    merged.script_direction = fields.script_direction;
  }
  return merged;
}

function rebaseEditableFields(draft: LessonContent, freshContent: LessonContent): LessonContent {
  return {
    ...freshContent,
    title: draft.title,
    topic: draft.topic,
    objectives: draft.objectives,
    drawing_subject: draft.drawing_subject,
    drawing_steps_text: draft.drawing_steps_text,
    subject_learning_notes: draft.subject_learning_notes,
    script_direction: draft.script_direction,
  };
}

function validateContent(content: LessonContent): Record<string, string> {
  const errors: Record<string, string> = {};
  const checkText = (field: string, value: string, min: number, max: number) => {
    if (value.trim().length < min) errors[field] = "Cần nhập nội dung.";
    else if (value.length > max) errors[field] = `Tối đa ${max} ký tự.`;
  };
  checkText("title", content.title, 1, 160);
  checkText("topic", content.topic, 1, 120);
  checkText("drawing_subject", content.drawing_subject, 1, 160);
  checkText("drawing_steps_text", content.drawing_steps_text, 1, 4000);
  checkText("subject_learning_notes", content.subject_learning_notes, 1, 5000);
  if (!content.target_age_band_ref.trim() || !/^[A-Za-z0-9._:-]{1,256}$/.test(content.target_age_band_ref)) {
    errors.age_band = "Nhóm tuổi hiện tại chưa hợp lệ.";
  }
  if (!Number.isInteger(content.target_age_band_version) || content.target_age_band_version < 1) {
    errors.age_band = "Phiên bản nhóm tuổi hiện tại chưa hợp lệ.";
  }
  if (content.objectives.length < 1 || content.objectives.length > 12) {
    errors.objectives = "Cần từ 1 đến 12 mục tiêu.";
  } else if (content.objectives.some((item) => !item.trim() || item.length > 1000)) {
    errors.objectives = "Mỗi mục tiêu cần có nội dung, tối đa 1.000 ký tự.";
  }
  if (content.script_direction !== null && (!content.script_direction.trim() || content.script_direction.length > 2000)) {
    errors.script_direction = "Để trống hoặc nhập tối đa 2.000 ký tự.";
  }
  if (content.activities.length < 1 || content.activities.length > 24) {
    errors.activities = "Cần có từ 1 đến 24 hoạt động trong giáo án hiện tại.";
  } else {
    content.activities.forEach((activity, index) => {
      if (!activity.title.trim() || activity.title.length > 160 || !activity.objective.trim() || activity.objective.length > 1000 ||
        !activity.instructions_text.trim() || activity.instructions_text.length > 5000 || activity.materials_text.length > 2000 ||
        activity.preparation_text.length > 2000 || activity.observation_notes.length > 3000 || activity.safety_notes.length > 3000) {
        errors.activities = `Hoạt động ${index + 1} hiện chưa đáp ứng giới hạn nội dung.`;
      }
    });
  }
  return errors;
}

function fieldKeyForPath(path: string): string {
  const normalized = path.replace(/^body\./, "").replace(/^content\./, "");
  const candidates = ["title", "topic", "objectives", "drawing_subject", "drawing_steps_text", "subject_learning_notes", "script_direction", "target_age_band_ref", "target_age_band_version", "activities"];
  const matched = candidates.find((field) => normalized === field || normalized.startsWith(`${field}.`) || normalized.startsWith(`${field}[`));
  if (matched === "target_age_band_ref" || matched === "target_age_band_version") return "age_band";
  return matched ?? "general";
}

function errorCopy(cause: unknown): string {
  if (!(cause instanceof BackendApiError)) return "Chưa thể hoàn tất thao tác. Vui lòng thử lại.";
  if (cause.status === 404) return "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách.";
  if (cause.status === 503) return "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.";
  if (cause.status === 401) return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
  if (cause.status === 403) return "Tài khoản chưa được cấp quyền cho thao tác này.";
  if (cause.status === 0 || cause.status === 408) return "Chưa kết nối được dịch vụ. Có thể thử lại cùng nội dung.";
  return "Chưa thể hoàn tất thao tác. Vui lòng kiểm tra nội dung rồi thử lại.";
}

function validateAgainstContent(content: LessonContent): LessonContent {
  return {
    ...content,
    title: content.title.trim(),
    topic: content.topic.trim(),
    drawing_subject: content.drawing_subject.trim(),
    objectives: content.objectives.map((item) => item.trim()),
    script_direction: content.script_direction?.trim() ? content.script_direction.trim() : null,
  };
}

export function ImportToVersionPanel({
  organizationId,
  lessonId,
  sourceDocument,
  revision,
  onRevisionConfirmed,
  onVersionCreated,
}: ImportToVersionPanelProps) {
  const canPromote = sourceDocument.state === "READY_FOR_REVIEW" && revision.review_state !== "CONFIRMED";
  const extractedFields = revision.extracted_fields;
  const loadKey = `${organizationId}/${lessonId}/${sourceDocument.source_document_id}/${revision.revision_id}`;
  const [lesson, setLesson] = useState<TeacherLessonDetail | null>(null);
  const [draft, setDraft] = useState<LessonContent | null>(null);
  const [lessonLoadedKey, setLessonLoadedKey] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<{ key: string; message: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [createdVersion, setCreatedVersion] = useState<LessonVersion | null>(null);
  const [sendingForReview, setSendingForReview] = useState(false);
  const [reviewRequested, setReviewRequested] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const attemptRef = useRef<{ signature: string; key: string } | null>(null);
  const reviewKeyRef = useRef<string | null>(null);
  const loading = canPromote && lessonLoadedKey !== loadKey && loadError?.key !== loadKey;
  const lessonReady = canPromote && lessonLoadedKey === loadKey && Boolean(lesson && draft);

  useEffect(() => {
    if (!canPromote) return;
    let active = true;
    backendApi.teacherLesson(organizationId, lessonId)
      .then((detail) => {
        if (!active) return;
        const currentContent = detail.current_version.content;
        if (!currentContent) {
          setLoadError({ key: loadKey, message: "Giáo án hiện tại chưa có nội dung để làm nền cho phiên bản mới." });
          return;
        }
        setLesson(detail);
        setDraft(mergeExtractedFields(currentContent, extractedFields));
        setLessonLoadedKey(loadKey);
        setLoadError(null);
      })
      .catch((cause: unknown) => {
        if (active) setLoadError({ key: loadKey, message: errorCopy(cause) });
      });
    return () => { active = false; };
  }, [organizationId, lessonId, sourceDocument.source_document_id, revision.revision_id, extractedFields, canPromote, loadKey]);

  const localErrors = useMemo(() => draft ? validateContent(draft) : {}, [draft]);
  const errors = { ...localErrors, ...fieldErrors };
  const updateDraft = (change: Partial<LessonContent>) => {
    setDraft((current) => current ? { ...current, ...change } : current);
    attemptRef.current = null;
    setConfirmChecked(false);
    setFieldErrors({});
    setError("");
  };

  const updateEditableField = (field: EditableField, value: string) => {
    if (!draft) return;
    if (field === "objectives") return;
    if (field === "script_direction") updateDraft({ script_direction: value ? value : null });
    else updateDraft({ [field]: value } as Pick<LessonContent, typeof field>);
  };

  const createVersion = async () => {
    if (!lesson || !draft || !confirmChecked || !lessonReady || Object.keys(errors).length > 0 || saving) return;
    const content = validateAgainstContent(draft);
    const signature = JSON.stringify({ revision: lesson.revision, sourceRevisionId: revision.revision_id, content });
    if (!attemptRef.current || attemptRef.current.signature !== signature) {
      attemptRef.current = { signature, key: createIdempotencyKey() };
    }
    setSaving(true);
    setError("");
    setFieldErrors({});
    try {
      const version = await backendApi.createLessonVersion(
        organizationId,
        lesson,
        revision.revision_id,
        content,
        attemptRef.current.key,
      );
      setCreatedVersion(version);
      setError("");
      setConfirmChecked(false);
      onRevisionConfirmed?.();
      onVersionCreated?.();
    } catch (cause) {
      if (cause instanceof BackendApiError && cause.status === 409 && cause.code === "STALE_REVISION") {
        attemptRef.current = null;
        try {
          const fresh = await backendApi.teacherLesson(organizationId, lessonId);
          setLesson(fresh);
          const freshContent = fresh.current_version.content;
          setConfirmChecked(false);
          if (!freshContent) {
            setDraft(null);
            setError("Giáo án hiện tại chưa có nội dung để làm nền cho phiên bản mới.");
            return;
          }
          setDraft((current) => current ? rebaseEditableFields(current, freshContent) : current);
          setError("Giáo án đã thay đổi. Bản chỉnh sửa của bạn vẫn được giữ; hãy rà soát và xác nhận lại.");
        } catch (reloadCause) {
          setError(errorCopy(reloadCause));
        }
      } else if (cause instanceof BackendApiError && cause.status === 422 && cause.fieldErrors.length > 0) {
        const mapped: Record<string, string> = {};
        cause.fieldErrors.forEach((item) => {
          const key = fieldKeyForPath(item.field);
          mapped[key] = key === "general" ? "Một mục trong nội dung chưa đúng định dạng." : "Kiểm tra nội dung và giới hạn của trường này.";
        });
        setFieldErrors(mapped);
        setError("Một số mục cần được chỉnh sửa trước khi tạo phiên bản.");
      } else {
        setError(errorCopy(cause));
      }
    } finally {
      setSaving(false);
    }
  };

  const requestReview = async () => {
    if (!createdVersion || sendingForReview || reviewRequested) return;
    setSendingForReview(true);
    setReviewError("");
    reviewKeyRef.current ??= createIdempotencyKey();
    try {
      const fresh = await backendApi.teacherLesson(organizationId, lessonId);
      if (fresh.current_version.version_id !== createdVersion.version_id) {
        setReviewError("Phiên bản hiện tại đã thay đổi. Hãy mở lại giáo án để gửi đúng phiên bản duyệt.");
        reviewKeyRef.current = null;
        return;
      }
      await backendApi.requestPublicReview(organizationId, fresh, reviewKeyRef.current);
      setReviewRequested(true);
    } catch (cause) {
      setReviewError(errorCopy(cause));
    } finally {
      setSendingForReview(false);
    }
  };

  const setObjective = (index: number, value: string) => {
    if (!draft) return;
    const objectives = [...draft.objectives];
    objectives[index] = value;
    updateDraft({ objectives });
  };

  const badgeStatus = createdVersion
    ? { label: "Đã xác nhận", tone: "success" as const }
    : canPromote
      ? { label: "Cần rà soát", tone: "warn" as const }
      : { label: "Chưa sẵn sàng", tone: "neutral" as const };

  return (
    <section className="tw-card cozy-form-card cozy-form-card--wide cozy-form-stack tp-form-column" aria-labelledby="import-version-heading">
      <div className="tw-row tw-between tw-wrap">
        <h2 className="tw-h2" id="import-version-heading">Rà soát và tạo phiên bản mới</h2>
        <StatusBadge tone={badgeStatus.tone}>{badgeStatus.label}</StatusBadge>
      </div>
      {!canPromote && !createdVersion && <p className="tw-sub">Tài liệu cần sẵn sàng rà soát và bản trích xuất chưa được xác nhận.</p>}
      {loading && <p className="tw-sub" role="status">Đang tải nội dung giáo án hiện tại…</p>}
      {error && <BackendNotice title="Chưa thể tạo phiên bản" tone="error">{error}</BackendNotice>}
      {loadError?.key === loadKey && <BackendNotice title="Chưa thể tải giáo án hiện tại" tone="error">{loadError.message}</BackendNotice>}
      {createdVersion && <>
        <BackendNotice title={`Đã tạo phiên bản ${createdVersion.version_no} · Bản nháp`} tone="success">
          Nội dung đã được xác nhận và tạo thành bản nháp. Phiên bản này chưa được duyệt công khai.
        </BackendNotice>
        {reviewRequested ? (
          <BackendNotice title="Đã gửi yêu cầu duyệt công khai" tone="info">Quản lý trường sẽ xem xét yêu cầu này.</BackendNotice>
        ) : (
          <>
            {reviewError && <p className="cozy-form-error" role="alert">{reviewError}</p>}
            <FormActionBar>
              <Button type="button" variant="secondary" loading={sendingForReview} disabled={sendingForReview} onClick={() => void requestReview()}>
                Gửi duyệt công khai
              </Button>
            </FormActionBar>
          </>
        )}
      </>}
      {draft && !createdVersion && <>
        <BackendNotice title="Nội dung sẽ tạo thành bản nháp" tone="info">
          Hãy kiểm tra và sửa phần trích xuất. Nhóm tuổi, hoạt động và ngôn ngữ giữ nguyên từ giáo án hiện tại.
        </BackendNotice>
        <div className="cozy-form-grid">
          <div className="cozy-span-3">
            <FormField label={FIELD_LABELS.title} required help="Từ 1 đến 160 ký tự." error={errors.title}>
              <input className="cozy-input" maxLength={160} value={draft.title} disabled={!lessonReady || saving} onChange={(event) => updateEditableField("title", event.target.value)} />
            </FormField>
          </div>
          <div className="cozy-span-3">
            <FormField label={FIELD_LABELS.topic} required help="Từ 1 đến 120 ký tự." error={errors.topic}>
              <input className="cozy-input" maxLength={120} value={draft.topic} disabled={!lessonReady || saving} onChange={(event) => updateEditableField("topic", event.target.value)} />
            </FormField>
          </div>
          <div className="cozy-span-6">
            <FormField label={FIELD_LABELS.drawing_subject} required help="Từ 1 đến 160 ký tự." error={errors.drawing_subject}>
              <input className="cozy-input" maxLength={160} value={draft.drawing_subject} disabled={!lessonReady || saving} onChange={(event) => updateEditableField("drawing_subject", event.target.value)} />
            </FormField>
          </div>
          <div className="cozy-span-6">
            <FormField label={FIELD_LABELS.objectives} required help="Từ 1 đến 12 mục tiêu; mỗi mục tối đa 1.000 ký tự." error={errors.objectives}>
              <div className="cozy-form-controls">
                {draft.objectives.map((objective, index) => (
                  <div key={index} className="cozy-form-controls">
                    <textarea className="cozy-textarea" rows={3} maxLength={1000} aria-label={`Mục tiêu ${index + 1}`} value={objective} disabled={!lessonReady || saving} onChange={(event) => setObjective(index, event.target.value)} />
                    {draft.objectives.length > 1 && <Button type="button" size="sm" variant="ghost" disabled={!lessonReady || saving} onClick={() => updateDraft({ objectives: draft.objectives.filter((_, itemIndex) => itemIndex !== index) })}>Bỏ mục tiêu {index + 1}</Button>}
                  </div>
                ))}
                {draft.objectives.length < 12 && <Button type="button" size="sm" variant="secondary" disabled={!lessonReady || saving} onClick={() => updateDraft({ objectives: [...draft.objectives, ""] })}>Thêm mục tiêu</Button>}
              </div>
            </FormField>
          </div>
          <div className="cozy-span-6">
            <FormField label={FIELD_LABELS.drawing_steps_text} required help="Tối đa 4.000 ký tự." error={errors.drawing_steps_text}>
              <textarea className="cozy-textarea" rows={3} maxLength={4000} value={draft.drawing_steps_text} disabled={!lessonReady || saving} onChange={(event) => updateEditableField("drawing_steps_text", event.target.value)} />
            </FormField>
          </div>
          <div className="cozy-span-6">
            <FormField label={FIELD_LABELS.subject_learning_notes} required help="Tối đa 5.000 ký tự." error={errors.subject_learning_notes}>
              <textarea className="cozy-textarea" rows={3} maxLength={5000} value={draft.subject_learning_notes} disabled={!lessonReady || saving} onChange={(event) => updateEditableField("subject_learning_notes", event.target.value)} />
            </FormField>
          </div>
          <div className="cozy-span-6">
            <FormField label={FIELD_LABELS.script_direction} labelAction="(không bắt buộc)" help="Có thể để trống; tối đa 2.000 ký tự." error={errors.script_direction}>
              <textarea className="cozy-textarea" rows={3} maxLength={2000} value={draft.script_direction ?? ""} disabled={!lessonReady || saving} onChange={(event) => updateEditableField("script_direction", event.target.value)} />
            </FormField>
          </div>
        </div>
        <div className="tw-item">
          <h3 className="tw-h2" style={{ fontSize: 16 }}>Thông tin giữ từ giáo án hiện tại</h3>
          <p>Nhóm tuổi: {draft.target_age_band_ref ? teacherAgeBandLabel(draft.target_age_band_ref) : "Chưa có"}</p>
          <p>Ngôn ngữ: Tiếng Việt · Hướng dẫn lời dẫn: {draft.script_following_allowed ? "Cho phép bám theo" : "Không bám theo"}</p>
          <p>Hoạt động được giữ: {draft.activities.length}</p>
          {errors.age_band && <p role="alert" className="cozy-form-error">{errors.age_band}</p>}
          {errors.activities && <p role="alert" className="cozy-form-error">{errors.activities}</p>}
          {fieldErrors.general && <p role="alert" className="cozy-form-error">{fieldErrors.general}</p>}
        </div>
        {Object.keys(localErrors).length > 0 && <p className="tw-meta">Sửa các trường được đánh dấu để tiếp tục.</p>}
        <label className="cozy-form-checkbox-card">
          <input type="checkbox" checked={confirmChecked} disabled={!lessonReady || loading || saving || Object.keys(errors).length > 0} onChange={(event) => setConfirmChecked(event.target.checked)} />
          <span>Tôi đã rà soát nội dung và xác nhận tạo phiên bản giáo án mới dưới dạng bản nháp.</span>
        </label>
        <FormActionBar hint={!confirmChecked && lessonReady && !loading && !saving && Object.keys(errors).length === 0 ? "Đánh dấu xác nhận ở trên để bật nút tạo phiên bản." : undefined}>
          <Button type="button" variant="primary" loading={saving} disabled={!lessonReady || loading || saving || !confirmChecked || Object.keys(errors).length > 0} onClick={() => void createVersion()}>
            Xác nhận tạo phiên bản
          </Button>
        </FormActionBar>
      </>}
      {lesson && !createdVersion && <p className="tw-meta">Phiên bản hiện tại: {lesson.current_version.version_no}. Sau khi tạo, phiên bản mới sẽ cần được duyệt trước khi chia sẻ công khai.</p>}
    </section>
  );
}
