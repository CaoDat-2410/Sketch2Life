import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminBe1Error } from "../services/be1Client";
import { ClassesPage } from "../pages/ClassesPage";
import { ParentGroupsPage } from "../pages/ParentGroupsPage";
import { RosterConsentPage } from "../pages/RosterConsentPage";
import { SchoolOverviewPage } from "../pages/SchoolOverviewPage";
import { classService } from "../services/classService";
import { managerBusinessService } from "../services/managerBusinessService";
import { authService } from "../services/authService";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  window.sessionStorage.clear();
});

describe("School Manager SRS-compatible business pages", () => {
  it("shows the organization name returned by the backend", async () => {
    vi.spyOn(managerBusinessService, "organization").mockResolvedValue({
      contract: "Be1OrganizationV1",
      organization_id: "org-qa",
      display_name: "Sketch2Life Manager QA",
    });

    render(<MemoryRouter><SchoolOverviewPage /></MemoryRouter>);

    expect(await screen.findByText("Sketch2Life Manager QA")).toBeTruthy();
    expect(screen.queryByText("org-qa")).toBeNull();
  });

  it("shows the T-7a count summary and consent rows without child names, ids or purposes", async () => {
    const list = vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-1", display_name: "Lớp Lá 1", state: "active", class_revision: 1 },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({
      contract: "Be1ClassRosterSummaryV1", class_id: "class-1", active_profile_count: 7,
    });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-1", state: "pending", effective: false },
    ]);

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByText(/hồ sơ đang hoạt động trong lớp/)).textContent).toContain("7");
    expect((await screen.findAllByText("Đang chờ xác nhận")).length).toBeGreaterThan(0);
    expect(screen.queryByText("Hiệu lực")).toBeNull();
    expect(list).toHaveBeenCalledWith("all");
    expect(container.textContent).not.toContain("Mục đích");
    expect(container.textContent).not.toContain("child-");
    expect(container.querySelector(".manager-business-profile-list")).toBeNull();
    expect(container.querySelector("img, video, audio")).toBeNull();
  });

  it("keeps the consent list visible and labels unknown states neutrally", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-unknown", display_name: "Lớp Mầm", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-unknown", active_profile_count: 0 });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-future", state: "unknown", effective: false },
    ]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect(await screen.findByText("Trạng thái không xác định")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("confirms a blind permanent consent revoke, locks repeats, and reloads the list", async () => {
    const pending = { consent_id: "consent-1", state: "pending" as const, effective: false as const };
    const revoked = { consent_id: "consent-1", state: "revoked" as const, effective: false as const };
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-1", display_name: "Lớp Lá", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-1", active_profile_count: 1 });
    const consents = vi.spyOn(managerBusinessService, "consents").mockResolvedValueOnce([pending]).mockResolvedValueOnce([revoked]);
    let resolveRevoke!: (value: { contract: "Be1ConsentV1"; consent_id: string; state: "revoked"; effective: false }) => void;
    const revokeResult = new Promise<{ contract: "Be1ConsentV1"; consent_id: string; state: "revoked"; effective: false }>((resolve) => { resolveRevoke = resolve; });
    const revoke = vi.spyOn(managerBusinessService, "revokeConsent").mockReturnValue(revokeResult);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi bản ghi 1" }));
    const dialog = screen.getByRole("alertdialog");
    expect(dialog.textContent).toContain("không thể xác định bản ghi thuộc trẻ nào");
    expect(dialog.textContent).toContain("vĩnh viễn");

    const confirmButton = screen.getByRole("button", { name: "Xác nhận thu hồi" });
    fireEvent.click(confirmButton);
    fireEvent.click(confirmButton);
    expect(revoke).toHaveBeenCalledTimes(1);
    expect(revoke).toHaveBeenCalledWith("class-1", "consent-1");
    expect(await screen.findByText("Đang thu hồi bản ghi…")).toBeTruthy();

    resolveRevoke({ contract: "Be1ConsentV1", consent_id: "consent-1", state: "revoked", effective: false });
    expect(await screen.findByText("Đã thu hồi bản ghi.")).toBeTruthy();
    expect((await screen.findAllByText("Đã thu hồi")).length).toBeGreaterThan(0);
    expect(consents).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: /Thu hồi bản ghi/ })).toBeNull();
  });

  it("hides revoke for rows that are already revoked", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-2", display_name: "Lớp Chồi", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-2", active_profile_count: 0 });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-2", state: "revoked", effective: false },
    ]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findAllByText("Đã thu hồi")).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Thu hồi bản ghi/ })).toBeNull();
  });

  it("reloads after a missing consent and uses safe 404 copy", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-3", display_name: "Lớp Mầm", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-3", active_profile_count: 0 });
    const consents = vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-3", state: "pending", effective: false },
    ]);
    vi.spyOn(managerBusinessService, "revokeConsent").mockRejectedValue(new AdminBe1Error("raw body", 404, "CONSENT_NOT_FOUND"));

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi bản ghi 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận thu hồi" }));

    expect(await screen.findByText("Không tìm thấy bản ghi")).toBeTruthy();
    expect(consents).toHaveBeenCalledTimes(2);
    expect(document.body.textContent).not.toContain("raw body");
    expect(document.body.textContent).not.toContain("CONSENT_NOT_FOUND");
  });

  it("reloads consent rows after an invalid success response", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-invalid", display_name: "Lớp Chồi", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-invalid", active_profile_count: 0 });
    const consents = vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-invalid", state: "pending", effective: false },
    ]);
    vi.spyOn(managerBusinessService, "revokeConsent").mockRejectedValue(new AdminBe1Error("bad response", 502, "INVALID_RESPONSE"));

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi bản ghi 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận thu hồi" }));

    expect(await screen.findByText("Không thể thu hồi bản ghi. Hãy tải lại danh sách.")).toBeTruthy();
    await waitFor(() => expect(consents).toHaveBeenCalledTimes(2));
  });

  it("shows roster denial separately while retaining the consent response", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-2", display_name: "Lớp Chồi", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockRejectedValue(new Error("Consent chưa hiệu lực."));
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-2", state: "pending", effective: false },
    ]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect(await screen.findByRole("alert")).toBeTruthy();
    await waitFor(() => expect(screen.getAllByText("Đang chờ xác nhận").length).toBeGreaterThan(0));
  });

  it("shows the roster-specific copy on 403 ACTION_NOT_ALLOWED, keeps consent and does not log out", async () => {
    const logout = vi.fn();
    window.addEventListener("storage", logout);
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-3", display_name: "Lớp Mầm", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockRejectedValue(
      new AdminBe1Error("Không có quyền.", 403, "ACTION_NOT_ALLOWED"),
    );
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-3", state: "pending", effective: false },
    ]);

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Bạn không có quyền xem hồ sơ trẻ trong lớp này.");
    expect(screen.getAllByText("Đang chờ xác nhận").length).toBeGreaterThan(0);
    expect(container.querySelectorAll("tbody tr").length).toBeGreaterThan(0);
    expect(screen.queryByText(/hồ sơ đang hoạt động/)).toBeNull();
    expect(logout).not.toHaveBeenCalled();
    window.removeEventListener("storage", logout);
  });

  it("keeps the server message for other roster errors", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-4", display_name: "Lớp Lá", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockRejectedValue(new AdminBe1Error("Máy chủ bận.", 503, "UNAVAILABLE"));
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Máy chủ bận.");
  });

  it("labels a suspended class as read-only and does not offer a Teacher assignment", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-5", display_name: "Lớp Hoa", state: "suspended", class_revision: 3, assignment_revision: 1, has_active_teacher: false },
    ]);
    const candidates = vi.spyOn(classService, "listTeacherCandidates");
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-5", active_profile_count: 0 });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect(await screen.findByText(/Tạm ngưng · Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ./)).toBeTruthy();
    expect(await screen.findByText(/không thể thay đổi giáo viên phụ trách/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Phân công" })).toBeNull();
    expect(candidates).not.toHaveBeenCalled();
  });

  it("shows the roster-specific copy on 403 ACTION_NOT_ALLOWED, keeps consent and does not log out", async () => {
    const logout = vi.fn();
    window.addEventListener("storage", logout);
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-3", display_name: "Lớp Mầm", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockRejectedValue(
      new AdminBe1Error("Không có quyền.", 403, "ACTION_NOT_ALLOWED"),
    );
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-3", state: "pending", effective: false },
    ]);

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Bạn không có quyền xem hồ sơ trẻ trong lớp này.");
    expect(screen.getAllByText("Đang chờ xác nhận").length).toBeGreaterThan(0);
    expect(container.querySelectorAll("tbody tr").length).toBeGreaterThan(0);
    expect(screen.queryByText(/hồ sơ đang hoạt động/)).toBeNull();
    expect(logout).not.toHaveBeenCalled();
    window.removeEventListener("storage", logout);
  });

  it("keeps the server message for other roster errors", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-4", display_name: "Lớp Lá", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockRejectedValue(new AdminBe1Error("Máy chủ bận.", 503, "UNAVAILABLE"));
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Máy chủ bận.");
  });

  it("labels a suspended class as read-only and does not offer a Teacher assignment", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-5", display_name: "Lớp Hoa", state: "suspended", class_revision: 3, assignment_revision: 1, has_active_teacher: false },
    ]);
    const candidates = vi.spyOn(classService, "listTeacherCandidates");
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({ contract: "Be1ClassRosterSummaryV1", class_id: "class-5", active_profile_count: 0 });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([]);

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect(await screen.findByText(/Tạm ngưng · Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ./)).toBeTruthy();
    expect(await screen.findByText(/không thể thay đổi giáo viên phụ trách/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Phân công" })).toBeNull();
    expect(candidates).not.toHaveBeenCalled();
  });

  it("creates a parent group with an idempotency key after explicit submit", async () => {
    vi.stubGlobal("crypto", { randomUUID: () => "parent-group-request-1" });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({
      contract: "ParentGroupPageV1",
      items: [],
      next_cursor: null,
    });
    vi.spyOn(managerBusinessService, "createParentGroup").mockResolvedValue({
      contract: "ParentGroupV1",
      parent_group_id: "group-1",
      organization_id: "org-qa",
      display_name: "Phụ huynh lớp Lá",
      state: "ACTIVE",
      created_at: "2026-11-17T00:00:00Z",
    });

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Tên nhóm phụ huynh"), {
      target: { value: "Phụ huynh lớp Lá" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tạo nhóm" }));

    await waitFor(() => {
      expect(managerBusinessService.createParentGroup).toHaveBeenCalledWith(
        "Phụ huynh lớp Lá",
        "parent-group-request-1",
      );
    });
    expect(await screen.findByText(/Đã tạo nhóm/)).toBeTruthy();
  });

  it("creates a class after explicit submit and sends one idempotency key", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([]);
    const create = vi.spyOn(classService, "createClass").mockResolvedValue({
      contract: "Be1ClassV1", class_id: "class-new", display_name: "Lớp Lá", state: "active", assignment_revision: 1,
    });

    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    expect(screen.queryByText(/chưa kiểm tra giới hạn sức chứa/)).toBeNull();
    fireEvent.change(screen.getByLabelText("Tên lớp"), { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));

    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    expect(create.mock.calls[0][0]).toBe("Lớp Lá");
    expect(create.mock.calls[0][1]).toBeTruthy();
    expect(await screen.findByText(/Đã tạo lớp/)).toBeTruthy();
  });

  it("shows the capacity-reached response with a link to the capacity page", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([]);
    const create = vi.spyOn(classService, "createClass").mockRejectedValue(
      new AdminBe1Error("CLASS_CAPACITY_REACHED class-private-id", 409, "CLASS_CAPACITY_REACHED"),
    );

    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Tên lớp"), { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Tổ chức đã đạt giới hạn số lớp hiện tại.");
    expect(alert.textContent).not.toContain("CLASS_CAPACITY_REACHED");
    expect(alert.textContent).not.toContain("class-private-id");
    expect(screen.getByRole("link", { name: "Xem sức chứa" }).getAttribute("href")).toBe("/school/capacity");
    expect(create).toHaveBeenCalledOnce();
  });

  it("retries a failed create with the same key, and uses a new key when the name changes", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([]);
    const create = vi.spyOn(classService, "createClass")
      .mockRejectedValueOnce(new AdminBe1Error("Không kết nối được dịch vụ.", 0, "NETWORK_ERROR"))
      .mockRejectedValueOnce(new AdminBe1Error("Không kết nối được dịch vụ.", 0, "NETWORK_ERROR"))
      .mockResolvedValueOnce({ contract: "Be1ClassV1", class_id: "class-new", display_name: "Lớp Hoa", state: "active", assignment_revision: 1 });
    const user = { uid: "manager-one" } as never;
    vi.stubEnv("VITE_BE1_ORGANIZATION_ID", "org-qa");
    vi.spyOn(authService, "getCurrentUser").mockReturnValue(user);
    vi.spyOn(authService, "observe").mockImplementation((callback) => { callback(user); return () => undefined; });

    const firstView = render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    const input = await screen.findByLabelText("Tên lớp");
    fireEvent.change(input, { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    const retryKey = await waitFor(() => {
      expect(create).toHaveBeenCalledTimes(1);
      return create.mock.calls[0][1];
    });
    firstView.unmount();

    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    const restoredInput = await screen.findByLabelText("Tên lớp") as HTMLInputElement;
    expect(restoredInput.value).toBe("Lớp Lá");
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][1]).toBe(retryKey);

    await screen.findAllByRole("alert");
    fireEvent.change(restoredInput, { target: { value: "Lớp Hoa" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(3));
    expect(create.mock.calls[2][1]).not.toBe(create.mock.calls[0][1]);
    expect((screen.getByLabelText("Tên lớp") as HTMLInputElement).value).toBe("");
    expect(Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) ?? "")
      .some((key) => key.startsWith("sketch2life:session-draft:v1:school-manager%3Aclass-create"))).toBe(false);
  });

  it("shows the server refusal of a create and does not reuse its key for the next action", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([]);
    const create = vi.spyOn(classService, "createClass")
      .mockRejectedValueOnce(new AdminBe1Error("Tài khoản không được phép thực hiện thao tác này.", 403, "ACTION_NOT_ALLOWED"))
      .mockResolvedValueOnce({ contract: "Be1ClassV1", class_id: "class-new", display_name: "Lớp Lá", state: "active", assignment_revision: 1 });

    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Tên lớp"), { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    expect((await screen.findAllByRole("alert")).map((item) => item.textContent).join(" ")).toContain("không được phép");
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][1]).not.toBe(create.mock.calls[0][1]);
  });
});

