import React from "react";

export type PortalRole = "parent" | "teacher" | "school_manager" | "platform_admin";

export interface RuntimeConfig {
  apiBaseUrl?: string;
  organizationId?: string;
}

export interface FirebaseAuthBridge {
  getIdToken: () => Promise<string | null>;
  signIn?: (email: string, password: string) => Promise<void>;
  signOut?: () => Promise<void>;
}

declare global {
  interface Window {
    sketch2lifeConfig?: RuntimeConfig;
    sketch2lifeAuth?: FirebaseAuthBridge;
  }
}

export interface ApiErrorBody {
  code: string;
  message: string;
  request_id?: string;
}

export class BackendApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "BackendApiError";
  }
}

export interface Be1Class {
  class_id: string;
  display_name: string;
  state: string;
}

export interface Be1CreatedClass {
  contract: "Be1ClassV1";
  class_id: string;
  display_name: string;
}

export interface Be1Assignment {
  assignment_id?: string;
  subject?: string;
  role: "school_admin" | "teacher" | "guide" | "observer";
  class_id: string | null;
  active?: boolean;
}

export interface Be1Assignments {
  contract: "Be1AdultAssignmentsV1";
  subject: string;
  organization_id: string;
  assignments: Be1Assignment[];
}

export interface LessonSummary {
  contract: "LessonSummaryV1";
  lesson_id: string;
  title: string;
  topic: string;
  current_version_no: number;
  review_state: string;
  visibility: string;
  activity_count: number;
  updated_at: string;
}

export interface LessonPage {
  contract: "LessonPageV1";
  items: LessonSummary[];
  next_cursor: string | null;
}

export interface ParentLessonSummary {
  contract: "ParentLessonSummaryV1";
  lesson_id: string;
  version_id: string;
  title: string;
  topic: string;
  target_age_band_ref: string;
  target_age_band_version: number;
  activity_count: number;
  access_source: "PUBLIC" | "SHARED";
}

export interface ParentLessonPage {
  contract: "ParentLessonPageV1";
  items: ParentLessonSummary[];
  next_cursor: string | null;
}

export interface AccessGrant {
  contract: "LessonAccessGrantV1";
  access_grant_id: string;
  lesson_id: string;
  version_id: string;
  audience_kind: string;
  audience_ref: string | null;
  capability: string;
  state: string;
  granted_by: string;
  approved_by: string | null;
  approved_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  revision: number;
}

export interface AccessGrantPage {
  contract: "LessonAccessGrantPageV1";
  items: AccessGrant[];
  next_cursor: string | null;
}

export interface LessonActivity {
  title: string;
  objective: string;
  materials_text: string;
  preparation_text: string;
  instructions_text: string;
  observation_notes: string;
  safety_notes: string;
  activity_kind: "outdoor" | "indoor" | "mixed";
}

export interface LessonContent {
  locale: "vi-VN";
  title: string;
  topic: string;
  target_age_band_ref: string;
  target_age_band_version: number;
  objectives: string[];
  drawing_subject: string;
  drawing_steps_text: string;
  subject_learning_notes: string;
  script_direction: string | null;
  script_following_allowed: boolean;
  activities: LessonActivity[];
}

export interface TeacherLessonDetail {
  contract: "LessonDetailV1";
  lesson_id: string;
  organization_id: string;
  owner_kind: "ORGANIZATION";
  created_by: string;
  state: "ACTIVE" | "ARCHIVED";
  visibility: "PRIVATE" | "SCHOOL" | "SELECTED_AUDIENCE" | "PUBLIC";
  moderation_state: "VISIBLE" | "HIDDEN";
  current_version: {
    contract: "LessonVersionV1";
    lesson_id: string;
    version_id: string;
    version_no: number;
    review_state: "DRAFT" | "PENDING_REVIEW" | "CHANGES_REQUESTED" | "APPROVED";
    structured_content_hash: string;
    source_document_revision_id: string | null;
    authored_principal_ref: string;
    created_at: string;
    content: LessonContent | null;
  };
  revision: number;
  created_at: string;
  updated_at: string;
}

