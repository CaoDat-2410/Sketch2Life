import {describe, expect, it} from 'vitest';

import {createNativeBridgeInjection} from '../src/bridge';
import {MAX_RENDERER_COMMAND_BYTES} from '../src/contracts';

describe('native-to-renderer bridge injection', () => {
  it('passes a valid message as an escaped string to the installed receiver', () => {
    const message = JSON.stringify({
      type: 'PLAYBACK_CONTROL',
      rendererInstanceId: 'instance-1',
      text: `Bướm says ");window.alert('no')`,
    });

    const script = createNativeBridgeInjection(message);

    expect(script).toContain(`receive(${JSON.stringify(message)})`);
    expect(script).toContain('window.__sketch2lifeReceiveNativeMessage');
    expect(script).toMatch(/true;$/);
    expect(script).not.toContain("receive({type:");
  });

  it('rejects invalid JSON before constructing executable script', () => {
    expect(() => createNativeBridgeInjection('not-json')).toThrow('RENDERER_MESSAGE_INVALID_JSON');
  });

  it('accepts a bounded launch larger than the small renderer-event limit', () => {
    const largeLaunch = JSON.stringify({value: 'a'.repeat(5000)});
    expect(createNativeBridgeInjection(largeLaunch)).toContain('window.__sketch2lifeReceiveNativeMessage');
  });

  it('rejects commands over the dedicated native-to-page limit', () => {
    const oversized = JSON.stringify({value: 'a'.repeat(MAX_RENDERER_COMMAND_BYTES)});
    expect(() => createNativeBridgeInjection(oversized)).toThrow('RENDERER_COMMAND_TOO_LARGE');
  });
});
