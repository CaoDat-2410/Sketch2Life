import {describe, expect, it} from 'vitest';

import {normalizeRendererFailureCode, RENDERER_FAILURE_CODES} from '../src/failureDiagnostics';

describe('renderer failure diagnostics', () => {
  it('preserves allowlisted safe codes for native diagnostics', () => {
    for (const code of RENDERER_FAILURE_CODES) {
      expect(normalizeRendererFailureCode(code)).toBe(code);
    }
  });

  it('does not leak exception messages, payloads, or arbitrary event reasons', () => {
    expect(normalizeRendererFailureCode(new Error('MASK_DIMENSIONS_MISMATCH'))).toBe('MASK_DIMENSIONS_MISMATCH');
    expect(normalizeRendererFailureCode('https://example.test/?token=secret')).toBe('RENDERER_V2_START_FAILED');
    expect(normalizeRendererFailureCode('UNLISTED_INTERNAL_DETAIL')).toBe('RENDERER_V2_START_FAILED');
    expect(normalizeRendererFailureCode({reason: 'MASK_DIMENSIONS_MISMATCH'})).toBe('RENDERER_V2_START_FAILED');
  });
});
