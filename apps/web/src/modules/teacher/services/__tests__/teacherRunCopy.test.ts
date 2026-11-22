import { describe, expect, it } from "vitest";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { copy, errorCopy } from "../teacherRunCopy";
const codes = ["ACTION_NOT_ALLOWED","TEACHER_ACTIVE_RUN_CONFLICT","ACTIVE_RUN_EXISTS","SAMPLE_VIDEO_ALREADY_EXISTS","LESSON_PLAN_NOT_APPROVED","INVALID_STATE_TRANSITION","STALE_REVISION","INVALID_REQUEST","INVALID_IDEMPOTENCY_KEY","MULTI_CHILD_NOT_SUPPORTED","TRANSCRIPT_NOT_CONFIRMED","SUBJECT_NOT_CONFIRMED","PROFILE_CONTEXT_NOT_CONFIRMED","STORY_REWRITE_LIMIT_REACHED","VIDEO_QUOTA_EXCEEDED","VIDEO_REGENERATION_LIMIT_REACHED","SUBSCRIPTION_RESTRICTED","AUDIO_TOO_LARGE","IMAGE_DIMENSIONS_EXCEEDED","MEDIA_TOO_LARGE","UNSUPPORTED_MEDIA_TYPE","UPLOAD_INCOMPLETE","UPLOAD_CHECKSUM_MISMATCH","UPLOAD_CONTENT_MISMATCH","INVALID_TOKEN","TOKEN_EXPIRED","RANGE_NOT_SATISFIABLE","NETWORK_ERROR"];
describe("teacher error copy",()=>{
 it.each(codes)("provides safe Vietnamese copy for %s",code=>{const message=errorCopy(new BackendApiError("raw",code,400)); expect(message).not.toBe(copy.generic); expect(message).not.toMatch(/\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b|http|upl_/i); expect(message).toMatch(/[À-ỹĐđ]/);});
 it("falls back for an unknown code and status",()=>{expect(errorCopy(new BackendApiError("raw","NEW_CODE",418))).toBe(copy.generic);expect(errorCopy(new Error("raw"))).toBe(copy.generic);});
});