describe("Parent group memberships", () => {
  const group = {
    contract: "ParentGroupV1" as const,
    parent_group_id: "group-1",
    organization_id: "org-qa",
    display_name: "Nhóm Lá",
    state: "ACTIVE" as const,
    created_at: "2026-11-17T00:00:00Z",
  };
  const member = (state: "INVITED" | "ACCEPTED" | "REVOKED" = "INVITED", revision = 7) => ({
    membership_id: "membership-123456789",
    parent_group_id: "group-1",
    state,
    invited_at: "2026-11-20T00:00:00Z",
    expires_at: "2026-11-21T00:00:00Z",
    accepted_at: state === "ACCEPTED" ? "2026-11-20T01:00:00Z" : null,
    revision,
  });
  const memberPage = (items: ReturnType<typeof member>[], nextCursor: string | null = null) => ({
    contract: "ParentGroupMemberListV1",
    items,
    counts: { invited: 4, accepted: 3, declined: 2, revoked: 1, expired: 5, total: 15 },
    next_cursor: nextCursor,
  });

  const invitation = {
    contract: "ParentGroupMembershipV1",
    membership_id: "membership-invited",
    parent_group_id: "group-1",
    state: "INVITED" as const,
    invited_at: "2026-11-25T10:00:00Z",
    expires_at: "2026-12-25T10:00:00Z",
    accepted_at: null,
    revision: 1,
  };

  it("shows all-state counts from the first page and sends the Manager state filter on later pages", async () => {
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    const listMembers = vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([member()], "cursor-2"));
    const { container } = render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    const counts = await screen.findByLabelText("Số lượng thành viên theo trạng thái");
    expect(counts.textContent).toContain("15");
    expect(counts.textContent).toContain("4");
    expect(container.textContent).toContain("Hết hạn");
    expect(container.textContent).not.toContain("INVITED");
    expect(container.textContent).not.toContain("membership-123456789");
    expect(listMembers).toHaveBeenCalledWith("group-1", { state: undefined, cursor: undefined, signal: undefined });

    fireEvent.change(screen.getByLabelText("Lọc trạng thái"), { target: { value: "ACCEPTED" } });
    await waitFor(() => expect(listMembers).toHaveBeenCalledTimes(2));
    expect(listMembers).toHaveBeenLastCalledWith("group-1", { state: "ACCEPTED", cursor: undefined, signal: undefined });
    fireEvent.click(await screen.findByRole("button", { name: "Tải thêm phụ huynh" }));
    await waitFor(() => expect(listMembers).toHaveBeenCalledTimes(3));
    expect(listMembers).toHaveBeenLastCalledWith("group-1", { state: "ACCEPTED", cursor: "cursor-2", signal: undefined });
  });

  it("renders accepted membership state in Vietnamese", async () => {
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([member("ACCEPTED")]));
    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    expect(await screen.findByText("Đã chấp nhận")).toBeTruthy();
    expect(screen.queryByText("ACCEPTED")).toBeNull();
  });

  it("renders active invited membership state in Vietnamese", async () => {
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(
      memberPage([{ ...member("INVITED"), expires_at: "2027-01-01T00:00:00Z" }]),
    );
    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    expect(await screen.findByText("Đã mời")).toBeTruthy();
    expect(screen.queryByText("INVITED")).toBeNull();
  });

  it("invites the typed Parent ref, shows the expiry date, and reloads members and counts", async () => {
    vi.stubGlobal("crypto", { randomUUID: () => "manager-invite-key" });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    const refreshedPage = {
      ...memberPage([member()]),
      counts: { invited: 5, accepted: 3, declined: 2, revoked: 1, expired: 5, total: 16 },
    };
    const members = vi.spyOn(managerBusinessService, "parentGroupMembers")
      .mockResolvedValueOnce(memberPage([]))
      .mockResolvedValueOnce(refreshedPage);
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup").mockResolvedValue(invitation);

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    const input = await screen.findByLabelText("Mã tài khoản phụ huynh") as HTMLTextAreaElement;
    expect(screen.getByText("Không tra cứu bằng email. Nhập một mã mỗi dòng; dấu phẩy, chấm phẩy hoặc khoảng trắng cũng được tính là dấu ngăn cách.")).toBeTruthy();
    fireEvent.change(input, { target: { value: "parent:opaque-ref" } });
    fireEvent.click(screen.getByRole("button", { name: "Mời phụ huynh" }));

    await waitFor(() => expect(invite).toHaveBeenCalledWith("group-1", "parent:opaque-ref", "manager-invite-key"));
    expect(await screen.findByText(`Đã gửi lời mời · Hết hạn ngày ${new Date(invitation.expires_at).toLocaleDateString("vi-VN")}`)).toBeTruthy();
    await waitFor(() => expect(members).toHaveBeenCalledTimes(2));
    expect(members).toHaveBeenLastCalledWith("group-1", { state: "INVITED", cursor: undefined, signal: undefined });
    expect(screen.getByLabelText("Số lượng thành viên theo trạng thái").textContent).toContain("16");
    expect(input.value).toBe("");
  });

  it("reuses an invitation key for retry and creates a new key after the ref changes", async () => {
    let minted = 0;
    vi.stubGlobal("crypto", { randomUUID: () => `manager-invite-${++minted}` });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([]));
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup")
      .mockRejectedValueOnce(new AdminBe1Error("Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.", 503, "PROVIDER_UNAVAILABLE", undefined, true))
      .mockRejectedValueOnce(new AdminBe1Error("Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.", 503, "PROVIDER_UNAVAILABLE", undefined, true))
      .mockResolvedValueOnce(invitation);

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    const input = await screen.findByLabelText("Mã tài khoản phụ huynh") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "parent:first" } });
    fireEvent.click(screen.getByRole("button", { name: "Mời phụ huynh" }));
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(invite).toHaveBeenCalledTimes(2));
    fireEvent.change(input, { target: { value: "parent:second" } });
    fireEvent.click(screen.getByRole("button", { name: "Mời phụ huynh" }));

    await waitFor(() => expect(invite).toHaveBeenCalledTimes(3));
    expect(invite.mock.calls).toEqual([
      ["group-1", "parent:first", "manager-invite-1"],
      ["group-1", "parent:first", "manager-invite-1"],
      ["group-1", "parent:second", "manager-invite-2"],
    ]);
    expect(await screen.findByText(/^Đã gửi lời mời · Hết hạn ngày/)).toBeTruthy();
  });

  it("disables Parent invitation for archived groups and while a request is pending", async () => {
    const archivedGroup = { ...group, state: "ARCHIVED" as const };
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [archivedGroup], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([]));
    const invite = vi.spyOn(managerBusinessService, "inviteParentToGroup");

    const { unmount } = render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    const archivedInput = await screen.findByLabelText("Mã tài khoản phụ huynh") as HTMLTextAreaElement;
    expect(archivedInput.disabled).toBe(true);
    expect(screen.getByRole("button", { name: "Mời phụ huynh" }).hasAttribute("disabled")).toBe(true);
    expect(screen.getByText("Nhóm đã lưu trữ; không thể mời thành viên.")).toBeTruthy();
    expect(invite).not.toHaveBeenCalled();
    unmount();

    vi.restoreAllMocks();
    const activeGroups = vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    const activeMembers = vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([]));
    let finishInvite!: (value: typeof invitation) => void;
    const pendingInvite = new Promise<typeof invitation>((resolve) => { finishInvite = resolve; });
    const pendingService = vi.spyOn(managerBusinessService, "inviteParentToGroup").mockReturnValue(pendingInvite);

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    const activeInput = await screen.findByLabelText("Mã tài khoản phụ huynh") as HTMLTextAreaElement;
    fireEvent.change(activeInput, { target: { value: "parent:opaque-ref" } });
    fireEvent.click(screen.getByRole("button", { name: "Mời phụ huynh" }));
    await waitFor(() => expect(pendingService).toHaveBeenCalledOnce());
    expect(activeInput.disabled).toBe(true);
    expect(screen.getByRole("button", { name: "Đang gửi lời mời…" }).hasAttribute("disabled")).toBe(true);
    finishInvite(invitation);
    expect(await screen.findByText(/^Đã gửi lời mời · Hết hạn ngày/)).toBeTruthy();
    expect(activeGroups).toHaveBeenCalled();
    expect(activeMembers).toHaveBeenCalledTimes(2);
  });

  it("confirms revocation, sends the listed revision, and refreshes counts after a stale revision", async () => {
    vi.stubGlobal("crypto", { randomUUID: () => "manager-revoke-key" });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    const members = vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([member()]));
    const revoke = vi.spyOn(managerBusinessService, "revokeParentGroupMember").mockRejectedValue(new AdminBe1Error("Danh sách đã thay đổi. Hãy tải lại số lượng và thử lại.", 409, "STALE_REVISION"));

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi lời mời" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Thu hồi lời mời của Phụ huynh 1?" })).toBeTruthy();
    expect(within(dialog).getByText("Lời mời này sẽ không còn hiệu lực.")).toBeTruthy();
    expect(revoke).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Thu hồi lời mời" }));

    expect((await screen.findByRole("alert")).textContent).toContain("Danh sách đã thay đổi. Hãy tải lại số lượng và thử lại.");
    expect(revoke).toHaveBeenCalledWith("group-1", "membership-123456789", 7, "manager-revoke-key");
    await waitFor(() => expect(members).toHaveBeenCalledTimes(2));
    expect(await screen.findByLabelText("Số lượng thành viên theo trạng thái")).toBeTruthy();
  });

  it("cancels member revocation without sending a request", async () => {
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers").mockResolvedValue(memberPage([member()]));
    const revoke = vi.spyOn(managerBusinessService, "revokeParentGroupMember");

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi lời mời" }));

    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Hủy" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(revoke).not.toHaveBeenCalled();
  });

  it("closes the member revocation dialog if the member revision changes during an in-flight refresh", async () => {
    let resolveRefresh!: (value: ReturnType<typeof memberPage>) => void;
    const refreshPromise = new Promise<ReturnType<typeof memberPage>>((resolve) => { resolveRefresh = resolve; });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers")
      .mockResolvedValueOnce(memberPage([member("ACCEPTED", 7)]))
      .mockReturnValueOnce(refreshPromise);
    const revoke = vi.spyOn(managerBusinessService, "revokeParentGroupMember");

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    const revokeButton = await screen.findByRole("button", { name: "Thu hồi thành viên" });
    const refreshButtons = screen.getAllByRole("button", { name: "Làm mới" });
    fireEvent.click(refreshButtons[refreshButtons.length - 1]);
    fireEvent.click(revokeButton);
    expect(screen.getByRole("dialog")).toBeTruthy();

    resolveRefresh(memberPage([member("ACCEPTED", 8)]));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(revoke).not.toHaveBeenCalled();
  });

  it("reuses the revoke key after a retryable failure", async () => {
    let keyIndex = 0;
    vi.stubGlobal("crypto", { randomUUID: () => `manager-revoke-${++keyIndex}` });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue({ contract: "ParentGroupPageV1", items: [group], next_cursor: null });
    vi.spyOn(managerBusinessService, "parentGroupMembers")
      .mockResolvedValueOnce(memberPage([member()]))
      .mockResolvedValueOnce(memberPage([member("REVOKED", 8)]));
    const revoke = vi.spyOn(managerBusinessService, "revokeParentGroupMember")
      .mockRejectedValueOnce(new AdminBe1Error("raw message", 503, "PROVIDER_UNAVAILABLE", undefined, true))
      .mockResolvedValueOnce(member("REVOKED", 8));

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /Nhóm Lá/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Thu hồi lời mời" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Thu hồi lời mời" }));
    fireEvent.click(await screen.findByRole("button", { name: "Thử lại: Thu hồi lời mời" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Thu hồi lời mời" }));

    await waitFor(() => expect(revoke).toHaveBeenCalledTimes(2));
    expect(revoke.mock.calls[0]).toEqual(["group-1", "membership-123456789", 7, "manager-revoke-1"]);
    expect(revoke.mock.calls[1]).toEqual(["group-1", "membership-123456789", 7, "manager-revoke-1"]);
  });
});

