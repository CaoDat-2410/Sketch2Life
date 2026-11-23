import { describe, expect, it } from "vitest";
import type { Occurrence } from "../../../../shared/api/teacherOccurrenceApi";
import type { TeacherRun } from "../../../../shared/api/teacherRunApi";
import { availableActions, entryLinks, shouldPoll, waitingForFirstStory } from "../teacherRunLogic";
import { stateLabel } from "../teacherRunCopy";
describe("Teacher sample run logic", () => {
 it("gates links by occurrence and slot", () => {
  const o = { state: "DRAFT", sample_video: { slot_state: "AVAILABLE" } } as Occurrence;
  expect(entryLinks(o)).toEqual({ sample: false, projection: false });
  for (const state of ["APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"] as const) expect(entryLinks({ ...o, state }).sample).toBe(true);
  expect(entryLinks({ ...o, sample_video: { ...o.sample_video, slot_state: "CLAIMED" } }).projection).toBe(true);
  expect(entryLinks({ ...o, state: "SAMPLE_USED" }).projection).toBe(true);
 });
 it("polls work but not input waiting", () => {
  const r = { run_state: "INPUT_PROCESSING", job_state: null } as TeacherRun;
  expect(shouldPoll(r)).toBe(false); expect(shouldPoll(r,"PENDING")).toBe(true);
  for (const state of ["STORY_GENERATING", "SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN", "VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED", "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING"]) expect(shouldPoll({ ...r, run_state: state })).toBe(true);
  expect(shouldPoll({ ...r, job_state:"RUNNING" })).toBe(true); expect(availableActions({ ...r, run_state:"COMPLETED" }).cancel).toBe(false); expect(stateLabel("FUTURE_STATE")).toBe("Đang cập nhật");
 });
 it("covers every known run state and all polling job states", () => {
  const r = { run_state: "DRAFT", job_state: null } as TeacherRun;
  const terminal = new Set(["COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"]);
  const states = ["DRAFT", "INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW", "PREPARATION_REVIEW", "STORY_GENERATING", "SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN", "SCRIPT_REVIEW", "VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED", "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING", "VIDEO_READY", "SAFETY_BLOCKED", ...terminal];
  for (const state of states) {
   expect(stateLabel(state)).not.toBe("Đang cập nhật");
   expect(availableActions({ ...r, run_state: state }).cancel).toBe(!terminal.has(state));
  }
  for (const job_state of ["QUEUED", "RUNNING", "AWAITING_RECONCILIATION"]) expect(shouldPoll({ ...r, job_state })).toBe(true);
  for (const job_state of ["SUCCEEDED", "FAILED", "FUTURE"]) expect(shouldPoll({ ...r, job_state })).toBe(false);
  expect(shouldPoll({ ...r, run_state: "SCRIPT_REVIEW", job_state: "FAILED" })).toBe(false);
  for (const transcript of ["NONE", "NEEDS_CONFIRMATION", "CONFIRMED", "FAILED"]) expect(shouldPoll(r, transcript)).toBe(false);
 });
 it("shows first-story waiting only when visible Teacher gates are complete", () => {
  const waiting = { run_state: "PREPARATION_REVIEW", context_confirmed: true, candidate: { candidate_subject: "tree", visible_features: [] }, activity: { plan_activity_id: "activity" }, story_revision_no: null } as unknown as TeacherRun;
  expect(waitingForFirstStory(waiting)).toBe(true);
  expect(waitingForFirstStory({ ...waiting, context_confirmed: false })).toBe(false);
  expect(waitingForFirstStory({ ...waiting, candidate: null })).toBe(false);
  expect(waitingForFirstStory({ ...waiting, activity: null })).toBe(false);
  expect(shouldPoll({ ...waiting, run_state: "SCRIPT_GENERATING", job_state: "QUEUED" })).toBe(true);
  expect(shouldPoll({ ...waiting, run_state: "SAFETY_BLOCKED", job_state: "FAILED" })).toBe(false);
 });
});
