import { CURSOR_PAGE_LIMIT, collectCursorPages, pageQuery } from "../../../../shared/api/cursorPages";
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

export type Be1ManagerConsentState = "pending" | "revoked";

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
const MANAGER_CONSENT_STATES: Be1ManagerConsentState[] = ["pending", "revoked"];
const DATA_REQUEST_TYPES: Be1DataRequestType[] = ["export", "delete"];
const DATA_REQUEST_STATES: Be1DataRequestState[] = ["requested", "running", "awaiting_external_purge", "completed", "exception"];
const visibleAscii = /^[\x21-\x7E]{1,128}$/;
const parentPrincipalRefPattern = /^[A-Za-z0-9._:-]{1,256}$/;

function invalidManagerResponse(message: string) {
  return new AdminBe1Error(message, 502, "INVALID_RESPONSE");
}

function managerConsentPage(value: unknown): { contract: "Be1ConsentListManagerV1"; items: Be1ManagerConsentStatus[]; next_cursor: string | null } {
  if (!value || typeof value !== "object") throw invalidManagerResponse("BE1 trả trạng thái consent không hợp lệ.");
  const page = value as Record<string, unknown>;
  if (page.contract !== "Be1ConsentListManagerV1" || !Array.isArray(page.items)
    || !(page.next_cursor === null || typeof page.next_cursor === "string")) {
    throw invalidManagerResponse("BE1 trả trạng thái consent không hợp lệ.");
  }
  const items: Be1ManagerConsentStatus[] = [];
  for (const value of page.items) {
    if (!value || typeof value !== "object") throw invalidManagerResponse("BE1 trả trạng thái consent không hợp lệ.");
    const item = value as Record<string, unknown>;
    if (typeof item.consent_id !== "string" || !item.consent_id || !MANAGER_CONSENT_STATES.includes(item.state as Be1ManagerConsentState) || item.effective !== false) {
      throw invalidManagerResponse("BE1 trả trạng thái consent không hợp lệ.");
    }
    items.push({ consent_id: item.consent_id, state: item.state as Be1ManagerConsentState, effective: false });
  }
  return { contract: "Be1ConsentListManagerV1", items, next_cursor: page.next_cursor };
}

