import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { TeacherPortalApp } from "../App";
vi.mock("../../../shared/auth/PortalSessionContext", () => ({usePortalSession: () => ({currentRole:"TEACHER",isAuthenticated:true,toast:null,logout:vi.fn()})}));
vi.mock("../pages/TeacherSampleRunPage", () => ({TeacherSampleRunPage: () => <h1>Sample run test page</h1>}));
afterEach(() => cleanup());
it("routes t06 to the sample run page", async () => {render(<MemoryRouter initialEntries={["/teacher/t06-sample-story-run"]}><TeacherPortalApp /></MemoryRouter>); expect(await screen.findByRole("heading",{name:"Sample run test page"})).toBeTruthy();});
it("C24 routes t07 to the projection page without loading a child selection", async () => {render(<MemoryRouter initialEntries={["/teacher/t07-video-presentation-confirmation"]}><TeacherPortalApp /></MemoryRouter>); expect(await screen.findByText("Hãy chọn một buổi dạy để tiếp tục.")).toBeTruthy();});
