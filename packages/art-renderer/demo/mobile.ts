import {Application, Rectangle, Texture} from 'pixi.js';

import {
  ART_RENDERER_PROTOCOL_VERSION,
  createAutoRigPlayer,
  createBrowserArtPlayer,
  MAX_RENDERER_MESSAGE_BYTES,
  RendererControlCommandSchema,
  RendererLoadCommandSchema,
  RendererLoadCommandV2Schema,
  RiggedArtworkPackageV1Schema,
  matchesDerivedMaskProvenance,
  sha256Hex,
  type PlaybackEvent,
  type RendererLoadCommand,
  type RendererLoadCommandV2,
} from '../src/index';

declare global {
  interface Window {
    ReactNativeWebView?: {postMessage(message: string): void};
  }
}

const stage = document.querySelector<HTMLElement>('#stage');
const status = document.querySelector<HTMLElement>('#status');
const playButton = document.querySelector<HTMLButtonElement>('#play');
const rendererInstanceId = new URLSearchParams(window.location.search).get('rendererInstanceId');

if (stage === null || status === null || playButton === null || rendererInstanceId === null) {
  throw new Error('Renderer host/bootstrap parameters are missing.');
}

const app = new Application();
await app.init({
  width: 800,
  height: 600,
  background: '#fffef9',
  antialias: true,
  autoDensity: true,
  resolution: Math.min(window.devicePixelRatio || 1, 2),
});
stage.append(app.canvas);

type ActiveLaunch = RendererLoadCommand | RendererLoadCommandV2;
type PlaybackController = Pick<ReturnType<typeof createBrowserArtPlayer>, 'play' | 'pause' | 'replay' | 'seekTo' | 'seekRelative' | 'getPlaybackState'>;

let launch: ActiveLaunch | null = null;
let sourceBlob: Blob | null = null;
let eventSequence = 0;
let lastLoadMessage: string | null = null;
let lastProgressPostAt = 0;
let activePlayer: PlaybackController | null = null;
let v2InteractionPhase: 'INTRO_LOADING' | 'INTRO_PLAYING' | 'DISCOVERY_READY' | 'FALLBACK' = 'INTRO_LOADING';

function post(value: unknown): void {
  const serialized = JSON.stringify(value);
  if (new TextEncoder().encode(serialized).byteLength > MAX_RENDERER_MESSAGE_BYTES) {
    status.textContent = 'Renderer bridge đã từ chối thông điệp vượt giới hạn.';
    return;
  }
  window.ReactNativeWebView?.postMessage(serialized);
}

function setPlaybackStatus(event: PlaybackEvent): void {
  switch (event.type) {
    case 'PLAYBACK_STARTED':
      status.textContent = 'Đang reveal bức vẽ gốc bằng PixiJS…';
      playButton.disabled = true;
      break;
    case 'PLAYBACK_COMPLETED':
      status.textContent = 'Đã hoàn tất reveal toàn ảnh gốc.';
      playButton.disabled = false;
      break;
    case 'INTRO_COMPLETED':
      status.textContent = 'Phần mở đầu từ bức vẽ đã hoàn thành.';
      break;
    case 'DISCOVERY_READY':
      status.textContent = 'Bức vẽ chuyển động đã sẵn sàng.';
      playButton.disabled = false;
      break;
    case 'CANVAS_TAPPED':
      break;
    case 'FALLBACK_APPLIED':
      status.textContent = 'Renderer dùng chuyển động dự phòng, vẫn giữ nguyên ảnh gốc.';
      playButton.disabled = false;
      break;
    case 'PLAYBACK_FAILED':
      status.textContent = 'Pixi không phát được chuyển động; ảnh gốc vẫn còn trong app.';
      playButton.disabled = false;
      break;
    case 'FOCUS_CHANGED':
      status.textContent = 'Đang soi gần hơn một chi tiết trong bức vẽ…';
      break;
    case 'DISCOVERED_ENTITY':
      status.textContent = `Con vừa khám phá ${event.labelVi}.`;
      break;
  }
}

function postLifecycle(event: PlaybackEvent): void {
  setPlaybackStatus(event);
  if (launch === null) return;
  eventSequence += 1;
  post({
    contractName: 'RendererPlaybackEventV1',
    contractVersion: '1.0',
    protocolVersion: ART_RENDERER_PROTOCOL_VERSION,
    rendererInstanceId,
    sequence: eventSequence,
    sessionId: launch.sessionId,
    experienceSpecRef: launch.experienceSpecRef,
    event,
  });
}

