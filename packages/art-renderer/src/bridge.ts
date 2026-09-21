import {
  MAX_RENDERER_MESSAGE_BYTES,
  PlaybackEventSchema,
  RendererBootstrapSchema,
  type PlaybackEvent,
  type RendererBootstrap,
} from './contracts';

export type RendererMessage = RendererBootstrap | PlaybackEvent;

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
