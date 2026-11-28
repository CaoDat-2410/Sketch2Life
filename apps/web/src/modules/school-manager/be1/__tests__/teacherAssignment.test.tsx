import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { AdminBe1Error } from "../services/be1Client";
import { classService, type Be1Class } from "../services/classService";
import { TeacherAssignmentCard } from "../pages/TeacherAssignmentCard";

const openClass: Be1Class = {
  class_id: "class-1",
  display_name: "Lớp Lá 1",
  state: "active",
  assignment_revision: 1,
  has_active_teacher: false,
};

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

describe("classService M9-B requests", () => {
  it("pages candidates and sends If-Match and Idempotency-Key on assignment", async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
      calls.push({ url, init });
      const body = calls.length === 1
        ? { contract: "Be1TeacherCandidatePageV1", items: [], next_cursor: null }
        : { contract: "Be1AdultAssignmentV1", assignment_id: "a-1", candidate_ref: "ref-1", role: "teacher", class_id: "class-1", active: true, assignment_revision: 4 };
      return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
    }));
    const { authService } = await import("../services/authService");
    vi.spyOn(authService, "getIdToken").mockResolvedValue("unit-test-id-token");

    await classService.listTeacherCandidates("c2");
    const assignment = await classService.assignTeacher("class-1", "ref-1", 3, "key-1");

    expect(calls[0].url).toBe("https://api.example.test/api/be1/v1/organizations/org-test/teacher-candidates?limit=25&cursor=c2");
    const headers = new Headers(calls[1].init.headers);
    expect(calls[1].url).toBe("https://api.example.test/api/be1/v1/classes/class-1/assignments");
    expect(headers.get("If-Match")).toBe('"3"');
    expect(headers.get("Idempotency-Key")).toBe("key-1");
    expect(JSON.parse(String(calls[1].init.body))).toEqual({ candidate_ref: "ref-1" });
    expect(assignment).toEqual({
      kind: "assigned",
      assignment: { contract: "Be1AdultAssignmentV1", assignment_id: "a-1", candidate_ref: "ref-1", role: "teacher", class_id: "class-1", active: true, assignment_revision: 4 },
    });
  });
});

describe("Teacher assignment card (FEAT-066 M9-B)", () => {
  it("assigns the chosen candidate with the class revision and reports success", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1",
      items: [{ candidate_ref: "ref-1", display_name: "Cô Lan" }, { candidate_ref: "ref-2", display_name: null }],
      next_cursor: null,
    });
    const assign = vi.spyOn(classService, "assignTeacher").mockResolvedValue({
      kind: "assigned",
      assignment: {
        contract: "Be1AdultAssignmentV1", assignment_id: "a-1", candidate_ref: "ref-1", role: "teacher",
        class_id: "class-1", active: true, assignment_revision: 2,
      },
    });
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={openClass} onAssigned={onAssigned} />);

    const select = await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" });
    fireEvent.click(select);
    expect(await screen.findByRole("option", { name: "Cô Lan" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Giáo viên chưa có tên hiển thị" })).toBeTruthy();
    // Nothing is preselected: the button stays disabled until a Teacher is chosen.
    expect((screen.getByRole("button", { name: "Phân công" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("option", { name: "Cô Lan" }));
    fireEvent.click(screen.getByRole("button", { name: "Phân công" }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith("class-1", "ref-1", 1, expect.any(String)));
    expect(await screen.findByText("Đã phân công Giáo viên cho lớp.")).toBeTruthy();
    expect(onAssigned).toHaveBeenCalledTimes(1);
  });

  it("reuses the key for a retry and reloads after a conflict or a uniform 404", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1", items: [{ candidate_ref: "ref-1", display_name: "Cô Lan" }], next_cursor: null,
    });
    const assign = vi.spyOn(classService, "assignTeacher")
      .mockRejectedValueOnce(new Error("Mất kết nối"))
      .mockRejectedValueOnce(new AdminBe1Error("x", 409, "STALE_REVISION"))
      .mockRejectedValueOnce(new AdminBe1Error("x", 404, "RESOURCE_NOT_FOUND"));
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={openClass} onAssigned={onAssigned} />);
    const select = await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" });
    fireEvent.click(select);
    fireEvent.click(await screen.findByRole("option", { name: "Cô Lan" }));
    const button = screen.getByRole("button", { name: "Phân công" });

    fireEvent.click(button);
    expect(await screen.findByText("Mất kết nối")).toBeTruthy();
    fireEvent.click(button);
    expect(await screen.findByText("Lớp đã thay đổi hoặc đã có Giáo viên; đã tải lại.")).toBeTruthy();
    await waitFor(() => expect((screen.getByRole("button", { name: "Phân công" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Phân công" }));
    expect(await screen.findByText("Không thể hoàn tất phân công; danh sách đã được tải lại.")).toBeTruthy();
    expect(assign.mock.calls[1][3]).toBe(assign.mock.calls[0][3]);
    expect(assign.mock.calls[2][3]).not.toBe(assign.mock.calls[1][3]);
    expect(onAssigned).toHaveBeenCalledTimes(2);
  });

  it("offers reassignment and offboarding, and keeps missing-revision and empty states", async () => {
    const list = vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1", items: [], next_cursor: null,
    });
    const { rerender } = render(<TeacherAssignmentCard selectedClass={{ ...openClass, has_active_teacher: true }} onAssigned={vi.fn()} />);
    expect(await screen.findByText("Chưa có Giáo viên nào khác của tổ chức đủ điều kiện.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Gỡ giáo viên phụ trách" })).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(1);
    rerender(<TeacherAssignmentCard selectedClass={{ class_id: "class-2", display_name: "Lớp Chồi", state: "active" }} onAssigned={vi.fn()} />);
    expect(screen.getByText(/chưa thể thay đổi giáo viên/)).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(1);
    rerender(<TeacherAssignmentCard selectedClass={openClass} onAssigned={vi.fn()} />);
    expect(await screen.findByText("Chưa có Giáo viên nào của tổ chức đủ điều kiện.")).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("reloads after a reassign response without the transfer contract", async () => {
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1",
      items: [{ candidate_ref: "ref-1", display_name: "Cô Lan" }],
      next_cursor: null,
    });
    vi.spyOn(classService, "reassignTeacher").mockResolvedValue(null);
    const poll = vi.spyOn(classService, "getAssignmentTransfer");
    const onAssigned = vi.fn();
    render(<TeacherAssignmentCard selectedClass={{ ...openClass, has_active_teacher: true }} onAssigned={onAssigned} />);

    fireEvent.click(await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" }));
    fireEvent.click(await screen.findByRole("option", { name: "Cô Lan" }));
    fireEvent.click(screen.getByRole("button", { name: "Đổi giáo viên phụ trách" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đổi giáo viên" }));

    expect(await screen.findByText("Lớp đã thay đổi. Danh sách lớp đã được tải lại.")).toBeTruthy();
    expect(screen.queryByText(/Mã yêu cầu:/)).toBeNull();
    expect(poll).not.toHaveBeenCalled();
    expect(onAssigned).toHaveBeenCalledTimes(1);
  });
});
