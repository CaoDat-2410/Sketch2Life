// Goal v4 Phase B T-7e roster paging; preserve existing T-7a reads, T-7c create, T-7d move and A07 paging.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { backendApi } from "../backendApi";
import { collectCursorPages } from "../cursorPages";
import {
  CLASS_READ_ONLY,
  NOT_FOUND_OR_NO_ACCESS,
  TeacherRosterApiError,
  TeacherRosterPageError,
  keepsCommandKey,
  profileInputProblem,
  teacherRosterApi,
} from "../teacherRosterApi";

function response(status: number, body?: unknown, headers: Record<string, string> = {}): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "response-1", ...headers }),
    text: async () => (body === undefined ? "" : JSON.stringify(body)),
  } as Response;
}
const rejectionOf = (promise: Promise<unknown>) =>
  promise.then(() => { throw new Error("expected a rejection"); }, (cause: unknown) => cause as TeacherRosterApiError);
const envelope = (code: string, message: string, extra: Record<string, unknown> = {}) => ({ code, message, correlation_id: "corr-1", retryable: false, ...extra });

function setup(replies: Response[]) {
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
const call = (fetcher: ReturnType<typeof setup>, index = 0) => {
  const [url, init] = fetcher.mock.calls[index];
  return { url: new URL(url), init, headers: new Headers(init.headers), body: init.body ? JSON.parse(String(init.body)) as unknown : undefined };
};

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") } as never;
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

describe("cursor paging (SRS l.1640)", () => {
  it("collects every page until next_cursor is null", async () => {
    const load = vi.fn()
      .mockResolvedValueOnce({ items: [1, 2], next_cursor: "c2" })
      .mockResolvedValueOnce({ items: [3], next_cursor: "c3" })
      .mockResolvedValueOnce({ items: [4], next_cursor: null });
    const { items } = await collectCursorPages<number>(load);
    expect(items).toEqual([1, 2, 3, 4]);
    expect(load.mock.calls.map((args) => args[0])).toEqual([undefined, "c2", "c3"]);
  });

  it("stops at the page cap instead of looping", async () => {
    let n = 0;
    const load = vi.fn(async () => ({ items: [n], next_cursor: `c${++n}` }));
    const { items } = await collectCursorPages<number>(load, 3);
    expect(load).toHaveBeenCalledTimes(3);
    expect(items).toHaveLength(3);
  });

  it("stops when a server repeats the same cursor", async () => {
    const load = vi.fn()
      .mockResolvedValueOnce({ items: [1], next_cursor: "same" })
      .mockResolvedValueOnce({ items: [2], next_cursor: "same" });
    const { items } = await collectCursorPages<number>(load);
    expect(items).toEqual([1, 2]);
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("backendApi.classes sends the state filter and joins every A07 page (T-7a/T-7b)", async () => {
    const fetcher = setup([
      response(200, { contract: "Be1ClassListV1", items: [{ class_id: "a", display_name: "A", state: "active", class_revision: 2 }], next_cursor: "n/2" }),
      response(200, { contract: "Be1ClassListV1", items: [{ class_id: "s", display_name: "S", state: "suspended", class_revision: 4 }], next_cursor: null }),
    ]);
    const page = await backendApi.classes("org-test", "all");
    expect(page.items.map((item) => [item.class_id, item.state, item.class_revision])).toEqual([["a", "active", 2], ["s", "suspended", 4]]);
    expect(Object.fromEntries(call(fetcher).url.searchParams)).toEqual({ state: "all", limit: "100" });
    expect(Object.fromEntries(call(fetcher, 1).url.searchParams)).toEqual({ state: "all", limit: "100", cursor: "n/2" });
  });

  it("backendApi.classes keeps the server default active filter for existing callers", async () => {
    const fetcher = setup([response(200, { contract: "Be1ClassListV1", items: [], next_cursor: null })]);
    await backendApi.classes("org-test");
    expect(call(fetcher).url.searchParams.get("state")).toBe("active");
  });
});

describe("Teacher roster reads (T-7e)", () => {
  it("pages the Teacher roster at limit 100, passes the cursor, and de-duplicates child ids", async () => {
    const first = { child_id: "c-1", class_id: "k", display_name: "Synthetic An", age_months: 60 };
    const second = { child_id: "c-2", class_id: "k", display_name: "Synthetic Bình", age_months: 61 };
    const third = { child_id: "c-3", class_id: "k", display_name: "Synthetic Chi", age_months: 62 };
    const cursor = "opaque /+?=cursor";
    const fetcher = setup([
      response(200, { contract: "Be1ManagedProfileListV1", items: [first, second], next_cursor: cursor, active_profile_count: 7 }),
      response(200, { contract: "Be1ManagedProfileListV1", items: [second, third], next_cursor: null, active_profile_count: 8 }),
      response(200, { contract: "Be1ClassRosterSummaryV1", class_id: "k", active_profile_count: 2 }),
    ]);
    await expect(teacherRosterApi.profiles("org-test", "k/1")).resolves.toEqual({
      items: [first, second, third],
      activeProfileCount: 7,
    });
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org-test/classes/k%2F1/profiles");
    expect(call(fetcher).url.search).toBe("?limit=100");
    expect(call(fetcher, 1).url.searchParams.get("limit")).toBe("100");
    expect(call(fetcher, 1).url.searchParams.get("cursor")).toBe(cursor);
    expect(call(fetcher, 1).headers.get("Authorization")).toBe("Bearer token-1");
    await expect(teacherRosterApi.profiles("org-test", "k")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });

  it("keeps an empty page when the active class count is positive", async () => {
    setup([response(200, { contract: "Be1ManagedProfileListV1", items: [], next_cursor: null, active_profile_count: 4 })]);
    await expect(teacherRosterApi.profiles("org-test", "k")).resolves.toEqual({ items: [], activeProfileCount: 4 });
  });

  it("keeps loaded roster items and stops when a later page fails", async () => {
    const first = { child_id: "c-1", class_id: "k", display_name: "Synthetic An", age_months: 60 };
    const fetcher = setup([
      response(200, { contract: "Be1ManagedProfileListV1", items: [first], next_cursor: "c/2", active_profile_count: 3 }),
      response(503, envelope("PROVIDER_UNAVAILABLE", "Máy chủ bận.")),
    ]);
    const error = await rejectionOf(teacherRosterApi.profiles("org-test", "k"));
    expect(error).toBeInstanceOf(TeacherRosterPageError);
    expect(error).toMatchObject({
      status: 503,
      code: "PROVIDER_UNAVAILABLE",
      partial: { items: [first], activeProfileCount: 3 },
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("reads every A10 page with the class cursor", async () => {
    const consent = (id: string) => ({ consent_id: id, child_id: "c-" + id, purpose_ref: "p", state: "effective", effective: true });
    const fetcher = setup([
      response(200, { contract: "Be1ConsentListV1", items: [consent("1")], next_cursor: "x" }),
      response(200, { contract: "Be1ConsentListV1", items: [consent("2")], next_cursor: null }),
    ]);
    const items = await teacherRosterApi.consents("org-test", "k");
    expect(items.map((item) => item.consent_id)).toEqual(["1", "2"]);
    expect(call(fetcher, 1).url.search).toBe("?limit=100&cursor=x");
  });

  it("T-7a2: a 404 for an other-class or revoked Teacher reads exactly like an unknown class", async () => {
    setup([
      response(404, envelope("RESOURCE_NOT_FOUND", "Không tìm thấy tài nguyên được yêu cầu.")),
      response(404, { detail: { code: "RESOURCE_NOT_FOUND", message: "Class not found" } }),
    ]);
    const first = await rejectionOf(teacherRosterApi.profiles("org-test", "other-class"));
    const second = await rejectionOf(teacherRosterApi.profiles("org-test", "missing"));
    expect(first.message).toBe(NOT_FOUND_OR_NO_ACCESS);
    expect(second.message).toBe(first.message);
    expect([first.status, first.code]).toEqual([second.status, second.code]);
  });

  it("T-7a2: a 403 for a covering non-class-Teacher row is the safe not-allowed text", async () => {
    setup([response(403, envelope("ACTION_NOT_ALLOWED", "Tài khoản không được phép thực hiện thao tác này."))]);
    await expect(teacherRosterApi.profiles("org-test", "k")).rejects.toMatchObject({ status: 403, code: "ACTION_NOT_ALLOWED", message: "Tài khoản không được phép thực hiện thao tác này." });
  });

  it("preserves 400 INVALID_REQUEST mapping for a bad roster request", async () => {
    setup([response(400, envelope("INVALID_REQUEST", "Yêu cầu không hợp lệ.", { field_errors: [{ field: "cursor", code: "INVALID_FORMAT", message: "Cursor không hợp lệ." }] }))]);
    await expect(teacherRosterApi.profiles("org-test", "k")).rejects.toMatchObject({ status: 400, code: "INVALID_REQUEST", message: "Yêu cầu không hợp lệ." });
  });

  it("does not add roster-specific handling for an unexpected legacy 409", async () => {
    setup([response(409, envelope("CONSENT_NOT_EFFECTIVE", "Roster request was rejected."))]);
    await expect(teacherRosterApi.profiles("org-test", "k")).rejects.toMatchObject({
      status: 409,
      code: "CONSENT_NOT_EFFECTIVE",
      message: "Roster request was rejected.",
    });
  });
});

describe("Teacher consent commands (GAP-04)", () => {
  const pendingConsent = {
    contract: "Be1ConsentV1" as const,
    consent_id: "consent-1",
    child_id: "real-child",
    purpose_ref: "classroom-learning-v1",
    state: "pending",
    effective: false,
  };

  it("posts the strict consent body, parses 201, and never sends If-Match", async () => {
    const fetcher = setup([response(201, pendingConsent)]);
    const result = await teacherRosterApi.recordConsent(
      "org/one",
      "k/1",
      { childId: "real-child", purposeRef: "classroom-learning-v1", evidenceRef: "paper-form-1" },
      "consent-key",
    );
    const request = call(fetcher);
    expect(request.init.method).toBe("POST");
    expect(request.url.pathname).toBe("/api/be1/v1/organizations/org%2Fone/classes/k%2F1/consents");
    expect(request.body).toEqual({
      class_id: "k/1",
      child_id: "real-child",
      purpose_ref: "classroom-learning-v1",
      evidence_ref: "paper-form-1",
    });
    expect(request.body).not.toHaveProperty("contract");
    expect(request.headers.get("Idempotency-Key")).toBe("consent-key");
    expect(request.headers.get("If-Match")).toBeNull();
    expect(result).toEqual({ consent_id: pendingConsent.consent_id, state: pendingConsent.state });
  });

  it("accepts a 201 consent receipt with only its required fields", async () => {
    setup([response(201, { consent_id: "consent-1", state: "pending", child_id: "different-child", purpose_ref: "different-purpose" })]);
    await expect(teacherRosterApi.recordConsent("org-test", "k", {
      childId: "real-child",
      purposeRef: "classroom-learning-v1",
    })).resolves.toEqual({ consent_id: "consent-1", state: "pending" });
  });

  it.each([
    [404, envelope("CLASS_NOT_FOUND", "Raw not-found body"), NOT_FOUND_OR_NO_ACCESS],
    [403, envelope("ACTION_NOT_ALLOWED", "Raw refusal body"), "Tài khoản không được phép thực hiện thao tác này."],
    [409, envelope("INVALID_STATE_TRANSITION", "Raw state body"), CLASS_READ_ONLY],
    [422, envelope("CLASS_SCOPE_MISMATCH", "Raw scope body"), "Lớp trong yêu cầu không khớp với lớp đã chọn."],
    [422, envelope("INVALID_REQUEST", "Raw validation body"), "Thông tin consent không hợp lệ. Vui lòng kiểm tra lại."],
    [400, envelope("INVALID_REQUEST", "Raw validation body"), "Thông tin consent không hợp lệ. Vui lòng kiểm tra lại."],
  ])("maps consent refusal %i to safe Vietnamese copy", async (status, body, message) => {
    setup([response(status, body)]);
    const error = await rejectionOf(teacherRosterApi.recordConsent("org-test", "k", {
      childId: "real-child",
      purposeRef: "classroom-learning-v1",
    }));
    expect(error.message).toBe(message);
    expect(error.message).not.toContain("Raw");
  });

  it("revokes by class and consent path with no body, key, or If-Match", async () => {
    const revoked = { ...pendingConsent, consent_id: "consent/1", state: "revoked" };
    const fetcher = setup([response(200, revoked)]);
    await expect(teacherRosterApi.revokeConsent("org/one", "k/1", "consent/1")).resolves.toEqual(revoked);
    const request = call(fetcher);
    expect(request.init.method).toBe("POST");
    expect(request.url.pathname).toBe("/api/be1/v1/organizations/org%2Fone/classes/k%2F1/consents/consent%2F1/revoke");
    expect(request.body).toBeUndefined();
    expect(request.headers.get("Idempotency-Key")).toBeNull();
    expect(request.headers.get("If-Match")).toBeNull();
  });

  it("maps a missing consent on revoke to the same uniform 404 copy", async () => {
    setup([response(404, envelope("CONSENT_NOT_FOUND", "Raw consent body"))]);
    await expect(teacherRosterApi.revokeConsent("org-test", "k", "missing")).rejects.toMatchObject({
      status: 404,
      message: NOT_FOUND_OR_NO_ACCESS,
    });
  });

  it("rejects invalid inputs before fetch", async () => {
    const fetcher = setup([]);
    await expect(teacherRosterApi.recordConsent("org-test", "k", {
      childId: " ",
      purposeRef: "classroom-learning-v1",
    })).rejects.toMatchObject({ code: "INVALID_REQUEST", status: 400 });
    expect(fetcher).not.toHaveBeenCalled();
  });
});

describe("Teacher profile create (T-7c, T-7c-fix)", () => {
  const input = { display_name: "Synthetic Minh", age_months: 60 };

  it("sends the key, the strong class-revision If-Match and a body without class_id", async () => {
    const fetcher = setup([response(201, { contract: "Be1ManagedProfileV1", child_id: "c-9", class_id: "k", enrollment_id: "e-1", display_name: "Synthetic Minh", age_months: 60, data_origin: "SYNTHETIC_DEV", class_revision: 3 }, { ETag: '"3"' })]);
    const created = await teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1");
    const { url, init, headers, body } = call(fetcher);
    expect(init.method).toBe("POST");
    expect(url.pathname).toBe("/api/be1/v1/organizations/org-test/classes/k/profiles");
    expect(headers.get("Idempotency-Key")).toBe("key-1");
    expect(headers.get("If-Match")).toBe('"3"');
    expect(body).toEqual({ display_name: "Synthetic Minh", age_months: 60 });
    expect(created.class_revision).toBe(3);
  });

  it("rejects a key outside 1-128 visible ASCII and an invalid revision before fetch", async () => {
    const fetcher = setup([]);
    for (const key of ["", "a".repeat(129), "has space", "khóa"]) {
      await expect(teacherRosterApi.createProfile("org-test", "k", 3, input, key)).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    }
    await expect(teacherRosterApi.createProfile("org-test", "k", 0, input, "a".repeat(128))).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("checks the synthetic name prefix and the 36-120 month age range on the client", () => {
    expect(profileInputProblem(input)).toBeNull();
    expect(profileInputProblem({ display_name: "Minh", age_months: 60 })).toMatch(/Synthetic /);
    expect(profileInputProblem({ display_name: "Synthetic ", age_months: 60 })).toMatch(/Synthetic /);
    expect(profileInputProblem({ display_name: "Synthetic " + "x".repeat(200), age_months: 60 })).toMatch(/200/);
    expect(profileInputProblem({ display_name: "Synthetic Minh", age_months: 35 })).toMatch(/36 đến 120/);
    expect(profileInputProblem({ display_name: "Synthetic Minh", age_months: 121 })).toMatch(/36 đến 120/);
    expect(profileInputProblem({ display_name: "Synthetic Minh", age_months: 60.5 })).toMatch(/36 đến 120/);
  });

  it.each([
    [409, envelope("STALE_REVISION", "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", { current_version: 4 }), "STALE_REVISION", "Thông tin đã thay đổi. Vui lòng tải lại và thử lại."],
    [400, envelope("INVALID_IDEMPOTENCY_KEY", "Khóa yêu cầu trùng với một yêu cầu có nội dung khác."), "INVALID_IDEMPOTENCY_KEY", "Khóa yêu cầu trùng với một yêu cầu có nội dung khác."],
    [409, envelope("INVALID_STATE_TRANSITION", "Tài nguyên chưa ở trạng thái phù hợp cho thao tác này."), "INVALID_STATE_TRANSITION", "Lớp hoặc hồ sơ không còn ở trạng thái cho phép thao tác này. Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ."],
    [409, envelope("SYNTHETIC_PROFILE_CREATION_UNAVAILABLE", "Tài nguyên chưa ở trạng thái phù hợp cho thao tác này."), "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE", "Môi trường này chưa cho phép tạo hồ sơ thử nghiệm."],
    [403, envelope("ACTION_NOT_ALLOWED", "Tài khoản không được phép thực hiện thao tác này."), "ACTION_NOT_ALLOWED", "Tài khoản không được phép thực hiện thao tác này."],
    [404, envelope("RESOURCE_NOT_FOUND", "Không tìm thấy tài nguyên được yêu cầu."), "RESOURCE_NOT_FOUND", NOT_FOUND_OR_NO_ACCESS],
    [400, envelope("INVALID_REQUEST", "Yêu cầu không hợp lệ.", { field_errors: [{ field: "body.class_id", code: "UNKNOWN_FIELD" }] }), "INVALID_REQUEST", "Yêu cầu không hợp lệ."],
  ])("projects %i %s to the SRS Vietnamese copy", async (status, body, code, message) => {
    setup([response(status, body)]);
    const error = await rejectionOf(teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1"));
    expect(error).toBeInstanceOf(TeacherRosterApiError);
    expect(error.code).toBe(code);
    expect(error.message).toBe(message);
    expect(keepsCommandKey(error)).toBe(false);
  });

  it("429 RATE_LIMITED keeps the Retry-After wait (SRS l.1735)", async () => {
    setup([
      response(429, envelope("RATE_LIMITED", "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.", { retryable: true }), { "Retry-After": "17" }),
      response(429, envelope("RATE_LIMITED", "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.", { retryable: true, retry_after_seconds: 9 })),
    ]);
    const fromHeader = await rejectionOf(teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1"));
    expect(fromHeader.retryAfterSeconds).toBe(17);
    expect(fromHeader.message).toBe("Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau 17 giây.");
    const fromBody = await rejectionOf(teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1"));
    expect(fromBody.retryAfterSeconds).toBe(9);
  });

  it("a 2xx with an unreadable body keeps the action key (the outcome is unclear, F-01)", async () => {
    setup([response(201, undefined), { ok: true, status: 201, headers: new Headers(), text: async () => "<html>" } as Response]);
    const empty = await rejectionOf(teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1"));
    const garbled = await rejectionOf(teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1"));
    expect(empty.code).toBe("INVALID_RESPONSE");
    expect(keepsCommandKey(empty)).toBe(true);
    expect(keepsCommandKey(garbled)).toBe(true);
  });

  it("a network failure or 5xx keeps the action key for a retry of the same command", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    const network = await teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1").catch((cause: unknown) => cause);
    expect(keepsCommandKey(network)).toBe(true);
    setup([response(503, envelope("PROVIDER_UNAVAILABLE", "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau."))]);
    const unavailable = await teacherRosterApi.createProfile("org-test", "k", 3, input, "key-1").catch((cause: unknown) => cause);
    expect(keepsCommandKey(unavailable)).toBe(true);
  });
});

describe("Teacher enrollment move (T-7d)", () => {
  it("puts the source revision in If-Match and the target class and revision in the body", async () => {
    const fetcher = setup([response(200, { contract: "Be1ProfileMoveV1", child_id: "c/1", from_class_id: "src", to_class_id: "dst", enrollment_id: "e-2", from_class_revision: 5, to_class_revision: 8 })]);
    const moved = await teacherRosterApi.moveProfile("src", 4, "c/1", { classId: "dst", revision: 7 }, "move-key");
    const { url, init, headers, body } = call(fetcher);
    expect(init.method).toBe("POST");
    expect(url.pathname).toBe("/api/be1/v1/classes/src/profiles/c%2F1/move");
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Idempotency-Key")).toBe("move-key");
    expect(body).toEqual({ target_class_id: "dst", target_class_revision: 7 });
    expect([moved.from_class_revision, moved.to_class_revision]).toEqual([5, 8]);
  });

  it("refuses a move to the same class before fetch", async () => {
    const fetcher = setup([]);
    await expect(teacherRosterApi.moveProfile("src", 4, "c", { classId: "src", revision: 4 }, "k")).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("projects stale and state refusals of a move", async () => {
    setup([
      response(409, envelope("STALE_REVISION", "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", { current_version: 9 })),
      response(409, envelope("INVALID_STATE_TRANSITION", "Tài nguyên chưa ở trạng thái phù hợp cho thao tác này.")),
    ]);
    await expect(teacherRosterApi.moveProfile("src", 4, "c", { classId: "dst", revision: 7 }, "k")).rejects.toMatchObject({ code: "STALE_REVISION", status: 409 });
    await expect(teacherRosterApi.moveProfile("src", 4, "c", { classId: "dst", revision: 7 }, "k")).rejects.toMatchObject({ code: "INVALID_STATE_TRANSITION" });
  });
});
