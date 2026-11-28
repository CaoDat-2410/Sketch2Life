import { CURSOR_PAGE_LIMIT, collectCursorPages, pageQuery } from "../../../../shared/api/cursorPages";
import { feedbackAuthorRole, feedbackDisplayName, type FeedbackAuthorRole } from "../../../../shared/api/feedbackLabels";
import { AdminBe1Error, adminApiRequest, adminBe1Request, adminOrganizationId } from "./be1Client";

export interface Be1Organization {
  contract: "Be1OrganizationV1";
  organization_id: string;
  display_name: string;
}

/** T-7a (SRS l.2586): the School Manager reads a count of active profiles, never profile contents. */
export interface Be1ClassRosterSummary {
  contract: "Be1ClassRosterSummaryV1";
  class_id: string;
  active_profile_count: number;
}

/** Opaque reference only; the School Manager never receives the referenced profile contents. */
export interface Be1ClassProfileRef {
  child_id: string;
}

interface Be1ClassProfileRefPage {
  contract: "Be1ClassProfileRefListV1";
  class_id: string;
  items: Be1ClassProfileRef[];
  next_cursor: string | null;
}

export interface Be1ProfileMoveResult {
  contract: "Be1ProfileMoveV1";
  child_id: string;
  from_class_id: string;
  to_class_id: string;
  enrollment_id: string;
  from_class_revision: number;
  to_class_revision: number;
}

export type Be1ManagerConsentState = "pending" | "revoked" | "unknown";

/** Manager consent rows deliberately contain no child reference or purpose. */
export interface Be1ManagerConsentStatus {
  consent_id: string;
  state: Be1ManagerConsentState;
  effective: false;
}

export interface Be1ConsentRevocation {
  contract: "Be1ConsentV1";
  consent_id: string;
  state: "revoked";
  effective: false;
}

export type Be1DataRequestType = "export" | "delete";
export type Be1DataRequestState = "requested" | "running" | "awaiting_external_purge" | "completed" | "exception";

export interface Be1DataRequestCreated {
  contract: "Be1DataRequestV1";
  request_id: string;
  state: "requested";
  completion_claimed: false;
}

export interface Be1DataRequest {
  contract: "Be1DataRequestV1";
  request_id: string;
  request_type: Be1DataRequestType;
  target_ref: string;
  state: Be1DataRequestState;
  unresolved_items: number;
  completion_claimed: boolean;
}

export interface ParentGroup {
  contract: "ParentGroupV1";
  parent_group_id: string;
  organization_id: string;
  display_name: string;
  state: "ACTIVE" | "ARCHIVED";
  created_at: string;
}

export interface ParentGroupPage {
  contract: "ParentGroupPageV1";
  items: ParentGroup[];
  next_cursor: string | null;
}

export type ParentGroupMemberState = "INVITED" | "ACCEPTED" | "DECLINED" | "REVOKED" | "EXPIRED";
export type ParentGroupMemberFilter = ParentGroupMemberState;

export interface ParentGroupMember {
  membership_id: string;
  parent_group_id: string;
  state: ParentGroupMemberState;
  invited_at: string;
  expires_at: string | null;
  accepted_at: string | null;
  revision: number;
}

export interface ParentGroupMemberCounts {
  invited: number;
  accepted: number;
  declined: number;
  revoked: number;
  expired: number;
  total: number;
}

export interface ParentGroupMemberPage {
  contract: string;
  items: ParentGroupMember[];
  counts: ParentGroupMemberCounts;
  next_cursor: string | null;
}

export interface ParentGroupInvitation {
  contract: string;
  membership_id: string;
  parent_group_id: string;
  state: "INVITED";
  invited_at: string;
  expires_at: string;
  accepted_at: null;
  revision: number;
}

const organizationPath = () =>
  "/organizations/" + encodeURIComponent(adminOrganizationId());

const lessonLibraryOrganizationPath = () =>
  "/lesson-library/v1" + organizationPath();

const withSignal = (signal?: AbortSignal): RequestInit =>
  signal ? { signal } : {};

const MEMBER_STATES: ParentGroupMemberState[] = ["INVITED", "ACCEPTED", "DECLINED", "REVOKED", "EXPIRED"];
const MANAGER_CONSENT_STATES: Exclude<Be1ManagerConsentState, "unknown">[] = ["pending", "revoked"];
const DATA_REQUEST_TYPES: Be1DataRequestType[] = ["export", "delete"];
const DATA_REQUEST_STATES: Be1DataRequestState[] = ["requested", "running", "awaiting_external_purge", "completed", "exception"];
const visibleAscii = /^[\x21-\x7E]{1,128}$/;
const parentPrincipalRefPattern = /^[A-Za-z0-9._:-]{1,256}$/;

function invalidManagerResponse(message: string) {
  return new AdminBe1Error(message, 502, "INVALID_RESPONSE");
}

