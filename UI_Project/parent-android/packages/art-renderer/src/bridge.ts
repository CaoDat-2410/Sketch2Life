import {
  MAX_RENDERER_MESSAGE_BYTES,
  MAX_RENDERER_COMMAND_BYTES,
  PlaybackEventSchema,
  RendererBootstrapSchema,
  type PlaybackEvent,
  type RendererBootstrap,
} from './contracts';

export type RendererMessage = RendererBootstrap | PlaybackEvent;

/**
 * Build a bounded call into the renderer's native-message receiver.
 * JSON.stringify keeps the payload a string literal so message contents can
 * never become executable JavaScript when passed to WebView.injectJavaScript.
 */
export function createNativeBridgeInjection(serialized: string): string {
  const byteLength = encodeURIComponent(serialized).replace(/%[0-9A-F]{2}/g, 'U').length;
  if (byteLength > MAX_RENDERER_COMMAND_BYTES) {
    throw new Error('RENDERER_COMMAND_TOO_LARGE');
  }
  try {
    JSON.parse(serialized);
  } catch {
    throw new Error('RENDERER_MESSAGE_INVALID_JSON');
  }

  return `(function(){var receive=window.__sketch2lifeReceiveNativeMessage;if(typeof receive==="function"){receive(${JSON.stringify(serialized)});}})();true;`;
}

/** Parse one bounded JSON message from the WebView/native bridge. */
export function parseRendererMessage(serialized: string): RendererMessage {
  if (new TextEncoder().encode(serialized).byteLength > MAX_RENDERER_MESSAGE_BYTES) {
    throw new Error('RENDERER_MESSAGE_TOO_LARGE');
  }

  let value: unknown;
  try {
    value = JSON.parse(serialized);
  } catch {
    throw new Error('RENDERER_MESSAGE_INVALID_JSON');
  }

  const bootstrap = RendererBootstrapSchema.safeParse(value);
  if (bootstrap.success) {
    return bootstrap.data;
  }
  const event = PlaybackEventSchema.safeParse(value);
  if (event.success) {
    return event.data;
  }
  throw new Error('RENDERER_MESSAGE_INVALID_CONTRACT');
}
