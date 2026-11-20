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

  it("loads roster and consent independently and never renders the child opaque ID", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-1", display_name: "Lớp Lá 1", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "profiles").mockResolvedValue({
      contract: "Be1ClassProfilePageV1",
      items: [{ child_id: "child-opaque-secret", class_id: "class-1", display_name: "Minh Anh", age_months: 72 }],
    });
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue({
      contract: "Be1ClassConsentPageV1",
      items: [{ consent_id: "consent-1", child_id: "child-opaque-secret", purpose_ref: "story_generation", state: "ACTIVE", effective: true }],
    });

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect(await screen.findByText("Minh Anh")).toBeTruthy();
    expect(await screen.findByText("Có")).toBeTruthy();
    expect(container.textContent).not.toContain("child-opaque-secret");
    expect(container.querySelector("img, video, audio")).toBeNull();
  });

  it("shows roster denial separately while retaining the consent response", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-2", display_name: "Lớp Chồi", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "profiles").mockRejectedValue(new Error("Consent chưa hiệu lực."));
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue({
      contract: "Be1ClassConsentPageV1",
      items: [{ consent_id: "consent-2", child_id: "child-opaque", purpose_ref: "story_generation", state: "PENDING", effective: false }],
    });

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(await screen.findByText("Đang chờ xác nhận")).toBeTruthy();
    expect(screen.queryByText("child-opaque")).toBeNull();
  });

  it("shows the roster-specific copy on 403 ACTION_NOT_ALLOWED, clears rows, keeps consent and does not log out", async () => {
    const logout = vi.fn();
    window.addEventListener("storage", logout);
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-3", display_name: "Lớp Mầm", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "profiles").mockRejectedValue(
      new AdminBe1Error("Không có quyền.", 403, "ACTION_NOT_ALLOWED"),
    );
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue({
      contract: "Be1ClassConsentPageV1",
      items: [{ consent_id: "consent-3", child_id: "child-opaque", purpose_ref: "story_generation", state: "ACTIVE", effective: true }],
    });

    const { container } = render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Bạn không có quyền xem hồ sơ trẻ trong lớp này.");
    expect(await screen.findByText("Đã ghi nhận")).toBeTruthy();
    expect(container.querySelectorAll("tbody tr").length).toBeGreaterThan(0);
    expect(screen.queryByText("Minh Anh")).toBeNull();
    expect(logout).not.toHaveBeenCalled();
    window.removeEventListener("storage", logout);
  });

  it("keeps the server message for other roster errors", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([
      { class_id: "class-4", display_name: "Lớp Lá", state: "active" },
    ]);
    vi.spyOn(managerBusinessService, "profiles").mockRejectedValue(new AdminBe1Error("Máy chủ bận.", 503, "UNAVAILABLE"));
    vi.spyOn(managerBusinessService, "consents").mockResolvedValue({ contract: "Be1ClassConsentPageV1", items: [] });

    render(<MemoryRouter><RosterConsentPage /></MemoryRouter>);

    expect((await screen.findByRole("alert")).textContent).toContain("Máy chủ bận.");
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

  it("keeps class creation unavailable while capacity is not enforced", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([]);
    vi.spyOn(classService, "createClass");

    render(<MemoryRouter><ClassesPage /></MemoryRouter>);

    expect(await screen.findByText(/API hiện chưa kiểm tra giới hạn capacity/)).toBeTruthy();
    expect(classService.createClass).not.toHaveBeenCalled();
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