function hasExactKeys(value: Record<string, unknown>, expected: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const sortedExpected = [...expected].sort();
  return actual.length === sortedExpected.length
    && actual.every((key, index) => key === sortedExpected[index]);
}

function profileRefPage(value: unknown, classId: string): Be1ClassProfileRefPage {
  const error = "Hệ thống trả tham chiếu hồ sơ không hợp lệ.";
  if (!value || typeof value !== "object") throw invalidManagerResponse(error);
  const page = value as Record<string, unknown>;
  if (!hasExactKeys(page, ["contract", "class_id", "items", "next_cursor"])
    || page.contract !== "Be1ClassProfileRefListV1" || page.class_id !== classId
    || !Array.isArray(page.items)
    || !(page.next_cursor === null || typeof page.next_cursor === "string")) {
    throw invalidManagerResponse(error);
  }
  const items: Be1ClassProfileRef[] = [];
  for (const value of page.items) {
    if (!value || typeof value !== "object") throw invalidManagerResponse(error);
    const item = value as Record<string, unknown>;
    if (!hasExactKeys(item, ["child_id"]) || typeof item.child_id !== "string" || !item.child_id.trim()) {
      throw invalidManagerResponse(error);
    }
    items.push({ child_id: item.child_id });
  }
  return {
    contract: "Be1ClassProfileRefListV1",
    class_id: classId,
    items,
    next_cursor: page.next_cursor,
  };
}

function profileMoveResult(
  value: unknown,
  expected: { childId: string; sourceClassId: string; targetClassId: string },
): Be1ProfileMoveResult {
  const error = "Hệ thống trả kết quả chuyển hồ sơ không hợp lệ.";
  if (!value || typeof value !== "object") throw invalidManagerResponse(error);
  const result = value as Record<string, unknown>;
  if (!hasExactKeys(result, [
    "contract", "child_id", "from_class_id", "to_class_id", "enrollment_id",
    "from_class_revision", "to_class_revision",
  ])
    || result.contract !== "Be1ProfileMoveV1"
    || result.child_id !== expected.childId
    || result.from_class_id !== expected.sourceClassId
    || result.to_class_id !== expected.targetClassId
    || typeof result.enrollment_id !== "string" || !result.enrollment_id
    || typeof result.from_class_revision !== "number" || !Number.isInteger(result.from_class_revision)
    || result.from_class_revision < 1
    || typeof result.to_class_revision !== "number" || !Number.isInteger(result.to_class_revision)
    || result.to_class_revision < 1) {
    throw invalidManagerResponse(error);
  }
  return {
    contract: "Be1ProfileMoveV1",
    child_id: result.child_id,
    from_class_id: result.from_class_id,
    to_class_id: result.to_class_id,
    enrollment_id: result.enrollment_id,
    from_class_revision: result.from_class_revision,
    to_class_revision: result.to_class_revision,
  };
}

function managerConsentPage(value: unknown): { contract: "Be1ConsentListManagerV1"; items: Be1ManagerConsentStatus[]; next_cursor: string | null } {
  if (!value || typeof value !== "object") throw invalidManagerResponse("Hệ thống trả trạng thái đồng ý không hợp lệ.");
  const page = value as Record<string, unknown>;
  if (page.contract !== "Be1ConsentListManagerV1" || !Array.isArray(page.items)
    || !(page.next_cursor === null || typeof page.next_cursor === "string")) {
    throw invalidManagerResponse("Hệ thống trả trạng thái đồng ý không hợp lệ.");
  }
  const items: Be1ManagerConsentStatus[] = [];
  for (const value of page.items) {
    if (!value || typeof value !== "object") throw invalidManagerResponse("Hệ thống trả trạng thái đồng ý không hợp lệ.");
    const item = value as Record<string, unknown>;
    if (typeof item.consent_id !== "string" || !item.consent_id || typeof item.state !== "string" || item.effective !== false) {
      throw invalidManagerResponse("Hệ thống trả trạng thái đồng ý không hợp lệ.");
    }
    const state = MANAGER_CONSENT_STATES.includes(item.state as Exclude<Be1ManagerConsentState, "unknown">)
      ? item.state as Exclude<Be1ManagerConsentState, "unknown">
      : "unknown";
    items.push({ consent_id: item.consent_id, state, effective: false });
  }
  return { contract: "Be1ConsentListManagerV1", items, next_cursor: page.next_cursor };
}

function consentRevocation(value: unknown, consentId: string): Be1ConsentRevocation {
  if (!value || typeof value !== "object") throw invalidManagerResponse("Hệ thống trả kết quả thu hồi không hợp lệ.");
  const item = value as Record<string, unknown>;
  if (item.contract !== "Be1ConsentV1" || item.consent_id !== consentId || item.state !== "revoked" || item.effective !== false) {
    throw invalidManagerResponse("Hệ thống trả kết quả thu hồi không hợp lệ.");
  }
  return { contract: "Be1ConsentV1", consent_id: consentId, state: "revoked", effective: false };
}

