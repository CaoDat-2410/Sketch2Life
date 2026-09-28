import {describe, expect, it} from 'vitest';

import {
  createSubjectCutoutLayers,
  matchesDerivedMaskProvenance,
  requireVerifiedCutoutMask,
} from '../src/subjectCutout';

describe('SAM subject cutout composition', () => {
  it('keeps original subject pixels on transparent alpha and patches only its mask', () => {
    const source = new Uint8ClampedArray(4 * 4 * 4);
    const mask = new Uint8ClampedArray(4 * 4 * 4);
    for (let pixel = 0; pixel < 16; pixel += 1) {
      source.set([250, 248, 240, 255], pixel * 4);
      mask.set([0, 0, 0, 255], pixel * 4);
    }
    for (const [x, y] of [[1, 1], [2, 1], [1, 2], [2, 2]]) {
      const offset = (y * 4 + x) * 4;
      source.set([20, 90, 240, 255], offset);
      mask.set([255, 255, 255, 255], offset);
    }

    const layers = createSubjectCutoutLayers(source, mask, 4, 4);
    const subjectPixel = (1 * 4 + 1) * 4;
    const outsidePixel = 0;
    expect(layers.sourceRegion).toEqual({x: 0.25, y: 0.25, width: 0.5, height: 0.5});
    expect(Array.from(layers.subjectPixels.slice(subjectPixel, subjectPixel + 4))).toEqual([20, 90, 240, 255]);
    expect(layers.subjectPixels[outsidePixel + 3]).toBe(0);
    expect(Array.from(layers.backgroundPixels.slice(subjectPixel, subjectPixel + 4))).toEqual([250, 248, 240, 255]);
    expect(Array.from(source.slice(subjectPixel, subjectPixel + 4))).toEqual([20, 90, 240, 255]);
  });

  it('rejects an empty or dimensionally invalid mask instead of animating the full drawing', () => {
    const source = new Uint8ClampedArray(4 * 4 * 4).fill(255);
    expect(() => createSubjectCutoutLayers(source, new Uint8ClampedArray(source.length), 4, 4))
      .toThrow('MASK_AREA_INVALID');
    expect(() => createSubjectCutoutLayers(source, new Uint8ClampedArray(4), 4, 4))
      .toThrow('MASK_DIMENSIONS_INVALID');
  });

  it('routes a subject-only package without a verified mask to the existing V1 fallback', () => {
    expect(() => requireVerifiedCutoutMask('CUTOUT_MICRO_MOTION', false))
      .toThrow('SUBJECT_MASK_UNAVAILABLE');
    expect(() => requireVerifiedCutoutMask('CUTOUT_MICRO_MOTION', true)).not.toThrow();
  });

  it('requires the derived mask descriptor to match source, digest, role and media type', () => {
    const descriptor = {
      role: 'ORIGINAL_DERIVED_MASK',
      sourceSha256: 'a'.repeat(64),
      sha256: 'b'.repeat(64),
      contentType: 'image/png',
    };
    expect(matchesDerivedMaskProvenance(descriptor, 'a'.repeat(64), 'b'.repeat(64))).toBe(true);
    expect(matchesDerivedMaskProvenance({...descriptor, sourceSha256: 'c'.repeat(64)}, 'a'.repeat(64), 'b'.repeat(64))).toBe(false);
    expect(matchesDerivedMaskProvenance({...descriptor, sha256: 'c'.repeat(64)}, 'a'.repeat(64), 'b'.repeat(64))).toBe(false);
    expect(matchesDerivedMaskProvenance({...descriptor, role: 'ORIGINAL_DERIVED_TEXTURE'}, 'a'.repeat(64), 'b'.repeat(64))).toBe(false);
    expect(matchesDerivedMaskProvenance({...descriptor, contentType: 'image/jpeg'}, 'a'.repeat(64), 'b'.repeat(64))).toBe(false);
  });

  it('rejects a patch when corner samples do not establish a neutral paper background', () => {
    const source = new Uint8ClampedArray(4 * 4 * 4);
    const mask = new Uint8ClampedArray(4 * 4 * 4);
    for (let pixel = 0; pixel < 16; pixel += 1) {
      source.set([30, 90, 220, 255], pixel * 4);
      mask.set([255, 255, 255, 255], pixel * 4);
    }
    for (let y = 1; y < 3; y += 1) {
      for (let x = 1; x < 3; x += 1) {
        mask.set([0, 0, 0, 255], (y * 4 + x) * 4);
      }
    }
    expect(() => createSubjectCutoutLayers(source, mask, 4, 4)).toThrow('MASK_BACKGROUND_PATCH_UNSAFE');
  });
});
