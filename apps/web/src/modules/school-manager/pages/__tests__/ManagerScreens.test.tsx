import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { M01PublicationReviewPage } from "../ManagerScreens";
import {
  backendApi,
  type AccessGrant,
  type AccessGrantPage,
  type TeacherLessonDetail,
} from "../../../../shared/api/backendApi";

const grant = (id: string): AccessGrant => ({
  contract: "LessonAccessGrantV1",
  access_grant_id: "grant-" + id,
  lesson_id: "lesson-" + id,
  lesson_title: "Giáo án " + id,
  version_id: "version-" + id,
  version_no: 3,
  audience_kind: "PUBLIC",
  audience_ref: null,
  capability: "VIEW",
  state: "PENDING_REVIEW",
  granted_by: "teacher-1",
  approved_by: null,
  approved_at: null,
  expires_at: null,
  revoked_at: null,
  revision: 3,
});

const lessonFor = (id: string): TeacherLessonDetail => ({
  contract: "LessonDetailV1",
  lesson_id: "lesson-" + id,
  organization_id: "org-test",
  owner_kind: "ORGANIZATION",
  created_by: "teacher-1",
  state: "ACTIVE",
  visibility: "PUBLIC",
  moderation_state: "VISIBLE",
  current_version: {
    contract: "LessonVersionV1",
    lesson_id: "lesson-" + id,
    version_id: "version-" + id,
    version_no: 1,
    review_state: "PENDING_REVIEW",
    structured_content_hash: "hash-" + id,
    source_document_revision_id: null,
    authored_principal_ref: "teacher-1",
    created_at: "2026-11-19T00:00:00Z",
    content: {
      locale: "vi-VN",
      title: "Giáo án mẫu " + id,
      topic: "Con vật",
      target_age_band_ref: "age-band-test",
      target_age_band_version: 1,
      objectives: ["Quan sát"],
      drawing_subject: "Con mèo",
      drawing_steps_text: "Vẽ đầu",
      subject_learning_notes: "Ghi chú",
      script_direction: null,
      script_following_allowed: false,
      activities: [],
    },
  },
  revision: 1,
  created_at: "2026-11-19T00:00:00Z",
  updated_at: "2026-11-19T00:00:00Z",
});

const grantPage = (items: AccessGrant[], next: string | null): AccessGrantPage => ({
  contract: "LessonAccessGrantPageV1",
  items,
  next_cursor: next,
});

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = {
    signIn: vi.fn(async () => undefined),
    getIdToken: vi.fn(async () => "unit-test-id-token"),
    signOut: vi.fn(async () => undefined),
  };
  vi.spyOn(backendApi, "assignments").mockResolvedValue({
    assignments: [{ role: "school_admin", active: true }],
  } as unknown as Awaited<ReturnType<typeof backendApi.assignments>>);
  vi.spyOn(backendApi, "teacherLesson").mockImplementation(async (_organizationId, lessonId) =>
    lessonFor(lessonId.replace("lesson-", "")),
  );
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
});

