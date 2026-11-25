import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({ parentConfig: { apiBaseUrl: 'https://api.example.test' } }));

import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';
import { ParentLearningUseCases } from '../src/parent/application/use-cases/ParentLearningUseCases';
import type { ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import type { ParentStoryRunV1 } from '../src/parent/domain/types';
import {
  buildPlaybackSource,
  classifyDrawingProgress,
  classifyRewriteProgress,
  classifyTranscript,
  isPlaybackGrantForRun,
  playbackNeedsRefresh,
  readIdeaAccepted,
  readActivityListV1,
  readPostVideoActivities,
  readRewriteAccepted,
  readRunAssetAccepted,
  readTranscript,
  readTranscriptConfirmed,
  readVideoGenerationAccepted,
  readVideoPanel,
  rewriteRangeForRun,
  rewritesLeft,
  scriptSpentByVideo,
} from '../src/parent/application/parentPhaseB';
import {
  RUN_UPLOAD_LIMITS,
  base64ToBytes,
  uploadRunMedia,
  type BinaryDigestPort,
  type UploadSessionView,
  type UploadSessionsPort,
} from '../src/parent/application/parentRunUploads';
import { RunWaitCancelled, waitForRun } from '../src/parent/application/parentRunWait';
import { readRunUnderstanding } from '../src/parent/presentation/navigation/parentFlowV1';

const RUN = '11111111-1111-4111-8111-111111111111';
const ASSET = 'upl_22222222-2222-4222-8222-222222222222';
const GENERATION = '33333333-3333-4333-8333-333333333333';
const SHA = 'a'.repeat(64);
const TOKEN = 'ptk1.' + 'x'.repeat(40);

type Call = { url: string; init: RequestInit };

function reply(status: number, body: unknown = {}, headers: Record<string, string> = {}): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(headers),
    json: async () => body,
    body: { cancel: async () => undefined },
  } as unknown as Response;
}

function apiWith(replies: Response[]) {
  const calls: Call[] = [];
  const queue = [...replies];
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return queue.shift() ?? reply(200);
  }) as unknown as typeof fetch;
  const auth = { getIdToken: vi.fn(async () => 'firebase-id-token') };
  return { api: new ParentApi(auth, fetcher, 'https://api.example.test'), calls, auth };
}

const headerOf = (call: Call, name: string) => (call.init.headers as Record<string, string>)[name];

function runOf(overrides: Partial<ParentStoryRunV1> = {}): ParentStoryRunV1 {
  return {
    run_id: RUN, run_revision: 7, run_state: 'SCRIPT_REVIEW', parent_profile_id: 'p', profile_revision_ref: 'r',
    context_revision: 1, context_confirmed: true,
    context_snapshot: { schema_version: 'sketch2life.parent-context.v1', profile_revision_ref: 'r', topic: 't', adult_confirmed_idea: 'i', age_months: 72, interests_summary: '' },
    context_snapshot_sha256: SHA, lesson_pin_snapshot: null, current_input_revision: 2, understanding_revision: 1,
    subject_label: 'bướm', candidate: null, story_revision_id: GENERATION, story_revision_no: 2, story_status: 'CONFIRMED',
    story_sha256: SHA, story: null, job_state: 'SUCCEEDED', retryable: false, error_code: null,
    created_at: '2026-11-21T00:00:00Z', updated_at: '2026-11-21T00:00:00Z',
    ...overrides,
  } as ParentStoryRunV1;
}

const videoOf = (overrides: Record<string, unknown> = {}) => ({
  current_generation_id: GENERATION, generation_no: 1, kind: 'INITIAL', state: 'READY', job: null,
  scenes: [], playback: { state: 'AVAILABLE', asset_ref: 'vid_x', token_route: `/v1/story-runs/${RUN}/playback-token` },
  video_requests_used: 1, video_requests_remaining: 2, admission_pending: false, history: [],
  ...overrides,
}) as ParentStoryRunV1['video'];

describe('Phase B API commands (SRS l.1664-1676)', () => {
  it('ignores future run fields and treats unknown states safely', () => {
    // A run with a real candidate, so the readers return a value that an unknown field could change.
    const withCandidate = runOf({
      understanding_revision: 2,
      candidate: { candidate_subject: 'bướm', visible_features: ['cánh'], confidence: 0.9, adult_confirmation_required: true, decision: 'REVIEW_REQUIRED' },
    });
    const future = { ...withCandidate, occurrence_ref: 'ignored', owner_kind: 'ignored' };
    expect(readRunUnderstanding(withCandidate)).not.toBeNull();
    expect(readRunUnderstanding(future)).toEqual(readRunUnderstanding(withCandidate));
    expect(readVideoPanel(future)).toEqual(readVideoPanel(withCandidate));
    expect(classifyDrawingProgress(future)).toEqual(classifyDrawingProgress(withCandidate));
    const unknown = { ...future, run_state: 'FUTURE_STATE' } as unknown as ParentStoryRunV1;
    expect(classifyDrawingProgress(unknown)).toEqual({ kind: 'unexpected' });
    expect(readVideoPanel(unknown)).toMatchObject({ canPlay: false, canRequest: false, tone: 'warning' });
  });
  it('attaches a drawing with a key, the opaque handle and the optional run revision', async () => {
    const { api, calls } = apiWith([reply(202, { story_run_id: RUN })]);
    await api.attachRunAssetV1(RUN, ASSET, 7, 'key-1');
    expect(calls[0].url).toBe(`https://api.example.test/v1/story-runs/${RUN}/assets`);
    expect(calls[0].init.method).toBe('POST');
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ asset_ref: ASSET, expected_run_revision: 7 });
    expect(headerOf(calls[0], 'Idempotency-Key')).toBe('key-1');
    const second = apiWith([reply(202, {})]);
    await second.api.attachRunAssetV1(RUN, ASSET, null, 'key-2');
    expect(JSON.parse(String(second.calls[0].init.body))).toEqual({ asset_ref: ASSET });
  });

  it('sends the three idea shapes and reads the transcript and its confirmation', async () => {
    const { api, calls } = apiWith([reply(202, {}), reply(202, {}), reply(202, {}), reply(200, {}), reply(200, {})]);
    await api.addRunIdeaV1(RUN, { expected_run_revision: 3, text: 'một chú thỏ' }, 'k1');
    await api.addRunIdeaV1(RUN, { expected_run_revision: 3, audio_ref: ASSET }, 'k2');
    await api.addRunIdeaV1(RUN, { expected_run_revision: 3, transcript_correction: { base_revision: 2, text: 'đã sửa' } }, 'k3');
    await api.getRunTranscriptV1(RUN);
    await api.confirmRunTranscriptV1(RUN, 2, SHA, 'k4');
    expect(calls.map((call) => `${call.init.method} ${new URL(call.url).pathname.replace(RUN, '{run}')}`)).toEqual([
      'POST /v1/story-runs/{run}/idea', 'POST /v1/story-runs/{run}/idea', 'POST /v1/story-runs/{run}/idea',
      'GET /v1/story-runs/{run}/transcript', 'POST /v1/story-runs/{run}/transcript-confirmation',
    ]);
    expect(JSON.parse(String(calls[2].init.body))).toEqual({ expected_run_revision: 3, transcript_correction: { base_revision: 2, text: 'đã sửa' } });
    expect(JSON.parse(String(calls[4].init.body))).toEqual({ expected_transcript_revision: 2, transcript_sha256: SHA, confirmed: true });
    expect(headerOf(calls[3], 'Idempotency-Key')).toBeUndefined();
  });

  it('sends rewrite, video request, unsuitable mark and completion with their exact bodies', async () => {
    const { api, calls } = apiWith([reply(202, {}), reply(202, {}), reply(200, {}), reply(200, {})]);
    await api.createStoryRewriteV1(RUN, { expected_story_revision: 2, expected_story_sha256: SHA, hint: 'thêm bạn mới' }, 'k1');
    await api.requestVideoGenerationV1(RUN, { expected_revision: 7, story_sha256: SHA, quality_reason_code: 'QUALITY_LOW' }, 'k2');
    await api.markVideoUnsuitableV1(RUN, { expected_revision: 8, generation_id: GENERATION, reason_code: 'OTHER' }, 'k3');
    await api.completeRunV1(RUN, 9, 'k4');
    expect(calls.map((call) => new URL(call.url).pathname.replace(RUN, '{run}'))).toEqual([
      '/v1/story-runs/{run}/story-rewrites', '/v1/story-runs/{run}/video-generations',
      '/v1/story-runs/{run}/video-unsuitable', '/v1/story-runs/{run}/complete',
    ]);
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ expected_story_revision: 2, expected_story_sha256: SHA, hint: 'thêm bạn mới' });
    expect(JSON.parse(String(calls[3].init.body))).toEqual({ expected_revision: 9 });
  });

  it('refuses a key outside 1 to 128 visible ASCII before any request, on every Phase B command', async () => {
    const { api, calls } = apiWith([]);
    const runs: Array<(key: string) => unknown> = [
      (key) => api.attachRunAssetV1(RUN, ASSET, 1, key),
      (key) => api.addRunIdeaV1(RUN, { expected_run_revision: 1, text: 'x' }, key),
      (key) => api.confirmRunTranscriptV1(RUN, 1, SHA, key),
      (key) => api.createStoryRewriteV1(RUN, { expected_story_revision: 1 }, key),
      (key) => api.requestVideoGenerationV1(RUN, { expected_revision: 1, story_sha256: SHA }, key),
      (key) => api.markVideoUnsuitableV1(RUN, { expected_revision: 1, generation_id: GENERATION, reason_code: 'OTHER' }, key),
      (key) => api.completeRunV1(RUN, 1, key),
      (key) => api.createStoryRunV1({ parent_profile_id: 'p', topic: 't', adult_confirmed_idea: 'i' }, key),
      (key) => api.confirmStoryRunContextV1(RUN, { expected_context_revision: 1, context_snapshot_sha256: SHA, confirmed: true }, key),
      (key) => api.confirmStoryRunScriptV1(RUN, 1, SHA, key),
    ];
    for (const run of runs) {
      for (const bad of ['', 'k'.repeat(129), 'has space', 'khoá-é']) {
        expect(() => run(bad)).toThrow(ParentApiError);
      }
    }
    expect(calls).toHaveLength(0);
  });

  it('answers a purged run as a lifecycle error instead of a result the screen could show', async () => {
    const { api } = apiWith([reply(202, { request_id: 'r', lifecycle: { run_state: 'DELETE_PENDING' } })]);
    await expect(api.attachRunAssetV1(RUN, ASSET, 1, 'k')).rejects.toMatchObject({ code: 'DELETE_PENDING' });
  });

  it('keeps the story-run error envelope for 404 wrong role, 409 caps and 503 holds', async () => {
    for (const [status, code] of [[404, 'RESOURCE_NOT_FOUND'], [409, 'STORY_REWRITE_LIMIT_REACHED'], [409, 'VIDEO_QUOTA_EXCEEDED'], [503, 'AI_COST_LIMIT_REACHED']] as const) {
      const { api } = apiWith([reply(status, { detail: { code } })]);
      await expect(api.createStoryRewriteV1(RUN, { expected_story_revision: 1 }, 'k')).rejects.toMatchObject({ code, status });
    }
  });
});

