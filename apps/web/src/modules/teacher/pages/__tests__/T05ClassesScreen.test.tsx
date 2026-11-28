// Goal v3 Phase B: Teacher class page (T-7a2 server-decided 403/404, T-7b read-only class, T-7c create, T-7d move).
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TeacherApiClassesPage, T05ClassDetailPage } from "../T05ClassesScreen";
import { BackendApiError, backendApi, type Be1Class } from "../../../../shared/api/backendApi";
import { teacherProfileShareApi } from "../../../../shared/api/teacherProfileShareApi";
import { teacherProfileApi } from "../../../../shared/api/teacherProfileApi";
import { NOT_FOUND_OR_NO_ACCESS, TeacherRosterApiError, TeacherRosterPageError, teacherRosterApi } from "../../../../shared/api/teacherRosterApi";

const klass = (id: string, state: Be1Class["state"] = "active", revision = 3): Be1Class => ({ class_id: id, display_name: "Lớp " + id, state, class_revision: revision });
const profile = (id: string) => ({ child_id: id, class_id: "k1", display_name: "Synthetic " + id, age_months: 60 });
const consent = (child: string) => ({ consent_id: "c-" + child, child_id: child, purpose_ref: "story", state: "effective", effective: true });

function mockApis(options: { classes?: Be1Class[]; teacherClassIds?: string[]; profiles?: unknown; consents?: unknown } = {}) {
  vi.spyOn(backendApi, "assignments").mockResolvedValue({
    contract: "Be1AdultAssignmentsV1", subject: "s", organization_id: "org-test",
    assignments: (options.teacherClassIds ?? ["k1", "k2"]).map((class_id) => ({ role: "teacher" as const, class_id, active: true })),
  });
  const classes = vi.spyOn(backendApi, "classes").mockResolvedValue({ contract: "Be1ClassListV1", items: options.classes ?? [klass("k1"), klass("k2", "active", 7)] });
  const profiles = vi.spyOn(teacherRosterApi, "profiles");
  if (options.profiles instanceof Error) profiles.mockRejectedValue(options.profiles);
  else profiles.mockResolvedValue((options.profiles as never) ?? { items: [profile("a")], activeProfileCount: 1 });
  const consents = vi.spyOn(teacherRosterApi, "consents");
  if (options.consents instanceof Error) consents.mockRejectedValue(options.consents); else consents.mockResolvedValue((options.consents as never) ?? [consent("a")]);
  return { classes, profiles, consents };
}

const renderDetail = (classId = "k1") => render(<MemoryRouter><T05ClassDetailPage classId={classId} /></MemoryRouter>);
const openConsentForm = async () => {
  const title = await screen.findByText("Ghi nhận sự đồng ý của phụ huynh");
  const summary = title.closest("summary");
  if (!summary) throw new Error("consent disclosure summary not rendered");
  fireEvent.click(summary);
};

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = { signIn: vi.fn(async () => undefined), getIdToken: vi.fn(async () => "token-1") } as never;
  vi.spyOn(teacherProfileShareApi, "getSharedProfile").mockRejectedValue(new BackendApiError("not found", "RESOURCE_NOT_FOUND", 404));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

describe("Teacher class list", () => {
  it("lists every visible state and labels a suspended class read-only", async () => {
    const { classes } = mockApis({ classes: [klass("k1"), klass("k2", "suspended")] });
    render(<MemoryRouter><TeacherApiClassesPage /></MemoryRouter>);
    expect(await screen.findByText(/Tạm ngưng · chỉ đọc/)).toBeTruthy();
    const consentCopy = screen.getByText("Chỉ hiển thị hồ sơ thử nghiệm hoặc hồ sơ đã có sự đồng ý của phụ huynh còn hiệu lực.");
    expect(consentCopy.tagName).toBe("P");
    expect(consentCopy.className).toContain("s2l-muted-copy");
    expect(classes).toHaveBeenCalledWith("org-test", "all");
  });
});

