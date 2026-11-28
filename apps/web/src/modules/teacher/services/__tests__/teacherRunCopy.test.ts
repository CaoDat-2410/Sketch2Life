import { describe, expect, it } from "vitest";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { copy, deleteErrorCopy, errorCopy } from "../teacherRunCopy";
const codes = ["ACTION_NOT_ALLOWED","TEACHER_ACTIVE_RUN_CONFLICT","ACTIVE_RUN_EXISTS","SAMPLE_VIDEO_ALREADY_EXISTS","LESSON_PLAN_NOT_APPROVED","INVALID_STATE_TRANSITION","STALE_REVISION","INVALID_REQUEST","INVALID_IDEMPOTENCY_KEY","MULTI_CHILD_NOT_SUPPORTED","TRANSCRIPT_NOT_CONFIRMED","SUBJECT_NOT_CONFIRMED","PROFILE_CONTEXT_NOT_CONFIRMED","STORY_REWRITE_LIMIT_REACHED","VIDEO_QUOTA_EXCEEDED","VIDEO_REGENERATION_LIMIT_REACHED","SUBSCRIPTION_RESTRICTED","PARENT_STORE_UNAVAILABLE","PARENT_STORY_RUN_STORE_UNAVAILABLE","DEPENDENCY_UNAVAILABLE","AUDIO_TOO_LARGE","IMAGE_DIMENSIONS_EXCEEDED","MEDIA_TOO_LARGE","UNSUPPORTED_MEDIA_TYPE","UPLOAD_INCOMPLETE","UPLOAD_CHECKSUM_MISMATCH","UPLOAD_CONTENT_MISMATCH","INVALID_TOKEN","TOKEN_EXPIRED","RANGE_NOT_SATISFIABLE","NETWORK_ERROR"];
describe("teacher error copy",()=>{
 it("uses the short sample video page title",()=>{expect(copy.title).toBe("Video mẫu");});
 it.each(codes)("provides safe Vietnamese copy for %s",code=>{const message=errorCopy(new BackendApiError("raw",code,400)); expect(message).not.toBe(copy.generic); expect(message).not.toMatch(/\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b|http|upl_/i); expect(message).toMatch(/[À-ỹĐđ]/);});
 it.each([
  ["QUOTA_ALLOCATION_NOT_FOUND", "chưa phân bổ"],
  ["TEACHER_QUOTA_INSUFFICIENT", "đã dùng hết"],
  ["SCHOOL_QUOTA_INSUFFICIENT", "Nhà trường đã hết"],
 ])("explains the BR-38 quota refusal %s", (code, phrase) => {
  expect(errorCopy(new BackendApiError("raw", code, 409))).toContain(phrase);
 });
 it("falls back for an unknown code and status",()=>{expect(errorCopy(new BackendApiError("raw","NEW_CODE",418))).toBe(copy.generic);expect(errorCopy(new Error("raw"))).toBe(copy.generic);});
 it("maps store and dependency failures by code and keeps plan-fence copy local",()=>{for(const code of ["PARENT_STORE_UNAVAILABLE","PARENT_STORY_RUN_STORE_UNAVAILABLE","DEPENDENCY_UNAVAILABLE"]) expect(errorCopy(new BackendApiError("server secret",code,503))).toBe(copy.dependencyUnavailable);expect(errorCopy(new BackendApiError("server secret","VIDEO_REGENERATION_LIMIT_REACHED",409))).toContain("hủy lượt");expect(errorCopy(new BackendApiError("server secret","INVALID_STATE_TRANSITION",409))).not.toContain("server secret");expect(errorCopy(new BackendApiError("server secret","STALE_REVISION",409))).not.toContain("server secret");});
 it("maps settled-run delete conflict and not-found safely",()=>{expect(deleteErrorCopy(new BackendApiError("raw","INVALID_STATE_TRANSITION",409))).toBe(copy.deleteConflict);expect(deleteErrorCopy(new BackendApiError("raw","RESOURCE_NOT_FOUND",404))).toContain("Không tìm thấy");expect(copy.deleteConfirm).toContain("không thể hoàn tác");});
});
