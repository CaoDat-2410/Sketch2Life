import type {
  ParentActivityListV1,
  ParentActivityRefV1,
  ParentActivitySuggestionSetV1,
  ParentSuggestedActivityV1,
  ParentActivityV1,
  ParentMainActivityV1,
  ParentPlaybackGrantV1,
  ParentPlaybackSourceV1,
  ParentRunAssetAcceptedV1,
  ParentRunIdeaAcceptedV1,
  ParentRunTranscriptV1,
  ParentStoryRewriteAcceptedV1,
  ParentStoryRunV1,
  ParentPostVideoActivityV1,
  ParentVideoCueV1,
  ParentVideoProgressV1,
  ParentTranscriptConfirmedV1,
  ParentVideoGenerationAcceptedV1,
  ParentVideoReasonCodeV1,
  SuggestedActivity,
} from '../domain/types';

/**
 * Goal v3 Phase B Parent logic with no framework, storage or network (SRS l.1664-1676, l.1811):
 * runtime readers for every new answer, state classifiers for the waits, the video panel view
 * model and the playback source builder. Everything here is pure so it is covered by unit tests.
 */

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SHA256_HEX = /^[0-9a-f]{64}$/;
const ASSET_REF = /^upl_[0-9a-f-]{36}$/;

export const CLOSED_RUN_STATES: ReadonlySet<string> = new Set([
  'COMPLETED', 'FAILED', 'ABANDONED', 'DELETE_PENDING', 'DELETED',
]);

/** States where the server (not the adult) is working: the app reads the run again until they change. */
export const BACKGROUND_RUN_STATES: ReadonlySet<string> = new Set([
  'INPUT_PROCESSING', 'STORY_GENERATING', 'SCRIPT_GENERATING',
  'VIDEO_ADMISSION_PENDING', 'VIDEO_QUEUED', 'VIDEO_GENERATING', 'VIDEO_SAFETY_VALIDATING',
]);

