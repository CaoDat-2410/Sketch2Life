import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TeacherWorkbenchPage } from "../TeacherWorkbenchPage";
import { backendApi, BackendApiError } from "../../../../shared/api/backendApi";
import { teacherQuotaApi } from "../../../../shared/api/teacherQuotaApi";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

function setup(quota: unknown) {
  window.sketch2lifeAuth = { getIdToken: async () => "token" };
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-1" };
  vi.spyOn(backendApi, "assignments").mockResolvedValue({ assignments: [{ role: "teacher", active: true, class_id: "class-1" }] } as never);
  vi.spyOn(backendApi, "classes").mockResolvedValue({ items: [] } as never);
  vi.spyOn(backendApi, "lessons").mockResolvedValue({ items: [] } as never);
  vi.spyOn(teacherQuotaApi, "getMyVideoQuota").mockResolvedValue(quota as never);
  render(<MemoryRouter><TeacherWorkbenchPage /></MemoryRouter>);
}

describe("Teacher workbench personal quota", () => {
  it("shows the no-allocation message for a null allocation", async () => {
    setup({ allocation: null, organization_quota_owner: "ORGANIZATION" });
    expect(await screen.findByText("Chưa được cấp lượt tạo video")).toBeTruthy();
    expect(document.body.textContent).not.toContain("Không hiển thị lượt quota");
  });

  it("shows available units", async () => {
    setup({ allocation: { allocation_id: "allocation-1", teacher_ref: "teacher-1", available_units: 6, active: true, revision: 2, updated_at: null }, organization_quota_owner: "ORGANIZATION" });
    expect(await screen.findByText(/Số dư lượt tạo video:/)).toBeTruthy();
    expect(screen.getByText("6")).toBeTruthy();
  });

  it("maps service failures to safe copy", async () => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-1" };
    vi.spyOn(backendApi, "assignments").mockResolvedValue({ assignments: [{ role: "teacher", active: true, class_id: "class-1" }] } as never);
    vi.spyOn(backendApi, "classes").mockResolvedValue({ items: [] } as never);
    vi.spyOn(backendApi, "lessons").mockResolvedValue({ items: [] } as never);
    vi.spyOn(teacherQuotaApi, "getMyVideoQuota").mockRejectedValue(new BackendApiError("secret", "DEPENDENCY_UNAVAILABLE", 503));
    render(<MemoryRouter><TeacherWorkbenchPage /></MemoryRouter>);
    expect((await screen.findByRole("alert")).textContent).toContain("Dịch vụ hạn mức video tạm thời chưa sẵn sàng.");
    expect(document.body.textContent).not.toContain("secret");
  });
});
