/**
 * Local notifications for the video (FEAT-093): "ready" and "could not be made". They are scheduled on the device by the
 * app itself; no push token and no server is involved. ``expo-notifications`` is loaded lazily and only when present,
 * so an app build without the native module keeps working (the in-app chip and badge still show the state).
 */
type NotificationsModule = {
  getPermissionsAsync(): Promise<{ granted: boolean; canAskAgain?: boolean }>;
  requestPermissionsAsync(): Promise<{ granted: boolean }>;
  scheduleNotificationAsync(request: { content: { title: string; body: string }; trigger: null }): Promise<string>;
  setNotificationHandler?(handler: { handleNotification: () => Promise<Record<string, boolean>> }): void;
};

let cached: NotificationsModule | null | undefined;

function load(): NotificationsModule | null {
  if (cached !== undefined) return cached;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    cached = require('expo-notifications') as NotificationsModule;
    cached.setNotificationHandler?.({
      handleNotification: async () => ({ shouldShowAlert: true, shouldPlaySound: false, shouldSetBadge: false }),
    });
  } catch {
    cached = null;
  }
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