function safeConsentError(cause: unknown): unknown {
  if (cause instanceof Error && cause.name === "AbortError") return cause;
  const source = cause instanceof AdminBe1Error
    ? cause
    : new AdminBe1Error("Chưa rõ kết quả, hãy tải lại.", 0, "NETWORK_ERROR", undefined, true);
  const message = source.status === 404 ? "Không tìm thấy bản ghi"
    : source.status === 403 ? "Không có quyền"
    : source.status === 0 ? "Chưa rõ kết quả, hãy tải lại"
    : "Không thể thu hồi bản ghi. Hãy tải lại danh sách.";
  return new AdminBe1Error(message, source.status, source.code, source.requestId, source.retryable);
}

function safeDataRequestError(cause: unknown, fallback: string): unknown {
  if (cause instanceof Error && cause.name === "AbortError") return cause;
  const source = cause instanceof AdminBe1Error
    ? cause
    : new AdminBe1Error("Chưa rõ kết quả. Hãy kiểm tra trạng thái trước khi gửi lại.", 0, "NETWORK_ERROR", undefined, true);
  const message = source.status === 404 ? "Không tìm thấy yêu cầu hoặc bạn không có quyền truy cập."
    : source.status === 403 ? "Không có quyền thực hiện thao tác này."
    : source.status === 0 ? fallback
    : source.status === 400 || source.status === 422 ? "Thông tin yêu cầu chưa hợp lệ. Hãy kiểm tra lại."
    : "Không thể xử lý yêu cầu lúc này.";
  return new AdminBe1Error(message, source.status, source.code, source.requestId, source.retryable);
}

function createdDataRequest(value: unknown): Be1DataRequestCreated {
  if (!value || typeof value !== "object") throw invalidManagerResponse("Hệ thống trả kết quả yêu cầu dữ liệu không hợp lệ.");
  const item = value as Record<string, unknown>;
  if (item.contract !== "Be1DataRequestV1" || typeof item.request_id !== "string" || !item.request_id
    || item.state !== "requested" || item.completion_claimed !== false) {
    throw invalidManagerResponse("Hệ thống trả kết quả yêu cầu dữ liệu không hợp lệ.");
  }
  return { contract: "Be1DataRequestV1", request_id: item.request_id, state: "requested", completion_claimed: false };
}

function dataRequest(value: unknown, requestId: string): Be1DataRequest {
  if (!value || typeof value !== "object") throw invalidManagerResponse("Hệ thống trả trạng thái yêu cầu dữ liệu không hợp lệ.");
  const item = value as Record<string, unknown>;
  if (item.contract !== "Be1DataRequestV1" || item.request_id !== requestId
    || !DATA_REQUEST_TYPES.includes(item.request_type as Be1DataRequestType)
    || typeof item.target_ref !== "string" || item.target_ref.length < 1 || item.target_ref.length > 256
    || !DATA_REQUEST_STATES.includes(item.state as Be1DataRequestState)
    || !Number.isInteger(item.unresolved_items) || Number(item.unresolved_items) < 0
    || typeof item.completion_claimed !== "boolean") {
    throw invalidManagerResponse("Hệ thống trả trạng thái yêu cầu dữ liệu không hợp lệ.");
  }
  return {
    contract: "Be1DataRequestV1",
    request_id: requestId,
    request_type: item.request_type as Be1DataRequestType,
    target_ref: item.target_ref,
    state: item.state as Be1DataRequestState,
    unresolved_items: Number(item.unresolved_items),
    completion_claimed: item.completion_claimed,
  };
}

function membershipErrorMessage(status: number, code: string) {
  if (status === 404 || code === "RESOURCE_NOT_FOUND") return "Không tìm thấy nhóm hoặc membership yêu cầu.";
  if (code === "STALE_REVISION") return "Danh sách đã thay đổi. Hãy tải lại số lượng và thử lại.";
  if (code === "INVALID_STATE_TRANSITION") return "Membership đã thay đổi trạng thái. Hãy làm mới danh sách.";
  if (code === "INVALID_IDEMPOTENCY_KEY") return "Khóa yêu cầu không hợp lệ. Hãy thử lại thao tác.";
  if (code === "PRECONDITION_REQUIRED") return "Không thể thu hồi membership lúc này. Hãy làm mới danh sách.";
  if (status === 503 || code === "PROVIDER_UNAVAILABLE") return "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  if (status === 401) return "Phiên đăng nhập chưa sẵn sàng. Hãy đăng nhập lại.";
  if (status === 403) return "Tài khoản không có quyền thực hiện thao tác này.";
  if (status === 400 || code === "INVALID_REQUEST") return "Yêu cầu chưa hợp lệ. Hãy kiểm tra bộ lọc rồi thử lại.";
  return "Không thể tải hoặc cập nhật membership lúc này.";
}