export interface LessonUploadSession {
  contract: "UploadSessionV1";
  upload_session_id: string;
  state: string;
  part_size_bytes: number;
  expected_parts: number;
  accepted_part_numbers: number[];
  expires_at: string;
}

export interface LessonSourceDocumentStatus {
  contract: "LessonSourceDocumentStatusV1";
  source_document_id: string;
  state: string;
  safe_file_name: string;
  file_extension: string;
  page_or_slide_count: number | null;
  warnings: string[];
  parser_version: string | null;
  asset_sha256: string;
  revision_id: string | null;
}

export interface LessonDocumentRevisionPreview {
  contract: "LessonDocumentRevisionPreviewV1";
  revision_id: string;
  extracted_fields: Record<string, unknown>;
  warnings: string[];
  page_coverage: number[];
  review_state: string;
  parser_version: string;
}

export interface ParentLessonDetail {
  contract: "ParentLessonDetailV1";
  lesson_id: string;
  version_id: string;
  version_no: number;
  title: string;
  topic: string;
  locale: "vi-VN";
  target_age_band_ref: string;
  target_age_band_version: number;
  objectives: string[];
  drawing_subject: string;
  drawing_steps_text: string;
  subject_learning_notes: string;
  script_direction: string | null;
  script_following_allowed: boolean;
  activities: LessonActivity[];
  access_source: "PUBLIC" | "SHARED";
  access_expires_at: string | null;
}

function runtimeConfig(): RuntimeConfig {
  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {};
  const injected = typeof window === "undefined" ? {} : window.sketch2lifeConfig ?? {};
  return {
    apiBaseUrl: injected.apiBaseUrl || env.VITE_SKETCH2LIFE_API_BASE_URL,
    organizationId: injected.organizationId || env.VITE_SKETCH2LIFE_ORGANIZATION_ID,
  };
}

export function apiBaseUrl(): string {
  return (runtimeConfig().apiBaseUrl || "http://localhost:8000").replace(/\/+$/, "");
}

export function configuredOrganizationId(): string {
  return runtimeConfig().organizationId?.trim() ?? "";
}

export function hasFirebaseAuthBridge(): boolean {
  return typeof window !== "undefined" && typeof window.sketch2lifeAuth?.getIdToken === "function";
}

export function isLocalPreview(): boolean {
  if (typeof window === "undefined") return false;
  const localHost = ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
  return localHost && !hasFirebaseAuthBridge();
}

