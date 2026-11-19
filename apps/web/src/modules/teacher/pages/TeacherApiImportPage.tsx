import { useCallback, useEffect, useState } from "react";
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
import { PageHeading } from "../../../shared/components/FeatureAvailability";

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
      setError("Không thể lưu metadata phiên upload trong sessionStorage; chưa bắt đầu gửi tệp.");
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
      setError("Chưa có Firebase ID token để tải hoặc nhập tài liệu.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setError("Chưa cấu hình organization_id cho API Lesson Library.");
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
          throw new BackendApiError("Tài khoản không có assignment teacher trong tổ chức này.", "ROLE_MISMATCH", 403);
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
      setError("Phiên upload đã lưu thuộc organization khác; không thể tiếp tục trong organization hiện tại.");
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
          setError(`Phiên upload đang ở trạng thái ${status.state}. API không trả kết quả source document cho trạng thái này; không gửi lại tệp.`);
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
      setError("Chỉ nhận PDF, DOCX hoặc PPTX theo hợp đồng upload BE.");
      return;
    }
    if (file.size < 1 || file.size > 25_000_000) {
      setError("Tệp phải từ 1 byte đến 25.000.000 byte.");
      return;
    }
    if (typeof crypto === "undefined" || !crypto.subtle) {
      setError("Trình duyệt hiện không hỗ trợ Web Crypto để tính SHA-256. Mở ứng dụng trên localhost hoặc HTTPS.");
      return;
    }
    if (resume && (
      resume.organizationId !== organizationId || resume.lessonId !== lessonId ||
      resume.byteLength !== file.size || resume.lastModified !== file.lastModified
    )) {
      setError("Phiên đang lưu chỉ tiếp tục với đúng organization, giáo án và tệp đã chọn ban đầu.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const sourceHash = await sha256(file);
      let activeResume = resume;
      if (activeResume && activeResume.sha256 !== sourceHash) {
        setError("SHA-256 không khớp phiên upload đã lưu. Chọn lại đúng tệp; chưa gửi thêm phần nào.");
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
          await backendApi.abortUploadSession(uploadSession.upload_session_id).catch(() => undefined);
          return;
        }
        activeResume = withSessionId;
      } else {
        uploadSession = await backendApi.uploadSessionStatus(activeResume.uploadSessionId);
        if (uploadSession.state === "COMPLETED") {
          await recoverCompletedUpload(activeResume);
          showToast("Server đã xác nhận phiên upload hoàn tất; trạng thái xử lý đã được khôi phục.", "info");
          return;
        }
        if (uploadSession.state !== "OPEN") {
          setSession(uploadSession);
          setError(`Phiên upload đang ở trạng thái ${uploadSession.state}. API không trả kết quả source document cho trạng thái này; không gửi lại tệp.`);
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
      showToast("Tài liệu đã được tải lên và xử lý qua API.", "ok");
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
      await backendApi.abortUploadSession(session.upload_session_id);
      clearResume();
      showToast("Đã hủy phiên upload qua API.", "info");
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
        showToast("Server đã xác nhận phiên upload hoàn tất; trạng thái xử lý đã được khôi phục.", "info");
      } else if (latest.state !== "OPEN") {
        setError(`Phiên upload đang ở trạng thái ${latest.state}. API không trả kết quả source document cho trạng thái này; không gửi lại tệp.`);
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

  return (
    <div className="tw-page">
      <PageHeading eyebrow="Teacher · Học liệu" title="Nhập tài liệu" description="Tải PDF, DOCX hoặc PPTX; rà soát bản trích xuất trước khi đưa nội dung vào giáo án." />
      <BackendModeNotice roleLabel="Giáo viên" />
      {error && <BackendNotice title="Không hoàn tất được quy trình nhập" tone="error">{error}</BackendNotice>}
      {loading && <BackendNotice title="Đang tải giáo án">Đang xác nhận role Teacher và tải danh sách lesson ACTIVE.</BackendNotice>}
      {!loading && lessons.length === 0 && <BackendNotice title="Cần có giáo án trước">Tạo giáo án trong màn Quản lý giáo án, sau đó quay lại để đính kèm tài liệu nguồn.</BackendNotice>}

      <section className="tw-card" style={{ maxWidth: 860 }}>
        <h2 className="tw-h2">Tệp nguồn</h2>
        <label className="tw-label">Giáo án đích
          <select className="tw-input" value={lessonId} disabled={uploading || Boolean(resume) || lessons.length === 0} onChange={(event) => { setLessonId(event.target.value); setSourceDocument(null); setRevision(null); }}>
            {lessons.map((item) => <option key={item.lesson_id} value={item.lesson_id}>{item.title} · {item.topic} · bản {item.current_version_no}</option>)}
          </select>
        </label>
        {lessonListError && <BackendNotice title="Không tải được giáo án tiếp theo" tone="error">{lessonListError}</BackendNotice>}
        {lessonNextCursor && <button type="button" className="tw-btn is-ghost is-sm" style={{ marginTop: 8 }} disabled={loadingMoreLessons || loading || Boolean(resume)} onClick={() => void loadMoreLessons()}>{loadingMoreLessons ? "Đang tải…" : "Tải thêm giáo án"}</button>}
        {resume && <BackendNotice title="Đã lưu metadata phiên upload trong tab này" tone="warn">Chọn lại tệp đã bắt đầu cho giáo án {resume.lessonId}. Chỉ kích thước, thời điểm sửa, hash, session ID và khóa retry được lưu; tên/nội dung tệp và credential không được lưu trong trình duyệt.</BackendNotice>}
        {sessionLoading && <BackendNotice title="Đang kiểm tra phiên upload">Đang đọc trạng thái server trước khi cho tiếp tục.</BackendNotice>}
        <div className="teacher-file-field" style={{ marginTop: 14 }}>
          <label className="tw-label" htmlFor="teacher-source-file">{resume ? "Chọn lại đúng tệp đã bắt đầu" : "Tệp nguồn · PDF, DOCX hoặc PPTX"}</label>
          <label className="teacher-file-picker" htmlFor="teacher-source-file">
            <span className="teacher-file-picker-button"><Icon name="upload" size={17} /> Chọn tệp</span>
            <span className="teacher-file-picker-name">{file?.name ?? "Chưa chọn tệp"}</span>
            <input id="teacher-source-file" className="teacher-file-picker-input" type="file" accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation" aria-describedby="teacher-file-help" disabled={uploading} onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError(null); }} />
          </label>
          <p className="teacher-file-help" id="teacher-file-help">Tối đa 25 MB. Trình duyệt tính SHA-256 để đối chiếu phiên upload khi tiếp tục.</p>
        </div>
        {file && <div className="tw-item tw-row tw-between tw-wrap" style={{ marginTop: 12 }}><span>{file.name}</span><span className="tw-meta">{(file.size / (1024 * 1024)).toFixed(2)} MB · SHA-256 sẽ được tính trong trình duyệt</span></div>}
        {resume && file && !resumeFileMatches && <BackendNotice title="Tệp được chọn không trùng metadata phiên" tone="error">Kích thước hoặc thời điểm sửa đổi khác phiên đã lưu. Chưa gửi thêm phần nào.</BackendNotice>}
        {session?.state === "OPEN" && <BackendNotice title="Phiên upload đang mở trên server" tone="warn">Đã nhận {session.accepted_part_numbers.length}/{session.expected_parts} phần. Sau khi xác minh lại SHA-256, chỉ các phần còn thiếu mới được gửi.</BackendNotice>}
        {resume?.uploadSessionId && session && session.state !== "OPEN" && <BackendNotice title="Phiên upload không còn mở" tone="warn">Server báo {session.state}. API status chưa trả source_document_id để nối tiếp kết quả đã đóng; không gửi lại tệp.</BackendNotice>}
        {!resume && <button type="button" className="tw-btn" disabled={uploading || loading || !file || !lessonId} onClick={() => void upload()}><Icon name="upload" size={16} />{uploading ? "Đang tải…" : "Tải tài liệu lên"}</button>}
        {resume && !resume.uploadSessionId && <button type="button" className="tw-btn" disabled={uploading || loading || !resumeFileMatches || !lessonId} onClick={() => void upload()}><Icon name="upload" size={16} />{uploading ? "Đang kết nối…" : "Thử lại tạo phiên upload"}</button>}
        {resume?.uploadSessionId && <div className="tw-row tw-wrap">
          <button type="button" className="tw-btn" disabled={uploading || loading || sessionLoading || !resumeFileMatches || session?.state !== "OPEN"} onClick={() => void upload()}><Icon name="upload" size={16} />{uploading ? "Đang tải…" : "Tiếp tục phần còn thiếu"}</button>
          {session?.state === "OPEN" && <button type="button" className="tw-btn is-ghost" disabled={uploading} onClick={() => void cancelUpload()}>Hủy phiên upload</button>}
          <button type="button" className="tw-btn is-ghost" disabled={uploading || sessionLoading} onClick={() => void refreshUploadStatus()}>Kiểm tra trạng thái phiên</button>
        </div>}
        {(uploading || progress > 0) && <div style={{ marginTop: 12 }}><div className="tw-row tw-between"><span className="tw-meta">Tiến trình upload</span><span className="tw-meta" style={{ fontVariantNumeric: "tabular-nums" }}>{progress}%</span></div><progress value={progress} max={100} style={{ width: "100%" }} /></div>}
      </section>

      {sourceDocument && <section className="tw-card" style={{ maxWidth: 860, marginTop: 16 }}>
        <div className="tw-row tw-between tw-wrap"><h2 className="tw-h2">Kết quả xử lý tài liệu</h2><button type="button" className="tw-btn is-ghost is-sm" disabled={uploading} onClick={() => void refreshStatus()}>Tải lại trạng thái</button></div>
        <div className="tw-grid-2"><div className="tw-item"><span className="tw-meta">Trạng thái</span><strong style={{ display: "block" }}>{sourceDocument.state}</strong></div><div className="tw-item"><span className="tw-meta">Tệp an toàn</span><strong style={{ display: "block" }}>{sourceDocument.safe_file_name}</strong></div><div className="tw-item"><span className="tw-meta">Số trang / slide</span><strong style={{ display: "block" }}>{sourceDocument.page_or_slide_count ?? "Chưa có"}</strong></div><div className="tw-item"><span className="tw-meta">Parser</span><strong style={{ display: "block" }}>{sourceDocument.parser_version ?? "Chưa có"}</strong></div></div>
        {sourceDocument.warnings.length > 0 && <BackendNotice title="Cảnh báo parser" tone="warn">{sourceDocument.warnings.join(" · ")}</BackendNotice>}
        {revision && <>
          <div className="tw-row tw-between tw-wrap"><h3 className="tw-h2" style={{ fontSize: 17 }}>Bản trích xuất để rà soát</h3><span className="tw-chip is-gray">{revision.review_state} · parser {revision.parser_version}</span></div>
          {revision.page_coverage.length > 0 && <p className="tw-meta">Trang đã bao phủ: {revision.page_coverage.join(", ")}</p>}
          {revision.warnings.length > 0 && <BackendNotice title="Cần kiểm tra nội dung trích xuất" tone="warn">{revision.warnings.join(" · ")}</BackendNotice>}
          <pre className="tw-item" style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", maxHeight: 360, overflow: "auto", fontFamily: "inherit" }}>{JSON.stringify(revision.extracted_fields, null, 2)}</pre>
          <BackendNotice title="Chưa tạo phiên bản giáo án từ bản trích xuất" tone="info">Hãy rà soát và biên tập structured content trước. API tạo version yêu cầu toàn bộ LessonContentInputV1 và revision hiện hành; tài liệu nguồn không tự động xuất bản.</BackendNotice>
        </>}
      </section>}
    </div>
  );
}
