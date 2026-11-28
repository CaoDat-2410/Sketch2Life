import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { TeacherPortalApp } from "../App";

vi.mock("../../../shared/auth/PortalSessionContext", () => ({ usePortalSession: () => ({ currentRole: "TEACHER", isAuthenticated: true, toast: null, logout: vi.fn() }) }));
vi.mock("../pages/TeacherPresentationPage", () => ({ TeacherPresentationPage: () => <h1>slides route</h1> }));
vi.mock("../pages/TeacherHistoryPage", () => ({ TeacherHistoryPage: () => <h1>history route</h1> }));
vi.mock("../pages/TeacherProfilePage", () => ({ TeacherProfilePage: () => <h1>profile route</h1> }));
vi.mock("../pages/TeacherActivitiesPage", () => ({ TeacherActivitiesPage: () => <h1>activities route</h1> }));

afterEach(() => cleanup());

it.each([
  ["/teacher/t02-presentation", "slides route"],
  ["/teacher/t09-history", "history route"],
  ["/teacher/t11-profile", "profile route"],
  ["/teacher/t12-activities", "activities route"],
])("routes %s to the implemented Teacher screen", async (path, heading) => {
  render(<MemoryRouter initialEntries={[path]}><TeacherPortalApp /></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: heading })).toBeTruthy();
});