function createRequestId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `ui-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function errorFromResponse(body: unknown, status: number, headerRequestId: string | null): BackendApiError {
  const record = typeof body === "object" && body !== null ? body as Record<string, unknown> : {};
  const detail = typeof record.detail === "object" && record.detail !== null
    ? record.detail as Record<string, unknown>
    : record;
  const code = typeof detail.code === "string" ? detail.code : `HTTP_${status}`;
  const message = typeof detail.message === "string"
    ? detail.message
    : status === 401
      ? "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại."
      : status === 403
        ? "Tài khoản chưa được cấp quyền cho dữ liệu này."
        : "Backend không thể hoàn tất yêu cầu.";
  const requestId = typeof detail.request_id === "string" ? detail.request_id : headerRequestId ?? undefined;
  return new BackendApiError(message, code, status, requestId);
}

export async function backendRequest<T>(
  path: string,
  init: RequestInit = {},
  options: { auth?: boolean; timeoutMs?: number } = {},
): Promise<T> {
  const needsAuth = options.auth !== false;
  const headers = new Headers(init.headers);
  const requestId = headers.get("X-Request-ID") ?? createRequestId();
  headers.set("X-Request-ID", requestId);
  headers.set("Accept", "application/json");

  if (needsAuth) {
    const token = await window.sketch2lifeAuth?.getIdToken().catch(() => null);
    if (!token) {
      throw new BackendApiError("Chưa có phiên Firebase Authentication để gọi API.", "AUTHENTICATION_REQUIRED", 401);
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs ?? 15000);
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, { ...init, headers, signal: controller.signal });
    const text = await response.text();
    let body: unknown = null;
    if (text) {
      try { body = JSON.parse(text) as unknown; }
      catch { throw new BackendApiError("Backend trả về dữ liệu không đúng định dạng JSON.", "INVALID_RESPONSE", response.status, response.headers.get("X-Request-ID") ?? undefined); }
    }
    if (!response.ok) throw errorFromResponse(body, response.status, response.headers.get("X-Request-ID"));
    return body as T;
  } catch (error) {
    if (error instanceof BackendApiError) throw error;
    if (error instanceof Error && error.name === "AbortError") {
      throw new BackendApiError("Yêu cầu quá thời gian chờ. Hãy tải lại dữ liệu trước khi gửi lại thao tác.", "REQUEST_TIMEOUT", 408, requestId);
    }
    throw new BackendApiError("Không kết nối được backend. Kiểm tra địa chỉ API và trạng thái máy chủ.", "NETWORK_ERROR", 0, requestId);
  } finally {
    window.clearTimeout(timeout);
  }
}

const q = (params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") search.set(key, String(value));
  });
  const value = search.toString();
  return value ? `?${value}` : "";
};

const orgPath = (organizationId: string) => `/api/be1/v1/organizations/${encodeURIComponent(organizationId)}`;
const lessonPath = (organizationId: string) => `/api/lesson-library/v1/organizations/${encodeURIComponent(organizationId)}`;

export const backendApi = {
  health: () => backendRequest<{ status: "ok"; service: string }>("/health", {}, { auth: false }),
  assignments: (organizationId: string) => backendRequest<Be1Assignments>(`${orgPath(organizationId)}/me`),
  classes: (organizationId: string) => backendRequest<{ contract: string; items: Be1Class[] }>(`${orgPath(organizationId)}/classes`),
  profiles: (organizationId: string, classId: string) => backendRequest<{ contract: string; items: Array<{ child_id: string; class_id: string; display_name: string; age_months: number }> }>(`${orgPath(organizationId)}/classes/${encodeURIComponent(classId)}/profiles`),
  consents: (organizationId: string, classId: string) => backendRequest<{ contract: string; items: Array<{ consent_id: string; child_id: string; purpose_ref: string; state: string; effective: boolean }> }>(`${orgPath(organizationId)}/classes/${encodeURIComponent(classId)}/consents`),
  recordConsent: (organizationId: string, classId: string, childId: string, purposeRef: string) => backendRequest<Record<string, unknown>>(`${orgPath(organizationId)}/classes/${encodeURIComponent(classId)}/consents`, {
    method: "POST",
    headers: { "Idempotency-Key": createRequestId() },
    body: JSON.stringify({ class_id: classId, child_id: childId, purpose_ref: purposeRef }),
  }),
  createAssignment: (organizationId: string, subject: string, role: "school_admin" | "teacher", classId?: string) => backendRequest<Record<string, unknown>>(`${orgPath(organizationId)}/assignments`, {
    method: "POST",
    headers: { "Idempotency-Key": createRequestId() },
    body: JSON.stringify({ subject, role, ...(classId ? { class_id: classId } : {}) }),
  }),
  createClass: (organizationId: string, displayName: string) => backendRequest<Be1CreatedClass>(`${orgPath(organizationId)}/classes`, {
    method: "POST", body: JSON.stringify({ display_name: displayName }),
  }),
  lessons: (organizationId: string, options: { state?: string; visibility?: string; cursor?: string } = {}) =>
    backendRequest<LessonPage>(`${lessonPath(organizationId)}/lessons${q(options)}`),
  teacherLesson: (organizationId: string, lessonId: string) =>
    backendRequest<TeacherLessonDetail>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lessonId)}`),
  createLesson: (organizationId: string, content: LessonContent) =>
    backendRequest<TeacherLessonDetail>(`${lessonPath(organizationId)}/lessons`, {
      method: "POST",
      headers: { "Idempotency-Key": createRequestId() },
      body: JSON.stringify({ contract: "CreateLessonRequestV1", content, visibility: "PRIVATE" }),
    }),
  updateLesson: (organizationId: string, lesson: TeacherLessonDetail, content: LessonContent) =>
    backendRequest<TeacherLessonDetail>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lesson.lesson_id)}`, {
      method: "PATCH",
      headers: { "If-Match": `"${lesson.revision}"` },
      body: JSON.stringify({ contract: "UpdateLessonRequestV1", content }),
    }),
  archiveLesson: (organizationId: string, lesson: TeacherLessonDetail) =>
    backendRequest<TeacherLessonDetail>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lesson.lesson_id)}`, {
      method: "DELETE",
      headers: { "If-Match": `"${lesson.revision}"` },
    }),
  requestPublicReview: (organizationId: string, lesson: TeacherLessonDetail) =>
    backendRequest<AccessGrant>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lesson.lesson_id)}/access-grants`, {
      method: "POST",
      headers: { "Idempotency-Key": createRequestId() },
      body: JSON.stringify({
        contract: "CreateLessonAccessGrantRequestV1",
        version_id: lesson.current_version.version_id,
        audience_kind: "PUBLIC",
        audience_ref: null,
        capability: "VIEW",
        expires_at: null,
      }),
    }),
  createUploadSession: (organizationId: string, lessonId: string, payload: { file_name: string; media_type: string; byte_length: number; sha256: string }) =>
    backendRequest<LessonUploadSession>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lessonId)}/upload-sessions`, {
      method: "POST",
      headers: { "Idempotency-Key": createRequestId() },
      body: JSON.stringify({ contract: "CreateLessonUploadSessionRequestV1", ...payload }),
    }),
  uploadLessonPart: (uploadSessionId: string, partNumber: number, chunk: Blob, start: number, end: number, total: number, sha256: string) =>
    backendRequest<Record<string, unknown>>(`/api/lesson-library/v1/upload-sessions/${encodeURIComponent(uploadSessionId)}/parts/${partNumber}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/octet-stream",
        "X-Part-SHA256": sha256,
        "Content-Range": `bytes ${start}-${end}/${total}`,
      },
      body: chunk,
    }),
  completeUpload: (uploadSessionId: string) =>
    backendRequest<LessonSourceDocumentStatus>(`/api/lesson-library/v1/upload-sessions/${encodeURIComponent(uploadSessionId)}/complete`, {
      method: "POST",
      headers: { "Idempotency-Key": createRequestId() },
    }),
  abortUploadSession: (uploadSessionId: string) =>
    backendRequest<LessonUploadSession>(`/api/lesson-library/v1/upload-sessions/${encodeURIComponent(uploadSessionId)}`, { method: "DELETE" }),
  sourceDocument: (organizationId: string, lessonId: string, documentId: string) =>
    backendRequest<LessonSourceDocumentStatus>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lessonId)}/source-documents/${encodeURIComponent(documentId)}`),
  documentRevision: (organizationId: string, lessonId: string, documentId: string, revisionId: string) =>
    backendRequest<LessonDocumentRevisionPreview>(`${lessonPath(organizationId)}/lessons/${encodeURIComponent(lessonId)}/source-documents/${encodeURIComponent(documentId)}/revisions/${encodeURIComponent(revisionId)}`),
  parentLessons: (source: "ALL" | "PUBLIC" | "SHARED" = "ALL") =>
    backendRequest<ParentLessonPage>(`/api/lesson-library/v1/me/lessons${q({ source })}`),
  parentInvitations: () => backendRequest<{ contract: string; items: AccessGrant[] }>("/api/lesson-library/v1/me/lesson-invitations"),
  parentLesson: (lessonId: string) => backendRequest<ParentLessonDetail>(`/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}`),
  answerParentInvitation: (grantId: string, accept: boolean) => backendRequest<Record<string, unknown>>(
    `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(grantId)}/${accept ? "accept" : "decline"}`,
    { method: "POST", headers: { "Idempotency-Key": createRequestId() } },
  ),
  accessGrants: (organizationId: string, options: { state?: string; audience_kind?: string; lesson_id?: string; cursor?: string } = {}) =>
    backendRequest<AccessGrantPage>(`${lessonPath(organizationId)}/access-grants${q(options)}`),
  decideAccessGrant: (organizationId: string, grant: AccessGrant, decision: "APPROVE" | "REQUEST_CHANGES", reason?: string) =>
    backendRequest<Record<string, unknown>>(`${lessonPath(organizationId)}/access-grants/${encodeURIComponent(grant.access_grant_id)}/decision`, {
      method: "POST",
      headers: { "If-Match": `"${grant.revision}"`, "Idempotency-Key": createRequestId() },
      body: JSON.stringify({ contract: "DecideLessonAccessGrantRequestV1", decision, ...(reason ? { reason } : {}) }),
    }),
  moderateLesson: (lessonId: string, revision: number, state: "HIDDEN" | "VISIBLE", reason: string) =>
    backendRequest<Record<string, unknown>>(`/api/lesson-library/v1/platform/lessons/${encodeURIComponent(lessonId)}/moderation`, {
      method: "PATCH",
      headers: { "If-Match": `"${revision}"`, "Idempotency-Key": createRequestId() },
      body: JSON.stringify({ contract: "ModerateLessonRequestV1", state, reason }),
    }),
};

