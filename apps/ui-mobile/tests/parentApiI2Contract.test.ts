import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort, ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import { ParentProfileUseCases } from '../src/parent/application/use-cases/ParentProfileUseCases';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';

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

const backendProfile = {
  parent_profile_id: 'synthetic-profile',
  state: 'ACTIVE',
  current_revision: {
    profile_revision_id: 'synthetic-revision', revision: 1, age_months: 72,
    display_name: 'Bé Mây', interests_summary: '', revision_sha256: 'hash-1', created_at: '2026-11-18T00:00:00Z',
  },
  authorization_state: 'GRANTED', authorization_policy_version: 'parent-v1', authorization_current: true,
  created_at: '2026-11-18T00:00:00Z', updated_at: '2026-11-18T00:00:00Z',
};
const profileEnvelope = { request_id: 'profile-request', profile: backendProfile };
const activeProfile = {
  profile_id: 'synthetic-profile', revision_no: 1, revision_hash: 'hash-1',
  state: 'ACTIVE', display_name: 'Bé Mây', age_months: 72,
  age_band_ref: null, age_band_version: null, interests_summary: null, data_origin: 'PARENT',
  authorization_state: 'GRANTED', authorization_policy_version: 'parent-v1', authorization_current: true,
};
const runEnvelope = {
  request_id: 'synthetic-request',
  story_run: {
    run_id: 'synthetic-run',
    run_state: 'CONTEXT_PENDING',
    parent_profile_id: 'synthetic-profile',
    context_revision: 2,
    context_snapshot: { topic: 'mây', adult_confirmed_idea: 'vẽ một chiếc diều' },
    context_snapshot_sha256: 'snapshot-hash',
    lesson_pin_snapshot: { lesson_id: 'lesson-1', version_id: 'lesson-version-1', content_sha256: 'lesson-hash' },
  },
};

