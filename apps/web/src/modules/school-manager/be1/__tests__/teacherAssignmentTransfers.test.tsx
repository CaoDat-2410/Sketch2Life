import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, configure, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { AdminBe1Error } from "../services/be1Client";
import {
  classService,
  type Be1Class,
  type Be1TeacherAssignmentTransferAcceptedV1,
  type Be1TeacherAssignmentTransferState,
  type Be1TeacherAssignmentTransferStatusV1,
} from "../services/classService";
import { TeacherAssignmentCard } from "../pages/TeacherAssignmentCard";

configure({ asyncUtilTimeout: 8_000 });

const assignedClass: Be1Class = {
  class_id: "class-1",
  display_name: "Lớp Lá 1",
  state: "active",
  assignment_revision: 8,
  has_active_teacher: true,
};

const candidatesPage = {
  contract: "Be1TeacherCandidatePageV1" as const,
  items: [
    { candidate_ref: "teacher-current", display_name: "Cô Mai" },
    { candidate_ref: "teacher-next", display_name: "Cô Lan" },
  ],
  next_cursor: null,
};

const acceptedTransfer = <T extends "REASSIGN" | "OFFBOARD">(action: T): Be1TeacherAssignmentTransferAcceptedV1 & { action: T } => ({
  contract: "Be1TeacherAssignmentTransferAcceptedV1",
  transfer_id: "12345678-1234-1234-1234-123456789012",
  class_id: "class-1",
  action,
  state: "TRANSFER_PENDING",
  assignment_revision: 8,
  status_url: "/api/be1/v1/classes/class-1/assignment-transfers/12345678-1234-1234-1234-123456789012",
});

const transferStatus = (state: Be1TeacherAssignmentTransferState): Be1TeacherAssignmentTransferStatusV1 => ({
  contract: "Be1TeacherAssignmentTransferStatusV1",
  transfer_id: "12345678-1234-1234-1234-123456789012",
  class_id: "class-1",
  action: "REASSIGN",
  state,
  assignment_revision: 8,
  created_at: "2026-11-26T00:00:00Z",
  updated_at: "2026-11-26T00:00:02Z",
  last_failure_code: null,
  status_url: "/api/be1/v1/classes/class-1/assignment-transfers/12345678-1234-1234-1234-123456789012",
});

async function chooseTeacher() {
  fireEvent.click(await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" }));
  fireEvent.click(await screen.findByRole("option", { name: "Cô Lan" }));
}

beforeEach(() => {
  vi.stubEnv("VITE_BE1_BASE_URL", "https://api.example.test");
  vi.stubEnv("VITE_BE1_ORGANIZATION_ID", "org-test");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("assignment transfer service requests", () => {
  it("sends revision and key headers, and leaves the offboard body empty", async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const responses = [
      acceptedTransfer("REASSIGN"),
      acceptedTransfer("OFFBOARD"),
      transferStatus("COMPLETED"),
    ];
    vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
      calls.push({ url, init });
      const body = responses[calls.length - 1];
      return new Response(JSON.stringify(body), {
        status: calls.length < 3 ? 202 : 200,
        headers: { "Content-Type": "application/json" },
      });
    }));
    const { authService } = await import("../services/authService");
    vi.spyOn(authService, "getIdToken").mockResolvedValue("unit-test-id-token");

    await classService.reassignTeacher("class-1", "teacher-next", 8, "reassign-key");
    await classService.offboardTeacher("class-1", 8, "offboard-key");
    await classService.getAssignmentTransfer("class-1", "transfer-id");

    const reassignHeaders = new Headers(calls[0].init.headers);
    expect(calls[0].url).toBe("https://api.example.test/api/be1/v1/classes/class-1/assignments");
    expect(reassignHeaders.get("If-Match")).toBe('"8"');
    expect(reassignHeaders.get("Idempotency-Key")).toBe("reassign-key");
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ candidate_ref: "teacher-next" });

    const offboardHeaders = new Headers(calls[1].init.headers);
    expect(calls[1].url).toBe("https://api.example.test/api/be1/v1/classes/class-1/assignments/current");
    expect(calls[1].init.method).toBe("DELETE");
    expect(offboardHeaders.get("If-Match")).toBe('"8"');
    expect(offboardHeaders.get("Idempotency-Key")).toBe("offboard-key");
    expect(calls[1].init.body).toBeUndefined();

    expect(calls[2].url).toBe("https://api.example.test/api/be1/v1/classes/class-1/assignment-transfers/transfer-id");
    expect(calls[2].init.method).toBeUndefined();
  });

  it("treats non-transfer 2xx contracts as a completed command", async () => {
    const adultAssignment = {
      contract: "Be1AdultAssignmentV1",
      assignment_id: "assignment-1",
      candidate_ref: "teacher-next",
      role: "teacher",
      class_id: "class-1",
      active: true,
      assignment_revision: 9,
    };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(adultAssignment), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })));
    const { authService } = await import("../services/authService");
    vi.spyOn(authService, "getIdToken").mockResolvedValue("unit-test-id-token");

    await expect(classService.reassignTeacher("class-1", "teacher-next", 8, "reassign-key")).resolves.toBeNull();
    await expect(classService.offboardTeacher("class-1", 8, "offboard-key")).resolves.toBeNull();
  });
});

