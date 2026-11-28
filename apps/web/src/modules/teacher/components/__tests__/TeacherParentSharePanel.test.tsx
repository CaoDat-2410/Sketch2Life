import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { teacherProfileShareApi, type ParentSharedProfile } from "../../../../shared/api/teacherProfileShareApi";
import { TeacherParentSharePanel } from "../TeacherParentSharePanel";

const shared: ParentSharedProfile = { contract: "Be1ParentSharedProfileV1", share_grant_id: "grant-1", child_id: "child-1", granted_fields: ["DISPLAY_NAME", "AGE_BAND"], expires_at: "2027-02-23T00:00:00Z", fields: { display_name: "Mầm", age_band: { band_ref: "age-72-107-months-v1", band_version: 1 } } };
beforeEach(() => {
  vi.spyOn(teacherProfileShareApi, "getSharedProfile").mockRejectedValue(new BackendApiError("not found", "RESOURCE_NOT_FOUND", 404));
  vi.spyOn(teacherProfileShareApi, "accept").mockResolvedValue({ contract: "Be1ParentShareLinkV1", share_grant_id: "grant-1", child_id: "child-1", state: "ACTIVE", granted_fields: shared.granted_fields, accepted_at: "2026-11-25T00:00:00Z", expires_at: shared.expires_at, revision: 1 });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Teacher parent share panel", () => {
  it("requires confirmation, then reads and displays only the granted fields", async () => {
    vi.mocked(teacherProfileShareApi.getSharedProfile).mockRejectedValueOnce(new BackendApiError("not found", "RESOURCE_NOT_FOUND", 404)).mockResolvedValueOnce(shared);
    render(<TeacherParentSharePanel organizationId="org-1" classId="class-1" childId="child-1" canAccept />);
    const details = screen.getByText("Chia sẻ từ phụ huynh").closest("details");
    const summary = screen.getByText("Chia sẻ từ phụ huynh").closest("summary");
    expect(details?.open).toBe(false);
    if (!summary) throw new Error("parent share disclosure summary not rendered");
    fireEvent.click(summary);
    await screen.findByText("Chưa có chia sẻ từ phụ huynh.");
    fireEvent.change(screen.getByLabelText("Mã do phụ huynh cung cấp"), { target: { value: "invite_code_123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Chấp nhận chia sẻ" }));
    expect(teacherProfileShareApi.accept).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận chấp nhận" }));
    expect(await screen.findByText("Mầm")).toBeTruthy();
    expect(screen.getByText("Nhóm tuổi:").parentElement?.textContent).toBe("Nhóm tuổi: 72–107 tháng");
    expect(screen.queryByText("age-72-107-months-v1")).toBeNull();
    expect(teacherProfileShareApi.accept).toHaveBeenCalledWith("org-1", "class-1", "child-1", "invite_code_123456", expect.any(String));
    expect(screen.queryByText(/support|context|tháng tuổi/i)).toBeNull();
  });

  it("keeps the entered code and does not reload when the disclosure closes and opens", async () => {
    render(<TeacherParentSharePanel organizationId="org-1" classId="class-1" childId="child-1" canAccept />);
    const details = screen.getByText("Chia sẻ từ phụ huynh").closest("details");
    const summary = screen.getByText("Chia sẻ từ phụ huynh").closest("summary");
    if (!details || !summary) throw new Error("parent share disclosure not rendered");
    expect(details.open).toBe(false);
    fireEvent.click(summary);
    await screen.findByText("Chưa có chia sẻ từ phụ huynh.");
    const input = screen.getByLabelText("Mã do phụ huynh cung cấp") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "invite_code_123456" } });
    expect(teacherProfileShareApi.getSharedProfile).toHaveBeenCalledTimes(1);
    fireEvent.click(summary);
    expect(details.open).toBe(false);
    fireEvent.click(summary);
    expect(details.open).toBe(true);
    expect((screen.getByLabelText("Mã do phụ huynh cung cấp") as HTMLInputElement).value).toBe("invite_code_123456");
    expect(teacherProfileShareApi.getSharedProfile).toHaveBeenCalledTimes(1);
  });
});
