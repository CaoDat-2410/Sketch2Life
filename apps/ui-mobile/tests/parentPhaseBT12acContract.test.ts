import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort } from '../src/parent/application/ports/ParentPorts';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import {
  isParentRunContextSnapshotV2,
  type ParentRunContextSnapshotV1,
  type ParentRunContextSnapshotV2,
} from '../src/parent/domain/types';
import { validateContextEntryRequest, validateSupportNeedsPut } from '../src/parent/application/parentProfileInputValidation';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://api.example.test' },
}));

type Reply = { status: number; body: Record<string, unknown> };
type Call = { url: string; init: RequestInit };

function createApi(replies: Reply[]) {
  const calls: Call[] = [];
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
  return { api: new ParentApi(auth, fetcher, 'https://api.example.test'), calls };
}

function bodyOf(call: Call): Record<string, unknown> {
  return JSON.parse(String(call.init.body)) as Record<string, unknown>;
}

function headerOf(call: Call, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

function caught<T>(operation: Promise<T>): Promise<unknown> {
  return operation.catch((cause: unknown) => cause);
}

describe('Goal v4 Phase B Parent route pins', () => {
  it('validates the new context-entry and support-needs field boundaries', () => {
    expect(validateContextEntryRequest({
      entry_kind: 'OBSERVATION', short_text: `${'é'.repeat(498)}\n\t`, source_kind: 'PARENT_ENTERED',
      approximate_date: '2026-02-28',
    })).toEqual([]);
    expect(validateContextEntryRequest({
      entry_kind: 'OBSERVATION', short_text: ` ${'x'.repeat(500)} `, source_kind: 'PARENT_ENTERED',
      approximate_date: '2026-02-30',
    })).toContainEqual({ field: 'short_text', code: 'TOO_LONG' });
    expect(validateContextEntryRequest({
      entry_kind: 'OBSERVATION', short_text: 'line\u0000break', source_kind: 'parent-entered',
      approximate_date: '2026-02-28',
    })).toEqual(expect.arrayContaining([
      { field: 'short_text', code: 'INVALID_FORMAT' },
      { field: 'source_kind', code: 'INVALID_FORMAT' },
    ]));

    expect(validateSupportNeedsPut({
      expected_revision: 0, category: '😀'.repeat(80), note: 'line\n\tbreak',
    })).toEqual([]);
    expect(validateSupportNeedsPut({
      expected_revision: 0, category: null, note: '\u0000',
    })).toContainEqual({ field: 'note', code: 'INVALID_FORMAT' });
    expect(validateSupportNeedsPut({ expected_revision: 0, category: ' ', note: null }))
      .toContainEqual({ field: 'note', code: 'EMPTY' });
  });

  it('pins both context-entry routes and both support-needs routes', async () => {
    const entry = {
      context_entry_id: 'entry-01', entry_kind: 'OBSERVATION', short_text: 'Quan sát chiếc lá.',
      source_kind: 'PARENT_ENTERED', approximate_date: '2026-11-20', created_at: '2026-11-20T00:00:00Z',
    };
    const list = { context_entries: [entry], next_cursor: 'cursor-next', limit: 25 };
    const writeEntry = { context_entry: entry };
    const support = { contract: 'ParentSupportNeedsV1', profile_id: 'profile-02', revision: 3, category: 'Học tập', note: 'Trao đổi cùng gia đình.' };
    const supportWrite = { contract: 'ParentSupportNeedsWriteV1', profile_id: 'profile-02', revision: 4 };
    const { api, calls } = createApi([
      { status: 200, body: list },
      { status: 201, body: writeEntry },
      { status: 200, body: support },
      { status: 200, body: supportWrite },
    ]);

    const listed = await api.listContextEntriesV1('profile/01', 'opaque +/?=');
    const created = await api.createContextEntryV1('profile/01', {
      entry_kind: 'OBSERVATION', short_text: 'Quan sát chiếc lá.', source_kind: 'PARENT_ENTERED',
      source_ref: 'must-not-be-sent', approximate_date: '2026-11-20',
    }, 'entry-action-01');
    const loaded = await api.getSupportNeedsV1('profile-02');
    const saved = await api.putSupportNeedsV1('profile-02', {
      expected_revision: 3, category: 'Học tập', note: 'Trao đổi cùng gia đình.',
    }, 'support-action-01');

    const firstUrl = new URL(calls[0].url);
    expect(firstUrl.pathname).toBe('/v1/parent/profiles/profile%2F01/context-entries');
    expect(firstUrl.searchParams.get('limit')).toBe('25');
    expect(firstUrl.searchParams.get('cursor')).toBe('opaque +/?=');
    expect(calls[0].init.method).toBe('GET');
    expect(listed).toEqual(list);

    expect(new URL(calls[1].url).pathname).toBe('/v1/parent/profiles/profile%2F01/context-entries');
    expect(calls[1].init.method).toBe('POST');
    expect(headerOf(calls[1], 'Idempotency-Key')).toBe('entry-action-01');
    expect(bodyOf(calls[1])).toEqual({
      entry_kind: 'OBSERVATION', short_text: 'Quan sát chiếc lá.', source_kind: 'PARENT_ENTERED', approximate_date: '2026-11-20',
    });
    expect(bodyOf(calls[1])).not.toHaveProperty('source_ref');
    expect(created).toEqual(writeEntry);

    expect(new URL(calls[2].url).pathname).toBe('/v1/parent/profiles/profile-02/support-needs');
    expect(calls[2].init.method).toBe('GET');
    expect(loaded).toEqual(support);

    expect(new URL(calls[3].url).pathname).toBe('/v1/parent/profiles/profile-02/support-needs');
    expect(calls[3].init.method).toBe('PUT');
    expect(headerOf(calls[3], 'Idempotency-Key')).toBe('support-action-01');
    expect(bodyOf(calls[3])).toEqual({ expected_revision: 3, category: 'Học tập', note: 'Trao đổi cùng gia đình.' });
    expect(saved).toEqual(supportWrite);
    expect(saved).not.toHaveProperty('category');
    expect(saved).not.toHaveProperty('note');
  });

  it('keeps the V1 snapshot unchanged and recognizes the V2 selected-entry shape', () => {
    const v1: ParentRunContextSnapshotV1 = {
      schema_version: 'sketch2life.parent-context.v1', profile_revision_ref: 'revision-01', age_months: 72,
      interests_summary: 'Màu sắc', topic: 'Khu vườn', adult_confirmed_idea: 'Vẽ chiếc lá.',
    };
    const v2: ParentRunContextSnapshotV2 = {
      schema_version: 'sketch2life.parent-context.v2', profile_revision_ref: 'revision-01', age_months: 72,
      interests_summary: 'Màu sắc', topic: 'Khu vườn', adult_confirmed_idea: 'Vẽ chiếc lá.',
      selected_entries: [{ kind: 'OBSERVATION', text: 'Quan sát chiếc lá.' }],
    };

    expect(isParentRunContextSnapshotV2(v1)).toBe(false);
    expect(isParentRunContextSnapshotV2(v2)).toBe(true);
    expect(v2.selected_entries).toHaveLength(1);
  });

  it('allows the new route codes and strips server field text from errors', async () => {
    const hiddenText = 'private support detail';
    const { api } = createApi([
      { status: 503, body: { code: 'SUPPORT_NEEDS_UNAVAILABLE' } },
      { status: 404, body: { code: 'PROFILE_NOT_FOUND' } },
      { status: 400, body: { code: 'INVALID_REQUEST', field_errors: [{ field: 'category', code: 'DIAGNOSIS_LIKE', message: hiddenText }] } },
      { status: 404, body: { code: 'RESOURCE_NOT_FOUND' } },
      { status: 503, body: { code: 'PARENT_STORY_RUN_STORE_UNAVAILABLE' } },
      { status: 409, body: { code: 'STALE_REVISION', current_version: 5 } },
      { status: 409, body: { code: 'INVALID_STATE_TRANSITION' } },
      { status: 400, body: { code: 'INVALID_REQUEST', field_errors: [{ field: 'selected_context_entry_ids', code: 'TOO_LONG' }] } },
    ]);

    const unavailable = await caught(api.getSupportNeedsV1('profile-02'));
    const missing = await caught(api.getSupportNeedsV1('profile-gone'));
    const diagnosis = await caught(api.putSupportNeedsV1('profile-02', {
      expected_revision: 0, category: hiddenText, note: null,
    }, 'support-action-02'));
    const entryMissing = await caught(api.confirmStoryRunContextV1('run-01', {
      expected_context_revision: 1, context_snapshot_sha256: 'snapshot', confirmed: true,
      selected_context_entry_ids: ['00000000-0000-4000-8000-000000000001'],
    }, 'confirm-action-01'));
    const runUnavailable = await caught(api.confirmStoryRunContextV1('run-01', {
      expected_context_revision: 1, context_snapshot_sha256: 'snapshot', confirmed: true,
    }, 'confirm-action-02'));
    const stale = await caught(api.putSupportNeedsV1('profile-02', {
      expected_revision: 4, category: 'Học tập', note: null,
    }, 'support-action-03'));
    const pendingDeletion = await caught(api.putSupportNeedsV1('profile-02', {
      expected_revision: 4, category: 'Học tập', note: null,
    }, 'support-action-04'));
    const oversized = await caught(api.confirmStoryRunContextV1('run-01', {
      expected_context_revision: 1, context_snapshot_sha256: 'snapshot', confirmed: true,
      selected_context_entry_ids: ['00000000-0000-4000-8000-000000000001'],
    }, 'confirm-action-03'));

    expect(unavailable).toMatchObject({ code: 'SUPPORT_NEEDS_UNAVAILABLE', status: 503 });
    expect(missing).toMatchObject({ code: 'PROFILE_NOT_FOUND', status: 404 });
    expect(diagnosis).toBeInstanceOf(ParentApiError);
    expect(diagnosis).toMatchObject({ code: 'INVALID_REQUEST', fieldErrors: [{ field: 'category', code: 'DIAGNOSIS_LIKE' }] });
    expect((diagnosis as Error).message).not.toContain(hiddenText);
    expect(entryMissing).toMatchObject({ code: 'RESOURCE_NOT_FOUND', status: 404 });
    expect(runUnavailable).toMatchObject({ code: 'PARENT_STORY_RUN_STORE_UNAVAILABLE', status: 503 });
    expect(stale).toMatchObject({ code: 'STALE_REVISION', status: 409, currentVersion: 5 });
    expect(pendingDeletion).toMatchObject({ code: 'INVALID_STATE_TRANSITION', status: 409 });
    expect(oversized).toMatchObject({
      code: 'INVALID_REQUEST', fieldErrors: [{ field: 'selected_context_entry_ids', code: 'TOO_LONG' }],
    });
  });
});
