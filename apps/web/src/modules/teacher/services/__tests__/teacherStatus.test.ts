import { describe, expect, it } from "vitest";
import { teacherStatusMeta } from "../teacherStatus";

describe("teacherStatusMeta visibility labels", () => {
  it("maps school and selected audiences to Vietnamese visibility labels", () => {
    expect(teacherStatusMeta("SCHOOL", "visibility")).toEqual({ label: "Trong trường", tone: "info" });
    expect(teacherStatusMeta("SELECTED_AUDIENCE", "visibility")).toEqual({ label: "Chia sẻ chọn lọc", tone: "info" });
  });

  it("uses a clear fallback for unknown visibility values", () => {
    expect(teacherStatusMeta("UNRECOGNIZED", "visibility")).toEqual({ label: "Chưa rõ", tone: "neutral" });
    expect(teacherStatusMeta(undefined, "visibility")).toEqual({ label: "Chưa rõ", tone: "neutral" });
  });
});