describe("Teacher class page scope (T-7a2)", () => {
  it("offers profile panels on roster rows and reads support needs only after open", async () => {
    mockApis();
    const supportRead = vi.spyOn(teacherProfileApi, "getSupportNeeds").mockResolvedValue({
      contract: "Be1SupportNeedsV1", child_id: "a", revision: 0, category: null, note: null,
    });
    renderDetail();
    const editHint = await screen.findByText("Chỉnh sửa danh sách chỉ khả dụng khi lớp đang hoạt động.");
    expect(editHint.className).toContain("cozy-form-hint");
    expect((await screen.findAllByText("Synthetic a")).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Hồ sơ nổi bật" })).toBeTruthy();
    const shareSummary = screen.getByText("Chia sẻ từ phụ huynh").closest("summary");
    if (!shareSummary) throw new Error("parent share disclosure summary not rendered");
    fireEvent.click(shareSummary);
    expect(await screen.findByLabelText("Mã do phụ huynh cung cấp")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Lịch sử hồ sơ" })).toBeTruthy();
    expect(supportRead).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Phiên bản 0")).toBeTruthy();
    expect(supportRead).toHaveBeenCalledWith("org-test", "k1", "a");
  });

  it("shows one uniform not-found text for a 404 and no local 403", async () => {
    mockApis({ profiles: new TeacherRosterApiError(NOT_FOUND_OR_NO_ACCESS, "RESOURCE_NOT_FOUND", 404), consents: new TeacherRosterApiError(NOT_FOUND_OR_NO_ACCESS, "RESOURCE_NOT_FOUND", 404), teacherClassIds: [] });
    const { container } = renderDetail("other-class");
    expect((await screen.findByRole("alert")).textContent).toContain(NOT_FOUND_OR_NO_ACCESS);
    expect(container.textContent).not.toContain("assignment Teacher hiện hành");
    expect(screen.queryByText(/Tạo hồ sơ thử nghiệm/)).toBeNull();
  });

  it("shows the safe not-allowed text when the server answers 403 for a covering row", async () => {
    mockApis({ profiles: new TeacherRosterApiError("Tài khoản không được phép thực hiện thao tác này.", "ACTION_NOT_ALLOWED", 403) });
    renderDetail();
    expect((await screen.findByRole("alert")).textContent).toContain("Tài khoản không được phép thực hiện thao tác này.");
    expect(screen.queryByText("Synthetic a")).toBeNull();
  });

  it("asks the server even when /me has no class row (the server decides 403 or 404)", async () => {
    const { profiles, consents } = mockApis({ teacherClassIds: [] });
    renderDetail();
    expect((await screen.findAllByText("Synthetic a")).length).toBeGreaterThan(0);
    expect(profiles).toHaveBeenCalledWith("org-test", "k1");
    expect(consents).toHaveBeenCalledWith("org-test", "k1");
    expect(screen.queryByRole("button", { name: "Chuyển lớp" })).toBeNull();
  });

  it("keeps the API-filtered roster visible when the separate consent read fails", async () => {
    mockApis({ consents: new TeacherRosterApiError("Máy chủ bận.", "PROVIDER_UNAVAILABLE", 503) });
    renderDetail();
    expect(await screen.findByText(/Chi tiết trạng thái đồng ý của phụ huynh chưa thể tải/)).toBeTruthy();
    expect((await screen.findAllByText("Synthetic a")).length).toBeGreaterThan(0);
  });

  it("shows an ordinary safe error for an unexpected legacy CONSENT_NOT_EFFECTIVE response", async () => {
    mockApis({ profiles: new TeacherRosterApiError("Roster request was rejected.", "CONSENT_NOT_EFFECTIVE", 409, "corr-locked") });
    renderDetail();
    const error = await screen.findByRole("alert");
    expect(error.textContent).toContain("Roster request was rejected.");
    expect(error.textContent).toContain("Mã yêu cầu: corr-locked");
    expect(screen.queryByText("Danh sách hồ sơ tạm khóa đến khi có consent hiệu lực")).toBeNull();
  });

  it("keeps rows loaded before a later roster page failure", async () => {
    const partial = { items: [profile("a")], activeProfileCount: 3 };
    mockApis({ profiles: new TeacherRosterPageError(
      new TeacherRosterApiError("Máy chủ bận.", "PROVIDER_UNAVAILABLE", 503),
      partial,
    ) });
    renderDetail();
    expect(await screen.findByText(/Danh sách hồ sơ chỉ tải được một phần: Máy chủ bận/)).toBeTruthy();
    expect(screen.getAllByText("Synthetic a").length).toBeGreaterThan(0);
  });

  it("explains an empty eligible list with the aggregate active count", async () => {
    mockApis({ profiles: { items: [], activeProfileCount: 4 } });
    renderDetail();
    expect(await screen.findByText("Lớp có 4 hồ sơ đang hoạt động nhưng chưa có hồ sơ nào đủ điều kiện hiển thị.")).toBeTruthy();
  });

  it("keeps the existing empty text when the active count is zero", async () => {
    mockApis({ profiles: { items: [], activeProfileCount: 0 } });
    renderDetail();
    expect(await screen.findByText("Chưa có hồ sơ có sự đồng ý còn hiệu lực cho lớp này.")).toBeTruthy();
  });
});

describe("Teacher read-only suspended class (T-7b)", () => {
  it("shows the read-only copy and offers no create or move", async () => {
    mockApis({ classes: [klass("k1", "suspended"), klass("k2")] });
    renderDetail();
    expect(await screen.findByText("Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.")).toBeTruthy();
    expect((await screen.findAllByText("Synthetic a")).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Tạo hồ sơ thử nghiệm/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Chuyển lớp" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Ghi nhận sự đồng ý" })).toBeNull();
    expect(screen.queryByLabelText("Mã trẻ")).toBeNull();
    expect(screen.queryByRole("button", { name: /Thu hồi sự đồng ý/ })).toBeNull();
    expect(screen.queryByLabelText("Mã do phụ huynh cung cấp")).toBeNull();
  });
});