export function isClosedRunState(state: unknown): boolean {
  return typeof state === 'string' && CLOSED_RUN_STATES.has(state);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isPositiveInt(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 1;
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function readActivityRef(value: unknown): ParentActivityRefV1 | null {
  if (!isRecord(value) || !isString(value.lesson_id) || !value.lesson_id.trim()
    || !isString(value.version_id) || !value.version_id.trim()
    || !isString(value.content_sha256) || !/^[0-9a-f]{64}$/i.test(value.content_sha256)
    || typeof value.activity_index !== 'number' || !Number.isInteger(value.activity_index)
    || value.activity_index < 0 || value.activity_index > 23) return null;
  return {
    lesson_id: value.lesson_id,
    version_id: value.version_id,
    content_sha256: value.content_sha256,
    activity_index: value.activity_index,
  };
}

function readActivity(value: unknown): ParentActivityV1 | null {
  if (!isRecord(value)) return null;
  const isDraft = value.source === 'AI_DRAFT' || value.source === 'AI_GENERATED_DRAFT';
  const activity_ref = value.activity_ref === null && isDraft
    ? null
    : readActivityRef(value.activity_ref);
  const textFields = ['title', 'objective', 'materials_text', 'preparation_text', 'instructions_text', 'observation_notes', 'safety_notes'] as const;
  if ((isDraft ? value.activity_ref !== null : !activity_ref)
    || textFields.some((field) => !isString(value[field]))
    || (value.lesson_title !== null && !isString(value.lesson_title))
    || (value.lesson_topic !== null && !isString(value.lesson_topic))) return null;
  if (value.activity_kind !== 'outdoor' && value.activity_kind !== 'indoor' && value.activity_kind !== 'mixed') return null;
  if (value.source !== 'PINNED_LESSON' && value.source !== 'PUBLIC' && value.source !== 'SHARED'
    && value.source !== 'PUBLISHED_SHARED_LESSON' && value.source !== 'AI_GENERATED_DRAFT' && value.source !== 'AI_DRAFT') return null;
  return {
    activity_ref,
    title: value.title as string,
    objective: value.objective as string,
    materials_text: value.materials_text as string,
    preparation_text: value.preparation_text as string,
    instructions_text: value.instructions_text as string,
    observation_notes: value.observation_notes as string,
    safety_notes: value.safety_notes as string,
    activity_kind: value.activity_kind,
    source: value.source,
    lesson_title: value.lesson_title as string | null,
    lesson_topic: value.lesson_topic as string | null,
  };
}

/** Reads the selected activity projection, including a draft that has no catalog reference. */
export function readMainActivityV1(value: unknown): ParentMainActivityV1 | null {
  if (!isRecord(value) || (value.state !== 'NOT_SELECTED' && value.state !== 'SELECTED')
    || (value.selected_at !== null && !isString(value.selected_at))) return null;
  const selected = value.selected === null ? null : readActivity(value.selected);
  if ((value.state === 'SELECTED' && !selected) || (value.state === 'NOT_SELECTED' && selected !== null)) return null;
  return {
    state: value.state,
    selected,
    selected_at: value.selected_at,
  };
}

function readSuggestedActivity(value: unknown): SuggestedActivity | null {
  if (!isRecord(value)) return null;
  const textFields = [
    'title', 'objective', 'materials_text', 'preparation_text', 'instructions_text', 'observation_notes', 'safety_notes',
  ] as const;
  if (textFields.some((field) => !isString(value[field]))) return null;
  if (value.activity_kind !== 'outdoor' && value.activity_kind !== 'indoor' && value.activity_kind !== 'mixed') return null;
  if (value.source !== 'PINNED_LESSON' && value.source !== 'PUBLISHED_SHARED_LESSON' && value.source !== 'AI_GENERATED_DRAFT') return null;
  const nullableTextFields = [
    'source_lesson_id', 'source_lesson_title', 'source_lesson_version_id', 'source_content_sha256', 'match_reason',
  ] as const;
  if (nullableTextFields.some((field) => value[field] !== null && !isString(value[field]))) return null;
  const sourceActivityIndex = value.source_activity_index;
  if (sourceActivityIndex !== null && (typeof sourceActivityIndex !== 'number'
    || !Number.isInteger(sourceActivityIndex) || sourceActivityIndex < 0 || sourceActivityIndex > 23)) return null;
  const sourceContentSha256 = value.source_content_sha256;
  if (sourceContentSha256 !== null && !/^[0-9a-f]{64}$/i.test(sourceContentSha256 as string)) return null;
  if (value.source === 'AI_GENERATED_DRAFT') {
    if (value.source_lesson_id !== null || value.source_lesson_title !== null
      || value.source_lesson_version_id !== null || value.source_content_sha256 !== null || sourceActivityIndex !== null) return null;
  } else if (!isString(value.source_lesson_id) || !isString(value.source_lesson_title)
    || !isString(value.source_lesson_version_id) || !isString(sourceContentSha256)
    || typeof sourceActivityIndex !== 'number') return null;
  return {
    title: value.title as string,
    objective: value.objective as string,
    materials_text: value.materials_text as string,
    preparation_text: value.preparation_text as string,
    instructions_text: value.instructions_text as string,
    observation_notes: value.observation_notes as string,
    safety_notes: value.safety_notes as string,
    activity_kind: value.activity_kind,
    source: value.source,
    source_lesson_id: value.source_lesson_id as string | null,
    source_lesson_title: value.source_lesson_title as string | null,
    source_lesson_version_id: value.source_lesson_version_id as string | null,
    source_content_sha256: value.source_content_sha256 as string | null,
    source_activity_index: sourceActivityIndex as number | null,
    match_reason: value.match_reason as string | null,
  };
}

/** Reads the versioned Parent suggestions before they reach the activity selection screen. */
export function readActivitySuggestionSetV1(value: unknown): ParentActivitySuggestionSetV1 | null {
  if (!isRecord(value) || value.contract !== 'ParentActivitySuggestionSetV1'
    || !isString(value.request_id) || !isString(value.story_run_id) || !isString(value.suggestion_set_id)
    || !isPositiveInt(value.set_revision) || !isPositiveInt(value.understanding_revision)
    || (value.selection_mode !== 'CATALOG_SELECTION' && value.selection_mode !== 'AI_GENERATED_FALLBACK')
    || typeof value.catalog_candidate_count !== 'number' || !Number.isInteger(value.catalog_candidate_count)
    || value.catalog_candidate_count < 0 || value.catalog_candidate_count > 500
    || !isString(value.activities_snapshot_sha256) || !/^[0-9a-f]{64}$/.test(value.activities_snapshot_sha256)
    || value.review_required !== true || (value.modal_call_id !== null && !isString(value.modal_call_id))
    || !Array.isArray(value.activities) || value.activities.length < 1 || value.activities.length > 24) return null;
  const activities = value.activities.map(readSuggestedActivity);
  if (activities.some((activity) => activity === null)) return null;
  return {
    contract: 'ParentActivitySuggestionSetV1',
    request_id: value.request_id,
    story_run_id: value.story_run_id,
    suggestion_set_id: value.suggestion_set_id,
    set_revision: value.set_revision,
    understanding_revision: value.understanding_revision,
    selection_mode: value.selection_mode,
    catalog_candidate_count: value.catalog_candidate_count,
    activities_snapshot_sha256: value.activities_snapshot_sha256,
    review_required: true,
    modal_call_id: value.modal_call_id,
    activities: activities as SuggestedActivity[],
  };
}

/** Reads the bounded Parent catalog response without trusting arbitrary JSON from the server. */
export function readActivityListV1(value: unknown): ParentActivityListV1 | null {
  if (!isRecord(value) || !isString(value.request_id) || !Array.isArray(value.items)
    || value.items.length > 12 || !isRecord(value.basis)) return null;
  const age_band = value.basis.age_band;
  if (age_band !== '36-71' && age_band !== '72-107' && age_band !== '108-120') return null;
  if (typeof value.basis.pinned_lesson !== 'boolean' || typeof value.basis.no_candidate !== 'boolean') return null;
  const items = value.items.map((item) => {
    const activity = readActivity(item);
    return activity && activity.source !== 'AI_DRAFT' && activity.activity_ref !== null ? activity : null;
  });
  if (items.some((item) => item === null) || (items.length === 0) !== value.basis.no_candidate) return null;
  return {
    request_id: value.request_id,
    items: items as ParentActivityV1[],
    basis: { age_band, pinned_lesson: value.basis.pinned_lesson, no_candidate: value.basis.no_candidate },
  };
}

/** Reads the persisted catalog-first/AI-fallback set before it reaches the selection screen. */
export function readParentActivitySuggestionSetV1(
  value: unknown,
  expected: { runId: string; understandingRevision: number },
): ParentActivitySuggestionSetV1 | null {
  if (!isRecord(value)
    || value.contract !== 'ParentActivitySuggestionSetV1'
    || !isString(value.request_id) || !UUID.test(value.request_id)
    || value.story_run_id !== expected.runId
    || !isString(value.suggestion_set_id) || !UUID.test(value.suggestion_set_id)
    || !isPositiveInt(value.set_revision)
    || value.understanding_revision !== expected.understandingRevision
    || (value.selection_mode !== 'CATALOG_SELECTION' && value.selection_mode !== 'AI_GENERATED_FALLBACK')
    || !isNonNegativeInt(value.catalog_candidate_count)
    || !isString(value.activities_snapshot_sha256) || !SHA256_HEX.test(value.activities_snapshot_sha256)
    || value.review_required !== true
    || !(value.modal_call_id === null || isString(value.modal_call_id))
    || !Array.isArray(value.activities) || value.activities.length < 1 || value.activities.length > 24) return null;

  const activities = value.activities.map(readParentSuggestedActivity);
  if (activities.some((activity) => activity === null)) return null;
  const typed = activities as ParentSuggestedActivityV1[];
  if (value.selection_mode === 'AI_GENERATED_FALLBACK'
    && (typed.length !== 3 || typed.some((item) => item.source !== 'AI_GENERATED_DRAFT'))) return null;
  if (value.selection_mode === 'CATALOG_SELECTION'
    && typed.some((item) => item.source === 'AI_GENERATED_DRAFT')) return null;

  return {
    contract: 'ParentActivitySuggestionSetV1',
    request_id: value.request_id,
    story_run_id: value.story_run_id,
    suggestion_set_id: value.suggestion_set_id,
    set_revision: value.set_revision,
    understanding_revision: value.understanding_revision,
    selection_mode: value.selection_mode,
    catalog_candidate_count: value.catalog_candidate_count,
    activities_snapshot_sha256: value.activities_snapshot_sha256,
    review_required: true,
    modal_call_id: value.modal_call_id,
    activities: typed,
  };
}

function readParentSuggestedActivity(value: unknown): ParentSuggestedActivityV1 | null {
  if (!isRecord(value)) return null;
  const textFields = [
    'title', 'objective', 'materials_text', 'preparation_text',
    'instructions_text', 'observation_notes', 'safety_notes',
  ] as const;
  if (textFields.some((field) => !isString(value[field]))
    || (value.activity_kind !== 'outdoor' && value.activity_kind !== 'indoor' && value.activity_kind !== 'mixed')
    || (value.source !== 'PINNED_LESSON' && value.source !== 'PUBLISHED_SHARED_LESSON' && value.source !== 'AI_GENERATED_DRAFT')) return null;
  const nullableTextFields = [
    'source_lesson_id', 'source_lesson_title', 'source_lesson_version_id', 'source_content_sha256', 'match_reason',
  ] as const;
  if (nullableTextFields.some((field) => value[field] !== null && !isString(value[field]))) return null;
  const activityIndex = value.source_activity_index;
  if (!(activityIndex === null || (typeof activityIndex === 'number' && Number.isInteger(activityIndex) && activityIndex >= 0 && activityIndex <= 23))) return null;
  if (value.source === 'AI_GENERATED_DRAFT') {
    if (value.source_lesson_id !== null || value.source_lesson_version_id !== null
      || value.source_content_sha256 !== null || activityIndex !== null) return null;
  } else if (!isString(value.source_lesson_id) || !value.source_lesson_id
    || !isString(value.source_lesson_version_id) || !value.source_lesson_version_id
    || !isString(value.source_content_sha256) || !SHA256_HEX.test(value.source_content_sha256)
    || activityIndex === null) return null;

  return {
    title: value.title as string,
    objective: value.objective as string,
    materials_text: value.materials_text as string,
    preparation_text: value.preparation_text as string,
    instructions_text: value.instructions_text as string,
    observation_notes: value.observation_notes as string,
    safety_notes: value.safety_notes as string,
    activity_kind: value.activity_kind,
    source: value.source,
    source_lesson_id: value.source_lesson_id as string | null,
    source_lesson_title: value.source_lesson_title as string | null,
    source_lesson_version_id: value.source_lesson_version_id as string | null,
    source_content_sha256: value.source_content_sha256 as string | null,
    source_activity_index: activityIndex as number | null,
    match_reason: value.match_reason as string | null,
  };
}

function isNonNegativeInt(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}

/** `null` is a normal post-video answer when the pinned lesson is no longer accessible. */
export function readPostVideoActivities(value: unknown): ParentPostVideoActivityV1[] | null {
  if (value === null || value === undefined) return null;
  if (!Array.isArray(value) || value.length > 24) return null;
  const parsed = value.map((item) => {
    if (!isRecord(item) || typeof item.is_main !== 'boolean') return null;
    const activity = readActivity(item);
    return activity ? { ...activity, is_main: item.is_main } : null;
  });
  if (parsed.some((item) => item === null)) return null;
  return parsed as ParentPostVideoActivityV1[];
}

// --------------------------------------------------------------------------- answer readers

/** The 202 of `/assets` must name this run and this handle; anything else is not trusted (T-2b). */
export function readRunAssetAccepted(
  value: unknown,
  expected: { runId: string; assetRef: string },
): ParentRunAssetAcceptedV1 | null {
  if (!isRecord(value)) return null;
  if (value.story_run_id !== expected.runId || value.asset_ref !== expected.assetRef) return null;
  if (value.asset_kind !== 'DRAWING' || value.asset_state !== 'READY') return null;
  if (!isPositiveInt(value.input_revision) || !isPositiveInt(value.run_revision)) return null;
  if (typeof value.run_state !== 'string') return null;
  const analysis = value.analysis_state;
  if (analysis !== 'QUEUED' && analysis !== 'RUNNING' && analysis !== 'SUCCEEDED'
    && analysis !== 'FAILED' && analysis !== 'AWAITING_RECONCILIATION') return null;
  return value as unknown as ParentRunAssetAcceptedV1;
}

export function isAssetRef(value: unknown): value is string {
  return typeof value === 'string' && ASSET_REF.test(value);
}

export function readIdeaAccepted(value: unknown, expectedRunId: string): ParentRunIdeaAcceptedV1 | null {
  if (!isRecord(value) || value.story_run_id !== expectedRunId) return null;
  if (!isPositiveInt(value.input_revision) || !isPositiveInt(value.run_revision) || typeof value.run_state !== 'string') return null;
  const source = value.idea_source;
  if (source !== null && source !== 'TEXT' && source !== 'VOICE' && source !== 'TEXT_AND_VOICE') return null;
  const transcript = value.transcript;
  if (transcript !== null && (!isRecord(transcript) || !isPositiveInt(transcript.transcript_revision)
    || !isTranscriptState(transcript.state))) return null;
  return value as unknown as ParentRunIdeaAcceptedV1;
}

function isTranscriptState(value: unknown): boolean {
  return value === 'NONE' || value === 'PENDING' || value === 'NEEDS_CONFIRMATION'
    || value === 'CONFIRMED' || value === 'FAILED';
}

export function readTranscript(value: unknown, expectedRunId: string): ParentRunTranscriptV1 | null {
  if (!isRecord(value) || value.story_run_id !== expectedRunId || !isTranscriptState(value.state)) return null;
  if (!isPositiveInt(value.run_revision)) return null;
  const revision = value.transcript_revision;
  if (revision !== null && !isPositiveInt(revision)) return null;
  if (value.text !== null && typeof value.text !== 'string') return null;
  if (value.transcript_sha256 !== null && !(typeof value.transcript_sha256 === 'string' && SHA256_HEX.test(value.transcript_sha256))) return null;
  return value as unknown as ParentRunTranscriptV1;
}

export type TranscriptProgress =
  | { kind: 'none' }
  | { kind: 'waiting' }
  | { kind: 'review'; revision: number; sha256: string; text: string; runRevision: number }
  | { kind: 'confirmed' }
  | { kind: 'failed'; revision: number | null; runRevision: number };

/** What the transcript step shows. A review needs the exact revision, hash and non-empty text (TD-04). */
export function classifyTranscript(transcript: ParentRunTranscriptV1): TranscriptProgress {
  switch (transcript.state) {
    case 'NONE': return { kind: 'none' };
    case 'PENDING': return { kind: 'waiting' };
    case 'CONFIRMED': return { kind: 'confirmed' };
    case 'FAILED': return { kind: 'failed', revision: transcript.transcript_revision, runRevision: transcript.run_revision };
    default: {
      const text = transcript.text?.trim() ?? '';
      if (transcript.transcript_revision === null || !transcript.transcript_sha256 || !text) {
        return { kind: 'failed', revision: transcript.transcript_revision, runRevision: transcript.run_revision };
      }
      return {
        kind: 'review',
        revision: transcript.transcript_revision,
        sha256: transcript.transcript_sha256,
        text: transcript.text ?? '',
        runRevision: transcript.run_revision,
      };
    }
  }
}

export function readTranscriptConfirmed(
  value: unknown,
  expected: { runId: string; revision: number },
): ParentTranscriptConfirmedV1 | null {
  if (!isRecord(value) || value.story_run_id !== expected.runId) return null;
  if (value.state !== 'CONFIRMED' || value.transcript_revision !== expected.revision) return null;
  if (!isPositiveInt(value.run_revision) || typeof value.run_state !== 'string') return null;
  return value as unknown as ParentTranscriptConfirmedV1;
}

export function readRewriteAccepted(
  value: unknown,
  expected: { runId: string; fromRevisionNo: number },
): ParentStoryRewriteAcceptedV1 | null {
  if (!isRecord(value) || value.story_run_id !== expected.runId) return null;
  if (value.run_state !== 'SCRIPT_GENERATING' || !isPositiveInt(value.run_revision)) return null;
  const revisionNo = value.story_revision_no;
  // A rewrite creates the next revision; a replay of an older key may return the same one.
  if (!isPositiveInt(revisionNo) || revisionNo < expected.fromRevisionNo || revisionNo > expected.fromRevisionNo + 1) return null;
  return value as unknown as ParentStoryRewriteAcceptedV1;
}

const VIDEO_GENERATION_STATES: ReadonlySet<string> = new Set([
  'ADMISSION_PENDING', 'ADMISSION_REJECTED', 'ACCEPTED', 'QUEUED', 'GENERATING', 'TECHNICAL_VALIDATING',
  'SAFETY_VALIDATING', 'READY', 'SAFETY_BLOCKED', 'FAILED', 'REJECTED_BY_ADULT', 'SUPERSEDED',
]);

export function readVideoGenerationAccepted(value: unknown, expectedRunId: string): ParentVideoGenerationAcceptedV1 | null {
  if (!isRecord(value) || !isRecord(value.video_generation)) return null;
  const generation = value.video_generation;
  if (typeof generation.generation_id !== 'string' || !UUID.test(generation.generation_id)) return null;
  // A replay answers the generation's current state, so every state of the schema is a valid answer (T-1a).
  if (!VIDEO_GENERATION_STATES.has(String(generation.state))) return null;
  if (typeof generation.run_state !== 'string' || !isPositiveInt(generation.run_revision)) return null;
  void expectedRunId;
  return value as unknown as ParentVideoGenerationAcceptedV1;
}

// --------------------------------------------------------------------------- drawing wait

export type DrawingProgress =
  | { kind: 'processing' }
  /** A new run (or one with only an idea): no analysis job exists, the adult still has to attach a drawing. */
  | { kind: 'awaiting-drawing' }
  | { kind: 'subject-ready' }
  | { kind: 'input-review'; analysisFailed: boolean }
  | { kind: 'beyond-subject' }
  | { kind: 'closed'; state: string }
  | { kind: 'unexpected' };

/**
 * Reads the run after a drawing or voice command (T-2b, T-2c, T-2d). `INPUT_PROCESSING` is the server
 * working; `SUBJECT_REVIEW` with a candidate is the visual answer; `INPUT_REVIEW` waits for the adult
 * (a transcript to confirm, or a recoverable analysis failure with `job_state FAILED`).
 */
export function classifyDrawingProgress(run: unknown): DrawingProgress {
  if (!isRecord(run) || typeof run.run_state !== 'string') return { kind: 'unexpected' };
  const state = run.run_state;
  if (isClosedRunState(state)) return { kind: 'closed', state };
  switch (state) {
    case 'DRAFT':
      return { kind: 'awaiting-drawing' };
    case 'INPUT_PROCESSING':
      return run.job_state === 'QUEUED' || run.job_state === 'RUNNING' || run.job_state === 'AWAITING_RECONCILIATION'
        ? { kind: 'processing' }
        : run.understanding_revision !== null && run.understanding_revision !== undefined
          ? { kind: 'processing' }
          : { kind: 'awaiting-drawing' };
    case 'INPUT_REVIEW':
      return { kind: 'input-review', analysisFailed: run.job_state === 'FAILED' };
    case 'SUBJECT_REVIEW':
      return isRecord(run.candidate) ? { kind: 'subject-ready' } : { kind: 'unexpected' };
    case 'PREPARATION_REVIEW':
    case 'STORY_GENERATING':
    case 'SCRIPT_GENERATING':
    case 'SCRIPT_GENERATION_UNKNOWN':
    case 'SCRIPT_REVIEW':
      return { kind: 'beyond-subject' };
    default:
      return { kind: 'unexpected' };
  }
}

// --------------------------------------------------------------------------- rewrite wait

export type RewriteProgress =
  | { kind: 'generating' }
  | { kind: 'ready'; revisionNo: number }
  | { kind: 'failed'; retryable: boolean; code: string | null }
  | { kind: 'unknown-outcome' }
  | { kind: 'closed'; state: string }
  | { kind: 'unexpected' };

/**
 * Reads the run after `story-rewrites` (T-2d, T-2d-fix): `SCRIPT_GENERATING` while the worker runs;
 * `SCRIPT_REVIEW` with a new `DRAFT` revision when it worked; `SCRIPT_REVIEW` at the old revision with
 * `job_state FAILED` when it failed (the previous story is intact, `retryable` says if another try is
 * allowed). `SCRIPT_GENERATION_UNKNOWN` waits for the server to reconcile; nothing is sent again.
 */
export function classifyRewriteProgress(
  run: unknown,
  expected: { fromRevisionNo: number; toRevisionNo: number },
): RewriteProgress {
  if (!isRecord(run) || typeof run.run_state !== 'string') return { kind: 'unexpected' };
  const state = run.run_state;
  if (isClosedRunState(state)) return { kind: 'closed', state };
  if (state === 'SCRIPT_GENERATING' || state === 'STORY_GENERATING') return { kind: 'generating' };
  if (state === 'SCRIPT_GENERATION_UNKNOWN') return { kind: 'unknown-outcome' };
  if (state !== 'SCRIPT_REVIEW') return { kind: 'unexpected' };
  const revisionNo = run.story_revision_no;
  if (typeof revisionNo === 'number' && revisionNo >= expected.toRevisionNo && run.story_status === 'DRAFT') {
    return { kind: 'ready', revisionNo };
  }
  if (revisionNo === expected.fromRevisionNo && run.job_state === 'FAILED') {
    return {
      kind: 'failed',
      retryable: run.retryable === true,
      code: typeof run.error_code === 'string' ? run.error_code : null,
    };
  }
  return { kind: 'unexpected' };
}

/**
 * The range to follow for a story the server is already generating (resume). While the new revision is
 * generated, the run reads the `GENERATING` row as its latest revision, so the old revision is one lower.
 */
export function rewriteRangeForRun(run: { story_revision_no?: number | null; story_status?: string | null }): { fromRevisionNo: number; toRevisionNo: number } {
  const latest = typeof run.story_revision_no === 'number' && run.story_revision_no >= 1 ? run.story_revision_no : 1;
  return run.story_status === 'GENERATING'
    ? { fromRevisionNo: latest - 1, toRevisionNo: latest }
    : { fromRevisionNo: latest, toRevisionNo: latest + 1 };
}

/** FR-P-07: the first story plus three rewrites, so revision 4 is the last one (l.378, l.1413). */
export const STORY_REWRITE_REVISION_LIMIT = 4;

export function rewritesLeft(storyRevisionNo: number | null | undefined): number {
  if (typeof storyRevisionNo !== 'number' || !Number.isInteger(storyRevisionNo) || storyRevisionNo < 1) return 0;
  return Math.max(0, STORY_REWRITE_REVISION_LIMIT - storyRevisionNo);
}

// --------------------------------------------------------------------------- video panel

export const VIDEO_REASON_LABELS: Record<ParentVideoReasonCodeV1, string> = {
  QUALITY_LOW: 'Hình hoặc tiếng chưa rõ',
  NOT_MATCHING_STORY: 'Chưa đúng với câu chuyện',
  CONTENT_CONCERN: 'Nội dung chưa phù hợp với bé',
  OTHER: 'Lý do khác',
};

export const VIDEO_REASON_CODES: readonly ParentVideoReasonCodeV1[] = [
  'QUALITY_LOW', 'NOT_MATCHING_STORY', 'CONTENT_CONCERN', 'OTHER',
];

export type VideoPanel = {
  /** One calm line for the adult. */
  headline: string;
  detail: string | null;
  tone: 'info' | 'success' | 'warning' | 'error';
  /** The server is working: keep reading the run. */
  inFlight: boolean;
  canRequest: boolean;
  /** A new request after an accepted one must carry a reason (T-1a). */
  requiresReason: boolean;
  /** The confirmed script is spent or not confirmed: the way forward is the script review. */
  needsScriptReview: boolean;
  canPlay: boolean;
  canMarkUnsuitable: boolean;
  canComplete: boolean;
  closed: boolean;
  requestsRemaining: number | null;
  scenes: Array<{ index: number; label: string }>;
  postVideoActivities: ParentPostVideoActivityV1[] | null;
  storyConfirmationRequired: boolean;
  onlyCancel: boolean;
  /** FEAT-093: the real stage of the video worker while it runs (server data, never invented here). */
  progress: ParentVideoProgressV1 | null;
  captions: ParentVideoCueV1[] | null;
};

const SCENE_LABELS = { QUEUED: 'Đang chờ', GENERATING: 'Đang tạo', READY: 'Đã xong', FAILED: 'Chưa tạo được' } as const;

const closedPanel = (headline: string, detail: string | null, tone: VideoPanel['tone']): VideoPanel => ({
  headline, detail, tone, inFlight: false, canRequest: false, requiresReason: false, needsScriptReview: false,
  canPlay: false, canMarkUnsuitable: false, canComplete: false, closed: true, requestsRemaining: null, scenes: [],
  postVideoActivities: null, storyConfirmationRequired: false, onlyCancel: false, progress: null, captions: null,
});

/**
 * The video step of one run (SRS l.395, l.1670-1676, l.383). `spentRevisionNo` is the story revision the
 * app already asked a video for (or marked unsuitable) in this session: the server refuses a second
 * request on the same confirmed script, so the panel sends the adult to the script review instead.
 * Without that local knowledge the server decides and its 409 gets the same advice.
 */
export type ScriptSpent = 'known' | 'likely' | 'no';

/**
 * Whether the confirmed script already carries a video request that cannot be repeated (T-1a: one request per
 * confirmed review). `known`: this session asked or marked it. `likely`: the last generation failed, was blocked
 * or was rejected and this session did not confirm a newer script (also after an app restart). The server decides.
 */
export function scriptSpentByVideo(
  run: ParentStoryRunV1,
  session: { spentRevisionNo?: number | null; confirmedRevisionNo?: number | null } = {},
): ScriptSpent {
  if (run.story_status !== 'CONFIRMED') return 'no';
  if (run.video?.state === 'ADMISSION_REJECTED') return 'no';
  if (session.spentRevisionNo !== null && session.spentRevisionNo !== undefined && session.spentRevisionNo === run.story_revision_no) return 'known';
  if (session.confirmedRevisionNo !== null && session.confirmedRevisionNo !== undefined && session.confirmedRevisionNo === run.story_revision_no) return 'no';
  const last = run.video?.state;
  return last === 'FAILED' || last === 'REJECTED_BY_ADULT' || last === 'SAFETY_BLOCKED' ? 'likely' : 'no';
}

export function readVideoPanel(
  run: ParentStoryRunV1 | null,
  options: { spentRevisionNo?: number | null; confirmedRevisionNo?: number | null } = {},
): VideoPanel {
  if (!run) return closedPanel('Chưa có buổi học để tạo video.', null, 'warning');
  const state = run.run_state;
  const video = run.video ?? null;
  const used = video?.video_requests_used ?? 0;
  const remaining = video ? video.video_requests_remaining : 3;
  const base: VideoPanel = {
    headline: '', detail: null, tone: 'info', inFlight: false, canRequest: false,
    requiresReason: used > 0, needsScriptReview: false, canPlay: false, canMarkUnsuitable: false,
    canComplete: false, closed: false, requestsRemaining: remaining,
    scenes: (video?.scenes ?? []).map((scene) => ({ index: scene.scene_index, label: SCENE_LABELS[scene.state] ?? 'Đang chờ' })),
    postVideoActivities: readPostVideoActivities(run.post_video_activities),
    storyConfirmationRequired: run.story_confirmation_required === true,
    onlyCancel: false,
    progress: video?.progress ?? null,
    captions: video?.captions ?? null,
  };

  switch (state) {
    case 'COMPLETED':
      return {
        ...base,
        headline: 'Buổi học đã hoàn tất.',
        detail: video?.state === 'READY' && video.playback.state === 'AVAILABLE'
          ? 'Bạn có thể xem lại video trong lịch sử buổi học.'
          : 'Video hiện chưa thể phát. Nội dung được giữ cho đến khi bạn xóa buổi học.',
        tone: 'success',
        canPlay: video?.state === 'READY' && video.playback.state === 'AVAILABLE',
        closed: true,
      };
    case 'ABANDONED':
      return closedPanel('Buổi học đã tự đóng.', 'Buổi học không có thao tác trong 7 ngày nên được đóng lại. Nội dung được giữ cho đến khi bạn xóa buổi học.', 'info');
    case 'FAILED':
      return closedPanel('Buổi học đã dừng.', failedRunDetail(run.error_code), 'error');
    case 'DELETE_PENDING':
      return closedPanel('Buổi học đang được xóa.', 'Yêu cầu xóa đang chờ máy chủ xác nhận.', 'info');
    case 'DELETED':
      return closedPanel('Buổi học đã được xóa.', null, 'info');
    case 'SAFETY_BLOCKED':
      return {
        ...base,
        headline: 'Video chưa qua kiểm tra an toàn.',
        detail: run.story_confirmation_required === true
          ? 'Bạn có thể xác nhận lại cùng kịch bản hoặc viết lại câu chuyện.'
          : 'Đã hết lượt tạo video. Bạn có thể dừng buổi học trong lịch sử.',
        tone: 'warning',
        needsScriptReview: run.story_confirmation_required === true,
        storyConfirmationRequired: run.story_confirmation_required === true,
        onlyCancel: run.story_confirmation_required === false,
        closed: run.story_confirmation_required === false,
      };
    case 'VIDEO_ADMISSION_PENDING':
      return { ...base, headline: 'Đang xác nhận yêu cầu tạo video…', detail: 'Chưa gửi lại yêu cầu. Máy chủ đang kiểm tra lượt tạo video.', inFlight: true };
    case 'VIDEO_QUEUED':
      return { ...base, headline: 'Video đang chờ tới lượt xử lý.', detail: 'Bạn có thể rời màn hình này; tiến độ vẫn được máy chủ giữ.', inFlight: true };
    case 'VIDEO_GENERATING': {
      const total = base.scenes.length;
      const done = video?.scenes.filter((scene) => scene.state === 'READY').length ?? 0;
      return {
        ...base,
        headline: 'Đang tạo video cho bé…',
        detail: total > 0 ? `Đã xong ${done} / ${total} cảnh.` : 'Việc này có thể mất vài phút.',
        inFlight: true,
      };
    }
    case 'VIDEO_SAFETY_VALIDATING':
      return { ...base, headline: 'Đang kiểm tra video trước khi phát…', detail: 'Chỉ video qua kiểm tra mới được phát.', inFlight: true };
    case 'VIDEO_READY': {
      const playable = video?.state === 'READY' && video.playback.state === 'AVAILABLE';
      return {
        ...base,
        headline: playable ? 'Video đã sẵn sàng.' : 'Video đã tạo xong nhưng chưa thể phát.',
        detail: playable ? 'Xem video, rồi hoàn tất buổi học hoặc đánh dấu video chưa phù hợp.' : 'Hãy tải lại sau ít phút.',
        tone: playable ? 'success' : 'warning',
        canPlay: playable,
        canMarkUnsuitable: playable && remaining > 0,
        canComplete: true,
      };
    }
    case 'SCRIPT_REVIEW':
      return scriptReviewPanel(run, base, scriptSpentByVideo(run, options));
    default:
      return {
        ...base,
        headline: 'Hãy hoàn tất các bước trước khi tạo video.',
        detail: 'Cần xác nhận chủ thể, ngữ cảnh và kịch bản của buổi học.',
        tone: 'warning',
        needsScriptReview: true,
      };
  }
}

function scriptReviewPanel(run: ParentStoryRunV1, base: VideoPanel, spentState: ScriptSpent): VideoPanel {
  const video = run.video ?? null;
  const confirmed = run.story_status === 'CONFIRMED' && typeof run.story_sha256 === 'string' && SHA256_HEX.test(run.story_sha256);
  const remaining = base.requestsRemaining ?? 3;
  const confirmationRequired = typeof run.story_confirmation_required === 'boolean'
    ? run.story_confirmation_required
    : !confirmed || spentState !== 'no';
  const atVideoCap = remaining <= 0 || (video?.video_requests_used ?? 0) >= 3;
  if (atVideoCap) {
    return {
      ...base,
      headline: 'Đã dùng hết lượt tạo video của buổi học này.',
      detail: 'Bạn có thể dừng buổi học trong lịch sử.',
      tone: 'warning',
      requiresReason: false,
      storyConfirmationRequired: false,
      onlyCancel: true,
      closed: true,
    };
  }
  if (!confirmed) {
    return { ...base, headline: 'Hãy xác nhận kịch bản trước khi tạo video.', detail: 'Video chỉ được tạo từ kịch bản người lớn đã xác nhận.', tone: 'warning', needsScriptReview: true, storyConfirmationRequired: confirmationRequired };
  }
  const last = video?.state ?? null;
  const advice = adviceAfter(last, video?.job?.error_code ?? run.error_code);
  const noRewritesLeft = rewritesLeft(run.story_revision_no) === 0;
  if (confirmationRequired) {
    const detail = noRewritesLeft
      ? 'Đã hết lượt viết lại kịch bản. Bạn có thể dừng buổi học trong lịch sử.'
      : advice.detail;
    return { ...base, headline: advice.headline, detail, tone: 'warning', needsScriptReview: true, storyConfirmationRequired: true };
  }
  if (last === 'ADMISSION_REJECTED') {
    return { ...base, headline: 'Chưa nhận được yêu cầu tạo video.', detail: 'Lượt này không bị tính. Bạn có thể thử lại sau ít phút.', tone: 'warning', canRequest: true };
  }
  return {
    ...base,
    headline: video ? advice.headline : 'Kịch bản đã xác nhận. Sẵn sàng tạo video.',
    detail: video ? advice.detail : `Còn ${remaining} lượt tạo video cho buổi học này.`,
    tone: video ? 'warning' : 'info',
    canRequest: true,
  };
}

function adviceAfter(last: string | null, code: string | null | undefined): { headline: string; detail: string } {
  if (last === 'SAFETY_BLOCKED' || code === 'VIDEO_SAFETY_BLOCKED') {
    return {
      headline: 'Video chưa qua kiểm tra an toàn.',
      detail: 'Bạn có thể xác nhận lại cùng kịch bản hoặc viết lại câu chuyện.',
    };
  }
  if (last === 'REJECTED_BY_ADULT') {
    return {
      headline: 'Bạn đã đánh dấu video chưa phù hợp.',
      detail: 'Hãy viết lại kịch bản, xác nhận lại rồi tạo video mới.',
    };
  }
  if (last === 'FAILED' && code === 'VIDEO_DEADLINE_EXCEEDED') {
    return {
      headline: 'Video chưa tạo xong trong thời gian cho phép.',
      detail: 'Lượt này vẫn được tính. Hãy viết lại kịch bản, xác nhận lại rồi tạo video mới.',
    };
  }
  if (last === 'FAILED' || last === 'SAFETY_BLOCKED') {
    return {
      headline: 'Video lần trước chưa tạo được.',
      detail: 'Lượt này vẫn được tính. Hãy viết lại kịch bản, xác nhận lại rồi tạo video mới.',
    };
  }
  return { headline: 'Kịch bản đã xác nhận. Sẵn sàng tạo video.', detail: 'Hãy viết lại và xác nhận kịch bản nếu muốn tạo lại.' };
}

function failedRunDetail(code: string | null): string {
  if (code === 'VIDEO_DEADLINE_EXCEEDED') return 'Video không tạo xong trong thời gian cho phép nên buổi học đã dừng.';
  if (code === 'VIDEO_TECHNICAL_FAILURE') return 'Video gặp lỗi kỹ thuật nên buổi học đã dừng.';
  if (code === 'VIDEO_SAFETY_BLOCKED') return 'Video chưa qua kiểm tra an toàn.';
  if (code === 'PROVIDER_TIMEOUT') return 'Dịch vụ tạo nội dung không phản hồi kịp. Bạn có thể bắt đầu buổi học mới.';
  return 'Bạn có thể xem lịch sử buổi học hoặc bắt đầu buổi học mới.';
}

/** Run-level state labels for the new states (history and home). */
export function phaseBRunStateLabel(state: string): string | null {
  const labels: Record<string, string> = {
    INPUT_REVIEW: 'Chờ xem lại ảnh và ý tưởng',
    STORY_GENERATING: 'Đang tạo câu chuyện',
    SCRIPT_GENERATING: 'Đang tạo câu chuyện',
    SCRIPT_REVIEW: 'Chờ xác nhận kịch bản',
    VIDEO_ADMISSION_PENDING: 'Đang xác nhận yêu cầu tạo video',
    VIDEO_QUEUED: 'Video đang chờ xử lý',
    VIDEO_GENERATING: 'Đang tạo video',
    VIDEO_SAFETY_VALIDATING: 'Đang kiểm tra video',
    VIDEO_READY: 'Video đã sẵn sàng',
    SAFETY_BLOCKED: 'Video chưa qua kiểm tra',
    COMPLETED: 'Đã hoàn tất',
    ABANDONED: 'Đã tự đóng',
  };
  return labels[state] ?? null;
}

// --------------------------------------------------------------------------- playback

const PRIVATE_DEV_HOST = /^http:\/\/(localhost|127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|[a-z0-9-]+\.(local|test|localhost))(:\d+)?(\/|$)/i;
const PLAYBACK_TOKEN = /^[\x21-\x7E]{16,4096}$/;

/** The grant must be well formed and name exactly this run's stream route (T-1c, SRS l.1692). */
export function isPlaybackGrantForRun(value: unknown, runId: string): value is ParentPlaybackGrantV1 {
  if (!isRecord(value)) return false;
  return typeof value.token === 'string' && PLAYBACK_TOKEN.test(value.token)
    && value.stream_path === `/v1/story-runs/${encodeURIComponent(runId)}/playback`
    && value.media_type === 'video/mp4'
    && typeof value.asset_ref === 'string'
    && typeof value.expires_at === 'string' && Number.isFinite(Date.parse(value.expires_at));
}

/**
 * Builds the player source. The address is the configured base URL plus the run's own stream path;
 * the grant travels in `X-Playback-Token` beside the Firebase bearer, never in the URL (SRS l.1693).
 * Returns `null` for an expired grant or a base URL that cannot carry the bearer safely.
 */
export function buildPlaybackSource(input: {
  baseUrl: string;
  runId: string;
  grant: ParentPlaybackGrantV1;
  bearer: string;
  nowMs: number;
}): ParentPlaybackSourceV1 | null {
  const base = input.baseUrl.replace(/\/+$/, '');
  if (!/^https?:\/\/[^\s?#]+$/i.test(base) || !input.bearer.trim()) return null;
  // The bearer and the grant never travel in cleartext, except to a local or private development host.
  if (/^http:\/\//i.test(base) && !PRIVATE_DEV_HOST.test(base)) return null;
  const expiresAtMs = Date.parse(input.grant.expires_at);
  if (!Number.isFinite(expiresAtMs) || expiresAtMs <= input.nowMs) return null;
  return {
    uri: `${base}${input.grant.stream_path}`,
    headers: {
      Authorization: `Bearer ${input.bearer}`,
      'X-Playback-Token': input.grant.token,
      Accept: 'video/mp4',
    },
    expiresAtMs,
  };
}

/** True when the grant stops working within `marginMs` (the screen asks for a new one first). */
export function playbackNeedsRefresh(source: Pick<ParentPlaybackSourceV1, 'expiresAtMs'>, nowMs: number, marginMs = 15_000): boolean {
  return source.expiresAtMs - nowMs <= marginMs;
}
