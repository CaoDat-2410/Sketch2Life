import {Application, Container, Rectangle, Sprite, Texture} from 'pixi.js';

import {
  ART_RENDERER_PROTOCOL_VERSION,
  createAutoRigPlayer,
  createBrowserArtPlayer,
  MAX_RENDERER_MESSAGE_BYTES,
  MAX_RENDERER_COMMAND_BYTES,
  RendererControlCommandSchema,
  RendererLoadCommandSchema,
  RendererLoadCommandV2Schema,
  RendererLoadCommandV3Schema,
  RendererLoadCommandV4Schema,
  getSpriteCycleFrameIndex,
  getSpriteCycleTransform,
  RiggedArtworkPackageV1Schema,
  matchesDerivedMaskProvenance,
  sha256Hex,
  createRendererStartupGate,
  normalizeRendererFailureCode,
  type PlaybackEvent,
  type RendererLoadCommand,
  type RendererLoadCommandV2,
  type RendererLoadCommandV3,
  type RendererLoadCommandV4,
  type PixiSpriteCycleReadV1,
} from '../src/index';

declare global {
  interface Window {
    ReactNativeWebView?: {postMessage(message: string): void};
    __sketch2lifeReceiveNativeMessage?: (serialized: string) => void;
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
let rendererInitialized = false;

type ActiveLaunch = RendererLoadCommand | RendererLoadCommandV2 | RendererLoadCommandV3 | RendererLoadCommandV4;
type PlaybackController = Pick<ReturnType<typeof createBrowserArtPlayer>, 'play' | 'pause' | 'replay' | 'seekTo' | 'seekRelative' | 'getPlaybackState' | 'destroy'>;

let launch: ActiveLaunch | null = null;
let sourceBlob: Blob | null = null;
let eventSequence = 0;
let lastLoadMessage: string | null = null;
let lastAcceptedLaunchMessage: string | null = null;
let lastProgressPostAt = 0;
let activePlayer: PlaybackController | null = null;
const destroyedPlayers = new Set<PlaybackController>();
let v2InteractionPhase: 'INTRO_LOADING' | 'INTRO_PLAYING' | 'DISCOVERY_READY' | 'FALLBACK' = 'INTRO_LOADING';
let supplementalRoot: Container | null = null;
let supplementalTextures: Texture[] = [];
let supplementalSprites = new Map<string, Sprite>();
let activeSpriteCycle: {cycle: PixiSpriteCycleReadV1; root: Container; sprite: Sprite; textures: Texture[]; frameIndex: number | null; wasVisible: boolean} | null = null;

function isV2Launch(command: ActiveLaunch): command is RendererLoadCommandV2 | RendererLoadCommandV3 | RendererLoadCommandV4 {
  return command.contractName === 'RendererLoadCommandV2' || command.contractName === 'RendererLoadCommandV3' || command.contractName === 'RendererLoadCommandV4';
}

function isShowLaunch(command: ActiveLaunch): command is RendererLoadCommandV3 | RendererLoadCommandV4 {
  return command.contractName === 'RendererLoadCommandV3' || command.contractName === 'RendererLoadCommandV4';
}

function launchPlanId(command: ActiveLaunch): string {
  return isV2Launch(command) ? command.animationPlan.planId : command.animationPlan.plan.planId;
}

function stopSupplementalShow(): void {
  autoRigPlayer.setShowBeat(null, 0);
  stopActiveSpriteCycle();
  supplementalRoot?.destroy({children: true});
  supplementalRoot = null;
  supplementalSprites.clear();
  for (const texture of supplementalTextures) texture.destroy(true);
  supplementalTextures = [];
}

function safelyDestroyPlayer(player: PlaybackController | null): void {
  if (player === null || destroyedPlayers.has(player)) return;
  destroyedPlayers.add(player);
  try { player.destroy(); } catch { /* Cleanup must not suppress the typed failure. */ }
}

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
      status.textContent = launch !== null && isV2Launch(launch)
        ? launch.animationPlan.tier === 'CUTOUT_MICRO_MOTION'
          ? 'Chủ thể chuyển động nhẹ; chưa tách được bộ phận.'
          : 'Đang phát chuyển động các bộ phận bằng PixiJS…'
        : 'Đang reveal bức vẽ gốc bằng PixiJS…';
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
      playButton.disabled = true;
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
    if (launch !== null && isShowLaunch(launch)) syncShowToTime(positionSeconds);
    postProgress(positionSeconds, durationSeconds, stateValue, v2InteractionPhase);
  },
  onCompleted: () => {
    if (launch === null || !isV2Launch(launch)) return;
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
  if (new TextEncoder().encode(serialized).byteLength > MAX_RENDERER_COMMAND_BYTES) {
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
  const parsedV4 = RendererLoadCommandV4Schema.safeParse(parsedJson);
  const parsedV3 = RendererLoadCommandV3Schema.safeParse(parsedJson);
  const parsedV2 = RendererLoadCommandV2Schema.safeParse(parsedJson);
  const parsedV1 = RendererLoadCommandSchema.safeParse(parsedJson);
  const command = parsedV4.success
    ? parsedV4.data
    : parsedV3.success
    ? parsedV3.data
    : parsedV2.success
      ? parsedV2.data
      : parsedV1.success
        ? parsedV1.data
        : null;
  if (command === null || command.rendererInstanceId !== rendererInstanceId) {
    status.textContent = 'Launch sai contract hoặc không khớp renderer instance.';
    return;
  }
  lastLoadMessage = serialized;
  launch = command;
  if (command.contractName === 'RendererLoadCommandV4' && command.spriteCycleStatus === 'BLOCKED') {
    console.info('[pixi-cycle]', JSON.stringify({
      event: 'blocked',
      behaviorClassId: command.showPlan.behaviorClass,
      reason: command.spriteCycleReasonCode ?? 'FRAME_QA_FAILED',
    }));
  }
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
      isV2Launch(command)
      && await sha256Hex(await image.arrayBuffer()) !== command.sourceSha256
    ) throw new Error('SOURCE_HASH_MISMATCH');
    sourceBlob = image;
    if (isV2Launch(command)) {
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
        if (rigPackage.tier === 'CUTOUT_MICRO_MOTION' || rigPackage.tier === 'FULL_AUTO_RIG') {
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
          maskCanvas = await maskCanvasFromBytes(maskBytes, foreground);
        }
        const partMaskCanvases = new Map<string, HTMLCanvasElement>();
        if (rigPackage.tier === 'FULL_AUTO_RIG') {
          if (maskCanvas === undefined || rigPackage.parts.length < 2) {
            throw new Error('PART_MASKS_REQUIRED');
          }
          const packagePartIds = new Set(rigPackage.parts.map((part) => part.partId));
          if (
            command.partMaskReads.length !== rigPackage.parts.length
            || command.rigParts.length !== rigPackage.parts.length
          ) throw new Error('PART_MASK_HANDOFF_INVALID');
          for (const partRead of command.partMaskReads) {
            const packagePart = rigPackage.parts.find((part) => part.partId === partRead.partId);
            const commandPart = command.rigParts.find((part) => part.partId === partRead.partId);
            if (
              packagePart === undefined
              || commandPart === undefined
              || packagePart.boneId !== partRead.boneId
              || packagePart.maskSha256 !== partRead.sha256
              || commandPart.maskArtifactRef !== packagePart.maskArtifactRef
              || commandPart.maskSha256 !== packagePart.maskSha256
              || !rigPackage.derivedArtifacts.some((artifact) => (
                matchesDerivedPartMaskProvenance(artifact, rigPackage.sourceSha256, packagePart.maskArtifactRef, partRead.sha256)
              ))
            ) throw new Error('PART_MASK_PROVENANCE_INVALID');
            const partResponse = await fetch(new URL(partRead.readEndpoint, window.location.href), {
              method: 'GET',
              headers: {'X-Rig-Mask-Capability': partRead.readCapability},
              cache: 'no-store',
              credentials: 'same-origin',
            });
            if (!partResponse.ok || partResponse.headers.get('Content-Type')?.split(';')[0] !== 'image/png') {
              throw new Error('PART_MASK_UNAVAILABLE');
            }
            const partBytes = await partResponse.arrayBuffer();
            if (
              partBytes.byteLength <= 8
              || partBytes.byteLength > 5_000_000
              || await sha256Hex(partBytes) !== partRead.sha256
              || partResponse.headers.get('X-Content-SHA256') !== partRead.sha256
            ) throw new Error('PART_MASK_HASH_INVALID');
            partMaskCanvases.set(partRead.partId, await maskCanvasFromBytes(partBytes, foreground));
          }
          if (packagePartIds.size !== partMaskCanvases.size) throw new Error('PART_MASK_HANDOFF_INVALID');
        } else if (rigPackage.tier === 'CUTOUT_MICRO_MOTION') {
          // A verified subject silhouette is a valid lower tier; it must not be rejected for
          // lacking independent part masks. The player keeps the silhouette intact and moves it
          // only within its fixed framing. FULL_AUTO_RIG remains separately part-mask gated.
          if (maskCanvas === undefined) throw new Error('SUBJECT_MASK_UNAVAILABLE');
        } else {
          throw new Error('RIG_TIER_NOT_RENDERABLE');
        }
        autoRigPlayer.load(
          packageJson,
          command.animationPlan,
          foreground.canvas,
          maskCanvas,
          partMaskCanvases,
        );
        activePlayer = autoRigPlayer;
        v2InteractionPhase = 'INTRO_LOADING';
        if (isShowLaunch(command)) {
          await loadSupplementalShow(command);
        }
        if (command.contractName === 'RendererLoadCommandV4' && command.spriteCycle !== undefined) {
          await loadSpriteCycle(command);
        }
      } catch (error) {
        console.error('[art-renderer] Renderer V2 package could not start.', safeFailureCode(error));
        stopSupplementalShow();
        safelyDestroyPlayer(autoRigPlayer);
        activePlayer = null;
        playButton.disabled = true;
        playButton.textContent = 'Thử mở lại trong ứng dụng';
        status.textContent = 'Đang giữ ảnh gốc. Hãy thử mở chuyển động lại trong ứng dụng.';
        postLifecycle({
          type: 'PLAYBACK_FAILED',
          planId: command.animationPlan.planId,
          reason: safeFailureCode(error),
        });
        return;
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
    if (isV2Launch(command)) {
      postLifecycle({type: 'PLAYBACK_STARTED', planId: command.animationPlan.planId});
    }
    activePlayer.play();
  } catch (error) {
    try {
      stopSupplementalShow();
      safelyDestroyPlayer(isV2Launch(command) ? autoRigPlayer : classicPlayer);
    } catch {
      // Keep the original source and still report the launch failure.
    }
    activePlayer = null;
    sourceBlob = null;
    status.textContent = 'Không nạp được ảnh gốc. Hãy về app và mở Pixi lại thủ công; không tự retry.';
    playButton.disabled = true;
    postLifecycle({
      type: 'PLAYBACK_FAILED',
      planId: launchPlanId(command),
      reason: safeFailureCode(error),
    });
  }
}

function receiveNativeMessage(event: MessageEvent): void {
  const serialized = typeof event.data === 'string' ? event.data : '';
  const serializedByteLength = new TextEncoder().encode(serialized).byteLength;
  if (!serialized || serializedByteLength > MAX_RENDERER_COMMAND_BYTES) return;
  let parsed: unknown;
  try {
    parsed = JSON.parse(serialized);
  } catch {
    return;
  }
  const control = RendererControlCommandSchema.safeParse(parsed);
  if (control.success && control.data.rendererInstanceId === rendererInstanceId) {
    if (serializedByteLength > MAX_RENDERER_MESSAGE_BYTES) return;
    try {
      switch (control.data.action) {
        case 'PLAY': activePlayer?.play(); break;
        case 'PAUSE': activePlayer?.pause(); break;
        case 'REPLAY': activePlayer?.replay(); break;
        case 'SEEK_RELATIVE_SECONDS': activePlayer?.seekRelative(control.data.seconds ?? 0); break;
        case 'SEEK_TO_SECONDS': activePlayer?.seekTo(control.data.seconds ?? 0); break;
      }
    } catch (error) {
      reportPlaybackFailure(error);
    }
    return;
  }
  const parsedV4 = RendererLoadCommandV4Schema.safeParse(parsed);
  const parsedV3 = RendererLoadCommandV3Schema.safeParse(parsed);
  const parsedV2 = RendererLoadCommandV2Schema.safeParse(parsed);
  const parsedV1 = RendererLoadCommandSchema.safeParse(parsed);
  const command = parsedV4.success
    ? parsedV4.data
    : parsedV3.success
    ? parsedV3.data
    : parsedV2.success
      ? parsedV2.data
      : parsedV1.success
        ? parsedV1.data
        : null;
  if (command?.rendererInstanceId === rendererInstanceId) {
    if (lastAcceptedLaunchMessage !== serialized) {
      lastAcceptedLaunchMessage = serialized;
      // A bootstrap only confirms that the page can talk to native. This
      // state is the explicit acknowledgment that native launch reached JS.
      postProgress(0, 0, 'READY', v2InteractionPhase);
    }
    startupGate.receive(serialized);
  }
}

window.__sketch2lifeReceiveNativeMessage = (serialized) => {
  receiveNativeMessage({data: serialized} as MessageEvent);
};

playButton.addEventListener('click', () => {
  if (launch === null) return;
  try {
    const stateValue = activePlayer?.getPlaybackState();
    if (stateValue?.state === 'PLAYING') activePlayer?.pause();
    else if (stateValue?.state === 'COMPLETED') activePlayer?.replay();
    else activePlayer?.play();
  } catch (error) {
    reportPlaybackFailure(error);
  }
});

function reportPlaybackFailure(error: unknown): void {
  const reason = safeFailureCode(error);
  stopSupplementalShow();
  safelyDestroyPlayer(activePlayer);
  activePlayer = null;
  playButton.disabled = true;
  playButton.textContent = 'Thử mở lại trong ứng dụng';
  status.textContent = 'Pixi không phát được chuyển động; ảnh gốc vẫn còn trong app.';
  if (launch !== null) {
    postLifecycle({
      type: 'PLAYBACK_FAILED',
      planId: launchPlanId(launch),
      reason,
    });
  }
}

window.addEventListener('pagehide', () => {
  stopSupplementalShow();
  safelyDestroyPlayer(activePlayer);
  if (activePlayer === null && launch !== null) {
    safelyDestroyPlayer(isV2Launch(launch) ? autoRigPlayer : classicPlayer);
  } else if (launch === null) {
    safelyDestroyPlayer(classicPlayer);
    safelyDestroyPlayer(autoRigPlayer);
  }
  sourceBlob = null;
  if (rendererInitialized) app.destroy(true);
});

function reportPixiInitializationFailure(serialized: string): void {
  let parsedJson: unknown;
  try {
    parsedJson = JSON.parse(serialized);
  } catch {
    return;
  }
  const parsedV4 = RendererLoadCommandV4Schema.safeParse(parsedJson);
  const parsedV3 = RendererLoadCommandV3Schema.safeParse(parsedJson);
  const parsedV2 = RendererLoadCommandV2Schema.safeParse(parsedJson);
  const parsedV1 = RendererLoadCommandSchema.safeParse(parsedJson);
  const command = parsedV4.success
    ? parsedV4.data
    : parsedV3.success
    ? parsedV3.data
    : parsedV2.success
      ? parsedV2.data
      : parsedV1.success
        ? parsedV1.data
        : null;
  if (command === null || command.rendererInstanceId !== rendererInstanceId) return;
  launch = command;
  const planId = launchPlanId(command);
  postLifecycle({type: 'PLAYBACK_FAILED', planId, reason: 'PIXI_APPLICATION_INIT_FAILED'});
}

const startupGate = createRendererStartupGate(
  (serialized) => { void loadLaunch(serialized); },
  reportPixiInitializationFailure,
);

function postRendererBootstrap(): void {
  post({protocolVersion: ART_RENDERER_PROTOCOL_VERSION, rendererInstanceId});
}

window.addEventListener('message', receiveNativeMessage);
document.addEventListener('message', receiveNativeMessage as EventListener);
status.textContent = 'Đã kết nối app; đang khởi tạo sân khấu Pixi…';
postRendererBootstrap();

void app.init({
  width: 800,
  height: 600,
  background: '#fffef9',
  antialias: true,
  autoDensity: true,
  resolution: Math.min(window.devicePixelRatio || 1, 2),
}).then(() => {
  stage.append(app.canvas);
  rendererInitialized = true;
  app.canvas.addEventListener('pointerdown', () => {
    if (launch === null || !isV2Launch(launch)) return;
    postLifecycle({type: 'CANVAS_TAPPED', planId: launch.animationPlan.planId});
  });
  status.textContent = 'Pixi sẵn sàng, đang chờ launch của đúng phiên.';
  startupGate.markReady();
  // React Native WebView can drop a native->page postMessage during WebGL
  // startup. Re-announcing the same bootstrap makes the host replay its one
  // cached launch after the renderer message listener is fully ready.
  postRendererBootstrap();
}).catch(() => {
  console.error('[art-renderer] Pixi application initialization failed.');
  status.textContent = 'Pixi chưa khởi tạo được; ảnh gốc vẫn an toàn trong app.';
  startupGate.markFailed();
  postRendererBootstrap();
});

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

async function loadSupplementalShow(command: RendererLoadCommandV3 | RendererLoadCommandV4): Promise<void> {
  stopSupplementalShow();
  const root = new Container();
  const textures: Texture[] = [];
    const sprites = new Map<string, Sprite>();
  try {
    for (const read of command.assetReads) {
      const response = await fetch(new URL(read.readEndpoint, window.location.href), {
        method: 'GET',
        headers: {'X-Pixi-Asset-Capability': read.readCapability},
        cache: 'no-store',
        credentials: 'same-origin',
      });
      if (!response.ok) throw new Error('SHOW_ASSET_UNAVAILABLE');
      if (response.headers.get('Content-Type')?.split(';')[0] !== read.contentType) {
        throw new Error('SHOW_ASSET_TYPE_INVALID');
      }
      const bytes = await response.arrayBuffer();
      if (
        bytes.byteLength !== read.byteLength
        || bytes.byteLength <= 0
        || bytes.byteLength > 1_000_000
        || await sha256Hex(bytes) !== read.sha256
        || response.headers.get('X-Content-SHA256') !== read.sha256
      ) throw new Error('SHOW_ASSET_HASH_INVALID');
      const decoded = await textureFromBlob(new Blob([bytes], {type: read.contentType}), false, 360);
      const texture = decoded.texture;
      textures.push(texture);
      const sprite = new Sprite(texture);
      sprite.anchor.set(0.5);
      const fit = Math.min(160 / Math.max(1, texture.width), 138 / Math.max(1, texture.height));
      sprite.scale.set(fit);
      sprite.alpha = 0;
      sprite.visible = false;
      root.addChild(sprite);
      sprites.set(read.assetId, sprite);
    }

    const beats = command.showPlan.beats.filter((beat) => beat.targetRole === 'SUPPLEMENTAL_ASSET');
    const missingAsset = beats.some((beat) => beat.assetId === undefined || !sprites.has(beat.assetId));
    if (missingAsset || sprites.size !== command.showPlan.selectedAssetIds.length) {
      throw new Error('SHOW_ASSET_PLAN_MISMATCH');
    }

    supplementalRoot = root;
    supplementalTextures = textures;
    supplementalSprites = sprites;
    app.stage.addChild(root);
    syncShowToTime(autoRigPlayer.getPlaybackState().positionSeconds);
  } catch (error) {
    root.destroy({children: true});
    for (const texture of textures) texture.destroy(true);
    throw error;
  }
}

async function loadSpriteCycle(command: RendererLoadCommandV4): Promise<void> {
  const cycle = command.spriteCycle;
  if (cycle === undefined) return;
  stopActiveSpriteCycle();
  const root = new Container();
  const textures: Texture[] = [];
  let totalBytes = 0;
  try {
    spriteCycleLog('loading', cycle);
    for (const [index, read] of cycle.frameReads.entries()) {
      const response = await fetch(new URL(read.readEndpoint, window.location.href), {
        method: 'GET',
        headers: {'X-Pixi-Asset-Capability': read.readCapability},
        cache: 'no-store',
        credentials: 'same-origin',
      });
      if (!response.ok) throw new Error('SPRITE_CYCLE_FRAME_UNAVAILABLE');
      if (response.headers.get('Content-Type')?.split(';')[0] !== read.contentType) {
        throw new Error('SPRITE_CYCLE_LAYOUT_INVALID');
      }
      const bytes = await response.arrayBuffer();
      totalBytes += bytes.byteLength;
      if (
        bytes.byteLength !== read.byteLength
        || bytes.byteLength <= 0
        || bytes.byteLength > 1_000_000
        || totalBytes > 2_000_000
        || await sha256Hex(bytes) !== read.sha256
        || response.headers.get('X-Content-SHA256') !== read.sha256
      ) throw new Error('SPRITE_CYCLE_FRAME_HASH_INVALID');
      try {
        const decoded = await textureFromBlob(new Blob([bytes], {type: read.contentType}), false, 320);
        textures[index] = decoded.texture;
      } catch {
        throw new Error('SPRITE_CYCLE_RENDER_FAILED');
      }
    }
    const decodedFrames = textures;
    if (decodedFrames.length !== cycle.frameReads.length || decodedFrames.some((texture) => texture.width <= 0 || texture.height <= 0)) {
      throw new Error('SPRITE_CYCLE_LAYOUT_INVALID');
    }
    spriteCycleLog('decoded', cycle, {frameCount: decodedFrames.length, byteLength: totalBytes});
    const maxWidth = Math.max(...decodedFrames.map((texture) => texture.width));
    const maxHeight = Math.max(...decodedFrames.map((texture) => texture.height));
    const sprite = new Sprite(decodedFrames[0]);
    sprite.anchor.set(0.5);
    const fit = Math.min(150 / Math.max(1, maxWidth, maxHeight), 1) * (cycle.scale / 0.4);
    sprite.scale.set(fit);
    sprite.x = cycle.x * 800;
    sprite.y = cycle.y * 600;
    sprite.visible = false;
    root.addChild(sprite);
    app.stage.addChild(root);
    activeSpriteCycle = {cycle, root, sprite, textures, frameIndex: null, wasVisible: false};
    spriteCycleLog('ready', cycle, {frameCount: decodedFrames.length, byteLength: totalBytes});
    syncSpriteCycleToTime(autoRigPlayer.getPlaybackState().positionSeconds);
  } catch (error) {
    if (activeSpriteCycle?.root === root) activeSpriteCycle = null;
    root.destroy({children: true});
    for (const texture of textures) texture?.destroy(true);
    spriteCycleLog('failed', cycle, {reason: safeFailureCode(error)});
    throw error;
  }
}

function stopActiveSpriteCycle(): void {
  if (activeSpriteCycle === null) return;
  activeSpriteCycle.root.destroy({children: true});
  for (const texture of activeSpriteCycle.textures) texture.destroy(true);
  activeSpriteCycle = null;
}

function spriteCycleLog(
  event: 'loading' | 'decoded' | 'ready' | 'playing' | 'frame' | 'failed',
  cycle: PixiSpriteCycleReadV1,
  detail: {frameCount?: number; frameIndex?: number; byteLength?: number; reason?: string} = {},
): void {
  console.info('[pixi-cycle]', JSON.stringify({
    event,
    cycleId: cycle.cycleId,
    behaviorClassId: cycle.behaviorClassId,
    frameCount: detail.frameCount ?? cycle.frameReads.length,
    ...(detail.frameIndex === undefined ? {} : {frameIndex: detail.frameIndex}),
    ...(detail.byteLength === undefined ? {} : {byteLength: detail.byteLength}),
    ...(detail.reason === undefined ? {} : {reason: detail.reason}),
  }));
}

function syncShowToTime(position: number): void {
  const current = launch;
  if (current === null || !isShowLaunch(current)) return;
  const activeSourceBeat = current.showPlan.beats.find((beat) => (
    beat.targetRole === 'SOURCE_SUBJECT'
    && position >= beat.startSeconds
    && position < beat.endSeconds
  ));
  autoRigPlayer.setShowBeat(
    activeSourceBeat?.action ?? null,
    activeSourceBeat === undefined
      ? 0
      : Math.min(1, (position - activeSourceBeat.startSeconds) / (activeSourceBeat.endSeconds - activeSourceBeat.startSeconds)),
  );

  for (const [assetId, sprite] of supplementalSprites) {
    const beat = current.showPlan.beats.find((candidate) => candidate.assetId === assetId
      && candidate.targetRole === 'SUPPLEMENTAL_ASSET'
      && position >= candidate.startSeconds
      && position < candidate.endSeconds);
    if (beat === undefined) {
      sprite.visible = false;
      sprite.alpha = 0;
      continue;
    }
    const progress = Math.min(1, Math.max(0, (position - beat.startSeconds) / (beat.endSeconds - beat.startSeconds)));
    const eased = progress * progress * (3 - 2 * progress);
    const targetX = beat.x * 800;
    const targetY = beat.y * 600;
    sprite.visible = true;
    sprite.alpha = beat.action === 'NOTICE' ? Math.min(1, progress * 5) : 1;
    sprite.x = beat.action === 'APPROACH' ? targetX + (1 - eased) * 32 : targetX;
    sprite.y = beat.action === 'INTERACT'
      ? targetY - Math.sin(progress * Math.PI * 2) * 10
      : beat.action === 'NOTICE'
        ? targetY - Math.sin(progress * Math.PI) * 7
        : targetY;
  }
  syncSpriteCycleToTime(position);
}

function syncSpriteCycleToTime(positionSeconds: number): void {
  const active = activeSpriteCycle;
  if (active === null) return;
  const index = getSpriteCycleFrameIndex(active.cycle, positionSeconds);
  if (index === null) {
    active.sprite.visible = false;
    active.wasVisible = false;
    return;
  }
  if (active.frameIndex !== index) {
    active.sprite.texture = active.textures[index];
    active.frameIndex = index;
    spriteCycleLog('frame', active.cycle, {frameIndex: index});
  }
  if (!active.wasVisible) spriteCycleLog('playing', active.cycle, {frameIndex: index});
  active.wasVisible = true;
  const transform = getSpriteCycleTransform(active.cycle, positionSeconds);
  active.sprite.x = active.cycle.x * 800 + transform.offsetX;
  active.sprite.y = active.cycle.y * 600 + transform.offsetY;
  active.sprite.visible = true;
}

function safeFailureCode(error: unknown): string {
  return normalizeRendererFailureCode(error);
}

async function maskCanvasFromBytes(
  bytes: ArrayBuffer,
  foreground: {canvas: HTMLCanvasElement; sourceWidth: number; sourceHeight: number},
): Promise<HTMLCanvasElement> {
  const bitmap = await createImageBitmap(new Blob([bytes], {type: 'image/png'}));
  if (bitmap.width !== foreground.sourceWidth || bitmap.height !== foreground.sourceHeight) {
    bitmap.close();
    throw new Error('MASK_DIMENSIONS_MISMATCH');
  }
  const canvas = document.createElement('canvas');
  canvas.width = foreground.canvas.width;
  canvas.height = foreground.canvas.height;
  const context = canvas.getContext('2d', {willReadFrequently: true});
  if (context === null) {
    bitmap.close();
    throw new Error('MASK_CANVAS_UNAVAILABLE');
  }
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas;
}

function matchesDerivedPartMaskProvenance(
  artifact: unknown,
  sourceSha256: string,
  artifactRef: string,
  digest: string,
): boolean {
  if (typeof artifact !== 'object' || artifact === null) return false;
  const item = artifact as Record<string, unknown>;
  return item.role === 'ORIGINAL_DERIVED_PART_MASK'
    && item.sourceSha256 === sourceSha256
    && item.artifactRef === artifactRef
    && item.sha256 === digest;
}
