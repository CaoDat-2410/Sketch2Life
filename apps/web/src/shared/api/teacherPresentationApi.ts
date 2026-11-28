import { BackendApiError, apiBaseUrl, createIdempotencyKey } from "./backendApi";
import { parseApiError } from "./errorEnvelope";
import { authorizedHeaders, data, enc, request, visibleAscii, write } from "./teacherHttp";

export type PresentationPlacement = "FULL" | "LEFT" | "RIGHT";
export type PresentationSourceState = "CURRENT" | "STALE";
export type PresentationStaleReason = "PLAN_REVISION_CHANGED" | "MEDIA_SOURCE_CHANGED";

export type PresentationMedia =
  | { kind: "IMAGE"; asset_ref: string; alt_text: string; media_type: "image/jpeg" | "image/png" | "image/webp"; width: number; height: number; placement: PresentationPlacement }
  | { kind: "SVG_CATALOG"; catalog_entry_id: string; alt_text: string; canonical_sha256: string; placement: PresentationPlacement }
  | { kind: "SVG_AI"; svg_draft_id: string; alt_text: string; canonical_sha256: string; placement: PresentationPlacement }
  | { kind: "VIDEO_EMBED"; provider: "YOUTUBE" | "VIMEO"; video_id: string; embed_url: string; placement: PresentationPlacement };

export interface PresentationSlide {
  slide_id: string;
  position: number;
  title: string;
  body_text: string;
  media: PresentationMedia | null;
  media_state: "CURRENT" | "STALE" | null;
}

export interface PresentationRevision {
  contract: "LessonPresentationRevisionV1";
  revision_no: number;
  base_revision_no: number | null;
  state: "DRAFT" | "READY" | "SUPERSEDED";
  aspect_ratio: "16:9";
  source_state: PresentationSourceState;
  stale_reasons: PresentationStaleReason[];
  plan_revision_no: number;
  plan_content_hash: string;
  content_hash: string;
  slides: PresentationSlide[];
  created_at: string;
  readied_at: string | null;
}

export interface LessonPresentation {
  contract: "LessonPresentationV1";
  presentation_id: string;
  occurrence_id: string;
  revision: number;
  head_revision_no: number;
  ready_revision_no: number | null;
  source_state: PresentationSourceState;
  stale_reasons: PresentationStaleReason[];
  presentable: boolean;
  head: PresentationRevision;
}

export type PresentationOperation =
  | { op: "UPDATE_SLIDE"; slide_id: string; title?: string; body_text?: string }
  | { op: "ADD_SLIDE"; after_slide_id: string | null; title: string; body_text: string }
  | { op: "DELETE_SLIDE"; slide_id: string }
  | { op: "MOVE_SLIDE"; slide_id: string; to_position: number }
  | { op: "SET_MEDIA"; slide_id: string; placement: PresentationPlacement; media: { kind: "IMAGE"; asset_ref: string; alt_text: string } | { kind: "SVG_CATALOG"; catalog_entry_id: string; alt_text: string } | { kind: "SVG_AI"; svg_draft_id: string; alt_text: string } | { kind: "VIDEO_EMBED"; url: string } }
  | { op: "CLEAR_MEDIA"; slide_id: string };

export interface PresentationSvgDraft {
  contract: "PresentationSvgDraftV1";
  svg_draft_id: string;
  state: "PENDING_REVIEW" | "ACCEPTED" | "DISCARDED";
  revision: number;
  document: { schema_version: string; view_box: string; paths: Array<{ path_id: string; d: string; fill: string | null; stroke: string | null; stroke_width: number | null }> };
  preview_svg: string;
  canonical_sha256: string;
  generator: { name: string; version: string };
  license_id: string;
  created_at: string;
  decided_at: string | null;
}

export interface PresentationUploadKeys { create: string; complete: string }

const NOT_FOUND = "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
const NO_IMAGE = "Ảnh chưa thể hiển thị. Hãy tải lại bản trình bày.";
const placement = (value: unknown): value is PresentationPlacement => value === "FULL" || value === "LEFT" || value === "RIGHT";
const record = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object" && !Array.isArray(value));
const string = (value: unknown): value is string => typeof value === "string";
const hash = (value: unknown): value is string => string(value) && /^[a-f0-9]{64}$/i.test(value);
const validStaleReasons = (value: unknown): value is PresentationStaleReason[] => Array.isArray(value) && value.every((item) => item === "PLAN_REVISION_CHANGED" || item === "MEDIA_SOURCE_CHANGED");

