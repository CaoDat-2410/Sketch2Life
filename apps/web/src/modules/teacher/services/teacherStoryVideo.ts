import type { TeacherRun } from "../../../shared/api/teacherRunApi";

export type QualityReason = "QUALITY_LOW" | "NOT_MATCHING_STORY" | "CONTENT_CONCERN" | "OTHER";
export function validHint(value: string): boolean {
  return Array.from(value).every(char => { const code = char.codePointAt(0)!; return code > 31 && (code < 127 || code > 159); }) && Array.from(value.trim()).length <= 400;
}
export function canRewrite(run: TeacherRun): boolean {
  if (!["SCRIPT_REVIEW", "SAFETY_BLOCKED"].includes(run.run_state) || run.story_revision_no === null || run.story_revision_no >= 4 || !run.story || (run.video?.video_requests_used ?? 0) >= 3) return false;
  if (run.story_confirmation_required === true) return true;
  return run.story_status === "DRAFT" || run.story_status === "FAILED" || (run.story_status === "CONFIRMED" && !!run.video?.history.some(item => item.state === "REJECTED_BY_ADULT"));
}
