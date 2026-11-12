import {
  PIXI_BRIDGE_PROTOCOL_VERSION,
  type RendererMessage,
} from '../protocol/messages';

export function isRendererMessage(value: unknown): value is RendererMessage {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    candidate.protocolVersion === PIXI_BRIDGE_PROTOCOL_VERSION &&
    (candidate.type === 'RENDERER_READY' || candidate.type === 'RENDERER_ERROR') &&
    typeof candidate.payload === 'object' &&
    candidate.payload !== null
  );
}