describe("Teacher reassignment and offboarding", () => {
  it("polls an accepted reassignment to completion and reloads the class list", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    const reassign = vi.spyOn(classService, "reassignTeacher").mockResolvedValue(acceptedTransfer("REASSIGN"));
    const poll = vi.spyOn(classService, "getAssignmentTransfer").mockResolvedValue(transferStatus("COMPLETED"));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Đổi giáo viên phụ trách?" })).toBeTruthy();
    expect(within(dialog).getByText(/đổi giáo viên phụ trách/)).toBeTruthy();
    expect(reassign).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Đổi giáo viên" }));

    await waitFor(() => expect(reassign).toHaveBeenCalledWith("class-1", "teacher-next", 8, expect.any(String)));
    expect(await screen.findByText("Đã đổi giáo viên phụ trách.")).toBeTruthy();
    expect(await screen.findByText("Mã yêu cầu: 12345678")).toBeTruthy();
    await waitFor(() => expect(poll).toHaveBeenCalledWith("class-1", "12345678-1234-1234-1234-123456789012", expect.any(AbortSignal)));
    expect(onAssigned).toHaveBeenCalledTimes(1);
  });

  it("cancels reassignment without sending a request and leaves the card unlocked", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    const reassign = vi.spyOn(classService, "reassignTeacher");
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={vi.fn()} pollIntervalMs={2} />);

    await chooseTeacher();
    const trigger = screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }) as HTMLButtonElement;
    fireEvent.click(trigger);

    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Hủy" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(reassign).not.toHaveBeenCalled();
    expect(trigger.disabled).toBe(false);
    expect((screen.getByRole("button", { name: "Gỡ giáo viên phụ trách" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("confirms offboarding and shows the offboarded state", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    const offboard = vi.spyOn(classService, "offboardTeacher").mockResolvedValue(acceptedTransfer("OFFBOARD"));
    vi.spyOn(classService, "getAssignmentTransfer").mockResolvedValue(transferStatus("OFFBOARDED"));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    fireEvent.click(await screen.findByRole("button", { name: "Gỡ giáo viên phụ trách" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Gỡ giáo viên phụ trách?" })).toBeTruthy();
    expect(within(dialog).getByText(/Lớp sẽ không còn giáo viên phụ trách\./)).toBeTruthy();
    expect(offboard).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Gỡ giáo viên" }));

    await waitFor(() => expect(offboard).toHaveBeenCalledWith("class-1", 8, expect.any(String)));
    expect(await screen.findByText("Đã gỡ giáo viên phụ trách.")).toBeTruthy();
    await waitFor(() => expect(onAssigned).toHaveBeenCalledTimes(1));
  });

  it("clears an offboarded banner when a new Teacher assignment starts and succeeds", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "offboardTeacher").mockResolvedValue(acceptedTransfer("OFFBOARD"));
    vi.spyOn(classService, "getAssignmentTransfer").mockResolvedValue(transferStatus("OFFBOARDED"));
    let completeAssignment: () => void = () => {};
    const assign = vi.spyOn(classService, "assignTeacher").mockImplementation(() => new Promise((resolve) => {
      completeAssignment = () => resolve({
        kind: "assigned",
        assignment: {
          contract: "Be1AdultAssignmentV1",
          assignment_id: "assignment-next",
          candidate_ref: "teacher-next",
          role: "teacher",
          class_id: "class-1",
          active: true,
          assignment_revision: 10,
        },
      });
    }));
    const onAssigned = vi.fn();
    const { rerender } = render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    fireEvent.click(await screen.findByRole("button", { name: "Gỡ giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Gỡ giáo viên" }));
    expect(await screen.findByText("Đã gỡ giáo viên phụ trách.")).toBeTruthy();

    rerender(<TeacherAssignmentCard selectedClass={{ ...assignedClass, assignment_revision: 9, has_active_teacher: false }} onAssigned={onAssigned} pollIntervalMs={2} />);
    fireEvent.click(await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" }));
    fireEvent.click(await screen.findByRole("option", { name: "Cô Lan" }));
    fireEvent.click(screen.getByRole("button", { name: "Phân công" }));

    await waitFor(() => expect(assign).toHaveBeenCalledWith("class-1", "teacher-next", 9, expect.any(String)));
    expect(screen.queryByText("Đã gỡ giáo viên phụ trách.")).toBeNull();
    completeAssignment();
    expect(await screen.findByText("Đã phân công Giáo viên cho lớp.")).toBeTruthy();
    expect(screen.queryByText("Đã gỡ giáo viên phụ trách.")).toBeNull();
  });

  it("clears transfer banners when the selected class changes", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "offboardTeacher").mockResolvedValue(acceptedTransfer("OFFBOARD"));
    vi.spyOn(classService, "getAssignmentTransfer").mockResolvedValue(transferStatus("OFFBOARDED"));
    const { rerender } = render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={vi.fn()} pollIntervalMs={2} />);

    fireEvent.click(await screen.findByRole("button", { name: "Gỡ giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Gỡ giáo viên" }));
    expect(await screen.findByText("Đã gỡ giáo viên phụ trách.")).toBeTruthy();

    rerender(<TeacherAssignmentCard selectedClass={{ ...assignedClass, class_id: "class-2", display_name: "Lớp khác" }} onAssigned={vi.fn()} pollIntervalMs={2} />);

    await waitFor(() => expect(screen.queryByText("Đã gỡ giáo viên phụ trách.")).toBeNull());
  });

  it("cancels offboarding without sending a request and leaves the card unlocked", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    const offboard = vi.spyOn(classService, "offboardTeacher");
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={vi.fn()} pollIntervalMs={2} />);

    const trigger = await screen.findByRole("button", { name: "Gỡ giáo viên phụ trách" }) as HTMLButtonElement;
    fireEvent.click(trigger);

    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(offboard).not.toHaveBeenCalled();
    expect(trigger.disabled).toBe(false);
  });

  it("closes the confirm dialog and does nothing when the selected class changes while open", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    const reassign = vi.spyOn(classService, "reassignTeacher");
    const { rerender } = render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={vi.fn()} pollIntervalMs={2} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    expect(screen.getByRole("dialog")).toBeTruthy();

    rerender(<TeacherAssignmentCard selectedClass={{ ...assignedClass, class_id: "class-2", display_name: "Lớp Chồi 2" }} onAssigned={vi.fn()} pollIntervalMs={2} />);

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(reassign).not.toHaveBeenCalled();
  });

  it("reloads after offboarding returns a non-transfer 2xx contract", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "offboardTeacher").mockResolvedValue(null);
    const poll = vi.spyOn(classService, "getAssignmentTransfer");
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    fireEvent.click(await screen.findByRole("button", { name: "Gỡ giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Gỡ giáo viên" }));

    expect(await screen.findByText("Lớp đã thay đổi. Danh sách lớp đã được tải lại.")).toBeTruthy();
    expect(screen.queryByText(/Mã yêu cầu:/)).toBeNull();
    expect(poll).not.toHaveBeenCalled();
    expect(onAssigned).toHaveBeenCalledTimes(1);
  });

  it.each([
    ["RESOURCE_CONFLICT", "Lớp đã thay đổi hoặc đã có Giáo viên; đã tải lại."],
    ["INVALID_STATE_TRANSITION", "Lớp đã thay đổi hoặc đã có Giáo viên; đã tải lại."],
    ["STALE_REVISION", "Lớp đã thay đổi hoặc đã có Giáo viên; đã tải lại."],
    ["TEACHER_ASSIGNMENT_REQUIRED", "Lớp hiện không có Giáo viên phụ trách. Danh sách lớp đã được tải lại."],
  ])("reloads after %s", async (code, message) => {
    const list = vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "reassignTeacher").mockRejectedValue(new AdminBe1Error("conflict", 409, code));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));

    expect(await screen.findByText(message)).toBeTruthy();
    await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
    expect(screen.getByText(message)).toBeTruthy();
    expect(onAssigned).toHaveBeenCalledTimes(1);
  });

  it("reuses a key after network failures and creates a new key after each 4xx", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    const reassign = vi.spyOn(classService, "reassignTeacher")
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockRejectedValueOnce(new AdminBe1Error("conflict", 409, "STALE_REVISION"))
      .mockRejectedValueOnce(new AdminBe1Error("invalid request", 400, "INVALID_REQUEST"))
      .mockRejectedValueOnce(new TypeError("Failed to fetch"));
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={vi.fn()} pollIntervalMs={2} />);
    const button = await screen.findByRole("button", { name: "Đổi giáo viên phụ trách" });
    await chooseTeacher();

    for (let attempt = 1; attempt <= 5; attempt += 1) {
      fireEvent.click(button);
      fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));
      await waitFor(() => expect(reassign).toHaveBeenCalledTimes(attempt));
    }

    const keys = reassign.mock.calls.map((call) => call[3]);
    expect(keys[0]).toBe(keys[1]);
    expect(keys[1]).toBe(keys[2]);
    expect(keys[3]).not.toBe(keys[2]);
    expect(keys[4]).not.toBe(keys[3]);
  });

  it("reloads after reconciliation and lets the manager restart polling", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "reassignTeacher").mockResolvedValue(acceptedTransfer("REASSIGN"));
    const poll = vi.spyOn(classService, "getAssignmentTransfer")
      .mockResolvedValueOnce(transferStatus("RECONCILE_REQUIRED"))
      .mockResolvedValueOnce(transferStatus("COMPLETED"));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));

    expect(await screen.findByText("Chuyển giáo viên cần được theo dõi thêm.")).toBeTruthy();
    expect(screen.getByText("Cần quản lý theo dõi để hoàn tất việc chuyển giáo viên.")).toBeTruthy();
    await waitFor(() => expect(onAssigned).toHaveBeenCalledTimes(1));
    expect(poll).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra lại" }));
    expect(await screen.findByText("Đã đổi giáo viên phụ trách.")).toBeTruthy();
    await waitFor(() => expect(poll).toHaveBeenCalledTimes(2));
    expect(onAssigned).toHaveBeenCalledTimes(2);
  });

  it("stops on permanent poll 4xx and shows a manual follow-up", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "reassignTeacher").mockResolvedValue(acceptedTransfer("REASSIGN"));
    const poll = vi.spyOn(classService, "getAssignmentTransfer")
      .mockRejectedValue(new AdminBe1Error("forbidden", 403, "FORBIDDEN"));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));

    expect(await screen.findByText("Không thể tự động kiểm tra trạng thái chuyển giáo viên. Hãy kiểm tra lại để xem trạng thái mới nhất.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Kiểm tra lại" })).toBeTruthy();
    await waitFor(() => expect(onAssigned).toHaveBeenCalledTimes(1));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(poll).toHaveBeenCalledTimes(1);
  });

  it.each([
    ["network errors", new TypeError("Failed to fetch")],
    ["5xx responses", new AdminBe1Error("server error", 500, "SERVER_ERROR")],
    ["408 responses", new AdminBe1Error("timeout", 408, "REQUEST_TIMEOUT")],
    ["429 responses", new AdminBe1Error("rate limited", 429, "RATE_LIMITED")],
  ])("retries %s before polling completion", async (_label, retryCause) => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "reassignTeacher").mockResolvedValue(acceptedTransfer("REASSIGN"));
    const poll = vi.spyOn(classService, "getAssignmentTransfer")
      .mockRejectedValueOnce(retryCause)
      .mockResolvedValue(transferStatus("COMPLETED"));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={2} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));

    expect(await screen.findByText("Đã đổi giáo viên phụ trách.")).toBeTruthy();
    await waitFor(() => expect(poll).toHaveBeenCalledTimes(2));
    expect(onAssigned).toHaveBeenCalledTimes(1);
  });

  it("offers manual recheck after poll exhaustion and reloads the class list", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "reassignTeacher").mockResolvedValue(acceptedTransfer("REASSIGN"));
    let calls = 0;
    const poll = vi.spyOn(classService, "getAssignmentTransfer").mockImplementation(async () => {
      calls += 1;
      if (calls <= 30) throw new TypeError("Failed to fetch");
      return transferStatus("COMPLETED");
    });
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={onAssigned} pollIntervalMs={0} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));

    expect(await screen.findByText("Chưa có kết quả cuối cùng. Hãy kiểm tra lại trạng thái sau.")).toBeTruthy();
    expect(poll).toHaveBeenCalledTimes(30);
    await waitFor(() => expect(onAssigned).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra lại" }));

    expect(await screen.findByText("Đã đổi giáo viên phụ trách.")).toBeTruthy();
    await waitFor(() => expect(poll).toHaveBeenCalledTimes(31));
    expect(onAssigned).toHaveBeenCalledTimes(2);
  });

  it("stops the scheduled poll after unmount", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue(candidatesPage);
    vi.spyOn(classService, "reassignTeacher").mockResolvedValue(acceptedTransfer("REASSIGN"));
    const poll = vi.spyOn(classService, "getAssignmentTransfer");
    const view = render(<TeacherAssignmentCard selectedClass={assignedClass} onAssigned={vi.fn()} pollIntervalMs={1_000} />);

    await chooseTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));
    expect(await screen.findByText("Đang chuyển giáo viên phụ trách.")).toBeTruthy();
    view.unmount();
    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(poll).not.toHaveBeenCalled();
  });

  it("keeps suspended classes read-only", () => {
    const list = vi.spyOn(classService, "listTeacherCandidates");
    render(<TeacherAssignmentCard selectedClass={{ ...assignedClass, state: "suspended" }} onAssigned={vi.fn()} />);

    expect(screen.getByText(/không thể thay đổi giáo viên phụ trách/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Đổi giáo viên phụ trách" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Gỡ giáo viên phụ trách" })).toBeNull();
    expect(list).not.toHaveBeenCalled();
  });
});