function postProgress(positionSeconds: number, durationSeconds: number, stateValue: 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED', interactionPhase: string): void {
  const now = performance.now();
  if (stateValue === 'PLAYING' && now - lastProgressPostAt < 100) return;
  lastProgressPostAt = now;
  eventSequence += 1;
  post({
    protocolVersion: ART_RENDERER_PROTOCOL_VERSION,
    rendererInstanceId,
    sequence: eventSequence,
    type: 'PLAYBACK_STATE',
    positionSeconds,
    durationSeconds,
    state: stateValue,
    interactionPhase,
  });
}

const classicPlayer = createBrowserArtPlayer({
  app,
  loadTexture: async (_uri, sourceRegion) => {
    if (sourceBlob === null) throw new Error('The original image is not loaded.');
    const bitmap = await createImageBitmap(sourceBlob);
    const bitmapWidth = bitmap.width;
    const bitmapHeight = bitmap.height;
    const canvas = document.createElement('canvas');
    canvas.width = bitmapWidth;
    canvas.height = bitmapHeight;
    const context = canvas.getContext('2d');
    if (context === null) {
      bitmap.close();
      throw new Error('Canvas context is unavailable.');
    }
    context.drawImage(bitmap, 0, 0);
    bitmap.close();
    const fullTexture = Texture.from(canvas);
    if (sourceRegion === undefined) return fullTexture;
    const x = Math.floor(sourceRegion.x * bitmapWidth);
    const y = Math.floor(sourceRegion.y * bitmapHeight);
    const width = Math.max(1, Math.floor(sourceRegion.width * bitmapWidth));
    const height = Math.max(1, Math.floor(sourceRegion.height * bitmapHeight));
    return new Texture({
      source: fullTexture.source,
      frame: new Rectangle(x, y, width, height),
      orig: new Rectangle(0, 0, width, height),
    });
  },
  onEvent: (event) => {
    postLifecycle(event);
  },
  onProgress: (progress) => {
    postProgress(progress.positionSeconds, progress.durationSeconds, progress.state, progress.interactionPhase);
  },
});

const autoRigPlayer = createAutoRigPlayer({
  app,
  onProgress: (positionSeconds, durationSeconds, stateValue) => {
    if (stateValue === 'PLAYING') v2InteractionPhase = 'INTRO_PLAYING';
    postProgress(positionSeconds, durationSeconds, stateValue, v2InteractionPhase);
  },
  onCompleted: () => {
    if (launch === null) return;
    const planId = launch.animationPlan.planId;
    v2InteractionPhase = 'DISCOVERY_READY';
    postLifecycle({type: 'PLAYBACK_COMPLETED', planId});
    postLifecycle({type: 'INTRO_COMPLETED', planId});
    postLifecycle({type: 'DISCOVERY_READY', planId, targetCount: 1});
  },
});

