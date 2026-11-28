import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

import { ParentLessonUseCases } from '../src/parent/application/use-cases/ParentLessonUseCases';
import type { ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import type { LessonExportV1, ParentLessonListOptions } from '../src/parent/domain/types';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import {
  parentLessonExportFailureMessage,
  parentLessonExportSaveFailureMessage,
  safeParentFlowErrorMessage,
  safeParentGroupInvitationErrorMessage,
} from '../src/parent/presentation/navigation/parentFlowV1';
import { mergeLessonSummaryPages, updateLessonSearchState } from '../src/parent/presentation/navigation/workflowTypes';

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
  const api = new ParentApi({ getIdToken: vi.fn(async () => 'parent-token') }, fetcher, 'https://parent.example.test');
  return { api, calls };
}

function headerOf(call: Call, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

function lessonExport(lessonId = 'lesson-1'): LessonExportV1 {
  return {
    contract: 'LessonExportV1',
    lesson_id: lessonId,
    version_id: 'version-1',
    version_no: 3,
    content_sha256: 'a'.repeat(64),
    title: 'Khám phá con cá',
    topic: 'Đại dương',
    locale: 'vi-VN',
    target_age_band_ref: 'age-band:3-5',
    target_age_band_version: 1,
    objectives: ['Nhận biết hình dáng con cá'],
    drawing_subject: 'Con cá',
    drawing_steps_text: 'Vẽ thân cá rồi thêm vây.',
    subject_learning_notes: 'Cùng bé kể về nơi cá sống.',
    script_direction: null,
    script_following_allowed: false,
    activities: [],
    access_source: 'PUBLIC',
    access_expires_at: null,
  };
}

describe('GAP-10 Parent lesson export API', () => {
  it('downloads and validates a JSON export from the requested lesson path', async () => {
    const lessonId = 'lesson 1';
    const { api, calls } = apiWith([reply(200, lessonExport(lessonId))]);
    const result = await api.downloadLesson(lessonId);
    const url = new URL(calls[0].url);

    expect(result).toMatchObject({ contract: 'LessonExportV1', lesson_id: lessonId, locale: 'vi-VN' });
    expect(url.pathname).toBe('/api/lesson-library/v1/me/lessons/lesson%201/download');
    expect(url.search).toBe('');
    expect(calls[0].init.method).toBe('GET');
    expect(calls[0].init.body).toBeUndefined();
    expect(headerOf(calls[0], 'Authorization')).toBe('Bearer parent-token');
    expect(headerOf(calls[0], 'Idempotency-Key')).toBeNull();
  });

  it('maps missing or ungranted lesson downloads to the safe 404 message', async () => {
    const { api } = apiWith([reply(404, { detail: { code: 'LESSON_NOT_FOUND', message: 'private detail' } })]);
    const error = await api.downloadLesson('lesson-1').catch((cause: unknown) => cause);
    expect(error).toMatchObject({ code: 'LESSON_NOT_FOUND', status: 404 });
    expect(parentLessonExportFailureMessage(error)).toBe('Bài học không cho phép tải về hoặc không còn khả dụng.');
  });

  it('keeps the shared missing-lesson message neutral outside the download call', () => {
    expect(new ParentApiError('LESSON_NOT_FOUND', 'request-1', 404).message)
      .toBe('Không tìm thấy bài học này hoặc bài học không còn khả dụng.');
  });

  it('uses safe messages for denied and unavailable export requests and cancelled saves', () => {
    expect(parentLessonExportFailureMessage({ code: 'ACCOUNT_SCOPE_UNAVAILABLE', status: 403 }))
      .toBe('Tài khoản phụ huynh chưa thể tải bài học này.');
    expect(parentLessonExportFailureMessage({ code: 'DEPENDENCY_UNAVAILABLE', status: 503 }))
      .toBe('Chưa thể tải bài học lúc này. Hãy thử lại sau.');
    expect(parentLessonExportSaveFailureMessage('cancelled')).toBe('Đã hủy lưu tệp.');
  });

  it('rejects a response whose lesson id does not match the requested id', async () => {
    const { api } = apiWith([reply(200, lessonExport('another-lesson'))]);
    await expect(api.downloadLesson('lesson-1')).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE', status: 200 });
  });

  it('exposes lesson download through the lesson use case', async () => {
    const download = vi.fn(async () => lessonExport('lesson-1'));
    const useCases = new ParentLessonUseCases({ downloadLesson: download } as unknown as ParentApiPort);
    await useCases.download('lesson-1');
    expect(download).toHaveBeenCalledWith('lesson-1');
  });
});

const membership = (state: 'ACTIVE' | 'DECLINED' = 'ACTIVE') => ({
  contract: 'ParentGroupMembershipV1',
  membership_id: 'member-1',
  parent_group_id: 'group-1',
  state,
  invited_at: '2026-11-20T10:00:00Z',
  expires_at: null,
  accepted_at: state === 'ACTIVE' ? '2026-11-21T10:00:00Z' : null,
  revision: state === 'ACTIVE' ? 2 : 3,
  revision_source: 'PARENT_ACTION',
});

describe('T-10a lesson filters and cursor paging', () => {
  it('trims filters, sends the age-band pair, and preserves an opaque cursor', async () => {
    const { api, calls } = apiWith([reply(200, { contract: 'ParentLessonPageV1', items: [], next_cursor: 'next/page' })]);
    await api.listLessons({
      source: 'SHARED',
      limit: 100,
      cursor: 'opaque / cursor',
      q: '  butterflies  ',
      topic: '  Nature  ',
      ageBand: { ref: ' age-band:v2 ', version: 2 },
    });
    const url = new URL(calls[0].url);
    expect(url.pathname).toBe('/api/lesson-library/v1/me/lessons');
    expect(Object.fromEntries(url.searchParams)).toEqual({
      source: 'SHARED',
      limit: '100',
      cursor: 'opaque / cursor',
      q: 'butterflies',
      topic: 'Nature',
      target_age_band_ref: 'age-band:v2',
      target_age_band_version: '2',
    });
    expect(calls[0].init.method).toBe('GET');
    expect(calls[0].init.body).toBeUndefined();
  });

  it('defaults to ALL and 25, and omits a blank search value', async () => {
    const { api, calls } = apiWith([reply(200, { contract: 'ParentLessonPageV1', items: [], next_cursor: null })]);
    await api.listLessons({ q: '   ', topic: '  ' });
    const url = new URL(calls[0].url);
    expect(url.searchParams.get('source')).toBe('ALL');
    expect(url.searchParams.get('limit')).toBe('25');
    expect(url.searchParams.has('q')).toBe(false);
    expect(url.searchParams.has('topic')).toBe(false);
  });

  it('rejects incomplete age-band pairs, invalid filters, cursors, and limits before fetch', () => {
    const { api, calls } = apiWith([]);
    const invalid: ParentLessonListOptions[] = [
      { ageBand: { ref: 'age-band:v1' } as unknown as { ref: string; version: number } },
      { ageBand: { ref: 'age band', version: 1 } },
      { ageBand: { ref: 'age-band:v1', version: 0 } },
      { q: 'x'.repeat(101) },
      { topic: 'x'.repeat(121) },
      { q: 'two\nlines' },
      { cursor: 'c'.repeat(1025) },
      { limit: 0 },
      { limit: 101 },
    ];
    for (const options of invalid) expect(() => api.listLessons(options)).toThrow(ParentApiError);
    expect(calls).toHaveLength(0);
  });

  it('resets the cursor when any search filter changes and merges duplicate page items once', () => {
    const state = updateLessonSearchState(
      { filters: { source: 'ALL', q: 'leaf', topic: '' }, cursor: 'opaque-next' },
      { source: 'ALL', q: 'leaf', topic: 'garden' },
    );
    expect(state.changed).toBe(true);
    expect(state.cursor).toBeNull();
    expect(updateLessonSearchState({ filters: state.filters, cursor: 'opaque-same-filter' }, state.filters).cursor).toBe('opaque-same-filter');
    const first = { lesson_id: 'lesson-1', version_id: 'v1' } as never;
    const second = { lesson_id: 'lesson-2', version_id: 'v1' } as never;
    expect(mergeLessonSummaryPages([first], [first, second])).toEqual([first, second]);
  });
});

describe('T-10c group decline and own memberships', () => {
  it('POSTs decline with one visible ASCII key, no body, and accepts only DECLINED', async () => {
    const { api, calls } = apiWith([reply(200, membership('DECLINED'), { ETag: '"3"' })]);
    const result = await api.declineParentGroupInvitation('member-1', 'decline-action-1');
    expect(result).toMatchObject({ membership_id: 'member-1', state: 'DECLINED', accepted_at: null });
    expect(calls[0].url).toBe('https://parent.example.test/api/lesson-library/v1/me/parent-group-invitations/member-1/decline');
    expect(calls[0].init.method).toBe('POST');
    expect(headerOf(calls[0], 'Idempotency-Key')).toBe('decline-action-1');
    expect(headerOf(calls[0], 'Content-Type')).toBeNull();
    expect(calls[0].init.body).toBeUndefined();
  });

  it('maps invitation expiry safely and retains current_version only for stale revision', async () => {
    const expired = apiWith([reply(409, { code: 'INVITATION_EXPIRED', current_version: 8 })]);
    const error = await expired.api.declineParentGroupInvitation('member-1', 'key-1').catch((cause: unknown) => cause);
    expect(error).toMatchObject({ code: 'INVITATION_EXPIRED', status: 409 });
    expect((error as ParentApiError).currentVersion).toBeUndefined();
    expect(safeParentFlowErrorMessage(error)).toContain('Lời mời đã hết hạn');

    const stale = apiWith([reply(409, { code: 'STALE_REVISION', current_version: 9 })]);
    const staleError = await stale.api.declineParentGroupInvitation('member-1', 'key-2').catch((cause: unknown) => cause);
    expect(staleError).toMatchObject({ code: 'STALE_REVISION', status: 409, currentVersion: 9 });
    expect(safeParentGroupInvitationErrorMessage(staleError)).toContain('Lời mời nhóm đã thay đổi');
  });

  it('lists only validated active memberships with an opaque cursor', async () => {
    const { api, calls } = apiWith([reply(200, { contract: 'ParentGroupMembershipPageV1', items: [membership()], next_cursor: 'next-cursor' })]);
    const page = await api.listParentGroupMemberships('opaque/cursor');
    expect(page.items).toMatchObject([{ membership_id: 'member-1', state: 'ACTIVE' }]);
    const url = new URL(calls[0].url);
    expect(url.pathname).toBe('/api/lesson-library/v1/me/parent-group-memberships');
    expect(url.searchParams.get('limit')).toBe('25');
    expect(url.searchParams.get('cursor')).toBe('opaque/cursor');
    expect(calls[0].init.method).toBe('GET');
  });

  it('preserves organization_id on current rows and accepts older rows without it', async () => {
    const current = { ...membership(), organization_id: 'organization-1' };
    const older = membership();
    const { api } = apiWith([reply(200, {
      contract: 'ParentGroupMembershipPageV1',
      items: [current, older],
      next_cursor: null,
    })]);

    const page = await api.listParentGroupMemberships();

    expect(page.items.map((item) => item.organization_id)).toEqual(['organization-1', undefined]);
  });

  it('passes the same action key through the lesson use case', async () => {
    const decline = vi.fn(async () => membership('DECLINED'));
    const useCases = new ParentLessonUseCases({ declineParentGroupInvitation: decline } as unknown as ParentApiPort);
    await useCases.declineGroupInvitation('member-1', 'same-key-on-retry');
    expect(decline).toHaveBeenCalledWith('member-1', 'same-key-on-retry');
  });
});

describe('T-8b push endpoints stay fail-closed in the UI', () => {
  it('POSTs the strict registration body and DELETEs with If-Match and idempotency key', async () => {
    const { api, calls } = apiWith([
      reply(201, { contract: 'PushEndpointRegistrationResultV1', endpoint_id: 'endpoint-1', version: 4 }, { ETag: '"4"' }),
      reply(204),
    ]);
    const input = {
      contract: 'PushEndpointRegistrationV1',
      platform_kind: 'ANDROID',
      provider_kind: 'ANDROID_PUSH',
      encrypted_registration_proof: 'opaque-proof',
      app_version: '4.2.0',
    } as const;
    await api.registerPushEndpointV1(input, 'register-key');
    await api.deletePushEndpointV1('endpoint-1', 4, 'delete-key');
    expect(calls[0].url).toBe('https://parent.example.test/v1/notifications/push-endpoints');
    expect(calls[0].init.method).toBe('POST');
    expect(JSON.parse(String(calls[0].init.body))).toEqual(input);
    expect(headerOf(calls[0], 'Idempotency-Key')).toBe('register-key');
    expect(calls[1].url).toBe('https://parent.example.test/v1/notifications/push-endpoints/endpoint-1');
    expect(calls[1].init.method).toBe('DELETE');
    expect(headerOf(calls[1], 'If-Match')).toBe('"4"');
    expect(headerOf(calls[1], 'Idempotency-Key')).toBe('delete-key');
    expect(calls[1].init.body).toBeUndefined();
  });

  it('shows a static Android notice and never calls registration from notification UI', () => {
    const screen = readFileSync(new URL('../src/parent/presentation/screens/NotificationsScreen.tsx', import.meta.url), 'utf8');
    const app = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    const row = screen.match(/<View accessibilityRole="summary" style=\{styles\.pushSupportNotice\}>([\s\S]*?)<\/View>/)?.[1] ?? '';
    expect(row).toContain('Thông báo đẩy chưa hỗ trợ trên Android. Bạn vẫn nhận thông báo trong hộp thư của ứng dụng.');
    expect(row).not.toMatch(/Pressable|onPress/);
    expect(screen).not.toContain('registerPushEndpointV1(');
    expect(app).not.toContain('registerPushEndpointV1(');
  });
});

describe('safe Phase C copy', () => {
  it('never exposes raw invitation, scope, provider, or push error codes', () => {
    for (const [code, status] of [
      ['INVITATION_EXPIRED', 409],
      ['STALE_REVISION', 409],
      ['ACCOUNT_SCOPE_UNAVAILABLE', 403],
      ['PROVIDER_UNAVAILABLE', 503],
      ['PUSH_PLATFORM_UNSUPPORTED', 422],
      ['PUSH_REGISTRATION_UNAVAILABLE', 503],
    ] as const) {
      const message = safeParentFlowErrorMessage(new ParentApiError(code, 'request-1', status));
      expect(message).not.toContain(code);
      expect(message.length).toBeGreaterThan(0);
    }
  });
});
