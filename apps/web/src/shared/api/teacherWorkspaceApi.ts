import { BackendApiError } from "./backendApi";
import { data, enc, request } from "./teacherHttp";
import type { Occurrence, OccurrenceState } from "./teacherOccurrenceApi";

export interface TeacherActivity {
  lesson_id: string;
  version_id: string;
  version_no: number;
  content_sha256: string;
  lesson_title: string;
  lesson_topic: string | null;
  lesson_activity_id: string;
  activity_order: number;
  title: string;
  objective: string | null;
  activity_kind: "outdoor" | "indoor" | "mixed";
  materials_text: string | null;
  preparation_text: string | null;
  instructions_text: string | null;
  observation_notes: string | null;
  safety_notes: string | null;
}

export interface TeacherActivityPage { contract: "TeacherActivityPageV1"; items: TeacherActivity[]; next_cursor: string | null }
export interface TeacherOccurrencePage { contract: "LessonOccurrencePageV1"; items: Occurrence[]; next_cursor: string | null }
export interface TeacherAccountProfile { contract: "TeacherProfileV1"; account_ref: string; display_name: string | null; email: string | null }
export interface TeacherPortfolioItem { observation_id: string; session_id: string; kind: "observation" | "reflection" | "assessment"; content: Record<string, unknown>; created_at: string }
export interface TeacherPortfolioPage { contract: "Be1PortfolioPageV1"; child_id: string; items: TeacherPortfolioItem[]; next_cursor: string | null }

const record = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object" && !Array.isArray(value));
const string = (value: unknown): value is string => typeof value === "string";
const nullableString = (value: unknown): value is string | null => value === null || string(value);
const hash = (value: unknown): value is string => string(value) && /^[a-f0-9]{64}$/i.test(value);
const cursor = (value: unknown): value is string | null => value === null || string(value);

function isActivity(value: unknown): value is TeacherActivity {
  return record(value) && string(value.lesson_id) && string(value.version_id) && Number.isInteger(value.version_no)
    && hash(value.content_sha256) && string(value.lesson_title) && nullableString(value.lesson_topic)
    && string(value.lesson_activity_id) && Number.isInteger(value.activity_order) && string(value.title)
    && nullableString(value.objective) && ["outdoor", "indoor", "mixed"].includes(String(value.activity_kind))
    && nullableString(value.materials_text) && nullableString(value.preparation_text)
    && nullableString(value.instructions_text) && nullableString(value.observation_notes) && nullableString(value.safety_notes);
}

function isOccurrence(value: unknown): value is Occurrence {
  if (!record(value) || value.contract !== "LessonOccurrenceV1" || !string(value.occurrence_id) || !string(value.class_id)
    || !string(value.title) || !nullableString(value.scheduled_date)
    || !["DRAFT", "DOCUMENT_REVIEW", "PLAN_REVIEW", "APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED", "ARCHIVED"].includes(String(value.state))
    || !Number.isInteger(value.revision) || !string(value.responsible_teacher_ref) || !string(value.created_at)
    || !record(value.sample_video) || !["AVAILABLE", "CLAIMED"].includes(String(value.sample_video.slot_state))
    || !nullableString(value.sample_video.claimed_at) || !nullableString(value.sample_video.run_ref)) return false;
  if (value.lesson_version_ref !== null && (!record(value.lesson_version_ref) || !string(value.lesson_version_ref.lesson_id)
    || !string(value.lesson_version_ref.version_id) || !hash(value.lesson_version_ref.content_sha256))) return false;
  if (value.approved_plan !== null && (!record(value.approved_plan) || !Number.isInteger(value.approved_plan.revision_no)
    || !hash(value.approved_plan.plan_hash) || !string(value.approved_plan.approved_at))) return false;
  return (value.lesson_version_no === null || Number.isInteger(value.lesson_version_no));
}

