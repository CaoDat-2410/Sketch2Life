export interface RendererBenchmarkSample {
  readonly startedAt: string;
  readonly startupMilliseconds: number;
  readonly averageFramesPerSecond: number | null;
  readonly usedHeapBytes: number | null;
  readonly fixtureId: string;
}

interface MemoryPerformance extends Performance {
  readonly memory?: Readonly<{usedJSHeapSize: number}>;
}

export function createRendererBenchmarkSample(
  fixtureId: string,
  startedAt: number,
  completedAt: number,
  framesRendered: number,
): RendererBenchmarkSample {
  const elapsedMilliseconds = Math.max(0, completedAt - startedAt);
  const performanceWithMemory = globalThis.performance as MemoryPerformance;
  const usedHeapBytes = performanceWithMemory.memory?.usedJSHeapSize ?? null;

  return {
    startedAt: new Date(Date.now() - elapsedMilliseconds).toISOString(),
    startupMilliseconds: elapsedMilliseconds,
    averageFramesPerSecond:
      elapsedMilliseconds > 0 ? Number(((framesRendered * 1000) / elapsedMilliseconds).toFixed(2)) : null,
    usedHeapBytes,
    fixtureId,
  };
}