export async function signInAndResolveRole(
  expectedRole: PortalRole,
  email: string,
  password: string,
): Promise<void> {
  const auth = typeof window === "undefined" ? undefined : window.sketch2lifeAuth;
  if (!auth?.signIn || !auth.getIdToken) {
    throw new BackendApiError("Ứng dụng chưa được nối Firebase Authentication. Không thể đăng nhập bằng tài khoản giả lập.", "AUTH_PROVIDER_NOT_CONFIGURED", 503);
  }

  await auth.signIn(email, password);
  const token = await auth.getIdToken();
  if (!token) throw new BackendApiError("Firebase chưa cấp ID token cho phiên đăng nhập.", "AUTHENTICATION_REQUIRED", 401);

  try {
    if (expectedRole === "parent") {
      await backendApi.parentLessons();
      return;
    }
    if (expectedRole === "platform_admin") {
      throw new BackendApiError("BE chưa có API đọc quyền Platform Admin; không thể xác nhận role sau đăng nhập.", "ROLE_DISCOVERY_UNAVAILABLE", 501);
    }
    const organizationId = configuredOrganizationId();
    if (!organizationId) {
      throw new BackendApiError("Chưa cấu hình organization_id để kiểm tra role qua /organizations/{id}/me.", "ORGANIZATION_NOT_CONFIGURED", 503);
    }
    const result = await backendApi.assignments(organizationId);
    const expectedAssignment = expectedRole === "school_manager" ? "school_admin" : "teacher";
    if (!result.assignments.some((assignment) => assignment.role === expectedAssignment)) {
      throw new BackendApiError("Tài khoản đã đăng nhập nhưng role không khớp với cổng này.", "ROLE_MISMATCH", 403);
    }
  } catch (error) {
    await auth.signOut?.().catch(() => undefined);
    throw error;
  }
}