function consentRevocation(value: unknown, consentId: string): Be1ConsentRevocation {
  if (!value || typeof value !== "object") throw invalidManagerResponse("BE1 trả kết quả thu hồi không hợp lệ.");
  const item = value as Record<string, unknown>;
  if (item.contract !== "Be1ConsentV1" || item.consent_id !== consentId || item.state !== "revoked" || item.effective !== false) {
    throw invalidManagerResponse("BE1 trả kết quả thu hồi không hợp lệ.");
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
  if (!value || typeof value !== "object") throw invalidManagerResponse("BE1 trả kết quả yêu cầu dữ liệu không hợp lệ.");
  const item = value as Record<string, unknown>;
  if (item.contract !== "Be1DataRequestV1" || typeof item.request_id !== "string" || !item.request_id
    || item.state !== "requested" || item.completion_claimed !== false) {
    throw invalidManagerResponse("BE1 trả kết quả yêu cầu dữ liệu không hợp lệ.");
  }
  return { contract: "Be1DataRequestV1", request_id: item.request_id, state: "requested", completion_claimed: false };
}

function dataRequest(value: unknown, requestId: string): Be1DataRequest {
  if (!value || typeof value !== "object") throw invalidManagerResponse("BE1 trả trạng thái yêu cầu dữ liệu không hợp lệ.");
  const item = value as Record<string, unknown>;
  if (item.contract !== "Be1DataRequestV1" || item.request_id !== requestId
    || !DATA_REQUEST_TYPES.includes(item.request_type as Be1DataRequestType)
    || typeof item.target_ref !== "string" || item.target_ref.length < 1 || item.target_ref.length > 256
    || !DATA_REQUEST_STATES.includes(item.state as Be1DataRequestState)
    || !Number.isInteger(item.unresolved_items) || Number(item.unresolved_items) < 0
    || typeof item.completion_claimed !== "boolean") {
    throw invalidManagerResponse("BE1 trả trạng thái yêu cầu dữ liệu không hợp lệ.");
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
  if (status === 409 && code === "INVITATION_EXISTS") return "Phụ huynh này đã được mời hoặc đang là thành viên.";
  if (status === 409 && code === "INVALID_TRANSITION") return "Nhóm đã lưu trữ; không thể mời thành viên.";
  if (status === 404 || code === "RESOURCE_NOT_FOUND") return "Không tìm thấy nhóm hoặc membership yêu cầu.";
  if (code === "STALE_REVISION") return "Danh sách đã thay đổi. Hãy tải lại số lượng và thử lại.";
  if (code === "INVALID_STATE_TRANSITION") return "Membership đã thay đổi trạng thái. Hãy làm mới danh sách.";
  if (code === "INVALID_IDEMPOTENCY_KEY") return "Khóa yêu cầu không hợp lệ. Hãy thử lại thao tác.";
  if (code === "PRECONDITION_REQUIRED") return "Không thể thu hồi membership lúc này. Hãy làm mới danh sách.";
  if (status === 503 || code === "PROVIDER_UNAVAILABLE") return "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  if (status === 401) return "Phiên đăng nhập chưa sẵn sàng. Hãy đăng nhập lại.";
  if (status === 403) return "Tài khoản không có quyền thực hiện thao tác này.";
  if (status === 400 || status === 422 || code === "INVALID_REQUEST") return "Mã tài khoản phụ huynh chưa hợp lệ. Hãy kiểm tra và thử lại.";
  if (code === "INVALID_RESPONSE") return "Không thể xác nhận kết quả lời mời. Hãy làm mới danh sách.";
  return "Không thể tải hoặc cập nhật membership lúc này.";
}

function safeMembershipError(cause: unknown) {
  if (cause instanceof Error && cause.name === "AbortError") return cause;
  const source = cause instanceof AdminBe1Error
    ? cause
    : new AdminBe1Error("Dịch vụ tạm thời chưa sẵn sàng.", 0, "NETWORK_ERROR", undefined, true);
  return new AdminBe1Error(membershipErrorMessage(source.status, source.code), source.status, source.code, source.requestId, source.retryable);
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

export interface FeedbackSummary { thread_id: string; lesson_id: string; version_id: string; revision: number; created_at: string }
export interface FeedbackMessage { message_id: string; body: string; from_you: boolean; created_at: string }
export interface FeedbackPage<T> { items: T[]; next_cursor: string | null }
export interface FeedbackThread extends FeedbackPage<FeedbackMessage> { thread_id: string; revision: number }

function feedbackPath(threadId?: string, cursor?: string) {
  const base = lessonLibraryOrganizationPath() + "/feedback" + (threadId === undefined ? "" : "/" + encodeURIComponent(threadId));
  return base + (cursor ? "?cursor=" + encodeURIComponent(cursor) : "");
}

function validPage(value: unknown, id: string): value is FeedbackPage<Record<string, unknown>> {
  if (!value || typeof value !== "object") return false;
  const page = value as Record<string, unknown>;
  return Array.isArray(page.items) && (page.next_cursor === null || typeof page.next_cursor === "string") && page.items.every((item: unknown) => !!item && typeof item === "object" && typeof (item as Record<string, unknown>)[id] === "string");
}

export const managerBusinessService = {
  feedbackThreads: async (cursor?: string, signal?: AbortSignal): Promise<FeedbackPage<FeedbackSummary>> => {
    const value: unknown = await adminApiRequest(feedbackPath(undefined, cursor), withSignal(signal));
    if (!validPage(value, "thread_id") || !value.items.every((item) => typeof item.lesson_id === "string" && typeof item.version_id === "string" && typeof item.created_at === "string" && typeof item.revision === "number")) throw new Error("Không thể đọc danh sách phản hồi.");
    return value as unknown as FeedbackPage<FeedbackSummary>;
  },
  feedbackThread: async (threadId: string, cursor?: string, signal?: AbortSignal): Promise<FeedbackThread> => {
    const value: unknown = await adminApiRequest(feedbackPath(threadId, cursor), withSignal(signal));
    if (!validPage(value, "message_id") || typeof (value as unknown as FeedbackThread).thread_id !== "string" || typeof (value as unknown as FeedbackThread).revision !== "number" || !value.items.every((item) => typeof item.body === "string" && typeof item.from_you === "boolean" && typeof item.created_at === "string")) throw new Error("Không thể đọc phản hồi.");
    return value as unknown as FeedbackThread;
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
      throw new Error("BE1 trả roster không đúng contract tóm tắt cho School Manager.");
    }
    return { contract: "Be1ClassRosterSummaryV1", class_id: String(body.class_id ?? classId), active_profile_count: count };
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
      throw safeMembershipError(cause);
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
