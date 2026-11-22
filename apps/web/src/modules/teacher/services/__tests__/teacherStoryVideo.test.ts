import { describe, expect, it } from "vitest";
import type { TeacherRun } from "../../../../shared/api/teacherRunApi";
import { canRewrite, validHint } from "../teacherStoryVideo";

describe("story review gates", () => {
  const run = { run_state: "SCRIPT_REVIEW", story_revision_no: 1, story_status: "DRAFT", story: {}, video: null } as TeacherRun;
  it("accepts blank and trimmed hints, but rejects controls and more than 400 code points", () => { expect(validHint("   ")).toBe(true); expect(validHint(" a ")).toBe(true); expect(validHint("a\nb")).toBe(false); expect(validHint("😀".repeat(401))).toBe(false); });
  it("gates rewrite on revision and rejected history", () => { expect(canRewrite(run)).toBe(true); expect(canRewrite({ ...run, story_revision_no: 4 })).toBe(false); expect(canRewrite({ ...run, story_status: "CONFIRMED" })).toBe(false); expect(canRewrite({ ...run, story_status: "CONFIRMED", video: { history: [{ state: "REJECTED_BY_ADULT" }] } as TeacherRun["video"] })).toBe(true); });
});
