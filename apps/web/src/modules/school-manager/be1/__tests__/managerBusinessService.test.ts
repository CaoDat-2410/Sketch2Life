import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => {
  class MockAdminBe1Error extends Error {
    readonly status: number;
    readonly code: string;
    readonly requestId?: string;
    readonly retryable: boolean;
    constructor(message: string, status: number, code: string, requestId?: string, retryable = false) {
      super(message);
      this.status = status;
      this.code = code;
      this.requestId = requestId;
      this.retryable = retryable;
    }
  }
  return {
    AdminBe1Error: MockAdminBe1Error,
    adminApiRequest: vi.fn(),
    adminBe1Request: vi.fn(),
    adminOrganizationId: vi.fn(),
  };
});

vi.mock("../services/be1Client", () => mocks);

import { managerBusinessService } from "../services/managerBusinessService";

describe("School Manager business API adapter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.adminOrganizationId.mockReturnValue("org /qa");
    mocks.adminApiRequest.mockResolvedValue({});
    mocks.adminBe1Request.mockResolvedValue({});
  });

  it("reads the verified organization", async () => {
    await managerBusinessService.organization();
    expect(mocks.adminBe1Request).toHaveBeenCalledWith("/organizations/org%20%2Fqa", {});
  });

  it("reads the T-7a roster count summary through the BE1 route", async () => {
    const signal = new AbortController().signal;
    mocks.adminBe1Request.mockResolvedValueOnce({ contract: "Be1ClassRosterSummaryV1", class_id: "class/one", active_profile_count: 3 });
    await expect(managerBusinessService.rosterSummary("class/one", signal)).resolves.toEqual({
      contract: "Be1ClassRosterSummaryV1", class_id: "class/one", active_profile_count: 3,
    });
    expect(mocks.adminBe1Request).toHaveBeenCalledWith(
      "/organizations/org%20%2Fqa/classes/class%2Fone/profiles",
      { signal },
    );
  });

  it("refuses a Teacher-shaped roster body instead of passing child names to the Manager screen", async () => {
    mocks.adminBe1Request.mockResolvedValueOnce({
      contract: "Be1ManagedProfileListV1",
      items: [{ child_id: "c-1", class_id: "class-1", display_name: "Synthetic An", age_months: 60 }],
    });
    await expect(managerBusinessService.rosterSummary("class-1")).rejects.toThrow("không đúng contract");
  });

  it("reads every consent page and keeps only the Manager item fields", async () => {
    mocks.adminBe1Request
      .mockResolvedValueOnce({ contract: "Be1ConsentListManagerV1", items: [{ consent_id: "k-1", state: "pending", effective: false }], next_cursor: "cur 2" })
      .mockResolvedValueOnce({ contract: "Be1ConsentListManagerV1", items: [{ consent_id: "k-2", state: "revoked", effective: false, child_id: "leak", purpose_ref: "leak" }], next_cursor: null });
    const items = await managerBusinessService.consents("class-1");
    expect(items).toEqual([
      { consent_id: "k-1", state: "pending", effective: false },
      { consent_id: "k-2", state: "revoked", effective: false },
    ]);
    expect(mocks.adminBe1Request).toHaveBeenNthCalledWith(1, "/organizations/org%20%2Fqa/classes/class-1/consents?limit=100", {});
    expect(mocks.adminBe1Request).toHaveBeenNthCalledWith(2, "/organizations/org%20%2Fqa/classes/class-1/consents?limit=100&cursor=cur+2", {});
  });

  it("revokes a consent with POST and no body, query, idempotency key, or revision", async () => {
    const result = { contract: "Be1ConsentV1", consent_id: "consent /1", state: "revoked", effective: false };
    mocks.adminBe1Request.mockResolvedValueOnce(result);
    await expect(managerBusinessService.revokeConsent("class /1", "consent /1")).resolves.toEqual(result);
    expect(mocks.adminBe1Request).toHaveBeenLastCalledWith(
      "/organizations/org%20%2Fqa/classes/class%20%2F1/consents/consent%20%2F1/revoke",
      { method: "POST" },
    );
    expect(mocks.adminBe1Request.mock.calls[0][1]).not.toHaveProperty("headers");
    expect(mocks.adminBe1Request.mock.calls[0][1]).not.toHaveProperty("body");
  });

  it("accepts the same revocation receipt for an already-revoked consent and maps a missing record safely", async () => {
    mocks.adminBe1Request.mockResolvedValueOnce({ contract: "Be1ConsentV1", consent_id: "consent-1", state: "revoked", effective: false });
    await expect(managerBusinessService.revokeConsent("class-1", "consent-1"))
      .resolves.toEqual({ contract: "Be1ConsentV1", consent_id: "consent-1", state: "revoked", effective: false });

    mocks.adminBe1Request.mockRejectedValueOnce(new mocks.AdminBe1Error("raw body and code", 404, "CONSENT_NOT_FOUND"));
    await expect(managerBusinessService.revokeConsent("class-1", "missing"))
      .rejects.toMatchObject({ status: 404, message: "Không tìm thấy bản ghi" });
  });

  it.each(["export", "delete"] as const)("creates a %s data request with the contract body and no duplicate-prevention headers", async (requestType) => {
    mocks.adminBe1Request.mockResolvedValueOnce({ contract: "Be1DataRequestV1", request_id: "request-1", state: "requested", completion_claimed: false });
    await expect(managerBusinessService.createDataRequest(requestType, "target /1 ")).resolves.toEqual({
      contract: "Be1DataRequestV1", request_id: "request-1", state: "requested", completion_claimed: false,
    });
    expect(mocks.adminBe1Request).toHaveBeenLastCalledWith("/organizations/org%20%2Fqa/data-requests", {
      method: "POST",
      body: JSON.stringify({ request_type: requestType, target_ref: "target /1 " }),
    });
  });

  it("validates target bounds and data-request response contracts", async () => {
    await expect(managerBusinessService.createDataRequest("export", "")).rejects.toMatchObject({ status: 422, code: "INVALID_REQUEST" });
    await expect(managerBusinessService.createDataRequest("delete", "x".repeat(257))).rejects.toMatchObject({ status: 422, code: "INVALID_REQUEST" });
    expect(mocks.adminBe1Request).not.toHaveBeenCalled();

    mocks.adminBe1Request.mockResolvedValueOnce({ contract: "wrong", request_id: "request-1", state: "requested", completion_claimed: false });
    await expect(managerBusinessService.createDataRequest("export", "child-1"))
      .rejects.toMatchObject({ status: 502, code: "INVALID_RESPONSE" });
  });

  it("looks up a data request by encoded id and guards its returned state", async () => {
    const signal = new AbortController().signal;
    mocks.adminBe1Request.mockResolvedValueOnce({
      contract: "Be1DataRequestV1", request_id: "request /1", request_type: "delete", target_ref: "class-1",
      state: "awaiting_external_purge", unresolved_items: 2, completion_claimed: false, private_field: "drop",
    });
    await expect(managerBusinessService.getDataRequest("request /1", signal)).resolves.toEqual({
      contract: "Be1DataRequestV1", request_id: "request /1", request_type: "delete", target_ref: "class-1",
      state: "awaiting_external_purge", unresolved_items: 2, completion_claimed: false,
    });
    expect(mocks.adminBe1Request).toHaveBeenLastCalledWith(
      "/organizations/org%20%2Fqa/data-requests/request%20%2F1",
      { signal },
    );

    mocks.adminBe1Request.mockRejectedValueOnce(new mocks.AdminBe1Error("raw response", 404, "DATA_REQUEST_NOT_FOUND"));
    await expect(managerBusinessService.getDataRequest("missing"))
      .rejects.toMatchObject({ status: 404, message: "Không tìm thấy yêu cầu hoặc bạn không có quyền truy cập." });
  });

  it("lists parent groups with an opaque cursor", async () => {
    await managerBusinessService.parentGroups("next page");
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups?cursor=next+page",
      {},
    );
  });

  it("lists the first page of parent groups without a query string", async () => {
    await managerBusinessService.parentGroups();
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups",
      {},
    );
  });

  it("never sends a page limit for parent groups", async () => {
    await managerBusinessService.parentGroups(undefined);
    await managerBusinessService.parentGroups("c");
    const paths = mocks.adminApiRequest.mock.calls.map((call) => String(call[0]));
    expect(paths).toHaveLength(2);
    paths.forEach((path) => expect(path).not.toContain("limit="));
  });

  it("creates a parent group only with explicit idempotency", async () => {
    await managerBusinessService.createParentGroup("Lớp Lá", "same-request-key");
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups",
      {
        method: "POST",
        headers: { "Idempotency-Key": "same-request-key" },
        body: JSON.stringify({
          contract: "CreateParentGroupRequestV1",
          display_name: "Lớp Lá",
        }),
      },
    );
  });

  it("lists parent group members with filter, opaque cursor, no-store, and only opaque member fields", async () => {
    const signal = new AbortController().signal;
    mocks.adminApiRequest.mockResolvedValueOnce({
      contract: "ParentGroupMemberListV1",
      items: [{ membership_id: "membership-123456789", parent_group_id: "group-1", state: "ACCEPTED", invited_at: "2026-11-01T00:00:00Z", expires_at: null, accepted_at: "2026-11-02T00:00:00Z", revision: 4, parent_name: "must be dropped", child_id: "must be dropped" }],
      counts: { invited: 1, accepted: 2, declined: 3, revoked: 4, expired: 5, total: 15, leaked_name: "must be dropped" },
      next_cursor: "opaque / cursor",
    });

    const page = await managerBusinessService.parentGroupMembers("group /1", { state: "ACCEPTED", cursor: "opaque + cursor", signal });

    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups/group%20%2F1/members?state=ACCEPTED&limit=25&cursor=opaque+%2B+cursor",
      { headers: { "Cache-Control": "private, no-store" }, signal },
    );
    expect(page.items).toEqual([{ membership_id: "membership-123456789", parent_group_id: "group-1", state: "ACCEPTED", invited_at: "2026-11-01T00:00:00Z", expires_at: null, accepted_at: "2026-11-02T00:00:00Z", revision: 4 }]);
    expect(page.counts).toEqual({ invited: 1, accepted: 2, declined: 3, revoked: 4, expired: 5, total: 15 });
    expect(JSON.stringify(page)).not.toContain("must be dropped");
  });

  it("validates member list bounds and state before sending a request", async () => {
    await expect(managerBusinessService.parentGroupMembers("group-1", { state: "ACTIVE" as never })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    await expect(managerBusinessService.parentGroupMembers("group-1", { limit: 0 })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    expect(mocks.adminApiRequest).not.toHaveBeenCalled();
  });

  it("revokes with the item's strong revision and idempotency key, and maps a foreign 404 neutrally", async () => {
    mocks.adminApiRequest.mockResolvedValueOnce({ membership_id: "membership-1", parent_group_id: "group-1", state: "REVOKED", invited_at: "2026-11-01T00:00:00Z", expires_at: null, accepted_at: null, revision: 5 });
    await expect(managerBusinessService.revokeParentGroupMember("group /1", "membership /1", 4, "revoke-key"))
      .resolves.toMatchObject({ state: "REVOKED", revision: 5 });
    expect(mocks.adminApiRequest).toHaveBeenLastCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups/group%20%2F1/members/membership%20%2F1",
      { method: "DELETE", headers: { "If-Match": '"4"', "Idempotency-Key": "revoke-key" } },
    );

    mocks.adminApiRequest.mockRejectedValueOnce(new mocks.AdminBe1Error("raw server text", 404, "RESOURCE_NOT_FOUND"));
    await expect(managerBusinessService.revokeParentGroupMember("group-1", "membership-2", 1, "revoke-key-2"))
      .rejects.toMatchObject({ status: 404, message: "Không tìm thấy nhóm hoặc membership yêu cầu." });
  });

  it("invites a Parent with the exact route, request contract, and idempotency key, then keeps only response fields", async () => {
    mocks.adminApiRequest.mockResolvedValueOnce({
      contract: "ParentGroupMembershipV1",
      membership_id: "membership-1",
      parent_group_id: "group /1",
      state: "INVITED",
      invited_at: "2026-11-25T10:00:00Z",
      expires_at: "2026-12-25T10:00:00Z",
      accepted_at: null,
      revision: 1,
      parent_principal_ref: "must be dropped",
    });

    await expect(managerBusinessService.inviteParentToGroup("group /1", " parent.ref ", "invite-key"))
      .resolves.toEqual({
        contract: "ParentGroupMembershipV1",
        membership_id: "membership-1",
        parent_group_id: "group /1",
        state: "INVITED",
        invited_at: "2026-11-25T10:00:00Z",
        expires_at: "2026-12-25T10:00:00Z",
        accepted_at: null,
        revision: 1,
      });
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups/group%20%2F1/invitations",
      {
        method: "POST",
        headers: { "Idempotency-Key": "invite-key" },
        body: JSON.stringify({ contract: "InviteParentToGroupRequestV1", parent_principal_ref: "parent.ref" }),
      },
    );
    expect(mocks.adminApiRequest.mock.calls[0][1]).not.toHaveProperty("headers.If-Match");
  });

  it("rejects malformed Parent refs before sending an invitation", async () => {
    await expect(managerBusinessService.inviteParentToGroup("group-1", "bad ref", "invite-key"))
      .rejects.toMatchObject({ status: 422, code: "INVALID_REQUEST", message: "Mã tài khoản phụ huynh chưa hợp lệ. Hãy kiểm tra và thử lại." });
    await expect(managerBusinessService.inviteParentToGroup("group-1", "x".repeat(257), "invite-key"))
      .rejects.toMatchObject({ status: 422, code: "INVALID_REQUEST" });
    expect(mocks.adminApiRequest).not.toHaveBeenCalled();
  });

  it.each([
    [409, "INVITATION_EXISTS", "Phụ huynh này đã được mời hoặc đang là thành viên."],
    [409, "INVALID_TRANSITION", "Nhóm đã lưu trữ; không thể mời thành viên."],
    [400, "INVALID_REQUEST", "Mã tài khoản phụ huynh chưa hợp lệ. Hãy kiểm tra và thử lại."],
    [422, "INVALID_REQUEST", "Mã tài khoản phụ huynh chưa hợp lệ. Hãy kiểm tra và thử lại."],
    [404, "RESOURCE_NOT_FOUND", "Không tìm thấy nhóm hoặc membership yêu cầu."],
    [503, "PROVIDER_UNAVAILABLE", "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau."],
    [403, "ACTION_NOT_ALLOWED", "Tài khoản không có quyền thực hiện thao tác này."],
  ])("maps invitation refusal %s %s to safe Vietnamese copy", async (status, code, message) => {
    mocks.adminApiRequest.mockRejectedValueOnce(new mocks.AdminBe1Error("raw server body and token", status as number, code as string));

    await expect(managerBusinessService.inviteParentToGroup("group-1", "parent:ref", "invite-key"))
      .rejects.toMatchObject({ status, code, message });
  });

  it("validates the invitation response state, membership id, revision, and expiry", async () => {
    const valid = {
      contract: "ParentGroupMembershipV1",
      membership_id: "membership-1",
      parent_group_id: "group-1",
      state: "INVITED",
      invited_at: "2026-11-25T10:00:00Z",
      expires_at: "2026-12-25T10:00:00Z",
      accepted_at: null,
      revision: 1,
    };
    for (const response of [
      { ...valid, state: "ACTIVE" },
      { ...valid, membership_id: "" },
      { ...valid, revision: 1.5 },
      { ...valid, expires_at: "not-a-date" },
    ]) {
      mocks.adminApiRequest.mockResolvedValueOnce(response);
      await expect(managerBusinessService.inviteParentToGroup("group-1", "parent:ref", "invite-key"))
        .rejects.toMatchObject({ status: 502, code: "INVALID_RESPONSE" });
    }
  });

  it("rejects a missing revision or malformed idempotency key before DELETE", async () => {
    await expect(managerBusinessService.revokeParentGroupMember("group-1", "membership-1", 0, "revoke-key"))
      .rejects.toMatchObject({ code: "INVALID_REQUEST" });
    await expect(managerBusinessService.revokeParentGroupMember("group-1", "membership-1", 1, "bad key"))
      .rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    expect(mocks.adminApiRequest).not.toHaveBeenCalled();
  });

  it("reads feedback with encoded paths and server-default pagination", async () => {
    mocks.adminApiRequest.mockResolvedValueOnce({ items: [], next_cursor: null });
    await managerBusinessService.feedbackThreads("next page");
    expect(mocks.adminApiRequest).toHaveBeenLastCalledWith("/lesson-library/v1/organizations/org%20%2Fqa/feedback?cursor=next%20page", {});
    mocks.adminApiRequest.mockResolvedValueOnce({ thread_id: "t/1", revision: 3, items: [], next_cursor: null });
    await managerBusinessService.feedbackThread("t/1", "c /2");
    expect(mocks.adminApiRequest).toHaveBeenLastCalledWith("/lesson-library/v1/organizations/org%20%2Fqa/feedback/t%2F1?cursor=c%20%2F2", {});
  });

  it("sends the exact reply precondition and rejects malformed responses", async () => {
    mocks.adminApiRequest.mockResolvedValueOnce({ thread_id: "t/1", revision: 4 });
    await managerBusinessService.replyFeedback("t/1", "Hello", 3, "key");
    expect(mocks.adminApiRequest).toHaveBeenLastCalledWith("/lesson-library/v1/organizations/org%20%2Fqa/feedback/t%2F1/replies", { method: "POST", headers: { "If-Match": '"3"', "Idempotency-Key": "key" }, body: '{"body":"Hello"}' });
    mocks.adminApiRequest.mockResolvedValueOnce({ items: [{}], next_cursor: null });
    await expect(managerBusinessService.feedbackThreads()).rejects.toThrow();
  });
});
