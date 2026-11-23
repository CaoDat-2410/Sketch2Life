// Goal v3 Phase B: Teacher BE1 roster client (T-7a reads, T-7c keyed create, T-7d move) and A07 paging.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { backendApi } from "../backendApi";
import { collectCursorPages } from "../cursorPages";
import {
  NOT_FOUND_OR_NO_ACCESS,
  TeacherRosterApiError,
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

describe("Teacher roster reads (T-7a)", () => {
  it("reads the Teacher A09 list and refuses a Manager count body", async () => {
    const fetcher = setup([
      response(200, { contract: "Be1ManagedProfileListV1", items: [{ child_id: "c-1", class_id: "k", display_name: "Synthetic An", age_months: 60 }] }),
      response(200, { contract: "Be1ClassRosterSummaryV1", class_id: "k", active_profile_count: 2 }),
    ]);
    await expect(teacherRosterApi.profiles("org-test", "k/1")).resolves.toHaveLength(1);
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org-test/classes/k%2F1/profiles");
    await expect(teacherRosterApi.profiles("org-test", "k")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
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
    await expect(teacherRosterApi.consents("org-test", "k")).rejects.toMatchObject({ status: 403, code: "ACTION_NOT_ALLOWED", message: "Tài khoản không được phép thực hiện thao tác này." });
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
    [409, envelope("SYNTHETIC_PROFILE_CREATION_UNAVAILABLE", "Tài nguyên chưa ở trạng thái phù hợp cho thao tác này."), "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE", "Môi trường này chưa cho phép tạo hồ sơ thử nghiệm (synthetic)."],
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
