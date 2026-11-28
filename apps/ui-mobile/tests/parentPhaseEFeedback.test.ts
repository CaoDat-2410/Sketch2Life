import { describe, expect, it, vi } from 'vitest';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

function reply(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function feedback(overrides: Record<string, unknown> = {}) {
  return {
    contract: 'ParentLessonFeedbackV1',
    feedback_id: 'feedback-1',
    lesson_id: 'lesson-1',
    version_id: 'version-1',
    revision: 1,
    feedback_text: 'A useful note',
    created_at: '2026-11-25T00:00:00Z',
    updated_at: '2026-11-25T00:00:00Z',
    reply_count: 1,
    ...overrides,
  };
}

type Call = { url: string; init: RequestInit };

function apiWith(replies: Response[]) {
  const calls: Call[] = [];
  const queue = [...replies];
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return queue.shift() ?? reply(500, {});
  }) as unknown as typeof fetch;
  const api = new ParentApi({ getIdToken: vi.fn(async () => 'parent-token') }, fetcher, 'https://parent.example.test');
  return { api, calls, fetcher };
}

function headerOf(call: Call, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

describe('Phase E Parent lesson feedback', () => {
  it('submits by lesson with an idempotency key and reads the thread and paged replies', async () => {
    const thread = { contract: 'ParentLessonFeedbackStateV1', lesson_id: 'lesson/one', feedback: feedback({ lesson_id: 'lesson/one' }) };
    const replies = {
      contract: 'ParentLessonFeedbackReplyPageV1',
      feedback_id: 'feedback-1',
      items: [{ reply_id: 'reply-1', reply_text: 'Thank you', created_at: '2026-11-25T01:00:00Z' }],
      next_cursor: 'reply-cursor',
    };
    const { api, calls } = apiWith([reply(201, feedback({ lesson_id: 'lesson/one', feedback_text: 'A note' })), reply(200, thread), reply(200, replies)]);

    await api.submitLessonFeedback('lesson/one', '  A note  ', 'feedback-key-1');
    const state = await api.getParentLessonFeedback('lesson/one');
    const page = await api.listParentLessonFeedbackReplies('lesson/one', 50, 'reply-cursor');

    expect(calls[0].url).toBe('https://parent.example.test/api/lesson-library/v1/me/lessons/lesson%2Fone/feedback');
    expect(calls[0].init.method).toBe('POST');
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ feedback_text: 'A note' });
    expect(headerOf(calls[0], 'Idempotency-Key')).toBe('feedback-key-1');
    expect(calls[1].url).toBe('https://parent.example.test/api/lesson-library/v1/me/lessons/lesson%2Fone/feedback');
    expect(calls[1].init.method).toBe('GET');
    expect(calls[2].url).toBe('https://parent.example.test/api/lesson-library/v1/me/lessons/lesson%2Fone/feedback/replies?limit=50&cursor=reply-cursor');
    expect(state.feedback?.feedback_text).toBe('A useful note');
    expect(page.items[0].reply_text).toBe('Thank you');
  });

  it('enforces the trimmed code point limit before sending', async () => {
    const { api, fetcher } = apiWith([]);
    const error = await api.submitLessonFeedback('lesson-1', '🙂'.repeat(1201), 'feedback-key-1')
      .catch((failure: unknown) => failure);
    expect(error).toBeInstanceOf(ParentApiError);
    expect(error).toMatchObject({ code: 'INVALID_REQUEST', status: 400 });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('rejects malformed runtime feedback and retains uniform 404 status', async () => {
    const { api: malformedApi } = apiWith([reply(201, feedback({ reply_count: -1 }))]);
    const malformed = await malformedApi.submitLessonFeedback('lesson-1', 'A note', 'feedback-key-1')
      .catch((failure: unknown) => failure);
    expect(malformed).toMatchObject({ code: 'INVALID_API_RESPONSE', status: 200 });

    const { api: missingApi } = apiWith([reply(404, { code: 'LESSON_NOT_FOUND', message: 'hidden lesson detail' })]);
    const missing = await missingApi.getParentLessonFeedback('lesson-1').catch((failure: unknown) => failure);
    expect(missing).toMatchObject({ code: 'LESSON_NOT_FOUND', status: 404 });
    expect((missing as Error).message).not.toContain('hidden lesson detail');
  });
});
