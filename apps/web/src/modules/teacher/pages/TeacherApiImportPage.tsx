import { useCallback, useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  createIdempotencyKey,
  hasFirebaseAuthBridge,
  type LessonDocumentRevisionPreview,
  type LessonSourceDocumentStatus,
  type LessonSummary,
  type LessonUploadSession,
} from "../../../shared/api/backendApi";
import { usePortalSession } from "../../../shared/auth/PortalSessionContext";
import { Icon } from "../components/Icon";
import { FormActionBar } from "../components/FormActionBar";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Button, FormField, Select, StatusBadge } from "../../../shared/ui";
import { teacherStatusMeta } from "../services/teacherStatus";
import { abortUploadWithRevision } from "../services/uploadAbort";
import { ImportToVersionPanel } from "../components/ImportToVersionPanel";
import { LessonVersionsPanel } from "../components/LessonVersionsPanel";

const MIME_BY_EXTENSION: Record<string, string> = {
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
};

async function sha256(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

interface UploadResumeRecord {
  organizationId: string;
  lessonId: string;
  byteLength: number;
  lastModified: number;
  sha256: string;
  uploadSessionId: string | null;
  createKey: string;
  completeKey: string;
  /** FEAT-066 C4: abort key and the session revision it was made for (absent in older records). */
  abortKey?: string;
  abortRevision?: number;
}

const UPLOAD_RESUME_STORAGE_KEY = "s2l.teacher.upload-resume.v1";

function readUploadResume(): UploadResumeRecord | null {
  try {
    const raw = window.sessionStorage.getItem(UPLOAD_RESUME_STORAGE_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as Partial<UploadResumeRecord>;
    if (typeof value.organizationId !== "string" || typeof value.lessonId !== "string" ||
      typeof value.byteLength !== "number" ||
      typeof value.lastModified !== "number" || typeof value.sha256 !== "string" ||
      !(value.uploadSessionId === null || typeof value.uploadSessionId === "string") ||
      typeof value.createKey !== "string" || typeof value.completeKey !== "string") return null;
    return value as UploadResumeRecord;
  } catch {
    return null;
  }
}

export function TeacherApiImportPage() {
  const { showToast } = usePortalSession();
  const organizationId = configuredOrganizationId();
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [lessonNextCursor, setLessonNextCursor] = useState<string | null>(null);
  const [loadingMoreLessons, setLoadingMoreLessons] = useState(false);
  const [lessonListError, setLessonListError] = useState<string | null>(null);
  const [lessonId, setLessonId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [session, setSession] = useState<LessonUploadSession | null>(null);
  const [resume, setResume] = useState<UploadResumeRecord | null>(() => readUploadResume());
  const [sessionLoading, setSessionLoading] = useState(() => Boolean(readUploadResume()?.uploadSessionId));
  const [sourceDocument, setSourceDocument] = useState<LessonSourceDocumentStatus | null>(null);
  const [revision, setRevision] = useState<LessonDocumentRevisionPreview | null>(null);
  const [versionsRefreshToken, setVersionsRefreshToken] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const persistResume = (next: UploadResumeRecord): boolean => {
    try {
      window.sessionStorage.setItem(UPLOAD_RESUME_STORAGE_KEY, JSON.stringify(next));
      setResume(next);
      return true;
    } catch {
      setError("Không thể lưu thông tin phiên tải lên trong trình duyệt; chưa bắt đầu gửi tệp.");
      return false;
    }
  };

  const clearResume = useCallback(() => {
    try { window.sessionStorage.removeItem(UPLOAD_RESUME_STORAGE_KEY); } catch { /* storage may be disabled */ }
    setResume(null);
    setSession(null);
    setSessionLoading(false);
    setProgress(0);
  }, []);

  const recoverCompletedUpload = useCallback(async (record: UploadResumeRecord) => {
    if (!record.uploadSessionId) return;
    const completed = await backendApi.completeUpload(record.uploadSessionId, record.completeKey);
    setSourceDocument(completed);
    setRevision(null);
    if (completed.revision_id) {
      const extractedRevision = await backendApi.documentRevision(record.organizationId, record.lessonId, completed.source_document_id, completed.revision_id);
      setRevision(extractedRevision);
    }
    clearResume();
  }, [clearResume]);

  useEffect(() => {
    let active = true;
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có phiên đăng nhập để tải hoặc nhập tài liệu.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setError("Chưa cấu hình tổ chức cho thư viện giáo án.");
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    setError(null);
    setLessonListError(null);
    setLessonNextCursor(null);
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản chưa được phân công vai trò giáo viên trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.lessons(organizationId, { state: "ACTIVE" });
      })
      .then((page) => { if (active) { const saved = readUploadResume(); setLessons(page.items); setLessonNextCursor(page.next_cursor); setLessonId((current) => current || (saved?.organizationId === organizationId ? saved.lessonId : "") || page.items[0]?.lesson_id || ""); } })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [organizationId]);

  const loadMoreLessons = async () => {
    const cursor = lessonNextCursor;
    if (!cursor || !organizationId || loadingMoreLessons) return;
    setLoadingMoreLessons(true);
    setLessonListError(null);
    try {
      const page = await backendApi.lessons(organizationId, { state: "ACTIVE", cursor });
      setLessons((current) => {
        const byId = new Map<string, LessonSummary>(current.map((item) => [item.lesson_id, item] as const));
        page.items.forEach((item) => byId.set(item.lesson_id, item));
        return Array.from(byId.values());
      });
      setLessonNextCursor(page.next_cursor);
    } catch (cause) {
      setLessonListError(backendMessage(cause));
    } finally {
      setLoadingMoreLessons(false);
    }
  };

  useEffect(() => {
    let active = true;
    if (!resume?.uploadSessionId) {
      setSession(null);
      setSessionLoading(false);
      return () => { active = false; };
    }
    if (resume.organizationId !== organizationId) {
      setSession(null);
      setSessionLoading(false);
      setError("Phiên tải lên đã lưu thuộc tổ chức khác; không thể tiếp tục trong tổ chức hiện tại.");
      return () => { active = false; };
    }
    setSessionLoading(true);
    backendApi.uploadSessionStatus(resume.uploadSessionId)
      .then(async (status) => {
        if (!active) return;
        setSession(status);
        setProgress(Math.round((status.accepted_part_numbers.length / Math.max(1, status.expected_parts)) * 100));
        if (status.state === "COMPLETED") {
          await recoverCompletedUpload(resume);
          return;
        }
        if (status.state !== "OPEN") {
          setError("Phiên tải lên không còn mở. Hãy tải lại trạng thái trước khi tiếp tục.");
        }
      })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setSessionLoading(false); });
    return () => { active = false; };
  }, [organizationId, resume?.organizationId, resume?.uploadSessionId, recoverCompletedUpload]);

  const inspect = async (status: LessonSourceDocumentStatus) => {
    setSourceDocument(status);
    setRevision(null);
    if (status.revision_id) {
      const result = await backendApi.documentRevision(organizationId, lessonId, status.source_document_id, status.revision_id);
      setRevision(result);
    }
  };

  const upload = async () => {
    if (!file || !lessonId) {
      setError("Chọn một giáo án đang hoạt động và chọn lại đúng tệp nguồn để tiếp tục.");
      return;
    }
    const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
    const mediaType = MIME_BY_EXTENSION[extension];
    if (!mediaType) {
      setError("Chỉ nhận tệp PDF, DOCX hoặc PPTX.");
      return;
    }
    if (file.size < 1 || file.size > 25_000_000) {
      setError("Tệp phải từ 1 byte đến 25 MB.");
      return;
    }
    if (typeof crypto === "undefined" || !crypto.subtle) {
      setError("Trình duyệt hiện không hỗ trợ kiểm tra tính toàn vẹn tệp. Mở ứng dụng trên kết nối an toàn HTTPS.");
      return;
    }
    if (resume && (
      resume.organizationId !== organizationId || resume.lessonId !== lessonId ||
      resume.byteLength !== file.size || resume.lastModified !== file.lastModified
    )) {
      setError("Phiên đang lưu chỉ tiếp tục với đúng tổ chức, giáo án và tệp đã chọn ban đầu.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const sourceHash = await sha256(file);
      let activeResume = resume;
      if (activeResume && activeResume.sha256 !== sourceHash) {
        setError("Tệp không khớp phiên tải lên đã lưu. Chọn lại đúng tệp ban đầu; chưa gửi thêm phần nào.");
        return;
      }
      if (!activeResume) {
        activeResume = {
          organizationId,
          lessonId,
          byteLength: file.size,
          lastModified: file.lastModified,
          sha256: sourceHash,
          uploadSessionId: null,
          createKey: createIdempotencyKey(),
          completeKey: createIdempotencyKey(),
        };
        if (!persistResume(activeResume)) return;
      }

      let uploadSession: LessonUploadSession;
      if (!activeResume.uploadSessionId) {
        uploadSession = await backendApi.createUploadSession(organizationId, lessonId, {
          file_name: file.name,
          media_type: mediaType,
          byte_length: file.size,
          sha256: sourceHash,
        }, activeResume.createKey);
        const withSessionId = { ...activeResume, uploadSessionId: uploadSession.upload_session_id };
        if (!persistResume(withSessionId)) {
          await abortUploadWithRevision(uploadSession.upload_session_id, { knownRevision: uploadSession.revision }).catch(() => undefined);
          return;
        }
        activeResume = withSessionId;
      } else {
        uploadSession = await backendApi.uploadSessionStatus(activeResume.uploadSessionId);
        if (uploadSession.state === "COMPLETED") {
          await recoverCompletedUpload(activeResume);
          showToast("Hệ thống đã xác nhận phiên tải lên hoàn tất; trạng thái xử lý đã được khôi phục.", "info");
          return;
        }
        if (uploadSession.state !== "OPEN") {
          setSession(uploadSession);
          setError("Phiên tải lên không còn mở. Hãy tải lại trạng thái trước khi tiếp tục.");
          return;
        }
      }

      setSession(uploadSession);
      const accepted = new Set(uploadSession.accepted_part_numbers);
      let completeParts = accepted.size;
      setProgress(Math.round((completeParts / uploadSession.expected_parts) * 100));
      for (let partNumber = 1; partNumber <= uploadSession.expected_parts; partNumber += 1) {
        if (accepted.has(partNumber)) continue;
        const start = (partNumber - 1) * uploadSession.part_size_bytes;
        const endExclusive = Math.min(file.size, start + uploadSession.part_size_bytes);
        const chunk = file.slice(start, endExclusive);
        await backendApi.uploadLessonPart(
          uploadSession.upload_session_id,
          partNumber,
          chunk,
          start,
          endExclusive - 1,
          file.size,
          await sha256(chunk),
        );
        accepted.add(partNumber);
        completeParts += 1;
        setSession({ ...uploadSession, accepted_part_numbers: Array.from(accepted) });
        setProgress(Math.round((completeParts / uploadSession.expected_parts) * 100));
      }

      const status = await backendApi.completeUpload(uploadSession.upload_session_id, activeResume.completeKey);
      clearResume();
      await inspect(status);
      showToast("Tài liệu đã được tải lên và xử lý.", "ok");
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setUploading(false);
    }
  };

  const cancelUpload = async () => {
    if (!session || session.state !== "OPEN") return;
    setUploading(true);
    setError(null);
    try {
      // FEAT-066 C4: read the current revision, send it as If-Match with a key kept for that revision.
      const record = resume?.uploadSessionId === session.upload_session_id ? resume : null;
      const outcome = await abortUploadWithRevision(session.upload_session_id, {
        record,
        remember: (abortKey, abortRevision) => {
          if (record) persistResume({ ...record, abortKey, abortRevision });
        },
      });
      if (outcome.kind === "completed" && record) {
        await recoverCompletedUpload(record);
        showToast("Hệ thống đã xác nhận phiên tải lên hoàn tất; trạng thái xử lý đã được khôi phục.", "info");
        return;
      }
      clearResume();
      showToast(
        outcome.kind === "aborted" ? "Đã hủy phiên tải lên." : "Phiên tải lên đã đóng; đã xóa phiên đã lưu.",
        "info",
      );
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setUploading(false);
    }
  };

  const refreshUploadStatus = async () => {
    if (!resume?.uploadSessionId) return;
    setSessionLoading(true);
    setError(null);
    try {
      const latest = await backendApi.uploadSessionStatus(resume.uploadSessionId);
      setSession(latest);
      setProgress(Math.round((latest.accepted_part_numbers.length / Math.max(1, latest.expected_parts)) * 100));
      if (latest.state === "COMPLETED") {
        await recoverCompletedUpload(resume);
        showToast("Hệ thống đã xác nhận phiên tải lên hoàn tất; trạng thái xử lý đã được khôi phục.", "info");
      } else if (latest.state !== "OPEN") {
        setError("Phiên tải lên không còn mở. Hãy tải lại trạng thái trước khi tiếp tục.");
      }
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setSessionLoading(false);
    }
  };

  const refreshStatus = async () => {
    if (!sourceDocument || !lessonId) return;
    setUploading(true);
    setError(null);
    try {
      const latest = await backendApi.sourceDocument(organizationId, lessonId, sourceDocument.source_document_id);
      await inspect(latest);
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setUploading(false);
    }
  };

  const resumeFileMatches = Boolean(resume && file && file.size === resume.byteLength && file.lastModified === resume.lastModified);
  const resumeLessonTitle = resume ? lessons.find((item) => item.lesson_id === resume.lessonId)?.title : undefined;
  const sourceStatus = sourceDocument ? teacherStatusMeta(sourceDocument.state) : null;
  const revisionStatus = revision ? teacherStatusMeta(revision.review_state) : null;

  return (
    <div className="tw-page">
      <PageHeading eyebrow="Giáo viên · Học liệu" title="Nhập tài liệu" description="Tải PDF, DOCX hoặc PPTX; rà soát bản trích xuất trước khi đưa nội dung vào giáo án." />
      {!hasFirebaseAuthBridge() && <BackendModeNotice roleLabel="Giáo viên" />}
      {loading && <BackendNotice title="Đang tải giáo án">Đang tải danh sách giáo án đang hoạt động.</BackendNotice>}
      {!loading && lessons.length === 0 && <BackendNotice title="Cần có giáo án trước">Tạo giáo án trong màn Quản lý giáo án, sau đó quay lại để đính kèm tài liệu nguồn.</BackendNotice>}

      <section className="tw-card cozy-form-card cozy-form-card--wide cozy-form-stack tp-form-column">
        <h2 className="tw-h2">Tệp nguồn</h2>
        <div className="cozy-form-grid">
          <div className="cozy-span-3 cozy-form-stack">
            <FormField label="Giáo án đích" htmlFor="teacher-import-lesson" required>
              <Select id="teacher-import-lesson" aria-label="Giáo án đích" value={lessonId} disabled={uploading || Boolean(resume) || lessons.length === 0} onChange={(event) => { setLessonId(event.target.value); setSourceDocument(null); setRevision(null); }}>
                {lessons.map((item) => <option key={item.lesson_id} value={item.lesson_id}>{item.title} · {item.topic} · Phiên bản {item.current_version_no}</option>)}
              </Select>
            </FormField>
            {lessonListError && <BackendNotice title="Không tải được giáo án tiếp theo" tone="error">{lessonListError}</BackendNotice>}
            {lessonNextCursor && (
              <div>
                <Button type="button" variant="secondary" size="sm" loading={loadingMoreLessons} disabled={loadingMoreLessons || loading || Boolean(resume)} onClick={() => void loadMoreLessons()}>
                  {loadingMoreLessons ? "Đang tải…" : "Tải thêm giáo án"}
                </Button>
              </div>
            )}
          </div>
          <div className="teacher-file-field cozy-span-3">
            <span id="teacher-source-file-label" className="cozy-form-label">
              {resume ? "Chọn lại đúng tệp đã bắt đầu" : "Tệp nguồn · PDF, DOCX hoặc PPTX"}{" "}
              <span className="cozy-form-required" aria-hidden="true">*</span>
            </span>
            <label className="teacher-file-picker" htmlFor="teacher-source-file">
              <span className="teacher-file-picker-button"><Icon name="upload" size={17} /> Chọn tệp</span>
              <span className="teacher-file-picker-name">{file?.name ?? "Chưa chọn tệp"}</span>
              <input id="teacher-source-file" className="teacher-file-picker-input" type="file" accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation" aria-labelledby="teacher-source-file-label" aria-describedby="teacher-file-help" aria-required="true" disabled={uploading} onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError(null); }} />
            </label>
            <p className="teacher-file-help" id="teacher-file-help">Tối đa 25 MB.</p>
          </div>
        </div>
        {resume && <BackendNotice title="Đã lưu phiên tải lên tạm trong thẻ trình duyệt này" tone="warn">Chọn lại đúng tệp đã bắt đầu{resumeLessonTitle ? ` cho giáo án "${resumeLessonTitle}"` : ""}. Tên và nội dung tệp không bị lưu trong trình duyệt.</BackendNotice>}
        {sessionLoading && <BackendNotice title="Đang kiểm tra phiên tải lên">Đang kiểm tra tiến trình trước khi cho tiếp tục.</BackendNotice>}
        {file && <div className="tw-item tw-row tw-between tw-wrap"><span>{file.name}</span><span className="tw-meta">{(file.size / (1024 * 1024)).toFixed(2)} MB</span></div>}
        {resume && file && !resumeFileMatches && <BackendNotice title="Tệp được chọn không trùng phiên đã lưu" tone="error">Kích thước hoặc thời điểm sửa đổi khác phiên đã lưu. Chưa gửi thêm phần nào.</BackendNotice>}
        {session?.state === "OPEN" && <BackendNotice title="Phiên tải lên đang mở" tone="warn">Đã nhận {session.accepted_part_numbers.length}/{session.expected_parts} phần. Sau khi xác minh lại tệp, chỉ các phần còn thiếu mới được gửi.</BackendNotice>}
        {resume?.uploadSessionId && session && session.state !== "OPEN" && <BackendNotice title="Phiên tải lên không còn mở" tone="warn">Không thể tiếp tục phiên này. Hãy bắt đầu một lần tải lên mới nếu cần.</BackendNotice>}
        {error && <BackendNotice title="Không hoàn tất được quy trình nhập" tone="error">{error}</BackendNotice>}
        {!resume && (
          <FormActionBar hint={!uploading && !loading && (!file || !lessonId) ? "Chọn tệp nguồn ở trên để bật nút tải tài liệu lên." : undefined}>
            <Button type="button" variant="primary" loading={uploading} disabled={uploading || loading || !file || !lessonId} iconLeft={<Icon name="upload" size={16} />} onClick={() => void upload()}>
              {uploading ? "Đang tải…" : "Tải tài liệu lên"}
            </Button>
          </FormActionBar>
        )}
        {resume && !resume.uploadSessionId && (
          <FormActionBar hint={!resumeFileMatches || !lessonId ? "Chọn lại đúng tệp ban đầu để bật nút thử lại." : undefined}>
            <Button type="button" variant="primary" loading={uploading} disabled={uploading || loading || !resumeFileMatches || !lessonId} iconLeft={<Icon name="upload" size={16} />} onClick={() => void upload()}>
              {uploading ? "Đang kết nối…" : "Thử lại tạo phiên tải lên"}
            </Button>
          </FormActionBar>
        )}
        {resume?.uploadSessionId && (
          <FormActionBar
            danger={session?.state === "OPEN" ? <Button type="button" variant="secondary" className="tp-quiet-danger" disabled={uploading} onClick={() => void cancelUpload()}>Hủy phiên tải lên</Button> : undefined}
          >
            <Button type="button" variant="secondary" disabled={uploading || sessionLoading} onClick={() => void refreshUploadStatus()}>Kiểm tra trạng thái phiên</Button>
            <Button type="button" variant="primary" loading={uploading} disabled={uploading || loading || sessionLoading || !resumeFileMatches || session?.state !== "OPEN"} iconLeft={<Icon name="upload" size={16} />} onClick={() => void upload()}>
              {uploading ? "Đang tải…" : "Tiếp tục phần còn thiếu"}
            </Button>
          </FormActionBar>
        )}
        {(uploading || progress > 0) && <div className="cozy-form-field"><div className="tw-row tw-between"><span className="tw-meta">Tiến trình tải lên</span><span className="tw-meta" style={{ fontVariantNumeric: "tabular-nums" }}>{progress}%</span></div><progress className="cozy-progress" value={progress} max={100} /></div>}
      </section>

      {sourceDocument && sourceStatus && <section className="tw-card cozy-form-card cozy-form-card--wide cozy-form-stack tp-form-column">
        <div className="tw-row tw-between tw-wrap"><h2 className="tw-h2">Kết quả xử lý tài liệu</h2><Button type="button" variant="secondary" size="sm" disabled={uploading} onClick={() => void refreshStatus()}>Tải lại trạng thái</Button></div>
        <div className="tw-grid-2">
          <div className="tw-item"><span className="tw-meta">Trạng thái</span><div style={{ marginTop: 4 }}><StatusBadge tone={sourceStatus.tone}>{sourceStatus.label}</StatusBadge></div></div>
          <div className="tw-item"><span className="tw-meta">Tệp an toàn</span><strong style={{ display: "block" }}>{sourceDocument.safe_file_name}</strong></div>
          <div className="tw-item"><span className="tw-meta">Số trang / slide</span><strong style={{ display: "block" }}>{sourceDocument.page_or_slide_count ?? "Chưa có"}</strong></div>
        </div>
        {sourceDocument.warnings.length > 0 && <BackendNotice title="Cần kiểm tra kết quả trích xuất" tone="warn">Có lưu ý từ quá trình xử lý. Hãy rà soát kỹ các trường bên dưới trước khi xác nhận.</BackendNotice>}
        {revision && revisionStatus && <>
          <details className="tp-collapsible">
            <summary className="tp-collapsible-summary">
              <span className="tp-collapsible-title">
                <span>Bản trích xuất để rà soát</span>
                <StatusBadge tone={revisionStatus.tone}>{revisionStatus.label}</StatusBadge>
              </span>
              <ChevronDown size={16} aria-hidden="true" />
            </summary>
            <div className="tp-collapsible-body">
              {revision.page_coverage.length > 0 && <p className="tw-meta">Trang đã bao phủ: {revision.page_coverage.join(", ")}</p>}
              {revision.warnings.length > 0 && <BackendNotice title="Cần kiểm tra nội dung trích xuất" tone="warn">Bản trích xuất có lưu ý. Hãy đối chiếu nội dung với tài liệu gốc trước khi tạo bản nháp.</BackendNotice>}
              <div className="tw-grid-2" aria-label="Các trường đã trích xuất">
                {([
                  ["Tên giáo án", revision.extracted_fields.title],
                  ["Chủ đề", revision.extracted_fields.topic],
                  ["Đối tượng vẽ", revision.extracted_fields.drawing_subject],
                  ["Các bước vẽ", revision.extracted_fields.drawing_steps_text],
                  ["Ghi chú kiến thức", revision.extracted_fields.subject_learning_notes],
                  ["Định hướng lời dẫn", revision.extracted_fields.script_direction],
                ] as const).map(([label, value]) => (
                  <div className="tw-item" key={label}><span className="tw-meta">{label}</span><p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{typeof value === "string" && value ? value : "Chưa có nội dung trích xuất"}</p></div>
                ))}
                <div className="tw-item"><span className="tw-meta">Mục tiêu</span>
                  {Array.isArray(revision.extracted_fields.objectives) && revision.extracted_fields.objectives.some((item) => typeof item === "string")
                    ? <ul>{revision.extracted_fields.objectives.filter((item): item is string => typeof item === "string").map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
                    : <p>Chưa có nội dung trích xuất</p>}
                </div>
              </div>
              <details className="tw-item tp-collapsible">
                <summary>Xem chi tiết dữ liệu trích xuất</summary>
                <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", maxHeight: 360, overflow: "auto", fontFamily: "inherit" }}>{JSON.stringify(revision.extracted_fields, null, 2)}</pre>
              </details>
            </div>
          </details>
          <ImportToVersionPanel
            organizationId={organizationId}
            lessonId={lessonId}
            sourceDocument={sourceDocument}
            revision={revision}
            onRevisionConfirmed={() => setRevision((current) => current ? { ...current, review_state: "CONFIRMED" } : current)}
            onVersionCreated={() => setVersionsRefreshToken((current) => current + 1)}
          />
        </>}
      </section>}
      {sourceDocument && lessonId && <LessonVersionsPanel organizationId={organizationId} lessonId={lessonId} refreshToken={versionsRefreshToken} />}
    </div>
  );
}