function safeMembershipError(cause: unknown) {
  if (cause instanceof Error && cause.name === "AbortError") return cause;
  const source = cause instanceof AdminBe1Error
    ? cause
    : new AdminBe1Error("Dịch vụ tạm thời chưa sẵn sàng.", 0, "NETWORK_ERROR", undefined, true);
  return new AdminBe1Error(membershipErrorMessage(source.status, source.code), source.status, source.code, source.requestId, source.retryable);
}

function safeInvitationError(cause: unknown) {
  if (cause instanceof Error && cause.name === "AbortError") return cause;
  const source = cause instanceof AdminBe1Error
    ? cause
    : new AdminBe1Error("Dịch vụ tạm thời chưa sẵn sàng.", 0, "NETWORK_ERROR", undefined, true);
  let message: string | undefined;
  if (source.status === 409 && source.code === "INVITATION_EXISTS") message = "Phụ huynh này đã được mời hoặc đang là thành viên.";
  else if (source.status === 409 && source.code === "INVALID_TRANSITION") message = "Nhóm đã lưu trữ; không thể mời thành viên.";
  else if (source.status === 404 && source.code === "PARENT_NOT_FOUND") message = "Không tìm thấy phụ huynh với mã này";
  else if (source.status === 400 || source.status === 422 || source.code === "INVALID_REQUEST") message = "Mã tài khoản phụ huynh chưa hợp lệ. Hãy kiểm tra và thử lại.";
  else if (source.code === "INVALID_RESPONSE") message = "Không thể xác nhận kết quả lời mời. Hãy làm mới danh sách.";
  if (message === undefined) return safeMembershipError(cause);
  return new AdminBe1Error(message, source.status, source.code, source.requestId, source.retryable);
}

function safeCounts(value: unknown): value is ParentGroupMemberCounts {
  if (!value || typeof value !== "object") return false;
  const counts = value as Record<string, unknown>;
  return ["invited", "accepted", "declined", "revoked", "expired", "total"].every((key) => Number.isInteger(counts[key]) && Number(counts[key]) >= 0);
}

function safeMember(value: unknown): ParentGroupMember | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Record<string, unknown>;
  if (typeof item.membership_id !== "string" || typeof item.parent_group_id !== "string" || !MEMBER_STATES.includes(item.state as ParentGroupMemberState)
    || typeof item.invited_at !== "string" || !(item.expires_at === null || typeof item.expires_at === "string")
    || !(item.accepted_at === null || typeof item.accepted_at === "string") || !Number.isInteger(item.revision) || Number(item.revision) < 1) return null;
  // Explicitly retain only the opaque membership fields; never pass through identity or child fields.
  return {
    membership_id: item.membership_id,
    parent_group_id: item.parent_group_id,
    state: item.state as ParentGroupMemberState,
    invited_at: item.invited_at,
    expires_at: item.expires_at as string | null,
    accepted_at: item.accepted_at as string | null,
    revision: Number(item.revision),
  };
}

function memberPage(value: unknown): ParentGroupMemberPage {
  if (!value || typeof value !== "object") throw new Error("Không thể đọc danh sách membership.");
  const page = value as Record<string, unknown>;
  if (typeof page.contract !== "string" || !Array.isArray(page.items) || !safeCounts(page.counts)
    || !(page.next_cursor === null || typeof page.next_cursor === "string")) throw new Error("Không thể đọc danh sách membership.");
  const items = page.items.map(safeMember);
  if (items.some((item) => item === null)) throw new Error("Không thể đọc danh sách membership.");
  const counts = page.counts as ParentGroupMemberCounts;
  return {
    contract: page.contract,
    items: items as ParentGroupMember[],
    counts: {
      invited: counts.invited,
      accepted: counts.accepted,
      declined: counts.declined,
      revoked: counts.revoked,
      expired: counts.expired,
      total: counts.total,
    },
    next_cursor: page.next_cursor,
  };
}

export interface FeedbackSummary {
  thread_id: string;
  lesson_id: string;
  version_id: string;
  lesson_title?: string | null;
  version_no?: number | null;
  revision: number;
  created_at: string;
}
export interface FeedbackMessage {
  message_id: string;
  body: string;
  from_you: boolean;
  author_role?: FeedbackAuthorRole;
  author_display_name?: string | null;
  created_at: string;
}
export interface FeedbackPage<T> { items: T[]; next_cursor: string | null }
export interface FeedbackThread extends FeedbackPage<FeedbackMessage> {
  thread_id: string;
  organization_id?: string;
  lesson_id?: string;
  version_id?: string;
  lesson_title?: string | null;
  version_no?: number | null;
  revision: number;
}

