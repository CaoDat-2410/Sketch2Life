import {describe, expect, it} from 'vitest';

import {fitCanvasToStage} from '../src/canvasFit';

describe('fitCanvasToStage', () => {
  it('contains large portrait artwork with a margin and centered letterboxing', () => {
    const fit = fitCanvasToStage(1200, 1800, 800, 600);

    expect(fit.scale).toBeCloseTo(0.2933, 3);
    expect(fit.x).toBeCloseTo(224, 0);
    expect(fit.y).toBeCloseTo(36, 0);
    expect(1200 * fit.scale).toBeLessThan(800);
    expect(1800 * fit.scale).toBeLessThan(600);
  });

  it('keeps landscape proportions without stretching', () => {
    const fit = fitCanvasToStage(1600, 900, 800, 600);

    expect(fit.scale).toBeCloseTo(0.44);
    expect(1600 * fit.scale / (900 * fit.scale)).toBeCloseTo(1600 / 900);
    expect(fit.x).toBeCloseTo(48);
    expect(fit.y).toBeCloseTo(102);
  });

  it('rejects invalid image dimensions', () => {
    expect(() => fitCanvasToStage(0, 300, 800, 600)).toThrow('CANVAS_FIT_DIMENSIONS_INVALID');
  });
});
