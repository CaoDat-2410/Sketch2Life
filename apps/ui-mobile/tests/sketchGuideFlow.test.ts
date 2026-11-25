import { describe, expect, it } from 'vitest';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';
import {
  sketchGuideFailureMessage,
  sketchGuideRequestSubject,
} from '../src/parent/presentation/navigation/sketchGuideFlow';

describe('sketch guide flow', () => {
  it('looks the guide up by the adult idea when present, otherwise by topic only', () => {
    expect(sketchGuideRequestSubject('  con bướm ')).toBe('con bướm');
    expect(sketchGuideRequestSubject('   ')).toBeUndefined();
  });

  it('tells the adult when no reviewed sample exists for the subject', () => {
    const notFound = new ParentApplicationError('RESOURCE_NOT_FOUND', 'x', undefined, 404);
    expect(sketchGuideFailureMessage(notFound)).toContain('Chưa có mẫu nét vẽ');
  });

  it('keeps a retryable message for any other failure', () => {
    const down = new ParentApplicationError('PROVIDER_UNAVAILABLE', 'x', undefined, 503);
    expect(sketchGuideFailureMessage(down)).toContain('thử lại');
    expect(sketchGuideFailureMessage(new Error('network'))).toContain('thử lại');
  });
});
