import {
  BackendApiError,
  type LessonContent,
  type TeacherLessonDetail,
  createIdempotencyKey,
} from "./backendApi";
import { pageQuery } from "./cursorPages";
import { data, enc, OccurrenceApiError, request, visibleAscii, write } from "./teacherHttp";

export type LessonReviewState = "DRAFT" | "PENDING_REVIEW" | "CHANGES_REQUESTED" | "APPROVED";

export interface LessonVersionSummary {
  contract: string;
  version_id: string;
  version_no: number;
  review_state: LessonReviewState;
  structured_content_hash: string;
  source_document_revision_id: string | null;
  authored_principal_ref: string;
  created_at: string;
}

export interface LessonVersionDetail extends LessonVersionSummary {
  lesson_id: string;
  content: LessonContent;
}

export interface LessonVersionsPage {
  contract: string;
  lesson_id: string;
  items: LessonVersionSummary[];
  next_cursor: string | null;
}

export interface PublicLessonHit {
  contract: string;
  lesson_id: string;
  version_id: string;
  structured_content_hash: string;
  title: string;
  topic: string;
  target_age_band_ref: string;
  target_age_band_version: number;
  activity_count: number;
  updated_at: string;
}

export interface PublicLessonPage {
  contract: string;
  items: PublicLessonHit[];
  next_cursor: string | null;
}

export interface PublicLessonSearchInput {
  q?: string;
  topic?: string;
  targetAgeBandRef?: string;
  targetAgeBandVersion?: number;
  limit?: number;
  cursor?: string;
  signal?: AbortSignal;
}

export interface RemixLessonResult {
  contract: string;
  lesson: TeacherLessonDetail;
  source: {
    lesson_id: string;
    version_id: string;
    content_sha256: string;
  };
}

const NO_STORE = "private, no-store";
const AGE_BAND_REF = /^[A-Za-z0-9._:-]{1,256}$/;

function hasControlCharacters(value: string) {
  for (const character of value) {
    const code = character.charCodeAt(0);
    if (code <= 0x1f || code === 0x7f) return true;
  }
  return false;
}

function organizationPath(organizationId: string) {
  if (!organizationId.trim()) throw new BackendApiError("Tổ chức chưa được cấu hình.", "INVALID_REQUEST", 400);
  return `/api/lesson-library/v1/organizations/${enc(organizationId)}`;
}

function validatePage(limit = 25, cursor?: string) {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new BackendApiError("Số mục mỗi trang phải từ 1 đến 100.", "INVALID_REQUEST", 400);
  }
  if (cursor !== undefined && cursor.length > 1024) {
    throw new BackendApiError("Vị trí trang không hợp lệ.", "INVALID_REQUEST", 400);
  }
}

function safeMessage(status: number, code: string, action: "read" | "search" | "remix") {
  if (status === 404 || code === "RESOURCE_NOT_FOUND") {
    return action === "remix"
      ? "Bài học không còn khả dụng để sao chép."
      : "Không tìm thấy nội dung hoặc bạn không có quyền truy cập.";
  }
  if (code === "INVALID_IDEMPOTENCY_KEY") return "Khóa yêu cầu không hợp lệ. Hãy thực hiện lại thao tác.";
  if (code === "INVALID_REQUEST") return "Thông tin tìm kiếm hoặc yêu cầu chưa hợp lệ.";
  if (code === "STALE_SOURCE_VERSION") return "Bản công khai đã thay đổi. Hãy làm mới tìm kiếm rồi thử lại.";
  if (code === "STALE_REVISION") return "Phiên bản đã thay đổi. Hãy tải lại nội dung rồi thử lại.";
  if (code === "RESOURCE_CONFLICT") return "Bài học đang có thay đổi khác. Hãy tải lại rồi thử lại.";
  if (status === 503 || code === "PROVIDER_UNAVAILABLE") return "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  if (status === 401) return "Phiên đăng nhập chưa sẵn sàng. Hãy đăng nhập lại.";
  if (status === 403) return "Tài khoản không có quyền thực hiện thao tác này.";
  return action === "search" ? "Không thể tìm bài học công khai lúc này." : "Không thể tải dữ liệu bài học lúc này.";
}