describe("School Manager public review queue", () => {
  it("loads the next cursor page and merges the grants by id", async () => {
    const list = vi.spyOn(backendApi, "accessGrants").mockImplementation(async (_organizationId, options) =>
      options?.cursor === "c2"
        ? grantPage([grant("2")], null)
        : grantPage([grant("1")], "c2"),
    );

    render(<M01PublicationReviewPage showToast={vi.fn()} />);

    expect(await screen.findByRole("button", { name: /^Giáo án 1/ })).toBeTruthy();
    fireEvent.click(await screen.findByRole("button", { name: "Tải thêm yêu cầu" }));
    expect(await screen.findByText("Giáo án 2", { selector: ".manager-review-item-copy strong" })).toBeTruthy();
    // The first page stays in the list: the second page was merged in, not swapped for it.
    expect(screen.getByText("Giáo án 1", { selector: ".manager-review-item-copy strong" })).toBeTruthy();
    expect(screen.getAllByText("Phiên bản 3", { selector: ".manager-review-item-copy span" })).toHaveLength(2);
    expect(screen.getByText("Công khai · Chờ duyệt")).toBeTruthy();
    expect(screen.queryByText("lesson-1", { selector: ".manager-review-item-copy strong" })).toBeNull();
    expect(screen.queryByText("lesson-2", { selector: ".manager-review-item-copy strong" })).toBeNull();
    expect(list).toHaveBeenLastCalledWith("org-test", {
      state: "PENDING_REVIEW",
      audience_kind: "PUBLIC",
      cursor: "c2",
    });
    expect(screen.queryByRole("button", { name: "Tải thêm yêu cầu" })).toBeNull();
  });

  it("uses a readable ordinal when the existing lesson read has no title", async () => {
    vi.spyOn(backendApi, "accessGrants").mockResolvedValue(grantPage([{ ...grant("1"), lesson_title: null }], null));
    vi.spyOn(backendApi, "teacherLesson").mockRejectedValue(new Error("private lesson read error"));

    render(<M01PublicationReviewPage showToast={vi.fn()} />);

    expect(await screen.findByRole("button", { name: /^Giáo án chờ duyệt 1/ })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Giáo án chờ duyệt 1" })).toBeTruthy();
    expect(screen.queryByText("lesson-1")).toBeNull();
  });

  it("uses plain Vietnamese for approval and change-request toasts", async () => {
    vi.spyOn(backendApi, "accessGrants").mockResolvedValue(grantPage([grant("1")], null));
    const decide = vi.spyOn(backendApi, "decideAccessGrant").mockResolvedValue({});
    const showToast = vi.fn();
    render(<M01PublicationReviewPage showToast={showToast} />);

    const confirm = await screen.findByRole("checkbox");
    await waitFor(() => expect(confirm.hasAttribute("disabled")).toBe(false));
    fireEvent.click(confirm);
    fireEvent.click(screen.getByRole("button", { name: "Duyệt công khai" }));
    await waitFor(() => expect(decide).toHaveBeenCalledTimes(1));
    expect(showToast).toHaveBeenCalledWith("Đã ghi nhận quyết định duyệt học liệu công khai.", "ok");

    const reason = await screen.findByLabelText(/Lý do yêu cầu chỉnh sửa/);
    await waitFor(() => expect(reason.hasAttribute("disabled")).toBe(false));
    fireEvent.change(reason, { target: { value: "Cần bổ sung hướng dẫn." } });
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu chỉnh sửa" }));
    await waitFor(() => expect(decide).toHaveBeenCalledTimes(2));
    expect(showToast).toHaveBeenCalledWith("Đã gửi yêu cầu chỉnh sửa học liệu công khai.", "ok");
    expect(showToast.mock.calls.every(([text]) => !/\b(API|grant|PUBLIC)\b/.test(text))).toBe(true);
  });

  it("keeps the decision key for the same decision and changes it when the reason changes", async () => {
    vi.spyOn(backendApi, "accessGrants").mockResolvedValue(grantPage([grant("1")], null));
    const decide = vi.spyOn(backendApi, "decideAccessGrant").mockRejectedValue(new Error("Mất kết nối"));

    render(<M01PublicationReviewPage showToast={vi.fn()} />);

    const reason = await screen.findByLabelText(/Lý do yêu cầu chỉnh sửa/);
    await waitFor(() => expect(reason.hasAttribute("disabled")).toBe(false));
    const requestChanges = screen.getByRole("button", { name: /Yêu cầu chỉnh sửa/ });
    const submitWith = async (text: string, expectedCalls: number) => {
      fireEvent.change(reason, { target: { value: text } });
      await waitFor(() => expect(requestChanges.hasAttribute("disabled")).toBe(false));
      fireEvent.click(requestChanges);
      await waitFor(() => expect(decide).toHaveBeenCalledTimes(expectedCalls));
      await waitFor(() => expect(requestChanges.hasAttribute("disabled")).toBe(false));
    };

    await submitWith("A", 1);
    await submitWith("A", 2);
    await submitWith("B", 3);
    await submitWith("A", 4);

    const keys = decide.mock.calls.map((call) => call[4]);
    expect(keys[0]).toBeTruthy();
    expect(keys[1]).toBe(keys[0]);
    expect(keys[2]).not.toBe(keys[0]);
    expect(keys[3]).toBe(keys[0]);
  });

  it("keeps the decision key when the same approval is sent again after a failure", async () => {
    vi.spyOn(backendApi, "accessGrants").mockResolvedValue(grantPage([grant("1")], null));
    const decide = vi
      .spyOn(backendApi, "decideAccessGrant")
      .mockRejectedValueOnce(new Error("Mất kết nối"))
      .mockResolvedValue({});

    render(<M01PublicationReviewPage showToast={vi.fn()} />);

    const confirm = await screen.findByRole("checkbox");
    await waitFor(() => expect(confirm.hasAttribute("disabled")).toBe(false));
    fireEvent.click(confirm);
    const approve = screen.getByRole("button", { name: /Duyệt công khai/ });
    await waitFor(() => expect(approve.hasAttribute("disabled")).toBe(false));
    fireEvent.click(approve);
    await waitFor(() => expect(decide).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(approve.hasAttribute("disabled")).toBe(false));
    fireEvent.click(approve);
    await waitFor(() => expect(decide).toHaveBeenCalledTimes(2));

    expect(decide.mock.calls[0][2]).toBe("APPROVE");
    expect(decide.mock.calls[0][4]).toBeTruthy();
    expect(decide.mock.calls[1][4]).toBe(decide.mock.calls[0][4]);
  });
});
