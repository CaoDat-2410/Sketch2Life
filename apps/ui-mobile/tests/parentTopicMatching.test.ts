import { describe, expect, it } from 'vitest';
import { isResolvedTopicConsistent, normalizeTopicLabel } from '../src/parent/domain/topicMatching';
import { readErrorCode } from '../src/parent/presentation/navigation/parentFlowV1';

describe('normalizeTopicLabel', () => {
  it('matches Vietnamese labels when accents, case, or spacing differ', () => {
    expect(normalizeTopicLabel('Dong vat')).toBe(normalizeTopicLabel('Động vật'));
    expect(normalizeTopicLabel('  THẾ   GIỚI CỔ TÍCH ')).toBe(normalizeTopicLabel('thế giới cổ tích'));
  });

  it('keeps distinct topics distinct', () => {
    expect(normalizeTopicLabel('Động vật')).not.toBe(normalizeTopicLabel('Thiên nhiên'));
  });

  it('accepts a backend-canonicalized custom topic and strictly checks selected catalog topics', () => {
    expect(isResolvedTopicConsistent({
      selectedTopicId: 'custom', selectedTopic: 'Dong vat',
      resolvedTopicId: 'animals', resolvedTopic: 'Động vật',
    })).toBe(true);
    expect(isResolvedTopicConsistent({
      selectedTopicId: 'animals', selectedTopic: 'Động vật',
      resolvedTopicId: 'animals', resolvedTopic: 'Dong vat',
    })).toBe(true);
    expect(isResolvedTopicConsistent({
      selectedTopicId: 'animals', selectedTopic: 'Động vật',
      resolvedTopicId: 'nature', resolvedTopic: 'Thiên nhiên',
    })).toBe(false);
    expect(isResolvedTopicConsistent({
      selectedTopicId: 'custom', selectedTopic: 'Dong vat',
      resolvedTopicId: '', resolvedTopic: '',
    })).toBe(false);
  });

  it('reads safe topic error codes structurally from plain API errors', () => {
    expect(readErrorCode({ code: 'PARENT_SUBJECT_SUGGESTION_INVALID' })).toBe('PARENT_SUBJECT_SUGGESTION_INVALID');
    expect(readErrorCode({ code: 'not-a-safe-code' })).toBeNull();
  });
});