describe('Playback grant (T-1c, SRS l.1676, l.1691-1693)', () => {
  const grant = (overrides: Record<string, unknown> = {}) => ({
    request_id: 'r',
    playback: {
      token: TOKEN, expires_at: new Date(Date.now() + 120_000).toISOString(),
      stream_path: `/v1/story-runs/${RUN}/playback`, media_type: 'video/mp4', asset_ref: 'vid_x', ...overrides,
    },
  });

  it('issues without a body or key, then probes the stream with the bearer and the grant in headers only', async () => {
    const { api, calls } = apiWith([reply(200, grant()), reply(206)]);
    const source = await api.openPlaybackV1(RUN);
    expect(calls[0].url).toBe(`https://api.example.test/v1/story-runs/${RUN}/playback-token`);
    expect(calls[0].init.method).toBe('POST');
    expect(calls[0].init.body).toBeUndefined();
    expect(headerOf(calls[0], 'Idempotency-Key')).toBeUndefined();
    expect(calls[1].url).toBe(`https://api.example.test/v1/story-runs/${RUN}/playback`);
    expect(calls[1].url).not.toContain(TOKEN);
    expect(calls[1].url).not.toContain('?');
    expect(headerOf(calls[1], 'X-Playback-Token')).toBe(TOKEN);
    expect(headerOf(calls[1], 'Authorization')).toBe('Bearer firebase-id-token');
    expect(headerOf(calls[1], 'Range')).toBe('bytes=0-0');
    expect(source.uri).toBe(`https://api.example.test/v1/story-runs/${RUN}/playback`);
    expect(source.headers['X-Playback-Token']).toBe(TOKEN);
  });

  it('asks for a new grant once after a 401 on the stream, and then reports a calm failure without a status', async () => {
    const expired = reply(401, { detail: { code: 'TOKEN_EXPIRED' } });
    const ok = apiWith([reply(200, grant()), expired, reply(200, grant()), reply(200)]);
    await expect(ok.api.openPlaybackV1(RUN)).resolves.toMatchObject({ uri: expect.stringContaining('/playback') });
    expect(ok.calls.filter((call) => call.url.endsWith('/playback-token'))).toHaveLength(2);

    const bad = apiWith([reply(200, grant()), reply(401, { code: 'TOKEN_EXPIRED' }), reply(200, grant()), reply(401, { code: 'TOKEN_EXPIRED' })]);
    const failure = await bad.api.openPlaybackV1(RUN).catch((cause: unknown) => cause) as ParentApiError;
    expect(failure.code).toBe('PLAYBACK_TOKEN_REJECTED');
    // A playback refusal is not a sign-in problem: no 401 status, so the session-expired path stays closed.
    expect(failure.status).toBeUndefined();
    expect(String(failure.message)).not.toContain(TOKEN);
  });

  it('surfaces a 401 of the token issue itself as the session, not as a playback problem', async () => {
    const { api } = apiWith([reply(401, { code: 'TOKEN_EXPIRED' })]);
    await expect(api.openPlaybackV1(RUN)).rejects.toMatchObject({ status: 401 });
  });

  it('handles an invalid grant and missing or unavailable streams without leaking the response', async () => {
    const invalid = apiWith([reply(200, grant()), reply(401, { code: 'INVALID_TOKEN' }), reply(200, grant()), reply(206)]);
    await expect(invalid.api.openPlaybackV1(RUN)).resolves.toBeDefined();
    expect(invalid.calls).toHaveLength(4);
    for (const status of [404, 416, 503]) {
      const { api, calls } = apiWith([reply(200, grant()), reply(status, { code: 'RESOURCE_NOT_FOUND', message: 'private data' })]);
      const error = await api.openPlaybackV1(RUN).catch((cause: unknown) => cause);
      expect(error).toBeInstanceOf(ParentApiError);
      expect((error as ParentApiError).status).toBe(status);
      expect(String(error)).not.toContain('private data');
      expect(calls).toHaveLength(2);
    }
  });

  it('never sends the bearer to a path or media type the grant names differently', async () => {
    for (const bad of [
      { stream_path: 'https://evil.example/leak' },
      { stream_path: '/v1/story-runs/other-run/playback' },
      { stream_path: `/v1/story-runs/${RUN}/playback?token=${TOKEN}` },
      { media_type: 'text/html' },
      { token: 'short' },
      { expires_at: 'not-a-date' },
    ]) {
      const { api, calls } = apiWith([reply(200, grant(bad))]);
      await expect(api.openPlaybackV1(RUN)).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE' });
      expect(calls).toHaveLength(1);
    }
  });

  it('builds a source only from a live grant and refreshes before expiry', () => {
    const live = grant().playback as never;
    expect(isPlaybackGrantForRun(live, RUN)).toBe(true);
    expect(isPlaybackGrantForRun(live, 'another')).toBe(false);
    const now = Date.now();
    const source = buildPlaybackSource({ baseUrl: 'https://api.example.test/', runId: RUN, grant: live, bearer: 'b', nowMs: now });
    expect(source?.uri).toBe(`https://api.example.test/v1/story-runs/${RUN}/playback`);
    expect(buildPlaybackSource({ baseUrl: 'ftp://x', runId: RUN, grant: live, bearer: 'b', nowMs: now })).toBeNull();
    expect(buildPlaybackSource({ baseUrl: 'https://a.test?x=1', runId: RUN, grant: live, bearer: 'b', nowMs: now })).toBeNull();
    expect(buildPlaybackSource({ baseUrl: 'https://a.test', runId: RUN, grant: live, bearer: ' ', nowMs: now })).toBeNull();
    expect(buildPlaybackSource({ baseUrl: 'https://a.test', runId: RUN, grant: live, bearer: 'b', nowMs: now + 10 * 60_000 })).toBeNull();
    // The bearer and the grant never travel in cleartext, except to a local or private development host.
    expect(buildPlaybackSource({ baseUrl: 'http://api.example.test', runId: RUN, grant: live, bearer: 'b', nowMs: now })).toBeNull();
    for (const dev of ['http://localhost:8000', 'http://10.0.2.2:8000', 'http://192.168.1.20:8000', 'http://127.0.0.1:8000']) {
      expect(buildPlaybackSource({ baseUrl: dev, runId: RUN, grant: live, bearer: 'b', nowMs: now })).not.toBeNull();
    }
    expect(playbackNeedsRefresh({ expiresAtMs: now + 5_000 }, now)).toBe(true);
    expect(playbackNeedsRefresh({ expiresAtMs: now + 60_000 }, now)).toBe(false);
  });
});