function feedbackPath(threadId?: string, cursor?: string) {
  const base = lessonLibraryOrganizationPath() + "/feedback" + (threadId === undefined ? "" : "/" + encodeURIComponent(threadId));
  return base + (cursor ? "?cursor=" + encodeURIComponent(cursor) : "");
}

type FeedbackRecord = Record<string, unknown>;
type FeedbackRecordPage = FeedbackPage<FeedbackRecord> & FeedbackRecord;

function isFeedbackRecord(value: unknown): value is FeedbackRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function validPage(value: unknown, id: string): value is FeedbackRecordPage {
  if (!isFeedbackRecord(value)) return false;
  const items = value.items;
  return Array.isArray(items)
    && (value.next_cursor === null || typeof value.next_cursor === "string")
    && items.every((item: unknown) => isFeedbackRecord(item) && typeof item[id] === "string");
}

function isOptionalNullableString(value: unknown): value is string | null | undefined {
  return value === undefined || value === null || typeof value === "string";
}

function isOptionalVersionNo(value: unknown): value is number | null | undefined {
  return value === undefined || value === null || (typeof value === "number" && Number.isInteger(value) && value >= 1);
}

function isFeedbackAuthorRole(value: unknown): value is FeedbackAuthorRole {
  return value === "parent" || value === "teacher" || value === "school_manager" || value === "platform_admin" || value === "other";
}

function readFeedbackSummary(item: FeedbackRecord): FeedbackSummary {
  const threadId = item.thread_id;
  const lessonId = item.lesson_id;
  const versionId = item.version_id;
  const lessonTitle = item.lesson_title;
  const versionNo = item.version_no;
  const revision = item.revision;
  const createdAt = item.created_at;
  if (typeof threadId !== "string" || typeof lessonId !== "string" || typeof versionId !== "string"
    || typeof revision !== "number" || typeof createdAt !== "string"
    || !isOptionalNullableString(lessonTitle) || !isOptionalVersionNo(versionNo)) throw new Error("Không thể đọc danh sách phản hồi.");
  return {
    thread_id: threadId,
    lesson_id: lessonId,
    version_id: versionId,
    lesson_title: lessonTitle ?? null,
    version_no: versionNo ?? null,
    revision,
    created_at: createdAt,
  };
}

function readFeedbackMessage(item: FeedbackRecord): FeedbackMessage {
  const messageId = item.message_id;
  const body = item.body;
  const fromYou = item.from_you;
  const createdAt = item.created_at;
  const authorRole = item.author_role;
  const authorDisplayName = item.author_display_name;
  if (typeof messageId !== "string" || typeof body !== "string" || typeof fromYou !== "boolean" || typeof createdAt !== "string"
    || (authorRole !== undefined && !isFeedbackAuthorRole(authorRole))
    || !isOptionalNullableString(authorDisplayName)) throw new Error("Không thể đọc phản hồi.");
  return {
    message_id: messageId,
    body,
    from_you: fromYou,
    author_role: feedbackAuthorRole(authorRole),
    author_display_name: feedbackDisplayName(authorDisplayName),
    created_at: createdAt,
  };
}

