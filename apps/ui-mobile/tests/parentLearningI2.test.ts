import { describe, expect, it, vi } from 'vitest';
import type { ParentActionIdentity, ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import { ParentLearningUseCases } from '../src/parent/application/use-cases/ParentLearningUseCases';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';
import type { ParentStoryRunCreateV1, ParentStoryRunV1, ParentStoryContextConfirmationV1 } from '../src/parent/domain/types';

const storyRun: ParentStoryRunV1 = {
  run_id: 'synthetic-run',
  run_state: 'CONTEXT_PENDING',
  parent_profile_id: 'synthetic-profile',
  context_revision: 4,
  context_snapshot: { topic: 'mây', adult_confirmed_idea: 'vẽ một chiếc diều' },
  context_snapshot_sha256: 'synthetic-context-hash',
  lesson_pin_snapshot: { lesson_id: 'lesson-1', version_id: 'version-3', content_sha256: 'lesson-hash' },
};

function createUseCases() {
  const api = {
    createStoryRunV1: vi.fn(async (_input: ParentStoryRunCreateV1, _identity: ParentActionIdentity) => ({ request_id: 'request-1', story_run: storyRun })),
    confirmStoryRunContextV1: vi.fn(async (_runId: string, _input: ParentStoryContextConfirmationV1, _identity: ParentActionIdentity) => ({ request_id: 'request-2', story_run: storyRun })),
  };
  return { api, useCases: new ParentLearningUseCases(api as unknown as ParentApiPort) };
}

describe('ParentLearningUseCases I2 pre-drawing flow', () => {
  it('requires a lesson pin and creates a run without image or legacy consent/context fields', async () => {
    const { api, useCases } = createUseCases();
    const lessonPin = { lesson_id: 'lesson-1', version_id: 'version-3', content_sha256: 'lesson-hash' };

    const result = await useCases.createRunBeforeDrawingV1({
      profileId: 'synthetic-profile',
      topic: '  mây  ',
      adultIdea: '  vẽ một chiếc diều  ',
      lessonPin,
      actionIdentity: 'story-action-1',
    });

    expect(api.createStoryRunV1).toHaveBeenCalledWith({
      parent_profile_id: 'synthetic-profile',
      topic: 'mây',
      adult_confirmed_idea: 'vẽ một chiếc diều',
      lesson_version: lessonPin,
    }, 'story-action-1');
    const request = api.createStoryRunV1.mock.calls[0][0];
    expect(request).not.toHaveProperty('photo');
    expect(request).not.toHaveProperty('consent_policy_version');
    expect(request).not.toHaveProperty('expected_profile_revision_id');
    expect(request).not.toHaveProperty('context_confirmed');
    expect(result.story_run).toBe(storyRun);
  });

  it('does not begin a run without a complete selected lesson pin', async () => {
    const { api, useCases } = createUseCases();
    const invalidPins = [
      null,
      { lesson_id: 'lesson-1', version_id: 'version-3', content_sha256: ' ' },
    ];

    for (const lessonPin of invalidPins) {
      const invalid = {
        profileId: 'synthetic-profile', topic: 'mây', adultIdea: 'diều', lessonPin, actionIdentity: 'story-action',
      } as unknown as Parameters<typeof useCases.createRunBeforeDrawingV1>[0];
      await expect(useCases.createRunBeforeDrawingV1(invalid)).rejects.toThrow('Hãy chọn bài học trước khi bắt đầu.');
    }
    expect(api.createStoryRunV1).not.toHaveBeenCalled();
  });

  it('confirms the server-returned context snapshot and preserves the same action identity on retry', async () => {
    const { api, useCases } = createUseCases();

    await useCases.confirmRunContextV1(storyRun, 'context-action-1');
    await useCases.confirmRunContextV1(storyRun, 'context-action-1');

    expect(api.confirmStoryRunContextV1).toHaveBeenNthCalledWith(1, 'synthetic-run', {
      expected_context_revision: 4,
      context_snapshot_sha256: 'synthetic-context-hash',
      confirmed: true,
    }, 'context-action-1');
    expect(api.confirmStoryRunContextV1).toHaveBeenNthCalledWith(2, 'synthetic-run', {
      expected_context_revision: 4,
      context_snapshot_sha256: 'synthetic-context-hash',
      confirmed: true,
    }, 'context-action-1');
  });

  it('recovers ACTIVE_RUN_EXISTS with one active-run read and does not retry creation', async () => {
    const api = {
      createStoryRunV1: vi.fn(async () => { throw new ParentApplicationError('ACTIVE_RUN_EXISTS', 'A run is already active.', 'request-1', 409); }),
      getActiveStoryRunV1: vi.fn(async () => ({ request_id: 'active-request', story_run: storyRun })),
    };
    const useCases = new ParentLearningUseCases(api as unknown as ParentApiPort);

    const result = await useCases.createRunBeforeDrawingV1({
      profileId: 'synthetic-profile', topic: 'mây', adultIdea: 'diều',
      lessonPin: { lesson_id: 'lesson-1', version_id: 'version-3', content_sha256: 'lesson-hash' },
      actionIdentity: 'story-action-once',
    });

    expect(api.createStoryRunV1).toHaveBeenCalledTimes(1);
    expect(api.getActiveStoryRunV1).toHaveBeenCalledTimes(1);
    expect(result.story_run).toBe(storyRun);
  });

  it('rethrows ACTIVE_RUN_EXISTS when the active-run endpoint returns null', async () => {
    const conflict = new ParentApplicationError('ACTIVE_RUN_EXISTS', 'A run is already active.', 'request-1', 409);
    const api = {
      createStoryRunV1: vi.fn(async () => { throw conflict; }),
      getActiveStoryRunV1: vi.fn(async () => ({ story_run: null })),
    };
    const useCases = new ParentLearningUseCases(api as unknown as ParentApiPort);

    await expect(useCases.createRunBeforeDrawingV1({
      profileId: 'synthetic-profile', topic: 'mây', adultIdea: 'diều',
      lessonPin: { lesson_id: 'lesson-1', version_id: 'version-3', content_sha256: 'lesson-hash' },
      actionIdentity: 'story-action-once',
    })).rejects.toBe(conflict);

    expect(api.createStoryRunV1).toHaveBeenCalledTimes(1);
    expect(api.getActiveStoryRunV1).toHaveBeenCalledTimes(1);
  });
});
