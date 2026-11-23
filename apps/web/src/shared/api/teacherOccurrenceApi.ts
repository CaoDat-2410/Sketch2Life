// Teacher lesson-occurrence client (goal v3 Phase A: T-3a documents/plan revisions, T-2a generic upload
// sessions, T0.4 job status). These DTOs follow the backend `LessonOccurrence*`, `GenericUpload*` and
// `AiJobStatusV1` contracts. They are deliberately separate from the lesson-library DTOs
// (`/api/lesson-library/...`, `upload_session_id`, `Content-Range`): the two wire contracts differ.
// The client only handles opaque ids and refs; it never reads or logs a storage location or token.
import { BackendApiError, createIdempotencyKey } from "./backendApi";
import { data, enc, ifNoneMatch, request, write } from "./teacherHttp";
import type { ConditionalResult } from "./teacherHttp";
export { NOT_FOUND_OR_NO_ACCESS, OccurrenceApiError } from "./teacherHttp";
export type { ConditionalResult, FieldIssue } from "./teacherHttp";

export type OccurrenceState = "DRAFT" | "DOCUMENT_REVIEW" | "PLAN_REVIEW" | "APPROVED" | "SAMPLE_AVAILABLE" | "SAMPLE_USED" | "ARCHIVED";
export type UploadState = "OPEN" | "COMPLETED" | "ABORTED" | "EXPIRED" | "FAILED";
export type JobState = "queued" | "running" | "succeeded" | "failed_retryable" | "failed_exhausted" | "blocked_unsafe" | "cancelled";

export interface LessonVersionRef { lesson_id: string; version_id: string; content_sha256: string }
export interface Occurrence {
  contract: "LessonOccurrenceV1"; occurrence_id: string; class_id: string; title: string;
  scheduled_date: string | null; state: OccurrenceState; revision: number;
  responsible_teacher_ref: string; lesson_version_ref: LessonVersionRef | null;
  lesson_version_no: number | null; approved_plan: { revision_no: number; plan_hash: string; approved_at: string } | null;
  sample_video: { slot_state: "AVAILABLE" | "CLAIMED"; claimed_at: string | null; run_ref: string | null };
  created_at: string;
}
export interface OccurrencePage { contract: "LessonOccurrencePageV1"; items: Occurrence[]; next_cursor: string | null }
export interface UploadSession {
  contract: "GenericUploadSessionV1" | "GenericUploadCompletionV1"; upload_id: string; purpose: "RUN_ARTWORK" | "RUN_AUDIO" | "OCCURRENCE_DOCUMENT";
  target_ref: string; state: UploadState; part_size_bytes: number; expected_parts: number;
  accepted_parts: Array<{ part_no: number; byte_length: number; sha256: string }>;
  byte_count: number; expires_at: string; revision: number; asset_ref: string | null;
  asset_state: "READY" | null; error_code: string | null;
}
export interface UploadPartReceipt {
  contract: "GenericUploadPartReceiptV1"; upload_id: string; part_no: number; byte_length: number; sha256: string;
  accepted: boolean; accepted_part_count: number; byte_count: number; revision: number;
}
export interface SourceDocument {
  contract: "LessonSourceDocumentV1"; source_document_id: string; occurrence_id: string; file_name: string;
  file_extension: ".pdf" | ".docx" | ".pptx"; page_or_slide_count: number | null;
  document_state: "EXTRACTED" | "DELETED"; head_revision_no: number; job_ref: string;
  warnings: string[]; page_coverage: number[]; uploaded_at: string;
}
export interface SourceDocumentPage { contract: "LessonSourceDocumentPageV1"; items: SourceDocument[]; next_cursor: string | null }
export interface DocumentRevisionSummary { revision_no: number; origin: "EXTRACTION" | "TEACHER_EDIT"; review_state: "NEEDS_REVIEW" | "CONFIRMED"; text_hash: string; text_length: number; created_at: string }
export interface DocumentRevisionPage { contract: "LessonDocumentRevisionPageV1"; items: DocumentRevisionSummary[]; next_cursor: string | null }
export interface DocumentRevision extends DocumentRevisionSummary {
  contract: "LessonDocumentRevisionV2"; source_document_id: string; extracted_text: string; base_revision_no: number | null;
  parser: { name: string; version: string } | null; warnings: string[]; page_coverage: number[];
}
export interface AcceptedDocument {
  contract: "LessonSourceDocumentAcceptedV1"; source_document_id: string; document_revision_no: 1;
  job: { job_id: string; target_kind: "LESSON_SOURCE_DOCUMENT"; state: "succeeded" };
}
export interface PlanActivity { plan_activity_id?: string | null; order: number; kind: "LESSON" | "CUSTOM" | "CATALOG"; lesson_activity_id: string | null; title: string | null; description: string | null; snapshot_hash: string | null; checklist_required: boolean; checklist_version: string | null; confirmed: boolean }
export interface PlanRevision {
  contract: "LessonPlanRevisionV1"; occurrence_id: string; revision_no: number; state: "DRAFT" | "APPROVED" | "SUPERSEDED";
  content_hash: string; document_revision_ref: { document_id: string; revision_no: number } | null;
  objectives: string[]; teacher_direction: string; safety_notes: string | null; lesson_version_ref: LessonVersionRef | null;
  lesson_version_no: number | null; activities: PlanActivity[]; created_at: string; approved_at: string | null; supersedes_revision_no: number | null;
}
export interface PlanRevisionSummary extends Pick<PlanRevision, "revision_no" | "state" | "content_hash" | "created_at" | "approved_at"> { activity_count: number }
export interface PlanRevisionPage { contract: "LessonPlanRevisionPageV1"; items: PlanRevisionSummary[]; next_cursor: string | null }
export interface CreatePlanInput {
  expected_head_revision_no: number;
  document_revision_ref?: { document_id: string; revision_no: number } | null;
  objectives: string[]; teacher_direction: string; safety_notes?: string | null;
  activities: Array<{ kind: "LESSON"; lesson_activity_id: string }>;
}
export interface JobStatus {
  job_id: string; target_kind: string; target_ref: string; job_revision: number; attempt_number: number; target_revision: number;
  input_hash: string; state: JobState; result_disposition: "accepted" | "stale" | "rejected" | null; correlation_id: string;
  created_at: string; updated_at: string; started_at: string | null; completed_at: string | null;
  progress: { kind: "unknown" | "stages" | "percentage"; value: number | null; stage_label: string | null };
  failure: { code: string; retryable: boolean; public_message: string; attempts_remaining: number | null } | null;
  result_refs: Array<{ artifact_ref: string; sha256: string }>; poll_after_ms: number | null;
}

