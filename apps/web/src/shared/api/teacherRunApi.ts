import { BackendApiError } from "./backendApi";
import { data, enc, ifNoneMatch, request, write } from "./teacherHttp";

export interface ChildSelection {
  selection_id: string | null; occurrence_id: string; outcome: "SELECTED" | "NO_ELIGIBLE_CHILD";
  state: "OPEN" | "CONFIRMED" | "CONSUMED" | "EXPIRED" | "STALE" | "VOID" | "EMPTY" | "STOPPED";
  contract?: "ChildSelectionV1"; draw_no?: number | null; issued_at?: string | null;
  revision: number | null; selection_sha256: string | null; reselect_available: boolean;
  expires_at: string | null; confirmation_expires_at: string | null; consumed_run_ref: string | null;
  plan: { revision_no: number; plan_hash: string } | null;
  child: { profile_id: string; display_name: string; age_months: number } | null;
}
export interface TeacherRun {
  run_id: string; occurrence_id: string | null; run_state: string; run_revision: number;
  context_revision: number; context_snapshot_sha256: string | null; context_confirmed: boolean;
  context_snapshot: { age_months: number; objectives?: string[]; teacher_direction?: string; activity_title?: string | null } | null;
  understanding_revision: number | null; candidate: { candidate_subject: string | null; visible_features: string[] } | null;
  story_revision_no: number | null; story_status: string | null; story_sha256: string | null;
  story: { title: string; story: { opening: string; middle: string; ending: string }; scenes: Array<{ title: string; action?: string; narration?: string; scene_index?: number; start_ms?: number; duration_ms?: number }> } | null; job_state: string | null;
  quota?: { state: "UNAVAILABLE"; granted: number | null; used: number | null; available: number | null; month: string | null };
  video: { state: string; current_generation_id: string | null; video_requests_used: number; video_requests_remaining: number; job?: { job_id: string; state: string; stage: string | null; retryable: boolean; error_code: string | null } | null; playback: { state: string }; history: Array<{ state: string }> } | null;
}
export interface Lifecycle { run_id: string; run_state: "DELETE_PENDING" | "DELETED"; revision: number; version: number; lifecycle_request_ref: string; purge_state: string }
export type LifecycleEnvelope = { request_id: string; lifecycle: Lifecycle };
export type RunResponse = { request_id: string; story_run: TeacherRun } | LifecycleEnvelope;
export type ActiveResponse = { request_id: string; story_run: TeacherRun | null } | { request_id: string; lifecycle: Lifecycle };
export interface TeacherCreateInput {
  profile_ref: { kind: "MANAGED_PROFILE"; id: string }; occurrence_id: string;
  plan: { revision_no: number; plan_hash: string }; activity_id: string; selection_id: string; selection_sha256: string;
}
export interface Transcript { state: string; text: string | null; transcript_revision: number | null; transcript_sha256: string | null; run_revision?: number; origin?: string | null; language?: string | null; error_code?: string | null }
export interface ProjectionReceipt { contract: "ClassProjectionConfirmationV1"; occurrence_id: string; run_id: string; generation_id: string; audience: "CLASS"; use: "CLASS_PROJECTION"; confirmed_at: string; confirmed_by_ref: string; assignment: { class_revision: number }; plan: { revision_no: number; plan_hash: string; is_current: boolean }; occurrence_revision: number; sample_video: { slot_state: "AVAILABLE" | "CLAIMED"; claimed_at: string | null; run_ref: string | null } }
export interface ProjectionGrant { contract: "ProjectionPlaybackTokenV1"; token: string; expires_at: string; stream_path: string; media_type: "video/mp4" }
export interface PlaybackToken { token: string; expires_at: string; stream_path: string; media_type: "video/mp4"; asset_ref: string }
const occurrence = (id: string) => `/v1/lesson-occurrences/${enc(id)}`;
const selection = (id: string, selectionId?: string) => `${occurrence(id)}/child-selections${selectionId ? `/${enc(selectionId)}` : ""}`;
const run = (id: string) => `/v1/story-runs/${enc(id)}`;

export type IdeaInput = { expected_run_revision: number; text?: string; audio_ref?: string; transcript_correction?: never } | { expected_run_revision: number; transcript_correction: { base_revision: number; text: string }; text?: never; audio_ref?: never };
function submitIdea<T>(id: string, input: IdeaInput, key: string, send: () => Promise<T>): Promise<T> {
  void id; void key;
  const correction = input.transcript_correction;
  if ((correction && (input.text !== undefined || input.audio_ref !== undefined)) || (!correction && !input.text && !input.audio_ref)) return Promise.reject(new BackendApiError("", "INVALID_REQUEST", 400));
  return send();
}

