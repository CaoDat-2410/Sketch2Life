import {describe, expect, it} from 'vitest';

import {sha256Hex, sha256HexPortable} from '../src/sha256';

const encoder = new TextEncoder();

describe('portable renderer package SHA-256', () => {
  it.each([
    ['', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
    ['abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
    [
      'The quick brown fox jumps over the lazy dog',
      'd7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592',
    ],
  ])('matches the SHA-256 vector for %j', (input, expected) => {
    expect(sha256HexPortable(encoder.encode(input))).toBe(expected);
  });

  it('keeps the asynchronous integrity API available to the renderer', async () => {
    const bytes = encoder.encode('Sketch2Life renderer package');
    expect(await sha256Hex(bytes.buffer as ArrayBuffer)).toBe(sha256HexPortable(bytes));
  });
});