describe('Phase B answer readers', () => {
  it('reads the asset, idea, transcript, confirmation, rewrite and video answers only when they name this run', () => {
    const asset = { story_run_id: RUN, asset_ref: ASSET, asset_kind: 'DRAWING', asset_state: 'READY', input_revision: 2, run_revision: 8, run_state: 'INPUT_PROCESSING', analysis_state: 'QUEUED' };
    expect(readRunAssetAccepted(asset, { runId: RUN, assetRef: ASSET })).not.toBeNull();
    expect(readRunAssetAccepted({ ...asset, asset_ref: 'upl_other' }, { runId: RUN, assetRef: ASSET })).toBeNull();
    expect(readRunAssetAccepted({ ...asset, story_run_id: 'x' }, { runId: RUN, assetRef: ASSET })).toBeNull();
    expect(readRunAssetAccepted({ ...asset, analysis_state: 'WEIRD' }, { runId: RUN, assetRef: ASSET })).toBeNull();

    const idea = { story_run_id: RUN, input_revision: 3, run_revision: 9, run_state: 'INPUT_PROCESSING', idea_source: 'VOICE', transcript: { transcript_revision: 1, state: 'PENDING' } };
    expect(readIdeaAccepted(idea, RUN)).not.toBeNull();
    expect(readIdeaAccepted({ ...idea, transcript: null, idea_source: null }, RUN)).not.toBeNull();
    expect(readIdeaAccepted({ ...idea, idea_source: 'MAGIC' }, RUN)).toBeNull();
    expect(readIdeaAccepted(idea, 'x')).toBeNull();

    expect(readTranscriptConfirmed({ story_run_id: RUN, transcript_revision: 2, state: 'CONFIRMED', run_revision: 10, run_state: 'SUBJECT_REVIEW' }, { runId: RUN, revision: 2 })).not.toBeNull();
    expect(readTranscriptConfirmed({ story_run_id: RUN, transcript_revision: 3, state: 'CONFIRMED', run_revision: 10, run_state: 'x' }, { runId: RUN, revision: 2 })).toBeNull();

    const rewrite = { story_run_id: RUN, story_revision_no: 3, run_revision: 11, run_state: 'SCRIPT_GENERATING' };
    expect(readRewriteAccepted(rewrite, { runId: RUN, fromRevisionNo: 2 })).not.toBeNull();
    expect(readRewriteAccepted({ ...rewrite, story_revision_no: 5 }, { runId: RUN, fromRevisionNo: 2 })).toBeNull();
    expect(readRewriteAccepted({ ...rewrite, run_state: 'SCRIPT_REVIEW' }, { runId: RUN, fromRevisionNo: 2 })).toBeNull();

    const video = { request_id: 'r', video_generation: { generation_id: GENERATION, state: 'ADMISSION_PENDING', generation_no: null, kind: 'INITIAL', job_id: null, run_state: 'VIDEO_ADMISSION_PENDING', run_revision: 12 } };
    expect(readVideoGenerationAccepted(video, RUN)).not.toBeNull();
    // A replay answers the generation's current state (T-1a): every state of the schema is valid, an unknown one is not.
    expect(readVideoGenerationAccepted({ ...video, video_generation: { ...video.video_generation, state: 'READY' } }, RUN)).not.toBeNull();
    expect(readVideoGenerationAccepted({ ...video, video_generation: { ...video.video_generation, state: 'MAGIC' } }, RUN)).toBeNull();
  });

  it('classifies a transcript into wait, review (exact revision and hash), confirmed and failed', () => {
    const base = { story_run_id: RUN, transcript_revision: 2, origin: 'ASR', text: 'một chú thỏ', transcript_sha256: SHA, language: 'vi', error_code: null, run_revision: 5 };
    const read = (state: string, extra: Record<string, unknown> = {}) => readTranscript({ ...base, state, ...extra }, RUN)!;
    expect(classifyTranscript(read('PENDING', { text: null, transcript_sha256: null }))).toEqual({ kind: 'waiting' });
    expect(classifyTranscript(read('NEEDS_CONFIRMATION'))).toMatchObject({ kind: 'review', revision: 2, sha256: SHA, runRevision: 5 });
    expect(classifyTranscript(read('CONFIRMED'))).toEqual({ kind: 'confirmed' });
    expect(classifyTranscript(read('FAILED', { text: null, transcript_sha256: null, error_code: 'PROVIDER_TIMEOUT' }))).toMatchObject({ kind: 'failed', revision: 2 });
    expect(classifyTranscript(read('NONE', { transcript_revision: null, text: null, transcript_sha256: null }))).toEqual({ kind: 'none' });
    // A review without text or hash can never be confirmed: it degrades to a failed transcript the adult retypes.
    expect(classifyTranscript(read('NEEDS_CONFIRMATION', { text: '  ' }))).toMatchObject({ kind: 'failed' });
    expect(readTranscript({ ...base, state: 'NEEDS_CONFIRMATION', transcript_sha256: 'zz' }, RUN)).toBeNull();
  });
});