function isMedia(value: unknown): value is PresentationMedia {
  if (!record(value) || !placement(value.placement)) return false;
  // A video embed has no alt_text; every picture kind must have one.
  if (value.kind !== "VIDEO_EMBED" && !string(value.alt_text)) return false;
  if (value.kind === "IMAGE") return typeof value.asset_ref === "string" && /^upl_[A-Za-z0-9._:-]{1,60}$/.test(value.asset_ref)
    && ["image/jpeg", "image/png", "image/webp"].includes(String(value.media_type))
    && Number.isInteger(value.width) && Number(value.width) > 0 && Number.isInteger(value.height) && Number(value.height) > 0;
  if (value.kind === "SVG_CATALOG") return string(value.catalog_entry_id) && hash(value.canonical_sha256);
  if (value.kind === "SVG_AI") return string(value.svg_draft_id) && hash(value.canonical_sha256);
  if (value.kind === "VIDEO_EMBED") return (value.provider === "YOUTUBE" || value.provider === "VIMEO")
    && string(value.video_id) && string(value.embed_url)
    && (value.provider === "YOUTUBE" ? value.embed_url.startsWith("https://www.youtube-nocookie.com/embed/") : value.embed_url.startsWith("https://player.vimeo.com/video/"));
  return false;
}

function isSlide(value: unknown): value is PresentationSlide {
  return record(value) && string(value.slide_id) && Number.isInteger(value.position) && Number(value.position) >= 1
    && string(value.title) && value.title.length <= 200 && string(value.body_text) && value.body_text.length <= 2000
    && (value.media === null || isMedia(value.media))
    && (value.media_state === null || value.media_state === "CURRENT" || value.media_state === "STALE");
}

export function isPresentationRevision(value: unknown): value is PresentationRevision {
  if (!record(value)) return false;
  return value.contract === "LessonPresentationRevisionV1" && Number.isInteger(value.revision_no) && Number(value.revision_no) > 0
    && (value.base_revision_no === null || (Number.isInteger(value.base_revision_no) && Number(value.base_revision_no) > 0))
    && (value.state === "DRAFT" || value.state === "READY" || value.state === "SUPERSEDED")
    && value.aspect_ratio === "16:9" && (value.source_state === "CURRENT" || value.source_state === "STALE")
    && validStaleReasons(value.stale_reasons) && Number.isInteger(value.plan_revision_no) && Number(value.plan_revision_no) > 0
    && hash(value.plan_content_hash) && hash(value.content_hash) && Array.isArray(value.slides)
    && value.slides.length >= 1 && value.slides.length <= 100 && value.slides.every(isSlide)
    && string(value.created_at) && (value.readied_at === null || string(value.readied_at));
}

export function isLessonPresentation(value: unknown): value is LessonPresentation {
  return record(value) && value.contract === "LessonPresentationV1" && string(value.presentation_id) && string(value.occurrence_id)
    && Number.isInteger(value.revision) && Number(value.revision) > 0 && Number.isInteger(value.head_revision_no) && Number(value.head_revision_no) > 0
    && (value.ready_revision_no === null || (Number.isInteger(value.ready_revision_no) && Number(value.ready_revision_no) > 0))
    && (value.source_state === "CURRENT" || value.source_state === "STALE") && validStaleReasons(value.stale_reasons)
    && typeof value.presentable === "boolean" && isPresentationRevision(value.head) && value.head.revision_no === value.head_revision_no;
}