export const teacherRunApi = {
  draw: (id: string, key: string) => write<ChildSelection>(selection(id), "POST", key, {}),
  getSelection: (id: string, selectionId: string, etag?: string) => request<ChildSelection>(selection(id, selectionId), { headers: ifNoneMatch(etag) }, true),
  confirmSelection: (id: string, selectionId: string, revision: number, hash: string, key: string) => write<ChildSelection>(`${selection(id, selectionId)}/confirmation`, "POST", key, { expected_selection_sha256: hash }, { "If-Match": `"${revision}"` }),
  active: () => request<ActiveResponse>("/v1/story-runs/active/current").then(data),
  create: (input: TeacherCreateInput, key: string) => write<RunResponse>("/v1/story-runs", "POST", key, input),
  get: (id: string, etag?: string, signal?: AbortSignal) => request<RunResponse>(run(id), { headers: ifNoneMatch(etag), signal }, true),
  cancel: (id: string, revision: number, key: string) => write<RunResponse>(`${run(id)}/cancel`, "POST", key, { expected_revision: revision }),
  attachArtwork: (id: string, asset: string, revision: number, key: string) => write<{ request_id: string; story_run_id: string; input_revision: number; run_revision: number; run_state: string; analysis_state: string; asset_ref: string; asset_kind: "DRAWING"; asset_state: "READY" } | LifecycleEnvelope>(`${run(id)}/assets`, "POST", key, { asset_ref: asset, expected_run_revision: revision }),
  idea: (id: string, input: IdeaInput, key: string) => submitIdea(id, input, key, () => write<{ request_id: string; story_run_id: string; input_revision: number; run_revision: number; run_state: string; idea_source: "TEXT" | "VOICE" | "TEXT_AND_VOICE" | null; transcript: { transcript_revision: number; state: string } | null } | LifecycleEnvelope>(`${run(id)}/idea`, "POST", key, input)),
  transcript: (id: string, signal?: AbortSignal) => request<Transcript>(`${run(id)}/transcript`, { signal }).then(data),
  confirmTranscript: (id: string, revision: number, hash: string, key: string) => write<{ request_id: string; story_run_id: string; transcript_revision: number; run_revision: number; run_state: string; state: "CONFIRMED" } | LifecycleEnvelope>(`${run(id)}/transcript-confirmation`, "POST", key, { expected_transcript_revision: revision, transcript_sha256: hash, confirmed: true }),
  confirmContext: (id: string, revision: number, hash: string, key: string) => write<RunResponse>(`${run(id)}/context-confirmation`, "POST", key, { expected_context_revision: revision, context_snapshot_sha256: hash, confirmed: true }),
  confirmSubject: (id: string, revision: number, subject: string, key: string) => write<{ request_id: string; decision: "CONFIRMED" | "RERUN_REQUESTED"; understanding_revision: number; run_revision: number } | LifecycleEnvelope>(`${run(id)}/subject-confirmation`, "POST", key, { expected_understanding_revision: revision, confirmed_subject: subject }),
  rewrite: (id: string, revision: number, hash: string | undefined, hint: string | undefined, key: string) => write<{ request_id: string; story_run_id: string; story_revision_no: number; run_revision: number; run_state: "SCRIPT_GENERATING" } | LifecycleEnvelope>(`${run(id)}/story-rewrites`, "POST", key, { expected_story_revision: revision, ...(hash ? { expected_story_sha256: hash } : {}), ...(hint ? { hint } : {}) }),
  confirmStory: (id: string, revision: number, hash: string, key: string) => write<RunResponse>(`${run(id)}/script-confirmation`, "POST", key, { expected_revision: revision, story_sha256: hash }),
  generateVideo: (id: string, revision: number, hash: string, reason: string | undefined, key: string) => write<{ request_id: string; video_generation: { generation_id: string; state: string; generation_no: number | null; kind: "INITIAL" | "QUALITY_REGEN"; job_id: string | null; run_state: string; run_revision: number } } | LifecycleEnvelope>(`${run(id)}/video-generations`, "POST", key, { expected_revision: revision, story_sha256: hash, ...(reason ? { quality_reason_code: reason } : {}) }),
  unsuitable: (id: string, revision: number, generation: string, reason: string, key: string) => write<RunResponse>(`${run(id)}/video-unsuitable`, "POST", key, { expected_revision: revision, generation_id: generation, reason_code: reason }),
  complete: (id: string, revision: number, key: string) => write<RunResponse>(`${run(id)}/complete`, "POST", key, { expected_revision: revision }),
  ownerToken: (id: string) => request<{ playback: PlaybackToken }>(`${run(id)}/playback-token`, { method: "POST" }).then(data),
  projectionConfirm: (id: string, revision: number, runId: string, generationId: string, key: string) => write<ProjectionReceipt>(`${occurrence(id)}/projection-confirmation`, "POST", key, { run_id: runId, generation_id: generationId, audience: "CLASS", use: "CLASS_PROJECTION" }, { "If-Match": `"${revision}"` }),
  projectionToken: (id: string) => request<ProjectionGrant>(`${occurrence(id)}/projection-playback-token`, { method: "POST" }).then(data),
};
