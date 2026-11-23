import { inputActions } from "./teacherRunInputs";
import type { TeacherRun } from "../../../shared/api/teacherRunApi";
import type { Occurrence } from "../../../shared/api/teacherOccurrenceApi";
const running = new Set(["STORY_GENERATING", "SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN", "VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED", "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING"]);
export function shouldPoll(run: TeacherRun, transcriptState?: string | null): boolean { if (["VIDEO_READY", "SAFETY_BLOCKED", "COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"].includes(run.run_state)) return false; return running.has(run.run_state) || ["QUEUED", "RUNNING", "AWAITING_RECONCILIATION"].includes(run.job_state ?? "") || transcriptState === "PENDING"; }
const cancellable = new Set(["DRAFT", "INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW", "PREPARATION_REVIEW", "STORY_GENERATING", "SCRIPT_GENERATING", "SCRIPT_GENERATION_UNKNOWN", "SCRIPT_REVIEW", "VIDEO_ADMISSION_PENDING", "VIDEO_QUEUED", "VIDEO_GENERATING", "VIDEO_SAFETY_VALIDATING", "VIDEO_READY", "SAFETY_BLOCKED"]);
export function availableActions(run: TeacherRun): { cancel: boolean; artwork: boolean; idea: boolean; transcript: boolean; context: boolean; subject: boolean } { return { cancel: cancellable.has(run.run_state), ...inputActions(run) }; }
export function waitingForFirstStory(run: TeacherRun): boolean { return run.run_state === "PREPARATION_REVIEW" && run.context_confirmed && !!run.candidate?.candidate_subject && !!run.activity?.plan_activity_id && run.story_revision_no === null; }
export function entryLinks(o: Occurrence) { return { sample: ["APPROVED", "SAMPLE_AVAILABLE", "SAMPLE_USED"].includes(o.state), projection: o.sample_video.slot_state === "CLAIMED" || o.state === "SAMPLE_USED" }; }