export function isPresentationSvgDraft(value: unknown): value is PresentationSvgDraft {
  if (!record(value) || value.contract !== "PresentationSvgDraftV1" || !string(value.svg_draft_id)
    || !["PENDING_REVIEW", "ACCEPTED", "DISCARDED"].includes(String(value.state)) || !Number.isInteger(value.revision)
    || Number(value.revision) < 1 || !record(value.document) || !string(value.document.schema_version)
    || !string(value.document.view_box) || !Array.isArray(value.document.paths) || !string(value.preview_svg)
    || !hash(value.canonical_sha256) || !record(value.generator) || !string(value.generator.name)
    || !string(value.generator.version) || value.license_id !== "CC0-1.0" || !string(value.created_at)
    || (value.decided_at !== null && !string(value.decided_at))) return false;
  return value.document.paths.every((path) => record(path) && string(path.path_id) && string(path.d)
    && (path.fill === null || string(path.fill)) && (path.stroke === null || string(path.stroke))
    && (path.stroke_width === null || (typeof path.stroke_width === "number" && Number.isFinite(path.stroke_width))));
}

function requirePresentation(value: unknown): LessonPresentation {
  if (!isLessonPresentation(value)) throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", 502);
  return value;
}

function requireRevision(value: unknown): PresentationRevision {
  if (!isPresentationRevision(value)) throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", 502);
  return value;
}

function requireDraft(value: unknown): PresentationSvgDraft {
  if (!isPresentationSvgDraft(value)) throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", 502);
  return value;
}

const occurrencePath = (occurrenceId: string) => `/v1/lesson-occurrences/${enc(occurrenceId)}/presentation`;
const draftPath = (occurrenceId: string, draftId: string) => `${occurrencePath(occurrenceId)}/svg-drafts/${enc(draftId)}`;
const uploadPath = (uploadId: string) => `/v1/upload-sessions/${enc(uploadId)}`;
const MAX_IMAGE_BYTES = 20 * 1024 * 1024;
const MAX_UPLOAD_PART_BYTES = 4 * 1024 * 1024;

async function sha256Hex(bytes: ArrayBuffer): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new BackendApiError("Trình duyệt không hỗ trợ kiểm tra tệp.", "CRYPTO_UNAVAILABLE", 0);
  return Array.from(new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", bytes)), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function imageType(file: File): "image/jpeg" | "image/png" | "image/webp" | null {
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (extension === "jpg" || extension === "jpeg") return "image/jpeg";
  if (extension === "png") return "image/png";
  if (extension === "webp") return "image/webp";
  return null;
}

function uploadSession(value: unknown): value is { contract: "GenericUploadSessionV1" | "GenericUploadCompletionV1"; upload_id: string; purpose: string; target_ref: string; state: string; part_size_bytes: number; accepted_parts: Array<{ part_no: number }>; asset_ref: string | null } {
  return record(value) && (value.contract === "GenericUploadSessionV1" || value.contract === "GenericUploadCompletionV1")
    && string(value.upload_id) && string(value.purpose) && string(value.target_ref) && string(value.state) && Number.isInteger(value.part_size_bytes)
    && Number(value.part_size_bytes) > 0 && Number(value.part_size_bytes) <= MAX_UPLOAD_PART_BYTES
    && Array.isArray(value.accepted_parts) && value.accepted_parts.every((part) => record(part) && Number.isInteger(part.part_no))
    && (value.asset_ref === null || string(value.asset_ref));
}

async function uploadRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const result = await request<unknown>(path, init);
  return data(result) as T;
}

async function loadUpload(uploadId: string, occurrenceId: string) {
  const value = await uploadRequest<unknown>(uploadPath(uploadId));
  if (!uploadSession(value) || value.purpose !== "PRESENTATION_IMAGE" || value.target_ref !== occurrenceId) throw new BackendApiError("Dịch vụ trả về dữ liệu tải ảnh không hợp lệ.", "INVALID_RESPONSE", 502);
  return value;
}

async function errorForImage(response: Response, requestId: string): Promise<BackendApiError> {
  let body: unknown = null;
  try { body = await response.json() as unknown; } catch { /* hide non-envelope content */ }
  const parsed = parseApiError(body, response.status, response.headers.get("X-Request-ID") ?? requestId);
  const message = response.status === 404 ? NOT_FOUND : NO_IMAGE;
  return new BackendApiError(message, parsed.code, response.status, parsed.requestId);
}