async function loadLaunch(serialized: string): Promise<void> {
  if (serialized === lastLoadMessage) return;
  if (launch !== null) {
    status.textContent = 'Renderer này đã nhận một launch. Mở Pixi lại từ app để tạo launch mới.';
    return;
  }
  if (new TextEncoder().encode(serialized).byteLength > MAX_RENDERER_MESSAGE_BYTES) {
    status.textContent = 'Launch vượt giới hạn bridge; không có ảnh nào được tải.';
    return;
  }

  let parsedJson: unknown;
  try {
    parsedJson = JSON.parse(serialized);
  } catch {
    status.textContent = 'Launch không phải JSON hợp lệ.';
    return;
  }
  const parsedV2 = RendererLoadCommandV2Schema.safeParse(parsedJson);
  const parsedV1 = RendererLoadCommandSchema.safeParse(parsedJson);
  const command = parsedV2.success ? parsedV2.data : parsedV1.success ? parsedV1.data : null;
  if (command === null || command.rendererInstanceId !== rendererInstanceId) {
    status.textContent = 'Launch sai contract hoặc không khớp renderer instance.';
    return;
  }
  lastLoadMessage = serialized;
  launch = command;
  status.textContent = 'Đang lấy đúng ảnh gốc từ backend qua capability tạm…';
  try {
    const response = await fetch(new URL(command.sourceReadEndpoint, window.location.href), {
      method: 'GET',
      headers: {'X-Render-Source-Capability': command.sourceReadCapability},
      cache: 'no-store',
      credentials: 'same-origin',
    });
    if (!response.ok) throw new Error('SOURCE_UNAVAILABLE');
    const image = await response.blob();
    if (image.size <= 0 || image.size > 5_000_000) throw new Error('SOURCE_SIZE_INVALID');
    if (image.type !== 'image/png' && image.type !== 'image/jpeg') throw new Error('SOURCE_TYPE_INVALID');
    if (
      command.contractName === 'RendererLoadCommandV2'
      && await sha256Hex(await image.arrayBuffer()) !== command.sourceSha256
    ) throw new Error('SOURCE_HASH_MISMATCH');
    sourceBlob = image;
    if (command.contractName === 'RendererLoadCommandV2') {
      status.textContent = 'Đang chuẩn bị từng nét vẽ chuyển động…';
      try {
        const packageResponse = await fetch(new URL(command.packageReadEndpoint, window.location.href), {
          method: 'GET',
          headers: {'X-Rig-Package-Capability': command.packageReadCapability},
          cache: 'no-store',
          credentials: 'same-origin',
        });
        if (!packageResponse.ok) throw new Error('RIG_PACKAGE_UNAVAILABLE');
        const packageBytes = await packageResponse.arrayBuffer();
        if (packageBytes.byteLength <= 0 || packageBytes.byteLength > 1_000_000) throw new Error('RIG_PACKAGE_SIZE_INVALID');
        if (await sha256Hex(packageBytes) !== command.packageSha256) throw new Error('RIG_PACKAGE_HASH_MISMATCH');
        const packageJson: unknown = JSON.parse(new TextDecoder().decode(packageBytes));
        const rigPackage = RiggedArtworkPackageV1Schema.parse(packageJson);
        if (rigPackage.sessionId !== command.sessionId || rigPackage.sourceSha256 !== command.sourceSha256) {
          throw new Error('RIG_PACKAGE_SOURCE_MISMATCH');
        }
        const foreground = await textureFromBlob(image, false, 1200);
        let maskCanvas: HTMLCanvasElement | undefined;
        if (rigPackage.tier === 'CUTOUT_MICRO_MOTION') {
          if (
            command.maskReadEndpoint === undefined
            || command.maskReadCapability === undefined
            || command.maskSha256 === undefined
            || !rigPackage.derivedArtifacts.some((artifact) => (
              matchesDerivedMaskProvenance(artifact, rigPackage.sourceSha256, command.maskSha256!)
            ))
          ) throw new Error('MASK_CAPABILITY_OR_PROVENANCE_INVALID');

          const maskResponse = await fetch(new URL(command.maskReadEndpoint, window.location.href), {
            method: 'GET',
            headers: {'X-Rig-Mask-Capability': command.maskReadCapability},
            cache: 'no-store',
            credentials: 'same-origin',
          });
          if (!maskResponse.ok || maskResponse.headers.get('Content-Type')?.split(';')[0] !== 'image/png') {
            throw new Error('MASK_UNAVAILABLE');
          }
          const maskBytes = await maskResponse.arrayBuffer();
          if (
            maskBytes.byteLength <= 8
            || maskBytes.byteLength > 5_000_000
            || await sha256Hex(maskBytes) !== command.maskSha256
            || maskResponse.headers.get('X-Content-SHA256') !== command.maskSha256
          ) throw new Error('MASK_HASH_OR_SIZE_INVALID');
          const maskBitmap = await createImageBitmap(new Blob([maskBytes], {type: 'image/png'}));
          if (maskBitmap.width !== foreground.sourceWidth || maskBitmap.height !== foreground.sourceHeight) {
            maskBitmap.close();
            throw new Error('MASK_DIMENSIONS_MISMATCH');
          }
          maskCanvas = document.createElement('canvas');
          maskCanvas.width = foreground.canvas.width;
          maskCanvas.height = foreground.canvas.height;
          const maskContext = maskCanvas.getContext('2d', {willReadFrequently: true});
          if (maskContext === null) {
            maskBitmap.close();
            throw new Error('MASK_CANVAS_UNAVAILABLE');
          }
          maskContext.drawImage(maskBitmap, 0, 0, maskCanvas.width, maskCanvas.height);
          maskBitmap.close();
        }
        autoRigPlayer.load(packageJson, command.animationPlan, foreground.texture, foreground.canvas, maskCanvas);
        activePlayer = autoRigPlayer;
        v2InteractionPhase = 'INTRO_LOADING';
      } catch (error) {
        console.error('[art-renderer] Renderer V2 package could not start.', safeFailureCode(error));
        await classicPlayer.load(v2FallbackPlan(command));
        activePlayer = classicPlayer;
        v2InteractionPhase = 'FALLBACK';
        postLifecycle({
          type: 'FALLBACK_APPLIED',
          planId: command.animationPlan.planId,
          reason: fallbackReason(error),
          durationSeconds: command.animationPlan.durationSeconds,
        });
      }
    } else {
      await classicPlayer.load(command.animationPlan.plan, {
        sceneExplorationPlan: command.sceneExplorationPlan,
        sceneFocusPlan: command.sceneFocusPlan,
      });
      activePlayer = classicPlayer;
    }
    playButton.disabled = false;
    playButton.textContent = 'Tạm dừng / tiếp tục';
    status.textContent = 'Pixi đã nạp ảnh gốc và bắt đầu câu chuyện.';
    if (command.contractName === 'RendererLoadCommandV2') {
      postLifecycle({type: 'PLAYBACK_STARTED', planId: command.animationPlan.planId});
    }
    activePlayer.play();
  } catch (error) {
    sourceBlob = null;
    status.textContent = 'Không nạp được ảnh gốc. Hãy về app và mở Pixi lại thủ công; không tự retry.';
    playButton.disabled = true;
    if (command.contractName === 'RendererLoadCommandV2') {
      postLifecycle({
        type: 'PLAYBACK_FAILED',
        planId: command.animationPlan.planId,
        reason: safeFailureCode(error),
      });
    }
  }
}