describe('Run waits and states', () => {
  it('reads the drawing stage from the run state and the failed job', () => {
    expect(classifyDrawingProgress(runOf({ run_state: 'INPUT_PROCESSING', job_state: 'QUEUED' }))).toEqual({ kind: 'processing' });
    expect(classifyDrawingProgress(runOf({ run_state: 'INPUT_PROCESSING', job_state: 'RUNNING' }))).toEqual({ kind: 'processing' });
    // A new run is INPUT_PROCESSING with no job: it waits for the adult's drawing, it is not server work (review F2).
    expect(classifyDrawingProgress(runOf({ run_state: 'INPUT_PROCESSING', job_state: null, current_input_revision: 1, understanding_revision: null }))).toEqual({ kind: 'awaiting-drawing' });
    expect(classifyDrawingProgress(runOf({ run_state: 'SUBJECT_REVIEW', candidate: { candidate_subject: 'a' } as never }))).toEqual({ kind: 'subject-ready' });
    expect(classifyDrawingProgress(runOf({ run_state: 'SUBJECT_REVIEW', candidate: null }))).toEqual({ kind: 'unexpected' });
    expect(classifyDrawingProgress(runOf({ run_state: 'INPUT_REVIEW', job_state: 'FAILED' }))).toEqual({ kind: 'input-review', analysisFailed: true });
    expect(classifyDrawingProgress(runOf({ run_state: 'INPUT_REVIEW', job_state: 'SUCCEEDED' }))).toEqual({ kind: 'input-review', analysisFailed: false });
    expect(classifyDrawingProgress(runOf({ run_state: 'ABANDONED' }))).toEqual({ kind: 'closed', state: 'ABANDONED' });
    expect(classifyDrawingProgress(runOf({ run_state: 'NEW_FUTURE_STATE' as never }))).toEqual({ kind: 'unexpected' });
    expect(classifyDrawingProgress(null)).toEqual({ kind: 'unexpected' });
  });

  it('tells a finished rewrite from a failed one and from one still running', () => {
    const range = { fromRevisionNo: 2, toRevisionNo: 3 };
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_GENERATING' }), range)).toEqual({ kind: 'generating' });
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_REVIEW', story_revision_no: 3, story_status: 'DRAFT' }), range)).toEqual({ kind: 'ready', revisionNo: 3 });
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_REVIEW', story_revision_no: 2, story_status: 'DRAFT', job_state: 'FAILED', retryable: true, error_code: 'PROVIDER_TIMEOUT' }), range))
      .toEqual({ kind: 'failed', retryable: true, code: 'PROVIDER_TIMEOUT' });
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_REVIEW', story_revision_no: 2, story_status: 'DRAFT', job_state: 'FAILED', retryable: false }), range))
      .toMatchObject({ kind: 'failed', retryable: false });
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_GENERATION_UNKNOWN' }), range)).toEqual({ kind: 'unknown-outcome' });
    expect(classifyRewriteProgress(runOf({ run_state: 'COMPLETED' }), range)).toEqual({ kind: 'closed', state: 'COMPLETED' });
    // The old story with no failure and no new draft is not a result.
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_REVIEW', story_revision_no: 2, story_status: 'DRAFT', job_state: 'SUCCEEDED' }), range)).toEqual({ kind: 'unexpected' });
    // Resume while the server generates revision 3: the run already reads the GENERATING row as its latest (review F3).
    const generating = runOf({ run_state: 'SCRIPT_GENERATING', story_revision_no: 3, story_status: 'GENERATING' });
    const resumed = rewriteRangeForRun(generating);
    expect(resumed).toEqual({ fromRevisionNo: 2, toRevisionNo: 3 });
    expect(classifyRewriteProgress(generating, resumed)).toEqual({ kind: 'generating' });
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_REVIEW', story_revision_no: 3, story_status: 'DRAFT' }), resumed)).toEqual({ kind: 'ready', revisionNo: 3 });
    expect(classifyRewriteProgress(runOf({ run_state: 'SCRIPT_REVIEW', story_revision_no: 2, story_status: 'DRAFT', job_state: 'FAILED', retryable: true }), resumed)).toMatchObject({ kind: 'failed', retryable: true });
    expect(rewriteRangeForRun(runOf({ story_revision_no: 2, story_status: 'DRAFT' }))).toEqual({ fromRevisionNo: 2, toRevisionNo: 3 });
    expect(rewritesLeft(1)).toBe(3);
    expect(rewritesLeft(2)).toBe(2);
    expect(rewritesLeft(4)).toBe(0);
    expect(rewritesLeft(null)).toBe(0);
  });

  it('shows the video panel for each server state without inventing a way forward', () => {
    const confirmed = runOf({ run_state: 'SCRIPT_REVIEW', video: null });
    const first = readVideoPanel(confirmed);
    expect(first).toMatchObject({ canRequest: true, requiresReason: false, closed: false, needsScriptReview: false });

    const regen = readVideoPanel(runOf({ video: videoOf({ state: 'FAILED', video_requests_used: 1, video_requests_remaining: 2, playback: { state: 'UNAVAILABLE', asset_ref: null, token_route: null } }) }));
    expect(regen).toMatchObject({ canRequest: false, needsScriptReview: true, requiresReason: true, storyConfirmationRequired: true });
    // The script the app already asked a video for (or marked unsuitable) is spent: the way on is the script review.
    expect(readVideoPanel(confirmed, { spentRevisionNo: 2 })).toMatchObject({ canRequest: false, needsScriptReview: true });
    expect(readVideoPanel(confirmed, { spentRevisionNo: 1 }).canRequest).toBe(true);
    // After a restart nothing is known locally: a failed or rejected last video makes the script "likely spent" (review F8).
    const afterFailure = runOf({ video: videoOf({ state: 'FAILED', video_requests_used: 1, video_requests_remaining: 2, playback: { state: 'UNAVAILABLE', asset_ref: null, token_route: null } }) });
    expect(scriptSpentByVideo(afterFailure)).toBe('likely');
    expect(readVideoPanel(afterFailure)).toMatchObject({ needsScriptReview: true, canRequest: false, requiresReason: true, storyConfirmationRequired: true });
    expect(scriptSpentByVideo(afterFailure, { spentRevisionNo: 2 })).toBe('known');
    expect(scriptSpentByVideo(afterFailure, { confirmedRevisionNo: 2 })).toBe('no');
    expect(scriptSpentByVideo(runOf({ video: null }))).toBe('no');
    expect(scriptSpentByVideo(runOf({ story_status: 'DRAFT', video: videoOf({ state: 'FAILED' }) }))).toBe('no');
    // A spent confirmed story must be re-confirmed before another video request.
    expect(readVideoPanel(runOf({ story_revision_no: 4, video: videoOf({ state: 'FAILED', video_requests_used: 1 }) })))
      .toMatchObject({ canRequest: false, needsScriptReview: true, storyConfirmationRequired: true });
    // A refused admission keeps the script reusable, even if this session believed it spent.
    expect(scriptSpentByVideo(runOf({ video: videoOf({ state: 'ADMISSION_REJECTED' }) }), { spentRevisionNo: 2 })).toBe('no');
    // An understood drawing with only the voice transcript pending is server work, not "waiting for a drawing".
    expect(classifyDrawingProgress(runOf({ run_state: 'INPUT_PROCESSING', job_state: 'SUCCEEDED', understanding_revision: 1 }))).toEqual({ kind: 'processing' });
    // At revision 4 no rewrite is left: the advice is to stop, and a second request is not offered once the session knows it is spent.
    expect(readVideoPanel(runOf({ story_revision_no: 4, video: videoOf({ state: 'REJECTED_BY_ADULT', video_requests_used: 1 }) }), { spentRevisionNo: 4 }))
      .toMatchObject({ canRequest: false, needsScriptReview: true, detail: expect.stringContaining('dừng buổi học') });
    expect(readVideoPanel(runOf({ story_status: 'DRAFT' }))).toMatchObject({ canRequest: false, needsScriptReview: true });
    expect(readVideoPanel(runOf({ video: videoOf({ state: 'REJECTED_BY_ADULT', video_requests_used: 1 }) }), { spentRevisionNo: 2 }).detail).toContain('viết lại kịch bản');
    expect(readVideoPanel(runOf({ video: videoOf({ state: 'FAILED', job: { job_id: 'j', state: 'failed_exhausted', stage: null, retryable: false, error_code: 'VIDEO_DEADLINE_EXCEEDED' } }) }), { spentRevisionNo: 2 }).headline).toContain('thời gian cho phép');
    expect(readVideoPanel(runOf({ video: videoOf({ state: 'ADMISSION_REJECTED', video_requests_used: 0, video_requests_remaining: 3 }) }))).toMatchObject({ canRequest: true, requiresReason: false });
    expect(readVideoPanel(runOf({ video: videoOf({ video_requests_used: 3, video_requests_remaining: 0, state: 'FAILED' }) }))).toMatchObject({ canRequest: false, requiresReason: false });

    for (const state of ['VIDEO_ADMISSION_PENDING', 'VIDEO_QUEUED', 'VIDEO_GENERATING', 'VIDEO_SAFETY_VALIDATING'] as const) {
      expect(readVideoPanel(runOf({ run_state: state, video: videoOf({ state: 'GENERATING', scenes: [{ scene_index: 1, state: 'READY' }, { scene_index: 2, state: 'GENERATING' }] }) }))).toMatchObject({ inFlight: true, canRequest: false, canComplete: false });
    }
    expect(readVideoPanel(runOf({ run_state: 'VIDEO_GENERATING', video: videoOf({ state: 'GENERATING', scenes: [{ scene_index: 1, state: 'READY' }, { scene_index: 2, state: 'GENERATING' }] }) })).detail).toBe('Đã xong 1 / 2 cảnh.');

    const ready = readVideoPanel(runOf({ run_state: 'VIDEO_READY', video: videoOf() }));
    expect(ready).toMatchObject({ canPlay: true, canComplete: true, canMarkUnsuitable: true, tone: 'success' });
    expect(readVideoPanel(runOf({ run_state: 'VIDEO_READY', video: videoOf({ video_requests_remaining: 0 }) })).canMarkUnsuitable).toBe(false);
    expect(readVideoPanel(runOf({ run_state: 'VIDEO_READY', video: videoOf({ playback: { state: 'HIDDEN', asset_ref: null, token_route: null } }) }))).toMatchObject({ canPlay: false, canComplete: true });

    for (const state of ['ABANDONED', 'FAILED', 'DELETE_PENDING', 'DELETED'] as const) {
      const panel = readVideoPanel(runOf({ run_state: state }));
      expect(panel).toMatchObject({ closed: true, canRequest: false, canPlay: false, canComplete: false });
    }
    expect(readVideoPanel(runOf({ run_state: 'COMPLETED', video: videoOf() })).detail).toContain('xem lại video');
    expect(readVideoPanel(runOf({ run_state: 'COMPLETED', video: videoOf() })).canPlay).toBe(true);
    expect(readVideoPanel(runOf({ run_state: 'COMPLETED', video: videoOf({ playback: { state: 'HIDDEN', asset_ref: null, token_route: null } }) })).canPlay).toBe(false);
    expect(readVideoPanel(runOf({ run_state: 'SAFETY_BLOCKED', story_confirmation_required: true })))
      .toMatchObject({ closed: false, needsScriptReview: true, storyConfirmationRequired: true, onlyCancel: false });
    expect(readVideoPanel(runOf({ run_state: 'FAILED', error_code: 'VIDEO_DEADLINE_EXCEEDED' })).detail).toContain('thời gian cho phép');
    expect(readVideoPanel(null).closed).toBe(true);
  });

  it('uses the public story confirmation flag and treats missing post-video activities as normal', () => {
    const blocked = readVideoPanel(runOf({
      run_state: 'SCRIPT_REVIEW', story_confirmation_required: true,
      video: videoOf({ state: 'SAFETY_BLOCKED', job: { job_id: 'j', state: 'blocked_unsafe', stage: null, retryable: false, error_code: 'VIDEO_SAFETY_BLOCKED' } }),
    }));
    expect(blocked).toMatchObject({ headline: 'Video chưa qua kiểm tra an toàn.', storyConfirmationRequired: true, needsScriptReview: true, canRequest: false, onlyCancel: false });
    const capped = readVideoPanel(runOf({
      run_state: 'SCRIPT_REVIEW', story_confirmation_required: false,
      video: videoOf({ video_requests_used: 3, video_requests_remaining: 0, state: 'SAFETY_BLOCKED' }),
    }));
    expect(capped).toMatchObject({ onlyCancel: true, closed: true, storyConfirmationRequired: false, canRequest: false });
    expect(readPostVideoActivities(null)).toBeNull();
    expect(readPostVideoActivities(undefined)).toBeNull();
    expect(readActivityListV1({ request_id: 'r', items: [], basis: { age_band: '72-107', pinned_lesson: false, no_candidate: true } })).toMatchObject({ items: [], basis: { no_candidate: true } });
    expect(readActivityListV1({ request_id: 'r', items: [], basis: { age_band: '72-107', pinned_lesson: false, no_candidate: false } })).toBeNull();
  });
});

