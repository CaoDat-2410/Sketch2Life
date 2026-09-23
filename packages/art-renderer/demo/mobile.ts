import {Application, Texture} from 'pixi.js';

import {
  ART_RENDERER_PROTOCOL_VERSION,
  createBrowserArtPlayer,
  MAX_RENDERER_MESSAGE_BYTES,
  RendererControlCommandSchema,
  RendererLoadCommandSchema,
  type PlaybackEvent,
  type RendererLoadCommand,
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

let launch: RendererLoadCommand | null = null;
let sourceBlob: Blob | null = null;
let eventSequence = 0;
let lastLoadMessage: string | null = null;
let lastProgressPostAt = 0;

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
    case 'FALLBACK_APPLIED':
      status.textContent = 'Renderer dùng chuyển động dự phòng, vẫn giữ nguyên ảnh gốc.';
      playButton.disabled = false;
      break;
    case 'PLAYBACK_FAILED':
      status.textContent = 'Pixi không phát được chuyển động; ảnh gốc vẫn còn trong app.';
      playButton.disabled = false;
      break;
  }
}

const player = createBrowserArtPlayer({
  app,
  loadTexture: async () => {
    if (sourceBlob === null) throw new Error('The original image is not loaded.');
    const bitmap = await createImageBitmap(sourceBlob);
    const canvas = document.createElement('canvas');
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const context = canvas.getContext('2d');
    if (context === null) {
      bitmap.close();
      throw new Error('Canvas context is unavailable.');
    }
    context.drawImage(bitmap, 0, 0);
    bitmap.close();
    return Texture.from(canvas);
  },
  onEvent: (event) => {
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
  },
  onProgress: (progress) => {
    const now = performance.now();
    if (progress.state === 'PLAYING' && now - lastProgressPostAt < 100) return;
    lastProgressPostAt = now;
    eventSequence += 1;
    post({
      protocolVersion: ART_RENDERER_PROTOCOL_VERSION,
      rendererInstanceId,
      sequence: eventSequence,
      type: 'PLAYBACK_STATE',
      positionSeconds: progress.positionSeconds,
      durationSeconds: progress.durationSeconds,
      state: progress.state,
    });
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
  const parsed = RendererLoadCommandSchema.safeParse(parsedJson);
  if (!parsed.success || parsed.data.rendererInstanceId !== rendererInstanceId) {
    status.textContent = 'Launch sai contract hoặc không khớp renderer instance.';
    return;
  }
  const command = parsed.data;
  lastLoadMessage = serialized;
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
    sourceBlob = image;
    await player.load(command.animationPlan.plan);
    launch = command;
    playButton.disabled = false;
    playButton.textContent = 'Tạm dừng / tiếp tục';
    status.textContent = 'Pixi đã nạp ảnh gốc và bắt đầu câu chuyện.';
    player.play();
  } catch {
    sourceBlob = null;
    status.textContent = 'Không nạp được ảnh gốc. Hãy về app và mở Pixi lại thủ công; không tự retry.';
    playButton.disabled = true;
  }
}

function receiveNativeMessage(event: MessageEvent): void {
  const serialized = typeof event.data === 'string' ? event.data : '';
  if (!serialized || new TextEncoder().encode(serialized).byteLength > MAX_RENDERER_MESSAGE_BYTES) return;
  try {
    const control = RendererControlCommandSchema.safeParse(JSON.parse(serialized));
    if (control.success && control.data.rendererInstanceId === rendererInstanceId) {
      switch (control.data.action) {
        case 'PLAY': player.play(); break;
        case 'PAUSE': player.pause(); break;
        case 'REPLAY': player.replay(); break;
        case 'SEEK_RELATIVE_SECONDS': player.seekRelative(control.data.seconds ?? 0); break;
        case 'SEEK_TO_SECONDS': player.seekTo(control.data.seconds ?? 0); break;
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
    const state = player.getPlaybackState();
    if (state.state === 'PLAYING') player.pause();
    else if (state.state === 'COMPLETED') player.replay();
    else player.play();
  } catch {
    status.textContent = 'Pixi không phát được chuyển động; ảnh gốc vẫn còn trong app.';
  }
});

window.addEventListener('pagehide', () => {
  player.destroy();
  sourceBlob = null;
  app.destroy(true);
});

status.textContent = 'Pixi sẵn sàng, đang chờ launch của đúng phiên.';
post({protocolVersion: ART_RENDERER_PROTOCOL_VERSION, rendererInstanceId});
