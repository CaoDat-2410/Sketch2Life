export const TEACHER_AGE_BANDS = [
  { ref: "age-36-71-months-v1", version: 1, label: "36–71 tháng" },
  { ref: "age-72-107-months-v1", version: 1, label: "72–107 tháng" },
  { ref: "age-108-120-months-v1", version: 1, label: "108–120 tháng" },
] as const;

export function isTeacherAgeBand(ref: string, version: number): boolean {
  return TEACHER_AGE_BANDS.some((band) => band.ref === ref && band.version === version);
}

export function teacherAgeBandForMonths(ageMonths: number): (typeof TEACHER_AGE_BANDS)[number] | null {
  if (!Number.isInteger(ageMonths) || ageMonths < 36 || ageMonths > 120) return null;
  if (ageMonths <= 71) return TEACHER_AGE_BANDS[0];
  if (ageMonths <= 107) return TEACHER_AGE_BANDS[1];
  return TEACHER_AGE_BANDS[2];
}

export function teacherAgeBandLabel(ref: string): string {
  return TEACHER_AGE_BANDS.find((band) => band.ref === ref)?.label ?? "Nhóm tuổi khác";
}
