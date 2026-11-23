import type { TeacherLessonDetail } from "./backendApi";

type LessonShareGateInput = Pick<TeacherLessonDetail, "state"> & {
  current_version?: Pick<TeacherLessonDetail["current_version"], "version_id"> | null;
};

export type PrivateShareGateResult =
  | { allowed: true }
  | { allowed: false; reason: "NO_CURRENT_VERSION" | "ARCHIVED" };

// Only a PUBLIC audience needs a School Manager decision (SRS FR-PL-05 l.2646, FR-PL-06 l.2647, BR-51 l.2676).
export function privateShareGate(lesson: LessonShareGateInput | null | undefined): PrivateShareGateResult {
  if (lesson?.state === "ARCHIVED") return { allowed: false, reason: "ARCHIVED" };
  if (!lesson?.current_version?.version_id) return { allowed: false, reason: "NO_CURRENT_VERSION" };
  return { allowed: true };
}