/** One key per upload step so a retry of the same user action replays instead of repeating it. */
export interface OccurrenceUploadKeys { create: string; complete: string }
export interface UploadOptions {
  keys?: OccurrenceUploadKeys;
  onProgress?: (done: number, total: number) => void;
  /** Called once the session exists, so the screen can offer a keyed abort. */
  onSession?: (session: UploadSession) => void;
  signal?: AbortSignal;
}

export const MAX_UPLOAD_PART_BYTES = 4 * 1024 * 1024;
export const MAX_DOCUMENT_BYTES = 25_000_000;
export const MAX_REVISION_TEXT_BYTES = 2 * 1024 * 1024;
export const JOB_POLL_MIN_MS = 2_000;
export const JOB_POLL_MAX_MS = 10_000;
export const LIST_PAGE_LIMIT = 100;
export const ABORT_STALE_ATTEMPTS = 3;
// Plan limits of the backend (domain/lesson_occurrences/plan.py); the form checks them before sending.
export const PLAN_LIMITS = { objectives: 12, objectiveChars: 1000, directionChars: 2000, safetyNotesChars: 2000 } as const;
export const JOB_POLL_MAX_TRANSIENT_FAILURES = 3;

export const TERMINAL_JOB_STATES: ReadonlySet<JobState> = new Set<JobState>(["succeeded", "failed_exhausted", "blocked_unsafe", "cancelled"]);
const occurrencePath = (id: string) => `/v1/lesson-occurrences/${enc(id)}`;
const docPath = (occurrenceId: string, documentId?: string) => `${occurrencePath(occurrenceId)}/documents${documentId ? `/${enc(documentId)}` : ""}`;
const plansPath = (occurrenceId: string, revisionNo?: number) => `${occurrencePath(occurrenceId)}/plan-revisions${revisionNo ? `/${revisionNo}` : ""}`;
const uploadPath = (id: string) => `/v1/upload-sessions/${enc(id)}`;
const pageQuery = (extra: Record<string, string | undefined> = {}, cursor?: string) => {
  const query = new URLSearchParams({ limit: String(LIST_PAGE_LIMIT) });
  for (const [name, value] of Object.entries(extra)) if (value) query.set(name, value);
  if (cursor) query.set("cursor", cursor);
  return `?${query}`;
};
export async function sha256Hex(bytes: ArrayBuffer): Promise<string> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) throw new BackendApiError("Trình duyệt không hỗ trợ kiểm tra toàn vẹn tệp.", "CRYPTO_UNAVAILABLE", 0);
  const digest = await subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
}