describe("Teacher consent record and revoke (GAP-04)", () => {
  const pendingConsent = {
    consent_id: "consent-1",
    child_id: "real-child",
    purpose_ref: "classroom-learning-v1",
    state: "pending",
    effective: false,
  };

  it("starts the consent disclosure closed and keeps it open while it has input", async () => {
    mockApis({ consents: [] });
    renderDetail();
    await screen.findByText("Chưa có bản ghi đồng ý nào cho lớp này.");
    const disclosure = screen.getByText("Ghi nhận sự đồng ý của phụ huynh").closest("details");
    const summary = screen.getByText("Ghi nhận sự đồng ý của phụ huynh").closest("summary");
    if (!disclosure || !summary) throw new Error("consent disclosure not rendered");
    expect(disclosure.open).toBe(false);
    fireEvent.click(summary);
    expect(disclosure.open).toBe(true);
    fireEvent.click(summary);
    expect(disclosure.open).toBe(false);
    fireEvent.click(summary);
    fireEvent.change(await screen.findByLabelText("Mã trẻ"), { target: { value: "real-child" } });
    fireEvent.click(summary);
    expect(disclosure.open).toBe(true);
  });

  it("records a manual child id, labels the pending row, and reloads consent rows", async () => {
    const { consents } = mockApis({ consents: [] });
    consents.mockResolvedValueOnce([]).mockResolvedValueOnce([pendingConsent]);
    const record = vi.spyOn(teacherRosterApi, "recordConsent").mockResolvedValue({ consent_id: pendingConsent.consent_id, state: pendingConsent.state });
    renderDetail();

    await openConsentForm();
    expect((await screen.findByLabelText("Mục đích") as HTMLInputElement).value).toBe("classroom-learning-v1");
    fireEvent.change(screen.getByLabelText("Mã trẻ"), { target: { value: "real-child" } });
    fireEvent.click(screen.getByRole("button", { name: "Ghi nhận sự đồng ý" }));

    await waitFor(() => expect(record).toHaveBeenCalledTimes(1));
    expect(record).toHaveBeenCalledWith("org-test", "k1", {
      childId: "real-child",
      purposeRef: "classroom-learning-v1",
    });
    expect(await screen.findByText("Đã ghi nhận sự đồng ý.")).toBeTruthy();
    expect(await screen.findByText("Đang chờ xác thực, chưa hiệu lực")).toBeTruthy();
    expect((document.body.textContent?.match(/chờ xác thực/g) ?? []).length).toBe(1);
    await waitFor(() => expect(consents).toHaveBeenCalledTimes(2));
    const consentRow = screen.getByText("Học sinh · hild").closest("li");
    expect(consentRow?.textContent).not.toContain("real-child");
    await openConsentForm();
    fireEvent.click(screen.getByRole("combobox", { name: "Chọn trẻ trong danh sách lớp" }));
    expect(screen.getByRole("option", { name: "Synthetic a" })).toBeTruthy();
    expect(screen.queryByRole("option", { name: "Synthetic a · a" })).toBeNull();
    expect(screen.getByRole("button", { name: "Thu hồi sự đồng ý cho Học sinh · hild" })).toBeTruthy();
    expect(screen.getAllByText("Synthetic a").length).toBeGreaterThan(0);
    expect(document.body.textContent).toContain("không làm trẻ xuất hiện trong danh sách lớp");
  });

  it.each([
    ["INVALID_RESPONSE", 502],
    ["PROVIDER_UNAVAILABLE", 503],
    ["NETWORK_ERROR", 0],
  ])("reloads consents and keeps the form after an uncertain %s result", async (code, status) => {
    const { consents } = mockApis({ consents: [] });
    consents.mockResolvedValueOnce([]).mockResolvedValueOnce([{ ...pendingConsent, child_id: "real-child" }]);
    vi.spyOn(teacherRosterApi, "recordConsent").mockRejectedValue(new TeacherRosterApiError("uncertain", code, status));
    renderDetail();

    await openConsentForm();
    const childInput = await screen.findByLabelText("Mã trẻ") as HTMLInputElement;
    fireEvent.change(childInput, { target: { value: "real-child" } });
    fireEvent.click(screen.getByRole("button", { name: "Ghi nhận sự đồng ý" }));

    expect((await screen.findByRole("alert")).textContent).toContain("Đã gửi yêu cầu, hãy kiểm tra danh sách trước khi gửi lại.");
    expect(screen.getByText("Ghi nhận sự đồng ý của phụ huynh").closest("details")?.open).toBe(true);
    expect((screen.getByLabelText("Mã trẻ") as HTMLInputElement).value).toBe("real-child");
    expect(screen.getByRole("alert").textContent).not.toMatch(/thử lại|gửi lại cùng yêu cầu/i);
    expect(await screen.findByText("Học sinh · hild")).toBeTruthy();
    await waitFor(() => expect(consents).toHaveBeenCalledTimes(2));
  });

  it("locks double submits while the record request is pending", async () => {
    mockApis({ consents: [] });
    let resolveRecord: ((value: { consent_id: string; state: string }) => void) | undefined;
    const record = vi.spyOn(teacherRosterApi, "recordConsent").mockImplementation(() => new Promise((resolve) => {
      resolveRecord = resolve;
    }));
    const { container } = renderDetail();
    await openConsentForm();
    fireEvent.change(await screen.findByLabelText("Mã trẻ"), { target: { value: "real-child" } });
    const form = container.querySelector("details[open] form");
    if (!form) throw new Error("consent form not rendered");
    fireEvent.submit(form);
    fireEvent.submit(form);

    expect(record).toHaveBeenCalledTimes(1);
    expect((screen.getByRole("button", { name: "Đang ghi nhận…" }) as HTMLButtonElement).disabled).toBe(true);
    await act(async () => {
      resolveRecord?.({ consent_id: pendingConsent.consent_id, state: pendingConsent.state });
    });
    expect(await screen.findByText("Đã ghi nhận sự đồng ý.")).toBeTruthy();
  });

  it("requires confirmation before revoke and refreshes the consent list", async () => {
    const revoked = { ...pendingConsent, state: "revoked" };
    const { consents } = mockApis({ consents: [pendingConsent] });
    consents.mockResolvedValueOnce([pendingConsent]).mockResolvedValueOnce([revoked]);
    const revoke = vi.spyOn(teacherRosterApi, "revokeConsent").mockResolvedValue({ consent_id: "consent-1", state: "revoked" });
    renderDetail();

    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi sự đồng ý cho Học sinh · hild" }));
    expect(revoke).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận thu hồi sự đồng ý cho Học sinh · hild" }));

    await waitFor(() => expect(revoke).toHaveBeenCalledWith("org-test", "k1", "consent-1"));
    await waitFor(() => expect(consents).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Đã thu hồi")).toBeTruthy();
  });
});

describe("Teacher synthetic profile create (T-7c)", () => {
  it("sends the class revision and one key, and reuses the key only for an unclear failure", async () => {
    mockApis();
    const create = vi.spyOn(teacherRosterApi, "createProfile")
      .mockRejectedValueOnce(new TeacherRosterApiError("Không kết nối được dịch vụ. Hãy thử lại cùng yêu cầu.", "NETWORK_ERROR", 0))
      .mockResolvedValueOnce({ contract: "Be1ManagedProfileV1", child_id: "n", class_id: "k1", enrollment_id: "e", display_name: "Synthetic Na", age_months: 48, data_origin: "SYNTHETIC_DEV", class_revision: 3 });
    renderDetail();
    fireEvent.change(await screen.findByLabelText("Tên hiển thị"), { target: { value: "Synthetic Na" } });
    fireEvent.change(screen.getByLabelText("Tuổi (tháng)"), { target: { value: "48" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo hồ sơ" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    expect(create.mock.calls[0].slice(0, 4)).toEqual(["org-test", "k1", 3, { display_name: "Synthetic Na", age_months: 48 }]);
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][4]).toBe(create.mock.calls[0][4]);
    expect(await screen.findByText(/Đã tạo hồ sơ thử nghiệm/)).toBeTruthy();
    expect(screen.getByText(/Hồ sơ thử nghiệm này có thể xuất hiện trong danh sách lớp/)).toBeTruthy();
  });

  it("blocks a name without the synthetic prefix before sending", async () => {
    mockApis();
    const create = vi.spyOn(teacherRosterApi, "createProfile");
    renderDetail();
    await screen.findByLabelText("Tên hiển thị");
    expect(screen.getByText("Hồ sơ này chỉ dùng để kiểm tra quy trình của lớp, không nhập dữ liệu của trẻ thật. Tên phải bắt đầu đúng bằng “Synthetic ” rồi đến tên hiển thị.")).toBeTruthy();
    expect(screen.getByText("Gõ đúng phần “Synthetic ” ở đầu tên.")).toBeTruthy();
    fireEvent.change(await screen.findByLabelText("Tên hiển thị"), { target: { value: "Minh" } });
    expect(screen.getByText("Tên phải bắt đầu bằng “Synthetic ” rồi có tên hiển thị phía sau.")).toBeTruthy();
    expect(screen.queryByText(/\(synthetic\)/i)).toBeNull();
    expect((screen.getByRole("button", { name: "Tạo hồ sơ" }) as HTMLButtonElement).disabled).toBe(true);
    expect(create).not.toHaveBeenCalled();
  });

  it("reloads after STALE_REVISION and uses a new key for the next action", async () => {
    const { classes } = mockApis();
    const create = vi.spyOn(teacherRosterApi, "createProfile")
      .mockRejectedValueOnce(new TeacherRosterApiError("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", "STALE_REVISION", 409))
      .mockRejectedValueOnce(new TeacherRosterApiError("Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau 12 giây.", "RATE_LIMITED", 429, undefined, 12));
    renderDetail();
    fireEvent.change(await screen.findByLabelText("Tên hiển thị"), { target: { value: "Synthetic Na" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo hồ sơ" }));
    expect((await screen.findByText(/hãy kiểm tra rồi xác nhận lại/)).textContent).toContain("Thông tin đã thay đổi.");
    await waitFor(() => expect(classes.mock.calls.length).toBeGreaterThanOrEqual(2));
    fireEvent.click(await screen.findByRole("button", { name: "Tạo hồ sơ" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][4]).not.toBe(create.mock.calls[0][4]);
    expect(await screen.findByText(/thử lại sau 12 giây/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Gửi lại cùng yêu cầu" })).toBeNull();
  });
});

describe("Teacher enrollment move (T-7d)", () => {
  it("offers only other active classes of the same Teacher and sends both revisions", async () => {
    mockApis({ classes: [klass("k1", "active", 3), klass("k2", "active", 7), klass("k3", "suspended", 2), klass("k4", "active", 5)], teacherClassIds: ["k1", "k2", "k3"] });
    const move = vi.spyOn(teacherRosterApi, "moveProfile").mockResolvedValue({ contract: "Be1ProfileMoveV1", child_id: "a", from_class_id: "k1", to_class_id: "k2", enrollment_id: "e", from_class_revision: 4, to_class_revision: 8 });
    const { container } = renderDetail();
    fireEvent.click(await screen.findByRole("button", { name: "Chuyển lớp" }));
    const select = screen.getByRole("combobox", { name: "Lớp đích" });
    const hiddenSelect = container.querySelector("select.s2l-select-native") as HTMLSelectElement;
    expect(Array.from(hiddenSelect.options).map((option) => option.value)).toEqual(["", "k2"]);
    fireEvent.click(select);
    fireEvent.click(screen.getByRole("option", { name: "Lớp k2" }));
    expect(hiddenSelect.value).toBe("k2");
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận chuyển lớp" }));
    await waitFor(() => expect(move).toHaveBeenCalledTimes(1));
    expect(move.mock.calls[0].slice(0, 4)).toEqual(["k1", 3, "a", { classId: "k2", revision: 7 }]);
    expect(await screen.findByText(/lịch sử lớp trước đó được đóng và lưu lại/)).toBeTruthy();
  });

  it("reloads both classes after a stale refusal", async () => {
    const { classes } = mockApis();
    vi.spyOn(teacherRosterApi, "moveProfile").mockRejectedValue(new TeacherRosterApiError("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", "STALE_REVISION", 409));
    renderDetail();
    fireEvent.click(await screen.findByRole("button", { name: "Chuyển lớp" }));
    fireEvent.click(screen.getByRole("combobox", { name: "Lớp đích" }));
    fireEvent.click(screen.getByRole("option", { name: "Lớp k2" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận chuyển lớp" }));
    expect(await screen.findByText(/hãy kiểm tra rồi xác nhận lại/)).toBeTruthy();
    await waitFor(() => expect(classes.mock.calls.length).toBeGreaterThanOrEqual(2));
  });
});