async function withSafeErrors<T>(action: "read" | "search" | "remix", run: () => Promise<T>): Promise<T> {
  try {
    return await run();
  } catch (cause) {
    if (cause instanceof Error && cause.name === "AbortError") throw cause;
    const backendError = cause instanceof BackendApiError ? cause : null;
    const status = backendError?.status ?? 0;
    const code = backendError?.code ?? "API_ERROR";
    const fields = cause instanceof OccurrenceApiError ? cause.fieldErrors : [];
    const retryable = cause instanceof OccurrenceApiError ? cause.retryable : status === 0 || status === 503;
    const retryAfter = cause instanceof OccurrenceApiError ? cause.retryAfterSeconds : undefined;
    const currentVersion = cause instanceof OccurrenceApiError ? cause.currentVersion : undefined;
    throw new OccurrenceApiError(
      safeMessage(status, code, action),
      code,
      status,
      backendError?.requestId,
      fields,
      retryable,
      retryAfter,
      currentVersion,
    );
  }
}

export async function listLessonVersions(
  organizationId: string,
  lessonId: string,
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<LessonVersionsPage> {
  const limit = options.limit ?? 25;
  validatePage(limit, options.cursor);
  return withSafeErrors("read", async () => data(await request<LessonVersionsPage>(
    `${organizationPath(organizationId)}/lessons/${enc(lessonId)}/versions${pageQuery({ limit, cursor: options.cursor })}`,
    { headers: { "Cache-Control": NO_STORE }, signal: options.signal },
  )));
}

export async function getLessonVersion(
  organizationId: string,
  lessonId: string,
  versionId: string,
  signal?: AbortSignal,
): Promise<LessonVersionDetail> {
  return withSafeErrors("read", async () => data(await request<LessonVersionDetail>(
    `${organizationPath(organizationId)}/lessons/${enc(lessonId)}/versions/${enc(versionId)}`,
    { headers: { "Cache-Control": NO_STORE }, signal },
  )));
}

export async function searchPublicLessons(
  organizationId: string,
  input: PublicLessonSearchInput = {},
): Promise<PublicLessonPage> {
  const { limit = 25, cursor } = input;
  validatePage(limit, cursor);
  const q = input.q?.trim();
  const topic = input.topic?.trim();
  if ((q && (q.length > 100 || hasControlCharacters(q))) || (topic && (topic.length > 120 || hasControlCharacters(topic)))) {
    throw new BackendApiError("Bộ lọc tìm kiếm chưa hợp lệ.", "INVALID_REQUEST", 400);
  }
  const hasAgeBandRef = input.targetAgeBandRef !== undefined && input.targetAgeBandRef.trim() !== "";
  const hasAgeBandVersion = input.targetAgeBandVersion !== undefined;
  if (hasAgeBandRef !== hasAgeBandVersion) {
    throw new BackendApiError("Mã và phiên bản nhóm tuổi cần được nhập cùng nhau.", "INVALID_REQUEST", 400);
  }
  let ageBandRef: string | undefined;
  if (hasAgeBandRef) {
    ageBandRef = input.targetAgeBandRef?.trim();
    if (!ageBandRef || !AGE_BAND_REF.test(ageBandRef) || !Number.isInteger(input.targetAgeBandVersion) || (input.targetAgeBandVersion ?? 0) < 1) {
      throw new BackendApiError("Mã hoặc phiên bản nhóm tuổi chưa hợp lệ.", "INVALID_REQUEST", 400);
    }
  }
  const query = pageQuery({
    q: q || undefined,
    topic: topic || undefined,
    target_age_band_ref: ageBandRef,
    target_age_band_version: ageBandRef ? input.targetAgeBandVersion : undefined,
    limit,
    cursor,
  });
  return withSafeErrors("search", async () => data(await request<PublicLessonPage>(
    `${organizationPath(organizationId)}/public-lessons${query}`,
    { headers: { "Cache-Control": NO_STORE }, signal: input.signal },
  )));
}

export async function remixLesson(
  organizationId: string,
  sourceLessonId: string,
  input: { sourceVersionId: string; sourceContentSha256: string },
  idempotencyKey: string = createIdempotencyKey(),
): Promise<RemixLessonResult> {
  if (!visibleAscii.test(idempotencyKey)) {
    throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  }
  if (!input.sourceVersionId || !/^[a-fA-F0-9]{64}$/.test(input.sourceContentSha256)) {
    throw new BackendApiError("Phiên bản bài học công khai chưa hợp lệ.", "INVALID_REQUEST", 400);
  }
  return withSafeErrors("remix", () => write<RemixLessonResult>(
    `${organizationPath(organizationId)}/lessons/${enc(sourceLessonId)}/remixes`,
    "POST",
    idempotencyKey,
    {
      source_version_id: input.sourceVersionId,
      source_content_sha256: input.sourceContentSha256,
    },
  ));
}