async function writeWithRetryAfter(path: string, key: string, body: unknown): Promise<unknown> {
  if (!visibleAscii.test(key)) throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  const headers = await authorizedHeaders();
  const requestId = createIdempotencyKey();
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");
  headers.set("Idempotency-Key", key);
  headers.set("X-Request-ID", requestId);
  let response: Response;
  try { response = await fetch(`${apiBaseUrl()}${path}`, { method: "POST", headers, body: JSON.stringify(body) }); }
  catch { throw new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0, requestId); }
  const text = await response.text();
  let result: unknown = null;
  if (text) {
    try { result = JSON.parse(text) as unknown; }
    catch { throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", response.ok ? 502 : response.status, requestId); }
  }
  if (!response.ok) {
    const parsed = parseApiError(result, response.status, response.headers.get("X-Request-ID") ?? requestId);
    const retryHeader = response.headers.get("Retry-After");
    const retryAfterSeconds = retryHeader && /^\d{1,6}$/.test(retryHeader.trim())
      ? Math.max(1, Number(retryHeader.trim()))
      : parsed.retryAfterSeconds;
    const error = new BackendApiError("Dịch vụ không thể hoàn tất yêu cầu.", parsed.code, response.status, parsed.requestId);
    Object.assign(error, retryAfterSeconds === undefined ? {} : { retryAfterSeconds });
    throw error;
  }
  return result;
}

