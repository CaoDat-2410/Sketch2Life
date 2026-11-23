// Goal v3 Phase B: Teacher class page (T-7a2 server-decided 403/404, T-7b read-only class, T-7c create, T-7d move).
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TeacherApiClassesPage, T05ClassDetailPage } from "../T05ClassesScreen";
import { backendApi, type Be1Class } from "../../../../shared/api/backendApi";
import { NOT_FOUND_OR_NO_ACCESS, TeacherRosterApiError, teacherRosterApi } from "../../../../shared/api/teacherRosterApi";

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
  if (options.profiles instanceof Error) profiles.mockRejectedValue(options.profiles); else profiles.mockResolvedValue((options.profiles as never) ?? [profile("a")]);
  const consents = vi.spyOn(teacherRosterApi, "consents");
  if (options.consents instanceof Error) consents.mockRejectedValue(options.consents); else consents.mockResolvedValue((options.consents as never) ?? [consent("a")]);
  return { classes, profiles, consents };
}

const renderDetail = (classId = "k1") => render(<MemoryRouter><T05ClassDetailPage classId={classId} /></MemoryRouter>);

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = { signIn: vi.fn(async () => undefined), getIdToken: vi.fn(async () => "token-1") } as never;
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
    expect(classes).toHaveBeenCalledWith("org-test", "all");
  });
});

describe("Teacher class page scope (T-7a2)", () => {
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
    expect(await screen.findByText("Synthetic a")).toBeTruthy();
    expect(profiles).toHaveBeenCalledWith("org-test", "k1");
    expect(consents).toHaveBeenCalledWith("org-test", "k1");
    expect(screen.queryByRole("button", { name: "Chuyển lớp" })).toBeNull();
  });

  it("keeps the roster hidden while consent cannot be read", async () => {
    mockApis({ consents: new TeacherRosterApiError("Máy chủ bận.", "PROVIDER_UNAVAILABLE", 503) });
    renderDetail();
    expect(await screen.findByText(/Consent chưa thể xác minh/)).toBeTruthy();
    expect(screen.queryByText("Synthetic a")).toBeNull();
  });

  it("shows a calm locked notice for consent-not-effective", async () => {
    mockApis({ profiles: new TeacherRosterApiError("", "CONSENT_NOT_EFFECTIVE", 403, "corr-locked") });
    renderDetail();
    await screen.findByText("Danh sách hồ sơ tạm khóa đến khi có consent hiệu lực");
    const lockedNotice = screen.getByRole("status");
    expect(lockedNotice.textContent).toContain("Danh sách hồ sơ tạm khóa đến khi có consent hiệu lực");
    expect(lockedNotice.textContent).toContain("Consent chưa được xác minh nên dữ liệu trẻ đang bị khóa.");
    expect(lockedNotice.textContent).toContain("Mã yêu cầu: corr-locked");
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("Teacher read-only suspended class (T-7b)", () => {
  it("shows the read-only copy and offers no create or move", async () => {
    mockApis({ classes: [klass("k1", "suspended"), klass("k2")] });
    renderDetail();
    expect(await screen.findByText("Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.")).toBeTruthy();
    expect(await screen.findByText("Synthetic a")).toBeTruthy();
    expect(screen.queryByText(/Tạo hồ sơ thử nghiệm/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Chuyển lớp" })).toBeNull();
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
  });

  it("blocks a name without the synthetic prefix before sending", async () => {
    mockApis();
    const create = vi.spyOn(teacherRosterApi, "createProfile");
    renderDetail();
    fireEvent.change(await screen.findByLabelText("Tên hiển thị"), { target: { value: "Minh" } });
    expect(screen.getByText(/Tên hồ sơ thử nghiệm phải bắt đầu bằng/)).toBeTruthy();
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
    expect(await screen.findByText(/enrollment trước đó được đóng và lưu lại/)).toBeTruthy();
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
