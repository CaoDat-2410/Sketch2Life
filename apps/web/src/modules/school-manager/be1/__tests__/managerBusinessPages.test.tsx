import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
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
