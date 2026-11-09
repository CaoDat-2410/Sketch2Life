import React, { useEffect, useState } from "react";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  type LessonDocumentRevisionPreview,
  type LessonSourceDocumentStatus,
  type LessonSummary,
  type LessonUploadSession,
} from "../../../shared/backendApi";
import { useTeacher } from "../context/TeacherContext";
import { Icon } from "../components/Icon";
import { PageHead } from "./T01WorkspaceScreen";

const MIME_BY_EXTENSION: Record<string, string> = {
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
};

async function sha256(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function TeacherApiImportPage() {
  const { showToast } = useTeacher();
  const organizationId = configuredOrganizationId();
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [lessonId, setLessonId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [session, setSession] = useState<LessonUploadSession | null>(null);
  const [sessionKey, setSessionKey] = useState("");
  const [sourceDocument, setSourceDocument] = useState<LessonSourceDocumentStatus | null>(null);
  const [revision, setRevision] = useState<LessonDocumentRevisionPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

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
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản không có assignment teacher trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.lessons(organizationId, { state: "ACTIVE" });
      })
      .then((page) => { if (active) { setLessons(page.items); setLessonId((current) => current || page.items[0]?.lesson_id || ""); } })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [organizationId]);

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
      setError("Chọn một giáo án đang hoạt động và một tệp nguồn.");
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
    const currentKey = `${lessonId}:${file.name}:${file.size}:${file.lastModified}`;
    if (session && currentKey !== sessionKey) {
      setError("Đang có upload dở. Tiếp tục đúng tệp đã chọn hoặc hủy upload trước khi đổi tệp.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const sourceHash = await sha256(file);
      let uploadSession = session;
      if (!uploadSession) {
        uploadSession = await backendApi.createUploadSession(organizationId, lessonId, {
          file_name: file.name,
          media_type: mediaType,
          byte_length: file.size,
          sha256: sourceHash,
        });
        setSession(uploadSession);
        setSessionKey(currentKey);
      }

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

      const status = await backendApi.completeUpload(uploadSession.upload_session_id);
      setSession(null);
      setSessionKey("");
      await inspect(status);
      showToast("Tài liệu đã được tải lên và xử lý qua API.", "ok");
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setUploading(false);
    }
  };

  const cancelUpload = async () => {
    if (!session) return;
    setUploading(true);
    setError(null);
    try {
      await backendApi.abortUploadSession(session.upload_session_id);
      setSession(null);
      setSessionKey("");
      setProgress(0);
      showToast("Đã hủy phiên upload.", "info");
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setUploading(false);
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

  return (
    <div className="tw-page">
      <PageHead title="Nhập tài liệu giáo án" hint="Chunk upload, SHA-256, scan an toàn và parser preview theo Lesson Library API." />
      <BackendModeNotice roleLabel="Giáo viên" />
      {error && <BackendNotice title="Không hoàn tất được quy trình nhập" tone="error">{error}</BackendNotice>}
      {loading && <BackendNotice title="Đang tải giáo án">Đang xác nhận role Teacher và tải danh sách lesson ACTIVE.</BackendNotice>}
      {!loading && lessons.length === 0 && <BackendNotice title="Cần có giáo án trước">Tạo giáo án trong màn Quản lý giáo án, sau đó quay lại để đính kèm tài liệu nguồn.</BackendNotice>}

      <section className="tw-card" style={{ maxWidth: 860 }}>
        <h2 className="tw-h2">Tệp nguồn</h2>
        <label className="tw-label">Giáo án đích
          <select className="tw-input" value={lessonId} disabled={uploading || Boolean(session) || lessons.length === 0} onChange={(event) => { setLessonId(event.target.value); setSourceDocument(null); setRevision(null); }}>
            {lessons.map((item) => <option key={item.lesson_id} value={item.lesson_id}>{item.title} · {item.topic} · bản {item.current_version_no}</option>)}
          </select>
        </label>
        <label className="tw-label" style={{ marginTop: 14 }}>PDF, DOCX hoặc PPTX · tối đa 25 MB
          <input className="tw-input" type="file" accept=".pdf,.docx,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation" disabled={uploading || Boolean(session)} onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError(null); }} />
        </label>
        {file && <div className="tw-item tw-row tw-between tw-wrap" style={{ marginTop: 12 }}><span>{file.name}</span><span className="tw-meta">{(file.size / (1024 * 1024)).toFixed(2)} MB · SHA-256 sẽ được tính trong trình duyệt</span></div>}
        {session && <BackendNotice title="Có phiên upload đang mở" tone="warn">Đã nhận {session.accepted_part_numbers.length}/{session.expected_parts} phần. Tiếp tục đúng tệp hiện tại hoặc hủy phiên.</BackendNotice>}
        {session && <div className="tw-row tw-wrap"><button type="button" className="tw-btn" disabled={uploading} onClick={() => void upload()}><Icon name="upload" size={16} /> Tiếp tục tải lên</button><button type="button" className="tw-btn is-ghost" disabled={uploading} onClick={() => void cancelUpload()}>Hủy phiên upload</button></div>}
        {!session && <button type="button" className="tw-btn" disabled={uploading || loading || !file || !lessonId} onClick={() => void upload()}><Icon name="upload" size={16} />{uploading ? "Đang tải…" : "Tải tài liệu lên"}</button>}
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
