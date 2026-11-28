import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { teacherFeedbackApi, type TeacherFeedbackListPage, type TeacherFeedbackThreadPage } from "../../../../shared/api/teacherFeedbackApi";
import { TeacherFeedbackPage } from "../TeacherFeedbackPage";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.sketch2lifeConfig = undefined;
  window.sketch2lifeAuth = undefined;
});

const summary = (threadId = "thread-1") => ({ thread_id: threadId, lesson_id: "lesson-1", version_id: "version-2", lesson_title: "Khoa học vui", version_no: 2, revision: 4, created_at: "2026-11-25T10:00:00Z" });
const message = (id: string, body: string, fromYou = false) => ({ message_id: id, body, from_you: fromYou, author_role: fromYou ? "teacher" as const : "parent" as const, author_display_name: fromYou ? "Cô Lan" : "Phụ huynh An", created_at: "2026-11-25T10:00:00Z" });
const thread = (revision = 4, items = [message("message-1", "Good lesson"), message("message-2", "Teacher reply", true)], nextCursor: string | null = null): TeacherFeedbackThreadPage => ({
  thread_id: "thread-1", organization_id: "org-1", lesson_id: "lesson-1", version_id: "version-2", lesson_title: "Khoa học vui", version_no: 2, revision, limit: 25, next_cursor: nextCursor, items,
});
function list(items = [summary()], nextCursor: string | null = null): TeacherFeedbackListPage {
  return { total: items.length, limit: 25, next_cursor: nextCursor, items };
}
function setup(initialList = list(), initialThread = thread()) {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-1" };
  const threads = vi.spyOn(teacherFeedbackApi, "feedbackThreads").mockResolvedValue(initialList);
  const detail = vi.spyOn(teacherFeedbackApi, "feedbackThread").mockResolvedValue(initialThread);
  const reply = vi.spyOn(teacherFeedbackApi, "replyFeedback").mockResolvedValue({ thread_id: "thread-1", revision: 5 });
  render(<MemoryRouter><TeacherFeedbackPage /></MemoryRouter>);
  return { threads, detail, reply };
}
async function openThread() {
  fireEvent.click(await screen.findByRole("button", { name: /Giáo án Khoa học vui/ }));
  await screen.findByText("Good lesson");
}

describe("Teacher lesson feedback", () => {
  it("shows organization feedback, lesson title when known, and does not offer thread creation", async () => {
    setup();
    expect(await screen.findByRole("heading", { name: "Phản hồi giáo án" })).toBeTruthy();
    expect(screen.getByText("Phụ huynh gửi phản hồi; bạn xem và trả lời tại đây.")).toBeTruthy();
    expect(await screen.findByRole("button", { name: /Khoa học vui/ })).toBeTruthy();
    await openThread();
    expect(screen.getByText("Phụ huynh An · Phụ huynh")).toBeTruthy();
    expect(screen.getByText("Bạn · Giáo viên")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/luồng/i);
    const date = screen.getByText("25/11/2026");
    expect(date.className).toContain("tp-muted");
    expect(date.className).toContain("cozy-form-hint");
    expect(date.closest(".s2l-status-badge")).toBeNull();
    expect("createThread" in teacherFeedbackApi).toBe(false);
  });

  it("keeps typed reply text after a stale revision and reloads the thread", async () => {
    const calls = setup();
    calls.detail.mockResolvedValueOnce(thread(4)).mockResolvedValueOnce(thread(5, [message("message-2", "New message") ]));
    calls.reply.mockRejectedValueOnce(new BackendApiError("stale details", "STALE_REVISION", 409));
    await openThread();
    const input = screen.getByLabelText("Nội dung phản hồi", { selector: "textarea" }) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Reply to parent" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));

    expect((await screen.findByRole("alert")).textContent).toContain("Phản hồi đã thay đổi");
    await waitFor(() => expect(calls.detail).toHaveBeenCalledTimes(2));
    expect(input.value).toBe("Reply to parent");
    expect(calls.reply).toHaveBeenCalledWith("org-1", "thread-1", "Reply to parent", 4, expect.any(String));
    expect(document.body.textContent).not.toContain("stale details");
  });

  it("reuses one idempotency key for a retry of the same reply", async () => {
    const calls = setup();
    calls.reply.mockRejectedValueOnce(new BackendApiError("offline", "NETWORK_ERROR", 0)).mockResolvedValueOnce({ thread_id: "thread-1", revision: 5 });
    await openThread();
    const input = screen.getByLabelText("Nội dung phản hồi", { selector: "textarea" }) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Try again" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await waitFor(() => expect(calls.reply).toHaveBeenCalledTimes(2));
    expect(calls.reply.mock.calls[1][4]).toBe(calls.reply.mock.calls[0][4]);
  });

  it("generates a fresh idempotency key after a rejected 400 reply", async () => {
    const calls = setup();
    calls.reply.mockRejectedValueOnce(new BackendApiError("bad key", "INVALID_IDEMPOTENCY_KEY", 400)).mockResolvedValueOnce({ thread_id: "thread-1", revision: 5 });
    await openThread();
    fireEvent.change(screen.getByLabelText("Nội dung phản hồi", { selector: "textarea" }), { target: { value: "Retry with a new key" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));

    await waitFor(() => expect(calls.reply).toHaveBeenCalledTimes(2));
    expect(calls.reply.mock.calls[1][4]).not.toBe(calls.reply.mock.calls[0][4]);
  });

  it("loads more list and thread pages while keeping unique items", async () => {
    const secondSummary = { ...summary("thread-2"), lesson_id: "lesson-2", lesson_title: "Thiên nhiên" };
    const calls = setup(list([summary()], "list-next"), thread(4, [message("message-1", "Good lesson")], "message-next"));
    const loadMoreList = await screen.findByRole("button", { name: "Tải thêm" });
    calls.threads.mockResolvedValueOnce(list([secondSummary]));
    fireEvent.click(loadMoreList);
    expect(await screen.findByRole("button", { name: /Thiên nhiên/ })).toBeTruthy();
    await openThread();
    calls.detail.mockResolvedValueOnce(thread(4, [message("message-1", "Duplicate"), message("message-2", "Second") ]));
    fireEvent.click(screen.getByRole("button", { name: "Tải thêm tin nhắn" }));
    expect(await screen.findByText("Second")).toBeTruthy();
    expect(screen.getAllByText("Good lesson")).toHaveLength(1);
    expect(calls.threads.mock.calls[1]).toEqual(["org-1", 25, "list-next"]);
    expect(calls.detail.mock.calls[1]).toEqual(["org-1", "thread-1", 25, "message-next"]);
  });
});
