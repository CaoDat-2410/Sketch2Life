import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AccessGrant, TeacherLessonDetail } from "../../../../shared/api/backendApi";
import { createPrivateShare, revokeAccessGrant, StaleAccessGrantRevisionError } from "../../../../shared/api/lessonSharingApi";
import { TeacherPrivateSharePanel } from "../TeacherPrivateSharePanel";

vi.mock("../../../../shared/api/lessonSharingApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../../shared/api/lessonSharingApi")>();
  return { ...actual, createPrivateShare: vi.fn(), revokeAccessGrant: vi.fn() };
});

function lesson(state = "ACTIVE", versionId: string | null = "version-1"): TeacherLessonDetail {
  return {
    contract: "LessonDetailV1",
    lesson_id: "lesson-1",
    state,
    current_version: versionId ? { version_id: versionId } : null,
  } as unknown as TeacherLessonDetail;
}

function grant(overrides: Partial<AccessGrant> = {}): AccessGrant {
  return {
    contract: "LessonAccessGrantV1",
    access_grant_id: "grant-1",
    lesson_id: "lesson-1",
    version_id: "version-1",
    audience_kind: "ORGANIZATION",
    audience_ref: "org-1",
    capability: "VIEW",
    state: "ACTIVE",
    granted_by: "teacher-1",
    approved_by: null,
    approved_at: null,
    expires_at: null,
    revoked_at: null,
    revision: 1,
    ...overrides,
  };
}

const createMock = vi.mocked(createPrivateShare);
const revokeMock = vi.mocked(revokeAccessGrant);

beforeEach(() => {
  createMock.mockReset();
  revokeMock.mockReset();
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("TeacherPrivateSharePanel", () => {
  it("uses the organization as the default audience and does not fetch a grant list", async () => {
    createMock.mockResolvedValue(grant());
    const fetcher = vi.mocked(fetch);
    render(<TeacherPrivateSharePanel organizationId="org-1" lesson={lesson()} />);

    expect(screen.getByText("Danh sách chia sẻ chỉ hiển thị các chia sẻ vừa tạo trong phiên này.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));

    await waitFor(() => expect(createMock).toHaveBeenCalledWith(
      "org-1",
      expect.objectContaining({ lessonId: "lesson-1", versionId: "version-1", audienceKind: "ORGANIZATION", audienceRef: "org-1", capability: "VIEW", expiresAt: null }),
      expect.any(String),
    ));
    expect(fetcher).not.toHaveBeenCalled();
    expect(await screen.findByText("Đang chia sẻ")).toBeTruthy();
  });

  it("uses a typed parent group id and selected capability", async () => {
    createMock.mockResolvedValue(grant({ audience_kind: "PARENT_GROUP", audience_ref: "group-7", capability: "DOWNLOAD" }));
    const { container } = render(<TeacherPrivateSharePanel organizationId="org-1" lesson={lesson()} />);
    const selects = container.querySelectorAll("select");
    fireEvent.change(selects[0], { target: { value: "PARENT_GROUP" } });
    fireEvent.change(screen.getByLabelText("ID nhóm phụ huynh"), { target: { value: "group-7" } });
    fireEvent.change(selects[1], { target: { value: "DOWNLOAD" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));

    await waitFor(() => expect(createMock).toHaveBeenCalledWith(
      "org-1",
      expect.objectContaining({ audienceKind: "PARENT_GROUP", audienceRef: "group-7", capability: "DOWNLOAD" }),
      expect.any(String),
    ));
  });

  it("reuses the same idempotency key when the same create action is retried", async () => {
    createMock.mockRejectedValueOnce(new Error("private failure")).mockResolvedValueOnce(grant());
    render(<TeacherPrivateSharePanel organizationId="org-1" lesson={lesson()} />);

    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));
    await screen.findByText("Chưa thể tạo lượt chia sẻ lúc này. Vui lòng kiểm tra thông tin rồi thử lại.");
    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));
    await waitFor(() => expect(createMock).toHaveBeenCalledTimes(2));

    expect(createMock.mock.calls[1][2]).toBe(createMock.mock.calls[0][2]);
  });

  it("updates its session row from the revoke response", async () => {
    createMock.mockResolvedValue(grant());
    revokeMock.mockResolvedValue(grant({ state: "REVOKED", revision: 2, revoked_at: "2026-11-25T00:00:00Z" }));
    render(<TeacherPrivateSharePanel organizationId="org-1" lesson={lesson()} />);
    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));
    await screen.findByRole("button", { name: "Thu hồi" });
    fireEvent.click(screen.getByRole("button", { name: "Thu hồi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận thu hồi" }));

    expect(await screen.findByText("Đã thu hồi")).toBeTruthy();
    expect(revokeMock).toHaveBeenCalledWith("org-1", "lesson-1", "grant-1", 1, expect.any(String));
    expect(screen.queryByRole("button", { name: "Thu hồi" })).toBeNull();
  });

  it("uses current_version after a stale revoke and asks for another confirmation", async () => {
    createMock.mockResolvedValue(grant());
    revokeMock
      .mockRejectedValueOnce(new StaleAccessGrantRevisionError("request-1", 3))
      .mockResolvedValueOnce(grant({ state: "REVOKED", revision: 4 }));
    render(<TeacherPrivateSharePanel organizationId="org-1" lesson={lesson()} />);
    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));
    await screen.findByRole("button", { name: "Thu hồi" });
    fireEvent.click(screen.getByRole("button", { name: "Thu hồi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận thu hồi" }));
    expect(await screen.findByText(/Lượt chia sẻ đã thay đổi/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận thu hồi" }));

    await screen.findByText("Đã thu hồi");
    expect(revokeMock).toHaveBeenNthCalledWith(1, "org-1", "lesson-1", "grant-1", 1, expect.any(String));
    expect(revokeMock).toHaveBeenNthCalledWith(2, "org-1", "lesson-1", "grant-1", 3, expect.any(String));
    expect(revokeMock.mock.calls[1][4]).not.toBe(revokeMock.mock.calls[0][4]);
  });

  it.each([
    ["archived lesson", lesson("ARCHIVED")],
    ["lesson without a current version", lesson("ACTIVE", null)],
  ])("disables new shares for a %s", (_label, detail) => {
    render(<TeacherPrivateSharePanel organizationId="org-1" lesson={detail} />);
    expect(screen.getByRole("button", { name: "Tạo chia sẻ" })).toHaveProperty("disabled", true);
    expect(screen.getByRole("combobox", { name: "Đối tượng nhận" })).toHaveProperty("disabled", true);
  });
});
