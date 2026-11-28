import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { TeacherAssignmentCard } from "../pages/TeacherAssignmentCard";
import { classService, teacherCandidateLabel, teacherCandidateLabels, type Be1Class } from "../services/classService";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

const assigned: Be1Class = { class_id: "class-1", display_name: "Lớp Mầm", state: "active", assignment_revision: 3, has_active_teacher: true };

describe("Teacher candidates", () => {
  it("tells candidates apart by name and masked e-mail", () => {
    expect(teacherCandidateLabel({ candidate_ref: "a", display_name: "Cô Lan", email_masked: "l***@school.test" })).toBe("Cô Lan · l***@school.test");
    expect(teacherCandidateLabel({ candidate_ref: "b", display_name: null, email_masked: "m***@school.test" })).toBe("m***@school.test");
    expect(teacherCandidateLabel({ candidate_ref: "c", display_name: null })).toBe("Giáo viên chưa có tên hiển thị");
  });

  it("adds stable ordinals to repeated labels without exposing candidate references", async () => {
    const candidates = [
      { candidate_ref: "private-ref-a", display_name: null, email_masked: "m***@school.test" },
      { candidate_ref: "private-ref-b", display_name: null, email_masked: "m***@school.test" },
      { candidate_ref: "private-ref-c", display_name: null },
      { candidate_ref: "private-ref-d", display_name: null },
    ];
    expect(teacherCandidateLabels(candidates)).toEqual([
      "m***@school.test (1)",
      "m***@school.test (2)",
      "Giáo viên chưa có tên hiển thị (1)",
      "Giáo viên chưa có tên hiển thị (2)",
    ]);
    vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1", items: candidates, next_cursor: null,
    });

    render(<TeacherAssignmentCard selectedClass={assigned} onAssigned={() => undefined} />);

    fireEvent.click(await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" }));
    expect(await screen.findByRole("option", { name: "m***@school.test (1)" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "m***@school.test (2)" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Giáo viên chưa có tên hiển thị (1)" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Giáo viên chưa có tên hiển thị (2)" })).toBeTruthy();
    expect(screen.queryByText(/private-ref/)).toBeNull();
    expect(await screen.findByText("Hiển thị tên và email đã được che (nếu có); không hiển thị mã định danh đăng nhập.")).toBeTruthy();
  });

  it("asks with the class and does not offer the current Teacher as a new one", async () => {
    const list = vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1", next_cursor: null,
      items: [
        { candidate_ref: "now", display_name: null, email_masked: "n***@school.test", is_current: true },
        { candidate_ref: "other", display_name: null, email_masked: "o***@school.test", is_current: false },
      ],
    });
    render(<TeacherAssignmentCard selectedClass={assigned} onAssigned={() => undefined} />);
    await vi.waitFor(() => expect(list).toHaveBeenCalledWith(undefined, "class-1"));
    expect(await screen.findByText("o***@school.test", { selector: "option" })).toBeTruthy();
    expect(screen.queryByText("n***@school.test")).toBeNull();
  });
});