export const managerBusinessService = {
  feedbackThreads: async (cursor?: string, signal?: AbortSignal): Promise<FeedbackPage<FeedbackSummary>> => {
    const value: unknown = await adminApiRequest(feedbackPath(undefined, cursor), withSignal(signal));
    if (!validPage(value, "thread_id")) throw new Error("Không thể đọc danh sách phản hồi.");
    return { items: value.items.map(readFeedbackSummary), next_cursor: value.next_cursor };
  },
  feedbackThread: async (threadId: string, cursor?: string, signal?: AbortSignal): Promise<FeedbackThread> => {
    const value: unknown = await adminApiRequest(feedbackPath(threadId, cursor), withSignal(signal));
    if (!validPage(value, "message_id") || typeof value.thread_id !== "string" || typeof value.revision !== "number"
      || !isOptionalNullableString(value.lesson_title) || !isOptionalVersionNo(value.version_no)) throw new Error("Không thể đọc phản hồi.");
    return {
      thread_id: value.thread_id,
      ...(typeof value.organization_id === "string" ? { organization_id: value.organization_id } : {}),
      ...(typeof value.lesson_id === "string" ? { lesson_id: value.lesson_id } : {}),
      ...(typeof value.version_id === "string" ? { version_id: value.version_id } : {}),
      lesson_title: typeof value.lesson_title === "string" ? value.lesson_title.trim() || null : null,
      version_no: value.version_no ?? null,
      revision: value.revision,
      items: value.items.map(readFeedbackMessage),
      next_cursor: value.next_cursor,
    };
  },
  replyFeedback: async (threadId: string, body: string, revision: number, idempotencyKey: string): Promise<{ thread_id: string; revision: number }> => {
    const value: unknown = await adminApiRequest(feedbackPath(threadId) + "/replies", { method: "POST", headers: { "If-Match": `"${revision}"`, "Idempotency-Key": idempotencyKey }, body: JSON.stringify({ body }) });
    if (!value || typeof value !== "object" || typeof (value as { thread_id?: unknown }).thread_id !== "string" || typeof (value as { revision?: unknown }).revision !== "number") throw new Error("Không thể đọc kết quả phản hồi.");
    return value as { thread_id: string; revision: number };
  },
  organization: (signal?: AbortSignal) =>
    adminBe1Request<Be1Organization>(organizationPath(), withSignal(signal)),

  /** A09 count summary; any other body (for example a Teacher list with names) is refused, never shown. */
  rosterSummary: async (classId: string, signal?: AbortSignal): Promise<Be1ClassRosterSummary> => {
    const body = await adminBe1Request<Partial<Be1ClassRosterSummary> & { contract?: string }>(
      organizationPath() + "/classes/" + encodeURIComponent(classId) + "/profiles",
      withSignal(signal),
    );
    const count = body.active_profile_count;
    if (body.contract !== "Be1ClassRosterSummaryV1" || typeof count !== "number" || !Number.isInteger(count) || count < 0) {
      throw new Error("Hệ thống trả dữ liệu tóm tắt danh sách lớp không hợp lệ.");
    }
    return { contract: "Be1ClassRosterSummaryV1", class_id: String(body.class_id ?? classId), active_profile_count: count };
  },

  /** Manager roster: read every page and keep exactly the opaque profile reference per item. */
  profileRefs: async (classId: string, signal?: AbortSignal): Promise<Be1ClassProfileRef[]> => {
    const items: Be1ClassProfileRef[] = [];
    const requestedCursors = new Set<string>();
    let cursor: string | undefined;
    while (true) {
      if (cursor !== undefined) {
        if (requestedCursors.has(cursor)) {
          throw invalidManagerResponse("Hệ thống lặp lại trang tham chiếu hồ sơ.");
        }
        requestedCursors.add(cursor);
      }
      const page = profileRefPage(await adminBe1Request<unknown>(
        organizationPath() + "/classes/" + encodeURIComponent(classId) + "/profile-refs"
          + pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor }),
        withSignal(signal),
      ), classId);
      items.push(...page.items);
      if (page.next_cursor === null) return items;
      cursor = page.next_cursor;
    }
  },

  unplacedProfileRefs: async (signal?: AbortSignal): Promise<Be1ClassProfileRef[]> => {
    const items: Be1ClassProfileRef[] = [];
    const seen = new Set<string>();
    let cursor: string | undefined;
    while (true) {
      if (cursor !== undefined) {
        if (seen.has(cursor)) throw invalidManagerResponse("Hệ thống lặp lại trang tham chiếu hồ sơ.");
        seen.add(cursor);
      }
      const value = await adminBe1Request<unknown>(organizationPath() + "/unplaced-profile-refs" + pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor }), withSignal(signal));
      if (!value || typeof value !== "object") throw invalidManagerResponse("Dữ liệu hồ sơ không hợp lệ.");
      const page = value as Record<string, unknown>;
      if (!hasExactKeys(page, ["contract", "items", "next_cursor"]) || page.contract !== "Be1UnplacedProfileRefListV1" || !Array.isArray(page.items) || !(page.next_cursor === null || (typeof page.next_cursor === "string" && page.next_cursor.length > 0))) throw invalidManagerResponse("Dữ liệu hồ sơ không hợp lệ.");
      for (const value of page.items) {
        if (!value || typeof value !== "object") throw invalidManagerResponse("Dữ liệu hồ sơ không hợp lệ.");
        const item = value as Record<string, unknown>;
        if (!hasExactKeys(item, ["child_id"]) || typeof item.child_id !== "string" || !item.child_id.trim()) throw invalidManagerResponse("Dữ liệu hồ sơ không hợp lệ.");
        items.push({ child_id: item.child_id });
      }
      if (page.next_cursor === null) return items;
      cursor = page.next_cursor as string;
    }
  },

  placeProfile: async (classId: string, childId: string, revision: number, idempotencyKey: string): Promise<void> => {
    const value = await adminBe1Request<unknown>("/classes/" + encodeURIComponent(classId) + "/profiles/" + encodeURIComponent(childId) + "/place", { method: "POST", headers: { "If-Match": `"${revision}"`, "Idempotency-Key": idempotencyKey } });
    if (!value || typeof value !== "object") throw invalidManagerResponse("Kết quả xếp lớp không hợp lệ.");
    const result = value as Record<string, unknown>;
    if (!hasExactKeys(result, ["contract", "child_id", "class_id", "enrollment_id", "class_revision"]) || result.contract !== "Be1ProfilePlacementV1" || result.child_id !== childId || result.class_id !== classId || typeof result.enrollment_id !== "string" || !result.enrollment_id.trim() || typeof result.class_revision !== "number" || !Number.isInteger(result.class_revision) || result.class_revision < 1) throw invalidManagerResponse("Kết quả xếp lớp không hợp lệ.");
  },

  /** One move command; caller retains and reuses the same key if the response is lost. */
  moveProfile: async (
    sourceClassId: string,
    childId: string,
    targetClassId: string,
    sourceClassRevision: number,
    targetClassRevision: number,
    idempotencyKey: string,
  ): Promise<Be1ProfileMoveResult> => {
    const value = await adminBe1Request<unknown>(
      "/classes/" + encodeURIComponent(sourceClassId) + "/profiles/" + encodeURIComponent(childId) + "/move",
      {
        method: "POST",
        headers: {
          "If-Match": `"${sourceClassRevision}"`,
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          target_class_id: targetClassId,
          target_class_revision: targetClassRevision,
        }),
      },
    );
    return profileMoveResult(value, { childId, sourceClassId, targetClassId });
  },

  /** A10, every page; only the Manager item fields are kept. */
  consents: async (classId: string, signal?: AbortSignal): Promise<Be1ManagerConsentStatus[]> => {
    const { items } = await collectCursorPages<Be1ManagerConsentStatus, { contract: "Be1ConsentListManagerV1"; items: Be1ManagerConsentStatus[]; next_cursor: string | null }>(async (cursor) =>
      managerConsentPage(await adminBe1Request<unknown>(
        organizationPath() + "/classes/" + encodeURIComponent(classId) + "/consents" + pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor }),
        withSignal(signal),
      )),
    );
    return items;
  },

  /** Manager revoke is naturally idempotent; this route sends no body, query, key, or revision header. */
  revokeConsent: async (classId: string, consentId: string): Promise<Be1ConsentRevocation> => {
    if (!classId.trim() || !consentId.trim()) {
      throw new AdminBe1Error("Không thể xác định bản ghi cần thu hồi.", 400, "INVALID_REQUEST");
    }
    try {
      const value = await adminBe1Request<unknown>(
        organizationPath() + "/classes/" + encodeURIComponent(classId) + "/consents/" + encodeURIComponent(consentId) + "/revoke",
        { method: "POST" },
      );
      return consentRevocation(value, consentId);
    } catch (cause) {
      throw safeConsentError(cause);
    }
  },

  createDataRequest: async (requestType: Be1DataRequestType, targetRef: string): Promise<Be1DataRequestCreated> => {
    const safeTargetRef = targetRef;
    if (!DATA_REQUEST_TYPES.includes(requestType) || safeTargetRef.length < 1 || safeTargetRef.length > 256) {
      throw new AdminBe1Error("Tham chiếu phải có từ 1 đến 256 ký tự.", 422, "INVALID_REQUEST");
    }
    try {
      const value = await adminBe1Request<unknown>(organizationPath() + "/data-requests", {
        method: "POST",
        body: JSON.stringify({ request_type: requestType, target_ref: safeTargetRef }),
      });
      return createdDataRequest(value);
    } catch (cause) {
      throw safeDataRequestError(cause, "Chưa rõ kết quả. Hãy kiểm tra trạng thái trước khi gửi lại.");
    }
  },

  getDataRequest: async (requestId: string, signal?: AbortSignal): Promise<Be1DataRequest> => {
    const safeRequestId = requestId;
    if (!safeRequestId.trim()) throw new AdminBe1Error("Hãy nhập mã yêu cầu.", 400, "INVALID_REQUEST");
    try {
      const value = await adminBe1Request<unknown>(
        organizationPath() + "/data-requests/" + encodeURIComponent(safeRequestId),
        withSignal(signal),
      );
      return dataRequest(value, safeRequestId);
    } catch (cause) {
      throw safeDataRequestError(cause, "Không kết nối được để kiểm tra trạng thái. Hãy thử lại.");
    }
  },

  parentGroups: (cursor?: string, signal?: AbortSignal) => {
    // SRS 21.1: cursor paging with the server default page size (25); no limit is sent.
    const query = new URLSearchParams();
    if (cursor) query.set("cursor", cursor);
    const queryString = query.toString();
    return adminApiRequest<ParentGroupPage>(
      lessonLibraryOrganizationPath() + "/parent-groups" + (queryString ? "?" + queryString : ""),
      withSignal(signal),
    );
  },

  parentGroupMembers: async (
    groupId: string,
    options: { state?: ParentGroupMemberFilter; limit?: number; cursor?: string; signal?: AbortSignal } = {},
  ): Promise<ParentGroupMemberPage> => {
    const limit = options.limit ?? 25;
    if (!groupId.trim() || !Number.isInteger(limit) || limit < 1 || limit > 100 || (options.cursor !== undefined && options.cursor.length > 1024)) {
      throw new AdminBe1Error("Bộ lọc danh sách membership chưa hợp lệ.", 400, "INVALID_REQUEST");
    }
    if (options.state !== undefined && !MEMBER_STATES.includes(options.state)) {
      throw new AdminBe1Error("Trạng thái membership chưa hợp lệ.", 400, "INVALID_REQUEST");
    }
    try {
      const value = await adminApiRequest<unknown>(
        lessonLibraryOrganizationPath() + "/parent-groups/" + encodeURIComponent(groupId) + "/members" + pageQuery({ state: options.state, limit, cursor: options.cursor }),
        { headers: { "Cache-Control": "private, no-store" }, ...withSignal(options.signal) },
      );
      return memberPage(value);
    } catch (cause) {
      throw safeMembershipError(cause);
    }
  },

  revokeParentGroupMember: async (
    groupId: string,
    membershipId: string,
    revision: number,
    idempotencyKey: string,
  ): Promise<ParentGroupMember> => {
    if (!groupId.trim() || !membershipId.trim() || !Number.isInteger(revision) || revision < 1) {
      throw new AdminBe1Error("Thông tin membership chưa hợp lệ. Hãy tải lại danh sách.", 400, "INVALID_REQUEST");
    }
    if (!visibleAscii.test(idempotencyKey)) {
      throw new AdminBe1Error("Khóa yêu cầu không hợp lệ.", 400, "INVALID_IDEMPOTENCY_KEY");
    }
    try {
      const value = await adminApiRequest<unknown>(
        lessonLibraryOrganizationPath() + "/parent-groups/" + encodeURIComponent(groupId) + "/members/" + encodeURIComponent(membershipId),
        { method: "DELETE", headers: { "If-Match": `"${revision}"`, "Idempotency-Key": idempotencyKey } },
      );
      const member = safeMember(value);
      if (!member || member.state !== "REVOKED" || member.revision !== revision + 1) {
        throw new Error("Không thể đọc kết quả thu hồi membership.");
      }
      return member;
    } catch (cause) {
      throw safeMembershipError(cause);
    }
  },

  inviteParentToGroup: async (
    groupId: string,
    parentPrincipalRef: string,
    idempotencyKey: string,
  ): Promise<ParentGroupInvitation> => {
    const trimmedPrincipalRef = parentPrincipalRef.trim();
    if (!groupId.trim()) {
      throw new AdminBe1Error("Không thể mời vào nhóm này.", 400, "INVALID_REQUEST");
    }
    if (!parentPrincipalRefPattern.test(trimmedPrincipalRef)) {
      throw new AdminBe1Error("Mã tài khoản phụ huynh chưa hợp lệ. Hãy kiểm tra và thử lại.", 422, "INVALID_REQUEST");
    }
    if (!visibleAscii.test(idempotencyKey)) {
      throw new AdminBe1Error("Khóa yêu cầu không hợp lệ. Hãy thử lại thao tác.", 400, "INVALID_IDEMPOTENCY_KEY");
    }
    try {
      const value = await adminApiRequest<unknown>(
        lessonLibraryOrganizationPath() + "/parent-groups/" + encodeURIComponent(groupId) + "/invitations",
        {
          method: "POST",
          headers: { "Idempotency-Key": idempotencyKey },
          body: JSON.stringify({
            contract: "InviteParentToGroupRequestV1",
            parent_principal_ref: trimmedPrincipalRef,
          }),
        },
      );
      if (!value || typeof value !== "object") {
        throw new AdminBe1Error("Kết quả lời mời chưa hợp lệ.", 502, "INVALID_RESPONSE");
      }
      const item = value as Record<string, unknown>;
      if (typeof item.contract !== "string" || !item.contract
        || typeof item.membership_id !== "string" || !item.membership_id
        || item.parent_group_id !== groupId || item.state !== "INVITED"
        || typeof item.invited_at !== "string" || !Number.isFinite(Date.parse(item.invited_at))
        || typeof item.expires_at !== "string" || !Number.isFinite(Date.parse(item.expires_at))
        || item.accepted_at !== null || !Number.isInteger(item.revision) || Number(item.revision) < 1) {
        throw new AdminBe1Error("Kết quả lời mời chưa hợp lệ.", 502, "INVALID_RESPONSE");
      }
      return {
        contract: item.contract,
        membership_id: item.membership_id,
        parent_group_id: item.parent_group_id,
        state: "INVITED",
        invited_at: item.invited_at,
        expires_at: item.expires_at,
        accepted_at: null,
        revision: Number(item.revision),
      };
    } catch (cause) {
      throw safeInvitationError(cause);
    }
  },

  createParentGroup: (displayName: string, idempotencyKey: string) =>
    adminApiRequest<ParentGroup>(lessonLibraryOrganizationPath() + "/parent-groups", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        contract: "CreateParentGroupRequestV1",
        display_name: displayName,
      }),
    }),
};