export function BackendNotice({
  title,
  children,
  tone = "info",
}: {
  title: string;
  children: React.ReactNode;
  tone?: "info" | "warn" | "error" | "success";
}) {
  const palette = {
    info: { background: "#E8EAFF", border: "#C7CCFF", color: "#192477" },
    warn: { background: "#fffbeb", border: "#fde68a", color: "#78350f" },
    error: { background: "#fef2f2", border: "#fecaca", color: "#7f1d1d" },
    success: { background: "#ecfdf5", border: "#a7f3d0", color: "#064e3b" },
  }[tone];
  return (
    <section role="status" style={{ margin: "14px 0", padding: "12px 16px", border: `1px solid ${palette.border}`, borderRadius: 14, background: palette.background, color: palette.color }}>
      <strong style={{ display: "block", marginBottom: 3 }}>{title}</strong>
      <div style={{ lineHeight: 1.5 }}>{children}</div>
    </section>
  );
}

export function BackendModeNotice({ roleLabel }: { roleLabel: string }) {
  if (isLocalPreview()) {
    return (
      <div className="backend-preview-notice" role="status" aria-label={`Bản xem thử ${roleLabel}`}>
        Xem thử · Dữ liệu minh họa, không lưu
      </div>
    );
  }
  if (!hasFirebaseAuthBridge()) {
    return (
      <BackendNotice title="Chưa có phiên Firebase Authentication" tone="error">
        Backend yêu cầu Firebase ID token. Giao diện sẽ không dùng dữ liệu mẫu để giả lập kết quả API.
      </BackendNotice>
    );
  }
  return (
    <BackendNotice title={`Đang dùng phiên đăng nhập cho ${roleLabel}`} tone="success">
      Dữ liệu và quyền truy cập được xác nhận từ backend.
    </BackendNotice>
  );
}