function receiveNativeMessage(event: MessageEvent): void {
  const serialized = typeof event.data === 'string' ? event.data : '';
  if (!serialized || new TextEncoder().encode(serialized).byteLength > MAX_RENDERER_MESSAGE_BYTES) return;
  try {
    const control = RendererControlCommandSchema.safeParse(JSON.parse(serialized));
    if (control.success && control.data.rendererInstanceId === rendererInstanceId) {
      switch (control.data.action) {
        case 'PLAY': activePlayer?.play(); break;
        case 'PAUSE': activePlayer?.pause(); break;
        case 'REPLAY': activePlayer?.replay(); break;
        case 'SEEK_RELATIVE_SECONDS': activePlayer?.seekRelative(control.data.seconds ?? 0); break;
        case 'SEEK_TO_SECONDS': activePlayer?.seekTo(control.data.seconds ?? 0); break;
      }
      return;
    }
  } catch {
    return;
  }
  void loadLaunch(serialized);
}

window.addEventListener('message', receiveNativeMessage);
document.addEventListener('message', receiveNativeMessage as EventListener);
playButton.addEventListener('click', () => {
  if (launch === null) return;
  try {
    const stateValue = activePlayer?.getPlaybackState();
    if (stateValue?.state === 'PLAYING') activePlayer?.pause();
    else if (stateValue?.state === 'COMPLETED') activePlayer?.replay();
    else activePlayer?.play();
  } catch {
    status.textContent = 'Pixi không phát được chuyển động; ảnh gốc vẫn còn trong app.';
  }
});

app.canvas.addEventListener('pointerdown', () => {
  if (launch?.contractName !== 'RendererLoadCommandV2') return;
  postLifecycle({
    type: 'CANVAS_TAPPED',
    planId: launch.animationPlan.planId,
  });
});

window.addEventListener('pagehide', () => {
  classicPlayer.destroy();
  autoRigPlayer.destroy();
  sourceBlob = null;
  app.destroy(true);
});

status.textContent = 'Pixi sẵn sàng, đang chờ launch của đúng phiên.';
post({protocolVersion: ART_RENDERER_PROTOCOL_VERSION, rendererInstanceId});

