import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort, ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';
import { readActivitySuggestionSetV1 } from '../src/parent/application/parentPhaseB';
import {
  isActivitySelectionPhaseAFallbackError,
  isActivitySuggestionFallbackError,
  isUncertainActivitySelectionError,
  retainedSuggestedActivitySelectionAction,
  ParentLearningUseCases,
} from '../src/parent/application/use-cases/ParentLearningUseCases';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://api.example.test' },
}));

type FetchResponse = { status: number; body: unknown };
type FetchCall = { url: string; init: RequestInit };

function createApi(responses: FetchResponse[]) {
  const calls: FetchCall[] = [];
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(input), init: init ?? {} });
    const response = responses.shift();
    if (!response) throw new Error('No synthetic response configured');
    return new Response(JSON.stringify(response.body), { status: response.status });
  });
  const auth: AuthTokenPort = { getIdToken: async () => 'synthetic-token' };
  return { api: new ParentApi(auth, fetcher as typeof fetch), calls, fetcher };
}

function requestBody(call: FetchCall): unknown {
  return JSON.parse(String(call.init.body));
}

function header(call: FetchCall, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

const suggestionSet = {
  contract: 'ParentActivitySuggestionSetV1',
  request_id: 'request-1',
  story_run_id: 'synthetic-run',
  suggestion_set_id: 'suggestion-set-1',
  set_revision: 1,
  understanding_revision: 2,
  selection_mode: 'AI_GENERATED_FALLBACK',
  catalog_candidate_count: 1,
  activities_snapshot_sha256: 'a'.repeat(64),
  review_required: true,
  modal_call_id: 'synthetic-modal-call',
  activities: [
    {
      title: 'Catalog activity', objective: 'Objective', materials_text: 'Materials', preparation_text: 'Preparation',
      instructions_text: 'Instructions', observation_notes: 'Observation', safety_notes: 'Safety', activity_kind: 'indoor',
      source: 'PUBLISHED_SHARED_LESSON', source_lesson_id: 'lesson-1', source_lesson_title: 'Lesson title',
      source_lesson_version_id: 'version-1', source_content_sha256: 'b'.repeat(64), source_activity_index: 0,
      match_reason: 'Catalog match',
    },
    {
      title: 'AI draft activity', objective: 'Objective', materials_text: 'Materials', preparation_text: 'Preparation',
      instructions_text: 'Instructions', observation_notes: 'Observation', safety_notes: 'Safety', activity_kind: 'mixed',
      source: 'AI_GENERATED_DRAFT', source_lesson_id: null, source_lesson_title: null,
      source_lesson_version_id: null, source_content_sha256: null, source_activity_index: null, match_reason: null,
    },
  ],
};

const selectionReceipt = {
  contract: 'ParentActivitySelectionReceiptV1', request_id: 'selection-request', story_run_id: 'synthetic-run',
  suggestion_set_id: 'suggestion-set-1', activity_selection_id: 'selection-1', selection_revision: 1,
  understanding_revision: 2, activity_index: 1, activity_snapshot_sha256: 'c'.repeat(64),
  persisted_at: '2026-11-25T00:00:00Z',
};

describe('Parent activity suggestion and selection routes', () => {
  it('sends the versioned suggestion request with an idempotency key and reads catalog plus AI cards', async () => {
    const { api, calls } = createApi([{ status: 200, body: suggestionSet }]);

    const response = await api.requestActivitySuggestionsV1('synthetic-run', 2, 'suggest-action-1');
    const parsed = readActivitySuggestionSetV1(response);

    expect(new URL(calls[0].url).pathname).toBe('/api/parent/v1/ai/story-runs/synthetic-run/activity-suggestions');
    expect(calls[0].init.method).toBe('POST');
    expect(requestBody(calls[0])).toEqual({ expected_understanding_revision: 2 });
    expect(header(calls[0], 'Idempotency-Key')).toBe('suggest-action-1');
    expect(parsed?.activities).toHaveLength(2);
    expect(parsed?.activities[1]).toMatchObject({ source: 'AI_GENERATED_DRAFT', source_lesson_id: null });
  });

  it('selects by suggestion set and activity index with the caller-retained key', async () => {
    const { api, calls } = createApi([{ status: 200, body: selectionReceipt }]);

    const receipt = await api.selectSuggestedActivityV1({
      storyRunId: 'synthetic-run', suggestionSetId: 'suggestion-set-1', revision: 2, activityIndex: 1,
      actionIdentity: 'select-action-1',
    });

    expect(new URL(calls[0].url).pathname).toBe('/api/parent/v1/ai/story-runs/synthetic-run/activity-selection');
    expect(requestBody(calls[0])).toEqual({
      suggestion_set_id: 'suggestion-set-1', expected_understanding_revision: 2, activity_index: 1,
    });
    expect(header(calls[0], 'Idempotency-Key')).toBe('select-action-1');
    expect(receipt).toEqual(selectionReceipt);
  });

  it('keeps lookup fallback broader than selection fallback and does not classify arbitrary TypeErrors as network failures', () => {
    const timeout = new ParentApplicationError('REQUEST_TIMEOUT', 'timeout', 'request-1', 408);
    const network = new ParentApplicationError('NETWORK_ERROR', 'offline');
    const missing = new ParentApplicationError('RESOURCE_NOT_FOUND', 'missing', 'request-2', 404);
    const unavailable = new ParentApplicationError('HTTP_503', 'unavailable', 'request-3', 503);

    expect(isActivitySuggestionFallbackError(timeout)).toBe(true);
    expect(isActivitySuggestionFallbackError(network)).toBe(true);
    expect(isActivitySuggestionFallbackError(missing)).toBe(true);
    expect(isActivitySuggestionFallbackError(new TypeError('programming error'))).toBe(false);
    expect(isActivitySelectionPhaseAFallbackError(missing)).toBe(true);
    expect(isActivitySelectionPhaseAFallbackError(unavailable)).toBe(true);
    expect(isActivitySelectionPhaseAFallbackError(timeout)).toBe(false);
    expect(isUncertainActivitySelectionError(timeout)).toBe(true);
    expect(isUncertainActivitySelectionError(network)).toBe(true);
  });

  it('retries an uncertain selection with the same key and body, then gives a different choice a new key', async () => {
    const calls: Array<{ body: Record<string, unknown>; key: string }> = [];
    const fakePort = {
      selectSuggestedActivityV1: vi.fn(async (input: Parameters<ParentApiPort['selectSuggestedActivityV1']>[0]) => {
        calls.push({
          body: {
            suggestion_set_id: input.suggestionSetId,
            expected_understanding_revision: input.revision,
            activity_index: input.activityIndex,
          },
          key: input.actionIdentity,
        });
        if (calls.length === 1) throw new ParentApplicationError('REQUEST_TIMEOUT', 'synthetic timeout', 'request-1', 408);
        return selectionReceipt;
      }),
    } as unknown as ParentApiPort;
    const learning = new ParentLearningUseCases(fakePort);
    const retainedActions = new Map<string, { signature: string; identity: string }>();
    const select = (activityIndex: number) => {
      const action = retainedSuggestedActivitySelectionAction(retainedActions, {
        runId: 'synthetic-run',
        suggestionSetId: 'suggestion-set-1',
        activityIndex,
        understandingRevision: 2,
      });
      return learning.selectSuggestedActivityV1({
        runId: 'synthetic-run',
        suggestionSetId: 'suggestion-set-1',
        revision: 2,
        activityIndex,
        actionIdentity: action.identity,
      });
    };

    await expect(select(1)).rejects.toMatchObject({ code: 'REQUEST_TIMEOUT' });
    await select(1);
    await select(2);

    expect(calls[0]).toEqual(calls[1]);
    expect(calls[1].key).toBe(calls[0].key);
    expect(calls[2].body).toEqual({
      suggestion_set_id: 'suggestion-set-1', expected_understanding_revision: 2, activity_index: 2,
    });
    expect(calls[2].key).not.toBe(calls[1].key);
  });
});