export function ApiUnavailableView({
  title,
  endpoint,
  detail,
}: {
  title: string;
  endpoint: string;
  detail: string;
}) {
  return (
    <main style={{ maxWidth: 760, margin: "7vh auto", padding: 24 }}>
      <BackendModeNotice roleLabel="đã đăng nhập" />
      <section aria-labelledby="unavailable-title" style={{ padding: 24, border: "1px solid #dbe3ef", borderRadius: 14, background: "#fff", color: "#0B0C0E" }}>
        <h1 id="unavailable-title" style={{ margin: "0 0 8px", fontSize: 24 }}>Màn hình này chưa sẵn sàng</h1>
        <p style={{ margin: "0 0 16px", lineHeight: 1.55, color: "#46536a" }}>
          Chức năng này chưa được kết nối trong phiên hiện tại. Thử quay lại màn trước; dữ liệu minh họa chỉ có trong bản xem thử.
        </p>
        <button type="button" onClick={() => window.history.back()} style={{ minHeight: 44, padding: "0 16px", border: 0, borderRadius: 9, background: "#1F2DE6", color: "#fff", font: "inherit", fontWeight: 650, cursor: "pointer" }}>
          Quay lại
        </button>
        <details style={{ marginTop: 18, color: "#526078", fontSize: 13 }}>
          <summary style={{ minHeight: 40, display: "inline-flex", alignItems: "center", cursor: "pointer", fontWeight: 600 }}>Thông tin kỹ thuật</summary>
          <strong style={{ display: "block", marginTop: 4 }}>{title}</strong>
          <p style={{ lineHeight: 1.5 }}>{detail}</p>
          <code style={{ display: "inline-block", padding: "6px 8px", border: "1px solid #CBD0D8", borderRadius: 6, background: "#F6F7F9", color: "#343A46" }}>{endpoint}</code>
        </details>
      </section>
    </main>
  );
}

export function backendMessage(error: unknown): string {
  if (error instanceof BackendApiError) {
    const request = error.requestId ? ` Mã yêu cầu: ${error.requestId}.` : "";
    if (error.code === "CONSENT_NOT_EFFECTIVE") return `Consent chưa được xác minh nên dữ liệu trẻ đang bị khóa.${request}`;
    if (error.code === "STALE_SESSION_REVISION" || error.code === "RESOURCE_CONFLICT") return `Dữ liệu đã thay đổi. Tải lại trước khi thao tác tiếp.${request}`;
    if (error.status === 401) return `Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Đăng nhập lại.${request}`;
    if (error.status === 403) return `Tài khoản này không có quyền xem hoặc sửa dữ liệu.${request}`;
    if (error.status === 503) return `Backend hoặc PostgreSQL hiện chưa sẵn sàng.${request}`;
    return `${error.message}${request}`;
  }
  return "Không tải được dữ liệu từ backend. Hãy thử tải lại.";
}
