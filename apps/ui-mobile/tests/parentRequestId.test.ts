import { afterEach, describe, expect, it, vi } from 'vitest';
import { createRequestId } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://api.example.test' },
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Parent request ids', () => {
  it('stays unique within one millisecond and matches the allowed format', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1_763_500_000_000);

    const requestIds = Array.from({ length: 2_000 }, () => createRequestId());

    expect(new Set(requestIds).size).toBe(requestIds.length);
    for (const requestId of requestIds) {
      expect(requestId).toMatch(/^parent-[0-9a-z]+-[0-9a-z]{12}$/);
      expect(requestId).toMatch(/^[A-Za-z0-9._:-]{1,120}$/);
    }
  });
});
