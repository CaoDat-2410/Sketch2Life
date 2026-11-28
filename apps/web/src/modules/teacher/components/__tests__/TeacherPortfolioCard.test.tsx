import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { teacherWorkspaceApi } from "../../../../shared/api/teacherWorkspaceApi";
import { TeacherPortfolioCard } from "../TeacherPortfolioCard";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("loads portfolio only when opened and shows an empty synthetic profile state", async () => {
  const load = vi.spyOn(teacherWorkspaceApi, "portfolio").mockResolvedValue({ contract: "Be1PortfolioPageV1", child_id: "child-1", items: [], next_cursor: null });
  render(<TeacherPortfolioCard organizationId="org-1" classId="class-1" childId="child-1" />);
  expect(load).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Hồ sơ nổi bật" }));
  expect(await screen.findByText("Chưa có ghi nhận trong hồ sơ nổi bật.")).toBeTruthy();
  expect(load).toHaveBeenCalledWith("org-1", "class-1", "child-1", { limit: 25, cursor: undefined });
});