function requirePage<T>(value: unknown, contract: string, guard: (item: unknown) => item is T): { items: T[]; next_cursor: string | null } {
  if (!record(value) || value.contract !== contract || !Array.isArray(value.items) || !value.items.every(guard) || !cursor(value.next_cursor)) {
    throw new BackendApiError("Dịch vụ trả về danh sách không hợp lệ.", "INVALID_RESPONSE", 502);
  }
  return { items: value.items, next_cursor: value.next_cursor };
}

function pageQuery(limit = 25, nextCursor?: string): string {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new BackendApiError("Số mục phải từ 1 đến 100.", "INVALID_REQUEST", 400);
  const query = new URLSearchParams({ limit: String(limit) });
  if (nextCursor) query.set("cursor", nextCursor);
  return `?${query.toString()}`;
}

function isProfile(value: unknown): value is TeacherAccountProfile {
  return record(value) && value.contract === "TeacherProfileV1" && string(value.account_ref)
    && nullableString(value.display_name) && nullableString(value.email);
}

function isPortfolioItem(value: unknown): value is TeacherPortfolioItem {
  return record(value) && string(value.observation_id) && string(value.session_id)
    && ["observation", "reflection", "assessment"].includes(String(value.kind))
    && record(value.content) && string(value.created_at);
}

export const teacherWorkspaceApi = {
  activities: async (organizationId: string, options: { limit?: number; cursor?: string } = {}): Promise<TeacherActivityPage> => {
    const query = pageQuery(options.limit ?? 25, options.cursor);
    const value = data(await request<unknown>(`/api/lesson-library/v1/organizations/${enc(organizationId)}/activities${query}`));
    return { contract: "TeacherActivityPageV1", ...requirePage(value, "TeacherActivityPageV1", isActivity) };
  },

  history: async (organizationId: string, options: { state?: OccurrenceState; limit?: number; cursor?: string } = {}): Promise<TeacherOccurrencePage> => {
    const allowed: OccurrenceState[] = ["DRAFT", "DOCUMENT_REVIEW", "PLAN_REVIEW", "APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED", "ARCHIVED"];
    if (options.state && !allowed.includes(options.state)) throw new BackendApiError("Bộ lọc trạng thái không hợp lệ.", "INVALID_REQUEST", 400);
    const query = new URLSearchParams({ limit: String(options.limit ?? 25) });
    if (!Number.isInteger(options.limit ?? 25) || (options.limit ?? 25) < 1 || (options.limit ?? 25) > 100) throw new BackendApiError("Số mục phải từ 1 đến 100.", "INVALID_REQUEST", 400);
    if (options.state) query.set("state", options.state);
    if (options.cursor) query.set("cursor", options.cursor);
    const value = data(await request<unknown>(`/api/teacher/v1/organizations/${enc(organizationId)}/history?${query.toString()}`));
    return { contract: "LessonOccurrencePageV1", ...requirePage(value, "LessonOccurrencePageV1", isOccurrence) };
  },

  profile: async (): Promise<TeacherAccountProfile> => {
    const value = data(await request<unknown>("/api/teacher/v1/me/profile"));
    if (!isProfile(value)) throw new BackendApiError("Dịch vụ trả về hồ sơ không hợp lệ.", "INVALID_RESPONSE", 502);
    return value;
  },

  portfolio: async (organizationId: string, classId: string, childId: string, options: { limit?: number; cursor?: string } = {}): Promise<TeacherPortfolioPage> => {
    const query = pageQuery(options.limit ?? 25, options.cursor);
    const path = `/api/be1/v1/organizations/${enc(organizationId)}/classes/${enc(classId)}/profiles/${enc(childId)}/portfolio${query}`;
    const value = data(await request<unknown>(path));
    if (!record(value) || value.contract !== "Be1PortfolioPageV1" || value.child_id !== childId
      || !Array.isArray(value.items) || !value.items.every(isPortfolioItem) || !cursor(value.next_cursor)) {
      throw new BackendApiError("Dịch vụ trả về hồ sơ nổi bật không hợp lệ.", "INVALID_RESPONSE", 502);
    }
    return value as unknown as TeacherPortfolioPage;
  },
};