// The backend accepts only the media type that belongs to the file extension, whatever the browser reports as `file.type`.
function mediaTypeFor(file: File): string {
  if (/\.pdf$/i.test(file.name)) return "application/pdf";
  if (/\.docx$/i.test(file.name)) return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  return "application/vnd.openxmlformats-officedocument.presentationml.presentation";
}

export const teacherOccurrenceApi = {
  list: (classId: string, options: { state?: OccurrenceState; cursor?: string } = {}) =>
    request<OccurrencePage>(`/v1/lesson-occurrences${pageQuery({ class_id: classId, state: options.state }, options.cursor)}`).then(data),
  create: (input: { class_id: string; title: string; scheduled_date?: string | null; lesson_version_ref?: LessonVersionRef | null }, key = createIdempotencyKey()) =>
    write<Occurrence>("/v1/lesson-occurrences", "POST", key, input),
  get: (id: string, etag?: string) => request<Occurrence>(occurrencePath(id), { headers: ifNoneMatch(etag) }, true),

  // Generic upload sessions (T-2a). Parts are raw bytes, each with its own SHA-256; there is no Content-Range.
  createUpload: (input: { purpose: "OCCURRENCE_DOCUMENT" | "RUN_ARTWORK" | "RUN_AUDIO"; target_ref: string; media_type: string; expected_size_bytes: number; expected_sha256: string; file_name?: string }, key = createIdempotencyKey()) =>
    write<UploadSession>("/v1/upload-sessions", "POST", key, input),
  getUpload: (id: string) => request<UploadSession>(uploadPath(id)).then(data),
  putPart: (id: string, partNo: number, bytes: Blob, sha256: string, signal?: AbortSignal) =>
    request<UploadPartReceipt>(`${uploadPath(id)}/parts/${partNo}`, { method: "PUT", headers: { "Content-Type": "application/octet-stream", "X-Part-SHA256": sha256 }, body: bytes, signal }).then(data),
  completeUpload: (id: string, input: { expected_size_bytes: number; expected_sha256: string }, key = createIdempotencyKey()) =>
    write<UploadSession>(`${uploadPath(id)}/complete`, "POST", key, input),
  /** Abort needs the strong revision of the session as `If-Match` and its own key. */
  abortUpload: (id: string, revision: number, key = createIdempotencyKey()) =>
    write<UploadSession>(uploadPath(id), "DELETE", key, undefined, { "If-Match": `"${revision}"` }),
  /**
   * Reads the current revision, then aborts. A session that is no longer open is returned as it is. A stale revision
   * (the session moved between the read and the abort) re-reads it and retries with the new revision.
   */
  async abortOpenUpload(id: string, key = createIdempotencyKey()): Promise<UploadSession> {
    for (let attempt = 1; ; attempt += 1) {
      const current = await teacherOccurrenceApi.getUpload(id);
      if (current.state !== "OPEN") return current;
      try { return await teacherOccurrenceApi.abortUpload(id, current.revision, key); }
      catch (cause) {
        if (!(cause instanceof BackendApiError) || cause.code !== "STALE_REVISION" || attempt >= ABORT_STALE_ATTEMPTS) throw cause;
      }
    }
  },

  attachDocument: (occurrenceId: string, assetRef: string, key = createIdempotencyKey()) =>
    write<AcceptedDocument>(docPath(occurrenceId), "POST", key, { asset_ref: assetRef }),
  listDocuments: (occurrenceId: string, cursor?: string) => request<SourceDocumentPage>(`${docPath(occurrenceId)}${pageQuery({}, cursor)}`).then(data),
  getDocument: (occurrenceId: string, documentId: string, etag?: string) => request<SourceDocument>(docPath(occurrenceId, documentId), { headers: ifNoneMatch(etag) }, true),
  listDocumentRevisions: (occurrenceId: string, documentId: string, cursor?: string) =>
    request<DocumentRevisionPage>(`${docPath(occurrenceId, documentId)}/revisions${pageQuery({}, cursor)}`).then(data),
  getDocumentRevision: (occurrenceId: string, documentId: string, revision: number, etag?: string) =>
    request<DocumentRevision>(`${docPath(occurrenceId, documentId)}/revisions/${revision}`, { headers: ifNoneMatch(etag) }, true),
  editDocumentRevision: (occurrenceId: string, documentId: string, extractedText: string, expectedHeadRevisionNo: number, key = createIdempotencyKey()) => {
    if (new TextEncoder().encode(extractedText).byteLength > MAX_REVISION_TEXT_BYTES) return Promise.reject(new BackendApiError("Văn bản vượt quá giới hạn 2 MiB.", "TEXT_TOO_LARGE", 400));
    return write<DocumentRevision>(`${docPath(occurrenceId, documentId)}/revisions`, "POST", key, { extracted_text: extractedText, expected_head_revision_no: expectedHeadRevisionNo });
  },

  listPlans: (occurrenceId: string, cursor?: string) => request<PlanRevisionPage>(`${plansPath(occurrenceId)}${pageQuery({}, cursor)}`).then(data),
  getPlan: (occurrenceId: string, revision: number, etag?: string) => request<PlanRevision>(plansPath(occurrenceId, revision), { headers: ifNoneMatch(etag) }, true),
  createPlan: (occurrenceId: string, input: CreatePlanInput, key = createIdempotencyKey()) =>
    write<PlanRevision>(plansPath(occurrenceId), "POST", key, input),
  /** `checklist` stays empty: the backend's production safety-checklist registry is empty, so no entry can be invented here. */
  confirmPlan: (occurrenceId: string, revision: number, hash: string, key = createIdempotencyKey()) =>
    write<PlanRevision>(`${plansPath(occurrenceId, revision)}/confirm`, "POST", key, { expected_plan_hash: hash, checklist: [] }),

  getJob: (id: string, etag?: string, signal?: AbortSignal) => request<JobStatus>(`/v1/jobs/${enc(id)}`, { headers: ifNoneMatch(etag), signal }, true),

  /** Upload a PDF/DOCX/PPTX in parts of at most 4 MiB and return the opaque asset ref. Parts the session already holds are skipped. */
  async uploadOccurrenceFile(file: File, occurrenceId: string, options: UploadOptions = {}): Promise<string> {
    if (file.size < 1 || file.size > MAX_DOCUMENT_BYTES || !/\.(pdf|docx|pptx)$/i.test(file.name)) {
      throw new BackendApiError("Chọn tệp PDF, DOCX hoặc PPTX có kích thước tối đa 25 MB.", "INVALID_FILE", 400);
    }
    return uploadFileForPurpose(file, occurrenceId, "OCCURRENCE_DOCUMENT", mediaTypeFor(file), options);
  },
};

