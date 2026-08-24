export const ART_RENDERER_PROTOCOL_VERSION = '1' as const;

export interface RendererBootstrap {
  readonly protocolVersion: typeof ART_RENDERER_PROTOCOL_VERSION;
  readonly rendererInstanceId: string;
}
