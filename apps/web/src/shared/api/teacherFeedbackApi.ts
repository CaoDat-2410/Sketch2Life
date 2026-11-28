import { BackendApiError } from "./backendApi";
import { feedbackAuthorRole, feedbackDisplayName, type FeedbackAuthorRole } from "./feedbackLabels";
import { data, enc, request, write } from "./teacherHttp";

export interface TeacherFeedbackSummary {
  thread_id: string;
  lesson_id: string;
  version_id: string;
  lesson_title?: string | null;
  version_no?: number | null;
  revision: number;
  created_at: string;
}

export interface TeacherFeedbackMessage {
  message_id: string;
  body: string;
  from_you: boolean;
  author_role?: FeedbackAuthorRole;
  author_display_name?: string | null;
  created_at: string;
}

export interface TeacherFeedbackListPage {
  total: number;
  limit: number;
  next_cursor: string | null;
  items: TeacherFeedbackSummary[];
}

export interface TeacherFeedbackThreadPage {
  thread_id: string;
  organization_id: string;
  lesson_id: string;
  version_id: string;
  lesson_title?: string | null;
  version_no?: number | null;
  revision: number;
  limit: number;
  next_cursor: string | null;
  items: TeacherFeedbackMessage[];
}

function invalidResponse(message: string): BackendApiError {
  return new BackendApiError(message, "INVALID_RESPONSE", 200);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function isTimestamp(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

function lessonTitle(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function pagePath(organizationId: string, threadId: string | undefined, limit: number, cursor?: string): string {
  if (!organizationId.trim() || !Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new BackendApiError("Yêu cầu tải phản hồi không hợp lệ.", "INVALID_REQUEST", 400);
  }
  const root = `/api/lesson-library/v1/organizations/${enc(organizationId)}/feedback`;
  const query = new URLSearchParams({ limit: String(limit) });
  if (cursor) query.set("cursor", cursor);
  return `${root}${threadId === undefined ? "" : `/${enc(threadId)}`}?${query.toString()}`;
}

function parseList(value: unknown): TeacherFeedbackListPage {
  if (!isRecord(value) || !Number.isInteger(value.total) || Number(value.total) < 0
    || !Number.isInteger(value.limit) || Number(value.limit) < 1 || Number(value.limit) > 100
    || !(value.next_cursor === null || typeof value.next_cursor === "string") || !Array.isArray(value.items)) {
    throw invalidResponse("Không đọc được danh sách phản hồi.");
  }
  const items = value.items.map((entry): TeacherFeedbackSummary | null => {
    if (!isRecord(entry) || typeof entry.thread_id !== "string" || !entry.thread_id
      || typeof entry.lesson_id !== "string" || !entry.lesson_id
      || typeof entry.version_id !== "string" || !entry.version_id
      || !(entry.lesson_title === undefined || entry.lesson_title === null || typeof entry.lesson_title === "string")
      || !(entry.version_no === undefined || entry.version_no === null || (Number.isInteger(entry.version_no) && Number(entry.version_no) >= 1))
      || !Number.isInteger(entry.revision) || Number(entry.revision) < 1
      || !isTimestamp(entry.created_at)) return null;
    return {
      thread_id: entry.thread_id,
      lesson_id: entry.lesson_id,
      version_id: entry.version_id,
      ...(entry.lesson_title !== undefined ? { lesson_title: lessonTitle(entry.lesson_title) } : {}),
      ...(entry.version_no !== undefined ? { version_no: entry.version_no == null ? null : Number(entry.version_no) } : {}),
      revision: Number(entry.revision),
      created_at: entry.created_at,
    };
  });
  if (items.some((item) => item === null)) throw invalidResponse("Không đọc được danh sách phản hồi.");
  return {
    total: Number(value.total),
    limit: Number(value.limit),
    next_cursor: value.next_cursor as string | null,
    items: items as TeacherFeedbackSummary[],
  };
}

function parseThread(value: unknown): TeacherFeedbackThreadPage {
  if (!isRecord(value) || typeof value.thread_id !== "string" || !value.thread_id
    || typeof value.organization_id !== "string" || !value.organization_id
    || typeof value.lesson_id !== "string" || !value.lesson_id
    || typeof value.version_id !== "string" || !value.version_id
    || !(value.lesson_title === undefined || value.lesson_title === null || typeof value.lesson_title === "string")
    || !(value.version_no === undefined || value.version_no === null || (Number.isInteger(value.version_no) && Number(value.version_no) >= 1))
    || !Number.isInteger(value.revision) || Number(value.revision) < 1
    || !Number.isInteger(value.limit) || Number(value.limit) < 1 || Number(value.limit) > 100
    || !(value.next_cursor === null || typeof value.next_cursor === "string") || !Array.isArray(value.items)) {
    throw invalidResponse("Không đọc được nội dung phản hồi.");
  }
  const items = value.items.map((entry): TeacherFeedbackMessage | null => {
    if (!isRecord(entry) || typeof entry.message_id !== "string" || !entry.message_id
      || typeof entry.body !== "string" || typeof entry.from_you !== "boolean"
      || !(entry.author_role === undefined || ["parent", "teacher", "school_manager", "platform_admin", "other"].includes(String(entry.author_role)))
      || !(entry.author_display_name === undefined || entry.author_display_name === null || typeof entry.author_display_name === "string")
      || !isTimestamp(entry.created_at)) return null;
    return {
      message_id: entry.message_id,
      body: entry.body,
      from_you: entry.from_you,
      ...(entry.author_role !== undefined ? { author_role: feedbackAuthorRole(entry.author_role) } : {}),
      ...(entry.author_display_name !== undefined ? { author_display_name: feedbackDisplayName(entry.author_display_name) } : {}),
      created_at: entry.created_at,
    };
  });
  if (items.some((item) => item === null)) throw invalidResponse("Không đọc được nội dung phản hồi.");
  return {
    thread_id: value.thread_id,
    organization_id: value.organization_id,
    lesson_id: value.lesson_id,
    version_id: value.version_id,
    ...(value.lesson_title !== undefined ? { lesson_title: lessonTitle(value.lesson_title) } : {}),
    ...(value.version_no !== undefined ? { version_no: value.version_no == null ? null : Number(value.version_no) } : {}),
    revision: Number(value.revision),
    limit: Number(value.limit),
    next_cursor: value.next_cursor as string | null,
    items: items as TeacherFeedbackMessage[],
  };
}

function parseReply(value: unknown, threadId: string, expectedRevision: number): { thread_id: string; revision: number } {
  if (!isRecord(value) || value.thread_id !== threadId || value.revision !== expectedRevision + 1) {
    throw invalidResponse("Không xác nhận được phản hồi đã gửi.");
  }
  return { thread_id: threadId, revision: expectedRevision + 1 };
}

export const teacherFeedbackApi = {
  feedbackThreads: async (organizationId: string, limit = 25, cursor?: string): Promise<TeacherFeedbackListPage> => {
    const result = await request<unknown>(pagePath(organizationId, undefined, limit, cursor));
    return parseList(data(result));
  },
  feedbackThread: async (organizationId: string, threadId: string, limit = 25, cursor?: string): Promise<TeacherFeedbackThreadPage> => {
    const result = await request<unknown>(pagePath(organizationId, threadId, limit, cursor));
    const page = parseThread(data(result));
    if (page.thread_id !== threadId || page.organization_id !== organizationId) throw invalidResponse("Không đọc được nội dung phản hồi.");
    return page;
  },
  replyFeedback: async (organizationId: string, threadId: string, body: string, revision: number, idempotencyKey: string): Promise<{ thread_id: string; revision: number }> => {
    if (!Number.isInteger(revision) || revision < 1 || !body.trim() || body.length > 2000) {
      throw new BackendApiError("Nội dung phản hồi không hợp lệ.", "INVALID_REQUEST", 400);
    }
    const value = await write<unknown>(
      `${pagePath(organizationId, threadId, 25).split("?")[0]}/replies`,
      "POST",
      idempotencyKey,
      { body },
      { "If-Match": `"${revision}"` },
    );
    return parseReply(value, threadId, revision);
  },
};
