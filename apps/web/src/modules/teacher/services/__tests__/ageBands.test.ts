import { describe, expect, it } from "vitest";
import { isTeacherAgeBand, TEACHER_AGE_BANDS, teacherAgeBandForMonths, teacherAgeBandLabel } from "../ageBands";

describe("teacher age bands", () => {
  it("defines the three supported refs and Vietnamese labels", () => {
    expect(TEACHER_AGE_BANDS).toEqual([
      { ref: "age-36-71-months-v1", version: 1, label: "36–71 tháng" },
      { ref: "age-72-107-months-v1", version: 1, label: "72–107 tháng" },
      { ref: "age-108-120-months-v1", version: 1, label: "108–120 tháng" },
    ]);
  });

  it("accepts only a supported ref at version 1", () => {
    expect(isTeacherAgeBand("age-36-71-months-v1", 1)).toBe(true);
    expect(isTeacherAgeBand("age-36-71-months-v1", 2)).toBe(false);
    expect(isTeacherAgeBand("age-band-old", 1)).toBe(false);
  });

  it("maps each supported month boundary to the versioned lesson age band", () => {
    expect(teacherAgeBandForMonths(36)?.ref).toBe("age-36-71-months-v1");
    expect(teacherAgeBandForMonths(71)?.ref).toBe("age-36-71-months-v1");
    expect(teacherAgeBandForMonths(72)?.ref).toBe("age-72-107-months-v1");
    expect(teacherAgeBandForMonths(107)?.ref).toBe("age-72-107-months-v1");
    expect(teacherAgeBandForMonths(108)?.ref).toBe("age-108-120-months-v1");
    expect(teacherAgeBandForMonths(120)?.ref).toBe("age-108-120-months-v1");
    expect(teacherAgeBandForMonths(35)).toBeNull();
    expect(teacherAgeBandForMonths(121)).toBeNull();
    expect(teacherAgeBandForMonths(48.5)).toBeNull();
  });

  it("returns a safe label for unknown refs", () => {
    expect(teacherAgeBandLabel("age-72-107-months-v1")).toBe("72–107 tháng");
    expect(teacherAgeBandLabel("age-band-old")).toBe("Nhóm tuổi khác");
  });
});
