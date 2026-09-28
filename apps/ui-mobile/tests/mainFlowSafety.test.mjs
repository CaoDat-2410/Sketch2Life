import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  acquireSingleFlight,
  FEEDBACK_OBSERVATIONS,
  normalizeSupportedImage,
  prepareNarration,
  releaseSingleFlight,
} from '../src/context/workflowSafety.ts';

describe('main-flow synchronous request guard', () => {
  it('allows one in-flight request and releases for a later retry', () => {
    const lock = { current: false };
    expect(acquireSingleFlight(lock)).toBe(true);
    expect(acquireSingleFlight(lock)).toBe(false);
    releaseSingleFlight(lock);
    expect(acquireSingleFlight(lock)).toBe(true);
  });
});

describe('drawing upload metadata', () => {
  it.each([
    ['art.png', 'image/png', { fileName: 'art.png', mimeType: 'image/png' }],
    ['art.JPG', 'image/jpeg', { fileName: 'art.JPG', mimeType: 'image/jpeg' }],
    ['drawing', 'image/png', { fileName: 'drawing.png', mimeType: 'image/png' }],
    [null, 'image/jpeg', { fileName: 'drawing.jpg', mimeType: 'image/jpeg' }],
  ])('normalizes supported image metadata', (fileName, mimeType, expected) => {
    expect(normalizeSupportedImage(fileName, mimeType)).toEqual(expected);
  });

  it.each([
    ['art.heic', 'image/heic'],
    ['art.webp', 'image/webp'],
    ['art.png', 'image/jpeg'],
    ['art.jpg', 'image/png'],
    ['art.bin', 'application/octet-stream'],
    [null, null],
  ])('fails closed for unsupported or conflicting metadata', (fileName, mimeType) => {
    expect(normalizeSupportedImage(fileName, mimeType)).toBeNull();
  });
});

describe('narration preflight', () => {
  it('keeps invalid input outside the request lock and supports a corrected retry', () => {
    const lock = { current: false };
    const invalid = prepareNarration('text', '   ', null);
    expect(invalid).toMatchObject({ ok: false });
    expect(lock.current).toBe(false);

    const corrected = prepareNarration('text', '  Con bướm bay  ', null);
    expect(corrected).toEqual({
      ok: true,
      narration: { kind: 'TEXT', text: 'Con bướm bay', language: 'vi', provenance: 'TEXT_TYPED' },
    });
    expect(acquireSingleFlight(lock)).toBe(true);
  });

  it('requires uploaded audio metadata before creating an audio request', () => {
    expect(prepareNarration('audio', '', null)).toMatchObject({ ok: false });
    expect(prepareNarration('audio', '', {
      artifactRef: 'artifact-a', sha256: 'a'.repeat(64), byteLength: 1,
    })).toMatchObject({
      ok: true,
      narration: { kind: 'AUDIO', artifact_ref: 'artifact-a', byte_length: 1 },
    });
  });
});

describe('feedback contract mapping and workflow integration', () => {
  it('uses exactly the observation values accepted by FeedbackV1', () => {
    expect(FEEDBACK_OBSERVATIONS.map((item) => item.code).sort()).toEqual([
      'ASKED_FOR_HELP',
      'CHANGED_APPROACH',
      'COMPLETED_STEPS',
      'STARTED_INDEPENDENTLY',
      'STOPPED_EARLY',
    ]);
    expect(new Set(FEEDBACK_OBSERVATIONS.map((item) => item.code)).size).toBe(FEEDBACK_OBSERVATIONS.length);
  });

  it('clears stale session inputs and keeps ordinary gated screens protected', () => {
    const root = resolve(process.cwd(), '../../');
    const context = readFileSync(resolve(root, 'apps/ui-mobile/src/context/AppContext.tsx'), 'utf8');
    const screens = readFileSync(resolve(root, 'apps/ui-mobile/src/screens/Flow2Screens.tsx'), 'utf8');
    const shell = readFileSync(resolve(root, 'apps/ui-mobile/BaoApp.tsx'), 'utf8');
    expect(context).toContain("setCorrection('')");
    expect(context).toContain('setDirectionRequeryUsed(false)');
    expect(context).toContain('setSelectedObservationTags([])');
    expect(context).toContain('releaseSingleFlight(sessionMutationLockRef)');
    expect(screens).toContain("['UNDERSTANDING_PROPOSED', 'GATE_B_PENDING'");
    expect(screens).toContain("!['HANDOFF_READY', 'FEEDBACK_RECORDED'].includes(sessionState)");
    expect(screens).not.toContain('setParentNotes');
    expect(screens).toContain('rendererPreparationAttempted.current');
    expect(screens).toContain('retryRendererPreparation');
    expect(shell).toContain('Đóng thông báo lỗi');
    expect(shell).not.toContain('Đóng thông báo và thử lại');
  });

  it('serializes each session mutation and validates narration before locking', () => {
    const root = resolve(process.cwd(), '../../');
    const context = readFileSync(resolve(root, 'apps/ui-mobile/src/context/AppContext.tsx'), 'utf8');
    const names = [
      'beginWorkflow',
      'uploadNarration',
      'uploadDrawing',
      'runAiSimulation',
      'selectSubject',
      'confirmGateA',
      'prepareActivityWorkflow',
      'approveActivity',
      'prepareRendererIntro',
      'completeActivityHandoff',
      'saveFeedback',
    ];
    for (const name of names) {
      const start = context.indexOf(`const ${name} = async`);
      const end = context.indexOf('\n  const ', start + 1);
      const body = context.slice(start, end < 0 ? undefined : end);
      expect(body, `${name} must use the shared synchronous request guard`)
        .toContain('acquireSingleFlight(sessionMutationLockRef)');
      expect(body, `${name} must release the request guard`)
        .toContain('releaseSingleFlight(sessionMutationLockRef)');
    }
    const understanding = context.slice(
      context.indexOf('const runAiSimulation = async'),
      context.indexOf('\n  const selectSubject =', context.indexOf('const runAiSimulation = async')),
    );
    expect(understanding.indexOf('prepareNarration')).toBeLessThan(understanding.indexOf('acquireSingleFlight'));
  });

  it('keeps image picking mutually exclusive with uploads and has one recording clock', () => {
    const root = resolve(process.cwd(), '../../');
    const context = readFileSync(resolve(root, 'apps/ui-mobile/src/context/AppContext.tsx'), 'utf8');
    const voiceScreens = readFileSync(resolve(root, 'apps/ui-mobile/src/screens/Flow1Screens.tsx'), 'utf8');
    const voiceScreen = voiceScreens.slice(
      voiceScreens.indexOf('export const VoiceScreen'),
      voiceScreens.indexOf('const styles = StyleSheet.create', voiceScreens.indexOf('export const VoiceScreen')),
    );
    expect(context).toContain('imagePickerLockRef.current || !acquireSingleFlight(sessionMutationLockRef)');
    expect(context).toContain('imagePickerLockRef.current = true');
    expect(voiceScreen).not.toContain('setInterval(');
    expect(context).toContain('Math.min(180, recordingElapsedSecondsRef.current + 1)');
    expect(context).toContain('clearRecordingTimer();');
  });
});
