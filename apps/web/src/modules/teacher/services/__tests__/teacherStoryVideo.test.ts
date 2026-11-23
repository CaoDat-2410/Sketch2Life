import { describe, expect, it } from "vitest";
import type { TeacherRun } from "../../../../shared/api/teacherRunApi";
import { canRewrite, validHint } from "../teacherStoryVideo";

describe("story review gates", () => {
  const run = { run_state: "SCRIPT_REVIEW", story_revision_no: 1, story_status: "DRAFT", story: {}, video: null } as TeacherRun;
  it("accepts blank and trimmed hints, but rejects controls and more than 400 code points", () => { expect(validHint("   ")).toBe(true); expect(validHint(" a ")).toBe(true); expect(validHint("a\nb")).toBe(false); expect(validHint("😀".repeat(401))).toBe(false); });
  it("gates rewrite on revision, backend confirmation flag, and the request cap", () => { expect(canRewrite(run)).toBe(true); expect(canRewrite({ ...run, story_confirmation_required: false })).toBe(true); expect(canRewrite({ ...run, story_revision_no: 4 })).toBe(false); expect(canRewrite({ ...run, story_status: "CONFIRMED" })).toBe(false); expect(canRewrite({ ...run, story_status: "CONFIRMED", video: { history: [{ state: "REJECTED_BY_ADULT" }] } as TeacherRun["video"] })).toBe(true); expect(canRewrite({ ...run, run_state: "SCRIPT_REVIEW", story_status: "CONFIRMED", story_confirmation_required: true })).toBe(true); expect(canRewrite({ ...run, run_state: "SCRIPT_REVIEW", story_status: "CONFIRMED", story_confirmation_required: false })).toBe(false); expect(canRewrite({ ...run, run_state: "SAFETY_BLOCKED", story_confirmation_required: true })).toBe(true); expect(canRewrite({ ...run, video: { video_requests_used: 3 } as TeacherRun["video"] })).toBe(false); });
});
