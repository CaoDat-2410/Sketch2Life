import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminBe1Error } from "../services/be1Client";
import { ClassesPage } from "../pages/ClassesPage";
import { ParentGroupsPage } from "../pages/ParentGroupsPage";
import { RosterConsentPage } from "../pages/RosterConsentPage";
import { SchoolOverviewPage } from "../pages/SchoolOverviewPage";
import { classService } from "../services/classService";
import { managerBusinessService } from "../services/managerBusinessService";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
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
    expect(screen.getByText("org-qa")).toBeTruthy();
  });

  it("shows the T-7a count summary and consent rows without child names, ids or purposes", async () => {
    const list = vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-1", display_name: "Lớp Lá 1", state: "active", class_revision: 1 },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockResolvedValue({
      contract: "Be1ClassRosterSummaryV1", class_id: "class-1", active_profile_count: 7,
    });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-1", state: "ACTIVE", effective: true },
    ]);

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByText(/hồ sơ đang hoạt động trong lớp/)).textContent).toContain("7");
    expect(await screen.findByText("Có")).toBeTruthy();
    expect(list).toHaveBeenCalledWith("all");
    expect(container.textContent).not.toContain("Mục đích");
    expect(container.textContent).not.toContain("child-");
    expect(container.querySelector(".manager-business-profile-list")).toBeNull();
    expect(container.querySelector("img, video, audio")).toBeNull();
  });

  it("shows roster denial separately while retaining the consent response", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-2", display_name: "Lớp Chồi", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "rosterSummary").mockRejectedValue(new Error("Consent chưa hiệu lực."));
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue([
      { consent_id: "consent-2", state: "PENDING", effective: false },
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
      { consent_id: "consent-3", state: "ACTIVE", effective: true },
    ]);

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Bạn không có quyền xem hồ sơ trẻ trong lớp này.");
    expect(screen.getAllByText("Đã ghi nhận").length).toBeGreaterThan(1);
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
    expect(await screen.findByText(/không thể phân công Teacher/)).toBeTruthy();
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
      { consent_id: "consent-3", state: "ACTIVE", effective: true },
    ]);

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Bạn không có quyền xem hồ sơ trẻ trong lớp này.");
    expect(await screen.findByText("Đã ghi nhận")).toBeTruthy();
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
    expect(await screen.findByText(/không thể phân công Teacher/)).toBeTruthy();
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
    expect(await screen.findByText(/chưa kiểm tra giới hạn sức chứa/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Tên lớp"), { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));

    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    expect(create.mock.calls[0][0]).toBe("Lớp Lá");
    expect(create.mock.calls[0][1]).toBeTruthy();
    expect(await screen.findByText(/Đã tạo lớp/)).toBeTruthy();
  });

  it("retries a failed create with the same key, and uses a new key when the name changes", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([]);
    const create = vi.spyOn(classService, "createClass")
      .mockRejectedValueOnce(new AdminBe1Error("Không kết nối được dịch vụ.", 0, "NETWORK_ERROR"))
      .mockRejectedValueOnce(new AdminBe1Error("Không kết nối được dịch vụ.", 0, "NETWORK_ERROR"))
      .mockResolvedValueOnce({ contract: "Be1ClassV1", class_id: "class-new", display_name: "Lớp Hoa", state: "active", assignment_revision: 1 });

    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    const input = await screen.findByLabelText("Tên lớp");
    fireEvent.change(input, { target: { value: "Lớp Lá" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    fireEvent.click(await screen.findByRole("button", { name: "Gửi lại cùng yêu cầu" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][1]).toBe(create.mock.calls[0][1]);

    await screen.findAllByRole("alert");
    fireEvent.change(input, { target: { value: "Lớp Hoa" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo lớp" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(3));
    expect(create.mock.calls[2][1]).not.toBe(create.mock.calls[0][1]);
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