/** Shared resumable upload; callers validate file type and size before invoking it. */
export async function uploadFileForPurpose(file: File, targetRef: string, purpose: "OCCURRENCE_DOCUMENT" | "RUN_ARTWORK" | "RUN_AUDIO", mediaType: string, options: UploadOptions = {}): Promise<string> {
    const keys = options.keys ?? { create: createIdempotencyKey(), complete: createIdempotencyKey() };
    const bytes = await file.arrayBuffer();
    const fullHash = await sha256Hex(bytes);
    const created = await teacherOccurrenceApi.createUpload({ purpose, target_ref: targetRef, media_type: mediaType, expected_size_bytes: file.size, expected_sha256: fullHash, ...(purpose === "OCCURRENCE_DOCUMENT" ? { file_name: file.name } : {}) }, keys.create);
    options.onSession?.(created);
    if (options.signal?.aborted) throw new DOMException("Upload stopped", "AbortError");
    // Creating again with the same key replays the first answer (always OPEN, no parts), so the live state is read back:
    // it tells a resumed upload which parts exist and a finished one its asset ref.
    const session = await teacherOccurrenceApi.getUpload(created.upload_id);
    if (options.signal?.aborted) throw new DOMException("Upload stopped", "AbortError");
    if (session.state === "COMPLETED" && session.asset_ref) return session.asset_ref;
    if (session.state !== "OPEN") throw new BackendApiError("Phiên tải lên không còn mở. Hãy chọn tệp và tải lại.", "UPLOAD_SESSION_NOT_OPEN", 409);
    const partSize = session.part_size_bytes;
    if (!Number.isInteger(partSize) || partSize < 1 || partSize > MAX_UPLOAD_PART_BYTES) throw new BackendApiError("Kích thước phần tải lên không hợp lệ.", "INVALID_UPLOAD_SESSION", 502);
    const accepted = new Set(session.accepted_parts.map((part) => part.part_no));
    let done = 0;
    for (let offset = 0, partNo = 1; offset < file.size; offset += partSize, partNo += 1) {
      if (options.signal?.aborted) throw new DOMException("Upload stopped", "AbortError");
      const chunk = bytes.slice(offset, Math.min(offset + partSize, file.size));
      if (!accepted.has(partNo)) await teacherOccurrenceApi.putPart(session.upload_id, partNo, new Blob([chunk], { type: "application/octet-stream" }), await sha256Hex(chunk), options.signal);
      if (options.signal?.aborted) throw new DOMException("Upload stopped", "AbortError");
      done += chunk.byteLength;
      options.onProgress?.(done, file.size);
    }
    const complete = await teacherOccurrenceApi.completeUpload(session.upload_id, { expected_size_bytes: file.size, expected_sha256: fullHash }, keys.complete);
    if (options.signal?.aborted) throw new DOMException("Upload stopped", "AbortError");
    if (complete.state !== "COMPLETED" || !complete.asset_ref) throw new BackendApiError("Tệp chưa sẵn sàng để đính kèm.", "ASSET_NOT_READY", 409);
    return complete.asset_ref;
}

