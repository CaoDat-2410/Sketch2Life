import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { TeacherPortalApp } from "../App";
vi.mock("../../../shared/auth/PortalSessionContext", () => ({usePortalSession: () => ({currentRole:"TEACHER",isAuthenticated:true,toast:null,logout:vi.fn()})}));
vi.mock("../pages/TeacherSampleRunPage", () => ({TeacherSampleRunPage: () => <h1>Sample run test page</h1>}));
vi.mock("../pages/TeacherFeedbackPage", () => ({TeacherFeedbackPage: () => <h1>Phản hồi giáo án test page</h1>}));
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});
it("routes t06 to the sample run page", async () => {render(<MemoryRouter initialEntries={["/teacher/t06-sample-story-run"]}><TeacherPortalApp /></MemoryRouter>); expect(await screen.findByRole("heading",{name:"Sample run test page"})).toBeTruthy();});
it("routes t14 to Teacher feedback", async () => {render(<MemoryRouter initialEntries={["/teacher/t14-feedback"]}><TeacherPortalApp /></MemoryRouter>); expect(await screen.findByRole("heading",{name:"Phản hồi giáo án test page"})).toBeTruthy();});
it("C24 routes t07 to the projection page without loading a child selection", async () => {render(<MemoryRouter initialEntries={["/teacher/t07-video-presentation-confirmation"]}><TeacherPortalApp /></MemoryRouter>); expect(await screen.findByText("Hãy chọn một buổi dạy để tiếp tục.")).toBeTruthy();});
it("routes the Teacher SVG catalog path", async () => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    status: 200,
    headers: new Headers(),
    text: async () => JSON.stringify({ items: [] }),
  })));
  render(<MemoryRouter initialEntries={["/teacher/svg-catalog"]}><TeacherPortalApp /></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: "Danh mục SVG" })).toBeTruthy();
  expect(await screen.findByText("Bản nháp AI chưa khả dụng.")).toBeTruthy();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});