describe("Parent groups paging and idempotency key retry", () => {
  const group = (id: string) => ({
    contract: "ParentGroupV1" as const,
    parent_group_id: id,
    organization_id: "org-qa",
    display_name: "Nhóm " + id,
    state: "ACTIVE" as const,
    created_at: "2026-11-17T00:00:00Z",
  });
  const page = (items: ReturnType<typeof group>[], next: string | null) => ({
    contract: "ParentGroupPageV1" as const,
    items,
    next_cursor: next,
  });

  it("follows next_cursor forward and back without assuming a page size", async () => {
    const list = vi.spyOn(managerBusinessService, "parentGroups").mockImplementation(async (cursor) =>
      cursor === "c2" ? page([group("g2")], null) : page([group("g1")], "c2"),
    );

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);

    expect(await screen.findByText(/Nhóm g1/)).toBeTruthy();
    expect(list).toHaveBeenNthCalledWith(1, undefined, expect.anything());
    const next = screen.getByRole("button", { name: /Tiếp/ });
    await waitFor(() => expect(next.hasAttribute("disabled")).toBe(false));
    fireEvent.click(next);
    expect(await screen.findByText(/Nhóm g2/)).toBeTruthy();
    expect(list).toHaveBeenLastCalledWith("c2", expect.anything());
    await waitFor(() => expect(screen.getByRole("button", { name: /Tiếp/ }).hasAttribute("disabled")).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: /Trước/ }));
    expect(await screen.findByText(/Nhóm g1/)).toBeTruthy();
    expect(list).toHaveBeenLastCalledWith(undefined, expect.anything());
  });

  it("keeps the key after an unknown outcome and clears it after a 4xx or a success", async () => {
    let minted = 0;
    vi.stubGlobal("crypto", { randomUUID: () => "key-" + ++minted });
    vi.spyOn(managerBusinessService, "parentGroups").mockResolvedValue(page([], null));
    const create = vi.spyOn(managerBusinessService, "createParentGroup")
      .mockRejectedValueOnce(new Error("Mất kết nối"))
      .mockRejectedValueOnce(new AdminBe1Error("Khóa yêu cầu trùng.", 400, "INVALID_IDEMPOTENCY_KEY"))
      .mockRejectedValueOnce(new Error("Mất kết nối"))
      .mockResolvedValueOnce({ ...group("g9"), display_name: "Lớp Lá" })
      .mockRejectedValueOnce(new Error("Mất kết nối"));
    const nameInputEnabled = async () => {
      const input = await screen.findByLabelText("Tên nhóm phụ huynh");
      await waitFor(() => expect(input.hasAttribute("disabled")).toBe(false));
      return input;
    };

    render(<MemoryRouter><ParentGroupsPage /></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Tên nhóm phụ huynh"), { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo nhóm" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    expect(create.mock.calls[0]).toEqual(["Lớp Lá", "key-1"]);

    // An unknown outcome keeps the key: the same request is offered again with the same key.
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1]).toEqual(["Lớp Lá", "key-1"]);

    // That retry was rejected with a 4xx, which clears the key: the next submit mints a new one.
    fireEvent.click(await screen.findByRole("button", { name: "Tạo nhóm" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(3));
    expect(create.mock.calls[2]).toEqual(["Lớp Lá", "key-2"]);

    // The key kept after the new unknown outcome is used again, and this retry succeeds.
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(4));
    expect(create.mock.calls[3]).toEqual(["Lớp Lá", "key-2"]);
    expect(await screen.findByText(/Đã tạo nhóm/)).toBeTruthy();

    // The success cleared the key: a new group gets a new key.
    fireEvent.change(await nameInputEnabled(), { target: { value: "Lớp Chồi" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo nhóm" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(5));
    expect(create.mock.calls[4]).toEqual(["Lớp Chồi", "key-3"]);
    expect(minted).toBe(3);
  });
});
