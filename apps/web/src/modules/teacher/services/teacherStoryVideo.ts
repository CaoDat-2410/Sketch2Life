import type { TeacherRun } from "../../../shared/api/teacherRunApi";

export type QualityReason = "QUALITY_LOW" | "NOT_MATCHING_STORY" | "CONTENT_CONCERN" | "OTHER";
export function validHint(value: string): boolean {
  return Array.from(value).every(char => { const code = char.codePointAt(0)!; return code > 31 && (code < 127 || code > 159); }) && Array.from(value.trim()).length <= 400;
}
export function canRewrite(run: TeacherRun): boolean {
  return run.run_state === "SCRIPT_REVIEW" && run.story_revision_no !== null && run.story_revision_no < 4 && !!run.story &&
    (run.story_status === "DRAFT" || run.story_status === "FAILED" || (run.story_status === "CONFIRMED" && !!run.video?.history.some(item => item.state === "REJECTED_BY_ADULT")));
}
