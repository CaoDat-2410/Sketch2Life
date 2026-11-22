import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FeedbackPage } from "../pages/FeedbackPage";
import { TeacherAssignmentsPage } from "../pages/TeacherAssignmentsPage";
import { managerBusinessService } from "../services/managerBusinessService";
import { classService } from "../services/classService";
import { AdminBe1Error } from "../services/be1Client";

const summary = { thread_id: "thread-1", lesson_id: "lesson-1", version_id: "v1", revision: 3, created_at: "2026-11-21T00:00:00Z" };
const detail = { thread_id: "thread-1", revision: 3, next_cursor: null, items: [{ message_id: "m1", body: "Xin chào", from_you: false, created_at: "2026-11-21T00:00:00Z" }, { message_id: "m2", body: "Đã xem", from_you: true, created_at: "2026-11-21T00:01:00Z" }] };
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
beforeEach(() => {
  vi.spyOn(managerBusinessService, "feedbackThreads").mockResolvedValue({ items: [summary], next_cursor: null });
  vi.spyOn(managerBusinessService, "feedbackThread").mockResolvedValue(detail);
});

describe("Manager feedback", () => {
  it("shows messages in order and clears the reply after confirmation", async () => {
    const reply = vi.spyOn(managerBusinessService, "replyFeedback").mockResolvedValue({ thread_id: "thread-1", revision: 4 });
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    expect(await screen.findByText("Phụ huynh hoặc nhân sự trường")).toBeTruthy();
    expect(screen.getByText("Bạn")).toBeTruthy();
    const input = screen.getByLabelText("Nội dung phản hồi") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "  Cảm ơn  " } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    expect(await screen.findByText("Đã gửi phản hồi.")).toBeTruthy();
    expect(input.value).toBe("");
    expect(reply).toHaveBeenCalledWith("thread-1", "Cảm ơn", 3, expect.any(String));
    expect(managerBusinessService.feedbackThread).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: /tạo|đính kèm/i })).toBeNull();
  });

  it("keeps text and reuses a key after an uncertain failure", async () => {
    const reply = vi.spyOn(managerBusinessService, "replyFeedback").mockRejectedValue(new Error("private server error"));
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    const input = await screen.findByLabelText("Nội dung phản hồi") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Kiểm tra" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Chưa rõ kết quả");
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await waitFor(() => expect(reply).toHaveBeenCalledTimes(2));
    expect(reply.mock.calls[0][3]).toBe(reply.mock.calls[1][3]);
    expect(input.value).toBe("Kiểm tra");
    expect(screen.queryByText("private server error")).toBeNull();
    await waitFor(() => expect((screen.getByRole("button", { name: "Gửi phản hồi" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.change(input, { target: { value: "Nội dung khác" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await waitFor(() => expect(reply).toHaveBeenCalledTimes(3));
    expect(reply.mock.calls[2][3]).not.toBe(reply.mock.calls[1][3]);
  });

  it("reloads a stale thread while retaining the draft", async () => {
    vi.spyOn(managerBusinessService, "replyFeedback").mockRejectedValue(new AdminBe1Error("unsafe", 409, "STALE_REVISION"));
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    const input = await screen.findByLabelText("Nội dung phản hồi") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Bản nháp" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    expect((await screen.findByRole("alert")).textContent).toContain("đã thay đổi");
    await waitFor(() => expect(managerBusinessService.feedbackThread).toHaveBeenCalledTimes(2));
    expect(input.value).toBe("Bản nháp");
  });

  it.each([[404, "Không tìm thấy"], [403, "không có quyền"], [422, "không hợp lệ"], [500, "Chưa rõ kết quả"]])("reports a safe %i reply failure and preserves the draft", async (status, message) => {
    vi.spyOn(managerBusinessService, "replyFeedback").mockRejectedValue(new AdminBe1Error("secret", status, "error"));
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    const input = await screen.findByLabelText("Nội dung phản hồi") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Bản nháp" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await waitFor(() => expect(screen.getAllByRole("alert").some((item) => item.textContent?.includes(message))).toBe(true));
    expect(input.value).toBe("Bản nháp");
    expect(screen.queryByText("secret")).toBeNull();
  });

  it("deduplicates later pages of threads", async () => {
    vi.mocked(managerBusinessService.feedbackThreads).mockResolvedValueOnce({ items: [summary], next_cursor: "next" }).mockResolvedValueOnce({ items: [summary, { ...summary, thread_id: "thread-2", lesson_id: "lesson-2" }], next_cursor: null });
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Tải thêm" }));
    expect(await screen.findByRole("button", { name: /Giáo án lesson-2/ })).toBeTruthy();
    expect(screen.getAllByRole("button", { name: /Giáo án lesson-1/ })).toHaveLength(1);
  });

  it("ignores a late response from a previously selected thread", async () => {
    let resolveFirst!: (value: typeof detail) => void;
    vi.mocked(managerBusinessService.feedbackThreads).mockResolvedValue({ items: [summary, { ...summary, thread_id: "thread-2", lesson_id: "lesson-2" }], next_cursor: null });
    vi.mocked(managerBusinessService.feedbackThread).mockImplementation((id) => id === "thread-1" ? new Promise((resolve) => { resolveFirst = resolve; }) : Promise.resolve({ ...detail, thread_id: "thread-2", items: [{ ...detail.items[0], body: "Tin thứ hai" }] }));
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    fireEvent.click(screen.getByRole("button", { name: /Giáo án lesson-2/ }));
    expect(await screen.findByText("Tin thứ hai")).toBeTruthy();
    await act(async () => { resolveFirst(detail); });
    expect(screen.queryByText("Xin chào")).toBeNull();
    expect(screen.getByText("Tin thứ hai")).toBeTruthy();
  });

  it("sends the new revision with a new key after a stale reload, and never reuses a key after success", async () => {
    const reply = vi.spyOn(managerBusinessService, "replyFeedback")
      .mockRejectedValueOnce(new AdminBe1Error("unsafe", 409, "STALE_REVISION"))
      .mockResolvedValue({ thread_id: "thread-1", revision: 5 });
    vi.mocked(managerBusinessService.feedbackThread)
      .mockResolvedValueOnce(detail)
      .mockResolvedValueOnce({ ...detail, revision: 4 })
      .mockResolvedValue({ ...detail, revision: 5 });
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    const input = await screen.findByLabelText("Nội dung phản hồi") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Cùng nội dung" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await waitFor(() => expect(managerBusinessService.feedbackThread).toHaveBeenCalledTimes(2));
    await waitFor(() => expect((screen.getByRole("button", { name: "Gửi phản hồi" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    expect(await screen.findByText("Đã gửi phản hồi.")).toBeTruthy();
    expect(reply.mock.calls[0][2]).toBe(3);
    expect(reply.mock.calls[1][2]).toBe(4);
    expect(reply.mock.calls[1][3]).not.toBe(reply.mock.calls[0][3]);
    fireEvent.change(input, { target: { value: "Cùng nội dung" } });
    await waitFor(() => expect((screen.getByRole("button", { name: "Gửi phản hồi" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));
    await waitFor(() => expect(reply).toHaveBeenCalledTimes(3));
    expect(reply.mock.calls[2][2]).toBe(5);
    expect(reply.mock.calls[2][3]).not.toBe(reply.mock.calls[1][3]);
  });

  it("offers no attachment or completion control", async () => {
    render(<FeedbackPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án lesson-1/ }));
    await screen.findByLabelText("Nội dung phản hồi");
    expect(document.querySelector("input[type=file], input[type=checkbox]")).toBeNull();
    expect(screen.queryByRole("button", { name: /hoàn thành|chat/i })).toBeNull();
  });
});

it("lists class status and assignment status without exposing candidate identifiers", async () => {
  vi.spyOn(classService, "listClasses").mockResolvedValue([{ class_id: "c1", display_name: "Lớp Lá", state: "suspended", has_active_teacher: false }]);
  render(<TeacherAssignmentsPage />);
  const list = await screen.findByRole("list", { name: "Danh sách lớp và trạng thái phân công" });
  const row = list.querySelector("li");
  if (!row) throw new Error("Expected the class list to contain a row.");
  expect(row.textContent).toContain("Lớp Lá");
  expect(row.textContent).toContain("Tạm ngưng");
  expect(row.textContent).toContain("Chưa có giáo viên phụ trách");
  expect(screen.getByText(/không thể phân công Teacher/)).toBeTruthy();
});

it("offers a retry when the class list fails", async () => {
  vi.spyOn(classService, "listClasses").mockRejectedValueOnce(new Error("private")).mockResolvedValueOnce([]);
  render(<TeacherAssignmentsPage />);
  expect(await screen.findByRole("alert")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Tải lại" }));
  expect(await screen.findByText("Chưa có lớp nào trong trường.")).toBeTruthy();
});