describe('ParentApi I2 contract', () => {
  it('reads the backend consent policy and maps the unpaginated profile collection', async () => {
    const policy = { purpose_code: 'PARENT_LEARNING', policy_version: 'parent-v1', consent_text: 'Nội dung đồng ý', consent_text_sha256: 'policy-hash' };
    const { api, calls } = createApi([
      { status: 200, body: { request_id: 'policy-request', policy } },
      { status: 200, body: { request_id: 'profiles-request', profiles: [backendProfile] } },
    ]);
    const consent = await api.getConsentPolicy();
    const page = await api.listProfilesV1();
    const url = new URL(calls[0].url);

    expect(url.pathname).toBe('/api/parent/v1/consent-policy');
    expect(calls[1].url).toContain('/api/parent/v1/child-profiles');
    expect(consent.policy).toEqual(policy);
    expect(page.items).toEqual([activeProfile]);
    expect(page.next_cursor).toBeNull();
    expect(page.request_id).toBe('profiles-request');
  });

  it('uses backend child-profile routes and sends explicit consent on create', async () => {
    const archivedEnvelope = { request_id: 'archive-request', profile: { ...backendProfile, state: 'ARCHIVED' } };
    const { api, calls } = createApi([
      { status: 201, body: profileEnvelope },
      { status: 200, body: profileEnvelope },
      { status: 200, body: profileEnvelope },
      { status: 200, body: archivedEnvelope },
    ]);

    const created = await api.createProfileV1({
      display_name: 'Bé Mây', age_months: 72, interests_summary: null,
      consent_accepted: true, consent_policy_version: 'parent-v1',
    }, 'create-action-1');
    const read = await api.getProfileV1('profile/a');
    const patched = await api.patchProfileV1('synthetic-profile', {
      expected_revision: 1, display_name: 'Bé Mây', age_months: 72,
    }, 'patch-action-1');
    const deletion = await api.requestProfileDeletionV1('synthetic-profile', 'delete-action-1');

    expect(calls.map((call) => new URL(call.url).pathname)).toEqual([
      '/api/parent/v1/child-profiles', '/api/parent/v1/child-profiles/profile%2Fa',
      '/api/parent/v1/child-profiles/synthetic-profile', '/api/parent/v1/child-profiles/synthetic-profile',
    ]);
    expect(header(calls[0], 'Idempotency-Key')).toBe('create-action-1');
    expect(header(calls[2], 'Idempotency-Key')).toBe('patch-action-1');
    expect(header(calls[3], 'Idempotency-Key')).toBe('delete-action-1');
    expect(created).toEqual(activeProfile);
    expect(read).toEqual(activeProfile);
    expect(patched).toEqual(activeProfile);
    expect(requestBody(calls[0])).toEqual({
      display_name: 'Bé Mây', age_months: 72, interests_summary: '',
      consent_accepted: true, consent_policy_version: 'parent-v1',
    });
    expect(deletion).toEqual({ profile_id: 'synthetic-profile', state: 'ARCHIVED', request_id: 'archive-request' });
  });

  it('preserves omitted and null interests_summary patch bodies', async () => {
    const { api, calls } = createApi([
      { status: 200, body: profileEnvelope },
      { status: 200, body: profileEnvelope },
      { status: 200, body: profileEnvelope },
    ]);
    const base = { expected_revision: 1, display_name: 'Bé Mây', age_months: 72 };

    await api.patchProfileV1('synthetic-profile', base, 'patch-same-action');
    await api.patchProfileV1('synthetic-profile', base, 'patch-same-action');
    await api.patchProfileV1('synthetic-profile', { ...base, interests_summary: null }, 'patch-new-action');

    expect(requestBody(calls[0])).not.toHaveProperty('interests_summary');
    expect(requestBody(calls[1])).not.toHaveProperty('interests_summary');
    expect(requestBody(calls[2]).interests_summary).toBe('');
    expect(header(calls[0], 'Idempotency-Key')).toBe('patch-same-action');
    expect(header(calls[1], 'Idempotency-Key')).toBe('patch-same-action');
    expect(header(calls[2], 'Idempotency-Key')).toBe('patch-new-action');
    expect(header(calls[2], 'Idempotency-Key')).not.toBe(header(calls[0], 'Idempotency-Key'));
  });

  it('reuses keys for create actions and uses a new key for a new profile action', async () => {
    const { api, calls } = createApi([
      { status: 201, body: profileEnvelope },
      { status: 201, body: profileEnvelope },
      { status: 201, body: profileEnvelope },
    ]);
    const input = { display_name: 'Bé Mây', age_months: 72, consent_accepted: true as const, consent_policy_version: 'parent-v1' };

    await api.createProfileV1(input, 'profile-create-action-a');
    await api.createProfileV1(input, 'profile-create-action-a');
    await api.createProfileV1(input, 'profile-create-action-b');

    const keys = calls.map((call) => header(call, 'Idempotency-Key'));
    expect(keys).toEqual(['profile-create-action-a', 'profile-create-action-a', 'profile-create-action-b']);
  });

  it('maps the backend synchronous archive response instead of inventing DELETE_PENDING', async () => {
    const archivedEnvelope = { request_id: 'archive-request', profile: { ...backendProfile, state: 'ARCHIVED' } };
    const { api, calls } = createApi([
      { status: 200, body: archivedEnvelope },
      { status: 200, body: archivedEnvelope },
    ]);

    await expect(api.requestProfileDeletionV1('synthetic-profile', 'delete-action-a')).resolves.toEqual({
      profile_id: 'synthetic-profile', state: 'ARCHIVED', request_id: 'archive-request',
    });
    await expect(api.getProfileV1('synthetic-profile')).resolves.toEqual({
      profile_id: 'synthetic-profile', state: 'ARCHIVED', request_id: 'archive-request',
    });

    expect(calls.map((call) => call.init.method)).toEqual(['DELETE', 'GET']);
    expect(calls.map((call) => new URL(call.url).pathname)).toEqual([
      '/api/parent/v1/child-profiles/synthetic-profile',
      '/api/parent/v1/child-profiles/synthetic-profile',
    ]);
    expect(header(calls[0], 'Idempotency-Key')).toBe('delete-action-a');
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

  it('blocks run creation and separate context confirmation until mobile matches the backend contract', async () => {
    const { api, calls } = createApi([]);
    const createBody = {
      parent_profile_id: 'synthetic-profile', topic: 'mây', adult_confirmed_idea: 'vẽ một chiếc diều',
      lesson_version: { lesson_id: 'lesson-1', version_id: 'lesson-version-1', content_sha256: 'lesson-hash' },
    };
    const contextBody = { expected_context_revision: 2, context_snapshot_sha256: 'snapshot-hash', confirmed: true as const };

    await expect(api.createStoryRunV1(createBody, 'story-create-action-a'))
      .rejects.toMatchObject({ code: 'PARENT_STORY_RUN_CREATE_CONTRACT_MISMATCH' });
    await expect(api.confirmStoryRunContextV1('synthetic-run', contextBody, 'context-action-a'))
      .rejects.toMatchObject({ code: 'PARENT_CONTEXT_CONFIRMATION_ROUTE_MISSING' });
    expect(calls).toHaveLength(0);
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
      'GET /api/parent/v1/story-runs/active/current',
      'GET /api/parent/v1/story-runs/synthetic-run',
      'POST /api/parent/v1/story-runs/synthetic-run/subject-confirmations',
      'POST /api/parent/v1/story-runs/synthetic-run/story-revision-confirmations',
      'POST /api/parent/v1/ai/story-runs/synthetic-run/story-revisions',
    ]);
    expect(header(calls[2], 'Idempotency-Key')).toBe('subject-action');
    expect(header(calls[3], 'Idempotency-Key')).toBe('script-action');
    expect(header(calls[4], 'Idempotency-Key')).toBe('revision-action');
    expect(requestBody(calls[2])).toEqual({ expected_understanding_revision: 2, confirmed_subject: 'một chiếc diều' });
    expect(requestBody(calls[3])).toEqual({ expected_revision: 3, story_sha256: 'story-hash' });
    expect(requestBody(calls[4])).toEqual({ expected_understanding_revision: 2, rewrite_instruction: 'thêm đám mây' });
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
    const activeRun = await api.getActiveStoryRunV1().catch((value: unknown) => value);
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

  it('calls drawing-understandings and activity-suggestions with their exact backend contracts', async () => {
    const activityResult = {
      request_id: 'activity-request',
      story_run_id: 'synthetic-run',
      understanding_revision: 1,
      contract: 'ParentActivitySuggestionResponseV2',
      selection_mode: 'CATALOG_SELECTION',
      catalog_candidate_count: 1,
      review_required: true,
      activities: [{
        title: 'Quan sát khu vườn', objective: 'Nhận ra hình dáng lá', materials_text: 'Giấy và bút màu',
        preparation_text: '', instructions_text: 'Cùng quan sát các chiếc lá.', observation_notes: '',
        safety_notes: '', activity_kind: 'outdoor', source: 'PUBLISHED_SHARED_LESSON',
        source_lesson_id: 'lesson-1', source_lesson_title: 'Khu vườn nhỏ', source_lesson_version_id: 'v1',
        source_content_sha256: 'a'.repeat(64), source_activity_index: 0, match_reason: 'Phù hợp với chủ thể đã xác nhận.',
      }],
    };
    const { api, calls, fetcher } = createApi([
      { status: 200, body: { request_id: 'drawing-request' } },
      { status: 200, body: activityResult },
    ]);
    await api.analyzeDrawing('synthetic-run', 'synthetic-image-data', 'image/png');
    const activities = await api.suggestActivities('synthetic-run', 1);

    expect(new URL(calls[0].url).pathname).toBe('/api/parent/v1/ai/drawing-understandings');
    expect(header(calls[0], 'Idempotency-Key')).toBeNull();
    expect(new URL(calls[1].url).pathname).toBe('/api/parent/v1/ai/story-runs/synthetic-run/activity-suggestions');
    expect(requestBody(calls[1])).toEqual({ expected_understanding_revision: 1 });
    expect(header(calls[1], 'Idempotency-Key')).toBeNull();
    expect(activities).toEqual(activityResult);
    expect(fetcher).toHaveBeenCalledTimes(2);
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
});
