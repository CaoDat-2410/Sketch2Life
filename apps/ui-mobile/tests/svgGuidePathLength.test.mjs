import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { estimateSvgPathLength } from '../src/parent/domain/svgGuide.ts';

const sourceSvg = readFileSync(
  new URL('../../../deployment/modal/srs_v23/data/arcadia_organism_strokes/gallus-gallus-source.svg', import.meta.url),
  'utf8',
);
const sourcePathData = [...sourceSvg.matchAll(/<path\b[^>]*\bd="([^"]+)"/g)].map((match) => match[1]);

describe('progressive SVG stroke animation lengths', () => {
  it('measures a straight stroke', () => {
    expect(estimateSvgPathLength('M 0 0 L 3 4')).toBe(5);
  });

  it('includes closing segments and approximates curves', () => {
    expect(estimateSvgPathLength('M 0 0 L 10 0 L 10 10 L 0 10 Z')).toBe(40);
    const curveLength = estimateSvgPathLength('M 0 0 Q 5 10 10 0');
    expect(curveLength).toBeGreaterThan(14);
    expect(curveLength).toBeLessThan(16);
  });

  it('measures relative source commands instead of treating them as unknown paths', () => {
    expect(estimateSvgPathLength('M0 0h3v4z')).toBe(12);
    const relativeCurve = estimateSvgPathLength('M0 0c0 10 10 10 10 0');
    expect(relativeCurve).toBeGreaterThan(19);
    expect(relativeCurve).toBeLessThan(21);
  });

  it('estimates an SVG arc so the animated dash can reveal its full contour', () => {
    const halfCircle = estimateSvgPathLength('M0 0A10 10 0 0 1 20 0');
    expect(halfCircle).toBeGreaterThan(31);
    expect(halfCircle).toBeLessThan(32);
  });

  it('measures the real pinned dataset paths used by the Parent guide', () => {
    expect(sourcePathData).toHaveLength(77);
    for (const pathData of sourcePathData) {
      const pathLength = estimateSvgPathLength(pathData);
      expect(pathLength).toBeGreaterThan(1);
      expect(pathLength).toBeLessThan(10_000);
    }
  });
});
