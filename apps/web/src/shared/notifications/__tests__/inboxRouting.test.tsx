import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { authService } from "../../../modules/school-manager/be1/services/authService";
import { classService } from "../../../modules/school-manager/be1/services/classService";
import { SchoolManagerBe1App } from "../../../modules/school-manager/be1/App";
import { TeacherPortalApp } from "../../../modules/teacher/App";
import * as notificationsApi from "../../api/notificationsApi";

vi.mock("../../auth/PortalSessionContext", () => ({
  usePortalSession: () => ({ currentRole: "TEACHER", isAuthenticated: true, toast: null, logout: vi.fn() }),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

beforeEach(() => {
  vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue({
    contract: "NotificationPageV1",
    items: [],
    next_cursor: null,
    unread_count: 0,
  });
});

describe("role inbox routes", () => {
  it("renders the shared inbox at the Teacher route", async () => {
    render(<MemoryRouter initialEntries={["/teacher/t10-inbox"]}><TeacherPortalApp /></MemoryRouter>);

    expect(await screen.findByText("Hộp thư hiện đang trống.")).toBeTruthy();
    // One call from the inbox page and one from the menu badge in the shell.
    expect(vi.mocked(notificationsApi.listNotifications).mock.calls.map(([options]) => options?.limit ?? "page").sort())
      .toEqual([1, "page"]);
    expect(screen.queryByText("Chưa khả dụng")).toBeNull();
  });

  it("renders the shared inbox at the School Manager route behind its access gate", async () => {
    vi.spyOn(authService, "observe").mockImplementation((callback) => {
      callback({ uid: "manager-test" } as never);
      return () => undefined;
    });
    vi.spyOn(classService, "currentAssignments").mockResolvedValue({
      contract: "Be1AdultAssignmentsV1",
      assignments: [{ role: "school_admin", class_id: null }],
    });

    render(<MemoryRouter initialEntries={["/school/inbox"]}><SchoolManagerBe1App /></MemoryRouter>);

    expect(await screen.findByText("Hộp thư hiện đang trống.")).toBeTruthy();
    // One call from the inbox page and one from the menu badge in the shell.
    expect(vi.mocked(notificationsApi.listNotifications).mock.calls.map(([options]) => options?.limit ?? "page").sort())
      .toEqual([1, "page"]);
    expect(screen.queryByText("Chưa khả dụng")).toBeNull();
    expect(classService.currentAssignments).toHaveBeenCalledOnce();
  });
});