export interface PollOptions {
  wait?: (ms: number, signal: AbortSignal) => Promise<void>;
  get?: (id: string, etag?: string, signal?: AbortSignal) => Promise<ConditionalResult<JobStatus>>;
  pauseWhenHidden?: boolean;
  maxElapsedMs?: number;
}

/**
 * Polls `GET /v1/jobs/{id}` with `If-None-Match`. The delay starts at 2 s and doubles up to 10 s (a
 * `poll_after_ms` hint is honoured inside that range). It returns at a terminal state and throws an
 * `AbortError` as soon as the signal aborts, so unmounting the screen stops the loop.
 */
export async function pollJob(jobId: string, onUpdate: (job: JobStatus) => void, signal: AbortSignal, options: PollOptions = {}): Promise<JobStatus> {
  const wait = options.wait ?? defaultWait;
  const get = options.get ?? teacherOccurrenceApi.getJob;
  let etag: string | undefined;
  let current: JobStatus | null = null;
  let delay = JOB_POLL_MIN_MS;
  let failures = 0;
  const started = Date.now();
  while (!signal.aborted) {
    if (options.maxElapsedMs !== undefined && Date.now() - started >= options.maxElapsedMs) {
      if (current) return current;
      throw new DOMException("Polling stopped", "AbortError");
    }
    if (options.pauseWhenHidden && document.hidden) { await wait(delay, signal); continue; }
    let result: ConditionalResult<JobStatus>;
    try { result = await get(jobId, etag, signal); failures = 0; }
    catch (cause) {
      // A transient failure (network, 429, 502-504) is retried a few times with the same backoff; anything else ends the poll.
      const transient = cause instanceof BackendApiError && [0, 429, 502, 503, 504].includes(cause.status);
      if (!transient || signal.aborted || (failures += 1) > JOB_POLL_MAX_TRANSIENT_FAILURES) throw cause;
      await wait(delay, signal);
      delay = Math.min(delay * 2, JOB_POLL_MAX_MS);
      continue;
    }
    if (signal.aborted) break;
    etag = result.etag ?? etag;
    if (result.data) { current = result.data; onUpdate(current); }
    if (current && TERMINAL_JOB_STATES.has(current.state)) return current;
    const hint = current?.poll_after_ms;
    await wait(hint ? Math.min(Math.max(hint, JOB_POLL_MIN_MS), JOB_POLL_MAX_MS) : delay, signal);
    delay = Math.min(delay * 2, JOB_POLL_MAX_MS);
  }
  throw new DOMException("Polling stopped", "AbortError");
}

function defaultWait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) { reject(new DOMException("Polling stopped", "AbortError")); return; }
    const onAbort = () => { window.clearTimeout(timer); reject(new DOMException("Polling stopped", "AbortError")); };
    const timer = window.setTimeout(() => { signal.removeEventListener("abort", onAbort); resolve(); }, ms);
    signal.addEventListener("abort", onAbort, { once: true });
  });
}
