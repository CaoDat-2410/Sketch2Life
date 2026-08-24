export const PIXI_BRIDGE_PROTOCOL_VERSION = '1' as const;

export type BridgeEnvelope<TType extends string, TPayload> = Readonly<{
  protocolVersion: typeof PIXI_BRIDGE_PROTOCOL_VERSION;
  type: TType;
  payload: TPayload;
}>;

export type RendererReadyMessage = BridgeEnvelope<'RENDERER_READY', Record<string, never>>;

export type RendererErrorMessage = BridgeEnvelope<
  'RENDERER_ERROR',
  Readonly<{code: string; message: string}>
>;

export type RendererMessage = RendererReadyMessage | RendererErrorMessage;
