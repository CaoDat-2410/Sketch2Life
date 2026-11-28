import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import { stageStartMarkers, strokeStartMarker } from '../src/parent/domain/svgGuide';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';
import { guideLevelForAge } from '../src/parent/presentation/navigation/sketchGuideFlow';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

const componentSource = readFileSync(new URL('../src/parent/presentation/components/ProgressiveSvgGuide.tsx', import.meta.url), 'utf8');
const screenSource = readFileSync(new URL('../src/parent/presentation/screens/LegacySketchGuideScreen.tsx', import.meta.url), 'utf8');

describe('FEAT-097 where the pencil starts and which way it goes', () => {
  it('starts at the first point and points along a straight line', () => {
    const marker = strokeStartMarker('M30 75 L30 93', 100);

    expect(marker).not.toBeNull();
    expect(marker?.start).toEqual({ x: 30, y: 75 });
    expect(marker?.angle).toBeCloseTo(Math.PI / 2, 3);
    expect(marker?.arrow.y).toBeGreaterThan(75);
    expect(marker?.arrow.y).toBeLessThan(93);
  });

  it('follows a curve: a circle drawn clockwise from the top leaves to the right and downwards', () => {
    const marker = strokeStartMarker('M45 40 C57.15 40 67 49.85 67 62 C67 74.15 57.15 84 45 84', 100);

    expect(marker?.start).toEqual({ x: 45, y: 40 });
    expect(marker?.arrow.x).toBeGreaterThan(45);
    expect(marker?.angle).toBeGreaterThan(0);
    expect(marker?.angle).toBeLessThan(Math.PI / 2);
  });

  it('shows nothing for a dot or for path commands it does not read', () => {
    expect(strokeStartMarker('M50 48.6 C50.77 48.6 51.4 49.23 51.4 50 C51.4 50.77 50.77 51.4 50 51.4', 100)).toBeNull();
    expect(strokeStartMarker('M10 10 a5 5 0 1 0 10 0', 100)).toBeNull();
    expect(strokeStartMarker('', 100)).toBeNull();
  });
});

describe('FEAT-097 the level of the guide', () => {
  it('follows the age of the child profile', () => {
    expect(guideLevelForAge(36)).toBe('beginner');
    expect(guideLevelForAge(71)).toBe('beginner');
    expect(guideLevelForAge(72)).toBe('simple');
    expect(guideLevelForAge(undefined)).toBe('beginner');
  });

  it('sends only the level, never the age', async () => {
    const fetcher = vi.fn(async () => new Response('{}', { status: 200 }));
    const api = new ParentApi({ getIdToken: async () => 'synthetic-token' }, fetcher as unknown as typeof fetch, 'https://parent.example.test');

    await api.generateSketchGuide('con gà', undefined, 'simple');
    await api.generateSketchGuide('con gà');

    const bodies = fetcher.mock.calls.map((call) => JSON.parse(String((call as unknown as [string, RequestInit])[1].body)));
    expect(bodies[0]).toEqual({ contract: 'SvgTopicStrokeGuideRequestV1', topic: 'con gà', difficulty: 'simple' });
    expect(bodies[1].difficulty).toBe('beginner');
  });
});

describe('FEAT-097 the screen', () => {
  it('draws new strokes one after another, dashed, with a start dot, and can replay them', () => {
    expect(componentSource).toContain('Animated.sequence(');
    expect(componentSource).not.toContain('Animated.parallel(');
    expect(componentSource).toContain('stageStartMarkers');
    expect(componentSource).toContain('Xem lại cách vẽ');
  });

  it('lets the adult change the level and does not call the recipe a third-party picture', () => {
    expect(screenSource).toContain('Bé 3–5 tuổi');
    expect(screenSource).toContain('Bé 6–10 tuổi');
    expect(screenSource).toContain('Mẫu vẽ của Sketch2Life · người lớn xem trước');
  });
});

describe('FEAT-097 which subject the guide is for', () => {
  it('asks for the subject chosen for the drawing before the free idea', () => {
    const controller = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');

    expect(controller).toContain('sketchGuideRequestSubject(intendedDrawingSubject.trim() || idea)');
  });
});

describe('FEAT-097 start marks of one step (seen on the emulator)', () => {
  const circle = 'M45 40 C57.15 40 67 49.85 67 62 C67 74.15 57.15 84 45 84';
  const line = 'M30 75 L30 93';
  const dot = 'M73 30.6 C73.77 30.6 74.4 31.23 74.4 32 C74.4 32.77 73.77 33.4 73 33.4';

  it('numbers the strokes only when there are at least two of them to order', () => {
    expect(stageStartMarkers([{ path_id: 'a', d: circle }, { path_id: 'eye', d: dot }], 100)).toEqual([
      expect.objectContaining({ pathId: 'a', number: null }),
    ]);
    expect(stageStartMarkers([{ path_id: 'a', d: line }, { path_id: 'b', d: circle }], 100).map((item) => item.number)).toEqual([1, 2]);
  });

  it('leaves a dot without a mark, so it can be drawn solid instead of dashed', () => {
    expect(stageStartMarkers([{ path_id: 'eye', d: dot }], 100)).toEqual([]);
    expect(componentSource).toContain('strokeDasharray={hasMarker ?');
  });

  it('shows the chosen level as selected, not as a disabled button', () => {
    expect(screenSource).toContain('props.level === value ? <PrimaryButton');
  });
});
