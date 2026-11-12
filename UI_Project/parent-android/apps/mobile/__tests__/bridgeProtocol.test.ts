import {isRendererMessage} from '../src/bridge/pixi/validation/isRendererMessage';

describe('Pixi bridge protocol', () => {
  it('accepts the versioned ready envelope', () => {
    expect(
      isRendererMessage({protocolVersion: '1', type: 'RENDERER_READY', payload: {}}),
    ).toBe(true);
  });

  it('rejects an unknown protocol version', () => {
    expect(
      isRendererMessage({protocolVersion: '2', type: 'RENDERER_READY', payload: {}}),
    ).toBe(false);
  });
});