describe('Upload sessions for a run (T-2a, SRS l.1654-1658)', () => {
  const digest: BinaryDigestPort = {
    sha256Hex: vi.fn(async (bytes: Uint8Array) => `h${bytes.byteLength}-${bytes[0] ?? 0}`.padEnd(64, '0')),
  };
  const session = (overrides: Partial<UploadSessionView> = {}): UploadSessionView => ({
    upload_id: 'upl-1', state: 'OPEN', part_size_bytes: 4, expected_parts: 3, accepted_parts: [], revision: 1,
    asset_ref: null, asset_state: null, error_code: null, ...overrides,
  });
  const bytes = Uint8Array.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  const keys = { create: 'k-create', complete: 'k-complete' };

  function sessions(first: UploadSessionView, done: UploadSessionView) {
    const parts: Array<{ no: number; length: number }> = [];
    const port: UploadSessionsPort = {
      create: vi.fn(async () => first),
      putPart: vi.fn(async (_id: string, no: number, part: Uint8Array) => { parts.push({ no, length: part.byteLength }); return {}; }),
      complete: vi.fn(async () => done),
    };
    return { port, parts };
  }

  it('creates the session for the run, sends the parts in order with their hashes and returns the asset handle', async () => {
    const { port, parts } = sessions(session(), session({ state: 'COMPLETED', asset_ref: ASSET, asset_state: 'READY' }));
    const result = await uploadRunMedia({ uploads: port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/jpeg', bytes, keys });
    expect(result.assetRef).toBe(ASSET);
    expect(parts).toEqual([{ no: 1, length: 4 }, { no: 2, length: 4 }, { no: 3, length: 2 }]);
    const [createInput, createKey] = (port.create as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(createInput).toMatchObject({ purpose: 'RUN_ARTWORK', target_ref: RUN, media_type: 'image/jpeg', expected_size_bytes: 10 });
    expect(createKey).toBe('k-create');
    expect((port.complete as ReturnType<typeof vi.fn>).mock.calls[0][2]).toBe('k-complete');
  });

  it('does not send a part the server already holds with the same hash, and resends one with another hash', async () => {
    const heldHash = await digest.sha256Hex(bytes.subarray(0, 4));
    const { port, parts } = sessions(
      session({ accepted_parts: [{ part_no: 1, byte_length: 4, sha256: heldHash }, { part_no: 2, byte_length: 4, sha256: 'f'.repeat(64) }] }),
      session({ state: 'COMPLETED', asset_ref: ASSET, asset_state: 'READY' }),
    );
    await uploadRunMedia({ uploads: port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/png', bytes, keys });
    expect(parts.map((part) => part.no)).toEqual([2, 3]);
  });

  it('returns a session that is already completed without sending anything again', async () => {
    const { port, parts } = sessions(session({ state: 'COMPLETED', asset_ref: ASSET, asset_state: 'READY' }), session());
    const result = await uploadRunMedia({ uploads: port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/png', bytes, keys });
    expect(result.assetRef).toBe(ASSET);
    expect(parts).toHaveLength(0);
    expect(port.complete).not.toHaveBeenCalled();
  });

  it('refuses a type or size outside the purpose, a session that cannot take parts and an unconfirmed completion', async () => {
    const { port } = sessions(session(), session({ state: 'COMPLETED', asset_ref: ASSET, asset_state: 'READY' }));
    const run = (extra: Partial<Parameters<typeof uploadRunMedia>[0]>) => uploadRunMedia({ uploads: port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/jpeg', bytes, keys, ...extra });
    await expect(run({ mediaType: 'video/mp4' })).rejects.toMatchObject({ code: 'UNSUPPORTED_MEDIA_TYPE' });
    await expect(run({ bytes: new Uint8Array(0) })).rejects.toMatchObject({ code: 'MEDIA_TOO_LARGE' });
    await expect(uploadRunMedia({ uploads: port, digest, purpose: 'RUN_AUDIO', runId: RUN, mediaType: 'audio/webm', bytes, keys })).rejects.toMatchObject({ code: 'UNSUPPORTED_MEDIA_TYPE' });
    expect(RUN_UPLOAD_LIMITS.RUN_AUDIO.maxBytes).toBe(20_000_000);
    expect(RUN_UPLOAD_LIMITS.RUN_ARTWORK.maxBytes).toBe(20 * 1024 * 1024);

    const aborted = sessions(session({ state: 'ABORTED', error_code: 'RUN_DELETED' }), session());
    await expect(uploadRunMedia({ uploads: aborted.port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/jpeg', bytes, keys })).rejects.toMatchObject({ code: 'RUN_DELETED' });
    const mismatched = sessions(session({ expected_parts: 9 }), session());
    await expect(uploadRunMedia({ uploads: mismatched.port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/jpeg', bytes, keys })).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE' });
    const notDone = sessions(session(), session({ state: 'FAILED', error_code: 'MALWARE_DETECTED' }));
    await expect(uploadRunMedia({ uploads: notDone.port, digest, purpose: 'RUN_ARTWORK', runId: RUN, mediaType: 'image/jpeg', bytes, keys })).rejects.toMatchObject({ code: 'MALWARE_DETECTED' });
  });

  it('decodes base64 without atob and refuses malformed input', () => {
    expect(Array.from(base64ToBytes('AQIDBAU='))).toEqual([1, 2, 3, 4, 5]);
    expect(Array.from(base64ToBytes('AQID\nBAU'))).toEqual([1, 2, 3, 4, 5]);
    expect(() => base64ToBytes('A')).toThrow(ParentApplicationError);
    expect(() => base64ToBytes('AB$D')).toThrow(ParentApplicationError);
  });
});

describe('Run wait loop', () => {
  const noSleep = async () => undefined;

  it('reads until the value is settled and reports every value it saw', async () => {
    const values = ['a', 'b', 'done'];
    const seen: string[] = [];
    const result = await waitForRun<string>({ read: async () => values.shift() as string, isSettled: (value) => value === 'done', sleep: noSleep, onValue: (value) => seen.push(value) });
    expect(result).toEqual({ value: 'done', timedOut: false });
    expect(seen).toEqual(['a', 'b', 'done']);
  });

  it('stops at the budget with the last value, using the doubled 2 s to 10 s backoff', async () => {
    let clock = 0;
    const waits: number[] = [];
    const result = await waitForRun<number>({
      read: async () => 1, isSettled: () => false, now: () => clock, budgetMs: 20_000,
      sleep: async (ms) => { waits.push(ms); clock += ms; },
    });
    expect(result).toEqual({ value: 1, timedOut: true });
    expect(waits[0]).toBe(2_000);
    expect(Math.max(...waits)).toBeLessThanOrEqual(10_000);
    expect(waits.every((ms, index) => index === 0 || ms >= waits[index - 1])).toBe(true);
  });

  it('retries a transient read failure a few times, then gives up on the same kind of failure and on any other', async () => {
    let calls = 0;
    const flaky = await waitForRun<string>({
      read: async () => { calls += 1; if (calls < 3) throw new Error('net'); return 'ok'; },
      isSettled: () => true, sleep: noSleep, isTransient: () => true,
    });
    expect(flaky).toEqual({ value: 'ok', timedOut: false });
    await expect(waitForRun<string>({ read: async () => { throw new Error('net'); }, isSettled: () => true, sleep: noSleep, isTransient: () => true })).rejects.toThrow('net');
    await expect(waitForRun<string>({ read: async () => { throw new Error('fatal'); }, isSettled: () => true, sleep: noSleep })).rejects.toThrow('fatal');
  });

  it('stops when the caller aborts, before or during the wait', async () => {
    const controller = new AbortController();
    controller.abort();
    await expect(waitForRun<string>({ read: async () => 'x', isSettled: () => false, sleep: noSleep, signal: controller.signal })).rejects.toBeInstanceOf(RunWaitCancelled);

    const later = new AbortController();
    await expect(waitForRun<string>({
      read: async () => { later.abort(); return 'x'; }, isSettled: () => false,
      sleep: async (_ms, signal) => { if (signal.aborted) throw new RunWaitCancelled(); },
      signal: later.signal,
    })).rejects.toBeInstanceOf(RunWaitCancelled);
  });

  it('writes nothing when the caller aborts while a read is in flight (review F7a)', async () => {
    const controller = new AbortController();
    const onValue = vi.fn();
    const pending = waitForRun<string>({
      read: async () => { controller.abort(); return 'done'; },
      isSettled: () => true, sleep: noSleep, signal: controller.signal, onValue,
    });
    await expect(pending).rejects.toBeInstanceOf(RunWaitCancelled);
    expect(onValue).not.toHaveBeenCalled();
  });

  it('pauses only while the app is in the background, not on inactive or unknown', async () => {
    const read = vi.fn(async () => 'done');
    const appState = { currentState: 'inactive' as string | null, addEventListener: () => ({ remove: () => undefined }) };
    await expect(waitForRun<string>({ read, isSettled: () => true, sleep: noSleep, appState })).resolves.toEqual({ value: 'done', timedOut: false });
    expect(read).toHaveBeenCalledTimes(1);
  });

  it('does not read while the app is in the background and resumes when it returns', async () => {
    let listener: ((state: string) => void) | undefined;
    const appState = {
      currentState: 'background' as string | null,
      addEventListener: (_event: 'change', next: (state: string) => void) => { listener = next; return { remove: () => undefined }; },
    };
    const read = vi.fn(async () => 'done');
    const pending = waitForRun<string>({ read, isSettled: () => true, sleep: noSleep, appState });
    await new Promise((resolve) => setTimeout(resolve, 5));
    expect(read).not.toHaveBeenCalled();
    listener?.('active');
    await expect(pending).resolves.toEqual({ value: 'done', timedOut: false });
    expect(read).toHaveBeenCalledTimes(1);
  });
});

describe('Learning use cases for Phase B', () => {
  function fakeApi(overrides: Record<string, unknown> = {}) {
    const calls: Array<{ method: string; args: unknown[] }> = [];
    const record = (method: string, answer: unknown) => vi.fn(async (...args: unknown[]) => { calls.push({ method, args }); return answer; });
    const api = {
      attachRunAssetV1: record('attach', { story_run_id: RUN, asset_ref: ASSET, asset_kind: 'DRAWING', asset_state: 'READY', input_revision: 2, run_revision: 8, run_state: 'INPUT_PROCESSING', analysis_state: 'QUEUED' }),
      addRunIdeaV1: record('idea', { story_run_id: RUN, input_revision: 3, run_revision: 9, run_state: 'INPUT_PROCESSING', idea_source: 'VOICE', transcript: { transcript_revision: 1, state: 'PENDING' } }),
      createStoryRewriteV1: record('rewrite', { story_run_id: RUN, story_revision_no: 3, run_revision: 10, run_state: 'SCRIPT_GENERATING' }),
      requestVideoGenerationV1: record('video', { request_id: 'r', video_generation: { generation_id: GENERATION, state: 'ADMISSION_PENDING', generation_no: null, kind: 'INITIAL', job_id: null, run_state: 'VIDEO_ADMISSION_PENDING', run_revision: 11 } }),
      markVideoUnsuitableV1: record('unsuitable', { request_id: 'r', story_run: runOf() }),
      completeRunV1: record('complete', { request_id: 'r', story_run: runOf({ run_state: 'COMPLETED' }) }),
      confirmStoryRunContextV1: record('context-confirmation', { request_id: 'r', story_run: runOf({ context_confirmed: true }) }),
      ...overrides,
    } as unknown as ParentApiPort;
    return { api, calls };
  }
  const uploadPort = () => {
    const sessions: UploadSessionsPort = {
      create: vi.fn(async () => ({ upload_id: 'upl-1', state: 'OPEN', part_size_bytes: 4_194_304, expected_parts: 1, accepted_parts: [], revision: 1, asset_ref: null, asset_state: null, error_code: null })),
      putPart: vi.fn(async () => ({})),
      complete: vi.fn(async () => ({ upload_id: 'upl-1', state: 'COMPLETED', part_size_bytes: 4_194_304, expected_parts: 1, accepted_parts: [], revision: 2, asset_ref: ASSET, asset_state: 'READY' as const, error_code: null })),
    };
    return { sessions, digest: { sha256Hex: async () => SHA }, readFileBytes: vi.fn(async () => Uint8Array.from([1, 2, 3])) };
  };

  it('keeps an omitted context selection distinct from explicit empty and selected IDs', async () => {
    const { api, calls } = fakeApi();
    const cases = new ParentLearningUseCases(api, uploadPort());
    const run = runOf({ context_confirmed: false });

    await cases.confirmRunContextV1(run, 'context-action-v1');
    await cases.confirmRunContextV1(run, 'context-action-empty', []);
    await cases.confirmRunContextV1(run, 'context-action-selected', ['00000000-0000-4000-8000-000000000001']);

    expect(calls.map((call) => call.method)).toEqual([
      'context-confirmation', 'context-confirmation', 'context-confirmation',
    ]);
    expect(calls[0].args[1]).toEqual({
      expected_context_revision: 1, context_snapshot_sha256: SHA, confirmed: true,
    });
    expect(calls[1].args[1]).toEqual({
      expected_context_revision: 1, context_snapshot_sha256: SHA, confirmed: true, selected_context_entry_ids: [],
    });
    expect(calls[2].args[1]).toEqual({
      expected_context_revision: 1, context_snapshot_sha256: SHA, confirmed: true,
      selected_context_entry_ids: ['00000000-0000-4000-8000-000000000001'],
    });
  });

  it('uploads the drawing first and attaches the returned handle to the run at its current revision', async () => {
    const { api, calls } = fakeApi();
    const uploads = uploadPort();
    const cases = new ParentLearningUseCases(api, uploads);
    const accepted = await cases.attachDrawingV1({ runId: RUN, runRevision: 7, photo: { base64: 'AQID', mediaType: 'image/jpeg' }, keys: { create: 'a', complete: 'b', attach: 'c' } });
    expect(accepted.analysis_state).toBe('QUEUED');
    expect(uploads.sessions.create).toHaveBeenCalledTimes(1);
    expect(calls[0]).toMatchObject({ method: 'attach', args: [RUN, ASSET, 7, 'c'] });
  });

  it('stops before any request without a drawing, and when the server answers another run', async () => {
    const { api } = fakeApi({ attachRunAssetV1: vi.fn(async () => ({ story_run_id: 'other', asset_ref: ASSET })) });
    const cases = new ParentLearningUseCases(api, uploadPort());
    await expect(cases.attachDrawingV1({ runId: RUN, runRevision: 1, photo: { base64: ' ', mediaType: 'image/png' }, keys: { create: 'a', complete: 'b', attach: 'c' } })).rejects.toMatchObject({ code: 'PARENT_DRAWING_REQUIRED' });
    await expect(cases.attachDrawingV1({ runId: RUN, runRevision: 1, photo: { base64: 'AQID', mediaType: 'image/png' }, keys: { create: 'a', complete: 'b', attach: 'c' } })).rejects.toMatchObject({ code: 'PARENT_DRAWING_RESULT_INVALID' });
    await expect(new ParentLearningUseCases(api, null).attachDrawingV1({ runId: RUN, runRevision: 1, photo: { base64: 'AQID', mediaType: 'image/png' }, keys: { create: 'a', complete: 'b', attach: 'c' } })).rejects.toMatchObject({ code: 'CAPABILITY_UNAVAILABLE' });
  });

  it('sends a voice idea as an uploaded audio handle with the revision read just before the command', async () => {
    const { api, calls } = fakeApi();
    const uploads = uploadPort();
    const revisions = [8, 9];
    const currentRunRevision = vi.fn(async () => revisions.shift() as number);
    const accepted = await new ParentLearningUseCases(api, uploads).submitVoiceIdeaV1({
      runId: RUN, currentRunRevision, audio: { uri: 'file:///cache/idea.m4a', mediaType: 'audio/mp4' }, keys: { create: 'a', complete: 'b', idea: 'c' },
    });
    expect(accepted.transcript?.state).toBe('PENDING');
    expect(uploads.readFileBytes).toHaveBeenCalledWith('file:///cache/idea.m4a');
    expect(calls[0].args).toEqual([RUN, { expected_run_revision: 8, audio_ref: ASSET }, 'c']);
    expect(JSON.stringify(calls[0].args)).not.toContain('file://');
    // The revision is read after the upload, not before it (the worker moves it meanwhile).
    expect((uploads.sessions.complete as ReturnType<typeof vi.fn>).mock.invocationCallOrder[0]).toBeLessThan(currentRunRevision.mock.invocationCallOrder[0]);
  });

  it('retries a stale voice idea once with the new revision and a new key, and gives up on a second refusal', async () => {
    const stale = new ParentApplicationError('STALE_REVISION', 'stale', 'r', 409);
    let first = true;
    const answer = { story_run_id: RUN, input_revision: 3, run_revision: 10, run_state: 'INPUT_PROCESSING', idea_source: 'VOICE', transcript: { transcript_revision: 1, state: 'PENDING' } };
    const addRunIdeaV1 = vi.fn(async () => { if (first) { first = false; throw stale; } return answer; });
    const revisions = [8, 9];
    const accepted = await new ParentLearningUseCases(fakeApi({ addRunIdeaV1 }).api, uploadPort()).submitVoiceIdeaV1({
      runId: RUN, currentRunRevision: async () => revisions.shift() as number,
      audio: { uri: 'file:///a.m4a', mediaType: 'audio/mp4' }, keys: { create: 'a', complete: 'b', idea: 'c' },
    });
    expect(accepted.run_revision).toBe(10);
    const [firstCall, secondCall] = addRunIdeaV1.mock.calls as unknown as Array<[string, { expected_run_revision: number }, string]>;
    expect(firstCall[1].expected_run_revision).toBe(8);
    expect(secondCall[1].expected_run_revision).toBe(9);
    expect(secondCall[2]).not.toBe('c');

    const alwaysStale = vi.fn(async () => { throw stale; });
    await expect(new ParentLearningUseCases(fakeApi({ addRunIdeaV1: alwaysStale }).api, uploadPort()).submitVoiceIdeaV1({
      runId: RUN, currentRunRevision: async () => 1, audio: { uri: 'file:///a.m4a', mediaType: 'audio/mp4' }, keys: { create: 'a', complete: 'b', idea: 'c' },
    })).rejects.toMatchObject({ code: 'STALE_REVISION' });
    expect(alwaysStale).toHaveBeenCalledTimes(2);
  });

  it('bounds the typed idea and the correction, and keeps the exact base revision', async () => {
    const { api, calls } = fakeApi();
    const cases = new ParentLearningUseCases(api, uploadPort());
    await expect(cases.submitTextIdeaV1(RUN, 3, '   ', 'k')).rejects.toMatchObject({ code: 'PARENT_IDEA_TEXT_INVALID' });
    await expect(cases.submitTextIdeaV1(RUN, 3, 'x'.repeat(501), 'k')).rejects.toMatchObject({ code: 'PARENT_IDEA_TEXT_INVALID' });
    await cases.correctTranscriptV1({ runId: RUN, runRevision: 5, baseRevision: 2, text: '  đã sửa  ', actionIdentity: 'k' });
    expect(calls.at(-1)?.args[1]).toEqual({ expected_run_revision: 5, transcript_correction: { base_revision: 2, text: 'đã sửa' } });
    await expect(cases.correctTranscriptV1({ runId: RUN, runRevision: 5, baseRevision: 0, text: 'x', actionIdentity: 'k' })).rejects.toMatchObject({ code: 'PARENT_TRANSCRIPT_TEXT_INVALID' });
  });

  it('rewrites from the displayed revision and hash, with the hint only when typed, and stops at revision 4', async () => {
    const { api, calls } = fakeApi();
    const cases = new ParentLearningUseCases(api, uploadPort());
    await cases.rewriteStoryV1(runOf({ story_revision_no: 2 }), '  thêm bạn mới  ', 'k');
    expect(calls[0].args[1]).toEqual({ expected_story_revision: 2, expected_story_sha256: SHA, hint: 'thêm bạn mới' });
    await cases.rewriteStoryV1(runOf({ story_revision_no: 2 }), undefined, 'k2');
    expect(calls[1].args[1]).toEqual({ expected_story_revision: 2, expected_story_sha256: SHA });
    await expect(cases.rewriteStoryV1(runOf({ story_revision_no: 4 }), 'x', 'k')).rejects.toMatchObject({ code: 'STORY_REWRITE_LIMIT_REACHED' });
    await expect(cases.rewriteStoryV1(runOf({ story_revision_no: null }), 'x', 'k')).rejects.toMatchObject({ code: 'PARENT_STORY_REVISION_INVALID' });
    await expect(cases.rewriteStoryV1(runOf({ story_revision_no: 1 }), 'x'.repeat(401), 'k')).rejects.toMatchObject({ code: 'PARENT_REWRITE_HINT_INVALID' });
    await expect(cases.rewriteStoryV1(runOf({ story_revision_no: 1 }), 'dòng 1\ndòng 2', 'k')).rejects.toMatchObject({ code: 'PARENT_REWRITE_HINT_INVALID' });
    // A rewrite answer for a different revision than the next one is not trusted.
    const wrong = fakeApi({ createStoryRewriteV1: vi.fn(async () => ({ story_run_id: RUN, story_revision_no: 4, run_revision: 3, run_state: 'SCRIPT_GENERATING' })) });
    await expect(new ParentLearningUseCases(wrong.api, uploadPort()).rewriteStoryV1(runOf({ story_revision_no: 2 }), 'x', 'k')).rejects.toMatchObject({ code: 'PARENT_REWRITE_RESULT_INVALID' });
  });

  it('accepts a first-story recovery from revision 1 without a hash and replays the same action identity', async () => {
    const rewrite = vi.fn(async () => ({
      story_run_id: RUN,
      story_revision_no: 2,
      run_revision: 8,
      run_state: 'SCRIPT_GENERATING',
    }));
    const { api } = fakeApi({ createStoryRewriteV1: rewrite });
    const cases = new ParentLearningUseCases(api, uploadPort());
    const failedFirstStory = runOf({
      run_state: 'FAILED',
      story_revision_no: 1,
      story_status: 'FAILED',
      story_sha256: null,
      job_state: 'FAILED',
      error_code: 'STORY_OUTPUT_INVALID',
      retryable: false,
    });

    const first = await cases.rewriteStoryV1(failedFirstStory, '  add a friend  ', 'recovery-key');
    const replay = await cases.rewriteStoryV1(failedFirstStory, '  add a friend  ', 'recovery-key');
    await cases.rewriteStoryV1(failedFirstStory, undefined, 'recovery-key-without-hint');

    expect(first.story_revision_no).toBe(2);
    expect(replay.story_revision_no).toBe(2);
    const calls = rewrite.mock.calls as unknown as Array<[string, { expected_story_revision: number; expected_story_sha256?: string; hint?: string }, string]>;
    expect(calls[0][1]).toEqual({ expected_story_revision: 1, hint: 'add a friend' });
    expect(calls[1][1]).toEqual(calls[0][1]);
    expect(calls[0][2]).toBe(calls[1][2]);
    expect(calls[2][1]).toEqual({ expected_story_revision: 1 });
  });

  it('asks for a video only from the confirmed script, with a reason exactly from the second request on', async () => {
    const { api, calls } = fakeApi();
    const cases = new ParentLearningUseCases(api, uploadPort());
    await cases.requestVideoV1(runOf({ video: null }), null, 'k');
    expect(calls[0].args[1]).toEqual({ expected_revision: 7, story_sha256: SHA });
    await cases.requestVideoV1(runOf({ video: videoOf({ video_requests_used: 1 }) }), 'QUALITY_LOW', 'k2');
    expect(calls[1].args[1]).toEqual({ expected_revision: 7, story_sha256: SHA, quality_reason_code: 'QUALITY_LOW' });
    await expect(cases.requestVideoV1(runOf({ video: videoOf({ video_requests_used: 1 }) }), null, 'k')).rejects.toMatchObject({ code: 'PARENT_VIDEO_REASON_INVALID' });
    await expect(cases.requestVideoV1(runOf({ video: null }), 'OTHER', 'k')).rejects.toMatchObject({ code: 'PARENT_VIDEO_REASON_INVALID' });
    await expect(cases.requestVideoV1(runOf({ story_status: 'DRAFT' }), null, 'k')).rejects.toMatchObject({ code: 'PARENT_STORY_NOT_CONFIRMABLE' });
    await expect(cases.requestVideoV1(runOf({ run_state: 'VIDEO_READY' }), null, 'k')).rejects.toMatchObject({ code: 'PARENT_STORY_NOT_CONFIRMABLE' });
  });

  it('marks the current ready video unsuitable and completes only at VIDEO_READY', async () => {
    const { api, calls } = fakeApi();
    const cases = new ParentLearningUseCases(api, uploadPort());
    await cases.markVideoUnsuitableV1(runOf({ run_state: 'VIDEO_READY', video: videoOf() }), 'NOT_MATCHING_STORY', 'k');
    expect(calls[0].args[1]).toEqual({ expected_revision: 7, generation_id: GENERATION, reason_code: 'NOT_MATCHING_STORY' });
    await cases.completeRunV1(runOf({ run_state: 'VIDEO_READY' }), 'k2');
    expect(calls[1].args).toEqual([RUN, 7, 'k2']);
    expect(() => cases.markVideoUnsuitableV1(runOf({ run_state: 'SCRIPT_REVIEW' }), 'OTHER', 'k')).toThrow(ParentApplicationError);
    expect(() => cases.completeRunV1(runOf({ run_state: 'SCRIPT_REVIEW' }), 'k')).toThrow(ParentApplicationError);
  });
});
