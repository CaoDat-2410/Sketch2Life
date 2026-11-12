import {describe, expect, it, vi} from 'vitest';

import {createRendererStartupGate} from '../src/startupGate';

describe('renderer startup gate', () => {
  it('queues a launch until Pixi is ready and ignores its readiness replay', () => {
    const onReady = vi.fn();
    const onFailed = vi.fn();
    const gate = createRendererStartupGate(onReady, onFailed);

    gate.receive('launch-1');
    gate.receive('launch-1');
    gate.receive('unexpected-launch-2');
    expect(onReady).not.toHaveBeenCalled();

    gate.markReady();
    gate.markReady();
    gate.receive('launch-1');
    gate.receive('unexpected-launch-2');

    expect(onReady).toHaveBeenCalledTimes(1);
    expect(onReady).toHaveBeenCalledWith('launch-1');
    expect(onFailed).not.toHaveBeenCalled();
  });

  it('reports a queued launch when Pixi initialization fails', () => {
    const onReady = vi.fn();
    const onFailed = vi.fn();
    const gate = createRendererStartupGate(onReady, onFailed);

    gate.receive('launch-1');
    gate.markFailed();
    gate.markFailed();
    gate.receive('launch-1');
    gate.receive('launch-1');
    gate.receive('unexpected-launch-2');

    expect(onReady).not.toHaveBeenCalled();
    expect(onFailed).toHaveBeenCalledTimes(1);
    expect(onFailed).toHaveBeenCalledWith('launch-1');
  });

  it('handles a launch arriving after initialization failure', () => {
    const onReady = vi.fn();
    const onFailed = vi.fn();
    const gate = createRendererStartupGate(onReady, onFailed);

    gate.markFailed();
    gate.receive('launch-1');

    expect(onReady).not.toHaveBeenCalled();
    expect(onFailed).toHaveBeenCalledTimes(1);
    expect(onFailed).toHaveBeenCalledWith('launch-1');
  });

  it('delivers launches immediately after successful initialization', () => {
    const onReady = vi.fn();
    const onFailed = vi.fn();
    const gate = createRendererStartupGate(onReady, onFailed);

    gate.markReady();
    gate.receive('launch-1');

    expect(onReady).toHaveBeenCalledTimes(1);
    expect(onReady).toHaveBeenCalledWith('launch-1');
    expect(onFailed).not.toHaveBeenCalled();
  });
});
