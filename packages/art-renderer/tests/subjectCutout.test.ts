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

  it('rejects a subject-only package when its verified mask is unavailable', () => {
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

  it('inpaints a valid subject mask from its local background when image corners are non-neutral', () => {
    const width = 12;
    const height = 12;
    const source = new Uint8ClampedArray(width * height * 4);
    const mask = new Uint8ClampedArray(width * height * 4);
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        source.set([238, 235, 228, 255], (y * width + x) * 4);
        mask.set([0, 0, 0, 255], (y * width + x) * 4);
      }
    }
    for (const [x, y, rgb] of [
      [0, 0, [30, 90, 220]], [width - 1, 0, [30, 90, 220]],
      [0, height - 1, [30, 90, 220]], [width - 1, height - 1, [30, 90, 220]],
    ] as const) source.set([...rgb, 255], (y * width + x) * 4);
    for (let y = 4; y < 8; y += 1) {
      for (let x = 4; x < 8; x += 1) {
        const offset = (y * width + x) * 4;
        source.set([220, 40, 20, 255], offset);
        mask.set([255, 255, 255, 255], offset);
      }
    }

    const sourceBefore = new Uint8ClampedArray(source);
    const layers = createSubjectCutoutLayers(source, mask, width, height);
    const subjectPixel = (5 * width + 5) * 4;
    const outsidePixel = (0 * width + 0) * 4;

    expect(Array.from(layers.backgroundPixels.slice(subjectPixel, subjectPixel + 4))).toEqual([238, 235, 228, 255]);
    expect(Array.from(layers.backgroundPixels.slice(outsidePixel, outsidePixel + 4))).toEqual([30, 90, 220, 255]);
    expect(Array.from(layers.subjectPixels.slice(subjectPixel, subjectPixel + 4))).toEqual([220, 40, 20, 255]);
    expect(source).toEqual(sourceBefore);
  });

  it('uses nearby paper rather than saturated pigment donors and preserves every outside pixel', () => {
    const width = 18;
    const height = 18;
    const source = new Uint8ClampedArray(width * height * 4);
    const mask = new Uint8ClampedArray(width * height * 4);
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const offset = (y * width + x) * 4;
        source.set([238, 235, 228, 255], offset);
        mask.set([0, 0, 0, 255], offset);
      }
    }
    // A heavy orange crayon ring just outside the SAM subject mask.
    for (let y = 5; y < 13; y += 1) {
      for (let x = 5; x < 13; x += 1) {
        if (x >= 7 && x < 11 && y >= 7 && y < 11) continue;
        source.set([245, 105, 12, 255], (y * width + x) * 4);
      }
    }
    for (let y = 7; y < 11; y += 1) {
      for (let x = 7; x < 11; x += 1) {
        const offset = (y * width + x) * 4;
        source.set([30, 110, 230, 255], offset);
        mask.set([255, 255, 255, 255], offset);
      }
    }

    const original = new Uint8ClampedArray(source);
    const layers = createSubjectCutoutLayers(source, mask, width, height);
    const subjectOffset = (8 * width + 8) * 4;
    expect(Array.from(layers.backgroundPixels.slice(subjectOffset, subjectOffset + 3)))
      .toEqual([238, 235, 228]);
    for (let pixel = 0; pixel < width * height; pixel += 1) {
      const offset = pixel * 4;
      const masked = mask[offset] > 8;
      if (!masked) {
        expect(Array.from(layers.backgroundPixels.slice(offset, offset + 4)))
          .toEqual(Array.from(original.slice(offset, offset + 4)));
      }
    }
    expect(source).toEqual(original);
  });

  it('rejects a mask whose local neighborhood contains no credible paper donors', () => {
    const width = 12;
    const height = 12;
    const source = new Uint8ClampedArray(width * height * 4);
    const mask = new Uint8ClampedArray(width * height * 4);
    for (let pixel = 0; pixel < width * height; pixel += 1) {
      source.set([90, 35, 205, 255], pixel * 4);
      mask.set([0, 0, 0, 255], pixel * 4);
    }
    for (let y = 4; y < 8; y += 1) {
      for (let x = 4; x < 8; x += 1) {
        const offset = (y * width + x) * 4;
        source.set([230, 45, 28, 255], offset);
        mask.set([255, 255, 255, 255], offset);
      }
    }
    expect(() => createSubjectCutoutLayers(source, mask, width, height))
      .toThrow('MASK_BACKGROUND_RECONSTRUCTION_FAILED');
  });
});
