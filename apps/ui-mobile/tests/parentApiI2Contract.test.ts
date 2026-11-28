import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort, ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import { ParentProfileUseCases } from '../src/parent/application/use-cases/ParentProfileUseCases';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import { svgGuideFailureMessage } from '../src/parent/domain/svgGuide';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://api.example.test' },
}));

type Reply = { status: number; body: Record<string, unknown> };
type FetchCall = { url: string; init: RequestInit };

function createApi(replies: Reply[]) {
  const calls: FetchCall[] = [];
  const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'synthetic-token') };
  const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    calls.push({ url: String(input), init });
    const reply = replies.shift() ?? { status: 200, body: {} };
    return {
      ok: reply.status >= 200 && reply.status < 300,
      status: reply.status,
      headers: new Headers({ 'X-Request-ID': 'synthetic-response-request' }),
      json: async () => reply.body,
    } as Response;
  }) as unknown as typeof fetch;
  return { api: new ParentApi(auth, fetcher, 'https://api.example.test'), auth, calls, fetcher };
}

function requestBody(call: FetchCall): Record<string, unknown> {
  return JSON.parse(String(call.init.body)) as Record<string, unknown>;
}

function header(call: FetchCall, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

const profileRef = { profile_id: 'synthetic-profile', revision_no: 1, revision_hash: 'hash-1' };
const activeProfile = {
  ...profileRef,
  state: 'ACTIVE',
  display_name: 'Bé Mây',
  age_months: 72,
  age_band_ref: 'age-6',
  age_band_version: 'age-6-v1',
  interests_summary: null,
  data_origin: 'PARENT_CREATED',
};
const runEnvelope = {
  request_id: 'synthetic-request',
  story_run: {
    run_id: 'synthetic-run',
    run_state: 'INPUT_PROCESSING',
    parent_profile_id: 'synthetic-profile',
    context_revision: 2,
    context_snapshot: { topic: 'mây', adult_confirmed_idea: 'vẽ một chiếc diều' },
    context_snapshot_sha256: 'snapshot-hash',
    lesson_pin_snapshot: { lesson_id: 'lesson-1', version_id: 'lesson-version-1', content_sha256: 'lesson-hash' },
  },
};

describe('ParentApi I2 contract', () => {
  it('sends stable request IDs when rotating curated topic and drawing-subject cards', async () => {
    const topicDraft = {
      contract: 'ParentTopicSuggestionSetV1', set_id: 'pts_000000000000000000000001',
      request_id: '00000000-0000-4000-8000-000000000001', draft_id: '00000000-0000-4000-8000-000000000010',
      catalog_revision: 'parent-topic-catalog-v1', excluded_set_ids: [],
      cards: [
        { topic_id: 'animals', title_vi: 'Động vật', description_vi: 'Các bạn quanh bé' },
        { topic_id: 'plants', title_vi: 'Cây cối', description_vi: 'Cây xanh quanh nhà' },
        { topic_id: 'weather', title_vi: 'Thời tiết', description_vi: 'Nắng, mưa và gió' },
      ],
    };
    const subjectDraft = {
      contract: 'ParentDrawingSubjectSuggestionSetV1', set_id: 'pds_000000000000000000000002',
      request_id: '00000000-0000-4000-8000-000000000002', draft_id: '00000000-0000-4000-8000-000000000010',
      topic_id: 'animals', topic: 'Động vật',
      catalog_revision: 'parent-topic-catalog-v1', generation_source: 'CURATED_CATALOG',
      review_required: true, excluded_set_ids: [],
      cards: [
        { subject_id: 'deer', title_vi: 'Hươu', guide_subject: 'con hươu', relation_to_topic_vi: 'Động vật trong rừng' },
        { subject_id: 'turtle', title_vi: 'Rùa', guide_subject: 'con rùa', relation_to_topic_vi: 'Động vật gần gũi' },
        { subject_id: 'chicken', title_vi: 'Gà', guide_subject: 'con gà', relation_to_topic_vi: 'Động vật quanh nhà' },
      ],
    };
    const { api, calls } = createApi([
      { status: 200, body: topicDraft },
      { status: 200, body: subjectDraft },
    ]);

    await api.listTopicSuggestions(
      '00000000-0000-4000-8000-000000000010', [], '00000000-0000-4000-8000-000000000001',
    );
    await api.listDrawingSubjectSuggestions({
      draftId: '00000000-0000-4000-8000-000000000010', topicId: 'animals', topic: 'Động vật', excludedSetIds: [],
      requestId: '00000000-0000-4000-8000-000000000002',
    });

    expect(new URL(calls[0].url).pathname).toBe('/api/parent/v1/topics/suggestions');
    expect(new URL(calls[0].url).searchParams.get('request_id')).toBe('00000000-0000-4000-8000-000000000001');
    expect(new URL(calls[1].url).pathname).toBe('/api/parent/v1/topics/animals/drawing-subject-suggestions');
    expect(new URL(calls[1].url).searchParams.get('request_id')).toBe('00000000-0000-4000-8000-000000000002');
  });

  it('encodes opaque profile cursors and reads items/next_cursor', async () => {
    const { api, calls } = createApi([{ status: 200, body: { items: [activeProfile], next_cursor: 'next +/?=', request_id: 'req-1' } }]);
    const page = await api.listProfilesV1(17, 'opaque +/?= token');
    const url = new URL(calls[0].url);

    expect(url.pathname).toBe('/v1/parent/profiles');
    expect(url.searchParams.get('limit')).toBe('17');
    expect(url.searchParams.get('cursor')).toBe('opaque +/?= token');
    expect(url.search).toContain('%2B%2F%3F%3D');
    expect(page.items).toEqual([activeProfile]);
    expect(page.next_cursor).toBe('next +/?=');
  });

  it('uses V1 profile create, read, patch and delete routes with per-action keys', async () => {
    const pending = { profile_id: 'synthetic-profile', state: 'DELETE_PENDING', request_id: 'delete-1' };
    const { api, calls } = createApi([
      { status: 201, body: profileRef },
      { status: 200, body: activeProfile },
      { status: 200, body: activeProfile },
      { status: 202, body: pending },
    ]);

    const created = await api.createProfileV1({ display_name: 'Bé Mây', age_months: 72, interests_summary: null }, 'create-action-1');
    const read = await api.getProfileV1('profile/a');
    const patched = await api.patchProfileV1('synthetic-profile', {
      expected_revision: 1, display_name: 'Bé Mây', age_months: 72,
    }, 'patch-action-1');
    const deletion = await api.requestProfileDeletionV1('synthetic-profile', 'delete-action-1');

    expect(calls.map((call) => new URL(call.url).pathname)).toEqual([
      '/v1/parent/profiles', '/v1/parent/profiles/profile%2Fa',
      '/v1/parent/profiles/synthetic-profile', '/v1/parent/profiles/synthetic-profile',
    ]);
    expect(header(calls[0], 'Idempotency-Key')).toBe('create-action-1');
    expect(header(calls[2], 'Idempotency-Key')).toBe('patch-action-1');
    expect(header(calls[3], 'Idempotency-Key')).toBe('delete-action-1');
    expect(created).toEqual(profileRef);
    expect(read).toEqual(activeProfile);
    expect(patched).toEqual(activeProfile);
    expect(requestBody(calls[0])).not.toHaveProperty('consent_policy_version');
    expect(deletion.state).toBe('DELETE_PENDING');
  });

  it('keeps an untouched context picker omitted and sends an explicit empty selection as an empty array', async () => {
    const { api, calls } = createApi([
      { status: 200, body: { request_id: 'receipt-v1', story_run: {} } },
      { status: 200, body: { request_id: 'receipt-v2', story_run: {} } },
    ]);
    const base = { expected_context_revision: 2, context_snapshot_sha256: 'snapshot-hash', confirmed: true as const };

    await api.confirmStoryRunContextV1('synthetic-run', base, 'context-v1-action');
    await api.confirmStoryRunContextV1('synthetic-run', { ...base, selected_context_entry_ids: [] }, 'context-v2-empty-action');

    expect(requestBody(calls[0])).toEqual(base);
    expect(requestBody(calls[0])).not.toHaveProperty('selected_context_entry_ids');
    expect(requestBody(calls[1])).toEqual({ ...base, selected_context_entry_ids: [] });
    expect(header(calls[0], 'Idempotency-Key')).toBe('context-v1-action');
    expect(header(calls[1], 'Idempotency-Key')).toBe('context-v2-empty-action');
  });

  it('preserves omitted and null interests_summary patch bodies', async () => {
    const { api, calls } = createApi([
      { status: 200, body: activeProfile },
      { status: 200, body: activeProfile },
      { status: 200, body: activeProfile },
    ]);
    const base = { expected_revision: 1, display_name: 'Bé Mây', age_months: 72 };

    await api.patchProfileV1('synthetic-profile', base, 'patch-same-action');
    await api.patchProfileV1('synthetic-profile', base, 'patch-same-action');
    await api.patchProfileV1('synthetic-profile', { ...base, interests_summary: null }, 'patch-new-action');

    expect(requestBody(calls[0])).not.toHaveProperty('interests_summary');
    expect(requestBody(calls[1])).not.toHaveProperty('interests_summary');
    expect(requestBody(calls[2]).interests_summary).toBeNull();
    expect(header(calls[0], 'Idempotency-Key')).toBe('patch-same-action');
    expect(header(calls[1], 'Idempotency-Key')).toBe('patch-same-action');
    expect(header(calls[2], 'Idempotency-Key')).toBe('patch-new-action');
    expect(header(calls[2], 'Idempotency-Key')).not.toBe(header(calls[0], 'Idempotency-Key'));
  });

  it('reuses keys for create actions and uses a new key for a new profile action', async () => {
    const { api, calls } = createApi([
      { status: 201, body: profileRef },
      { status: 201, body: profileRef },
      { status: 201, body: profileRef },
    ]);
    const input = { display_name: 'Bé Mây', age_months: 72 };

    await api.createProfileV1(input, 'profile-create-action-a');
    await api.createProfileV1(input, 'profile-create-action-a');
    await api.createProfileV1(input, 'profile-create-action-b');

    const keys = calls.map((call) => header(call, 'Idempotency-Key'));
    expect(keys).toEqual(['profile-create-action-a', 'profile-create-action-a', 'profile-create-action-b']);
  });

  it('reconciles DELETE_PENDING by GET-by-ID and distinguishes replay from a new pending delete', async () => {
    const pending = { profile_id: 'synthetic-profile', state: 'DELETE_PENDING', request_id: 'delete-request' };
    const { api, calls } = createApi([
      { status: 202, body: pending },
      { status: 200, body: pending },
      { status: 202, body: pending },
      { status: 409, body: { code: 'INVALID_STATE_TRANSITION', message: 'child detail must not leak' } },
    ]);

    await expect(api.requestProfileDeletionV1('synthetic-profile', 'delete-action-a')).resolves.toEqual(pending);
    await expect(api.getProfileV1('synthetic-profile')).resolves.toEqual(pending);
    await expect(api.requestProfileDeletionV1('synthetic-profile', 'delete-action-a')).resolves.toEqual(pending);
    const error = await api.requestProfileDeletionV1('synthetic-profile', 'delete-action-b').catch((value: unknown) => value);

    expect(calls.map((call) => call.init.method)).toEqual(['DELETE', 'GET', 'DELETE', 'DELETE']);
    expect(header(calls[0], 'Idempotency-Key')).toBe('delete-action-a');
    expect(header(calls[2], 'Idempotency-Key')).toBe('delete-action-a');
    expect(header(calls[3], 'Idempotency-Key')).toBe('delete-action-b');
    expect(error).toBeInstanceOf(ParentApiError);
    expect((error as Error).message).toBe('Trạng thái hồ sơ đã thay đổi. Hãy tải lại hồ sơ.');
    expect((error as Error).message).not.toContain('child detail');
  });

  it('refreshes a stale profile after one patch attempt and returns it for adult review', async () => {
    const profileApi = {
      patchProfileV1: vi.fn(async () => { throw new ParentApiError('STALE_REVISION', 'stale-request', 409); }),
      getProfileV1: vi.fn(async () => activeProfile),
    };
    const useCases = new ParentProfileUseCases(profileApi as unknown as ParentApiPort);

    const result = await useCases.patchV1('synthetic-profile', {
      expected_revision: 1, display_name: 'Bé Mây', age_months: 72,
    }, 'patch-action-once');

    expect(profileApi.patchProfileV1).toHaveBeenCalledTimes(1);
    expect(profileApi.patchProfileV1).toHaveBeenCalledWith('synthetic-profile', {
      expected_revision: 1, display_name: 'Bé Mây', age_months: 72,
    }, 'patch-action-once');
    expect(profileApi.getProfileV1).toHaveBeenCalledWith('synthetic-profile');
    expect(result).toEqual({ status: 'STALE', profile: activeProfile });
  });

  it('creates a pinned pre-drawing run and confirms the returned context with action identities', async () => {
    const { api, calls } = createApi([
      { status: 201, body: runEnvelope },
      { status: 200, body: runEnvelope },
      { status: 201, body: runEnvelope },
      { status: 200, body: runEnvelope },
      { status: 200, body: runEnvelope },
      { status: 200, body: runEnvelope },
    ]);
    const createBody = {
      parent_profile_id: 'synthetic-profile', topic: 'mây', adult_confirmed_idea: 'vẽ một chiếc diều',
      lesson_version: { lesson_id: 'lesson-1', version_id: 'lesson-version-1', content_sha256: 'lesson-hash' },
    };
    const contextBody = { expected_context_revision: 2, context_snapshot_sha256: 'snapshot-hash', confirmed: true as const };

    await api.createStoryRunV1(createBody, 'story-create-action-a');
    await api.createStoryRunV1(createBody, 'story-create-action-a');
    await api.createStoryRunV1(createBody, 'story-create-action-b');
    await api.confirmStoryRunContextV1('synthetic-run', contextBody, 'context-action-a');
    await api.confirmStoryRunContextV1('synthetic-run', contextBody, 'context-action-a');
    await api.confirmStoryRunContextV1('synthetic-run', contextBody, 'context-action-b');

    expect(calls.slice(0, 3).map((call) => header(call, 'Idempotency-Key'))).toEqual([
      'story-create-action-a', 'story-create-action-a', 'story-create-action-b',
    ]);
    expect(calls.slice(3).map((call) => header(call, 'Idempotency-Key'))).toEqual([
      'context-action-a', 'context-action-a', 'context-action-b',
    ]);
    expect(requestBody(calls[0])).toEqual(createBody);
    expect(requestBody(calls[0])).not.toHaveProperty('photo');
    expect(requestBody(calls[0])).not.toHaveProperty('consent_policy_version');
    expect(requestBody(calls[0])).not.toHaveProperty('expected_profile_revision_id');
    expect(requestBody(calls[0])).not.toHaveProperty('context_confirmed');
    expect(new URL(calls[3].url).pathname).toBe('/v1/story-runs/synthetic-run/context-confirmation');
    expect(requestBody(calls[3])).toEqual(contextBody);
  });

  it('only serializes Parent create fields even if a caller supplies Teacher fields at runtime', async () => {
    const { api, calls } = createApi([{ status: 201, body: runEnvelope }]);
    const input = {
      parent_profile_id: 'synthetic-profile', topic: 'clouds', adult_confirmed_idea: 'kite',
      occurrence_id: 'teacher-occurrence', selection_id: 'teacher-selection', plan_revision: 2,
      lesson_version: { lesson_id: 'lesson-1', version_id: 'v1', content_sha256: 'hash', selection_id: 'hidden' },
    };
    expect(await api.createStoryRunV1(input, 'parent-action')).toEqual(runEnvelope);
    expect(new URL(calls[0].url).pathname).toBe('/v1/story-runs');
    expect(header(calls[0], 'Idempotency-Key')).toBe('parent-action');
    expect(requestBody(calls[0])).toEqual({
      parent_profile_id: 'synthetic-profile', topic: 'clouds', adult_confirmed_idea: 'kite',
      lesson_version: { lesson_id: 'lesson-1', version_id: 'v1', content_sha256: 'hash' },
    });
  });

  it('keeps an omitted lesson pin omitted and an explicit null pin null in the create body', async () => {
    const { api, calls } = createApi([{ status: 201, body: runEnvelope }, { status: 201, body: runEnvelope }]);
    const base = { parent_profile_id: 'synthetic-profile', topic: 'clouds', adult_confirmed_idea: 'kite' };
    await api.createStoryRunV1(base, 'parent-action-1');
    await api.createStoryRunV1({ ...base, lesson_version: null }, 'parent-action-2');
    expect(String(calls[0].init.body)).not.toContain('lesson_version');
    expect(requestBody(calls[0])).toEqual(base);
    expect(requestBody(calls[1])).toEqual({ ...base, lesson_version: null });
  });

  it('uses the versioned active/read/subject/script/revision routes and explicit action keys', async () => {
    const { api, calls } = createApi([
      { status: 200, body: { request_id: 'active-request', story_run: null } },
      { status: 200, body: runEnvelope },
      { status: 200, body: { request_id: 'subject-request', story_run_id: 'synthetic-run', understanding_revision: 2, decision: 'CONFIRMED' } },
      { status: 200, body: runEnvelope },
      { status: 200, body: { request_id: 'revision-request', story_sha256: 'story-hash' } },
    ]);

    const activeRun = await api.getActiveStoryRunV1();
    await api.getStoryRunV1('synthetic-run');
    await api.confirmStoryRunSubjectV1('synthetic-run', 2, 'một chiếc diều', 'subject-action');
    await api.confirmStoryRunScriptV1('synthetic-run', 3, 'story-hash', 'script-action');
    await api.createStoryRevisionV1('synthetic-run', 2, 'thêm đám mây', 'revision-action');

    expect(activeRun).toEqual({ request_id: 'active-request', story_run: null });

    expect(calls.map((call) => `${call.init.method} ${new URL(call.url).pathname}`)).toEqual([
      'GET /v1/story-runs/active/current',
      'GET /v1/story-runs/synthetic-run',
      'POST /v1/story-runs/synthetic-run/subject-confirmation',
      'POST /v1/story-runs/synthetic-run/script-confirmation',
      'POST /api/parent/v1/ai/story-runs/synthetic-run/story-revisions',
    ]);
    expect(header(calls[2], 'Idempotency-Key')).toBe('subject-action');
    expect(header(calls[3], 'Idempotency-Key')).toBe('script-action');
    expect(header(calls[4], 'Idempotency-Key')).toBe('revision-action');
    expect(requestBody(calls[2])).toEqual({ expected_understanding_revision: 2, confirmed_subject: 'một chiếc diều' });
    expect(requestBody(calls[3])).toEqual({ expected_revision: 3, story_sha256: 'story-hash' });
    expect(requestBody(calls[4])).toEqual({ expected_understanding_revision: 2, rewrite_instruction: 'thêm đám mây' });
  });

  it('pins Phase A activity list and selection routes, headers, body, and safe error codes', async () => {
    const activityRef = { lesson_id: 'lesson-a', version_id: 'version-a', content_sha256: 'a'.repeat(64), activity_index: 2 };
    const activity = {
      activity_ref: activityRef, title: 'Mô phỏng hoạt động', objective: 'Mô phỏng mục tiêu',
      materials_text: 'Giấy', preparation_text: 'Chuẩn bị giấy', instructions_text: 'Cùng quan sát',
      observation_notes: 'Để bé kể', safety_notes: 'Người lớn ở cạnh', activity_kind: 'indoor',
      source: 'PINNED_LESSON', lesson_title: 'Khu vườn', lesson_topic: 'Cây cối',
    };
    const selectedRun = { ...runEnvelope.story_run, run_state: 'PREPARATION_REVIEW', run_revision: 4 };
    const { api, calls } = createApi([
      { status: 200, body: { request_id: 'activity-list', items: [activity], basis: { age_band: '72-107', pinned_lesson: true, no_candidate: false } } },
      { status: 200, body: { request_id: 'activity-selection', story_run: selectedRun } },
    ]);

    await api.listActivitiesV1('synthetic-run');
    await api.selectActivityV1('synthetic-run', { expected_revision: 3, activity: activityRef }, 'select-action-1');

    const listUrl = new URL(calls[0].url);
    expect(`${calls[0].init.method} ${listUrl.pathname}`).toBe('GET /v1/activities');
    expect(listUrl.searchParams.get('story_run_id')).toBe('synthetic-run');
    expect(header(calls[0], 'Idempotency-Key')).toBeNull();
    expect(header(calls[0], 'If-Match')).toBeNull();
    expect(`${calls[1].init.method} ${new URL(calls[1].url).pathname}`).toBe('POST /v1/story-runs/synthetic-run/activity-selection');
    expect(header(calls[1], 'Idempotency-Key')).toBe('select-action-1');
    expect(header(calls[1], 'If-Match')).toBeNull();
    expect(requestBody(calls[1])).toEqual({ expected_revision: 3, activity: activityRef });

    const failed = createApi([
      { status: 503, body: { code: 'DEPENDENCY_UNAVAILABLE', message: 'private dependency detail' } },
      { status: 409, body: { code: 'STALE_REVISION', message: 'private conflict detail', current_version: 9 } },
      { status: 409, body: { code: 'INVALID_STATE_TRANSITION', message: 'private state detail' } },
    ]);
    const listError = await failed.api.listActivitiesV1('synthetic-run').catch((value: unknown) => value);
    const selectError = await failed.api.selectActivityV1('synthetic-run', { expected_revision: 3, activity: activityRef }, 'select-action-2').catch((value: unknown) => value);
    expect(listError).toMatchObject({ code: 'DEPENDENCY_UNAVAILABLE', status: 503 });
    expect((listError as Error).message).not.toContain('private dependency detail');
    expect(selectError).toMatchObject({ code: 'STALE_REVISION', currentVersion: 9 });
    expect((selectError as Error).message).not.toContain('private conflict detail');
    const transitionError = await failed.api.selectActivityV1('synthetic-run', { expected_revision: 3, activity: activityRef }, 'select-action-3').catch((value: unknown) => value);
    expect(transitionError).toMatchObject({ code: 'INVALID_STATE_TRANSITION', status: 409 });
    expect((transitionError as Error).message).not.toContain('private state detail');
    const unknown = createApi([{ status: 503, body: { code: 'PRIVATE_INTERNAL_CODE', message: 'private internals' } }]);
    const unknownError = await unknown.api.listActivitiesV1('synthetic-run').catch((value: unknown) => value);
    expect(unknownError).toMatchObject({ code: 'HTTP_503', status: 503 });
    expect((unknownError as Error).message).not.toContain('PRIVATE_INTERNAL_CODE');
    expect((unknownError as Error).message).not.toContain('private internals');
  });

  it('retains safe top-level and defensive nested error metadata without exposing server messages', async () => {
    const { api } = createApi([
      { status: 403, body: {
        code: 'ACTION_NOT_ALLOWED', message: 'private server detail', request_id: 'profile-request',
        correlation_id: 'profile-correlation', retryable: false,
        field_errors: [{ field: 'display_name', code: 'TOO_LONG' }, { field: 'private_child_field', code: 'REQUIRED' }],
      } },
      { status: 503, body: { code: 'PARENT_STORE_UNAVAILABLE', message: 'store internals', retry_after_seconds: 15, retryable: true } },
      { status: 409, body: { code: 'ACTIVE_RUN_EXISTS', message: 'run detail', correlation_id: 'run-correlation' } },
      { status: 409, body: { code: 'STALE_REVISION', message: 'revision detail', current_version: 3 } },
      { status: 422, body: { detail: { code: 'INVALID_FORMAT', message: 'nested secret', request_id: 'nested-request', field_errors: [{ field: 'interests_summary', code: 'INVALID_FORMAT' }] } } },
    ]);
    const profile = await api.getProfileV1('profile-a').catch((value: unknown) => value);
    const unavailable = await api.listProfilesV1().catch((value: unknown) => value);
    const activeRun = await api.createStoryRunV1({
      parent_profile_id: 'profile-a', topic: 'clouds', adult_confirmed_idea: 'kite',
      lesson_version: { lesson_id: 'lesson-a', version_id: 'v1', content_sha256: 'hash' },
    }, 'story-key').catch((value: unknown) => value);
    const stale = await api.patchProfileV1('profile-a', {
      expected_revision: 2, display_name: 'Bé Mây', age_months: 72,
    }, 'patch-key').catch((value: unknown) => value);
    const nested = await api.getProfileV1('profile-a').catch((value: unknown) => value);

    expect(profile).toBeInstanceOf(ParentApiError);
    expect((profile as ParentApiError).status).toBe(403);
    expect((profile as ParentApiError).code).toBe('ACTION_NOT_ALLOWED');
    expect((profile as ParentApiError).requestId).toBe('profile-request');
    expect((profile as ParentApiError).correlationId).toBe('profile-correlation');
    expect((profile as ParentApiError).fieldErrors).toEqual([{ field: 'display_name', code: 'TOO_LONG' }]);
    expect((profile as Error).message).not.toContain('private server detail');
    expect((unavailable as ParentApiError).retryable).toBe(true);
    expect((unavailable as ParentApiError).retryAfterSeconds).toBe(15);
    expect((unavailable as ParentApiError).message).not.toContain('store internals');
    expect((activeRun as ParentApiError).code).toBe('ACTIVE_RUN_EXISTS');
    expect((activeRun as ParentApiError).correlationId).toBe('run-correlation');
    expect((stale as ParentApiError).code).toBe('STALE_REVISION');
    expect((stale as ParentApiError).currentVersion).toBe(3);
    expect((nested as ParentApiError).requestId).toBe('nested-request');
    expect((nested as ParentApiError).fieldErrors).toEqual([{ field: 'interests_summary', code: 'INVALID_FORMAT' }]);
    expect((nested as Error).message).not.toContain('nested secret');
  });

  it('does not add an idempotency key to drawing-understandings', async () => {
    const { api, calls, fetcher } = createApi([{ status: 200, body: { request_id: 'drawing-request' } }]);
    await api.analyzeDrawing('synthetic-run', 'synthetic-image-data', 'image/png');

    expect(new URL(calls[0].url).pathname).toBe('/api/parent/v1/ai/drawing-understandings');
    expect(header(calls[0], 'Idempotency-Key')).toBeNull();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('does not retry an unknown Modal outcome automatically', async () => {
    const { api, calls, fetcher } = createApi([
      { status: 504, body: { code: 'MODAL_OUTCOME_UNKNOWN', message: 'private provider detail', retryable: false } },
    ]);

    await expect(api.createStoryRevisionV1('synthetic-run', 2, undefined, 'revision-action-once'))
      .rejects.toMatchObject({ code: 'MODAL_OUTCOME_UNKNOWN' });

    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(header(calls[0], 'Idempotency-Key')).toBe('revision-action-once');
  });

  it('uses the catalog topic and subject routes with the backend query and body fields', async () => {
    const topicSet = {
      contract: 'ParentTopicSuggestionSetV1', set_id: 'pts_000000000000000000000001',
      draft_id: '00000000-0000-4000-8000-000000000001', catalog_revision: 'topics-v1', excluded_set_ids: [],
      cards: [
        { topic_id: 'animals', title_vi: 'Động vật', description_vi: 'Những người bạn quanh ta' },
        { topic_id: 'nature', title_vi: 'Thiên nhiên', description_vi: 'Cây cối và hoa lá' },
        { topic_id: 'ocean', title_vi: 'Đại dương', description_vi: 'Sinh vật dưới biển' },
      ],
    };
    const subjectSet = {
      contract: 'ParentDrawingSubjectSuggestionSetV1', set_id: 'pds_000000000000000000000002',
      draft_id: '00000000-0000-4000-8000-000000000001', topic_id: 'animals', topic: 'Động vật',
      catalog_revision: 'subjects-v1', generation_source: 'CURATED_CATALOG', review_required: true,
      excluded_set_ids: [], cards: [
        { subject_id: 'cat', title_vi: 'Con mèo', guide_subject: 'con mèo', relation_to_topic_vi: 'Vật nuôi' },
        { subject_id: 'bird', title_vi: 'Chim sẻ', guide_subject: 'chim sẻ', relation_to_topic_vi: 'Động vật bay' },
        { subject_id: 'fish', title_vi: 'Cá vàng', guide_subject: 'cá vàng', relation_to_topic_vi: 'Động vật dưới nước' },
      ],
    };
    const validation = {
      contract: 'ParentCustomSubjectValidationV1', decision: 'ON_TOPIC',
      normalized_subject: 'con mèo', message_vi: 'Lựa chọn phù hợp với chủ đề.',
    };
    const { api, calls } = createApi([
      { status: 200, body: topicSet }, { status: 200, body: subjectSet }, { status: 200, body: validation },
    ]);

    const topicExclusions = Array.from({ length: 18 }, (_, index) => `pts_${String(index + 1).padStart(24, '0')}`);
    const subjectSetExclusions = Array.from({ length: 18 }, (_, index) => `pds_${String(index + 1).padStart(24, '0')}`);
    const subjectTextExclusions = Array.from({ length: 26 }, (_, index) => `subject-${index + 1}`);
    await api.listTopicSuggestions('00000000-0000-4000-8000-000000000001', topicExclusions);
    await api.listDrawingSubjectSuggestions({
      draftId: '00000000-0000-4000-8000-000000000001', topicId: 'animals', topic: 'Động vật',
      excludedSetIds: subjectSetExclusions, excludedSubjects: subjectTextExclusions,
    });
    await api.validateCustomSubject({ topicId: 'animals', topic: 'Động vật', subject: 'con mèo' });

    const topicUrl = new URL(calls[0].url);
    expect(topicUrl.pathname).toBe('/api/parent/v1/topics/suggestions');
    expect(topicUrl.searchParams.get('draft_id')).toBe('00000000-0000-4000-8000-000000000001');
    expect(topicUrl.searchParams.getAll('exclude_set_ids')).toEqual(topicExclusions.slice(-16));
    const subjectUrl = new URL(calls[1].url);
    expect(subjectUrl.pathname).toBe('/api/parent/v1/topics/animals/drawing-subject-suggestions');
    expect(subjectUrl.searchParams.get('topic')).toBe('Động vật');
    expect(subjectUrl.searchParams.getAll('exclude_set_ids')).toEqual(subjectSetExclusions.slice(-16));
    expect(subjectUrl.searchParams.getAll('exclude_subjects')).toEqual(subjectTextExclusions.slice(-24));
    expect(new URL(calls[2].url).pathname).toBe('/api/parent/v1/topics/custom-subject-validation');
    expect(requestBody(calls[2])).toEqual({ topic_id: 'animals', topic: 'Động vật', subject: 'con mèo' });
  });

  it('normalizes drawing-subject exclusions and sends only backend-supported lengths', async () => {
    const { api, calls } = createApi([{ status: 200, body: {} }]);

    await api.listDrawingSubjectSuggestions({
      draftId: '00000000-0000-4000-8000-000000000001',
      topicId: 'animals',
      topic: 'Động vật',
      excludedSetIds: [],
      excludedSubjects: [
        'a'.repeat(81),
        'b'.repeat(120),
        'c'.repeat(80),
        'de',
        'f',
        '   ',
        '  red\t  apple\n  ',
      ],
    });

    expect(new URL(calls[0].url).searchParams.getAll('exclude_subjects')).toEqual([
      'c'.repeat(80),
      'de',
      'red apple',
    ]);
  });

  it('applies the 24-item drawing-subject exclusion window after filtering', async () => {
    const { api, calls } = createApi([{ status: 200, body: {} }]);
    const subjects = Array.from({ length: 26 }, (_, index) => `subject-${index + 1}`);

    await api.listDrawingSubjectSuggestions({
      draftId: '00000000-0000-4000-8000-000000000001',
      topicId: 'animals',
      topic: 'Động vật',
      excludedSetIds: [],
      excludedSubjects: [...subjects, 'x'],
    });

    expect(new URL(calls[0].url).searchParams.getAll('exclude_subjects')).toEqual(subjects.slice(-24));
  });

  it('sends the versioned SVG topic-guide request body without the retired step_count field', async () => {
    const { api, calls } = createApi([{ status: 200, body: { contract: 'SvgTopicStrokeGuideSourceDraftV1' } }]);

    await api.generateSketchGuide('Động vật', 'con mèo');

    expect(new URL(calls[0].url).pathname).toBe('/api/parent/v1/ai/sketch-guides');
    expect(requestBody(calls[0])).toEqual({
      contract: 'SvgTopicStrokeGuideRequestV1', topic: 'Động vật', intended_subject: 'con mèo', difficulty: 'beginner',
    });
    expect(requestBody(calls[0])).not.toHaveProperty('step_count');
  });

  it('preserves the API Vietnamese messages for disabled topic AI and private topic text', async () => {
    const disabledMessage = 'Chủ đề này chưa có gợi ý trong danh mục. Hãy chọn một chủ đề gợi ý hoặc thử lại sau.';
    const privateTextMessage = 'Chỉ nhập tên chủ đề hoặc đồ vật chung; không nhập tên, thông tin liên hệ hay dữ liệu riêng của trẻ.';
    const { api } = createApi([
      { status: 503, body: { detail: { code: 'PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED', message: disabledMessage } } },
      { status: 422, body: { detail: { code: 'PARENT_TOPIC_TEXT_NOT_ALLOWED', message: privateTextMessage } } },
    ]);

    const disabled = await api.listDrawingSubjectSuggestions({
      draftId: '00000000-0000-4000-8000-000000000001', topicId: 'custom', topic: 'Chủ đề riêng', excludedSetIds: [],
    }).catch((cause: unknown) => cause);
    const privateText = await api.validateCustomSubject({ topicId: 'animals', topic: 'Động vật', subject: 'con mèo' })
      .catch((cause: unknown) => cause);

    expect(disabled).toBeInstanceOf(ParentApiError);
    expect(disabled).toMatchObject({
      code: 'PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED', status: 503,
      message: disabledMessage, safeDisplayMessage: disabledMessage,
    });
    expect(privateText).toBeInstanceOf(ParentApiError);
    expect(privateText).toMatchObject({
      code: 'PARENT_TOPIC_TEXT_NOT_ALLOWED', status: 422,
      message: privateTextMessage, safeDisplayMessage: privateTextMessage,
    });
  });

  it('treats CURATED_SVG_GUIDE_NOT_FOUND as one optional-guide response without a fallback request', async () => {
    const { api, calls, fetcher } = createApi([
      { status: 404, body: { detail: { code: 'CURATED_SVG_GUIDE_NOT_FOUND', message: 'No approved source drawing guide is available.' } } },
    ]);
    const result = await api.generateSketchGuide('Chủ đề chưa có', 'một đồ vật').catch((cause: unknown) => cause);

    expect(result).toBeInstanceOf(ParentApiError);
    expect(result).toMatchObject({ code: 'CURATED_SVG_GUIDE_NOT_FOUND', status: 404 });
    expect(svgGuideFailureMessage((result as ParentApiError).code)).toContain('Bạn vẫn có thể tiếp tục chụp tranh mà không cần gợi ý.');
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(calls).toHaveLength(1);
  });
});
