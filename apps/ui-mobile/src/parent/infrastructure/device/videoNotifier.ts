/**
 * Local notifications for the video (FEAT-093): "ready" and "could not be made". They are scheduled on the device by the
 * app itself; no push token and no server is involved. ``expo-notifications`` is registered by the app shell only when its native code is part of the build,
 * so an app build without the native module keeps working (the in-app chip and badge still show the state).
 */
type NotificationsModule = {
  getPermissionsAsync(): Promise<{ granted: boolean; canAskAgain?: boolean }>;
  requestPermissionsAsync(): Promise<{ granted: boolean }>;
  scheduleNotificationAsync(request: { content: { title: string; body: string }; trigger: null }): Promise<string>;
  setNotificationHandler?(handler: { handleNotification: () => Promise<Record<string, boolean>> }): void;
};

let cached: NotificationsModule | null = null;

/**
 * Registers the native notifications module. The app shell does this once ``expo-notifications`` is part of the native
 * build; until then nothing is registered and every call below is a no-op (the chip and badge still show the state).
 * The module is not imported here on purpose: Metro would bundle it into builds that lack the native code.
 */
export function registerNotificationsModule(module: NotificationsModule | null): void {
  cached = module;
  cached?.setNotificationHandler?.({
    handleNotification: async () => ({ shouldShowAlert: true, shouldPlaySound: false, shouldSetBadge: false }),
  });
}

function load(): NotificationsModule | null {
  return cached;
}

export async function ensureVideoNotificationPermission(): Promise<boolean> {
  const module = load();
  if (!module) return false;
  try {
    const current = await module.getPermissionsAsync();
    if (current.granted) return true;
    if (current.canAskAgain === false) return false;
    return (await module.requestPermissionsAsync()).granted;
  } catch {
    return false;
  }
}

export type VideoNotice = 'ready' | 'failed';

const COPY: Record<VideoNotice, { title: string; body: string }> = {
  ready: { title: 'Video của bé đã sẵn sàng', body: 'Mở ứng dụng để xem video và phụ đề.' },
  failed: { title: 'Chưa tạo được video', body: 'Mở ứng dụng để xem lý do và thử lại.' },
};

export async function notifyVideo(kind: VideoNotice): Promise<void> {
  const module = load();
  if (!module) return;
  try {
    const status = await module.getPermissionsAsync();
    if (!status.granted) return;
    await module.scheduleNotificationAsync({ content: COPY[kind], trigger: null });
  } catch {
    // a missed notification is never an error for the adult
  }
}