async function textureFromBlob(
  blob: Blob,
  removePaper: boolean,
  maxDimension?: number,
): Promise<{texture: Texture; canvas: HTMLCanvasElement; sourceWidth: number; sourceHeight: number}> {
  const bitmap = await createImageBitmap(blob);
  const sourceWidth = bitmap.width;
  const sourceHeight = bitmap.height;
  const scale = maxDimension === undefined ? 1 : Math.min(1, maxDimension / Math.max(sourceWidth, sourceHeight));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(sourceWidth * scale));
  canvas.height = Math.max(1, Math.round(sourceHeight * scale));
  const context = canvas.getContext('2d', {willReadFrequently: removePaper});
  if (context === null) {
    bitmap.close();
    throw new Error('Canvas context is unavailable.');
  }
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  if (removePaper) {
    const image = context.getImageData(0, 0, canvas.width, canvas.height);
    const corners = [0, (canvas.width - 1) * 4, (canvas.height - 1) * canvas.width * 4, (canvas.width * canvas.height - 1) * 4];
    const paper = [0, 1, 2].map((channel) => corners.reduce((sum, index) => sum + image.data[index + channel], 0) / corners.length);
    for (let index = 0; index < image.data.length; index += 4) {
      const distance = Math.hypot(image.data[index] - paper[0], image.data[index + 1] - paper[1], image.data[index + 2] - paper[2]);
      const brightness = (image.data[index] + image.data[index + 1] + image.data[index + 2]) / 3;
      if (distance < 34 && brightness > 185) image.data[index + 3] = 0;
    }
    context.putImageData(image, 0, 0);
  }
  return {texture: Texture.from(canvas), canvas, sourceWidth, sourceHeight};
}

function safeFailureCode(error: unknown): string {
  const message = error instanceof Error ? error.message : '';
  const knownCodes = [
    'SOURCE_UNAVAILABLE', 'SOURCE_SIZE_INVALID', 'SOURCE_TYPE_INVALID', 'SOURCE_HASH_MISMATCH',
    'RIG_PACKAGE_UNAVAILABLE', 'RIG_PACKAGE_SIZE_INVALID', 'RIG_PACKAGE_HASH_MISMATCH',
    'RIG_PACKAGE_SOURCE_MISMATCH',
    'MASK_UNAVAILABLE', 'MASK_CAPABILITY_OR_PROVENANCE_INVALID', 'MASK_HASH_OR_SIZE_INVALID',
    'MASK_DIMENSIONS_MISMATCH', 'MASK_CANVAS_UNAVAILABLE', 'MASK_AREA_INVALID',
    'MASK_REGION_INVALID', 'MASK_REGION_MISMATCH', 'MASK_DIMENSIONS_INVALID',
    'MASK_BACKGROUND_PATCH_UNSAFE', 'SUBJECT_MASK_UNAVAILABLE',
  ];
  return knownCodes.includes(message) ? message : 'RENDERER_V2_START_FAILED';
}

function fallbackReason(error: unknown): 'EXTRACTION_UNAVAILABLE' | 'MASK_INVALID' | 'ASSET_LOAD_FAILED' | 'MOTION_COMPILE_FAILED' {
  const code = safeFailureCode(error);
  if (code.startsWith('MASK_')) return 'MASK_INVALID';
  if (code.includes('PACKAGE') || code.includes('SOURCE')) return 'ASSET_LOAD_FAILED';
  return code === 'RENDERER_V2_START_FAILED' ? 'MOTION_COMPILE_FAILED' : 'EXTRACTION_UNAVAILABLE';
}

function v2FallbackPlan(command: RendererLoadCommandV2): unknown {
  return {
    contractVersion: '1',
    planId: command.animationPlan.planId,
    planVersion: String(command.experienceSpecRef.version),
    stage: {width: 800, height: 600},
    objects: [{
      id: 'original-art',
      label: command.animationPlan.learningBridgeVi,
      asset: {
        sourceAssetId: 'source-original-art',
        sourceAssetVersion: '1',
        uri: 'source:original-art',
        assetKind: 'WHOLE_DRAWING',
        sourceSha256: command.sourceSha256,
      },
      initialTransform: {
        position: {x: 0.5, y: 0.5},
        scale: 0.94,
        rotationDegrees: 0,
        opacity: 1,
      },
      extractionStatus: 'READY',
      interactive: false,
    }],
    motions: [
      {id: 'fallback-reveal', sceneId: 'fallback', kind: 'DRAW_REVEAL', targetId: 'original-art', durationSeconds: 1.2},
      {id: 'fallback-focus', sceneId: 'fallback', kind: 'SCALE', targetId: 'original-art', durationSeconds: 1.8, scale: 1.04},
      {id: 'fallback-settle', sceneId: 'fallback', kind: 'ROTATE', targetId: 'original-art', durationSeconds: 1.2, rotationDegrees: 1},
    ],
  };
}