export const teacherPresentationApi = {
  get: async (occurrenceId: string): Promise<LessonPresentation> =>
    requirePresentation(data(await request<unknown>(occurrencePath(occurrenceId)))),

  create: async (occurrenceId: string, seed: "PLAN_ACTIVITIES" | "BLANK", key = createIdempotencyKey()): Promise<LessonPresentation> =>
    requirePresentation(await write<unknown>(occurrencePath(occurrenceId), "POST", key, { seed })),

  createRevision: async (occurrenceId: string, revision: number, input: { repin_to_current_plan: boolean; operations: PresentationOperation[] }, key = createIdempotencyKey()): Promise<LessonPresentation> => {
    if (!Number.isInteger(revision) || revision < 1) throw new BackendApiError("Hãy tải lại bản trình bày trước khi sửa.", "INVALID_REQUEST", 400);
    return requirePresentation(await write<unknown>(`${occurrencePath(occurrenceId)}/revisions`, "POST", key, input, { "If-Match": `"${revision}"` }));
  },

  getRevision: async (occurrenceId: string, revisionNo: number): Promise<PresentationRevision> => {
    const value = data(await request<unknown>(`${occurrencePath(occurrenceId)}/revisions/${revisionNo}`));
    return requireRevision(value);
  },

  ready: async (occurrenceId: string, revisionNo: number, revision: number, key = createIdempotencyKey()): Promise<LessonPresentation> => {
    if (!Number.isInteger(revision) || revision < 1) throw new BackendApiError("Hãy tải lại bản trình bày trước khi duyệt.", "INVALID_REQUEST", 400);
    return requirePresentation(await write<unknown>(`${occurrencePath(occurrenceId)}/revisions/${revisionNo}/ready`, "POST", key, undefined, { "If-Match": `"${revision}"` }));
  },

  createSvgDraft: async (occurrenceId: string, input: { plan_activity_id: string; subject_text: string }, key = createIdempotencyKey()): Promise<PresentationSvgDraft> =>
    requireDraft(await writeWithRetryAfter(`${occurrencePath(occurrenceId)}/svg-drafts`, key, input)),

  getSvgDraft: async (occurrenceId: string, draftId: string): Promise<PresentationSvgDraft> =>
    requireDraft(data(await request<unknown>(draftPath(occurrenceId, draftId)))),

  decideSvgDraft: async (occurrenceId: string, draftId: string, revision: number, decision: "ACCEPT" | "DISCARD", key = createIdempotencyKey()): Promise<PresentationSvgDraft> => {
    if (!Number.isInteger(revision) || revision < 1) throw new BackendApiError("Hãy tải lại bản SVG trước khi chọn.", "INVALID_REQUEST", 400);
    return requireDraft(await write<unknown>(`${draftPath(occurrenceId, draftId)}/decision`, "POST", key, { decision }, { "If-Match": `"${revision}"` }));
  },

  async image(occurrenceId: string, assetRef: string, signal?: AbortSignal): Promise<Blob> {
    const headers = await authorizedHeaders();
    const requestId = createIdempotencyKey();
    headers.set("Accept", "image/jpeg, image/png, image/webp");
    headers.set("X-Request-ID", requestId);
    let response: Response;
    try { response = await fetch(`${apiBaseUrl()}${occurrencePath(occurrenceId)}/images/${enc(assetRef)}`, { method: "GET", headers, signal }); }
    catch (cause) {
      if (cause instanceof Error && cause.name === "AbortError") throw cause;
      throw new BackendApiError(NO_IMAGE, "NETWORK_ERROR", 0, requestId);
    }
    if (!response.ok) throw await errorForImage(response, requestId);
    const contentType = response.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase();
    if (contentType !== "image/jpeg" && contentType !== "image/png" && contentType !== "image/webp") {
      throw new BackendApiError(NO_IMAGE, "INVALID_RESPONSE", 502, requestId);
    }
    return response.blob();
  },

  async uploadImage(file: File, occurrenceId: string, keys: PresentationUploadKeys = { create: createIdempotencyKey(), complete: createIdempotencyKey() }, onProgress?: (done: number, total: number) => void): Promise<string> {
    const mediaType = imageType(file);
    if (!mediaType || (file.type && file.type.toLowerCase() !== mediaType) || file.size < 1 || file.size > MAX_IMAGE_BYTES) {
      throw new BackendApiError("Chọn ảnh JPEG, PNG hoặc WebP có kích thước tối đa 20 MiB.", "INVALID_REQUEST", 400);
    }
    const bytes = await file.arrayBuffer();
    const fullHash = await sha256Hex(bytes);
    const created = await write<unknown>("/v1/upload-sessions", "POST", keys.create, {
      purpose: "PRESENTATION_IMAGE", target_ref: occurrenceId, media_type: mediaType,
      expected_size_bytes: file.size, expected_sha256: fullHash,
    });
    if (!uploadSession(created) || created.purpose !== "PRESENTATION_IMAGE" || created.target_ref !== occurrenceId || created.state !== "OPEN") throw new BackendApiError("Phiên tải ảnh chưa sẵn sàng. Hãy thử lại.", "INVALID_RESPONSE", 502);
    const session = await loadUpload(created.upload_id, occurrenceId);
    if (session.state === "COMPLETED" && session.asset_ref) return session.asset_ref;
    if (session.state !== "OPEN") throw new BackendApiError("Phiên tải ảnh không còn mở. Hãy chọn ảnh khác.", "UPLOAD_SESSION_NOT_OPEN", 409);
    const accepted = new Set(session.accepted_parts.map((part) => part.part_no));
    for (let offset = 0, partNo = 1; offset < file.size; offset += session.part_size_bytes, partNo += 1) {
      const chunk = bytes.slice(offset, Math.min(offset + session.part_size_bytes, file.size));
      if (!accepted.has(partNo)) {
        const digest = await sha256Hex(chunk);
        const receipt = await uploadRequest<unknown>(`${uploadPath(session.upload_id)}/parts/${partNo}`, {
          method: "PUT", headers: { "Content-Type": "application/octet-stream", "X-Part-SHA256": digest },
          body: new Blob([chunk], { type: "application/octet-stream" }),
        });
        if (!record(receipt) || receipt.accepted !== true || receipt.part_no !== partNo) throw new BackendApiError("Một phần ảnh chưa được xác nhận. Hãy thử lại.", "UPLOAD_INCOMPLETE", 422);
      }
      onProgress?.(Math.min(offset + chunk.byteLength, file.size), file.size);
    }
    const complete = await write<unknown>(`${uploadPath(session.upload_id)}/complete`, "POST", keys.complete, { expected_size_bytes: file.size, expected_sha256: fullHash });
    if (!uploadSession(complete) || complete.purpose !== "PRESENTATION_IMAGE" || complete.target_ref !== occurrenceId || complete.state !== "COMPLETED" || !complete.asset_ref) throw new BackendApiError("Ảnh chưa sẵn sàng để đính kèm.", "UPLOAD_INCOMPLETE", 422);
    return complete.asset_ref;
  },
};
